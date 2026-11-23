"""Export the database tables to CSV files (open in Excel) under data_preview/ at the repository root.

Usage (from backend/):  uv run python -m tools.export_preview
"""
import csv
from pathlib import Path

from app import db

OUT = db.BACKEND_DIR.parent / "data_preview"
QUERIES = {
    "1_hospitals.csv": "SELECT * FROM hospitals",
    "2_contracts.csv": "SELECT * FROM contracts",
    "3_notes.csv": "SELECT hospital_id, source, note_date, text FROM notes ORDER BY hospital_id, note_date",
    "4_drg_weights.csv": "SELECT * FROM drg_weights",
    "5_claims_all.csv": "SELECT * FROM claims",
    "6_claims_riverside_2025.csv": "SELECT * FROM claims WHERE hospital_id='H-RIV' AND year=2025",
    "7_cases_review_queue.csv": ("SELECT cs.id, cs.patient_name, cs.age, cs.sex, h.name AS hospital, cl.billed_drg, cl.los, "
                                 "cl.icu_days, cs.source, cs.source_detail, cs.status, cs.assigned_to, cs.due_date, "
                                 "(SELECT COUNT(*) FROM charts ch WHERE ch.case_id = cs.id) AS has_chart "
                                 "FROM cases cs JOIN claims cl ON cl.id = cs.claim_id JOIN hospitals h ON h.id = cl.hospital_id"),
    "8_chart_pages.csv": "SELECT chart_id, page, section, text FROM chart_pages ORDER BY chart_id, page",
    "9_answer_keys.csv": "SELECT * FROM answer_keys",
}


def main() -> None:
    OUT.mkdir(exist_ok=True)
    conn = db.connect()
    for old in OUT.glob("7_cases.csv"):
        try:
            old.unlink()
        except OSError:
            pass
    for name, query in QUERIES.items():
        cur = conn.execute(query)
        rows = cur.fetchall()
        try:
            with open(OUT / name, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow([d[0] for d in cur.description])
                writer.writerows(rows)
            print(f"{name}: {len(rows):,} rows")
        except PermissionError:
            print(f"{name}: SKIPPED (file is open in another program; close it and re-run)")


if __name__ == "__main__":
    main()
