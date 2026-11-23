"""Records follow-up: turn the review's missing/conflicting gaps into a targeted records request.

One structured model call (not a loop). The output is checked: every item must come from a recorded gap, the
wording check applies, and only cited page numbers that exist are kept. Saved to disk so the demo can replay it.
If the model is unavailable, a plain template built from the gaps is used instead (labelled 'template').
"""
import json
from datetime import datetime, timezone

from app import db
from app.agents import validators
from app.agents.provider import OpenAIProvider

REQUESTS_DIR = db.DATA_DIR / "requests"

PROMPT = """You draft a records request from a health plan's clinical reviewer to a hospital's health information
management department. The plan reviewed an inpatient claim and could not reach a conclusion because some
information is missing or conflicting.

Write a short, courteous, specific request. Rules:
- Ask ONLY for items that address the gaps listed below. One item per gap that needs records (skip coding questions).
- For each item say exactly what document or value is needed and why (refer to what the record currently shows,
  with page numbers from the evidence).
- Neutral wording. Do not suggest wrongdoing; do not mention payment, denial, overpayment, fraud or recovery.
- Ask for documents that may exist, not for tests that were never done. If a test such as a blood gas was not
  obtained, ask instead for related documentation that could exist (e.g. home oxygen use, prior baseline values,
  any blood gas results not included in the records sent).
- Combine related gaps about the same organ system into one item.
- Do not invent facts not in the inputs.

Return JSON: {"items": [{"request": "...", "reason": "...", "pages": [int]}], "letter": "full letter text"}
The letter is addressed to the hospital's Health Information Management department, references the claim number,
patient name and dates of service, lists the items as a numbered list, and asks for a response within 14 days.
Sign it: Sam Okoro, RN, Clinical Reviewer, Northstar Health Plan Payment Integrity.
"""


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def gather(conn, case_id):
    case = dict(conn.execute(
        "SELECT cs.id, cs.patient_name, cl.id AS claim_id, cl.admit_date, cl.discharge_date, h.name AS hospital "
        "FROM cases cs JOIN claims cl ON cl.id = cs.claim_id JOIN hospitals h ON h.id = cl.hospital_id WHERE cs.id=?",
        (case_id,)).fetchone())
    run = conn.execute("SELECT id FROM agent_runs WHERE subject_id=? AND agent='claim_review' ORDER BY started_at DESC LIMIT 1",
                       (case_id,)).fetchone()
    gaps = [dict(g) for g in conn.execute("SELECT kind, item, why_it_matters FROM gaps WHERE run_id=? AND kind IN ('missing','conflicting')",
                                          (run["id"],))] if run else []
    evidence = [dict(e) for e in conn.execute("SELECT ref, criterion, system, value, page, quote FROM evidence WHERE run_id=? ORDER BY ref",
                                              (run["id"],))] if run else []
    # The SOFA table also says what is unresolved, even when the agent did not write it as a gap.
    sofa_needs = {
        "baseline_uncertain": "No sourced baseline for the {s} system although a pre-existing condition is documented ({d})",
        "not_formally_assessable": "The {s} system could not be scored from the record ({d})",
        "not_documented": "No {s} values are documented in the record",
    }
    if run:
        for row in conn.execute("SELECT system, status, detail FROM sofa_results WHERE run_id=?", (run["id"],)):
            if row["status"] in sofa_needs:
                gaps.append({"kind": "missing", "item": sofa_needs[row["status"]].format(s=row["system"], d=row["detail"]),
                             "why_it_matters": f"The {row['system']} SOFA change cannot be established without it."})
    pages = {r[0] for r in conn.execute("SELECT cp.page FROM chart_pages cp JOIN charts ch ON ch.id = cp.chart_id WHERE ch.case_id=?", (case_id,))}
    return case, (run["id"] if run else None), gaps, evidence, pages


def template(case, gaps):
    items = [{"request": f"Documentation addressing: {g['item']}", "reason": g["why_it_matters"], "pages": []} for g in gaps]
    lines = "\n".join(f"{i}. {it['request']}. Reason: {it['reason']}" for i, it in enumerate(items, start=1))
    letter = (f"To: Health Information Management, {case['hospital']}\n"
              f"Re: Claim {case['claim_id']}, {case['patient_name']}, dates of service {case['admit_date']} to {case['discharge_date']}\n\n"
              f"As part of a clinical review of this admission, please provide the following:\n\n{lines}\n\n"
              "Please respond within 14 days.\n\nSam Okoro, RN, Clinical Reviewer\nNorthstar Health Plan Payment Integrity")
    return items, letter


def draft(conn, case_id: str, mode: str = "live") -> dict:
    case, run_id, gaps, evidence, pages = gather(conn, case_id)
    if not gaps:
        raise ValueError("this review recorded no missing or conflicting items, so there is nothing to request")
    saved = REQUESTS_DIR / f"{case_id}.json"
    used = mode
    if mode == "replay" and saved.exists():
        out = json.loads(saved.read_text(encoding="utf-8"))
    else:
        try:
            provider = OpenAIProvider()
            payload = {"claim": case, "gaps": gaps,
                       "evidence": [{k: e[k] for k in ("ref", "system", "value", "page", "quote")} for e in evidence]}
            resp = provider.client.chat.completions.create(
                model=provider.model, response_format={"type": "json_object"},
                messages=[{"role": "system", "content": PROMPT}, {"role": "user", "content": json.dumps(payload)}])
            out = json.loads(resp.choices[0].message.content)
            used = "live"
            REQUESTS_DIR.mkdir(parents=True, exist_ok=True)
            saved.write_text(json.dumps(out, indent=1), encoding="utf-8")
        except Exception:
            items, letter = template(case, gaps)
            out, used = {"items": items, "letter": letter}, "template"

    # checks: valid pages only; wording; at most one item per gap
    items = []
    for it in out.get("items", [])[: len(gaps)]:
        it["pages"] = [p for p in it.get("pages", []) if isinstance(p, int) and p in pages]
        items.append({"request": str(it.get("request", "")), "reason": str(it.get("reason", "")), "pages": it["pages"]})
    letter = str(out.get("letter", ""))
    problems = validators.wording_problems(letter + " " + " ".join(i["request"] + " " + i["reason"] for i in items))
    if problems or not items:
        items, letter = template(case, gaps)
        used = "template"
    conn.execute("DELETE FROM records_requests WHERE case_id=? AND status='draft'", (case_id,))
    cur = conn.execute("INSERT INTO records_requests (case_id, run_id, mode, status, items, letter, created_at) VALUES (?,?,?,?,?,?,?)",
                       (case_id, run_id, used, "draft", json.dumps(items), letter, _now()))
    conn.commit()
    return {"id": cur.lastrowid, "mode": used, "status": "draft", "items": items, "letter": letter}
