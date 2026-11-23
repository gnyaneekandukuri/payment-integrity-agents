"""Evaluate the claim review agent against the answer keys (our own fictional test expectations).

Runs every case N times live and checks each run. Evaluation runs are saved under data/runs/_eval/ so they never
replace the saved runs the demo replays. With --save-for-demo, each case runs once and is saved as the demo run.

Usage (from backend/, API server stopped or running; it only adds rows):
  uv run python -m tools.evaluate --runs 3
  uv run python -m tools.evaluate --save-for-demo
"""
import argparse
import re
import json
import statistics
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from app import db
from app.agents import validators
from app.agents.claim_prompt import SYSTEM_PROMPT, USER_TEMPLATE
from app.agents.claim_tools import TOOL_SPECS, ClaimReviewContext
from app.agents.provider import OpenAIProvider
from app.agents.runtime import RUNS_DIR, run_agent
from app.charts import extract_pages, guess_section

EVAL_DIR = db.DATA_DIR / "eval"

# What a good review must contain, per case (fictional test expectations, not clinical validation).
# key_facts: (organ system, regex) pairs that must appear in the cited evidence (value or quote), from ANY page.
EXPECT = {
    "CASE-ORTIZ":  {"conclusion": "demonstrated", "sofa_min": 4,
                    "key_facts": [("cardiovascular", r"0\.08"), ("renal", r"1\.6"), ("renal", r"0\.8")]},
    "CASE-LEE":    {"conclusion": "not_demonstrated", "sofa_max": 1,
                    "key_facts": [("cardiovascular", r"83|112/68|no vasopressor|none"), ("renal", r"0\.9|0\.8"),
                                  ("cns", r"normal|alert|orient")]},
    "CASE-PATEL":  {"conclusion": "cannot_determine", "uncertain_systems": ["renal"], "conflict": True,
                    "key_facts": [("renal", r"2\.0"), ("renal", r"ckd|chronic kidney"), ("cns", r"confus|altered|disorient")]},
    "CASE-NGUYEN": {"conclusion": "demonstrated", "sofa_min": 2, "coding_codes": ["E43"],
                    "key_facts": [("coagulation", r"140"), ("renal", r"1\.5"), ("cardiovascular", r"64")]},
    "CASE-BROOKS": {"conclusion": "demonstrated", "sofa_min": 2, "sofa_max": 2,
                    "key_facts": [("respiratory", r"78|217|ratio|pao2")]},
    "CASE-BG04":   {"conclusion": "demonstrated", "sofa_min": 4,
                    "key_facts": [("coagulation", r"88"), ("liver", r"2\.4"), ("renal", r"1\.3")]},
    "CASE-BG10":   {"conclusion": "not_demonstrated", "sofa_max": 1, "coding_codes": ["G93.41"],
                    "key_facts": [("cns", r"normal|alert|orient"), ("cardiovascular", r"93|no vasopressor|none|128/76"),
                                  ("renal", r"0\.9|1\.0")]},
}


def _norm(t):
    return " ".join((t or "").lower().replace("|", " ").split())


def attach_upload_records(conn):
    """Attach the two live-upload PDFs (if not attached yet) so they can be evaluated."""
    from seed.run import DEMO_UPLOADS_DIR, UPLOAD_CASES
    for case in UPLOAD_CASES:
        if conn.execute("SELECT 1 FROM charts WHERE case_id=?", (case["case_id"],)).fetchone():
            continue
        path = DEMO_UPLOADS_DIR / case["upload_filename"]
        texts = extract_pages(path)
        chart_id = f"CHART-EVAL-{case['case_id'][5:]}"
        conn.execute("INSERT INTO charts VALUES (?,?,?,?)", (chart_id, case["case_id"], str(path), len(texts)))
        for i, t in enumerate(texts, start=1):
            conn.execute("INSERT INTO chart_pages VALUES (?,?,?,?)", (chart_id, i, guess_section(t, i), t))
        conn.execute("UPDATE cases SET status='ready' WHERE id=?", (case["case_id"],))
    conn.commit()


def run_one(case_id, save_dir):
    conn = db.connect()
    out = run_agent(conn, agent="claim_review", subject_id=case_id, context_factory=ClaimReviewContext, tool_specs=TOOL_SPECS,
                    system_prompt=SYSTEM_PROMPT, user_message=USER_TEMPLATE.format(case_id=case_id),
                    provider=OpenAIProvider(), mode="live", save_dir=save_dir)
    return case_id, out["run_id"]


