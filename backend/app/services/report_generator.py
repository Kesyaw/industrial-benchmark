"""
PDF Report Generator — Industrial Benchmark

Generates a professional benchmark health report as a downloadable PDF.
Uses ReportLab for PDF creation.
"""
import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
)


# ── Color palette ──────────────────────────────────
DARK_BG      = colors.HexColor("#0a0a0a")
CARD_BG      = colors.HexColor("#171717")
EMERALD      = colors.HexColor("#10b981")
EMERALD_DARK = colors.HexColor("#065f46")
BLUE         = colors.HexColor("#3b82f6")
YELLOW       = colors.HexColor("#eab308")
ORANGE       = colors.HexColor("#f97316")
ROSE         = colors.HexColor("#f43f5e")
WHITE        = colors.HexColor("#ffffff")
GRAY_300     = colors.HexColor("#d4d4d4")
GRAY_500     = colors.HexColor("#737373")
GRAY_700     = colors.HexColor("#404040")
GRAY_800     = colors.HexColor("#262626")


def _predicate_color(predicate: str) -> colors.HexColor:
    mapping = {
        "Sangat Sehat": EMERALD,
        "Sehat": BLUE,
        "Cukup Sehat": YELLOW,
        "Kurang Sehat": ORANGE,
        "Tidak Sehat": ROSE,
    }
    return mapping.get(predicate, GRAY_500)


def _score_color(score) -> colors.HexColor:
    if score is None:
        return GRAY_500
    if score >= 76:
        return EMERALD
    if score >= 51:
        return BLUE
    if score >= 26:
        return YELLOW
    return ROSE


def _fmt(value) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, float):
        return f"{value:,.4f}"
    return str(value)


