"""FastAPI app: the JSON API the screens use. Fictional data only; not medical or billing advice."""
import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app import analytics, db
from app.agents.claim_prompt import SYSTEM_PROMPT, USER_TEMPLATE
from app.agents.claim_tools import TOOL_SPECS, ClaimReviewContext
from app.agents.provider import OpenAIProvider, ReplayProvider
from app.agents import records_request as rr
from app.agents import pattern_tools as pt
from app.agents.runtime import RUNS_DIR, run_agent
from app.charts import extract_pages, guess_section, text_layer_report

app = FastAPI(title="Payment integrity agents API", description="Fictional data only. Not medical or billing advice.")
UPLOADS_DIR = db.DATA_DIR / "uploads"
REVIEWER = "Sam Okoro"


def _conn():
    return db.connect()


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _rows(cur):
    return [dict(r) for r in cur.fetchall()]


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


# ------------------------------------------------------------------ queue
@app.get("/api/queue")
def queue():
    conn = _conn()
    rows = _rows(conn.execute("""
        SELECT cs.id, cs.patient_name, cs.age, cs.sex, cs.source, cs.source_detail, cs.status, cs.assigned_to, cs.due_date,
               cs.review_origin, cs.review_reason,
               cl.id AS claim_id, cl.billed_drg, dw.title AS drg_title, cl.admit_date, cl.discharge_date, cl.los, cl.paid_amount,
               h.name AS hospital, (SELECT COUNT(*) FROM charts ch WHERE ch.case_id = cs.id) AS has_records,
               (SELECT d.conclusion FROM drafts d JOIN agent_runs r ON r.id = d.run_id WHERE d.case_id = cs.id
                 ORDER BY r.started_at DESC LIMIT 1) AS draft_conclusion
        FROM cases cs JOIN claims cl ON cl.id = cs.claim_id JOIN hospitals h ON h.id = cl.hospital_id
        JOIN drg_weights dw ON dw.drg = cl.billed_drg
        WHERE cs.in_queue = 1 AND cs.assigned_to = ?
        ORDER BY CASE cs.status WHEN 'ready' THEN 0 WHEN 'in_review' THEN 1 WHEN 'awaiting_records' THEN 2 ELSE 3 END, cs.due_date""", (REVIEWER,)))
    return rows


# ------------------------------------------------------------------ case details
def _latest_run(conn, case_id):
    return conn.execute("SELECT * FROM agent_runs WHERE subject_id=? AND agent='claim_review' ORDER BY started_at DESC LIMIT 1",
                        (case_id,)).fetchone()


