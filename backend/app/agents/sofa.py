"""Fixed SOFA calculation from cited evidence only. No AI in this file.

Thresholds follow the SOFA table in Singer et al., Sepsis-3 (JAMA 2016). Rules:
- A system with no cited value is 'not_documented' (never scored as 0 or normal).
- Baseline: a cited, SOURCED baseline value (dated result or report) is used; unsourced mentions are ignored. If no baseline value is cited and no pre-existing
  dysfunction is recorded, baseline is assumed 0 (Sepsis-3 assumption, labelled). If pre-existing
  dysfunction is recorded but no sourced baseline value, the system is 'baseline_uncertain'.
- Respiratory without PaO2/FiO2 is 'not_formally_assessable'.
- CNS without a GCS value: 'normal' mental status scores 0; 'altered' is 'not_formally_assessable'.
"""

SYSTEMS = ["respiratory", "coagulation", "liver", "cardiovascular", "cns", "renal"]


def _num(v):
    try:
        return float(str(v).replace(",", "").split()[0])
    except (ValueError, IndexError):
        return None


def score_measure(system: str, measure: str, value, extra: dict) -> int | None:
    m = (measure or "").lower()
    x = _num(value)
    if system == "renal" and "creatinine" in m and x is not None:
        return 0 if x < 1.2 else 1 if x < 2.0 else 2 if x < 3.5 else 3 if x < 5.0 else 4
    if system == "coagulation" and "platelet" in m and x is not None:
        return 0 if x >= 150 else 1 if x >= 100 else 2 if x >= 50 else 3 if x >= 20 else 4
    if system == "liver" and "bilirubin" in m and x is not None:
        return 0 if x < 1.2 else 1 if x < 2.0 else 2 if x < 6.0 else 3 if x < 12.0 else 4
    if system == "cns":
        if "gcs" in m and x is not None:
            return 0 if x >= 15 else 1 if x >= 13 else 2 if x >= 10 else 3 if x >= 6 else 4
        if "mental" in m and str(value).strip().lower() in ("normal", "alert and oriented", "baseline"):
            return 0
        return None
    if system == "cardiovascular":
        if "map" in m and x is not None:
            return 1 if x < 70 else 0
        if any(d in m for d in ("norepinephrine", "epinephrine")) and x is not None:
            return 3 if x <= 0.1 else 4
        if "dopamine" in m and x is not None:
            return 2 if x <= 5 else 3 if x <= 15 else 4
        if "dobutamine" in m:
            return 2
        return None
    if system == "respiratory":
        ratio = None
        if ("pf" in m or "pao2/fio2" in m or "ratio" in m) and x is not None:
            ratio = x
        elif "pao2" in m and x is not None and _num(extra.get("fio2")):
            ratio = x / _num(extra.get("fio2"))
        if ratio is None:
            return None
        supported = bool(extra.get("ventilatory_support"))
        if ratio >= 400:
            return 0
        if ratio >= 300:
            return 1
        if ratio >= 200 or not supported:
            return 2
        return 3 if ratio >= 100 else 4
    return None


def compute(evidence: list[dict]) -> dict:
    """evidence rows: id, system, measure, value, timepoint ('baseline'|'acute'), extra (dict), criterion."""
    result = {}
    for system in SYSTEMS:
        rows = [e for e in evidence if (e.get("system") or "").lower() == system]
        preexisting = [e for e in rows if e.get("criterion") == "preexisting_condition"]
        base_rows = [e for e in rows if e.get("timepoint") == "baseline" and e.get("criterion") != "preexisting_condition"]
        unsourced = [e for e in base_rows if (e.get("extra", {}).get("source_quality") or "").lower() != "sourced"]
        base_rows = [e for e in base_rows if e not in unsourced]  # only dated, documented baselines count
        scored_base = [(score_measure(system, e["measure"], e["value"], e.get("extra", {})), e) for e in base_rows]
        scored_base = [(s, e) for s, e in scored_base if s is not None]
        scored_acute = [(score_measure(system, e["measure"], e["value"], e.get("extra", {})), e) for e in rows
                        if e.get("timepoint") != "baseline" and e.get("criterion") != "preexisting_condition"]
        acute_known = [(s, e) for s, e in scored_acute if s is not None]
        acute_unknown = [e for s, e in scored_acute if s is None]
        ids = [e["id"] for e in rows]

        if not acute_known:
            if acute_unknown:
                status, detail = "not_formally_assessable", "values recorded but no scorable measurement (e.g. no PaO2/FiO2 or GCS)"
            else:
                status, detail = "not_documented", "no cited value for this system"
            result[system] = {"status": status, "baseline": None, "worst": None, "change": None, "detail": detail, "evidence_ids": ids}
            continue
        worst = max(s for s, _ in acute_known)
        if scored_base:
            baseline = min(s for s, _ in scored_base)
            status, detail = "scored", "baseline from a cited value"
        elif preexisting:
            extra_note = " (an unsourced baseline mention was found but cannot be used)" if unsourced else ""
            result[system] = {"status": "baseline_uncertain", "baseline": None, "worst": worst, "change": None,
                              "detail": "pre-existing dysfunction recorded but no sourced baseline value" + extra_note,
                              "evidence_ids": ids}
            continue
        else:
            baseline = 0
            status, detail = "scored", "baseline assumed 0 (no known pre-existing dysfunction; Sepsis-3 assumption)"
        result[system] = {"status": status, "baseline": baseline, "worst": worst, "change": max(0, worst - baseline),
                          "detail": detail, "evidence_ids": ids}

    change_total = sum(v["change"] for v in result.values() if v["status"] == "scored")
    return {
        "systems": result,
        "change_total": change_total,
        "threshold_met": change_total >= 2,
        "unscored_systems": [s for s, v in result.items() if v["status"] != "scored"],
        "note": "Threshold: acute change in total SOFA of 2 or more (Sepsis-3). Unscored systems are not assumed normal.",
    }
