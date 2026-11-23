"""Generate fictional Northstar Medicare Advantage inpatient claims for infection-related DRGs.

Calibrated with exact counts (not just random draws) so the computed numbers match the scenario:
- Riverside DRG 871 share: 22% (2023) -> 29% (2024) -> 38% (2025), rise starting Q3 2024
- Group A (community peers) 2025 median 18%, range 12-31%; group B (referral) median 24%
- Among DRG 871 stays (2025): transfers in 14% vs 5%; ICU 21% vs 39%; median stay 4 vs 6 days
- Member risk score (all infection stays): Riverside ~1.18 vs group A ~1.05
"""
import json
import random
from datetime import date, timedelta

SEED = 20251123
YEARS = [2023, 2024, 2025]

# 2025 DRG 871 shares; earlier years drift down by ~1 point a year for peers
GROUP_A_2025 = {"H-LAK": 0.18, "H-CED": 0.12, "H-PRA": 0.13, "H-HAR": 0.14, "H-OAK": 0.15, "H-SUM": 0.16,
                "H-WIL": 0.17, "H-BRK": 0.18, "H-MAP": 0.19, "H-STO": 0.20, "H-GRV": 0.22, "H-NOR": 0.24,
                "H-SIL": 0.27, "H-ASH": 0.31}
GROUP_B_2025 = {"H-MET": 0.21, "H-UNI": 0.22, "H-CRE": 0.23, "H-VAL": 0.25, "H-HIG": 0.26, "H-BAY": 0.29}
# Riverside by quarter (CDI program starts Jan 2024; rise begins two quarters later)
RIVERSIDE_Q = {2023: [0.22, 0.22, 0.22, 0.22], 2024: [0.22, 0.23, 0.33, 0.38], 2025: [0.38, 0.38, 0.38, 0.38]}

# Riverside 2025: 1,196 generated stays + 4 case claims (all DRG 871) = 1,200 stays, 456 DRG 871
RIVERSIDE_N = {2023: 1150, 2024: 1180, 2025: 1196}
RIVERSIDE_2025_GENERATED_871 = 452

# mix of the non-871 stays
OTHER_MIX = [("872", 0.13), ("193", 0.08), ("194", 0.15), ("195", 0.11), ("177", 0.05), ("178", 0.07),
             ("179", 0.05), ("689", 0.13), ("690", 0.23)]

PRINCIPAL = {"871": ("A41.9", "Sepsis, unspecified organism"), "872": ("A41.9", "Sepsis, unspecified organism"),
             "193": ("J18.9", "Pneumonia, unspecified organism"), "194": ("J18.9", "Pneumonia, unspecified organism"),
             "195": ("J18.9", "Pneumonia, unspecified organism"), "177": ("J15.9", "Unspecified bacterial pneumonia"),
             "178": ("J15.9", "Unspecified bacterial pneumonia"), "179": ("J15.9", "Unspecified bacterial pneumonia"),
             "689": ("N39.0", "Urinary tract infection, site not specified"),
             "690": ("N39.0", "Urinary tract infection, site not specified")}
COMMON_SECONDARY = [("I10", "Essential (primary) hypertension"), ("E11.9", "Type 2 diabetes mellitus without complications"),
                    ("E78.5", "Hyperlipidemia, unspecified"), ("N18.30", "Chronic kidney disease, stage 3 unspecified"),
                    ("J44.9", "Chronic obstructive pulmonary disease, unspecified"), ("E87.1", "Hypo-osmolality and hyponatremia")]
SEPSIS_SOURCES = [("J18.9", "Pneumonia, unspecified organism"), ("N39.0", "Urinary tract infection, site not specified")]
MCC_LIKE = [("R65.20", "Severe sepsis without septic shock"), ("R65.21", "Severe sepsis with septic shock"),
            ("J96.01", "Acute respiratory failure with hypoxia"), ("G93.41", "Metabolic encephalopathy"),
            ("E43", "Unspecified severe protein-calorie malnutrition")]
STATUSES = [("home", 0.58), ("home_health", 0.14), ("skilled_nursing", 0.19), ("transfer_out", 0.03), ("expired", 0.06)]


def _weighted(rng, items):
    r, acc = rng.random(), 0.0
    for value, w in items:
        acc += w
        if r <= acc:
            return value
    return items[-1][0]


def _exact_flags(rng, n, rate):
    k = round(n * rate)
    flags = [1] * k + [0] * (n - k)
    rng.shuffle(flags)
    return flags


def _los(rng, center):
    # integer stays around a target median
    spread = [center - 2, center - 1, center - 1, center, center, center, center + 1, center + 1, center + 2, center + 4]
    return max(1, rng.choice(spread))


def _date_in_quarter(rng, year, quarter):
    start = date(year, 3 * (quarter - 1) + 1, 1)
    return start + timedelta(days=rng.randrange(0, 89))


