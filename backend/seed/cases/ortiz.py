"""Case A: available evidence supports the selected criteria. FICTIONAL."""

CASE = {
    "case_id": "CASE-ORTIZ",
    "patient_name": "Maria Ortiz",
    "age": 64,
    "sex": "F",
    "mrn": "RG-0048213",
    "hospital_id": "H-RIV",
    "source": "routine",
    "source_detail": "Post-payment audit selection: DRG 871 claims",
    "claim": {
        "id": "CLM-RIV-2025-CASE01", "year": 2025, "quarter": 3, "admit_date": "2025-08-12",
        "discharge_date": "2025-08-17", "los": 5, "billed_drg": "871", "icu_days": 2, "transfer_in": 0,
        "discharge_status": "home", "member_risk": 1.21,
        "principal_dx": "A41.51",
        "secondary_dx": [
            {"code": "R65.21", "poa": "Y", "desc": "Severe sepsis with septic shock"},
            {"code": "N39.0", "poa": "Y", "desc": "Urinary tract infection, site not specified"},
            {"code": "N17.9", "poa": "Y", "desc": "Acute kidney failure, unspecified"},
            {"code": "E11.9", "poa": "Y", "desc": "Type 2 diabetes mellitus without complications"},
            {"code": "I10", "poa": "Y", "desc": "Essential (primary) hypertension"},
        ],
    },
    "sections": [
        ("Emergency Department Physician Note", """
<p><b>Date/time:</b> 08/12/2025 14:05 &nbsp; <b>Author:</b> J. Alvarez, MD (Emergency Medicine)</p>
<p><b>Chief complaint:</b> Fever, chills and painful urination for 2 days; lightheaded today.</p>
<p><b>History:</b> 64-year-old woman with type 2 diabetes and hypertension. Two days of dysuria and urinary frequency, fever to 102 F at home, chills. Today felt lightheaded on standing. Denies cough, chest pain, abdominal pain. No recent hospitalizations.</p>
<p><b>Initial vital signs (14:10):</b> Temp 39.1 C, HR 118, BP 82/44 (MAP 57), RR 22, SpO2 97% on room air.</p>
<p><b>Exam:</b> Ill-appearing, alert and oriented to person, place and time. Dry mucous membranes. Right costovertebral angle tenderness. Lungs clear. No focal neurologic deficit.</p>
<p><b>Assessment:</b> Suspected sepsis from a urinary source with hypotension.</p>
<p><b>Plan:</b> Blood cultures x2 and urine culture drawn before antibiotics. Lactate. 30 mL/kg lactated Ringer's (weight 68 kg, about 2,000 mL). Ceftriaxone 2 g IV given at 14:50. Reassess blood pressure after fluids; ICU consult if hypotension persists.</p>
<p><b>Reassessment (17:20):</b> Received 2,000 mL lactated Ringer's between 14:30 and 17:15. Blood pressure remains low, MAP 58 to 61. Repeat lactate pending. ICU accepted.</p>
"""),
        ("ICU Admission History and Physical", """
<p><b>Date/time:</b> 08/12/2025 17:35 &nbsp; <b>Author:</b> R. Chen, MD (Critical Care)</p>
<p><b>Past medical history:</b> Type 2 diabetes (on metformin), hypertension (on lisinopril). No known kidney, liver, lung or heart disease. No dementia.</p>
<p><b>Baseline kidney function:</b> Creatinine 0.8 mg/dL on 05/06/2025 at her primary care visit (outside laboratory report scanned into this record, page 8).</p>
<p><b>Social:</b> Lives with husband, independent in daily activities. Never smoker.</p>
<p><b>Exam:</b> Alert and oriented x3, follows commands. Warm extremities. Lungs clear. Right flank tenderness.</p>
<p><b>Data:</b> Lactate 4.2 mmol/L at 14:30. WBC 18.4. Creatinine 1.6 mg/dL. Platelets 180. Bilirubin 0.7. Urinalysis: large leukocyte esterase, positive nitrite.</p>
<p><b>Assessment:</b> Septic shock due to acute pyelonephritis. Hypotension persisting despite 30 mL/kg crystalloid; lactate elevated. Acute kidney injury (creatinine 1.6 from baseline 0.8).</p>
<p><b>Plan:</b> Norepinephrine started at 17:40 at 0.08 mcg/kg/min, titrate to MAP of 65 or more. Continue ceftriaxone pending cultures. Repeat lactate at 18:00. Strict intake and output.</p>
"""),
        ("ICU Progress Note, Hospital Day 2", """
<p><b>Date/time:</b> 08/13/2025 09:10 &nbsp; <b>Author:</b> R. Chen, MD (Critical Care)</p>
<p><b>Interval:</b> Remained on norepinephrine overnight, dose 0.05 to 0.08 mcg/kg/min, MAP 66 to 72. Repeat lactate 3.1 mmol/L at 18:00 yesterday and 1.8 mmol/L this morning. Urine output improving.</p>
<p><b>Cultures:</b> Blood cultures 2 of 2 growing gram-negative rods. Urine culture growing Escherichia coli, greater than 100,000 colonies.</p>
<p><b>Exam:</b> Alert and oriented x3. Lungs clear on room air.</p>
<p><b>Labs:</b> Creatinine 1.3 mg/dL. Platelets 172. Bilirubin 0.6.</p>
<p><b>Assessment and plan:</b> Septic shock from E. coli pyelonephritis with bacteremia, improving. Wean norepinephrine as tolerated. AKI improving.</p>
"""),
        ("Progress Note, Hospital Day 3", """
<p><b>Date/time:</b> 08/14/2025 10:00 &nbsp; <b>Author:</b> L. Grant, MD (Hospital Medicine)</p>
<p><b>Interval:</b> Norepinephrine discontinued 08/13/2025 at 23:40 after about 30 hours. Blood pressure stable off vasopressors, 118/70. Transferred from ICU to the medical floor this morning.</p>
<p><b>Labs:</b> Creatinine 1.0 mg/dL. Blood culture final: Escherichia coli, susceptible to ceftriaxone.</p>
<p><b>Plan:</b> Continue ceftriaxone, plan oral step-down when afebrile for 24 hours.</p>
"""),
        ("Nursing Notes", """
<p><b>08/12/2025 18:00 (ICU):</b> Patient alert and oriented x4. Norepinephrine infusing at 0.08 mcg/kg/min. Skin warm. Foley in place.</p>
<p><b>08/13/2025 02:00 (ICU):</b> Alert and oriented x4, resting. Norepinephrine 0.05 mcg/kg/min. MAP 68.</p>
<p><b>08/13/2025 14:00 (ICU):</b> Alert and oriented x4. Tolerating diet. On room air, SpO2 97%.</p>
<p><b>08/14/2025 08:00 (Floor):</b> Alert and oriented x4. Ambulating with assistance. No supplemental oxygen.</p>
"""),
        ("Vital Signs Flowsheet", """
<table>
<tr><th>Date/time</th><th>Temp C</th><th>HR</th><th>BP</th><th>MAP</th><th>RR</th><th>SpO2</th><th>O2</th></tr>
<tr><td>08/12 14:10</td><td>39.1</td><td>118</td><td>82/44</td><td>57</td><td>22</td><td>97%</td><td>Room air</td></tr>
<tr><td>08/12 16:00</td><td>38.8</td><td>114</td><td>84/48</td><td>60</td><td>21</td><td>97%</td><td>Room air</td></tr>
<tr><td>08/12 17:15</td><td>38.6</td><td>110</td><td>86/49</td><td>61</td><td>20</td><td>98%</td><td>Room air</td></tr>
<tr><td>08/12 20:00</td><td>38.2</td><td>102</td><td>98/56</td><td>70</td><td>18</td><td>98%</td><td>Room air</td></tr>
<tr><td>08/13 08:00</td><td>37.6</td><td>94</td><td>104/58</td><td>73</td><td>16</td><td>97%</td><td>Room air</td></tr>
<tr><td>08/14 08:00</td><td>37.1</td><td>86</td><td>118/70</td><td>86</td><td>16</td><td>98%</td><td>Room air</td></tr>
<tr><td>08/16 08:00</td><td>36.8</td><td>78</td><td>124/74</td><td>91</td><td>14</td><td>98%</td><td>Room air</td></tr>
</table>
"""),
        ("Laboratory Results", """
<table>
<tr><th>Date/time</th><th>Lactate mmol/L</th><th>Creatinine mg/dL</th><th>Platelets K/uL</th><th>Bilirubin mg/dL</th><th>WBC K/uL</th></tr>
<tr><td>08/12 14:30</td><td>4.2</td><td>1.6</td><td>180</td><td>0.7</td><td>18.4</td></tr>
<tr><td>08/12 18:00</td><td>3.1</td><td>-</td><td>-</td><td>-</td><td>-</td></tr>
<tr><td>08/13 06:00</td><td>1.8</td><td>1.3</td><td>172</td><td>0.6</td><td>14.9</td></tr>
<tr><td>08/14 06:00</td><td>-</td><td>1.0</td><td>190</td><td>-</td><td>10.2</td></tr>
<tr><td>08/16 06:00</td><td>-</td><td>0.9</td><td>205</td><td>-</td><td>8.1</td></tr>
</table>
<p>No arterial blood gas was obtained during this admission.</p>
"""),
        ("Outside Records", """
<p><b>Outside laboratory report (scanned)</b> &nbsp; Ordering clinic: Riverbend Family Practice (fictional)</p>
<p>Collection date: 05/06/2025. Creatinine 0.8 mg/dL (reference 0.6 to 1.1). eGFR greater than 90.</p>
"""),
        ("Medication Administration Record", """
<table>
<tr><th>Medication</th><th>Dose / rate</th><th>Start</th><th>Stop</th></tr>
<tr><td>Lactated Ringer's bolus</td><td>2,000 mL</td><td>08/12 14:30</td><td>08/12 17:15</td></tr>
<tr><td>Ceftriaxone</td><td>2 g IV daily</td><td>08/12 14:50</td><td>08/16</td></tr>
<tr><td>Norepinephrine infusion</td><td>0.08 mcg/kg/min, titrated 0.05-0.08</td><td>08/12 17:40</td><td>08/13 23:40</td></tr>
<tr><td>Cephalexin (oral step-down)</td><td>500 mg four times daily</td><td>08/16</td><td>discharge</td></tr>
</table>
"""),
        ("Discharge Summary", """
<p><b>Admission:</b> 08/12/2025 &nbsp; <b>Discharge:</b> 08/17/2025 &nbsp; <b>Author:</b> L. Grant, MD</p>
<p><b>Discharge diagnoses:</b> Septic shock due to Escherichia coli pyelonephritis with bacteremia; acute kidney injury, resolved; type 2 diabetes; hypertension.</p>
<p><b>Hospital course:</b> Presented with fever and hypotension that persisted after 30 mL/kg fluid resuscitation; lactate 4.2 mmol/L. Required norepinephrine for about 30 hours in the ICU. Creatinine peaked at 1.6 mg/dL and returned to 0.9 mg/dL. Completed IV ceftriaxone and stepped down to oral cephalexin.</p>
<p><b>Disposition:</b> Home with husband. Follow up with primary care in 1 week.</p>
"""),
    ],
    "answer_key": {
        "expected_conclusion": "demonstrated",
        "expected_sofa_change_at_least": 4,
        "must_find": ["BP 82/44 (MAP 57)", "Norepinephrine started at 17:40 at 0.08 mcg/kg/min",
                      "Lactate 4.2 mmol/L at 14:30", "Creatinine 0.8 mg/dL on 05/06/2025"],
        "expected_gaps": ["respiratory component not formally assessable (no arterial blood gas)"],
        "expected_contradictions": [],
        "coding_note": "Clinical criteria demonstrated. MCC coded (R65.21 septic shock) appears supported by vasopressors plus lactate after fluids; coder validates complete coding.",
    },
}
