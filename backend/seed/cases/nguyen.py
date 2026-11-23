"""Case D: clinical criteria demonstrated, but the coded MCC is weakly documented. FICTIONAL.

Shows that clinical review is separate from coding: supporting sepsis does not validate DRG 871.
"""

CASE = {
    "case_id": "CASE-NGUYEN",
    "patient_name": "Linh Nguyen",
    "age": 58,
    "sex": "F",
    "mrn": "RG-0062530",
    "hospital_id": "H-RIV",
    "source": "investigation_sample",
    "source_detail": "Targeted records review: Riverside General DRG 871 pattern",
    "claim": {
        "id": "CLM-RIV-2025-CASE04", "year": 2025, "quarter": 3, "admit_date": "2025-07-22",
        "discharge_date": "2025-07-25", "los": 3, "billed_drg": "871", "icu_days": 0, "transfer_in": 0,
        "discharge_status": "home", "member_risk": 0.94,
        "principal_dx": "A41.9",
        "secondary_dx": [
            {"code": "J18.9", "poa": "Y", "desc": "Pneumonia, unspecified organism"},
            {"code": "E43", "poa": "Y", "desc": "Unspecified severe protein-calorie malnutrition"},
            {"code": "N17.9", "poa": "Y", "desc": "Acute kidney failure, unspecified"},
            {"code": "D69.6", "poa": "Y", "desc": "Thrombocytopenia, unspecified"},
        ],
    },
    "sections": [
        ("Emergency Department Physician Note", """
<p><b>Date/time:</b> 07/22/2025 08:15 &nbsp; <b>Author:</b> M. Okafor, MD (Emergency Medicine)</p>
<p><b>Chief complaint:</b> Fever, cough and weakness for 4 days.</p>
<p><b>History:</b> 58-year-old woman, previously healthy, with 4 days of productive cough, fever and fatigue. Decreased appetite for about a week.</p>
<p><b>Initial vital signs (08:20):</b> Temp 39.0 C, HR 116, BP 88/52 (MAP 64), RR 24, SpO2 95% on room air.</p>
<p><b>Exam:</b> Alert and oriented x3. Thin. Crackles at the right base.</p>
<p><b>Data:</b> WBC 17.1. Lactate 2.6 mmol/L. Creatinine 1.5 mg/dL. Platelets 140. Chest X-ray: right middle and lower lobe infiltrates.</p>
<p><b>Plan:</b> Cultures, ceftriaxone and azithromycin, 1,500 mL lactated Ringer's. After fluids, BP 104/62 (MAP 76) at 10:30. Admit to medicine.</p>
"""),
        ("History and Physical", """
<p><b>Date/time:</b> 07/22/2025 12:10 &nbsp; <b>Author:</b> P. Ramos, MD (Hospital Medicine)</p>
<p><b>Past medical history:</b> None significant. No known kidney, liver, lung or blood disorders.</p>
<p><b>Baseline labs:</b> Creatinine 0.9 mg/dL and platelets 245 on 01/14/2025 at an annual physical (outside laboratory report scanned into this record, page 8).</p>
<p><b>Exam:</b> Alert and oriented x3. Thin build. Right basilar crackles. Room air.</p>
<p><b>Assessment:</b> Sepsis due to right-sided pneumonia with hypotension responsive to fluids, acute kidney injury (creatinine 1.5 from baseline 0.9) and mild thrombocytopenia (platelets 140 from baseline 245).</p>
<p><b>Plan:</b> Continue antibiotics, IV fluids, trend creatinine and platelets. Nutrition consult for poor intake.</p>
"""),
        ("Progress Note, Hospital Day 2", """
<p><b>Date/time:</b> 07/23/2025 09:40 &nbsp; <b>Author:</b> P. Ramos, MD</p>
<p><b>Interval:</b> Blood pressure stable without vasopressors, 110 to 118 systolic. Fever curve improving. Room air.</p>
<p><b>Labs:</b> Creatinine 1.2 mg/dL. Platelets 152. Bilirubin 0.7.</p>
<p><b>Plan:</b> Continue antibiotics. Appreciate nutrition recommendations.</p>
"""),
        ("Dietitian Consult Note", """
<p><b>Date/time:</b> 07/23/2025 13:30 &nbsp; <b>Author:</b> J. Kim, RD</p>
<p><b>Assessment:</b> Patient appears thin. Reports decreased appetite for about 1 week during this illness. Current weight 54 kg, BMI 20.8. No prior weight history available to assess weight loss. No documented muscle wasting or fat loss on exam.</p>
<p><b>Recommendation:</b> Oral nutrition supplement twice daily. Reassess intake in 48 hours.</p>
"""),
        ("Nursing Notes", """
<p><b>07/22/2025 16:00:</b> Alert and oriented x4. Room air, SpO2 95%.</p>
<p><b>07/23/2025 02:00:</b> Alert and oriented x4. Resting.</p>
<p><b>07/23/2025 14:00:</b> Alert and oriented x4. Ate 50% of lunch. Supplement given.</p>
<p><b>07/24/2025 08:00:</b> Alert and oriented x4. Ambulating independently.</p>
"""),
        ("Vital Signs Flowsheet", """
<table>
<tr><th>Date/time</th><th>Temp C</th><th>HR</th><th>BP</th><th>MAP</th><th>RR</th><th>SpO2</th><th>O2</th></tr>
<tr><td>07/22 08:20</td><td>39.0</td><td>116</td><td>88/52</td><td>64</td><td>24</td><td>95%</td><td>Room air</td></tr>
<tr><td>07/22 10:30</td><td>38.5</td><td>104</td><td>104/62</td><td>76</td><td>20</td><td>96%</td><td>Room air</td></tr>
<tr><td>07/22 16:00</td><td>38.2</td><td>98</td><td>110/66</td><td>81</td><td>18</td><td>95%</td><td>Room air</td></tr>
<tr><td>07/23 08:00</td><td>37.5</td><td>90</td><td>114/68</td><td>83</td><td>18</td><td>96%</td><td>Room air</td></tr>
<tr><td>07/24 08:00</td><td>36.9</td><td>82</td><td>118/72</td><td>87</td><td>16</td><td>97%</td><td>Room air</td></tr>
</table>
"""),
        ("Laboratory Results", """
<table>
<tr><th>Date/time</th><th>Lactate mmol/L</th><th>Creatinine mg/dL</th><th>Platelets K/uL</th><th>Bilirubin mg/dL</th><th>Albumin g/dL</th><th>WBC K/uL</th></tr>
<tr><td>07/22 08:30</td><td>2.6</td><td>1.5</td><td>140</td><td>0.8</td><td>3.4</td><td>17.1</td></tr>
<tr><td>07/22 11:00</td><td>1.7</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td></tr>
<tr><td>07/23 06:00</td><td>-</td><td>1.2</td><td>152</td><td>0.7</td><td>-</td><td>13.0</td></tr>
<tr><td>07/24 06:00</td><td>-</td><td>1.0</td><td>178</td><td>-</td><td>-</td><td>9.6</td></tr>
</table>
<p>No arterial blood gas was obtained during this admission.</p>
"""),
        ("Outside Records", """
<p><b>Outside laboratory report (scanned)</b> &nbsp; Ordering clinic: Westfield Primary Care (fictional)</p>
<p>Collection date: 01/14/2025. Creatinine 0.9 mg/dL (reference 0.6 to 1.1). Platelets 245 K/uL (reference 150 to 400).</p>
"""),
        ("Discharge Summary", """
<p><b>Admission:</b> 07/22/2025 &nbsp; <b>Discharge:</b> 07/25/2025 &nbsp; <b>Author:</b> P. Ramos, MD</p>
<p><b>Discharge diagnoses:</b> Sepsis due to right-sided pneumonia; acute kidney injury, resolved; thrombocytopenia, resolved; severe protein-calorie malnutrition.</p>
<p><b>Hospital course:</b> Hypotension responded to 1,500 mL of fluid; no vasopressors required. Creatinine improved from 1.5 to 1.0 mg/dL and platelets from 140 to 178. Seen by nutrition for poor intake; oral supplements started.</p>
<p><b>Disposition:</b> Home.</p>
"""),
    ],
    "answer_key": {
        "expected_conclusion": "demonstrated",
        "expected_sofa_change_at_least": 2,
        "must_find": ["BP 88/52 (MAP 64)", "Creatinine 0.9 mg/dL and platelets 245 on 01/14/2025",
                      "No documented muscle wasting or fat loss on exam"],
        "expected_gaps": ["coding question: coded MCC E43 (severe malnutrition) is weakly documented (dietitian note lacks severity criteria; discharge summary lists it without support)"],
        "expected_contradictions": ["malnutrition severity: discharge summary 'severe protein-calorie malnutrition' vs dietitian note with no weight history and no muscle wasting or fat loss"],
        "coding_note": "Sepsis-3 criteria demonstrated (cardiovascular MAP <70 = 1, renal 1.5 = 1, coagulation 140 = 1 from sourced baselines). Whether DRG 871 stands depends on validating an MCC; the coded E43 appears weakly supported. Coder question.",
    },
}