@app.get("/api/cases/{case_id}")
def case_detail(case_id: str):
    conn = _conn()
    case = conn.execute("""
        SELECT cs.*, cl.billed_drg, cl.principal_dx, cl.secondary_dx, cl.admit_date, cl.discharge_date, cl.los, cl.icu_days,
               cl.transfer_in, cl.discharge_status, cl.paid_amount, cl.hospital_id, h.name AS hospital, dw.title AS drg_title
        FROM cases cs JOIN claims cl ON cl.id = cs.claim_id JOIN hospitals h ON h.id = cl.hospital_id
        JOIN drg_weights dw ON dw.drg = cl.billed_drg WHERE cs.id=?""", (case_id,)).fetchone()
    if case is None:
        raise HTTPException(404, "case not found")
    case = dict(case)
    case["secondary_dx"] = json.loads(case["secondary_dx"])
    contract = dict(conn.execute("SELECT sepsis_criteria, summary FROM contracts WHERE hospital_id=?", (case["hospital_id"],)).fetchone())
    chart = conn.execute("SELECT * FROM charts WHERE case_id=?", (case_id,)).fetchone()
    pages = _rows(conn.execute("SELECT page, section, LENGTH(text) AS chars FROM chart_pages WHERE chart_id=? ORDER BY page",
                               (chart["id"],))) if chart else []
    run = _latest_run(conn, case_id)
    review = None
    if run:
        rid = run["id"]
        draft = conn.execute("SELECT conclusion, rationale, sections, evidence_ids, validator_result FROM drafts WHERE run_id=?", (rid,)).fetchone()
        review = {
            "run": dict(run),
            "evidence": _rows(conn.execute("SELECT ref, criterion, system, value, unit, observed_at, page, quote, stance FROM evidence "
                                           "WHERE run_id=? ORDER BY ref", (rid,))),
            "gaps": _rows(conn.execute("SELECT kind, item, why_it_matters FROM gaps WHERE run_id=? ORDER BY id", (rid,))),
            "sofa": _rows(conn.execute("SELECT system, baseline, worst, change, status, detail FROM sofa_results WHERE run_id=?", (rid,))),
            "draft": ({**dict(draft), "sections": json.loads(draft["sections"]) if draft["sections"] else None,
                       "evidence_ids": json.loads(draft["evidence_ids"]),
                       "validator_result": json.loads(draft["validator_result"])} if draft else None),
        }
    actions = _rows(conn.execute("SELECT actor, action, before, after, reason, at FROM review_actions WHERE case_id=? ORDER BY id", (case_id,)))
    saved_runs = sorted(p.stem for p in (RUNS_DIR / case_id).glob("RUN-*.json")) if (RUNS_DIR / case_id).exists() else []
    req = conn.execute("SELECT * FROM records_requests WHERE case_id=? ORDER BY id DESC LIMIT 1", (case_id,)).fetchone()
    request = {**dict(req), "items": json.loads(req["items"])} if req else None
    return {"case": case, "contract": contract, "chart": dict(chart) if chart else None, "pages": pages,
            "review": review, "actions": actions, "has_saved_run": bool(saved_runs), "records_request": request,
            "has_saved_request": (rr.REQUESTS_DIR / f"{case_id}.json").exists()}


@app.get("/api/cases/{case_id}/pages/{page}")
def page_text(case_id: str, page: int):
    conn = _conn()
    row = conn.execute("SELECT cp.page, cp.section, cp.text FROM chart_pages cp JOIN charts ch ON ch.id = cp.chart_id "
                       "WHERE ch.case_id=? AND cp.page=?", (case_id, page)).fetchone()
    if row is None:
        raise HTTPException(404, "page not found")
    return dict(row)


@app.get("/api/cases/{case_id}/pdf")
def case_pdf(case_id: str):
    conn = _conn()
    chart = conn.execute("SELECT pdf_path FROM charts WHERE case_id=?", (case_id,)).fetchone()
    if chart is None:
        raise HTTPException(404, "no records for this case")
    path = db.BACKEND_DIR / chart["pdf_path"]
    return FileResponse(path, media_type="application/pdf", headers={"Content-Disposition": "inline"})


# ------------------------------------------------------------------ upload records
@app.post("/api/cases/{case_id}/records")
async def upload_records(case_id: str, file: UploadFile = File(...)):
    conn = _conn()
    case = conn.execute("SELECT id, status FROM cases WHERE id=?", (case_id,)).fetchone()
    if case is None:
        raise HTTPException(404, "case not found")
    if conn.execute("SELECT 1 FROM charts WHERE case_id=?", (case_id,)).fetchone():
        raise HTTPException(409, "records are already attached to this case")
    data = await file.read()
    if not data.startswith(b"%PDF"):
        raise HTTPException(400, "please upload a PDF")
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    chart_id = f"CHART-UP-{uuid.uuid4().hex[:8]}"
    path = UPLOADS_DIR / f"{chart_id}.pdf"
    path.write_bytes(data)
    texts = extract_pages(path)
    needs_ocr = text_layer_report(texts)
    conn.execute("INSERT INTO charts VALUES (?,?,?,?)", (chart_id, case_id, str(path.relative_to(db.BACKEND_DIR)), len(texts)))
    sections = []
    for i, text in enumerate(texts, start=1):
        section = guess_section(text, i)
        sections.append({"page": i, "section": section, "chars": len(text), "needs_ocr": i in needs_ocr})
        conn.execute("INSERT INTO chart_pages VALUES (?,?,?,?)", (chart_id, i, section, text))
    conn.execute("UPDATE cases SET status='ready', assigned_to=? WHERE id=?", (REVIEWER, case_id))
    conn.execute("INSERT INTO review_actions (case_id, actor, action, after, at) VALUES (?,?,?,?,?)",
                 (case_id, REVIEWER, "records_uploaded", f"{file.filename} ({len(texts)} pages)", _now()))
    conn.commit()
    return {"chart_id": chart_id, "filename": file.filename, "pages": sections, "needs_ocr": needs_ocr}