def _shares(hid, peer_group, year):
    if hid == "H-RIV":
        return RIVERSIDE_Q[year]
    base = (GROUP_A_2025 if peer_group == "A" else GROUP_B_2025)[hid]
    s = round(base - 0.005 * (2025 - year), 3)
    return [s, s, s, s]


def generate(hospitals):
    rng = random.Random(SEED)
    rows, counter = [], 0
    for hid, _name, _beds, _teach, _ref, peer_group, base_rate in hospitals:
        is_riv = hid == "H-RIV"
        for year in YEARS:
            n_year = RIVERSIDE_N[year] if is_riv else (rng.randint(500, 1300) if peer_group == "A" else rng.randint(1300, 1900))
            per_q = [n_year // 4 + (1 if q < n_year % 4 else 0) for q in range(4)]
            shares = _shares(hid, peer_group, year)
            stays = []
            for q in range(4):
                n_q = per_q[q]
                k871 = round(n_q * shares[q])
                drgs = ["871"] * k871 + [_weighted(rng, OTHER_MIX) for _ in range(n_q - k871)]
                stays.extend((q + 1, d) for d in drgs)
            if is_riv and year == 2025:  # pin the exact 2025 total
                idx871 = [i for i, (_, d) in enumerate(stays) if d == "871"]
                diff = len(idx871) - RIVERSIDE_2025_GENERATED_871
                for i in idx871[:max(0, diff)]:
                    stays[i] = (stays[i][0], "872")
            # attributes for DRG 871 stays, with exact rates
            n871 = sum(1 for _, d in stays if d == "871")
            if is_riv:
                icu_rate, xfer_rate, los_center = 0.21, 0.14, 4
            elif peer_group == "A":
                icu_rate, xfer_rate, los_center = 0.39, 0.05, 6
            else:
                icu_rate, xfer_rate, los_center = 0.42, 0.12, 6
            icu_flags = iter(_exact_flags(rng, n871, icu_rate))
            xfer_flags = iter(_exact_flags(rng, n871, xfer_rate))
            risk_mean = 1.18 if is_riv else (1.05 if peer_group == "A" else 1.15)
            for quarter, drg in stays:
                counter += 1
                admit = _date_in_quarter(rng, year, quarter)
                if drg == "871":
                    los = _los(rng, los_center)
                    icu_days = rng.randint(1, min(4, los)) if next(icu_flags) else 0
                    transfer = next(xfer_flags)
                else:
                    los = _los(rng, 4)
                    icu_days = 1 if rng.random() < 0.08 else 0
                    transfer = 1 if rng.random() < (0.06 if is_riv else 0.03) else 0
                principal = PRINCIPAL[drg]
                secondary = []
                if drg in ("871", "872"):
                    secondary.append(rng.choice(SEPSIS_SOURCES))
                if drg in ("871", "193", "177", "689"):
                    secondary.append(rng.choice(MCC_LIKE[2:] if drg != "871" else MCC_LIKE))
                secondary += rng.sample(COMMON_SECONDARY, rng.randint(1, 3))
                sec_json = json.dumps([{"code": c, "poa": "Y", "desc": d} for c, d in secondary])
                weight = {"871": 1.90, "872": 1.03, "193": 1.30, "194": 0.90, "195": 0.70, "177": 1.75,
                          "178": 1.20, "179": 0.88, "689": 1.10, "690": 0.78}[drg]
                rows.append((
                    f"CLM-{hid[2:]}-{year}-{counter:06d}", hid, f"M{rng.randint(10_000_000, 99_999_999)}", year, quarter,
                    admit.isoformat(), (admit + timedelta(days=los)).isoformat(), los, drg, principal[0], sec_json,
                    icu_days, transfer, _weighted(rng, STATUSES), round(weight * base_rate, 2),
                    round(max(0.45, rng.gauss(risk_mean, 0.32)), 3), 0,
                ))
    return rows


# ---------------------------------------------------------------- other inpatient stays
# Separate random stream, so adding these never changes the calibrated infection claims.
OTHER_FAMILIES = [
    # drg, share of other stays, principal dx (code, desc), typical stay
    ("291", 0.10, ("I50.23", "Acute on chronic systolic heart failure"), 5),
    ("292", 0.09, ("I50.33", "Acute on chronic diastolic heart failure"), 4),
    ("293", 0.04, ("I50.9", "Heart failure, unspecified"), 3),
    ("190", 0.05, ("J44.1", "COPD with acute exacerbation"), 5),
    ("191", 0.05, ("J44.1", "COPD with acute exacerbation"), 4),
    ("192", 0.04, ("J44.1", "COPD with acute exacerbation"), 3),
    ("189", 0.05, ("J96.01", "Acute respiratory failure with hypoxia"), 4),
    ("064", 0.03, ("I63.9", "Cerebral infarction, unspecified"), 6),
    ("065", 0.05, ("I63.9", "Cerebral infarction, unspecified"), 4),
    ("066", 0.03, ("I63.9", "Cerebral infarction, unspecified"), 3),
    ("377", 0.03, ("K92.2", "Gastrointestinal hemorrhage, unspecified"), 5),
    ("378", 0.04, ("K92.2", "Gastrointestinal hemorrhage, unspecified"), 3),
    ("392", 0.08, ("K52.9", "Noninfective gastroenteritis and colitis, unspecified"), 3),
    ("470", 0.12, ("M17.11", "Unilateral primary osteoarthritis, right knee"), 2),
    ("640", 0.04, ("E87.1", "Hypo-osmolality and hyponatremia"), 4),
    ("641", 0.06, ("E86.0", "Dehydration"), 3),
    ("682", 0.03, ("N17.9", "Acute kidney failure, unspecified"), 5),
    ("683", 0.04, ("N17.9", "Acute kidney failure, unspecified"), 4),
    ("684", 0.03, ("N17.9", "Acute kidney failure, unspecified"), 3),
]


# Patterns for other leads (fictional). Applied with their own random stream so nothing else moves.
HF = ("291", "292", "293")          # heart failure: with MCC / with CC / without
METABOLIC = ("640", "641")          # nutrition & metabolic: with MCC / without


def _signal_drg(srng, hid, year, quarter, drg):
    late = year == 2025 or (year == 2024 and quarter >= 3)
    if drg in HF:
        if hid == "H-HAR" and late:
            return _weighted(srng, [("291", 0.62), ("292", 0.28), ("293", 0.10)])
        if hid == "H-SUM":
            return _weighted(srng, [("291", 0.61), ("292", 0.29), ("293", 0.10)])
    if drg in METABOLIC and hid == "H-GRV" and year >= 2024:
        return "640" if srng.random() < (0.55 if year == 2024 else 0.66) else "641"
    return drg


def generate_other(hospitals, weights, start_counter=500_000):
    rng = random.Random(SEED + 1)
    srng = random.Random(SEED + 2)  # signals and readmissions
    mix = [(drg, share) for drg, share, _dx, _los in OTHER_FAMILIES]
    info = {drg: (dx, los) for drg, _share, dx, los in OTHER_FAMILIES}
    rows, counter = [], start_counter
    for hid, _name, _beds, _teach, _ref, peer_group, base_rate in hospitals:
        for year in YEARS:
            n = rng.randint(900, 2200) if peer_group != "B" else rng.randint(2200, 3400)
            if hid == "H-RIV":
                n = 1850
            risk_mean = 1.18 if hid == "H-RIV" else (1.05 if peer_group == "A" else 1.15)
            for _ in range(n):
                counter += 1
                drg = _weighted(rng, mix)
                quarter = rng.randint(1, 4)
                drg = _signal_drg(srng, hid, year, quarter, drg)
                (dx_code, _dx_desc), los_c = info[drg]
                admit = _date_in_quarter(rng, year, quarter)
                los = _los(rng, los_c)
                if hid == "H-UNI" and year == 2025 and srng.random() < 0.20:
                    los = 1  # very short inpatient stays
                secondary = rng.sample(COMMON_SECONDARY, rng.randint(1, 3))
                rows.append((
                    f"CLM-{hid[2:]}-{year}-{counter:06d}", hid, f"M{rng.randint(10_000_000, 99_999_999)}", year, quarter,
                    admit.isoformat(), (admit + timedelta(days=los)).isoformat(), los, drg, dx_code,
                    json.dumps([{"code": c, "poa": "Y", "desc": d} for c, d in secondary]),
                    1 if rng.random() < 0.07 else 0, 1 if rng.random() < 0.03 else 0, _weighted(rng, STATUSES),
                    round(weights[drg] * base_rate, 2), round(max(0.45, rng.gauss(risk_mean, 0.32)), 3), 0,
                ))
    # 30-day readmissions: a share of stays are followed by another stay for the same member at the same hospital.
    readmits = []
    for r in rows:
        hid, year = r[1], r[3]
        rate = 0.19 if (hid == "H-NOR" and year == 2025) else 0.11
        if srng.random() < rate:
            counter += 1
            discharge = date.fromisoformat(r[6])
            admit = discharge + timedelta(days=srng.randint(3, 27))
            if admit.year != year:
                continue
            drg = _weighted(srng, mix)
            (dx_code, _d), los_c = info[drg]
            los = _los(srng, los_c)
            base_rate = next(h[6] for h in hospitals if h[0] == hid)
            readmits.append((f"CLM-{hid[2:]}-{year}-{counter:06d}", hid, r[2], year, (admit.month - 1) // 3 + 1,
                             admit.isoformat(), (admit + timedelta(days=los)).isoformat(), los, drg, dx_code, r[10],
                             0, 0, _weighted(srng, STATUSES), round(weights[drg] * base_rate, 2), r[15], 0))
    return rows + readmits
