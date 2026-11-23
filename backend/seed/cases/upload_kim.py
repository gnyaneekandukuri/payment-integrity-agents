"""Upload demo record 2: complete record, criteria not supported, plus a coding question. FICTIONAL.

Not pre-loaded: rendered to demo_uploads/ for a live upload onto queue item CASE-BG10 (Crestview Regional, awaiting records).
"""

CASE = {
    "case_id": "CASE-BG10",
    "patient_name": "Joseph Kim",
    "age": 77,
    "sex": "M",
    "mrn": "CR-0044127",
    "hospital_id": "H-CRE",
    "upload_filename": "Crestview_Regional_records_Joseph_Kim.pdf",
    "claim": {
        "year": 2025, "quarter": 4, "admit_date": "2025-11-02", "discharge_date": "2025-11-05", "los": 3,
        "billed_drg": "871", "icu_days": 0, "transfer_in": 0, "discharge_status": "home",
        "principal_dx": "A41.51",
        "secondary_dx": [
            {"code": "N39.0", "poa": "Y", "desc": "Urinary tract infection, site not specified"},
            {"code": "G93.41", "poa": "Y", "desc": "Metabolic encephalopathy"},
            {"code": "E11.9", "poa": "Y", "desc": "Type 2 diabetes mellitus without complications"},
            {"code": "N40.0", "poa": "Y", "desc": "Benign prostatic hyperplasia without lower urinary tract symptoms"},
        ],
    },
    "sections": [
        ("Emergency Department Physician Note", """
<p><b>Date/time:</b> 11/02/2025 15:20 &nbsp; <b>Author:</b> L. Ford, MD (Emergency Medicine)</p>
<p><b>Chief complaint:</b> Burning urination and fever since yesterday.</p>
<p><b>History:</b> 77-year-old man with type 2 diabetes and an enlarged prostate. Dysuria, frequency and fever to 101.5 F since yesterday. No vomiting. Eating and drinking normally.</p>
<p><b>Initial vital signs (15:25):</b> Temp 38.6 C, HR 104, BP 138/82, RR 20, SpO2 97% on room air.</p>
<p><b>Exam:</b> Alert and oriented x3, conversing normally. Mild suprapubic tenderness. No flank tenderness.</p>
<p><b>Data:</b> WBC 14.6. Lactate 1.3 mmol/L. Urinalysis positive for leukocyte esterase and nitrite. Creatinine 1.0. Platelets 232. Bilirubin 0.5.</p>
<p><b>Assessment:</b> Urinary tract infection with fever and tachycardia, meeting SIRS criteria; sepsis due to E. coli suspected.</p>
<p><b>Plan:</b> Urine and blood cultures, ceftriaxone, admit to medicine.</p>
"""),
        ("History and Physical", """
<p><b>Date/time:</b> 11/02/2025 19:00 &nbsp; <b>Author:</b> R. Haddad, MD (Hospital Medicine)</p>
<p><b>Past medical history:</b> Type 2 diabetes (metformin), benign prostatic hyperplasia. No chronic kidney, liver, lung or blood disease. No cognitive impairment.</p>
<p><b>Baseline labs:</b> Creatinine 0.9 mg/dL on 09/30/2025 (outside laboratory report scanned into this record, page 8).</p>
<p><b>Exam:</b> Alert and oriented x3. Mild suprapubic tenderness. Room air.</p>
<p><b>Assessment:</b> Sepsis due to urinary tract infection. Hemodynamically stable.</p>
<p><b>Plan:</b> Continue ceftriaxone pending cultures. Encourage fluids.</p>
"""),
        ("Progress Note, Hospital Day 2", """
<p><b>Date/time:</b> 11/03/2025 09:20 &nbsp; <b>Author:</b> R. Haddad, MD</p>
<p><b>Interval:</b> Fever resolved overnight. Eating well. Alert, oriented, conversing appropriately.</p>
<p><b>Labs:</b> Creatinine 0.9 mg/dL. Platelets 228. Urine culture growing Escherichia coli.</p>
<p><b>Plan:</b> Switch to oral antibiotics tomorrow if afebrile.</p>
"""),
        ("Nursing Notes", """
<p><b>11/02/2025 22:00:</b> Alert and oriented x4. Room air, SpO2 97%. Voiding without difficulty.</p>
<p><b>11/03/2025 06:00:</b> Alert and oriented x4. Slept well.</p>
<p><b>11/03/2025 18:00:</b> Alert and oriented x4. Walking in hallway.</p>
<p><b>11/04/2025 08:00:</b> Alert and oriented x4. No supplemental oxygen at any time this admission.</p>
"""),
        ("Vital Signs Flowsheet", """
<table>
<tr><th>Date/time</th><th>Temp C</th><th>HR</th><th>BP</th><th>MAP</th><th>RR</th><th>SpO2</th><th>O2</th></tr>
<tr><td>11/02 15:25</td><td>38.6</td><td>104</td><td>138/82</td><td>101</td><td>20</td><td>97%</td><td>Room air</td></tr>
<tr><td>11/02 22:00</td><td>38.1</td><td>98</td><td>130/78</td><td>95</td><td>18</td><td>97%</td><td>Room air</td></tr>
<tr><td>11/03 08:00</td><td>37.2</td><td>86</td><td>128/76</td><td>93</td><td>16</td><td>98%</td><td>Room air</td></tr>
<tr><td>11/04 08:00</td><td>36.8</td><td>78</td><td>132/80</td><td>97</td><td>16</td><td>98%</td><td>Room air</td></tr>
</table>
<p>Lowest blood pressure recorded this admission: 128/76 (MAP 93).</p>
"""),
        ("Laboratory Results", """
<table>
<tr><th>Date/time</th><th>Lactate mmol/L</th><th>Creatinine mg/dL</th><th>Platelets K/uL</th><th>Bilirubin mg/dL</th><th>WBC K/uL</th></tr>
<tr><td>11/02 15:30</td><td>1.3</td><td>1.0</td><td>232</td><td>0.5</td><td>14.6</td></tr>
<tr><td>11/03 06:00</td><td>-</td><td>0.9</td><td>228</td><td>-</td><td>10.8</td></tr>
<tr><td>11/04 06:00</td><td>-</td><td>0.9</td><td>240</td><td>-</td><td>8.4</td></tr>
</table>
<p>No arterial blood gas was obtained during this admission.</p>
"""),
        ("Medication Administration Record", """
<table>
<tr><th>Medication</th><th>Dose</th><th>Start</th><th>Stop</th></tr>
<tr><td>Ceftriaxone</td><td>1 g IV daily</td><td>11/02 16:10</td><td>11/04</td></tr>
<tr><td>Cefpodoxime (oral)</td><td>200 mg twice daily</td><td>11/04</td><td>discharge</td></tr>
</table>
<p>No vasopressors were administered. No supplemental oxygen was ordered.</p>
"""),
        ("Outside Records", """
<p><b>Outside laboratory report (scanned)</b> &nbsp; Ordering clinic: Crestview Primary Care (fictional)</p>
<p>Collection date: 09/30/2025. Creatinine 0.9 mg/dL. Platelets 236 K/uL. HbA1c 7.1%.</p>
"""),
        ("Discharge Summary", """
<p><b>Admission:</b> 11/02/2025 &nbsp; <b>Discharge:</b> 11/05/2025 &nbsp; <b>Author:</b> R. Haddad, MD</p>
<p><b>Discharge diagnoses:</b> Sepsis due to E. coli urinary tract infection; metabolic encephalopathy; type 2 diabetes; benign prostatic hyperplasia.</p>
<p><b>Hospital course:</b> Fever and tachycardia resolved within 24 hours of IV antibiotics. Blood pressure, kidney function and oxygen levels remained normal. Alert and oriented throughout the stay.</p>
<p><b>Disposition:</b> Home. Complete 7 days of oral antibiotics.</p>
"""),
    ],
    "answer_key": {
        "expected_conclusion": "not_demonstrated",
        "expected_sofa_change_at_most": 1,
        "must_find": ["Lactate 1.3 mmol/L", "No vasopressors were administered", "Alert and oriented throughout the stay"],
        "expected_gaps": ["coding question: G93.41 metabolic encephalopathy coded, but the patient is documented alert and oriented throughout"],
        "expected_contradictions": ["discharge summary lists metabolic encephalopathy vs alert and oriented throughout"],
        "coding_note": "Infection supported; no organ dysfunction documented. Encephalopathy (the likely MCC) is contradicted by the record. Contract specifies Sepsis-3.",
    },
}