# ------------------------------------------------------------------ run a review (background)
class ReviewRequest(BaseModel):
    mode: str = "live"   # 'live' | 'replay'


AGENTS = {
    "claim_review": dict(context_factory=ClaimReviewContext, tool_specs=TOOL_SPECS, system_prompt=SYSTEM_PROMPT,
                         user=lambda sid: USER_TEMPLATE.format(case_id=sid)),
    "pattern_review": dict(context_factory=pt.PatternReviewContext, tool_specs=pt.TOOL_SPECS, system_prompt=pt.SYSTEM_PROMPT,
                           user=lambda sid: pt.USER_TEMPLATE.format(question_id=sid)),
}


def _run_in_background(case_id: str, mode: str, run_id: str, agent: str = "claim_review"):
    conn = db.connect()
    spec = AGENTS[agent]
    try:
        if mode == "replay":
            files = sorted((RUNS_DIR / case_id).glob("RUN-*.json"))
            provider = ReplayProvider(files[-1])
        else:
            provider = OpenAIProvider()
        run_agent(conn, agent=agent, subject_id=case_id, context_factory=spec["context_factory"], tool_specs=spec["tool_specs"],
                  system_prompt=spec["system_prompt"], user_message=spec["user"](case_id), provider=provider,
                  mode=mode, run_id=run_id)
    except Exception as exc:  # surface provider/setup errors to the progress view
        conn.execute("INSERT OR IGNORE INTO agent_runs (id, agent, subject_id, mode, status, started_at, error) VALUES (?,?,?,?,?,?,?)",
                     (run_id, agent, case_id, mode, "failed", _now(), str(exc)))
        conn.execute("UPDATE agent_runs SET status='failed', error=? WHERE id=?", (str(exc), run_id))
        conn.commit()


@app.post("/api/cases/{case_id}/review")
def start_review(case_id: str, req: ReviewRequest):
    conn = _conn()
    if not conn.execute("SELECT 1 FROM charts WHERE case_id=?", (case_id,)).fetchone():
        raise HTTPException(400, "upload the medical records first")
    if req.mode == "replay" and not list((RUNS_DIR / case_id).glob("RUN-*.json")):
        raise HTTPException(400, "no saved run to replay for this case")
    running = conn.execute("SELECT id FROM agent_runs WHERE subject_id=? AND status='running'", (case_id,)).fetchone()
    if running:
        return {"run_id": running["id"], "already_running": True}
    run_id = f"RUN-{datetime.now():%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:6]}"
    conn.execute("UPDATE cases SET status='in_review' WHERE id=?", (case_id,))
    conn.commit()
    threading.Thread(target=_run_in_background, args=(case_id, req.mode, run_id), daemon=True).start()
    return {"run_id": run_id}


STEP_LABELS = {"list_metrics": "Listed the available metrics", "get_metric": "Read a metric (fixed calculation)",
               "get_notes": "Read provider-relations notes", "record_explanation": "Recorded an explanation",
               "draft_sample_rationale": "Drafted the records-review rationale",
               "get_claim": "Read the claim", "get_contract_criteria": "Checked the contract's sepsis criteria",
               "list_pages": "Listed the record's pages", "search_chart": "Searched the record", "read_page": "Read a page",
               "record_evidence": "Recorded evidence", "record_gap": "Recorded a gap", "compute_sofa": "Calculated SOFA (fixed rules)",
               "submit_draft": "Submitted the draft"}


