"""PDF -> page text (PyMuPDF), shared by the seed scripts and record uploads."""
import re
from pathlib import Path

import pymupdf as fitz

FLAGS = fitz.TEXTFLAGS_WORDS & ~fitz.TEXT_PRESERVE_LIGATURES  # "fi" stays two letters


def _page_lines(page) -> str:
    """Rebuild reading lines from word positions so table rows stay on one line.

    A wide horizontal gap between words (a table column boundary) becomes ' | '.
    """
    words = page.get_text("words", flags=FLAGS)
    words.sort(key=lambda w: (round(w[1] / 3), w[0]))
    lines, current, last_y = [], [], None
    for x0, y0, x1, _y1, text, *_ in words:
        key = round(y0 / 3)
        if last_y is not None and abs(key - last_y) > 1:
            lines.append(current)
            current = []
        current.append((x0, x1, text))
        last_y = key
    if current:
        lines.append(current)
    out = []
    for line in lines:
        line.sort()
        parts, prev_x1 = [], None
        for x0, x1, text in line:
            if prev_x1 is not None:
                parts.append(" | " if x0 - prev_x1 > 14 else " ")
            parts.append(text)
            prev_x1 = x1
        out.append("".join(parts))
    return "\n".join(out)


def extract_pages(pdf_path: Path) -> list[str]:
    with fitz.open(str(pdf_path)) as doc:
        return [_page_lines(page) for page in doc]


HEADER = re.compile(r"(fictional|FICTIONAL RECORD|DEMONSTRATION ONLY|Patient:|MRN)", re.IGNORECASE)


def guess_section(text: str, page_no: int) -> str:
    """Best-effort section title: the first short line that is not the running header."""
    for line in text.splitlines()[:8]:
        clean = line.strip()
        if not clean or HEADER.search(clean) or "|" in clean or ":" in clean:
            continue
        if 3 <= len(clean) <= 60:
            return clean
    return f"Page {page_no}"


def text_layer_report(texts: list[str]) -> list[int]:
    """Pages with almost no extractable text (likely scanned images that need OCR)."""
    return [i for i, t in enumerate(texts, start=1) if len(t.strip()) < 40]
