"""Case C: missing or conflicting evidence prevents a reliable assessment. FICTIONAL."""

CASE = {
    "case_id": "CASE-PATEL",
    "patient_name": "Ravi Patel",
    "age": 80,
    "sex": "M",
    "mrn": "RG-0039254",
    "hospital_id": "H-RIV",
    "source": "investigation_sample",
    "source_detail": "Targeted records review: Riverside General DRG 871 pattern",
    "claim": {
        "id": "CLM-RIV-2025-CASE03", "year": 2025, "quarter": 3, "admit_date": "2025-09-18",
        "discharge_date": "2025-09-22", "los": 4, "billed_drg": "871", "icu_days": 0, "transfer_in": 0,
        "discharge_status": "home", "member_risk": 1.64,
        "principal_dx": "A41.9",
        "secondary_dx": [
            {"code": "J18.9", "poa": "Y", "desc": "Pneumonia, unspecified organism"},
            {"code": "G93.41", "poa": "Y", "desc": "Metabolic encephalopathy"},
            {"code": "N17.9", "poa": "Y", "desc": "Acute kidney failure, unspecified"},
            {"code": "N18.30", "poa": "Y", "desc": "Chronic kidney disease, stage 3 unspecified"},
            {"code": "F03.90", "poa": "Y", "desc": "Unspecified dementia, unspecified severity, without behavioral disturbance"},
        ],
    },
    "sections": [
        ("Emergency Department Physician Note", """
<p><b>Date/time:</b> 09/18/2025 11:20 &nbsp; <b>Author:</b> A. Brooks, MD (Emergency Medicine)</p>
<p><b>Chief complaint:</b> Cough, fever, poor appetite for 2 days. Brought in by daughter.</p>
<p><b>History:</b> 80-year-old man with mild dementia and chronic kidney disease. Daughter reports cough and fever for 2 days and that he is "more tired than usual." Daughter states his thinking today is at his usual baseline.</p>
<p><b>Initial vital signs (11:25):</b> Temp 38.6 C, HR 104, BP 124/70, RR 22, SpO2 89% on room air, improved to 92% on 2 L nasal cannula.</p>
<p><b>Exam:</b> Oriented to person and place, not to date. Crackles at the left base.</p>
<p><b>Data:</b> WBC 13.8. Lactate 1.9 mmol/L. Chest X-ray: left lower lobe infiltrate. Creatinine 2.0 mg/dL.</p>
<p><b>Assessment:</b> Sepsis due to left lower lobe pneumonia. Acute kidney injury on chronic kidney disease, baseline uncertain.</p>
"""),
        ("History and Physical", """
<p><b>Date/time:</b> 09/18/2025 15:40 &nbsp; <b>Author:</b> T. Nguyen, MD (Hospital Medicine)</p>
<p><b>Past medical history:</b> Mild dementia. Chronic kidney disease stage 3. Hypertension.</p>
<p><b>Kidney function history:</b> creatinine 1.1 in 2024 per outside records. No outside laboratory report is attached to this record.</p>
<p><b>Home oxygen:</b> Not documented.</p>
<p><b>Exam:</b> Oriented to person and place. Left basilar crackles. On 2 L nasal cannula, SpO2 90 to 92%.</p>
<p><b>Assessment:</b> Sepsis due to left lower lobe pneumonia. Acute kidney injury superimposed on chronic kidney disease. Mental status at baseline per daughter.</p>
<p><b>Plan:</b> Ceftriaxone and azithromycin. IV fluids. Trend creatinine. Request prior kidney function from primary care.</p>
"""),
        ("Progress Note, Hospital Day 2", """
<p><b>Date/time:</b> 09/19/2025 09:30 &nbsp; <b>Author:</b> T. Nguyen, MD</p>
<p><b>Interval:</b> Nursing reported confusion overnight. On my exam this morning, mental status at baseline; known mild dementia.</p>
<p><b>Respiratory:</b> SpO2 90% on 2 L nasal cannula. No arterial blood gas obtained.</p>
<p><b>Labs:</b> Creatinine 1.7 mg/dL. Platelets 165. Bilirubin 0.8.</p>
<p><b>Plan:</b> Continue antibiotics. Prior creatinine from primary care not yet received.</p>
"""),
        ("Progress Note, Hospital Day 3", """
<p><b>Date/time:</b> 09/20/2025 10:05 &nbsp; <b>Author:</b> T. Nguyen, MD</p>
<p><b>Interval:</b> Afebrile. Weaned to 1 L nasal cannula, SpO2 93%. Eating better.</p>
<p><b>Labs:</b> Creatinine 1.5 mg/dL. Prior primary care creatinine still not received.</p>
<p><b>Plan:</b> Oral antibiotics tomorrow if stable.</p>
"""),
        ("Nursing Notes", """
<p><b>09/18/2025 20:00:</b> Patient alert, oriented to self only. Pulling at nasal cannula. Reoriented frequently.</p>
<p><b>09/19/2025 02:00:</b> Patient confused, disoriented to time and place. Calling out for daughter. Bed alarm on.</p>
<p><b>09/19/2025 14:00:</b> Patient alert, oriented to person and place. Calm. On 2 L nasal cannula, SpO2 90%.</p>
<p><b>09/20/2025 14:00:</b> Alert, oriented to person and place. 1 L nasal cannula.</p>
"""),
        ("Vital Signs Flowsheet", """
<table>
<tr><th>Date/time</th><th>Temp C</th><th>HR</th><th>BP</th><th>MAP</th><th>RR</th><th>SpO2</th><th>O2</th></tr>
<tr><td>09/18 11:25</td><td>38.6</td><td>104</td><td>124/70</td><td>88</td><td>22</td><td>89%</td><td>Room air</td></tr>
<tr><td>09/18 12:00</td><td>38.4</td><td>100</td><td>122/68</td><td>86</td><td>22</td><td>92%</td><td>2 L NC</td></tr>
<tr><td>09/18 20:00</td><td>38.0</td><td>98</td><td>126/72</td><td>90</td><td>20</td><td>91%</td><td>2 L NC</td></tr>
<tr><td>09/19 08:00</td><td>37.6</td><td>92</td><td>128/74</td><td>92</td><td>20</td><td>90%</td><td>2 L NC</td></tr>
<tr><td>09/20 08:00</td><td>37.0</td><td>86</td><td>130/74</td><td>93</td><td>18</td><td>93%</td><td>1 L NC</td></tr>
<tr><td>09/21 08:00</td><td>36.8</td><td>82</td><td>132/76</td><td>95</td><td>16</td><td>94%</td><td>Room air</td></tr>
</table>
"""),
        ("Laboratory Results", """
<table>
<tr><th>Date/time</th><th>Lactate mmol/L</th><th>Creatinine mg/dL</th><th>Platelets K/uL</th><th>Bilirubin mg/dL</th><th>WBC K/uL</th></tr>
<tr><td>09/18 11:40</td><td>1.9</td><td>2.0</td><td>170</td><td>0.8</td><td>13.8</td></tr>
<tr><td>09/19 06:00</td><td>-</td><td>1.7</td><td>165</td><td>0.8</td><td>11.6</td></tr>
<tr><td>09/20 06:00</td><td>-</td><td>1.5</td><td>172</td><td>-</td><td>9.8</td></tr>
<tr><td>09/22 06:00</td><td>-</td><td>1.4</td><td>180</td><td>-</td><td>8.2</td></tr>
</table>
<p>No arterial blood gas was obtained during this admission. No prior creatinine result is on file in this record.</p>
"""),
        ("Medication Administration Record", """
<table>
<tr><th>Medication</th><th>Dose</th><th>Start</th><th>Stop</th></tr>
<tr><td>Ceftriaxone</td><td>1 g IV daily</td><td>09/18 12:30</td><td>09/21</td></tr>
<tr><td>Azithromycin</td><td>500 mg IV daily</td><td>09/18 12:45</td><td>09/20</td></tr>
<tr><td>Normal saline</td><td>100 mL/hr</td><td>09/18 13:00</td><td>09/20 08:00</td></tr>
<tr><td>Oxygen</td><td>2 L nasal cannula, weaned</td><td>09/18 12:00</td><td>09/21</td></tr>
</table>
<p>No vasopressors were administered.</p>
"""),
        ("Discharge Summary", """
<p><b>Admission:</b> 09/18/2025 &nbsp; <b>Discharge:</b> 09/22/2025 &nbsp; <b>Author:</b> T. Nguyen, MD</p>
<p><b>Discharge diagnoses:</b> Sepsis due to left lower lobe pneumonia; acute metabolic encephalopathy, resolved; acute kidney injury on chronic kidney disease stage 3; dementia.</p>
<p><b>Hospital course:</b> Treated with IV antibiotics and fluids. Required 1 to 2 L oxygen, weaned to room air. Creatinine improved from 2.0 to 1.4 mg/dL; true baseline not confirmed. Intermittent confusion overnight on day 1.</p>
<p><b>Disposition:</b> Home with daughter.</p>
"""),
    ],
    "answer_key": {
        "expected_conclusion": "cannot_determine",
        "must_find": ["creatinine 1.1 in 2024 per outside records", "Chronic kidney disease stage 3",
                      "Patient confused, disoriented to time and place", "mental status at baseline; known mild dementia",
                      "Home oxygen: Not documented"],
        "expected_gaps": ["sourced baseline creatinine (the 1.1 is unsourced and CKD is documented)",
                          "baseline mental status", "home oxygen use / respiratory baseline", "no arterial blood gas"],
        "expected_contradictions": ["mental status: nursing documents confusion vs physician documents baseline; discharge summary lists acute metabolic encephalopathy"],
        "coding_note": "Coded MCC is G93.41 metabolic encephalopathy, which rests on the conflicting mental-status evidence; coder and physician advisor question.",
    },
}