@app.get("/api/runs/{run_id}")
def run_progress(run_id: str):
    conn = _conn()
    run = conn.execute("SELECT * FROM agent_runs WHERE id=?", (run_id,)).fetchone()
    if run is None:
        return {"run": {"id": run_id, "status": "starting"}, "steps": []}
    steps = []
    for s in conn.execute("SELECT n, tool, args, result, accepted FROM agent_steps WHERE run_id=? ORDER BY n", (run_id,)):
        args, result = json.loads(s["args"]), json.loads(s["result"]) if s["result"].startswith(("{", "[")) else {}
        detail = ""
        if s["tool"] == "read_page":
            detail = f"page {args.get('page')}"
        elif s["tool"] == "search_chart":
            detail = f"\"{args.get('query', '')}\""
        elif s["tool"] == "record_evidence":
            detail = f"{args.get('measure', '')}: {args.get('value', '')} (page {args.get('page')})"
        elif s["tool"] == "record_gap":
            detail = f"{args.get('kind', '')}: {args.get('item', '')}"
        elif s["tool"] == "submit_draft":
            detail = args.get("conclusion", "")
        elif s["tool"] == "get_metric":
            detail = args.get("metric_id", "")
        elif s["tool"] == "record_explanation":
            detail = f"{pt.EXPLANATIONS.get(args.get('explanation'), args.get('explanation'))}: {args.get('status', '')}"
        reason = ""
        if not s["accepted"] and isinstance(result, dict):
            reason = str(result.get("reason") or result.get("problems") or result.get("error") or "")
        steps.append({"n": s["n"], "tool": s["tool"], "label": STEP_LABELS.get(s["tool"], s["tool"]), "detail": detail,
                      "accepted": bool(s["accepted"]), "reason": reason})
    return {"run": dict(run), "steps": steps}


# ------------------------------------------------------------------ reviewer actions
class Action(BaseModel):
    action: str                      # accept | change_conclusion | edit_rationale | escalate | send_to_coder
    conclusion: str | None = None
    rationale: str | None = None
    reason: str | None = None


@app.post("/api/cases/{case_id}/actions")
def reviewer_action(case_id: str, a: Action):
    conn = _conn()
    run = _latest_run(conn, case_id)
    draft = conn.execute("SELECT id, conclusion, rationale FROM drafts WHERE run_id=?", (run["id"],)).fetchone() if run else None
    if draft is None:
        raise HTTPException(400, "there is no draft to act on")
    before = after = None
    if a.action == "change_conclusion":
        if a.conclusion not in ("demonstrated", "not_demonstrated", "cannot_determine") or not (a.reason or "").strip():
            raise HTTPException(400, "a valid conclusion and a reason are required")
        before, after = draft["conclusion"], a.conclusion
    elif a.action == "edit_rationale":
        before, after = draft["rationale"], a.rationale
    elif a.action not in ("accept", "escalate", "send_to_coder"):
        raise HTTPException(400, "unknown action")
    status = {"accept": "reviewed", "change_conclusion": "reviewed", "escalate": "escalated",
              "send_to_coder": "sent_to_coder"}.get(a.action)
    conn.execute("INSERT INTO review_actions (case_id, actor, action, before, after, reason, at) VALUES (?,?,?,?,?,?,?)",
                 (case_id, REVIEWER, a.action, before, after, a.reason, _now()))
    if status:
        conn.execute("UPDATE cases SET status=? WHERE id=?", (status, case_id))
    conn.commit()
    return {"ok": True}


# ------------------------------------------------------------------ records follow-up request
@app.post("/api/cases/{case_id}/records-request")
def draft_records_request(case_id: str, req: ReviewRequest):
    conn = _conn()
    try:
        out = rr.draft(conn, case_id, req.mode)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    conn.execute("INSERT INTO review_actions (case_id, actor, action, after, at) VALUES (?,?,?,?,?)",
                 (case_id, "Assistant", "records_request_drafted", f"{len(out['items'])} items ({out['mode']})", _now()))
    conn.commit()
    return out


class LetterEdit(BaseModel):
    letter: str


