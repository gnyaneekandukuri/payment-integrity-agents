"""Prove the whole demo runs without OpenAI: break the API key, then walk every demo step in replay mode.

Runs in-process (no servers needed), then resets the demo to its starting state.
Usage (from backend/, with the API server stopped):  uv run python -m tools.offline_check
"""
import os
import time

os.environ["OPENAI_API_KEY"] = "offline-check-invalid-key"  # any live model call would now fail

from fastapi.testclient import TestClient  # noqa: E402

from app import db  # noqa: E402
from app.main import app  # noqa: E402
from seed.run import DEMO_UPLOADS_DIR  # noqa: E402
from tools import demo_reset  # noqa: E402

c = TestClient(app)
results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(f"  {'PASS' if ok else 'FAIL'}  {name}{('  (' + detail + ')') if detail else ''}")


def wait(run_id, timeout=120):
    for _ in range(timeout):
        r = c.get(f"/api/runs/{run_id}").json()
        if r["run"]["status"] in ("completed", "failed", "incomplete"):
            return r
        time.sleep(1)
    return r


def main():
    demo_reset.main()
    print("\n== Offline walk-through (OpenAI key deliberately invalid) ==")
    leads = c.get("/api/leads").json()
    check("Leads list loads", len(leads) >= 7, f"{len(leads)} leads")
    riv = next(item for item in leads if item["question_id"] == "Q-RIV-871")
    check("Riverside lead detail loads", c.get(f"/api/leads/{riv['id']}").status_code == 200, riv["id"])

    run = c.post("/api/patterns/Q-RIV-871/review", json={"mode": "replay"}).json()["run_id"]
    prog = wait(run)
    pattern = c.get("/api/patterns/Q-RIV-871").json()
    check("Maya: explanations replay", prog["run"]["status"] == "completed" and len(pattern["explanations"]) == 6,
          f"{len(pattern['explanations'])} explanations, {len(prog['steps'])} steps")
    check("Maya: rationale says not extrapolable", "extrapolat" in (pattern["rationale"] or "").lower())

    before = len(c.get("/api/queue").json())
    c.post("/api/patterns/Q-RIV-871/sample/approve")
    after = len(c.get("/api/queue").json())
    check("Sample approval releases cases to Sam", after - before == 20, f"{before} -> {after}")

    for case_id, fname, expected in [("CASE-BG04", "Metro_Regional_records_Samuel_Adeyemi.pdf", "demonstrated"),
                                     ("CASE-BG10", "Crestview_Regional_records_Joseph_Kim.pdf", "not_demonstrated")]:
        with open(DEMO_UPLOADS_DIR / fname, "rb") as f:
            up = c.post(f"/api/cases/{case_id}/records", files={"file": (fname, f, "application/pdf")}).json()
        check(f"Upload {fname}", len(up.get("pages", [])) >= 8 and not up.get("needs_ocr"), f"{len(up.get('pages', []))} pages")
        rid = c.post(f"/api/cases/{case_id}/review", json={"mode": "replay"}).json()["run_id"]
        prog = wait(rid)
        draft = (c.get(f"/api/cases/{case_id}").json()["review"] or {}).get("draft") or {}
        check(f"Review {case_id} replay", draft.get("conclusion") == expected, f"{draft.get('conclusion')}, {len(prog['steps'])} steps")

    for case_id, expected in [("CASE-PATEL", "cannot_determine"), ("CASE-LEE", "not_demonstrated"), ("CASE-ORTIZ", "demonstrated")]:
        d = c.get(f"/api/cases/{case_id}").json()
        check(f"{case_id} saved review present", d["review"]["draft"]["conclusion"] == expected)

    req = c.post("/api/cases/CASE-PATEL/records-request", json={"mode": "replay"}).json()
    check("Patel records request from saved draft", req.get("mode") == "replay" and len(req.get("items", [])) >= 2,
          f"mode {req.get('mode')}, {len(req.get('items', []))} items")

    conn = db.connect()
    live = conn.execute("SELECT COUNT(*) FROM agent_runs WHERE mode='live' AND started_at > datetime('now','-10 minutes')").fetchone()[0]
    check("No live model runs during the walk-through", live == 0)

    print(f"\n{sum(results)}/{len(results)} checks passed")
    print("\nResetting the demo to its starting state...")
    demo_reset.main()


if __name__ == "__main__":
    main()
