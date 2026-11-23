"""Fixed calculations over the fictional claims for the billing-pattern review. No AI in this file.

Every metric has an id the pattern review agent must cite, so each statement on Maya's screen traces back to a
calculation anyone can re-run.
"""
import statistics

INFECTION = ("871", "872", "193", "194", "195", "177", "178", "179", "689", "690")
_PH = ",".join("?" * len(INFECTION))
SUBJECT, DRG, LATEST = "H-RIV", "871", 2025
QUESTION_ID = "Q-RIV-871"


def _share(conn, hid, year, quarter=None):
    q = f"SELECT SUM(billed_drg='871'), COUNT(*) FROM claims WHERE hospital_id=? AND year=? AND billed_drg IN ({_PH})"
    args = [hid, year, *INFECTION]
    if quarter:
        q += " AND quarter=?"
        args.append(quarter)
    k, n = conn.execute(q, args).fetchone()
    return (k or 0) / n if n else 0.0, k or 0, n


def _group(conn, g):
    return [r[0] for r in conn.execute("SELECT id FROM hospitals WHERE peer_group=? ORDER BY id", (g,))]


def _871_stat(conn, ids, expr):
    ph = ",".join("?" * len(ids))
    return conn.execute(f"SELECT {expr} FROM claims WHERE hospital_id IN ({ph}) AND year=? AND billed_drg='871'",
                        (*ids, LATEST)).fetchone()[0]


def _median_los(conn, ids):
    ph = ",".join("?" * len(ids))
    return statistics.median(r[0] for r in conn.execute(
        f"SELECT los FROM claims WHERE hospital_id IN ({ph}) AND year=? AND billed_drg='871'", (*ids, LATEST)))


def catalog(conn) -> dict:
    """All metrics for the Riverside DRG 871 question, keyed by metric id."""
    a, b = _group(conn, "A"), _group(conn, "B")
    m = {}

    def add(mid, label, value, unit="", note=""):
        m[mid] = {"id": mid, "label": label, "value": value, "unit": unit, "note": note}

    for y in (2023, 2024, 2025):
        s, k, n = _share(conn, SUBJECT, y)
        add(f"share_riverside_{y}", f"Riverside: share of infection stays billed as DRG 871, {y}", round(s * 100, 1), "%",
            f"{k} of {n} stays")
    for y in (2024, 2025):
        for q in (1, 2, 3, 4):
            s, k, n = _share(conn, SUBJECT, y, q)
            add(f"share_riverside_{y}q{q}", f"Riverside DRG 871 share, {y} Q{q}", round(s * 100, 1), "%", f"{k} of {n}")
    for label, ids, key in (("community peers (14)", a, "community"), ("referral peers (6)", b, "referral")):
        for y in (2023, 2025):
            shares = [_share(conn, h, y)[0] * 100 for h in ids]
            add(f"peer_median_{key}_{y}", f"Median DRG 871 share, {label}, {y}", round(statistics.median(shares), 1), "%",
                f"range {min(shares):.0f}-{max(shares):.0f}%")
    for who, ids in (("riverside", [SUBJECT]), ("community", a)):
        add(f"icu_rate_871_{who}", f"Share of {LATEST} DRG 871 stays with ICU days, {who}", round(_871_stat(conn, ids, "AVG(icu_days>0)") * 100, 1), "%")
        add(f"transfer_rate_871_{who}", f"Share of {LATEST} DRG 871 stays transferred in from another hospital, {who}",
            round(_871_stat(conn, ids, "AVG(transfer_in)") * 100, 1), "%")
        add(f"median_los_871_{who}", f"Median length of stay of {LATEST} DRG 871 stays, {who}", _median_los(conn, ids), "days")
        ph = ",".join("?" * len(ids))
        risk = conn.execute(f"SELECT AVG(member_risk) FROM claims WHERE hospital_id IN ({ph}) AND year=?", (*ids, LATEST)).fetchone()[0]
        add(f"member_risk_{who}", f"Average member risk score, {LATEST} stays, {who}", round(risk, 2))
    dup = conn.execute("SELECT COUNT(*) FROM (SELECT member_id, admit_date, COUNT(*) c FROM claims WHERE hospital_id=? "
                       "GROUP BY member_id, admit_date HAVING c > 1)", (SUBJECT,)).fetchone()[0]
    add("dq_duplicate_stays_riverside", "Riverside: possible duplicate stays (same member and admission date)", dup, "stays")
    mismatch = conn.execute(
        "SELECT COUNT(*) FROM claims c JOIN drg_weights w ON w.drg=c.billed_drg JOIN hospitals h ON h.id=c.hospital_id "
        "WHERE c.hospital_id=? AND ABS(c.paid_amount - w.weight*h.base_rate) > 1", (SUBJECT,)).fetchone()[0]
    add("dq_payment_mismatch_riverside", "Riverside: claims whose paid amount does not match the billed DRG's payment", mismatch, "claims")
    # Fixed comparison sentences, so direction is never left to the model to work out.
    for base in ("icu_rate_871", "transfer_rate_871", "median_los_871", "member_risk"):
        r, c = m[f"{base}_riverside"], m[f"{base}_community"]
        word = "higher" if r["value"] > c["value"] else "lower" if r["value"] < c["value"] else "the same"
        unit = r["unit"] if r["unit"] == "%" else (" " + r["unit"] if r["unit"] else "")
        sentence = f"Riverside {word} than community peers: {r['value']}{unit} vs {c['value']}{unit}"
        r["note"] = (r["note"] + "; " if r["note"] else "") + sentence
        c["note"] = (c["note"] + "; " if c["note"] else "") + sentence
    for y in (2023, 2025):
        r = m[f"share_riverside_{y}"]["value"]
        for key in ("community", "referral"):
            p = m[f"peer_median_{key}_{y}"]
            p["note"] += f"; Riverside {y}: {r}% ({'higher' if r > p['value'] else 'lower'} than this median)"
    crit = conn.execute("SELECT sepsis_criteria FROM contracts WHERE hospital_id=?", (SUBJECT,)).fetchone()[0]
    add("contract_sepsis_criteria_riverside", "Riverside contract: sepsis criteria specified", crit)
    return m


