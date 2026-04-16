from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import TableStyle

# ── COLOR PALETTE ─────────────────────────────────────────────────────
PDF_COLORS = {
    "header_bg": "#1a1a2e",
    "header_text": colors.white,
    "border": "#dddddd",
    "row_alt": "#f9f9f9",
    "row_normal": colors.white,
    "accent_green": "#1a7a5a",
    "accent_red": "#cc3333",
    "total_bg": "#eaf4ee",
    "text_normal": colors.black,
}

# ── MARGINS ───────────────────────────────────────────────────────────
PDF_MARGINS = {
    "left": 2 * cm,
    "right": 2 * cm,
    "top": 2 * cm,
    "bottom": 2 * cm,
}

# ── COLUMN WIDTHS ────────────────────────────────────────────────────
PDF_COL_WIDTHS = {
    "abikasse": [5 * cm, 2.5 * cm, 2.5 * cm, 2.5 * cm, 2.5 * cm, 2.5 * cm],
    "hoodie_list": [5.5 * cm, 2.5 * cm, 4 * cm, 4.5 * cm],
    "participation": [8 * cm, 8 * cm],
}


def get_base_styles():
    """Return standard PDF styles used across all PDF generators."""
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Title"],
        fontSize=18,
        spaceAfter=6,
        alignment=TA_LEFT,
    )
    subtitle_style = ParagraphStyle(
        "Sub",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.grey,
        spaceAfter=16,
    )
    heading_style = ParagraphStyle(
        "Heading",
        parent=styles["Heading2"],
        fontSize=12,
        spaceBefore=14,
        spaceAfter=6,
        textColor=colors.HexColor(PDF_COLORS["header_bg"]),
    )
    normal_style = ParagraphStyle(
        "Normal2", parent=styles["Normal"], fontSize=10)
    return title_style, subtitle_style, heading_style, normal_style


def get_header_style():
    """Return header cell style for tables."""
    _, _, _, normal_style = get_base_styles()
    return ParagraphStyle(
        "Header",
        parent=normal_style,
        fontSize=9,
        textColor=PDF_COLORS["header_text"],
        fontName="Helvetica-Bold",
    )


def get_cell_style():
    """Return standard cell style for tables."""
    _, _, _, normal_style = get_base_styles()
    return ParagraphStyle("Cell", parent=normal_style, fontSize=9)


def get_standard_table_style(with_total_row=False):
    """
    Return standard table styling.

    Args:
        with_total_row: If True, adds styling for a total row at the bottom
    """
    table_style = [
        ("BACKGROUND", (0, 0), (-1, 0),
         colors.HexColor(PDF_COLORS["header_bg"])),
        ("TEXTCOLOR", (0, 0), (-1, 0), PDF_COLORS["header_text"]),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2 if with_total_row else -1),
         [colors.HexColor(PDF_COLORS["row_alt"]), PDF_COLORS["row_normal"]]),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor(PDF_COLORS["border"])),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]

    if with_total_row:
        table_style.extend([
            ("BACKGROUND", (0, -1), (-1, -1),
             colors.HexColor(PDF_COLORS["total_bg"])),
            ("LINEABOVE", (0, -1), (-1, -1), 1,
             colors.HexColor(PDF_COLORS["accent_green"])),
            ("TEXTCOLOR", (0, -1), (-1, -1),
             colors.HexColor(PDF_COLORS["accent_green"])),
        ])

    return TableStyle(table_style)
