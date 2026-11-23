"""Case B: a sufficiently complete record does not demonstrate the selected criteria. FICTIONAL."""

CASE = {
    "case_id": "CASE-LEE",
    "patient_name": "David Lee",
    "age": 72,
    "sex": "M",
    "mrn": "RG-0051877",
    "hospital_id": "H-RIV",
    "source": "investigation_sample",
    "source_detail": "Targeted records review: Riverside General DRG 871 pattern",
    "claim": {
        "id": "CLM-RIV-2025-CASE02", "year": 2025, "quarter": 4, "admit_date": "2025-10-03",
        "discharge_date": "2025-10-07", "los": 4, "billed_drg": "871", "icu_days": 0, "transfer_in": 0,
        "discharge_status": "home", "member_risk": 1.02,
        "principal_dx": "A41.9",
        "secondary_dx": [
            {"code": "J18.9", "poa": "Y", "desc": "Pneumonia, unspecified organism"},
            {"code": "R65.20", "poa": "Y", "desc": "Severe sepsis without septic shock"},
            {"code": "E87.1", "poa": "Y", "desc": "Hypo-osmolality and hyponatremia"},
            {"code": "I10", "poa": "Y", "desc": "Essential (primary) hypertension"},
            {"code": "E78.5", "poa": "Y", "desc": "Hyperlipidemia, unspecified"},
        ],
    },
    "sections": [
        ("Emergency Department Physician Note", """
<p><b>Date/time:</b> 10/03/2025 21:40 &nbsp; <b>Author:</b> S. Patel, MD (Emergency Medicine)</p>
<p><b>Chief complaint:</b> Cough and fever for 3 days.</p>
<p><b>History:</b> 72-year-old man with hypertension and hyperlipidemia. Productive cough, fever and fatigue for 3 days. Mild shortness of breath on exertion. No chest pain. Eating and drinking less than usual.</p>
<p><b>Initial vital signs (21:45):</b> Temp 38.9 C, HR 112, BP 128/76, RR 24, SpO2 96% on room air.</p>
<p><b>Exam:</b> Alert and oriented x3. Crackles at the right lung base. No increased work of breathing at rest.</p>
<p><b>Data:</b> WBC 15.2. Lactate 1.4 mmol/L. Chest X-ray: right lower lobe consolidation. Sodium 131.</p>
<p><b>Assessment:</b> Meets SIRS criteria (temperature, heart rate, respiratory rate, white count). Sepsis due to right lower lobe pneumonia.</p>
<p><b>Plan:</b> Blood cultures, ceftriaxone and azithromycin, admit to medicine.</p>
"""),
        ("History and Physical", """
<p><b>Date/time:</b> 10/04/2025 00:30 &nbsp; <b>Author:</b> K. Moore, MD (Hospital Medicine)</p>
<p><b>Past medical history:</b> Hypertension, hyperlipidemia. No known chronic kidney, liver, lung or heart disease. No cognitive impairment.</p>
<p><b>Baseline kidney function:</b> Creatinine 0.9 mg/dL on 04/02/2025 (outside laboratory report scanned into this record, page 9).</p>
<p><b>Exam:</b> Alert and oriented x3. Right basilar crackles. Breathing comfortably on room air.</p>
<p><b>Assessment:</b> Sepsis due to community-acquired right lower lobe pneumonia. Mild hyponatremia, likely from poor intake.</p>
<p><b>Plan:</b> Continue ceftriaxone and azithromycin. Gentle IV fluids for poor intake. Monitor sodium.</p>
"""),
        ("Progress Note, Hospital Day 2", """
<p><b>Date/time:</b> 10/04/2025 10:15 &nbsp; <b>Author:</b> K. Moore, MD</p>
<p><b>Interval:</b> Fever to 38.4 C overnight. Cough improving. No oxygen requirement.</p>
<p><b>Exam:</b> Alert and oriented x3. Crackles right base.</p>
<p><b>Labs:</b> Creatinine 0.9 mg/dL. Platelets 210. Bilirubin 0.6. Sodium 133.</p>
<p><b>Plan:</b> Continue antibiotics. Encourage oral intake.</p>
"""),
        ("Progress Note, Hospital Day 3", """
<p><b>Date/time:</b> 10/05/2025 09:50 &nbsp; <b>Author:</b> K. Moore, MD</p>
<p><b>Interval:</b> Afebrile for 18 hours. Eating well. Remains on room air.</p>
<p><b>Labs:</b> Creatinine 0.8 mg/dL. Platelets 205. Sodium 135. Blood cultures no growth at 48 hours.</p>
<p><b>Plan:</b> Transition to oral antibiotics; anticipate discharge in 1 to 2 days.</p>
"""),
        ("Nursing Notes", """
<p><b>10/04/2025 02:00:</b> Alert and oriented x4. On room air, SpO2 96%. Cough productive.</p>
<p><b>10/04/2025 14:00:</b> Alert and oriented x4. Ambulating in hallway. Room air.</p>
<p><b>10/05/2025 02:00:</b> Alert and oriented x4. Sleeping comfortably. Room air, SpO2 97%.</p>
<p><b>10/05/2025 14:00:</b> Alert and oriented x4. Tolerating diet.</p>
<p><b>10/06/2025 08:00:</b> Alert and oriented x4. No supplemental oxygen at any time this admission.</p>
"""),
        ("Vital Signs Flowsheet", """
<table>
<tr><th>Date/time</th><th>Temp C</th><th>HR</th><th>BP</th><th>MAP</th><th>RR</th><th>SpO2</th><th>O2</th></tr>
<tr><td>10/03 21:45</td><td>38.9</td><td>112</td><td>128/76</td><td>93</td><td>24</td><td>96%</td><td>Room air</td></tr>
<tr><td>10/04 02:00</td><td>38.4</td><td>104</td><td>118/70</td><td>86</td><td>22</td><td>96%</td><td>Room air</td></tr>
<tr><td>10/04 06:00</td><td>38.1</td><td>100</td><td>112/68</td><td>83</td><td>20</td><td>95%</td><td>Room air</td></tr>
<tr><td>10/04 14:00</td><td>37.8</td><td>96</td><td>120/72</td><td>88</td><td>20</td><td>96%</td><td>Room air</td></tr>
<tr><td>10/05 02:00</td><td>37.4</td><td>90</td><td>122/74</td><td>90</td><td>18</td><td>97%</td><td>Room air</td></tr>
<tr><td>10/05 14:00</td><td>37.1</td><td>84</td><td>126/76</td><td>93</td><td>16</td><td>97%</td><td>Room air</td></tr>
<tr><td>10/06 08:00</td><td>36.9</td><td>80</td><td>130/78</td><td>95</td><td>16</td><td>97%</td><td>Room air</td></tr>
</table>
<p>Vital signs recorded every 4 hours throughout the stay; the lowest blood pressure recorded was 112/68 (MAP 83). Representative rows shown.</p>
"""),
        ("Laboratory Results", """
<table>
<tr><th>Date/time</th><th>Lactate mmol/L</th><th>Creatinine mg/dL</th><th>Platelets K/uL</th><th>Bilirubin mg/dL</th><th>Sodium</th><th>WBC K/uL</th></tr>
<tr><td>10/03 21:50</td><td>1.4</td><td>0.9</td><td>218</td><td>0.6</td><td>131</td><td>15.2</td></tr>
<tr><td>10/04 06:00</td><td>-</td><td>0.9</td><td>210</td><td>0.6</td><td>133</td><td>13.1</td></tr>
<tr><td>10/05 06:00</td><td>-</td><td>0.8</td><td>205</td><td>-</td><td>135</td><td>10.4</td></tr>
<tr><td>10/06 06:00</td><td>-</td><td>0.8</td><td>212</td><td>-</td><td>136</td><td>8.9</td></tr>
</table>
<p>No arterial blood gas was obtained during this admission.</p>
"""),
        ("Medication Administration Record", """
<table>
<tr><th>Medication</th><th>Dose</th><th>Start</th><th>Stop</th></tr>
<tr><td>Ceftriaxone</td><td>1 g IV daily</td><td>10/03 22:30</td><td>10/05</td></tr>
<tr><td>Azithromycin</td><td>500 mg IV daily</td><td>10/03 22:45</td><td>10/05</td></tr>
<tr><td>Normal saline</td><td>75 mL/hr</td><td>10/04 01:00</td><td>10/05 08:00</td></tr>
<tr><td>Amoxicillin-clavulanate (oral)</td><td>875 mg twice daily</td><td>10/05</td><td>discharge</td></tr>
</table>
<p>No vasopressors were administered. No supplemental oxygen was ordered.</p>
"""),
        ("Outside Records", """
<p><b>Outside laboratory report (scanned)</b> &nbsp; Ordering clinic: Northside Internal Medicine (fictional)</p>
<p>Collection date: 04/02/2025. Creatinine 0.9 mg/dL (reference 0.7 to 1.3). Sodium 139.</p>
"""),
        ("Discharge Summary", """
<p><b>Admission:</b> 10/03/2025 &nbsp; <b>Discharge:</b> 10/07/2025 &nbsp; <b>Author:</b> K. Moore, MD</p>
<p><b>Discharge diagnoses:</b> Sepsis due to right lower lobe pneumonia, resolved; hyponatremia, resolved; hypertension.</p>
<p><b>Hospital course:</b> Admitted with fever, tachycardia, tachypnea and leukocytosis with right lower lobe pneumonia. Treated with IV antibiotics, transitioned to oral. Remained on room air with normal blood pressure throughout. Creatinine remained at baseline.</p>
<p><b>Disposition:</b> Home. Complete 5 more days of oral antibiotics.</p>
"""),
    ],
    "answer_key": {
        "expected_conclusion": "not_demonstrated",
        "expected_sofa_change_at_least": 0,
        "expected_sofa_change_at_most": 1,
        "must_find": ["Lactate 1.4 mmol/L", "the lowest blood pressure recorded was 112/68 (MAP 83)",
                      "No vasopressors were administered", "Creatinine 0.9 mg/dL on 04/02/2025"],
        "expected_gaps": ["respiratory component not formally assessable (no arterial blood gas); room air with normal SpO2 throughout must be stated explicitly"],
        "expected_contradictions": [],
        "coding_note": "Pneumonia supported. Coded R65.20 (severe sepsis) not supported by organ dysfunction evidence. E87.1 hyponatremia documented. Replacement DRG depends on the coder's complete coding.",
    },
}
