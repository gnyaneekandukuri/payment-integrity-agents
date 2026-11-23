"""Monitoring (detection) job: fixed rules over the plan's claims that produce leads. No AI in this file.

In production this would run on a schedule over governed data products and shared metric definitions; here it runs
over the fictional claims when the database is built. Each rule compares a hospital with its peer group (community
or referral hospitals) and flags it only when the gap is both large and material.
"""
import json
import statistics

YEAR = 2025
INFECTION = ("871", "872", "193", "194", "195", "177", "178", "179", "689", "690")

# A DRG shift = more stays coded at the highest-paying severity level within a family than peers.
DRG_SHIFTS = [
    {"top": "871", "family": INFECTION, "label": "Sepsis with a major complication (DRG 871)",
     "measure": "Share of infection-related stays billed as DRG 871"},
    {"top": "291", "family": ("291", "292", "293"), "label": "Heart failure with a major complication (DRG 291)",
     "measure": "Share of heart failure stays billed as DRG 291"},
    {"top": "640", "family": ("640", "641"), "label": "Nutrition/metabolic disorder with a major complication (DRG 640)",
     "measure": "Share of nutrition/metabolic stays billed as DRG 640"},
]

# Workflow state: in a real system this lives in the case-management tool, not in the detection output.
STATUS = {
    ("drg_shift", "H-RIV", "871"): ("new", None),
    ("drg_shift", "H-GRV", "640"): ("in_analysis", "Analyst review opened; targeted records review in progress."),
    ("drg_shift", "H-HAR", "291"): ("new", None),
    ("drg_shift", "H-SUM", "291"): ("closed_no_findings", "Prior review closed with no findings; pattern explained by an older member population (Aug 2024)."),
    ("short_stays", "H-UNI", None): ("records_requested", "Observation-status review: records requested for a sample of stays."),
    ("readmissions", "H-NOR", None): ("new", None),
}


def _peers(conn, hid):
    group = conn.execute("SELECT peer_group FROM hospitals WHERE id=?", (hid,)).fetchone()[0]
    group = "A" if group == "subject" else group
    return [r[0] for r in conn.execute("SELECT id FROM hospitals WHERE peer_group=? AND id<>?", (group, hid))]


def drg_share(conn, hid, top, family, year=YEAR, quarter=None):
    ph = ",".join("?" * len(family))
    q = f"SELECT SUM(billed_drg=?), COUNT(*) FROM claims WHERE hospital_id=? AND year=? AND billed_drg IN ({ph})"
    args = [top, hid, year, *family]
    if quarter:
        q += " AND quarter=?"
        args.append(quarter)
    k, n = conn.execute(q, args).fetchone()
    return (100.0 * (k or 0) / n if n else 0.0), (k or 0), n


def short_stay_rate(conn, hid, year=YEAR, quarter=None):
    q = "SELECT SUM(los<=1), COUNT(*) FROM claims WHERE hospital_id=? AND year=?"
    args = [hid, year]
    if quarter:
        q += " AND quarter=?"
        args.append(quarter)
    k, n = conn.execute(q, args).fetchone()
    return (100.0 * (k or 0) / n if n else 0.0), (k or 0), n


def readmission_rate(conn, hid, year=YEAR, quarter=None):
    q = ("SELECT COUNT(*), SUM(EXISTS (SELECT 1 FROM claims b WHERE b.member_id=a.member_id AND b.hospital_id=a.hospital_id "
         "AND b.admit_date > a.discharge_date AND julianday(b.admit_date) - julianday(a.discharge_date) <= 30)) "
         "FROM claims a WHERE a.hospital_id=? AND a.year=?")
    args = [hid, year]
    if quarter:
        q += " AND a.quarter=?"
        args.append(quarter)
    n, k = conn.execute(q, args).fetchone()
    return (100.0 * (k or 0) / n if n else 0.0), (k or 0), n


def compute(conn, lead_type, hid, params, year=YEAR, quarter=None):
    if lead_type == "drg_shift":
        return drg_share(conn, hid, params["top"], tuple(params["family"]), year, quarter)
    if lead_type == "short_stays":
        return short_stay_rate(conn, hid, year, quarter)
    return readmission_rate(conn, hid, year, quarter)


def _peer_median(conn, lead_type, hid, params, year=YEAR):
    return statistics.median(compute(conn, lead_type, p, params, year)[0] for p in _peers(conn, hid))


