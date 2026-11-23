"""Upload demo record 1: criteria supported (clear case). FICTIONAL.

Not pre-loaded: rendered to demo_uploads/ for a live upload onto queue item CASE-BG04 (Metro Regional, awaiting records).
"""

CASE = {
    "case_id": "CASE-BG04",
    "patient_name": "Samuel Adeyemi",
    "age": 74,
    "sex": "M",
    "mrn": "MR-0098812",
    "hospital_id": "H-MET",
    "upload_filename": "Metro_Regional_records_Samuel_Adeyemi.pdf",
    "claim": {
        "year": 2025, "quarter": 4, "admit_date": "2025-11-14", "discharge_date": "2025-11-20", "los": 6,
        "billed_drg": "871", "icu_days": 2, "transfer_in": 0, "discharge_status": "home",
        "principal_dx": "A41.9",
        "secondary_dx": [
            {"code": "J18.9", "poa": "Y", "desc": "Pneumonia, unspecified organism"},
            {"code": "R65.20", "poa": "Y", "desc": "Severe sepsis without septic shock"},
            {"code": "D69.6", "poa": "Y", "desc": "Thrombocytopenia, unspecified"},
            {"code": "N17.9", "poa": "Y", "desc": "Acute kidney failure, unspecified"},
            {"code": "I10", "poa": "Y", "desc": "Essential (primary) hypertension"},
        ],
    },
    "sections": [
        ("Emergency Department Physician Note", """
<p><b>Date/time:</b> 11/14/2025 06:40 &nbsp; <b>Author:</b> C. Romero, MD (Emergency Medicine)</p>
<p><b>Chief complaint:</b> Fever and cough for 3 days. Wife reports he is tired but thinking clearly.</p>
<p><b>History:</b> 74-year-old man with hypertension. Productive cough, fever and shortness of breath for 3 days. No known lung, kidney, liver or blood disorders. No home oxygen.</p>
<p><b>Initial vital signs (06:45):</b> Temp 38.7 C, HR 112, BP 96/58 (MAP 71), RR 26, SpO2 91% on room air, 95% on 2 L nasal cannula.</p>
<p><b>Exam:</b> Alert and oriented x3. Bronchial breath sounds right base. Petechiae absent.</p>
<p><b>Data:</b> WBC 17.9. Lactate 2.9 mmol/L. Platelets 88. Bilirubin 2.4. Creatinine 1.3. Chest X-ray: right lower lobe consolidation.</p>
<p><b>Assessment:</b> Sepsis due to right lower lobe pneumonia with thrombocytopenia and elevated bilirubin.</p>
<p><b>Plan:</b> Blood cultures, piperacillin-tazobactam, 30 mL/kg fluids, admit to step-down ICU.</p>
"""),
        ("History and Physical", """
<p><b>Date/time:</b> 11/14/2025 10:15 &nbsp; <b>Author:</b> A. Osei, MD (Critical Care)</p>
<p><b>Past medical history:</b> Hypertension. No chronic kidney, liver, lung or blood disease. No alcohol use.</p>
<p><b>Baseline labs:</b> Platelets 210, bilirubin 0.6 mg/dL and creatinine 1.0 mg/dL on 08/22/2025 (outside laboratory report scanned into this record, page 8).</p>
<p><b>Exam:</b> Alert and oriented x3. Right basilar consolidation. On 2 L nasal cannula.</p>
<p><b>Assessment:</b> Sepsis due to community-acquired pneumonia with new thrombocytopenia (platelets 88 from 210), hyperbilirubinemia (2.4 from 0.6) and mild acute kidney injury (creatinine 1.3 from 1.0). No evidence of liver disease on ultrasound.</p>
<p><b>Plan:</b> Continue antibiotics, trend platelets, bilirubin and creatinine. Hematology not needed unless platelets fall below 50.</p>
"""),
        ("ICU Progress Note, Hospital Day 2", """
<p><b>Date/time:</b> 11/15/2025 08:30 &nbsp; <b>Author:</b> A. Osei, MD</p>
<p><b>Interval:</b> Blood pressure stable without vasopressors, MAP 72 to 80. Lactate cleared to 1.6 mmol/L.</p>
<p><b>Labs:</b> Platelets 92. Bilirubin 2.1. Creatinine 1.2. Blood cultures: Streptococcus pneumoniae.</p>
<p><b>Plan:</b> Narrow antibiotics to ceftriaxone. Transfer to floor tomorrow if stable.</p>
"""),
        ("Progress Note, Hospital Day 4", """
<p><b>Date/time:</b> 11/17/2025 09:00 &nbsp; <b>Author:</b> J. Park, MD (Hospital Medicine)</p>
<p><b>Interval:</b> Afebrile 36 hours. Weaned to room air. Platelets 140, bilirubin 1.1, creatinine 1.0.</p>
<p><b>Plan:</b> Oral antibiotics; discharge planning.</p>
"""),
        ("Nursing Notes", """
<p><b>11/14/2025 12:00 (ICU):</b> Alert and oriented x4. 2 L nasal cannula, SpO2 95%.</p>
<p><b>11/15/2025 02:00 (ICU):</b> Alert and oriented x4. Resting.</p>
<p><b>11/16/2025 14:00 (Floor):</b> Alert and oriented x4. Ambulating.</p>
"""),
        ("Vital Signs Flowsheet", """
<table>
<tr><th>Date/time</th><th>Temp C</th><th>HR</th><th>BP</th><th>MAP</th><th>RR</th><th>SpO2</th><th>O2</th></tr>
<tr><td>11/14 06:45</td><td>38.7</td><td>112</td><td>96/58</td><td>71</td><td>26</td><td>91%</td><td>Room air</td></tr>
<tr><td>11/14 09:00</td><td>38.3</td><td>104</td><td>104/62</td><td>76</td><td>22</td><td>95%</td><td>2 L NC</td></tr>
<tr><td>11/15 08:00</td><td>37.8</td><td>96</td><td>110/64</td><td>79</td><td>20</td><td>95%</td><td>2 L NC</td></tr>
<tr><td>11/17 08:00</td><td>36.9</td><td>84</td><td>124/72</td><td>89</td><td>16</td><td>95%</td><td>Room air</td></tr>
</table>
"""),
        ("Laboratory Results", """
<table>
<tr><th>Date/time</th><th>Lactate mmol/L</th><th>Platelets K/uL</th><th>Bilirubin mg/dL</th><th>Creatinine mg/dL</th><th>WBC K/uL</th></tr>
<tr><td>11/14 06:50</td><td>2.9</td><td>88</td><td>2.4</td><td>1.3</td><td>17.9</td></tr>
<tr><td>11/15 06:00</td><td>1.6</td><td>92</td><td>2.1</td><td>1.2</td><td>14.2</td></tr>
<tr><td>11/17 06:00</td><td>-</td><td>140</td><td>1.1</td><td>1.0</td><td>9.1</td></tr>
</table>
<p>No arterial blood gas was obtained during this admission.</p>
"""),
        ("Outside Records", """
<p><b>Outside laboratory report (scanned)</b> &nbsp; Ordering clinic: Eastside Family Medicine (fictional)</p>
<p>Collection date: 08/22/2025. Platelets 210 K/uL. Total bilirubin 0.6 mg/dL. Creatinine 1.0 mg/dL.</p>
"""),
        ("Discharge Summary", """
<p><b>Admission:</b> 11/14/2025 &nbsp; <b>Discharge:</b> 11/20/2025 &nbsp; <b>Author:</b> J. Park, MD</p>
<p><b>Discharge diagnoses:</b> Sepsis due to pneumococcal pneumonia with bacteremia; sepsis-associated thrombocytopenia and hyperbilirubinemia, resolved; acute kidney injury, resolved; hypertension.</p>
<p><b>Hospital course:</b> Platelets fell to 88 and bilirubin rose to 2.4 on admission from normal baselines, with creatinine 1.3; all normalized with treatment. No vasopressors required. Weaned from 2 L oxygen to room air.</p>
<p><b>Disposition:</b> Home.</p>
"""),
    ],
    "answer_key": {
        "expected_conclusion": "demonstrated",
        "expected_sofa_change_at_least": 4,
        "must_find": ["Platelets 88", "Bilirubin 2.4", "on 08/22/2025"],
        "expected_gaps": ["respiratory not formally assessable (no blood gas)"],
        "expected_contradictions": [],
        "coding_note": "Coagulation 2 (88 from 210), liver 2 (2.4 from 0.6), renal 1 (1.3 from 1.0): change 5. Contract specifies Sepsis-3.",
    },
}