@app.put("/api/records-requests/{request_id}")
def edit_records_request(request_id: int, body: LetterEdit):
    conn = _conn()
    row = conn.execute("SELECT case_id, status FROM records_requests WHERE id=?", (request_id,)).fetchone()
    if row is None:
        raise HTTPException(404, "request not found")
    if row["status"] != "draft":
        raise HTTPException(409, "an approved request cannot be edited")
    conn.execute("UPDATE records_requests SET letter=? WHERE id=?", (body.letter, request_id))
    conn.execute("INSERT INTO review_actions (case_id, actor, action, at) VALUES (?,?,?,?)",
                 (row["case_id"], REVIEWER, "records_request_edited", _now()))
    conn.commit()
    return {"ok": True}


@app.post("/api/records-requests/{request_id}/approve")
def approve_records_request(request_id: int):
    conn = _conn()
    row = conn.execute("SELECT case_id, status FROM records_requests WHERE id=?", (request_id,)).fetchone()
    if row is None:
        raise HTTPException(404, "request not found")
    conn.execute("UPDATE records_requests SET status='approved', approved_by=?, approved_at=? WHERE id=?",
                 (REVIEWER, _now(), request_id))
    conn.execute("INSERT INTO review_actions (case_id, actor, action, after, at) VALUES (?,?,?,?,?)",
                 (row["case_id"], REVIEWER, "records_request_approved", "ready to send (not sent in this demo)", _now()))
    conn.execute("UPDATE cases SET status='awaiting_records' WHERE id=?", (row["case_id"],))
    conn.commit()
    return {"ok": True}


# ------------------------------------------------------------------ Maya: billing-pattern review
SAMPLE_NAMES = ["Margaret Hill", "Walter Brooks", "Dorothy Evans", "Harold Price", "Ruth Coleman", "George Sanders",
                "Betty Russell", "Frank Griffin", "Joan Hayes", "Raymond Myers", "Shirley Ford", "Eugene Hamilton",
                "Carol Graham", "Ralph Sullivan", "Janice Wallace", "Louis West", "Gloria Cole"]


def _fmt(m):
    unit = m["unit"]
    return f"{m['value']}%" if unit == "%" else f"{m['value']} {unit}".strip()


@app.get("/api/patterns/{qid}")
def pattern_detail(qid: str):
    conn = _conn()
    q = conn.execute("SELECT * FROM pattern_questions WHERE id=?", (qid,)).fetchone()
    if q is None:
        raise HTTPException(404, "question not found")
    state = json.loads(q["metrics"])
    metrics = analytics.catalog(conn)
    run = conn.execute("SELECT * FROM agent_runs WHERE subject_id=? AND agent='pattern_review' ORDER BY started_at DESC LIMIT 1",
                       (qid,)).fetchone()
    explanations = []
    if run:
        for e in conn.execute("SELECT name, status, summary, citations, confirmed_by FROM explanations "
                              "WHERE question_id=? AND run_id=? ORDER BY id", (qid, run["id"])):
            cites = []
            for c in json.loads(e["citations"]):
                if c in metrics:
                    cites.append({"id": c, "label": metrics[c]["label"], "value": _fmt(metrics[c])})
                else:
                    cites.append({"id": c, "label": "Provider-relations note", "value": c})
            explanations.append({**dict(e), "label": pt.EXPLANATIONS.get(e["name"], e["name"]), "citations": cites})
    stays, eligible = analytics.sample_candidates(conn)
    approved = conn.execute("SELECT * FROM samples WHERE question_id=?", (qid,)).fetchone()
    hosp = conn.execute("SELECT name FROM hospitals WHERE id=?", (q["hospital_id"],)).fetchone()["name"]
    trend = [{"period": f"{y} Q{n}", "value": metrics[f"share_riverside_{y}q{n}"]["value"]} for y in (2024, 2025) for n in (1, 2, 3, 4)]
    return {
        "question": {"id": qid, "hospital": hosp, "drg": q["drg"],
                     "title": "Septicemia or Severe Sepsis without MV >96 Hours with MCC"},
        "metrics": metrics, "trend": trend, "explanations": explanations,
        "rationale": state.get("rationale") if run and state.get("rationale_run") == run["id"] else None,
        "run": dict(run) if run else None, "has_saved_run": (RUNS_DIR / qid).exists(),
        "sensitivity": analytics.sensitivity(conn),
        "sample": {"stays": stays, "eligible": eligible, "approved": bool(approved),
                   "approved_note": approved["rationale"] if approved else None},
    }


