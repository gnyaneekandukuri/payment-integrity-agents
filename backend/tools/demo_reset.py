"""Reset the demo to its starting state (stop the API server first).

Rebuilds the database, restores the five pre-reviewed cases from their saved runs (no network), and leaves
Samuel Adeyemi (Metro Regional) and Joseph Kim (Crestview Regional) as "awaiting records" for the live upload.
The upload PDFs are in demo_uploads/ at the repository root.

Usage (from backend/):  uv run python -m tools.demo_reset
"""
from app import db
from app.main import restore_saved_runs
from seed import run as seed_run


def main() -> None:
    seed_run.main()
    print("restored from saved runs:", restore_saved_runs()["restored"])
    conn = db.connect()
    waiting = [r["patient_name"] for r in conn.execute(
        "SELECT patient_name FROM cases WHERE id IN ('CASE-BG04','CASE-BG10') AND status='awaiting_records'")]
    print("awaiting records for the live upload:", waiting)


if __name__ == "__main__":
    main()
