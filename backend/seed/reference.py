"""Reference data: hospitals, contracts, provider-relations notes, DRG titles and weights.

Everything here is fictional. DRG titles are from the CMS MS-DRG v43.0 Definitions Manual;
the weights are APPROXIMATE and ILLUSTRATIVE, not the official FY2026 relative weights.
"""

# id, name, beds, teaching, referral_center, peer_group, base_rate
HOSPITALS = [
    ("H-RIV", "Riverside General Hospital", 300, 0, 1, "subject", 7200),
    # Group A: community, non-teaching, similar size
    ("H-LAK", "Lakeside Medical Center", 280, 0, 0, "A", 7050),
    ("H-CED", "Cedar Valley Medical Center", 260, 0, 0, "A", 6980),
    ("H-PRA", "Prairie View Hospital", 240, 0, 0, "A", 6900),
    ("H-HAR", "Harbor Point Hospital", 310, 0, 0, "A", 7150),
    ("H-OAK", "Oakridge Community Hospital", 220, 0, 0, "A", 6850),
    ("H-SUM", "Summit Ridge Medical Center", 290, 0, 0, "A", 7100),
    ("H-WIL", "Willow Creek Hospital", 250, 0, 0, "A", 6950),
    ("H-BRK", "Brookfield Regional Hospital", 330, 0, 0, "A", 7180),
    ("H-MAP", "Maple Grove Medical Center", 270, 0, 0, "A", 7000),
    ("H-STO", "Stonebridge Hospital", 230, 0, 0, "A", 6880),
    ("H-GRV", "Greenvale Community Hospital", 210, 0, 0, "A", 6820),
    ("H-NOR", "Northgate Medical Center", 300, 0, 0, "A", 7120),
    ("H-SIL", "Silver Lake Hospital", 260, 0, 0, "A", 6970),
    ("H-ASH", "Ashford Valley Hospital", 240, 0, 0, "A", 6910),
    # Group B: regional referral hospitals
    ("H-MET", "Metro Regional Medical Center", 420, 0, 1, "B", 7400),
    ("H-UNI", "Unity Regional Hospital", 380, 0, 1, "B", 7350),
    ("H-CRE", "Crestview Regional Medical Center", 400, 0, 1, "B", 7380),
    ("H-VAL", "Valley Regional Hospital", 360, 0, 1, "B", 7300),
    ("H-HIG", "Highland Regional Medical Center", 440, 0, 1, "B", 7450),
    ("H-BAY", "Bayshore Regional Hospital", 390, 0, 1, "B", 7320),
]
REGION = "Central region (fictional)"

CONTRACTS = {
    "H-RIV": ("silent",
              "Agreement references MS-DRG grouping and gives the plan audit and medical-record rights. "
              "It does not specify which clinical criteria apply when validating sepsis. "
              "Record request limits and look-back period: not stated in this summary (open question)."),
    "H-LAK": ("Sepsis-3",
              "Agreement references MS-DRG grouping. Clinical validation of sepsis uses Sepsis-3 criteria "
              "(suspected infection plus an acute change in total SOFA score of 2 points or more). "
              "Up to 2% of paid inpatient claims per quarter may be requested for review."),
    "H-CED": ("Sepsis-3", "MS-DRG grouping. Sepsis-3 criteria apply to clinical validation. Record requests limited to 50 per quarter."),
    "H-HAR": ("Sepsis-3", "MS-DRG grouping. Sepsis-3 criteria apply. 12-month look-back for post-payment review."),
    "H-SUM": ("silent", "MS-DRG grouping. No clinical criteria specified. Disputes go to a joint clinical review committee before formal appeal."),
    "H-BRK": ("Sepsis-3", "MS-DRG grouping. Sepsis-3 criteria apply. Pre-payment review requires 30 days' written notice."),
    "H-MAP": ("silent", "MS-DRG grouping. No clinical criteria specified. 18-month look-back."),
    "H-NOR": ("Sepsis-3", "MS-DRG grouping. Sepsis-3 criteria apply. Record requests limited to 40 per quarter."),
    "H-MET": ("Sepsis-3", "MS-DRG grouping with outlier provisions. Sepsis-3 criteria apply."),
    "H-UNI": ("silent", "MS-DRG grouping with outlier provisions. No clinical criteria specified."),
    "H-CRE": ("Sepsis-3", "MS-DRG grouping. Sepsis-3 criteria apply. Joint review committee for clinical disputes."),
    "H-HIG": ("silent", "MS-DRG grouping. No clinical criteria specified. Contract renewal due 2026."),
}
DEFAULT_CONTRACT = ("silent", "Agreement references MS-DRG grouping. No sepsis clinical criteria specified. Standard audit rights.")

