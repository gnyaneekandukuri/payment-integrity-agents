"""Agent loop: the model picks a tool, the runtime runs it, the result goes back, repeat.

Every step is written to agent_steps; the model turns are saved to data/runs/ so a run can be replayed offline.
"""
import json
import uuid
from datetime import datetime, timezone

from app import db
from app.agents.provider import Turn

RUNS_DIR = db.DATA_DIR / "runs"
MAX_STEPS = 60          # tool calls (a 9-10 page chart needs ~25-45)
MAX_NUDGES = 2          # times we remind the model to keep using tools


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def run_agent(conn, *, agent: str, subject_id: str, context_factory, tool_specs, system_prompt: str,
              user_message: str, provider, mode: str, run_id: str | None = None, save_dir=None) -> dict:
    run_id = run_id or f"RUN-{datetime.now():%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:6]}"
    conn.execute("INSERT INTO agent_runs (id, agent, subject_id, model, mode, status, started_at) VALUES (?,?,?,?,?,?,?)",
                 (run_id, agent, subject_id, provider.model, mode, "running", _now()))
    conn.commit()
    ctx = context_factory(conn, subject_id, run_id)
    messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_message}]
    turns: list[Turn] = []
    steps = nudges = tokens_in = tokens_out = 0
    status, error = "incomplete", None
    try:
        while steps < MAX_STEPS and not ctx.done:
            turn = provider.complete(messages, tool_specs)
            turns.append(turn)
            tokens_in += turn.input_tokens
            tokens_out += turn.output_tokens
            if not turn.tool_calls:
                if nudges >= MAX_NUDGES:
                    break
                nudges += 1
                messages.append({"role": "assistant", "content": turn.content or ""})
                messages.append({"role": "user", "content": "Continue using the tools. Finish only by calling submit_draft."})
                continue
            messages.append({"role": "assistant", "content": turn.content,
                             "tool_calls": [{"id": tc.id, "type": "function",
                                             "function": {"name": tc.name, "arguments": tc.arguments}} for tc in turn.tool_calls]})
            for tc in turn.tool_calls:
                steps += 1
                try:
                    args = json.loads(tc.arguments or "{}")
                except json.JSONDecodeError:
                    args, result = {}, {"error": "arguments were not valid JSON"}
                else:
                    result = ctx.call(tc.name, args)
                accepted = not (isinstance(result, dict) and (result.get("accepted") is False or "error" in result))
                conn.execute("INSERT INTO agent_steps VALUES (?,?,?,?,?,?)",
                             (run_id, steps, tc.name, json.dumps(args), json.dumps(result)[:4000], int(accepted)))
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(result)})
                conn.execute("UPDATE agent_runs SET steps=? WHERE id=?", (steps, run_id))
                conn.commit()  # each step becomes visible to the live progress view
        status = "completed" if ctx.done else "incomplete"
    except Exception as exc:  # keep the trace even if the provider fails
        status, error = "failed", f"{exc.__class__.__name__}: {exc}"
    conn.execute("UPDATE agent_runs SET status=?, finished_at=?, steps=?, input_tokens=?, output_tokens=?, error=? WHERE id=?",
                 (status, _now(), steps, tokens_in, tokens_out, error, run_id))
    conn.commit()
    if mode == "live" and turns:
        out = (save_dir or RUNS_DIR) / subject_id
        out.mkdir(parents=True, exist_ok=True)
        (out / f"{run_id}.json").write_text(json.dumps(
            {"run_id": run_id, "agent": agent, "subject_id": subject_id, "model": provider.model,
             "status": status, "turns": [t.to_dict() for t in turns]}, indent=1), encoding="utf-8")
    return {"run_id": run_id, "status": status, "steps": steps, "input_tokens": tokens_in,
            "output_tokens": tokens_out, "error": error, "draft": getattr(ctx, "draft", None)}
