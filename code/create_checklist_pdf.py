"""Build the Gradescope checklist PDF from the generated cleaning evidence."""

from pathlib import Path
import subprocess

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
PDF_PATH = ROOT / "Module_6_Cleaning_Checklist.pdf"


def para(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(str(text).replace("&", "&amp;"), style)


def evidence_table(path: Path, columns: list[str], widths: list[float], styles: dict) -> Table:
    frame = pd.read_csv(path)
    rows = [[para(column, styles["table_header"]) for column in columns]]
    for _, row in frame.iterrows():
        rows.append([para(row.get(column, ""), styles["table_cell"]) for column in columns])
    table = Table(rows, colWidths=widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e79")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eef4f8")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    return table


def main() -> None:
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="CenterTitle", parent=styles["Title"], alignment=TA_CENTER, fontSize=16, leading=20))
    styles.add(ParagraphStyle(name="Small", parent=styles["BodyText"], fontSize=8.5, leading=11))
    styles.add(ParagraphStyle(name="table_header", parent=styles["Small"], textColor=colors.white, fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle(name="table_cell", parent=styles["Small"], fontSize=7.2, leading=9))

    document = SimpleDocTemplate(
        str(PDF_PATH), pagesize=letter, rightMargin=0.55 * inch, leftMargin=0.55 * inch,
        topMargin=0.5 * inch, bottomMargin=0.5 * inch,
    )
    commit_id = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    story = [
        Paragraph("DSO 576 — Project Data Cleaning Assignment", styles["CenterTitle"]),
        Spacer(1, 8),
        Paragraph("Project: AI Workforce Investment Planner", styles["Heading2"]),
        Paragraph("Student: [ENTER YOUR NAME]", styles["BodyText"]),
        Paragraph("Branch: cleaning-emerald", styles["BodyText"]),
        Paragraph("Branch URL: PENDING — push the branch, then replace with the GitHub branch URL", styles["BodyText"]),
        Paragraph(f"Submitted commit ID for this draft: {commit_id}", styles["BodyText"]),
        Spacer(1, 8),
        Paragraph("Project vision and question", styles["Heading2"]),
        Paragraph("The project supports workforce-development decisions about occupations that may deserve priority for AI-transition training and reskilling. The business question is which occupations should be prioritized based on observed AI exposure, task penetration, employment, wages, and projected employment change.", styles["BodyText"]),
        Spacer(1, 6),
        Paragraph("14-item checklist", styles["Heading2"]),
    ]

    checklist = [
        (1, "Done", "Vision, business question, and main comparison are stated above and in README."),
        (2, "Done", "Occupation tables use SOC keys; task statements use Task ID; task penetration uses normalized task text and penetration."),
        (3, "Done", "Sources and versions are listed in README. Raw files remain unchanged under data/raw/."),
        (4, "Done", "Numeric conversions and failed conversions are recorded in cleaning_conversions.csv; failed conversions were zero."),
        (5, "Done", "Whitespace and case-normalized matching keys are added while original source text is retained."),
        (6, "Done", "Exact and normalized duplicate counts are reported; seven task-penetration duplicates were removed."),
        (7, "Done", "Missing values are reported before/after; missing values were retained rather than imputed."),
        (8, "Done", "Missing wage markers and the unmatched Legislators occupation are flagged for review."),
        (9, "Done", "The exposure-to-BLS merge reports 755 matches and one unmatched exposure record."),
        (10, "Done", "Starting and final row counts are recorded in cleaning_row_counts.csv."),
        (11, "Unresolved", "Cleaning metrics are validated, but final project scoring calculations and their denominators have not yet been implemented."),
        (12, "Done", "Five original/expected/actual record checks are recorded in record_checks.csv."),
        (13, "Done", "The notebook reruns inspection and cleaning from raw files; outputs were regenerated successfully."),
        (14, "Done", "Limitations include the unmatched Legislators occupation and source-level missing fields."),
    ]
    checklist_rows = [[para("#", styles["table_header"]), para("Status", styles["table_header"]), para("Evidence", styles["table_header"])]]
    checklist_rows += [[para(n, styles["table_cell"]), para(status, styles["table_cell"]), para(evidence, styles["table_cell"])] for n, status, evidence in checklist]
    checklist_table = Table(checklist_rows, colWidths=[0.3 * inch, 0.8 * inch, 6.6 * inch], repeatRows=1)
    checklist_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e79")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eef4f8")]),
    ]))
    story.append(checklist_table)

    story += [Spacer(1, 10), Paragraph("Cleaning decision log", styles["Heading2"])]
    decisions = [
        ("Preserve raw files", "The assignment requires unchanged sources and reproducibility.", "Raw files are read from data/raw/ and never overwritten."),
        ("Keep SOC identifiers as strings and derive soc6", "Prevents identifier corruption and supports cross-source joins.", "Invalid key counts are recorded; all source key formats were valid."),
        ("Normalize whitespace and task case for matching", "Prevents avoidable text-match failures while retaining source text.", "Changed values and normalized duplicate groups are reported."),
        ("Deduplicate only agreeing task/penetration pairs", "Repeated identical observations add no information; conflicts require review.", "Seven duplicates removed; zero conflicting task groups found."),
        ("Convert formatted numeric fields", "Wages and percentages must be numeric for checks and calculations.", "All nonmissing conversions succeeded."),
        ("Use BLS line items for occupation joins", "Summary rows could double-count occupations.", "831 line items used; 755 of 756 exposure records matched."),
        ("Retain missing values", "Missing does not mean zero and should not be silently imputed.", "Missing counts are reported in cleaning_missing_values.csv."),
    ]
    decision_rows = [[para("Rule", styles["table_header"]), para("Reason", styles["table_header"]), para("Check", styles["table_header"])]]
    decision_rows += [[para(a, styles["table_cell"]), para(b, styles["table_cell"]), para(c, styles["table_cell"])] for a, b, c in decisions]
    decision_table = Table(decision_rows, colWidths=[2.0 * inch, 2.35 * inch, 3.35 * inch], repeatRows=1)
    decision_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e79")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eef4f8")]),
    ]))
    story.append(decision_table)

    story += [Spacer(1, 10), Paragraph("Five record checks", styles["Heading2"])]
    story.append(evidence_table(OUTPUTS / "record_checks.csv", ["check_id", "case", "original", "expected", "actual", "matches_expected"], [0.45 * inch, 1.0 * inch, 1.55 * inch, 1.7 * inch, 1.55 * inch, 0.75 * inch], styles))

    story += [Spacer(1, 10), Paragraph("Codex suggestion review", styles["Heading2"]), Paragraph("Codex suggested normalizing SOC identifiers to a six-digit join key and normalizing task text for matching. I checked that suggestion against the raw data by comparing key validity, duplicate counts, merge row counts, the one unmatched Legislators record, and the five individual record checks. The checks supported using derived normalized keys while preserving the original source fields.", styles["BodyText"])]
    story += [Spacer(1, 10), Paragraph("Remaining limitations", styles["Heading2"]), Paragraph("The exposure record for Legislators (11-1031) is absent from the BLS line-item extract and is preserved as unmatched. Several source fields are genuinely missing, including BLS wage/training fields and O*NET task metadata. The final project priority score and its weighting/denominator rules have not yet been implemented.", styles["BodyText"])]

    document.build(story)
    print(PDF_PATH)


if __name__ == "__main__":
    main()