NOTES = [
    ("H-RIV", "Provider relations", "2024-01-15",
     "Riverside General launched a clinical documentation integrity (CDI) program in January 2024 with an external vendor. "
     "Stated focus areas: sepsis, malnutrition and acute respiratory failure documentation."),
    ("H-RIV", "Provider relations", "2023-06-02",
     "Riverside General is the regional referral hospital for Pine Hollow, Mill Creek and Elmwood community hospitals "
     "and accepts their transfers for higher-acuity inpatient care."),
    ("H-RIV", "Contract summary", "2022-03-01", CONTRACTS["H-RIV"][1]),
    ("H-RIV", "Provider relations", "2025-02-20",
     "No changes to Riverside's ICU bed count reported in 2024 or 2025. No new service lines reported."),
    ("H-RIV", "Provider relations", "2024-09-12",
     "Quarterly joint operating meeting. Riverside raised slow prior-authorization turnaround for imaging; no billing topics discussed."),
    ("H-RIV", "Network management", "2025-06-30",
     "Riverside added two hospitalists and extended weekend case management coverage."),
    # other hospitals: mostly routine, some relevant to other patterns
    ("H-LAK", "Contract summary", "2023-01-01", CONTRACTS["H-LAK"][1]),
    ("H-LAK", "Provider relations", "2025-04-08", "Lakeside opened a 12-bed observation unit in April 2025."),
    ("H-CED", "Provider relations", "2024-11-19", "Cedar Valley switched electronic health record vendors in October 2024; claim submission delays expected for one quarter."),
    ("H-PRA", "Network management", "2025-01-15", "Prairie View contract renewed for three years with no material changes."),
    ("H-HAR", "Provider relations", "2024-05-02", "Harbor Point began a CDI program focused on heart failure and malnutrition documentation."),
    ("H-OAK", "Provider relations", "2025-03-21", "Oakridge reports nursing staffing shortages; elective surgery volume reduced."),
    ("H-SUM", "Payment integrity", "2024-08-07", "Prior review of Summit Ridge DRG 291 (heart failure) closed with no findings; pattern explained by an aging member population."),
    ("H-WIL", "Provider relations", "2025-07-10", "Willow Creek joined the Central Health System; billing office consolidation planned for 2026."),
    ("H-BRK", "Network management", "2024-12-03", "Brookfield added a stroke center certification."),
    ("H-MAP", "Provider relations", "2025-05-28", "Maple Grove requested education on the plan's records request portal."),
    ("H-GRV", "Payment integrity", "2025-02-11", "Greenvale DRG 640 (nutrition and metabolic disorders) share rose in 2024; under analyst review."),
    ("H-NOR", "Provider relations", "2024-10-22", "Northgate disputes the plan's readmission policy; escalated to contracting."),
    ("H-SIL", "Network management", "2025-08-14", "Silver Lake contract renewal negotiations started."),
    ("H-ASH", "Provider relations", "2024-06-18", "Ashford Valley serves an older rural population; high skilled-nursing discharge rate is long-standing."),
    ("H-MET", "Provider relations", "2023-11-30", "Metro Regional is a level II trauma center and accepts transfers from eight community hospitals."),
    ("H-UNI", "Payment integrity", "2025-09-02", "Unity Regional short-stay inpatient admissions flagged for observation-status review."),
    ("H-VAL", "Network management", "2025-03-03", "Valley Regional opened a new cardiac catheterization lab."),
    ("H-BAY", "Provider relations", "2024-07-25", "Bayshore Regional CDI program in place since 2021."),
]

