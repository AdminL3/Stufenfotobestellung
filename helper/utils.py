from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.pagesizes import A4
from collections import defaultdict
from reportlab.lib.units import cm
from reportlab.lib import colors
from datetime import datetime
import streamlit as st
from helper.auth import get_headers
from helper.constants import (
    SUPABASE_URL,
    BUCKET_NAME,
    MOTTO_LABELS,
    STUFEN_LABELS,
    NAME_OPTIONS,
    COLOR_OPTIONS,
    SIZE_OPTIONS,
    ORDERS_URL,
    IMAGES_URL,
)
from helper.config import (
    NORMAL_IMAGE_PRICE,
    UPLOAD_PHOTO_PRICE,
    AMOUNT_OF_FREE_IMAGES,
)
import requests
import zipfile
import io
import os


def get_headers():
    key = os.environ.get("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY")
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }


def update_payment(order_id, paid: bool):
    resp = requests.patch(
        f"{ORDERS_URL}?id=eq.{order_id}",
        json={"paid": paid},
        headers={**get_headers(), "Prefer": "return=minimal"},
        timeout=10
    )
    return resp.status_code in [200, 201, 204]


def build_image_map(images):
    img_map = defaultdict(list)
    for img in sorted(images, key=lambda x: x.get("position") or 0):
        img_map[img["order_id"]].append(img["url"])
    return img_map


def build_picture_map(orders):
    picture_map = defaultdict(list)
    for o in orders:
        name = o.get("name", "?")
        is_paid = o.get("paid", False)

        lk = o.get("leistungskurs")
        gk = o.get("grundkurs")
        for t in (o.get("lk_typ") or []):
            picture_map[("lk", lk, t)].append((name, is_paid))
        for t in (o.get("gk_typ") or []):
            picture_map[("gk", gk, t)].append((name, is_paid))
        for m in (o.get("mottowoche") or []):
            picture_map[("motto", int(m))].append((name, is_paid))
        for s in (o.get("stufenfotos") or []):
            picture_map[("stufe", int(s))].append((name, is_paid))
        extra_photos = o.get("extra_photos", 0) or 0
        if extra_photos > 0:
            picture_map[("extra",)].append(
                (f"{name} (x{extra_photos})", is_paid)
            )
    return picture_map


def format_label(key):
    if key[0] == "lk":
        _, lk, t = key
        return f"{lk} - {t}"
    elif key[0] == "gk":
        _, gk, t = key
        return f"{gk} - {t}"
    elif key[0] == "motto":
        return f"{MOTTO_LABELS.get(key[1], key[1])}"
    elif key[0] == "stufe":
        return f"Stufenfoto: {STUFEN_LABELS.get(key[1], key[1])}"
    elif key[0] == "extra":
        return "Zusatzfotos"
    return str(key)


def calculate_extra_cost(num_images=0, extra_photos=0, order=None):
    if order is not None:
        num_images = order.get("image_count") or 0
        extra_photos = order.get("extra_photos") or 0
    cost = 0.0
    if num_images > AMOUNT_OF_FREE_IMAGES:
        cost += (num_images - AMOUNT_OF_FREE_IMAGES) * NORMAL_IMAGE_PRICE
    cost += extra_photos * UPLOAD_PHOTO_PRICE
    return cost


# ── SHARED PDF STYLES ─────────────────────────────────────────────────────────
def _base_styles():
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title", parent=styles["Title"],
                                 fontSize=18, spaceAfter=6, alignment=TA_LEFT)
    subtitle_style = ParagraphStyle("Sub", parent=styles["Normal"],
                                    fontSize=9, textColor=colors.grey, spaceAfter=16)
    heading_style = ParagraphStyle("Heading", parent=styles["Heading2"],
                                   fontSize=12, spaceBefore=14, spaceAfter=6,
                                   textColor=colors.HexColor("#1a1a2e"))
    normal_style = ParagraphStyle(
        "Normal2", parent=styles["Normal"], fontSize=10)
    return title_style, subtitle_style, heading_style, normal_style