def detect(conn) -> list[dict]:
    hospitals = [r[0] for r in conn.execute("SELECT id FROM hospitals ORDER BY id")]
    found = []

    def consider(lead_type, hid, params, title, measure, rule, min_gap, min_ratio):
        value, k, n = compute(conn, lead_type, hid, params)
        peer = _peer_median(conn, lead_type, hid, params)
        if n < 100 or value - peer < min_gap or value < peer * min_ratio:
            return
        earlier = compute(conn, lead_type, hid, params, YEAR - 2)[0]
        key = (lead_type, hid, params.get("top"))
        status, note = STATUS.get(key, ("new", None))
        found.append({"lead_type": lead_type, "hospital_id": hid, "title": title, "measure": measure, "value": round(value, 1),
                      "peer_value": round(peer, 1), "earlier_value": round(earlier, 1), "unit": "%", "stays": k, "rule": rule,
                      "params": params, "status": status, "status_note": note})

    for hid in hospitals:
        for d in DRG_SHIFTS:
            consider("drg_shift", hid, {"top": d["top"], "family": list(d["family"])}, d["label"], d["measure"],
                     "Share at least 10 points and 1.25x above the peer median", 10, 1.25)
        consider("short_stays", hid, {}, "Very short inpatient stays (1 day or less)", "Share of inpatient stays of 1 day or less",
                 "Share at least 8 points and 1.8x above the peer median", 8, 1.8)
        consider("readmissions", hid, {}, "Readmissions within 30 days", "Share of stays followed by a readmission within 30 days",
                 "Rate at least 5 points above the peer median", 5, 1.0)
    return found


def write(conn, found):
    conn.execute("DELETE FROM leads")
    flagged = {"new": "2026-01-08", "in_analysis": "2025-10-07", "records_requested": "2025-11-04", "closed_no_findings": "2024-07-15"}
    order = sorted(found, key=lambda x: (x["status"] == "closed_no_findings", -len(x.get("detected_by", [])),
                                         -((x["value"] or 0) - (x["peer_value"] or 0))))
    for i, f in enumerate(order, start=1):
        lead_id = f"LEAD-{i:03d}"
        question = "Q-RIV-871" if (f["hospital_id"], f["params"].get("top")) == ("H-RIV", "871") and f["lead_type"] == "drg_shift" else None
        conn.execute("INSERT INTO leads VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                     (lead_id, f["lead_type"], f["hospital_id"], f["title"], f["measure"], f["value"], f["peer_value"],
                      f["earlier_value"], f["unit"], f["stays"] or 0, f.get("rule") or "", json.dumps(f["params"]), f["status"],
                      f["status_note"], flagged[f["status"]], question, json.dumps(f.get("detected_by", ["rule"])),
                      json.dumps(f.get("evidence", []))))
    conn.commit()


# ====================================================================================================================
# Detection methods that do not need anyone to name the pattern first.
#   1. Peer profiling: every DRG family with severity levels, every hospital: share billed at the highest level vs peers.
#   2. Change detection: each hospital's own quarterly history: a lasting step up (where and how big).
# ====================================================================================================================
from collections import defaultdict  # noqa: E402

FAMILY_LABEL = {"sepsis": "Sepsis", "pneumonia": "Simple pneumonia", "respiratory_infection": "Respiratory infection",
                "kidney_uti": "Kidney/urinary infection", "stroke": "Stroke", "copd": "COPD", "heart_failure": "Heart failure",
                "gi_bleed": "GI bleeding", "metabolic": "Nutrition/metabolic disorder", "renal_failure": "Renal failure"}
QUARTERS = [(y, q) for y in (2023, 2024, 2025) for q in (1, 2, 3, 4)]


def _lc(label):
    """Lower-case a label but keep acronyms (COPD, GI)."""
    return " ".join(w if w.isupper() else w.lower() for w in label.split())


def families(conn):
    """Severity families from the DRG table; the 'top' DRG is the highest-weight one in each family."""
    fam = defaultdict(list)
    for r in conn.execute("SELECT drg, family, weight, title FROM drg_weights WHERE family <> 'joint_replacement'"):
        fam[r["family"]].append((r["weight"], r["drg"], r["title"]))
    out = []
    for name, drgs in fam.items():
        if len(drgs) < 2:
            continue
        drgs.sort(reverse=True)
        top = drgs[0]
        out.append({"family": name, "top": top[1], "drgs": [d[1] for d in drgs],
                    "label": f"{FAMILY_LABEL.get(name, name)}: share at the highest severity (DRG {top[1]})",
                    "measure": f"Share of {_lc(FAMILY_LABEL.get(name, name))} stays billed as DRG {top[1]}"})
    return out


