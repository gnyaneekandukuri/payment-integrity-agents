"""Fixed checks the agent cannot bypass. No AI in this file.

- Citation: a quote must exist on the cited page (whitespace, case and table separators ignored).
- Wording: drafts may not use accusatory or payment-action words.
- Consistency: a draft conclusion must match the evidence and the SOFA result.
"""
import re

FORBIDDEN = ["overpay", "fraud", "abuse", "upcod", "recoup", "deny", "denial", "refund", "penalt"]


def _normalise_with_map(text: str) -> tuple[str, list[int]]:
    """Lowercase, drop table separators, collapse whitespace; keep a map back to original offsets."""
    out, index_map, prev_space = [], [], False
    for i, ch in enumerate(text):
        c = " " if ch in "|\n\t\r" or ch.isspace() else ch.lower()
        if c == " ":
            if prev_space or not out:
                continue
            prev_space = True
        else:
            prev_space = False
        out.append(c)
        index_map.append(i)
    return "".join(out).rstrip(), index_map


def locate_quote(page_text: str, quote: str) -> tuple[int, int] | None:
    """Return (start, end) offsets of the quote in the original page text, or None."""
    quote = (quote or "").strip()
    if len(quote) < 4:
        return None
    norm_page, index_map = _normalise_with_map(page_text)
    norm_quote, _ = _normalise_with_map(quote)
    pos = norm_page.find(norm_quote)
    if pos == -1:
        return None
    start = index_map[pos]
    end = index_map[min(pos + len(norm_quote) - 1, len(index_map) - 1)] + 1
    return start, end


def wording_problems(text: str) -> list[str]:
    lowered = (text or "").lower()
    return [w for w in FORBIDDEN if re.search(rf"\b{w}", lowered)]


def check_draft(conclusion: str, sofa: dict | None, infection_ids: list[int], gaps: list[dict],
                justifications: dict, rationale: str, cited_ids: list[int], known_ids: set[int]) -> list[str]:
    """Return a list of problems; empty means the draft is consistent."""
    problems = []
    if conclusion not in ("demonstrated", "not_demonstrated", "cannot_determine"):
        return [f"unknown conclusion '{conclusion}'"]
    if sofa is None:
        problems.append("compute_sofa has not been run since the last evidence was recorded")
    missing_ids = [i for i in cited_ids if i not in known_ids]
    if missing_ids:
        problems.append(f"rationale cites evidence ids that don't exist: {missing_ids}")
    if not cited_ids:
        problems.append("the draft must cite at least one evidence id")
    words = wording_problems(rationale)
    if words:
        problems.append(f"wording not allowed in a clinical review draft: {words}")
    if sofa is None:
        return problems

    if conclusion == "demonstrated":
        if not infection_ids:
            problems.append("'demonstrated' needs recorded evidence of suspected or confirmed infection")
        if not sofa["threshold_met"]:
            problems.append(f"'demonstrated' needs a SOFA change of 2 or more from scored systems; computed change is {sofa['change_total']}")
    elif conclusion == "not_demonstrated":
        if sofa["threshold_met"]:
            problems.append("'not_demonstrated' contradicts the computed SOFA change (threshold met)")
        for system in sofa["unscored_systems"]:
            status = sofa["systems"][system]["status"]
            if status == "baseline_uncertain":
                problems.append(f"'not_demonstrated' is not allowed while the {system} baseline is uncertain")
            elif not justifications.get(system):
                problems.append(f"'not_demonstrated' needs an explicit justification for the unscored {system} system "
                                f"(status: {status}), e.g. why the record shows no dysfunction")
        conflicting = [g for g in gaps if g["kind"] == "conflicting"]
        if conflicting:
            problems.append("'not_demonstrated' is not allowed while conflicting evidence is recorded; use cannot_determine")
    elif conclusion == "cannot_determine":
        if not [g for g in gaps if g["kind"] in ("missing", "conflicting")]:
            problems.append("'cannot_determine' needs at least one recorded missing or conflicting item")
    return problems