def generate_pdf(picture_map):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    title_style, subtitle_style, heading_style, normal_style = _base_styles()
    story = []

    story.append(Paragraph("Fotobestellung - Bildübersicht", title_style))
    story.append(HRFlowable(width="100%", thickness=1,
                 color=colors.HexColor("#dddddd"), spaceAfter=16))

    for label, entries in picture_map.items():
        story.append(Paragraph(
            f"{format_label(label)}  -  {len(entries)} Bestellungen", heading_style))

        paid_names = [n for n, paid in entries if paid]
        unpaid_names = [n for n, paid in entries if not paid]
        table_data = []

        if paid_names:
            table_data.append([
                Paragraph("<b>✓ Bezahlt</b>", ParagraphStyle(
                    "", parent=normal_style, textColor=colors.HexColor("#1a7a5a"), fontSize=9)),
                Paragraph(", ".join(paid_names), normal_style)
            ])
        if unpaid_names:
            table_data.append([
                Paragraph("<b>⏳ Ausstehend</b>", ParagraphStyle(
                    "", parent=normal_style, textColor=colors.HexColor("#cc3333"), fontSize=9)),
                Paragraph(", ".join(unpaid_names), normal_style)
            ])

        if table_data:
            t = Table(table_data, colWidths=[3.5*cm, 13*cm])
            t.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 0), (-1, -1),
                 [colors.HexColor("#f9f9f9"), colors.white]),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LINEBELOW", (0, -1), (-1, -1), 0.5, colors.HexColor("#eeeeee")),
            ]))
            story.append(t)
        story.append(Spacer(1, 6))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()


def generate_abikasse_pdf(orders):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    title_style, subtitle_style, heading_style, normal_style = _base_styles()

    header_style = ParagraphStyle("Header", parent=normal_style,
                                  fontSize=9, textColor=colors.white, fontName="Helvetica-Bold")
    cell_style = ParagraphStyle("Cell", parent=normal_style, fontSize=9)
    total_style = ParagraphStyle("Total", parent=normal_style,
                                 fontSize=10, fontName="Helvetica-Bold")

    story = []
    story.append(Paragraph("Abikasse - Gratis-Bilder Abrechnung", title_style))
    story.append(HRFlowable(width="100%", thickness=1,
                 color=colors.HexColor("#dddddd"), spaceAfter=16))

    # Table header
    col_widths = [5*cm, 2.5*cm, 2.5*cm, 2.5*cm]
    header_row = [
        Paragraph("Name", header_style),
        Paragraph("Bilder\ngesamt", header_style),
        Paragraph(f"Gratis\n(max {AMOUNT_OF_FREE_IMAGES})", header_style),
        Paragraph("Kosten Abikasse", header_style),
    ]

    rows = [header_row]
    total_free_images = 0
    total_cost = 0.0

    for order in orders:
        num_images = order.get("image_count") or 0
        free_images = min(num_images, AMOUNT_OF_FREE_IMAGES)
        if free_images == 0:
            continue
        name = order.get("name", "?")
        cost = free_images * NORMAL_IMAGE_PRICE
        total_free_images += free_images
        total_cost += cost

        rows.append([
            Paragraph(name, cell_style),
            Paragraph(str(num_images), cell_style),
            Paragraph(str(free_images), cell_style),
            Paragraph(f"{cost:.2f}€", cell_style)
        ])

    # Totals row
    rows.append([
        Paragraph("GESAMT", total_style),
        Paragraph("", cell_style),
        Paragraph(str(total_free_images), total_style),
        Paragraph(f"{total_cost:.2f}€", total_style),
    ])

    t = Table(rows, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2),
         [colors.HexColor("#f9f9f9"), colors.white]),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#eaf4ee")),
        ("LINEABOVE", (0, -1), (-1, -1), 1, colors.HexColor("#1a7a5a")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#dddddd")),
    ]))
    story.append(t)

    doc.build(story)
    buffer.seek(0)
    return buffer.read()


