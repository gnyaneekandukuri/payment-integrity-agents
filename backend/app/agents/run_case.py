"""Run the claim review agent on one case and print what it produced.

Usage (from backend/):
  uv run python -m app.agents.run_case CASE-PATEL              # live (calls OpenAI)
  uv run python -m app.agents.run_case CASE-PATEL --replay     # replays the latest saved run, no network
"""
import json
import sys

from app import db
from app.agents.claim_prompt import SYSTEM_PROMPT, USER_TEMPLATE
from app.agents.claim_tools import TOOL_SPECS, ClaimReviewContext
from app.agents.provider import OpenAIProvider, ReplayProvider
from app.agents.runtime import RUNS_DIR, run_agent


def latest_saved_run(case_id):
    files = sorted((RUNS_DIR / case_id).glob("RUN-*.json"))
    if not files:
        raise SystemExit(f"no saved run for {case_id}; run it live first")
    return files[-1]


def review(case_id: str, replay: bool = False) -> dict:
    conn = db.connect()
    provider = ReplayProvider(latest_saved_run(case_id)) if replay else OpenAIProvider()
    return run_agent(conn, agent="claim_review", subject_id=case_id, context_factory=ClaimReviewContext,
                     tool_specs=TOOL_SPECS, system_prompt=SYSTEM_PROMPT, user_message=USER_TEMPLATE.format(case_id=case_id),
                     provider=provider, mode="replay" if replay else "live")


def print_run(run_id: str):
    conn = db.connect()
    run = dict(conn.execute("SELECT * FROM agent_runs WHERE id=?", (run_id,)).fetchone())
    print(f"\n== {run['id']}  {run['subject_id']}  model={run['model']}  status={run['status']}  steps={run['steps']}  "
          f"tokens in/out={run['input_tokens']}/{run['output_tokens']}")
    if run["error"]:
        print("ERROR:", run["error"])
    print("-- steps")
    for s in conn.execute("SELECT n, tool, accepted, result FROM agent_steps WHERE run_id=? ORDER BY n", (run_id,)):
        mark = "ok " if s["accepted"] else "REJ"
        res = json.loads(s["result"])
        extra = ""
        if not s["accepted"]:
            extra = " -> " + str(res.get("reason") or res.get("problems") or res.get("error"))[:200]
        print(f"  {s['n']:>2} {mark} {s['tool']}{extra}")
    print("-- evidence")
    for e in conn.execute("SELECT ref, criterion, system, value, stance, page, quote FROM evidence WHERE run_id=? ORDER BY ref", (run_id,)):
        print(f"  [E{e['ref']}] {e['criterion']}/{e['system']} {e['value']} ({e['stance']}) p{e['page']}: \"{e['quote'][:80]}\"")
    print("-- gaps")
    for g in conn.execute("SELECT kind, item FROM gaps WHERE run_id=?", (run_id,)):
        print(f"  {g['kind']}: {g['item']}")
    print("-- SOFA")
    for r in conn.execute("SELECT system, baseline, worst, change, status FROM sofa_results WHERE run_id=?", (run_id,)):
        print(f"  {r['system']:<15} base={r['baseline']} worst={r['worst']} change={r['change']} [{r['status']}]")
    d = conn.execute("SELECT conclusion, rationale FROM drafts WHERE run_id=?", (run_id,)).fetchone()
    print("-- draft:", (d["conclusion"] + " | " + d["rationale"]) if d else "none")


if __name__ == "__main__":
    case = sys.argv[1] if len(sys.argv) > 1 else "CASE-PATEL"
    out = review(case, replay="--replay" in sys.argv)
    print_run(out["run_id"])
