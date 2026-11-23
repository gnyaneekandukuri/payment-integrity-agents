"""Why each queued claim is under clinical review. All fictional.

origin:   where the selection came from (data-mining rule, billing-pattern review, pre-payment rule, QA sample, appeal)
reason:   the specific rule or program, in plain words
concern:  why that pattern is worth a clinical look
question: what the clinical reviewer must answer
not_yours: what is decided by someone else
context:  wider background, if any (never evidence about this patient)
"""

RIVERSIDE_CONTEXT = ("Riverside General bills 38% of its infection-related stays as DRG 871, against a median of 18% at similar "
                     "community hospitals (24% against referral hospitals). This is a hospital-level pattern, not evidence about "
                     "this patient. The sample is targeted, not statistical, so its findings describe only the stays reviewed.")
SEPSIS_Q = "Does the medical record support sepsis under the criteria applied (Sepsis-3)?"
CODER = "Whether the coded MCC is supported and what the correct DRG is: decided by the coder (Lena Park)."

REASONS = {
    "CASE-ORTIZ": dict(
        origin="Data-mining rule",
        reason="Post-payment rule 'High-value sepsis with a major complication (DRG 871)': a sample of these paid claims is reviewed each quarter.",
        concern="DRG 871 pays substantially more than sepsis without a major complication or the infection DRGs, so a sample is checked for clinical support.",
        question=SEPSIS_Q, not_yours=CODER, context=""),
    "CASE-LEE": dict(
        origin="Billing-pattern review",
        reason="Targeted records review of Riverside General's DRG 871 pattern, recommended by Maya Chen (payment integrity analyst) and approved by the payment integrity manager.",
        concern="The sample tests short stays without ICU care, discharged home, where the documentation may not support sepsis with a major complication.",
        question=SEPSIS_Q, not_yours=CODER, context=RIVERSIDE_CONTEXT),
    "CASE-PATEL": dict(
        origin="Billing-pattern review",
        reason="Targeted records review of Riverside General's DRG 871 pattern, recommended by Maya Chen (payment integrity analyst) and approved by the payment integrity manager.",
        concern="The sample tests short stays without ICU care, discharged home, where the documentation may not support sepsis with a major complication.",
        question=SEPSIS_Q, not_yours=CODER, context=RIVERSIDE_CONTEXT),
    "CASE-NGUYEN": dict(
        origin="Billing-pattern review",
        reason="Targeted records review of Riverside General's DRG 871 pattern, recommended by Maya Chen (payment integrity analyst) and approved by the payment integrity manager.",
        concern="The sample tests short stays without ICU care, discharged home, where the documentation may not support sepsis with a major complication.",
        question=SEPSIS_Q, not_yours=CODER, context=RIVERSIDE_CONTEXT),
    "CASE-BROOKS": dict(
        origin="Pre-payment rule",
        reason="Pre-payment rule: DRG 871 claims above the plan's dollar threshold are held for clinical validation before payment.",
        concern="Payment is on hold until the review is complete, so prompt-pay timelines apply. Lakeside's contract specifies Sepsis-3.",
        question=SEPSIS_Q, not_yours=CODER, context=""),
    "CASE-BG01": dict(
        origin="Pre-payment rule",
        reason="Pre-payment rule: heart failure with a major complication (DRG 291) and a stay of 3 days or less.",
        concern="The major complication drives the payment; a short stay can indicate a less complex admission than the coding suggests.",
        question="Does the record clinically support the diagnoses that drive the DRG, including the major complication?",
        not_yours="The correct DRG and payment: decided by the coder.", context=""),
    "CASE-BG02": dict(
        origin="Billing-pattern review",
        reason="Targeted records review of Greenvale Community Hospital's DRG 640 pattern (nutrition and metabolic disorders), opened by a payment integrity analyst.",
        concern="Greenvale's share of DRG 640 rose in 2024; the sample checks whether the documented conditions support the major complication.",
        question="Does the record support the nutrition or metabolic diagnosis and the major complication coded?",
        not_yours="The correct DRG: decided by the coder.",
        context="Hospital-level pattern; not evidence about this patient."),
    "CASE-BG03": dict(
        origin="Data-mining rule",
        reason="Post-payment rule: acute respiratory failure as the principal diagnosis (DRG 189).",
        concern="Acute respiratory failure needs documented low oxygen or high carbon dioxide levels and matching treatment; it is commonly questioned in clinical validation.",
        question="Does the record support acute respiratory failure?", not_yours="The correct DRG: decided by the coder.", context=""),
    "CASE-BG04": dict(
        origin="Pre-payment rule",
        reason="Pre-payment rule: DRG 871 claims above the plan's dollar threshold are held for clinical validation before payment.",
        concern="Payment is on hold until the review is complete, so prompt-pay timelines apply. Records were requested from the hospital.",
        question=SEPSIS_Q, not_yours=CODER, context=""),
    "CASE-BG05": dict(
        origin="Data-mining rule",
        reason="Short inpatient stay (2 days or less) flagged for an observation-status review.",
        concern="Some short stays meet observation rather than inpatient criteria, which changes how the stay is paid.",
        question="Did the documented care meet inpatient criteria?", not_yours="Payment terms: decided by the claims team.", context=""),
    "CASE-BG06": dict(
        origin="Quality-assurance sample",
        reason="Random quality-assurance sample of completed clinical reviews.",
        concern="Checks that reviews are consistent and well documented.",
        question="Is the original review's conclusion supported by the record?", not_yours="", context=""),
    "CASE-BG07": dict(
        origin="Appeal",
        reason="The hospital appealed a prior finding on this stroke admission (DRG 064).",
        concern="The appeal includes additional documentation; the earlier conclusion must be re-checked against it.",
        question="Does the record, including the appeal documents, support the original finding?",
        not_yours="The final appeal decision: physician advisor.", context=""),
    "CASE-BG08": dict(
        origin="Data-mining rule",
        reason="Post-payment rule: renal failure with a complication (DRG 683) where acute kidney injury appears once in the coding history.",
        concern="Acute kidney injury needs a documented rise in creatinine from baseline; a single mention may not support it.",
        question="Does the record support acute kidney injury?", not_yours="The correct DRG: decided by the coder.", context=""),
    "CASE-BG09": dict(
        origin="Pre-payment rule",
        reason="Pre-payment rule: COPD with a major complication (DRG 190).",
        concern="The major complication drives the payment and must be documented with supporting findings.",
        question="Does the record support the major complication coded?", not_yours="The correct DRG: decided by the coder.", context=""),
    "CASE-BG10": dict(
        origin="Pre-payment rule",
        reason="Pre-payment rule: DRG 871 claims above the plan's dollar threshold are held for clinical validation before payment.",
        concern="Payment is on hold until the review is complete, so prompt-pay timelines apply. Crestview's contract specifies Sepsis-3.",
        question=SEPSIS_Q, not_yours=CODER, context=""),
}