@app.post("/api/patterns/{qid}/review")
def start_pattern_review(qid: str, req: ReviewRequest):
    if req.mode == "replay" and not list((RUNS_DIR / qid).glob("RUN-*.json")):
        raise HTTPException(400, "no saved run to replay")
    run_id = f"RUN-{datetime.now():%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:6]}"
    threading.Thread(target=_run_in_background, args=(qid, req.mode, run_id, "pattern_review"), daemon=True).start()
    return {"run_id": run_id}


class ExplanationEdit(BaseModel):
    status: str
    note: str | None = None


@app.post("/api/patterns/{qid}/explanations/{name}")
def confirm_explanation(qid: str, name: str, body: ExplanationEdit):
    if body.status not in pt.STATUSES:
        raise HTTPException(400, f"status must be one of {pt.STATUSES}")
    conn = _conn()
    run = conn.execute("SELECT id FROM agent_runs WHERE subject_id=? AND agent='pattern_review' ORDER BY started_at DESC LIMIT 1",
                       (qid,)).fetchone()
    if run is None:
        raise HTTPException(400, "run the pattern review first")
    who = "Maya Chen" + (f": {body.note}" if body.note else "")
    conn.execute("UPDATE explanations SET status=?, confirmed_by=? WHERE question_id=? AND run_id=? AND name=?",
                 (body.status, who, qid, run["id"], name))
    conn.commit()
    return {"ok": True}


@app.post("/api/patterns/{qid}/sample/approve")
def approve_sample(qid: str):
    conn = _conn()
    if conn.execute("SELECT 1 FROM samples WHERE question_id=?", (qid,)).fetchone():
        return {"ok": True, "already": True}
    stays, _ = analytics.sample_candidates(conn)
    reason = tuple(conn.execute("SELECT review_origin, review_reason, review_concern, review_question, review_not_yours, "
                                "review_context FROM cases WHERE id='CASE-LEE'").fetchone())
    names = iter(SAMPLE_NAMES)
    for i, st in enumerate(stays, start=1):
        if st["case_id"]:
            conn.execute("UPDATE cases SET in_queue=1 WHERE id=?", (st["case_id"],))
            continue
        cid = f"CASE-SMP{i:02d}"
        conn.execute(
            "INSERT INTO cases (id, claim_id, patient_name, age, sex, source, source_detail, status, assigned_to, due_date, in_queue, "
            "review_origin, review_reason, review_concern, review_question, review_not_yours, review_context) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,1,?,?,?,?,?,?)",
            (cid, st["id"], next(names, f"Patient {i}"), 65 + (i * 7) % 25, "F" if i % 2 else "M", "investigation_sample",
             "Targeted records review: Riverside General DRG 871 pattern", "awaiting_records", REVIEWER, "2025-12-12", *reason))
    conn.execute("INSERT INTO samples VALUES (?,?,?,?,1)",
                 (f"SMP-{qid}", qid, json.dumps([s["id"] for s in stays]), f"Approved by the payment integrity manager at {_now()}"))
    conn.commit()
    return {"ok": True, "added_to_queue": len(stays)}


# ------------------------------------------------------------------ Maya: leads (from the monitoring job)
from app import leads as leads_mod  # noqa: E402

LEAD_TYPE_LABEL = {"drg_shift": "DRG severity shift", "short_stays": "Short inpatient stays", "readmissions": "Readmissions"}
_lead_detail_cache: dict[str, dict] = {}


