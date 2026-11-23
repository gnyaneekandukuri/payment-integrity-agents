"""Render a case's sections into a multi-page PDF, then extract page text (PyMuPDF).

Each section starts on a new page, so a page number identifies a section of the chart.
"""
from pathlib import Path

import pymupdf as fitz

CSS = """
* { font-family: sans-serif; }
body { font-size: 10pt; line-height: 1.35; }
.hdr { font-size: 8pt; color: #555555; border-bottom: 1px solid #999999; padding-bottom: 4px; margin-bottom: 8px; }
h2 { font-size: 13pt; margin: 4px 0 8px 0; }
p { margin: 0 0 6px 0; }
table { border-collapse: collapse; width: 100%; font-size: 9pt; margin-bottom: 6px; }
th, td { border: 1px solid #888888; padding: 3px 4px; text-align: left; }
th { background-color: #EEEEEE; }
"""

PAGE = fitz.paper_rect("letter")
WHERE = PAGE + (54, 54, -54, -54)


def _header(case, hospital_name, section):
    return (
        f'<div class="hdr">{hospital_name} (fictional) &nbsp;|&nbsp; Patient: {case["patient_name"]} &nbsp;|&nbsp; '
        f'MRN {case["mrn"]} &nbsp;|&nbsp; Admit {case["claim"]["admit_date"]} &nbsp;|&nbsp; '
        f'FICTIONAL RECORD FOR DEMONSTRATION ONLY</div><h2>{section}</h2>'
    )


def render_pdf(case, hospital_name, out_path: Path) -> list[str]:
    """Write the PDF and return the section title for each page (1-based order)."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    writer = fitz.DocumentWriter(str(out_path))
    page_sections = []
    for section, body in case["sections"]:
        story = fitz.Story(html=_header(case, hospital_name, section) + body, user_css=CSS)
        more = True
        while more:
            dev = writer.begin_page(PAGE)
            more, _ = story.place(WHERE)
            story.draw(dev)
            writer.end_page()
            page_sections.append(section)
    writer.close()
    return page_sections


from app.charts import extract_pages  # noqa: E402,F401  (kept here for the seed scripts)