def score(conn, case_id, run_id):
    exp = EXPECT[case_id]
    key = json.loads(conn.execute("SELECT json FROM answer_keys WHERE case_id=?", (case_id,)).fetchone()[0])
    run = dict(conn.execute("SELECT * FROM agent_runs WHERE id=?", (run_id,)).fetchone())
    draft = conn.execute("SELECT conclusion, rationale, sections FROM drafts WHERE run_id=?", (run_id,)).fetchone()
    evidence = [dict(e) for e in conn.execute("SELECT page, quote, system, value FROM evidence WHERE run_id=?", (run_id,))]
    gaps = [dict(g) for g in conn.execute("SELECT kind, item, why_it_matters FROM gaps WHERE run_id=?", (run_id,))]
    sofa = {r["system"]: dict(r) for r in conn.execute("SELECT * FROM sofa_results WHERE run_id=?", (run_id,))}
    pages = {r["page"]: r["text"] for r in conn.execute(
        "SELECT cp.page, cp.text FROM chart_pages cp JOIN charts ch ON ch.id = cp.chart_id WHERE ch.case_id=?", (case_id,))}
    rejected = conn.execute("SELECT COUNT(*) FROM agent_steps WHERE run_id=? AND accepted=0", (run_id,)).fetchone()[0]

    change = sum(v["change"] or 0 for v in sofa.values() if v["status"] == "scored")
    facts = exp.get("key_facts", [])
    found = [f for f in facts if any(e["system"] == f[0] and re.search(f[1], _norm(f"{e['value']} {e['quote']}")) for e in evidence)]
    missing_facts = [f"{sys}~{rx}" for sys, rx in facts if (sys, rx) not in found]
    cites_ok = all(validators.locate_quote(pages.get(e["page"], ""), e["quote"]) for e in evidence)
    draft_text = (draft["rationale"] + " " + (draft["sections"] or "")) if draft else ""
    checks = {
        "completed": run["status"] == "completed",
        "conclusion": bool(draft) and draft["conclusion"] == exp["conclusion"],
        "sofa_in_range": (change >= exp.get("sofa_min", -1)) and (change <= exp.get("sofa_max", 99)),
        "key_evidence": (len(found) / len(facts)) if facts else 1.0,
        "citations_valid": cites_ok,
        "no_forbidden_words": not validators.wording_problems(draft_text),
    }
    if "coding_codes" in exp:
        checks["coding_question"] = all(any(code in (g["item"] + g["why_it_matters"]) for g in gaps if g["kind"] == "coding_question")
                                        for code in exp["coding_codes"])
    if "uncertain_systems" in exp:
        checks["baseline_uncertain"] = all(sofa.get(s, {}).get("status") == "baseline_uncertain" for s in exp["uncertain_systems"])
    if exp.get("conflict"):
        checks["conflict_recorded"] = any(g["kind"] == "conflicting" for g in gaps)
    return {"missing_facts": missing_facts, "case": case_id, "run_id": run_id, "conclusion": draft["conclusion"] if draft else None, "sofa_change": change,
            "steps": run["steps"], "rejected": rejected, "input_tokens": run["input_tokens"], "output_tokens": run["output_tokens"],
            "checks": checks}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--cases", nargs="*", default=list(EXPECT))
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--save-for-demo", action="store_true")
    ap.add_argument("--rescore", help="re-score the runs in an earlier eval JSON without re-running")
    a = ap.parse_args()
    conn = db.connect()
    if a.rescore:
        prev = json.loads(open(a.rescore, encoding="utf-8").read())
        done = [(r["case"], r["run_id"]) for r in prev["results"]]
        a.cases = list(dict.fromkeys(c for c, _ in done))
        return report(conn, a, [score(conn, c, r) for c, r in done])
    attach_upload_records(conn)
    save_dir = RUNS_DIR if a.save_for_demo else RUNS_DIR / "_eval"
    jobs = [c for c in a.cases for _ in range(1 if a.save_for_demo else a.runs)]
    print(f"running {len(jobs)} live reviews ({len(a.cases)} cases x {1 if a.save_for_demo else a.runs})...")
    with ThreadPoolExecutor(max_workers=a.concurrency) as pool:
        done = list(pool.map(lambda c: run_one(c, save_dir), jobs))
    return report(conn, a, [score(conn, c, r) for c, r in done])


def report(conn, a, results):
    print(f"\n{'case':<13} {'run':<28} {'conclusion':<17} {'SOFA':>4} {'steps':>5} {'rej':>3}  checks")
    for r in results:
        failed = [k for k, v in r["checks"].items() if v is False or (isinstance(v, float) and v < 1)]
        mark = "PASS" if not failed else "FAIL " + ",".join(failed) + (f" {r['missing_facts']}" if r["missing_facts"] else "")
        print(f"{r['case']:<13} {r['run_id']:<28} {str(r['conclusion']):<17} {r['sofa_change']:>4} {r['steps']:>5} {r['rejected']:>3}  {mark}")

    print("\nper case (share of runs passing every check):")
    summary = {}
    for c in a.cases:
        rs = [r for r in results if r["case"] == c]
        passed = sum(all(v is True or (isinstance(v, float) and v >= 1) for v in r["checks"].values()) for r in rs)
        right = sum(r["checks"]["conclusion"] for r in rs)
        summary[c] = {"runs": len(rs), "all_checks": passed, "conclusion_correct": right,
                      "median_steps": statistics.median(r["steps"] for r in rs),
                      "avg_input_tokens": round(statistics.mean(r["input_tokens"] for r in rs))}
        print(f"  {c:<13} conclusion {right}/{len(rs)}  all checks {passed}/{len(rs)}  median steps {summary[c]['median_steps']}")
    total = len(results)
    print(f"\noverall: conclusion correct {sum(r['checks']['conclusion'] for r in results)}/{total}; "
          f"citations valid {sum(r['checks']['citations_valid'] for r in results)}/{total}; "
          f"forbidden words 0 in {sum(r['checks']['no_forbidden_words'] for r in results)}/{total}; "
          f"tokens in/out {sum(r['input_tokens'] for r in results):,}/{sum(r['output_tokens'] for r in results):,}")
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    path = EVAL_DIR / f"eval-{datetime.now():%Y%m%d-%H%M%S}{'-demo' if a.save_for_demo else ''}.json"
    path.write_text(json.dumps({"results": results, "summary": summary}, indent=1), encoding="utf-8")
    print("saved", path)


if __name__ == "__main__":
    main()
