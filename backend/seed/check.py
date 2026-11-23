"""Phase 1 acceptance check: scenario numbers from the claims, and case quotes present in page text.

Usage (from backend/):  uv run python -m seed.check
"""
import json
import statistics

from app import db

INFECTION = ("871", "872", "193", "194", "195", "177", "178", "179", "689", "690")


def share_871(conn, hid, year):
    q = f"SELECT SUM(billed_drg='871')*1.0/COUNT(*), COUNT(*), SUM(billed_drg='871') FROM claims WHERE hospital_id=? AND year=? AND billed_drg IN ({','.join('?'*len(INFECTION))})"
    return conn.execute(q, (hid, year, *INFECTION)).fetchone()


def group_ids(conn, group):
    return [r[0] for r in conn.execute("SELECT id FROM hospitals WHERE peer_group=?", (group,))]


def stat_871(conn, ids, year, expr):
    ph = ",".join("?" * len(ids))
    return conn.execute(f"SELECT {expr} FROM claims WHERE hospital_id IN ({ph}) AND year=? AND billed_drg='871'", (*ids, year)).fetchone()[0]


def median_los(conn, ids, year):
    ph = ",".join("?" * len(ids))
    vals = [r[0] for r in conn.execute(f"SELECT los FROM claims WHERE hospital_id IN ({ph}) AND year=? AND billed_drg='871'", (*ids, year))]
    return statistics.median(vals)


def main():
    conn = db.connect()
    ok = True
    print("== Riverside DRG 871 share ==")
    for y in (2023, 2024, 2025):
        s, n, k = share_871(conn, "H-RIV", y)
        print(f"  {y}: {s:.1%}  ({k} of {n} infection stays)")
    a, b = group_ids(conn, "A"), group_ids(conn, "B")
    for label, ids in (("Group A (community)", a), ("Group B (referral)", b)):
        for y in (2023, 2025):
            shares = [share_871(conn, h, y)[0] for h in ids]
            print(f"  {label} {y}: median {statistics.median(shares):.1%}, range {min(shares):.0%}-{max(shares):.0%}")
    print("== Among DRG 871 stays, 2025 ==")
    for label, ids in (("Riverside", ["H-RIV"]), ("Group A", a)):
        print(f"  {label}: transfers in {stat_871(conn, ids, 2025, 'AVG(transfer_in)'):.0%}, "
              f"ICU {stat_871(conn, ids, 2025, 'AVG(icu_days>0)'):.0%}, median stay {median_los(conn, ids, 2025)} days")
    for label, ids in (("Riverside", ["H-RIV"]), ("Group A", a)):
        ph = ",".join("?" * len(ids))
        r = conn.execute(f"SELECT AVG(member_risk) FROM claims WHERE hospital_id IN ({ph}) AND year=2025", ids).fetchone()[0]
        print(f"  {label}: average member risk score {r:.2f}")

    print("== Case quotes found in extracted page text ==")
    for case_id, key_json in conn.execute("SELECT case_id, json FROM answer_keys"):
        key = json.loads(key_json)
        chart = conn.execute("SELECT id, page_count FROM charts WHERE case_id=?", (case_id,)).fetchone()
        if chart is None:  # live-upload record: check the PDF in demo_uploads/ instead
            from app.charts import extract_pages
            from seed.run import UPLOAD_CASES, DEMO_UPLOADS_DIR
            upload = next(c for c in UPLOAD_CASES if c["case_id"] == case_id)
            pages = extract_pages(DEMO_UPLOADS_DIR / upload["upload_filename"])
            chart = {"page_count": f"{len(pages)} (upload)"}
        else:
            pages = [r[0] for r in conn.execute("SELECT text FROM chart_pages WHERE chart_id=? ORDER BY page", (chart["id"],))]
        norm = [" ".join(p.split()) for p in pages]
        missing = [q for q in key["must_find"] if not any(" ".join(q.split()) in p for p in norm)]
        status = "OK" if not missing else f"MISSING {missing}"
        ok &= not missing
        print(f"  {case_id}: {chart['page_count']} pages, {len(key['must_find'])} quotes -> {status}")
    print("PASS" if ok else "FAIL")


if __name__ == "__main__":
    main()
