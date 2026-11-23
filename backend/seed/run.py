"""Rebuild the demo database from scratch: reference data, fictional claims, cases, charts.

Usage (from backend/):  uv run python -m seed.run
"""
import json

from app import db
from seed import claims_gen, reference, review_reasons
from seed.cases import brooks, lee, nguyen, ortiz, patel, upload_adeyemi, upload_kim
from seed.render import extract_pages, render_pdf

CASES = [ortiz.CASE, lee.CASE, patel.CASE, nguyen.CASE, brooks.CASE]

# Other items in the clinical review queue (no chart loaded in the demo). All fictional.
# hospital, drg, source, source detail, status, assigned to, patient, age, sex
BACKGROUND_QUEUE = [
    ("H-HAR", "291", "routine", "Pre-payment selection rule: heart failure with MCC, short stay", "awaiting_records", "Sam Okoro", "Grace Holloway", 77, "F"),
    ("H-GRV", "640", "investigation_sample", "Targeted records review: Greenvale DRG 640 pattern", "awaiting_records", "Sam Okoro", "Victor Mendes", 71, "M"),
    ("H-SUM", "189", "routine", "Post-payment audit selection: respiratory failure", "in_review", "J. Rivera", "Helen Park", 66, "F"),
    ("H-MET", "871", "routine", "Pre-payment selection rule: high-value DRG 871 claim", "awaiting_records", "Sam Okoro", "Samuel Adeyemi", 74, "M"),
    ("H-UNI", "392", "routine", "Short-stay inpatient admission: observation-status review", "completed", "J. Rivera", "Olivia Grant", 59, "F"),
    ("H-CED", "470", "routine", "Quality-assurance sample", "completed", "Sam Okoro", "Frank Novak", 68, "M"),
    ("H-BRK", "064", "routine", "Appeal re-review: hospital disputed prior finding", "in_review", "Dr. Ruth Adeyemi", "Rosa Delgado", 81, "F"),
    ("H-ASH", "683", "routine", "Post-payment audit selection: renal failure with CC", "awaiting_records", "Sam Okoro", "Arthur Bell", 79, "M"),
    ("H-NOR", "190", "routine", "Pre-payment selection rule: COPD with MCC", "awaiting_records", "J. Rivera", "Nina Kowalski", 70, "F"),
    ("H-CRE", "871", "routine", "Pre-payment selection rule: high-value DRG 871 claim", "awaiting_records", "Sam Okoro", "Joseph Kim", 77, "M"),
]

# Records for live-upload demos: rendered to demo_uploads/, NOT attached. Their claims are aligned to the record.
UPLOAD_CASES = [upload_adeyemi.CASE, upload_kim.CASE]
DEMO_UPLOADS_DIR = db.BACKEND_DIR.parent / "demo_uploads"


