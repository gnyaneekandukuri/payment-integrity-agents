"""Tools for the claim review agent. Every write passes a fixed validator before it is stored.

There is deliberately no tool to regroup a DRG, price a claim, deny, approve, send or contact anyone.
"""
import json
import re

from app.agents import sofa as sofa_calc
from app.agents import validators

CRITERIA = ["infection", "organ_function", "baseline", "preexisting_condition", "lactate", "vasopressor", "fluids", "other"]
SYSTEMS = ["respiratory", "coagulation", "liver", "cardiovascular", "cns", "renal", "none"]

TOOL_SPECS = [
    {"name": "get_claim", "description": "Get the claim under review: hospital, billed DRG and title, principal and secondary diagnosis codes with present-on-admission flags, dates.",
     "parameters": {"type": "object", "properties": {}, "required": []}},
    {"name": "get_contract_criteria", "description": "Get the clinical criteria the hospital's contract specifies for sepsis validation, or 'silent' if it specifies none.",
     "parameters": {"type": "object", "properties": {}, "required": []}},
    {"name": "list_pages", "description": "List the pages of the medical record with their section titles.",
     "parameters": {"type": "object", "properties": {}, "required": []}},
    {"name": "search_chart", "description": "Keyword search across all pages of the medical record. Returns matching lines with page numbers.",
     "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
    {"name": "read_page", "description": "Read the full text of one page of the medical record.",
     "parameters": {"type": "object", "properties": {"page": {"type": "integer", "minimum": 1}}, "required": ["page"]}},
    {"name": "record_evidence",
     "description": ("Record one piece of evidence with an EXACT quote copied from the cited page. The quote is checked against the page; "
                     "if it is not found, the evidence is rejected. Use timepoint 'baseline' for pre-illness values and 'acute' for values "
                     "during this illness. For a pre-existing chronic condition use criterion 'preexisting_condition'."),
     "parameters": {"type": "object", "properties": {
         "criterion": {"type": "string", "enum": CRITERIA},
         "system": {"type": "string", "enum": SYSTEMS, "description": "SOFA organ system, or 'none'"},
         "measure": {"type": "string", "description": "e.g. MAP, norepinephrine dose (mcg/kg/min), creatinine, platelets, bilirubin, GCS, mental status, PaO2, PaO2/FiO2 ratio, SpO2, lactate, culture, imaging"},
         "value": {"type": "string", "description": "the value as documented, e.g. '57', '0.08', '2.0', 'normal', 'altered'"},
         "unit": {"type": "string"},
         "observed_at": {"type": "string", "description": "date/time as documented"},
         "timepoint": {"type": "string", "enum": ["baseline", "acute"]},
         "fio2": {"type": "string", "description": "FiO2 as a fraction, only when recording PaO2"},
         "ventilatory_support": {"type": "boolean", "description": "true only for mechanical ventilation or non-invasive ventilation"},
         "source_quality": {"type": "string", "enum": ["sourced", "unsourced"],
                            "description": "For baseline values: 'sourced' only if a dated result or report is in the record; otherwise 'unsourced'"},
         "stance": {"type": "string", "enum": ["supports", "contradicts", "context"],
                    "description": "Relative to the selected sepsis criteria"},
         "page": {"type": "integer", "minimum": 1},
         "quote": {"type": "string", "description": "exact text copied from that page"},
     }, "required": ["criterion", "system", "measure", "value", "timepoint", "stance", "page", "quote"]}},
    {"name": "record_gap", "description": "Record something missing or conflicting in the record, or a coding question outside the clinical criteria, and why it matters.",
     "parameters": {"type": "object", "properties": {
         "kind": {"type": "string", "enum": ["missing", "conflicting", "coding_question"]},
         "item": {"type": "string"},
         "why_it_matters": {"type": "string"},
     }, "required": ["kind", "item", "why_it_matters"]}},
    {"name": "compute_sofa", "description": "Compute SOFA baseline, worst and change per organ system from the evidence recorded so far (fixed calculation, cited values only). Call again after recording new evidence.",
     "parameters": {"type": "object", "properties": {}, "required": []}},
    {"name": "submit_draft",
     "description": ("Submit the draft conclusion for the clinical reviewer. Checked for consistency with the evidence and SOFA result; "
                     "if rejected, fix the problems or choose 'cannot_determine'. This ends your work when accepted."),
     "parameters": {"type": "object", "properties": {
         "conclusion": {"type": "string", "enum": ["demonstrated", "not_demonstrated", "cannot_determine"]},
         "summary": {"type": "string", "description": "One plain sentence answering the reviewer's question, e.g. 'The record does not show new organ dysfunction, so sepsis is not supported.'"},
         "documented": {"type": "string", "description": "What the record shows, in plain words for a nurse reviewer, citing evidence ids like [E3]. 2-4 short sentences."},
         "uncertain": {"type": "string", "description": "What is missing, conflicting or could not be scored, in plain words. Write 'Nothing material.' if none."},
         "would_resolve": {"type": "string", "description": "What document or value would settle the open points. Write 'Not needed.' if the conclusion is clear."},
         "evidence_ids": {"type": "array", "items": {"type": "integer"}},
         "unscored_justifications": {"type": "object", "additionalProperties": {"type": "string"},
                                     "description": "For not_demonstrated: for each unscored SOFA system, why the record shows no dysfunction"},
         "gaps_addressed": {"type": "string",
                            "description": "Required if you recorded any missing or conflicting gap and conclude demonstrated or not_demonstrated: why those gaps cannot change the conclusion"},
     }, "required": ["conclusion", "summary", "documented", "uncertain", "would_resolve", "evidence_ids"]}},
]


_SYSTEM_WORDS = {
    "renal": ["kidney", "renal", "ckd", "creatinine", "dialysis"],
    "cns": ["dementia", "mental", "gcs", "confus", "orient", "encephalopathy", "cognitive"],
    "respiratory": ["copd", "oxygen", "pao2", "spo2", "lung", "respiratory", "fio2"],
    "liver": ["liver", "cirrhosis", "bilirubin", "hepatic"],
    "coagulation": ["platelet", "thrombocytopenia", "coagul"],
    "cardiovascular": ["map", "blood pressure", "bp ", "norepinephrine", "vasopressor", "hypotension", "heart failure"],
}


_NEGATION = re.compile(r"\b(no|none|not|denies|without|absent|negative)\b", re.IGNORECASE)


def _infer_system(text: str):
    low = text.lower()
    for system, words in _SYSTEM_WORDS.items():
        if any(w in low for w in words):
            return system
    return None


class ClaimReviewContext:
    """State for one run: database connection, case, and what has been recorded."""

    def __init__(self, conn, case_id: str, run_id: str):
        self.conn, self.case_id, self.run_id = conn, case_id, run_id
        row = conn.execute(
            "SELECT cs.*, cl.*, h.name AS hospital_name, ch.id AS chart_id FROM cases cs "
            "JOIN claims cl ON cl.id = cs.claim_id JOIN hospitals h ON h.id = cl.hospital_id "
            "JOIN charts ch ON ch.case_id = cs.id WHERE cs.id = ?", (case_id,)).fetchone()
        if row is None:
            raise ValueError(f"case {case_id} has no chart")
        self.case = dict(row)
        self.pages = {r["page"]: dict(r) for r in conn.execute(
            "SELECT page, section, text FROM chart_pages WHERE chart_id=? ORDER BY page", (self.case["chart_id"],))}
        self.evidence: list[dict] = []
        self.gaps: list[dict] = []
        self.sofa: dict | None = None
        self.draft: dict | None = None
        self.done = False

    # ---------------- read tools
    def get_claim(self):
        c = self.case
        title = self.conn.execute("SELECT title FROM drg_weights WHERE drg=?", (c["billed_drg"],)).fetchone()["title"]
        return {
            "claim_id": c["claim_id"], "hospital": c["hospital_name"], "patient": f'{c["patient_name"]}, {c["age"]}{c["sex"]}',
            "admit_date": c["admit_date"], "discharge_date": c["discharge_date"], "length_of_stay": c["los"],
            "icu_days": c["icu_days"], "billed_drg": c["billed_drg"], "billed_drg_title": title,
            "principal_diagnosis": c["principal_dx"], "secondary_diagnoses": json.loads(c["secondary_dx"]),
            "review_source": c["source_detail"],
            "note": ("Your task is the clinical question only: does the record demonstrate the selected sepsis criteria? "
                     "Validating sepsis does not validate the DRG: the MCC and complete coding are the coder's step. "
                     "If a coded secondary diagnosis looks weakly documented, record a coding_question gap."),
        }

    def get_contract_criteria(self):
        row = self.conn.execute("SELECT sepsis_criteria, summary FROM contracts WHERE hospital_id=?", (self.case["hospital_id"],)).fetchone()
        out = {"hospital": self.case["hospital_name"], "contract_sepsis_criteria": row["sepsis_criteria"], "contract_summary": row["summary"]}
        if row["sepsis_criteria"] == "silent":
            out["applied_for_this_review"] = "Sepsis-3 (plan default)"
            out["flag"] = "CONTRACT SILENT: the contract does not specify sepsis criteria. Sepsis-3 is applied as the plan default; state this in the rationale."
        else:
            out["applied_for_this_review"] = row["sepsis_criteria"]
        out["sepsis3"] = ("Suspected or confirmed infection plus an acute change in total SOFA score of 2 points or more. "
                          "Baseline SOFA may be assumed 0 only if no pre-existing organ dysfunction is known.")
        return out

    def list_pages(self):
        return [{"page": p, "section": v["section"]} for p, v in self.pages.items()]

    def search_chart(self, query: str):
        terms = [t for t in re.findall(r"[a-z0-9.]+", query.lower()) if len(t) > 1]
        hits = []
        for p, v in self.pages.items():
            for line in v["text"].splitlines():
                low = line.lower()
                score = sum(1 for t in terms if t in low)
                if score:
                    hits.append((score, p, v["section"], line.strip()))
        hits.sort(key=lambda h: (-h[0], h[1]))
        return [{"page": p, "section": s, "line": line} for _, p, s, line in hits[:12]] or {"result": "no matches"}

    def read_page(self, page: int):
        v = self.pages.get(int(page))
        if not v:
            return {"error": f"page {page} does not exist; pages are 1-{max(self.pages)}"}
        return {"page": int(page), "section": v["section"], "text": v["text"]}

    # ---------------- write tools (validated)
    def record_evidence(self, **a):
        page = self.pages.get(int(a.get("page", 0)))
        if not page:
            return {"accepted": False, "reason": "page does not exist"}
        span = validators.locate_quote(page["text"], a.get("quote", ""))
        if span is None:
            return {"accepted": False, "reason": f"quote not found on page {a.get('page')}; copy the text exactly from that page"}
        if a.get("criterion") == "preexisting_condition" and _NEGATION.search(f'{a.get("measure", "")} {a.get("value", "")}'):
            # "no home oxygen", "no known lung disease": absence of a condition is baseline context, not dysfunction
            a = {**a, "criterion": "baseline", "timepoint": "baseline", "stance": "context"}
        system = None if a.get("system") in (None, "none") else a["system"]
        if a["criterion"] in ("preexisting_condition", "baseline", "organ_function") and system is None:
            system = _infer_system(f'{a.get("measure", "")} {a.get("value", "")}')
            if system is None:
                return {"accepted": False,
                        "reason": f"criterion '{a['criterion']}' needs the SOFA system it belongs to (e.g. renal for kidney disease, cns for dementia)"}
        extra = {k: a[k] for k in ("fio2", "ventilatory_support", "source_quality") if a.get(k) not in (None, "")}
        ref = len(self.evidence) + 1
        self.conn.execute(
            "INSERT INTO evidence (run_id, case_id, ref, criterion, system, value, unit, observed_at, page, quote, char_start, char_end, stance) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (self.run_id, self.case_id, ref, a["criterion"], system, f'{a.get("measure", "")}: {a.get("value", "")}', a.get("unit"),
             a.get("observed_at"), int(a["page"]), page["text"][span[0]:span[1]], span[0], span[1], a["stance"]))
        eid = ref
        self.evidence.append({"id": eid, "criterion": a["criterion"], "system": system, "measure": a.get("measure", ""),
                              "value": a.get("value", ""), "timepoint": a.get("timepoint"), "extra": extra, "stance": a["stance"]})
        self.sofa = None  # must be recomputed
        return {"accepted": True, "evidence_id": eid}

    def record_gap(self, kind: str, item: str, why_it_matters: str):
        self.conn.execute("INSERT INTO gaps (run_id, case_id, kind, item, why_it_matters) VALUES (?,?,?,?,?)",
                          (self.run_id, self.case_id, kind, item, why_it_matters))
        self.gaps.append({"kind": kind, "item": item})
        return {"accepted": True}

    def compute_sofa(self):
        self.sofa = sofa_calc.compute(self.evidence)
        self.conn.execute("DELETE FROM sofa_results WHERE run_id=?", (self.run_id,))
        for system, v in self.sofa["systems"].items():
            self.conn.execute("INSERT INTO sofa_results VALUES (?,?,?,?,?,?,?,?,?)",
                              (self.run_id, self.case_id, system, v["baseline"], v["worst"], v["change"], v["status"],
                               v["detail"], json.dumps(v["evidence_ids"])))
        hints = []
        for system, v in self.sofa["systems"].items():
            if v["status"] == "not_documented":
                hints.append(f"{system}: no value recorded. Check the vital signs and laboratory pages; if it is truly absent, record a 'missing' gap.")
            elif v["status"] == "scored" and "assumed 0" in v["detail"]:
                hints.append(f"{system}: baseline assumed 0. Confirm there is no pre-existing {system} condition in the history "
                             f"(if there is, record it as preexisting_condition with system '{system}') and no dated baseline result.")
        return {**self.sofa, "hints": hints}

    def submit_draft(self, conclusion: str, evidence_ids: list, summary: str = "", documented: str = "", uncertain: str = "",
                     would_resolve: str = "", rationale: str = "", unscored_justifications: dict | None = None,
                     gaps_addressed: str | None = None):
        sections = {"summary": summary, "documented": documented, "uncertain": uncertain, "would_resolve": would_resolve}
        rationale = rationale or " ".join(v for v in (summary, documented, uncertain) if v)
        if not summary.strip() or not documented.strip():
            return {"accepted": False, "problems": ["summary and documented are required, in plain language"]}
        infection_ids = [e["id"] for e in self.evidence if e["criterion"] == "infection" and e["stance"] == "supports"]
        problems = validators.check_draft(conclusion, self.sofa, infection_ids, self.gaps, unscored_justifications or {},
                                          " ".join([rationale, *sections.values()]), [int(i) for i in evidence_ids],
                                          {e["id"] for e in self.evidence})
        open_gaps = [g for g in self.gaps if g["kind"] in ("missing", "conflicting")]
        if conclusion != "cannot_determine" and open_gaps and not (gaps_addressed or "").strip():
            problems.append("you recorded missing or conflicting evidence " + str([g["item"] for g in open_gaps]) +
                            "; explain in gaps_addressed why it cannot change the conclusion, or choose cannot_determine")
        if problems:
            return {"accepted": False, "problems": problems}
        self.conn.execute("INSERT INTO drafts (run_id, case_id, conclusion, rationale, sections, evidence_ids, validator_result) VALUES (?,?,?,?,?,?,?)",
                          (self.run_id, self.case_id, conclusion, rationale, json.dumps(sections), json.dumps(evidence_ids),
                           json.dumps({"passed": True, "unscored_justifications": unscored_justifications or {},
                                       "gaps_addressed": gaps_addressed})))
        self.draft = {"conclusion": conclusion}
        self.done = True
        return {"accepted": True, "message": "Draft stored for the clinical reviewer. Your work is complete."}

    def call(self, name: str, args: dict):
        fn = getattr(self, name, None)
        if fn is None or name.startswith("_") or name == "call":
            return {"error": f"unknown tool {name}"}
        try:
            return fn(**args)
        except TypeError as exc:
            return {"error": f"bad arguments for {name}: {exc}"}
