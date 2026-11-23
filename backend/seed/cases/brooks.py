"""Case E: routine pre-payment claim at a hospital whose contract specifies Sepsis-3. FICTIONAL.

Change in SOFA is exactly 2 (respiratory), which sits right at the threshold.
"""

CASE = {
    "case_id": "CASE-BROOKS",
    "patient_name": "Thomas Brooks",
    "age": 69,
    "sex": "M",
    "mrn": "LM-0017741",
    "hospital_id": "H-LAK",
    "source": "routine",
    "source_detail": "Pre-payment selection rule: high-value DRG 871 claim",
    "claim": {
        "id": "CLM-LAK-2025-CASE05", "year": 2025, "quarter": 4, "admit_date": "2025-11-05",
        "discharge_date": "2025-11-10", "los": 5, "billed_drg": "871", "icu_days": 1, "transfer_in": 0,
        "discharge_status": "home", "member_risk": 1.10,
        "principal_dx": "A41.9",
        "secondary_dx": [
            {"code": "J18.9", "poa": "Y", "desc": "Pneumonia, unspecified organism"},
            {"code": "J96.01", "poa": "Y", "desc": "Acute respiratory failure with hypoxia"},
            {"code": "I10", "poa": "Y", "desc": "Essential (primary) hypertension"},
        ],
    },
    "sections": [
        ("Emergency Department Physician Note", """
<p><b>Date/time:</b> 11/05/2025 19:05 &nbsp; <b>Author:</b> E. Walsh, MD (Emergency Medicine)</p>
<p><b>Chief complaint:</b> Shortness of breath and fever for 2 days.</p>
<p><b>History:</b> 69-year-old man with hypertension. Increasing shortness of breath, fever and cough. Does not use oxygen at home. No history of lung disease. Never smoker.</p>
<p><b>Initial vital signs (19:10):</b> Temp 38.8 C, HR 108, BP 132/80, RR 28, SpO2 86% on room air.</p>
<p><b>Exam:</b> Alert and oriented x3. Using accessory muscles. Diffuse crackles on the left.</p>
<p><b>Data:</b> Arterial blood gas on 4 L nasal cannula (FiO2 about 0.36) at 19:40: pH 7.44, PaCO2 34, PaO2 78 mmHg. Lactate 1.8 mmol/L. WBC 16.4. Chest X-ray: left lower and lingular consolidation.</p>
<p><b>Assessment:</b> Sepsis due to left-sided pneumonia with acute hypoxic respiratory failure.</p>
"""),
        ("History and Physical", """
<p><b>Date/time:</b> 11/05/2025 22:30 &nbsp; <b>Author:</b> H. Silva, MD (Critical Care)</p>
<p><b>Past medical history:</b> Hypertension. No known lung, kidney, liver or blood disorders. No home oxygen.</p>
<p><b>Baseline labs:</b> Creatinine 0.9 mg/dL on 06/10/2025 (outside laboratory report scanned into this record, page 7).</p>
<p><b>Assessment:</b> Acute hypoxic respiratory failure due to pneumonia; PaO2 to FiO2 ratio about 217 on 4 L nasal cannula. Admitted to ICU for close respiratory monitoring.</p>
<p><b>Plan:</b> Ceftriaxone and azithromycin. High-flow oxygen available if needed. Repeat blood gas in the morning.</p>
"""),
        ("ICU Progress Note, Hospital Day 2", """
<p><b>Date/time:</b> 11/06/2025 08:45 &nbsp; <b>Author:</b> H. Silva, MD</p>
<p><b>Interval:</b> Remained on 4 L nasal cannula overnight; did not require high-flow oxygen or ventilation. Blood pressure normal throughout, no vasopressors.</p>
<p><b>Arterial blood gas 06:00:</b> PaO2 82 mmHg on 4 L nasal cannula (FiO2 about 0.36); ratio about 228.</p>
<p><b>Labs:</b> Creatinine 1.0 mg/dL. Platelets 230. Bilirubin 0.5.</p>
<p><b>Plan:</b> Transfer to floor, wean oxygen as tolerated.</p>
"""),
        ("Nursing Notes", """
<p><b>11/05/2025 23:00 (ICU):</b> Alert and oriented x4. 4 L nasal cannula, SpO2 93%.</p>
<p><b>11/06/2025 12:00 (Floor):</b> Alert and oriented x4. 3 L nasal cannula.</p>
<p><b>11/08/2025 08:00:</b> Alert and oriented x4. 1 L nasal cannula.</p>
<p><b>11/09/2025 08:00:</b> Alert and oriented x4. Room air, SpO2 94%.</p>
"""),
        ("Vital Signs Flowsheet", """
<table>
<tr><th>Date/time</th><th>Temp C</th><th>HR</th><th>BP</th><th>MAP</th><th>RR</th><th>SpO2</th><th>O2</th></tr>
<tr><td>11/05 19:10</td><td>38.8</td><td>108</td><td>132/80</td><td>97</td><td>28</td><td>86%</td><td>Room air</td></tr>
<tr><td>11/05 19:30</td><td>38.6</td><td>104</td><td>128/78</td><td>95</td><td>26</td><td>92%</td><td>4 L NC</td></tr>
<tr><td>11/06 06:00</td><td>37.9</td><td>96</td><td>126/76</td><td>93</td><td>22</td><td>93%</td><td>4 L NC</td></tr>
<tr><td>11/07 08:00</td><td>37.3</td><td>88</td><td>130/78</td><td>95</td><td>20</td><td>94%</td><td>2 L NC</td></tr>
<tr><td>11/09 08:00</td><td>36.9</td><td>80</td><td>128/76</td><td>93</td><td>16</td><td>94%</td><td>Room air</td></tr>
</table>
"""),
        ("Laboratory Results", """
<table>
<tr><th>Date/time</th><th>PaO2 mmHg</th><th>FiO2</th><th>Lactate mmol/L</th><th>Creatinine mg/dL</th><th>Platelets K/uL</th><th>Bilirubin mg/dL</th></tr>
<tr><td>11/05 19:40</td><td>78</td><td>0.36</td><td>1.8</td><td>1.0</td><td>236</td><td>0.6</td></tr>
<tr><td>11/06 06:00</td><td>82</td><td>0.36</td><td>-</td><td>1.0</td><td>230</td><td>0.5</td></tr>
<tr><td>11/08 06:00</td><td>-</td><td>-</td><td>-</td><td>0.9</td><td>244</td><td>-</td></tr>
</table>
"""),
        ("Outside Records", """
<p><b>Outside laboratory report (scanned)</b> &nbsp; Ordering clinic: Lakeview Internal Medicine (fictional)</p>
<p>Collection date: 06/10/2025. Creatinine 0.9 mg/dL (reference 0.7 to 1.3). Platelets 240 K/uL.</p>
"""),
        ("Discharge Summary", """
<p><b>Admission:</b> 11/05/2025 &nbsp; <b>Discharge:</b> 11/10/2025 &nbsp; <b>Author:</b> H. Silva, MD</p>
<p><b>Discharge diagnoses:</b> Sepsis due to left-sided pneumonia; acute hypoxic respiratory failure, resolved; hypertension.</p>
<p><b>Hospital course:</b> Required 4 L nasal cannula oxygen with PaO2 to FiO2 ratio about 217 on admission; no high-flow oxygen or ventilation. Weaned to room air by day 5. Kidney function, platelets, bilirubin and blood pressure remained normal.</p>
<p><b>Disposition:</b> Home. No home oxygen needed.</p>
"""),
    ],
    "answer_key": {
        "expected_conclusion": "demonstrated",
        "expected_sofa_change_at_least": 2,
        "expected_sofa_change_at_most": 2,
        "must_find": ["PaO2 78 mmHg", "Does not use oxygen at home", "Creatinine 0.9 mg/dL on 06/10/2025"],
        "expected_gaps": ["FiO2 on nasal cannula is an estimate (about 0.36), so the ratio is approximate; the change sits exactly at the threshold"],
        "expected_contradictions": [],
        "coding_note": "Contract specifies Sepsis-3. Respiratory SOFA 2 (PaO2/FiO2 ~217, below 300, without ventilatory support) from a room-air home baseline; other systems 0. Change = 2, at threshold. J96.01 documented with blood gas. Coder validates.",
    },
}