def main() -> None:
    conn = db.reset()
    hosp_names = {}
    for hid, name, beds, teach, ref, group, base in reference.HOSPITALS:
        conn.execute("INSERT INTO hospitals VALUES (?,?,?,?,?,?,?,?)",
                     (hid, name, reference.REGION, beds, teach, ref, group, base))
        crit, summary = reference.CONTRACTS.get(hid, reference.DEFAULT_CONTRACT)
        conn.execute("INSERT INTO contracts VALUES (?,?,?)", (hid, crit, summary))
        hosp_names[hid] = name
    for hid, source, date, text in reference.NOTES:
        conn.execute("INSERT INTO notes (hospital_id, source, note_date, text) VALUES (?,?,?,?)",
                     (hid, source, date, text))
    weights = {}
    for drg, title, weight, family in reference.DRGS:
        conn.execute("INSERT INTO drg_weights VALUES (?,?,?,?)", (drg, title, weight, family))
        weights[drg] = weight

    rows = claims_gen.generate(reference.HOSPITALS)
    rows += claims_gen.generate_other(reference.HOSPITALS, weights)
    conn.executemany("INSERT INTO claims VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)

    base_rates = {h[0]: h[6] for h in reference.HOSPITALS}
    for case in CASES:
        c = case["claim"]
        conn.execute(
            "INSERT INTO claims VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (c["id"], case["hospital_id"], f"M-{case['case_id']}", c["year"], c["quarter"], c["admit_date"],
             c["discharge_date"], c["los"], c["billed_drg"], c["principal_dx"], json.dumps(c["secondary_dx"]),
             c["icu_days"], c["transfer_in"], c["discharge_status"],
             round(weights[c["billed_drg"]] * base_rates[case["hospital_id"]], 2), c["member_risk"], 1))
        conn.execute(
            "INSERT INTO cases (id, claim_id, patient_name, age, sex, source, source_detail, status, assigned_to, due_date, in_queue) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (case["case_id"], c["id"], case["patient_name"], case["age"], case["sex"], case["source"],
             case["source_detail"], "ready", "Sam Okoro", case.get("due_date", "2025-11-28"),
             0 if case["source"] == "investigation_sample" else 1))  # shown to Sam once Maya's sample is approved
        chart_id = f"CHART-{case['case_id'][5:]}"
        pdf_path = db.CHARTS_DIR / f"{chart_id}.pdf"
        try:
            sections = render_pdf(case, hosp_names[case["hospital_id"]], pdf_path)
        except Exception as exc:  # e.g. the PDF is open in a viewer on Windows
            if not pdf_path.exists():
                raise
            print(f"  note: could not rewrite {pdf_path.name} ({exc.__class__.__name__}); reusing the existing file")
            sections = [title for title, _ in case["sections"]]
        texts = extract_pages(pdf_path)
        conn.execute("INSERT INTO charts VALUES (?,?,?,?)",
                     (chart_id, case["case_id"], str(pdf_path.relative_to(db.BACKEND_DIR)), len(texts)))
        for i, (section, text) in enumerate(zip(sections, texts), start=1):
            conn.execute("INSERT INTO chart_pages VALUES (?,?,?,?)", (chart_id, i, section, text))
        conn.execute("INSERT INTO answer_keys VALUES (?,?)", (case["case_id"], json.dumps(case["answer_key"])))
    for i, (hid, drg, source, detail, status, who, name, age, sex) in enumerate(BACKGROUND_QUEUE, start=1):
        claim = conn.execute("SELECT id FROM claims WHERE hospital_id=? AND billed_drg=? AND year=2025 AND is_case=0 "
                             "ORDER BY id LIMIT 1", (hid, drg)).fetchone()
        conn.execute(
            "INSERT INTO cases (id, claim_id, patient_name, age, sex, source, source_detail, status, assigned_to, due_date, in_queue) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,1)",
            (f"CASE-BG{i:02d}", claim["id"], name, age, sex, source, detail, status, who, f"2025-12-{i + 1:02d}"))
    for case in UPLOAD_CASES:
        c = case["claim"]
        claim_id = conn.execute("SELECT claim_id FROM cases WHERE id=?", (case["case_id"],)).fetchone()["claim_id"]
        conn.execute("UPDATE claims SET admit_date=?, discharge_date=?, los=?, billed_drg=?, icu_days=?, transfer_in=?, "
                     "discharge_status=?, principal_dx=?, secondary_dx=?, paid_amount=?, year=?, quarter=? WHERE id=?",
                     (c["admit_date"], c["discharge_date"], c["los"], c["billed_drg"], c["icu_days"], c["transfer_in"],
                      c["discharge_status"], c["principal_dx"], json.dumps(c["secondary_dx"]),
                      round(weights[c["billed_drg"]] * base_rates[case["hospital_id"]], 2), c["year"], c["quarter"], claim_id))
        conn.execute("UPDATE cases SET patient_name=?, age=?, sex=? WHERE id=?",
                     (case["patient_name"], case["age"], case["sex"], case["case_id"]))
        conn.execute("INSERT INTO answer_keys VALUES (?,?)", (case["case_id"], json.dumps(case["answer_key"])))
        out = DEMO_UPLOADS_DIR / case["upload_filename"]
        try:
            render_pdf(case, hosp_names[case["hospital_id"]], out)
        except Exception as exc:
            print(f"  note: could not rewrite {out.name} ({exc.__class__.__name__}); keeping the existing file")
    conn.execute("INSERT INTO pattern_questions VALUES (?,?,?,?)", ("Q-RIV-871", "H-RIV", "871", json.dumps({"status": "open"})))
    from app import leads
    found = leads.detect_all(conn)
    leads.write(conn, found)
    print(f"  monitoring job: {len(found)} leads")
    for case_id, r in review_reasons.REASONS.items():
        conn.execute("UPDATE cases SET review_origin=?, review_reason=?, review_concern=?, review_question=?, review_not_yours=?, "
                     "review_context=? WHERE id=?",
                     (r["origin"], r["reason"], r["concern"], r["question"], r["not_yours"], r["context"], case_id))
    conn.commit()
    n = conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0]
    print(f"Seeded {n:,} claims, {len(CASES)} cases, charts in {db.CHARTS_DIR}")


if __name__ == "__main__":
    main()