def sample_candidates(conn, limit=20):
    """Targeted (not statistical) sample: short stays, no ICU, not transferred in, discharged home.
    The three stays with records in the demo (Lee, Patel, Nguyen) come first."""
    rows = conn.execute(
        "SELECT cl.id, cl.admit_date, cl.los, cl.paid_amount, cs.id AS case_id, cs.patient_name "
        "FROM claims cl LEFT JOIN cases cs ON cs.claim_id = cl.id "
        "WHERE cl.hospital_id=? AND cl.year=? AND cl.billed_drg='871' AND cl.los<=4 AND cl.icu_days=0 "
        "AND cl.transfer_in=0 AND cl.discharge_status='home' "
        "ORDER BY (cs.id IS NULL), cl.admit_date DESC LIMIT ?", (SUBJECT, LATEST, limit)).fetchall()
    eligible = conn.execute(
        "SELECT COUNT(*) FROM claims WHERE hospital_id=? AND year=? AND billed_drg='871' AND los<=4 AND icu_days=0 "
        "AND transfer_in=0 AND discharge_status='home'", (SUBJECT, LATEST)).fetchone()[0]
    return [dict(r) for r in rows], eligible


def sensitivity(conn, shares=(0, 25, 50), diffs=(3000, 6000)):
    """Hypothetical only: stays above the referral-peer rate x share regrouped x average difference."""
    m = catalog(conn)
    _, k, n = _share(conn, SUBJECT, LATEST)
    referral = m["peer_median_referral_2025"]["value"] / 100
    above = round(k - referral * n)
    return {"stays": n, "billed_871": k, "referral_rate": round(referral * 100, 1), "above_peer_rate": above,
            "rows": [{"share": s, "values": [round(above * s / 100 * d) for d in diffs]} for s in shares], "diffs": list(diffs)}