def generate_hoodie_pdf(merch_orders):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    title_style, subtitle_style, heading_style, normal_style = _base_styles()
    header_style = ParagraphStyle("Header", parent=normal_style,
                                  fontSize=9, textColor=colors.white, fontName="Helvetica-Bold")
    cell_style = ParagraphStyle("Cell", parent=normal_style, fontSize=9)

    story = []
    story.append(Paragraph("Hoodie Bestellungen - Übersicht", title_style))

    story.append(HRFlowable(width="100%", thickness=1,
                 color=colors.HexColor("#dddddd"), spaceAfter=16))

    # ── Color x Size Matrix ───────────────────────────────
    story.append(Paragraph("Farben x Größen Übersicht", heading_style))

    # Build color x size matrix
    color_size_matrix = defaultdict(lambda: defaultdict(int))
    for o in merch_orders:
        color = o.get("color", "?")
        size = o.get("size", "?")
        color_size_matrix[color][size] += 1

    # Create matrix table with size headers
    matrix_rows = [[Paragraph("Farbe", header_style)] +
                   [Paragraph(size, header_style) for size in SIZE_OPTIONS] +
                   [Paragraph("Σ", header_style)]]

    total_per_size = defaultdict(int)
    for color in COLOR_OPTIONS:
        row = [Paragraph(color, cell_style)]
        color_total = 0
        for size in SIZE_OPTIONS:
            count = color_size_matrix[color][size]
            row.append(Paragraph(str(count) if count > 0 else "-", cell_style))
            total_per_size[size] += count
            color_total += count
        row.append(Paragraph(str(color_total) if color_total > 0 else "-",
                             ParagraphStyle("T", parent=cell_style, fontName="Helvetica-Bold")))
        matrix_rows.append(row)

    col_widths = [2.8*cm] + [1.2*cm] * len(SIZE_OPTIONS) + [1.2*cm]
    t_matrix = Table(matrix_rows, colWidths=col_widths)
    t_matrix.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2),
         [colors.HexColor("#f9f9f9"), colors.white]),
        ("BACKGROUND", (-1, 1), (-1, -1), colors.HexColor("#eaf4ee")),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#dddddd")),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("ALIGNMENT", (0, 0), (-1, -1), "CENTER"),
    ]))
    story.append(t_matrix)
    story.append(Spacer(1, 20))

    # ── Full order list ───────────────────────────────────
    story.append(Paragraph("Alle Bestellungen", heading_style))
    list_rows = [[
        Paragraph("Name", header_style),
        Paragraph("Größe", header_style),
        Paragraph("Farbe", header_style),
    ]]
    for o in sorted(merch_orders, key=lambda x: x.get("name", "")):
        list_rows.append([
            Paragraph(o.get("name", "?"), cell_style),
            Paragraph(o.get("size", "?"), cell_style),
            Paragraph(o.get("color", "?"), cell_style),
        ])

    t_list = Table(list_rows, colWidths=[5.5*cm, 2.5*cm, 4*cm])
    t_list.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.HexColor("#f9f9f9"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#dddddd")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t_list)

    doc.build(story)
    buffer.seek(0)
    return buffer.read()


def generate_teilnahme_pdf(orders, merch_orders):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    title_style, subtitle_style, heading_style, normal_style = _base_styles()
    header_style = ParagraphStyle("Header", parent=normal_style,
                                  fontSize=9, textColor=colors.white, fontName="Helvetica-Bold")
    cell_style = ParagraphStyle("Cell", parent=normal_style, fontSize=9)

    foto_names_submitted = {o.get("name") for o in orders}
    merch_names_submitted = {o.get("name") for o in merch_orders}

    story = []
    story.append(Paragraph("Übersicht", title_style))

    story.append(HRFlowable(width="100%", thickness=1,
                 color=colors.HexColor("#dddddd"), spaceAfter=16))

    # ── Foto participation table ───────────────────────────────
    story.append(Paragraph("Fotobestellung", heading_style))

    foto_submitted = sorted(
        [n for n in NAME_OPTIONS if n in foto_names_submitted])
    foto_missing = sorted(
        [n for n in NAME_OPTIONS if n not in foto_names_submitted])

    foto_rows = [[
        Paragraph("Bestellt", header_style),
        Paragraph("Noch nicht bestellt", header_style),
    ]]

    max_rows = max(len(foto_submitted), len(foto_missing))
    for i in range(max_rows):
        submitted_name = Paragraph(
            foto_submitted[i] if i < len(foto_submitted) else "",
            ParagraphStyle("Sub", parent=cell_style,
                           textColor=colors.HexColor("#1a7a5a"))
        ) if i < len(foto_submitted) else Paragraph("", cell_style)

        missing_name = Paragraph(
            foto_missing[i] if i < len(foto_missing) else "",
            ParagraphStyle("Sub", parent=cell_style,
                           textColor=colors.HexColor("#cc3333"))
        ) if i < len(foto_missing) else Paragraph("", cell_style)

        foto_rows.append([submitted_name, missing_name])

    t_foto = Table(foto_rows, colWidths=[8*cm, 8*cm])
    t_foto.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.HexColor("#f9f9f9"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#dddddd")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(t_foto)

    story.append(Spacer(1, 20))

    # ── Hoodie participation table ───────────────────────────────
    story.append(Paragraph("Hoodie Bestellung", heading_style))

    merch_submitted = sorted(
        [n for n in NAME_OPTIONS if n in merch_names_submitted])
    merch_missing = sorted(
        [n for n in NAME_OPTIONS if n not in merch_names_submitted])

    merch_rows = [[
        Paragraph("Bestellt", header_style),
        Paragraph("Noch nicht bestellt", header_style),
    ]]

    max_rows = max(len(merch_submitted), len(merch_missing))
    for i in range(max_rows):
        submitted_name = Paragraph(
            merch_submitted[i] if i < len(merch_submitted) else "",
            ParagraphStyle("Sub", parent=cell_style,
                           textColor=colors.HexColor("#1a7a5a"))
        ) if i < len(merch_submitted) else Paragraph("", cell_style)

        missing_name = Paragraph(
            merch_missing[i] if i < len(merch_missing) else "",
            ParagraphStyle("Sub", parent=cell_style,
                           textColor=colors.HexColor("#cc3333"))
        ) if i < len(merch_missing) else Paragraph("", cell_style)

        merch_rows.append([submitted_name, missing_name])

    t_merch = Table(merch_rows, colWidths=[8*cm, 8*cm])
    t_merch.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.HexColor("#f9f9f9"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#dddddd")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(t_merch)

    doc.build(story)
    buffer.seek(0)
    return buffer.read()


def create_zip_all(images_list, order_lookup):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        for img in images_list:
            url = img["url"]
            order_id = img["order_id"]
            pos = img.get("position", 0)
            person_name = order_lookup.get(
                order_id, "unknown").replace(" ", "_")
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                filename = f"{person_name}_{order_id[:8]}_{pos:02d}.jpg"
                z.writestr(filename, response.content)
    buffer.seek(0)
    return buffer


def upload_image_to_supabase(file, filename: str) -> str | None:
    upload_url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{filename}"
    upload_headers = {
        **get_headers(),
        "Content-Type": file.type,
    }
    response = requests.post(
        upload_url, headers=upload_headers, data=file.getvalue(), timeout=10)
    if response.status_code in [200, 201]:
        return f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{filename}"
    else:
        st.error(f"❌ Bild-Upload fehlgeschlagen ({filename}): {response.text}")
        return None


def fetch_images():
    resp = requests.get(
        IMAGES_URL, headers=get_headers(),
        params={"select": "*", "order": "order_id,position.asc"},
        timeout=10
    )
    return resp.json() if resp.status_code == 200 else []


def archive_order(order_id, archived: bool):
    resp = requests.patch(
        f"{ORDERS_URL}?id=eq.{order_id}",
        json={"archived": archived},
        headers={**get_headers(), "Prefer": "return=minimal"},
        timeout=10
    )
    return resp.status_code in [200, 201, 204]


def fetch_orders():
    resp = requests.get(
        ORDERS_URL, headers=get_headers(),
        params={"select": "*", "order": "created_at.asc",
                "archived": "eq.false"},
        timeout=10
    )
    return resp.json() if resp.status_code == 200 else []


def fetch_archived_orders():
    resp = requests.get(
        ORDERS_URL, headers=get_headers(),
        params={"select": "*", "order": "created_at.asc", "archived": "eq.true"},
        timeout=10
    )
    return resp.json() if resp.status_code == 200 else []


def fetch_merch_orders():
    url = os.environ.get("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
    if not url:
        return []
    resp = requests.get(
        f"{url}/rest/v1/abimerch",
        headers=get_headers(),
        params={"select": "*", "order": "created_at.asc"},
        timeout=10
    )
    return resp.json() if resp.status_code == 200 else []