def generate_benchmark_pdf(result: dict) -> bytes:
    """
    Generate a benchmark report PDF from a BenchmarkResult dict.
    Returns the PDF as bytes.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=15*mm, bottomMargin=15*mm,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "ReportTitle", parent=styles["Title"],
        fontSize=22, leading=26, textColor=GRAY_300,
        spaceAfter=2*mm, alignment=TA_CENTER,
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle", parent=styles["Normal"],
        fontSize=11, textColor=GRAY_500,
        alignment=TA_CENTER, spaceAfter=6*mm,
    )
    heading_style = ParagraphStyle(
        "SectionHeading", parent=styles["Heading2"],
        fontSize=14, textColor=GRAY_300,
        spaceBefore=8*mm, spaceAfter=4*mm,
    )
    body_style = ParagraphStyle(
        "BodyText", parent=styles["Normal"],
        fontSize=10, textColor=GRAY_500, leading=14,
    )
    small_style = ParagraphStyle(
        "SmallText", parent=styles["Normal"],
        fontSize=8, textColor=GRAY_500, leading=10,
    )

    elements = []

    # ── Header ──────────────────────────────────
    elements.append(Paragraph("INDUSTRIAL BENCHMARK", title_style))
    elements.append(Paragraph("Financial Health Report", subtitle_style))
    elements.append(HRFlowable(
        width="100%", thickness=1, color=GRAY_700,
        spaceAfter=6*mm,
    ))

    # ── Company Info ────────────────────────────
    company = result.get("company", "Unknown")
    sector = result.get("sector_code", "N/A")
    avg_score = result.get("average_score", 0)
    predicate = result.get("health_predicate", "N/A")
    pred_color = _predicate_color(predicate)

    info_data = [
        [
            Paragraph(f"<b>Company:</b> {company}", body_style),
            Paragraph(f"<b>Sector:</b> {sector}", body_style),
        ],
        [
            Paragraph(f"<b>Report Date:</b> {datetime.now().strftime('%d %B %Y')}", body_style),
            Paragraph(f"<b>Average Score:</b> {avg_score}", body_style),
        ],
    ]
    info_table = Table(info_data, colWidths=["50%", "50%"])
    info_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 4*mm))

    # Predicate badge
    predicate_style = ParagraphStyle(
        "Predicate", parent=styles["Normal"],
        fontSize=16, textColor=pred_color,
        alignment=TA_CENTER, spaceBefore=2*mm, spaceAfter=2*mm,
    )
    elements.append(Paragraph(f"<b>Health Predicate: {predicate}</b>", predicate_style))
    elements.append(Spacer(1, 4*mm))

    # ── Score Details Table ─────────────────────
    elements.append(Paragraph("Ratio Analysis", heading_style))

    score_details = result.get("score_details", [])

    # Table header
    header = [
        Paragraph("<b>Ratio</b>", small_style),
        Paragraph("<b>Value</b>", small_style),
        Paragraph("<b>Level</b>", small_style),
        Paragraph("<b>Score</b>", small_style),
    ]

    table_data = [header]
    row_colors = []

    for d in score_details:
        ratio_name = d.get("ratio_code", "").replace("_", " ").title()
        ratio_value = _fmt(d.get("ratio_value"))
        level_label = d.get("level_label", "N/A")
        score = d.get("score")
        s_color = _score_color(score)

        row = [
            Paragraph(ratio_name, body_style),
            Paragraph(f"<b>{ratio_value}</b>", body_style),
            Paragraph(level_label, body_style),
            Paragraph(f"<b>{score if score is not None else 'N/A'}</b>", body_style),
        ]
        table_data.append(row)
        row_colors.append(s_color)

    col_widths = ["35%", "22%", "25%", "18%"]
    detail_table = Table(table_data, colWidths=col_widths)

    style_cmds = [
        # Header row
        ("BACKGROUND", (0, 0), (-1, 0), GRAY_800),
        ("TEXTCOLOR", (0, 0), (-1, 0), GRAY_300),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
        # All rows
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
        ("TOPPADDING", (0, 1), (-1, -1), 5),
        # Grid
        ("LINEBELOW", (0, 0), (-1, 0), 1, GRAY_700),
        ("LINEBELOW", (0, 1), (-1, -2), 0.5, GRAY_800),
        ("LINEBELOW", (0, -1), (-1, -1), 1, GRAY_700),
    ]

    # Alternate row backgrounds
    for i in range(1, len(table_data)):
        bg = CARD_BG if i % 2 == 0 else colors.HexColor("#1a1a1a")
        style_cmds.append(("BACKGROUND", (0, i), (-1, i), bg))

    detail_table.setStyle(TableStyle(style_cmds))
    elements.append(detail_table)

    # ── Raw Ratios Table ────────────────────────
    ratios = result.get("ratios", {})
    if ratios:
        elements.append(Spacer(1, 6*mm))
        elements.append(Paragraph("Computed Ratios (All)", heading_style))

        ratio_header = [
            Paragraph("<b>Metric</b>", small_style),
            Paragraph("<b>Value</b>", small_style),
        ]
        ratio_rows = [ratio_header]
        for code, val in ratios.items():
            ratio_rows.append([
                Paragraph(code.replace("_", " ").title(), body_style),
                Paragraph(f"<b>{_fmt(val)}</b>", body_style),
            ])

        ratio_table = Table(ratio_rows, colWidths=["55%", "45%"])
        r_style = [
            ("BACKGROUND", (0, 0), (-1, 0), GRAY_800),
            ("TEXTCOLOR", (0, 0), (-1, 0), GRAY_300),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("LINEBELOW", (0, 0), (-1, 0), 1, GRAY_700),
            ("LINEBELOW", (0, -1), (-1, -1), 1, GRAY_700),
        ]
        for i in range(1, len(ratio_rows)):
            bg = CARD_BG if i % 2 == 0 else colors.HexColor("#1a1a1a")
            r_style.append(("BACKGROUND", (0, i), (-1, i), bg))
        ratio_table.setStyle(TableStyle(r_style))
        elements.append(ratio_table)

    # ── Footer ──────────────────────────────────
    elements.append(Spacer(1, 10*mm))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=GRAY_700, spaceAfter=3*mm))
    footer_style = ParagraphStyle(
        "Footer", parent=styles["Normal"],
        fontSize=7, textColor=GRAY_700, alignment=TA_CENTER,
    )
    elements.append(Paragraph(
        f"Generated by Industrial Benchmark Engine v2.0 on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        footer_style,
    ))
    elements.append(Paragraph(
        "This report is for internal analysis purposes only.",
        footer_style,
    ))

    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer.read()