@app.get("/api/leads")
def list_leads():
    conn = _conn()
    rows = _rows(conn.execute(
        "SELECT l.*, h.name AS hospital, h.peer_group FROM leads l JOIN hospitals h ON h.id = l.hospital_id "
        "ORDER BY CASE l.status WHEN 'new' THEN 0 WHEN 'in_analysis' THEN 1 WHEN 'records_requested' THEN 2 ELSE 3 END, "
        "(l.value - l.peer_value) DESC"))
    for r in rows:
        r["type_label"] = LEAD_TYPE_LABEL.get(r["lead_type"], r["lead_type"])
        r["peer_label"] = "referral peers" if r["peer_group"] == "B" else "community peers"
        r["params"] = json.loads(r["params"])
        r["detected_by"] = json.loads(r["detected_by"])
        r["evidence"] = json.loads(r["evidence"])
    return rows


@app.get("/api/leads/{lead_id}")
def lead_detail(lead_id: str):
    if lead_id in _lead_detail_cache:
        return _lead_detail_cache[lead_id]
    conn = _conn()
    lead = conn.execute("SELECT l.*, h.name AS hospital, h.peer_group FROM leads l JOIN hospitals h ON h.id = l.hospital_id "
                        "WHERE l.id=?", (lead_id,)).fetchone()
    if lead is None:
        raise HTTPException(404, "lead not found")
    lead = dict(lead)
    params = json.loads(lead["params"])
    lt, hid = lead["lead_type"], lead["hospital_id"]
    years = []
    for y in (2023, 2024, 2025):
        v, k, n = leads_mod.compute(conn, lt, hid, params, y)
        years.append({"year": y, "value": round(v, 1), "count": k, "of": n,
                      "peer_median": round(leads_mod._peer_median(conn, lt, hid, params, y), 1)})
    quarters = [{"period": f"{y} Q{q}", "value": round(leads_mod.compute(conn, lt, hid, params, y, q)[0], 1)}
                for y in (2024, 2025) for q in (1, 2, 3, 4)]
    notes = _rows(conn.execute("SELECT source, note_date, text FROM notes WHERE hospital_id=? ORDER BY note_date DESC", (hid,)))
    out = {**lead, "params": params, "type_label": LEAD_TYPE_LABEL.get(lt, lt),
           "detected_by": json.loads(lead["detected_by"]), "evidence": json.loads(lead["evidence"]),
           "peer_label": "referral peers" if lead["peer_group"] == "B" else "community peers",
           "years": years, "quarters": quarters, "notes": notes}
    _lead_detail_cache[lead_id] = out
    return out


# ------------------------------------------------------------------ demo admin
@app.post("/api/admin/restore-saved-runs")
def restore_saved_runs(include_patterns: bool = False):
    """Replay every saved run once so the screens have results after a fresh seed (no network)."""
    restored = []
    for case_dir in sorted(list(RUNS_DIR.glob("CASE-*")) + list(RUNS_DIR.glob("Q-*"))):
        conn = db.connect()
        case_id = case_dir.name
        if case_id.startswith("Q-"):
            if include_patterns and not conn.execute("SELECT 1 FROM agent_runs WHERE subject_id=?", (case_id,)).fetchone():
                files = sorted(case_dir.glob("RUN-*.json"))
                if files:
                    spec = AGENTS["pattern_review"]
                    run_agent(conn, agent="pattern_review", subject_id=case_id, context_factory=spec["context_factory"],
                              tool_specs=spec["tool_specs"], system_prompt=spec["system_prompt"], user_message=spec["user"](case_id),
                              provider=ReplayProvider(files[-1]), mode="replay")
                    restored.append(case_id)
            continue
        if _latest_run(conn, case_id) or not conn.execute("SELECT 1 FROM charts WHERE case_id=?", (case_id,)).fetchone():
            continue  # already has a run, or records not uploaded yet (live-upload demo cases)
        files = sorted(case_dir.glob("RUN-*.json"))
        if files:
            run_agent(conn, agent="claim_review", subject_id=case_id, context_factory=ClaimReviewContext, tool_specs=TOOL_SPECS,
                      system_prompt=SYSTEM_PROMPT, user_message=USER_TEMPLATE.format(case_id=case_id),
                      provider=ReplayProvider(files[-1]), mode="replay")
            restored.append(case_id)
    return {"restored": restored}