def peer_profiling(conn):
    found = []
    hospitals = [r[0] for r in conn.execute("SELECT id FROM hospitals")]
    for f in families(conn):
        for hid in hospitals:
            value, k, n = drg_share(conn, hid, f["top"], tuple(f["drgs"]))
            if n < 100:
                continue
            peer = statistics.median(drg_share(conn, p, f["top"], tuple(f["drgs"]))[0] for p in _peers(conn, hid))
            if value - peer >= 10 and value >= peer * 1.25:
                found.append({"key": ("drg_shift", hid, f["top"]), "method": "peer_profiling", "title": f["label"],
                              "measure": f["measure"], "value": round(value, 1), "peer_value": round(peer, 1), "stays": k,
                              "params": {"top": f["top"], "family": f["drgs"]},
                              "evidence": f"Peer profiling across all {len(families(conn))} severity families: {value:.1f}% vs peer median {peer:.1f}%"})
    return found


def _step(series):
    """Largest lasting step up: best split with at least 3 quarters each side."""
    best = None
    for k in range(3, len(series) - 2):
        pre, post = series[:k], series[k:]
        a, b = statistics.mean(pre), statistics.mean(post)
        if best is None or b - a > best[1] - best[0]:
            best = (a, b, k, min(post))
    return best


def change_detection(conn):
    found = []
    hospitals = [r[0] for r in conn.execute("SELECT id FROM hospitals")]
    series_defs = [("drg_shift", {"top": f["top"], "family": f["drgs"]}, f["label"], f["measure"]) for f in families(conn)]
    series_defs.append(("drg_shift", {"top": "871", "family": list(INFECTION)}, DRG_SHIFTS[0]["label"], DRG_SHIFTS[0]["measure"]))
    series_defs.append(("short_stays", {}, "Very short inpatient stays (1 day or less)", "Share of inpatient stays of 1 day or less"))
    for hid in hospitals:
        for lt, params, title, measure in series_defs:
            vals = [compute(conn, lt, hid, params, y, q)[0] for y, q in QUARTERS]
            a, b, k, post_min = _step(vals)
            if b - a >= 8 and b >= a * 1.25 and post_min >= a + 4:
                y, q = QUARTERS[k]
                found.append({"key": (lt, hid, params.get("top")), "method": "change_detection", "title": title, "measure": measure,
                              "value": round(b, 1), "peer_value": None, "stays": None, "params": params,
                              "evidence": f"Lasting step up from {y} Q{q}: average {a:.1f}% before vs {b:.1f}% after"})
    return found


def detect_all(conn):
    """Rules + peer profiling + change detection, merged into one lead per hospital and pattern."""
    merged = {}
    for f in detect(conn):
        key = (f["lead_type"], f["hospital_id"], f["params"].get("top"))
        if key[0] == "drg_shift" and key[2] == "871" and f["params"].get("family") == list(INFECTION):
            key = (key[0], key[1], "871")
        merged[key] = {**f, "detected_by": ["rule"], "evidence": [f"Rule: {f['rule']}"]}
    for f in peer_profiling(conn) + change_detection(conn):
        key = f["key"]
        if key in merged:
            if f["method"] not in merged[key]["detected_by"]:
                merged[key]["detected_by"].append(f["method"])
                merged[key]["evidence"].append(f["evidence"])
            continue
        if f["method"] == "change_detection":  # a shift alone still needs a peer comparison to show
            peer = _peer_median(conn, key[0], key[1], f["params"])
            value, k, _n = compute(conn, key[0], key[1], f["params"])
            f.update(value=round(value, 1), peer_value=round(peer, 1), stays=k)
        status, note = STATUS.get(key, ("new", None))
        merged[key] = {"lead_type": key[0], "hospital_id": key[1], "title": f["title"], "measure": f["measure"],
                       "value": f["value"], "peer_value": f["peer_value"],
                       "earlier_value": round(compute(conn, key[0], key[1], f["params"], YEAR - 2)[0], 1), "unit": "%",
                       "stays": f["stays"], "rule": "", "params": f["params"], "status": status, "status_note": note,
                       "detected_by": [f["method"]], "evidence": [f["evidence"]]}
    return list(merged.values())