# drg, title (v43.0), approx weight, family
DRGS = [
    ("871", "Septicemia or Severe Sepsis without MV >96 Hours with MCC", 1.90, "sepsis"),
    ("872", "Septicemia or Severe Sepsis without MV >96 Hours without MCC", 1.03, "sepsis"),
    ("193", "Simple Pneumonia and Pleurisy with MCC", 1.30, "pneumonia"),
    ("194", "Simple Pneumonia and Pleurisy with CC", 0.90, "pneumonia"),
    ("195", "Simple Pneumonia and Pleurisy without CC/MCC", 0.70, "pneumonia"),
    ("177", "Respiratory Infections and Inflammations with MCC", 1.75, "respiratory_infection"),
    ("178", "Respiratory Infections and Inflammations with CC", 1.20, "respiratory_infection"),
    ("179", "Respiratory Infections and Inflammations without CC/MCC", 0.88, "respiratory_infection"),
    ("689", "Kidney and Urinary Tract Infections with MCC", 1.10, "kidney_uti"),
    ("690", "Kidney and Urinary Tract Infections without MCC", 0.78, "kidney_uti"),
    # other inpatient stays (not part of the sepsis question)
    ("064", "Intracranial Hemorrhage or Cerebral Infarction with MCC", 1.80, "stroke"),
    ("065", "Intracranial Hemorrhage or Cerebral Infarction with CC or tPA in 24 Hours", 1.10, "stroke"),
    ("066", "Intracranial Hemorrhage or Cerebral Infarction without CC/MCC", 0.85, "stroke"),
    ("189", "Pulmonary Edema and Respiratory Failure", 1.15, "respiratory_failure"),
    ("190", "Chronic Obstructive Pulmonary Disease with MCC", 1.10, "copd"),
    ("191", "Chronic Obstructive Pulmonary Disease with CC", 0.90, "copd"),
    ("192", "Chronic Obstructive Pulmonary Disease without CC/MCC", 0.72, "copd"),
    ("291", "Heart Failure and Shock with MCC", 1.30, "heart_failure"),
    ("292", "Heart Failure and Shock with CC", 0.88, "heart_failure"),
    ("293", "Heart Failure and Shock without CC/MCC", 0.65, "heart_failure"),
    ("377", "Gastrointestinal Hemorrhage with MCC", 1.65, "gi_bleed"),
    ("378", "Gastrointestinal Hemorrhage with CC", 0.98, "gi_bleed"),
    ("392", "Esophagitis, Gastroenteritis and Miscellaneous Digestive Disorders without MCC", 0.75, "digestive"),
    ("470", "Major Hip and Knee Joint Replacement or Reattachment of Lower Extremity without MCC", 1.90, "joint_replacement"),
    ("640", "Miscellaneous Disorders of Nutrition, Metabolism, Fluids and Electrolytes with MCC", 1.15, "metabolic"),
    ("641", "Miscellaneous Disorders of Nutrition, Metabolism, Fluids and Electrolytes without MCC", 0.75, "metabolic"),
    ("682", "Renal Failure with MCC", 1.45, "renal_failure"),
    ("683", "Renal Failure with CC", 0.90, "renal_failure"),
    ("684", "Renal Failure without CC/MCC", 0.62, "renal_failure"),
]
INFECTION_DRGS = ("871", "872", "193", "194", "195", "177", "178", "179", "689", "690")
