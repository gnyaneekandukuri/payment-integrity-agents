"""Pattern review agent (Maya's flow): tests each possible explanation for a hospital's DRG pattern.

It can only read fixed metrics and provider notes, and write explanations with an allowed status and citations.
It cannot conclude overpayment or fraud, contact anyone, or approve anything.
"""
import json
import re

from app import analytics
from app.agents import validators

EXPLANATIONS = {
    "data_error": "Data error (duplicates, feed or payment mapping problems)",
    "peer_comparability": "Peer group isn't comparable",
    "patient_severity": "Patients are sicker",
    "transfers": "More transfers in from other hospitals",
    "documentation_change": "Documentation change (e.g. a CDI program)",
    "clinical_definition": "Different clinical definition of sepsis",
}
STATUSES = ["supported", "supported_in_part", "weakened", "unresolved"]

SYSTEM_PROMPT = """You are a payment integrity analysis assistant for a health plan analyst (Maya Chen).
A monitoring report shows Riverside General bills a much higher share of infection-related stays as DRG 871
(sepsis with a major complication) than similar hospitals. A pattern is a QUESTION, not a finding.

Your job: test each possible explanation against the evidence, and draft the rationale for a targeted records
review if questions remain. You never decide anything; the analyst confirms every status.

Method:
1. Call list_metrics and get_notes. Read the metrics you need with get_metric.
2. For EACH of the six explanations, call record_explanation with:
   - status: 'supported' (evidence explains the pattern), 'supported_in_part' (explains some of it),
     'weakened' (evidence points against it, for the checks made), or 'unresolved' (evidence is mixed or the
     data cannot answer it). Never say 'ruled out'.
   - a short plain-language summary of the evidence, citing metric ids and note ids in the citations list.
   Meaning of 'supported': the evidence shows this explanation accounts for the gap in a way that needs no
   medical-record review. Matching timing alone is not enough.
   Rules of thumb:
   - Use each metric's 'note' for comparisons (it states which is higher); never infer direction yourself.
   - Patients are sicker: weigh member risk score together with ICU use and length of stay; if they point in
     different directions, it is 'unresolved'.
   - Documentation change: a program starting before the rise matches the timing, but claims cannot tell more
     complete documentation of real sepsis from a broader working definition, so it is 'unresolved'.
   - If the contract is silent on criteria, the clinical definition question is 'unresolved'.
   - Data checks that find nothing make a data error 'weakened' (for the checks made), not ruled out.
3. Call draft_sample_rationale: explain which unresolved questions a targeted review of medical records can
   answer, and state plainly that a targeted sample cannot be extrapolated to the hospital's other stays.

Rules: plain language for a non-clinical analyst; no words like overpayment, fraud, abuse, recoup or deny;
a statistical gap from peers is not evidence that any claim is wrong.
"""

USER_TEMPLATE = "Review question {question_id}: Riverside General, DRG 871. Begin with list_metrics."

TOOL_SPECS = [
    {"name": "list_metrics", "description": "List the available metric ids with labels.", "parameters": {"type": "object", "properties": {}, "required": []}},
    {"name": "get_metric", "description": "Get one metric's value (fixed calculation over the plan's claims).",
     "parameters": {"type": "object", "properties": {"metric_id": {"type": "string"}}, "required": ["metric_id"]}},
    {"name": "get_notes", "description": "Get provider-relations notes and the contract summary for the hospital, with note ids.",
     "parameters": {"type": "object", "properties": {}, "required": []}},
    {"name": "record_explanation", "description": "Record the status of one explanation, with a plain summary and citations (metric ids and/or note ids).",
     "parameters": {"type": "object", "properties": {
         "explanation": {"type": "string", "enum": list(EXPLANATIONS)},
         "status": {"type": "string", "enum": STATUSES},
         "summary": {"type": "string"},
         "citations": {"type": "array", "items": {"type": "string"}},
     }, "required": ["explanation", "status", "summary", "citations"]}},
    {"name": "draft_sample_rationale", "description": "Draft the rationale for a targeted records review. Must state that the sample cannot be extrapolated. Ends your work when accepted.",
     "parameters": {"type": "object", "properties": {"rationale": {"type": "string"}}, "required": ["rationale"]}},
]


class PatternReviewContext:
    def __init__(self, conn, question_id: str, run_id: str):
        self.conn, self.question_id, self.run_id = conn, question_id, run_id
        self.metrics = analytics.catalog(conn)
        self.notes = {f"N{r['id']}": dict(r) for r in conn.execute(
            "SELECT id, source, note_date, text FROM notes WHERE hospital_id=? ORDER BY note_date", (analytics.SUBJECT,))}
        self.recorded: dict[str, dict] = {}
        self.done = False

    def list_metrics(self):
        return [{"id": k, "label": v["label"]} for k, v in self.metrics.items()]

    def get_metric(self, metric_id: str):
        m = self.metrics.get(metric_id)
        return m if m else {"error": f"unknown metric id {metric_id}; call list_metrics"}

    def get_notes(self):
        return [{"note_id": k, "source": v["source"], "date": v["note_date"], "text": v["text"]} for k, v in self.notes.items()]

    def record_explanation(self, explanation: str, status: str, summary: str, citations: list):
        if explanation not in EXPLANATIONS:
            return {"accepted": False, "reason": f"unknown explanation; use one of {list(EXPLANATIONS)}"}
        if status not in STATUSES:
            return {"accepted": False, "reason": f"status must be one of {STATUSES}"}
        if re.search(r"\bruled? out\b", summary, re.IGNORECASE):
            return {"accepted": False, "reason": "do not say 'ruled out'; use weakened or unresolved"}
        bad = [c for c in citations if c not in self.metrics and c not in self.notes]
        if bad or not citations:
            return {"accepted": False, "reason": f"every citation must be a metric id or note id; unknown: {bad or 'none given'}"}
        words = validators.wording_problems(summary)
        if words:
            return {"accepted": False, "reason": f"wording not allowed: {words}"}
        self.conn.execute("DELETE FROM explanations WHERE question_id=? AND run_id=? AND name=?", (self.question_id, self.run_id, explanation))
        self.conn.execute("INSERT INTO explanations (question_id, run_id, name, status, summary, citations) VALUES (?,?,?,?,?,?)",
                          (self.question_id, self.run_id, explanation, status, summary, json.dumps(citations)))
        self.recorded[explanation] = {"status": status}
        return {"accepted": True, "recorded": len(self.recorded), "remaining": [e for e in EXPLANATIONS if e not in self.recorded]}

    def draft_sample_rationale(self, rationale: str):
        missing = [e for e in EXPLANATIONS if e not in self.recorded]
        if missing:
            return {"accepted": False, "reason": f"record every explanation first; missing: {missing}"}
        if not re.search(r"extrapolat", rationale, re.IGNORECASE):
            return {"accepted": False, "reason": "state plainly that a targeted sample cannot be extrapolated"}
        words = validators.wording_problems(rationale)
        if words:
            return {"accepted": False, "reason": f"wording not allowed: {words}"}
        self.conn.execute("UPDATE pattern_questions SET metrics=json_set(metrics, '$.rationale', ?, '$.rationale_run', ?) WHERE id=?",
                          (rationale, self.run_id, self.question_id))
        self.done = True
        return {"accepted": True, "message": "Rationale stored for the analyst. Your work is complete."}

    def call(self, name, args):
        fn = getattr(self, name, None)
        if fn is None or name.startswith("_") or name == "call":
            return {"error": f"unknown tool {name}"}
        try:
            return fn(**args)
        except TypeError as exc:
            return {"error": f"bad arguments for {name}: {exc}"}
