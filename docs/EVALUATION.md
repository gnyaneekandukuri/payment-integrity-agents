# Evaluation: claim review agent

*Sunday 22 Nov 2026. Model: `gpt-5.4-mini`. All cases are fictional; the expectations are our own test answers, not clinical validation.*

## What we measured
Each case was run **3 times live** (the model is not deterministic), and every run was checked automatically (`backend/tools/evaluate.py`):

| Check | What it means |
|---|---|
| **Conclusion** | Supported / not supported / unable to determine matches the expected answer |
| **SOFA in range** | The fixed calculator's change total falls in the expected range |
| **Key facts** | The decisive facts are cited (e.g. Ortiz: norepinephrine 0.08, creatinine 1.6, baseline 0.8), from any page |
| **Citations valid** | Every stored quote is found on the page it cites |
| **No forbidden words** | No "overpayment", "fraud", "deny" and similar in the draft |
| **Case-specific** | Patel: kidney baseline marked uncertain and the mental-status conflict recorded. Nguyen: malnutrition (E43) coding question. Kim: encephalopathy (G93.41) coding question |

## Results (21 runs: 7 cases × 3)
| Case | What it tests | Expected | Conclusion correct | All checks |
|---|---|---|---|---|
| Ortiz | Clear sepsis (vasopressors, kidney) | Supported | 3/3 | 3/3 |
| Lee | Complete record, no organ damage | Not supported | 3/3 | 3/3 |
| Patel | Uncertain baseline, conflicting notes | Unable to determine | 3/3 | 1/3 → **3/3 after fix** |
| Nguyen | Sepsis supported, weak malnutrition code | Supported + coding question | 3/3 | 3/3 |
| Brooks | Change exactly at the threshold (2) | Supported | 3/3 | 3/3 |
| Adeyemi (upload) | New record, three organ systems | Supported | 3/3 | 3/3 |
| Kim (upload) | New record, contradicted encephalopathy code | Not supported + coding question | 3/3 | 3/3 |

**Overall:** conclusion correct **21/21**, citations valid **21/21**, forbidden words **0/21**. About 48k input tokens per review on average.

## What failed, and what changed
1. **Patel's reasoning was incomplete in 2 of 3 runs**, although the conclusion was right. One run did not cite the nurse's "confused" note, and another did not record the disagreement as a conflict. **Fix:** the instructions now say to record both sides of a disagreement as evidence and as a conflict gap. Re-run: **3/3**. (The other cases were measured before this change.)
2. **My first "key evidence" metric was too literal.** It required the exact sentence from the answer key, and failed runs that cited the same fact from another page (e.g. the outside lab report instead of the admission note). **Fix:** check facts by organ system and value, from any page.

Earlier, during the build (Phase 2), failures were fixed in the rules, not only in the prompt:
- chronic conditions must name their organ system
- logged conflicts must be explained or lead to "unable to determine"
- "no home oxygen" is treated as context, not disease
- evidence is numbered per run so replays are identical

## Limits (say these out loud)
- **Seven cases, three runs each.** This checks behavior and consistency, not accuracy at scale.
- **The answer keys are our own,** written alongside the fictional charts. No clinician has validated them.
- **Clean, digital records.** Real records include scans, faxes and hundreds of pages, which needs OCR and layout-aware parsing.
- **In production,** ground truth would be reviewer decisions (fast) and appeal outcomes (slow). Reviewer agreement and overturn rates would be the core metrics.
