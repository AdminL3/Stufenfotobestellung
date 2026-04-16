from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.pagesizes import A4
from collections import defaultdict
from reportlab.lib.units import cm
from reportlab.lib import colors
from datetime import datetime
import streamlit as st
from helper.constants import (
    SUPABASE_URL,
    SUPABASE_KEY,
    BUCKET_NAME,
    MOTTO_LABELS,
    STUFEN_LABELS,
    NAME_OPTIONS,
    COLOR_OPTIONS,
    SIZE_OPTIONS,
    ORDERS_URL,
    IMAGES_URL,
    BASE_HEADERS
)
from helper.config import (
    NORMAL_IMAGE_PRICE,
    UPLOAD_PHOTO_PRICE,
    AMOUNT_OF_FREE_IMAGES,
    PRINTING_COST
)
import requests
import zipfile
import io


def update_payment(order_id, paid: bool):
    resp = requests.patch(
        f"{ORDERS_URL}?id=eq.{order_id}",
        json={"paid": paid},
        headers={**BASE_HEADERS, "Prefer": "return=minimal"}
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


# ── PDF A: PICTURE OVERVIEW ───────────────────────────────────────────────────
def generate_pdf(picture_map):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    title_style, subtitle_style, heading_style, normal_style = _base_styles()
    story = []

    story.append(Paragraph("Fotobestellung – Bildübersicht", title_style))
    story.append(Paragraph(
        f"Erstellt am {datetime.now().strftime('%d.%m.%Y um %H:%M')} Uhr  ·  "
        f"{sum(len(v) for v in picture_map.values())} Bestellungen",
        subtitle_style
    ))
    story.append(HRFlowable(width="100%", thickness=1,
                 color=colors.HexColor("#dddddd"), spaceAfter=16))

    for label, entries in picture_map.items():
        story.append(Paragraph(
            f"{format_label(label)}  –  {len(entries)} Bestellungen", heading_style))

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


# ── PDF B: ABIKASSE REPORT ────────────────────────────────────────────────────
def generate_abikasse_pdf(orders):
    """
    Exports the free images that the Abikasse has to pay for.
    One row per order that has free images, plus a totals section.
    """
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
    story.append(Paragraph("Abikasse – Gratis-Bilder Abrechnung", title_style))
    story.append(Paragraph(
        f"Erstellt am {datetime.now().strftime('%d.%m.%Y um %H:%M')} Uhr  ·  "
        f"Preis pro Bild: {NORMAL_IMAGE_PRICE:.2f}€  ·  Druckkosten: {PRINTING_COST:.2f}€",
        subtitle_style
    ))
    story.append(HRFlowable(width="100%", thickness=1,
                 color=colors.HexColor("#dddddd"), spaceAfter=16))

    # Table header
    col_widths = [5*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm]
    header_row = [
        Paragraph("Name", header_style),
        Paragraph("Bilder\ngesamt", header_style),
        Paragraph(f"Gratis\n(max {AMOUNT_OF_FREE_IMAGES})", header_style),
        Paragraph("Einnahmen\n(Abikasse)", header_style),
        Paragraph("Druck-\nkosten", header_style),
        Paragraph("Abikasse\nzahlt", header_style),
    ]

    rows = [header_row]
    total_free_images = 0
    total_revenue = 0.0
    total_print_cost = 0.0

    for order in orders:
        num_images = order.get("image_count") or 0
        free_images = min(num_images, AMOUNT_OF_FREE_IMAGES)
        if free_images == 0:
            continue
        name = order.get("name", "?")
        rev = free_images * NORMAL_IMAGE_PRICE
        cost = free_images * PRINTING_COST
        # what abikasse actually pays (the price they reimburse)
        net = rev - cost

        total_free_images += free_images
        total_revenue += rev
        total_print_cost += cost

        rows.append([
            Paragraph(name, cell_style),
            Paragraph(str(num_images), cell_style),
            Paragraph(str(free_images), cell_style),
            Paragraph(f"{rev:.2f}€", cell_style),
            Paragraph(f"{cost:.2f}€", cell_style),
            Paragraph(f"{net:.2f}€", cell_style),
        ])

    # Totals row
    rows.append([
        Paragraph("GESAMT", total_style),
        Paragraph("", cell_style),
        Paragraph(str(total_free_images), total_style),
        Paragraph(f"{total_revenue:.2f}€", total_style),
        Paragraph(f"{total_print_cost:.2f}€", total_style),
        Paragraph(f"{total_revenue - total_print_cost:.2f}€", total_style),
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

    story.append(Spacer(1, 20))
    net_total = total_revenue - total_print_cost
    story.append(Paragraph(
        f"Zusammenfassung: {total_free_images} Gratis-Bilder · "
        f"Einnahmen {total_revenue:.2f}€ · Druckkosten {total_print_cost:.2f}€ · "
        f"Abikasse zahlt netto: <b>{net_total:.2f}€</b>",
        ParagraphStyle("Summary", parent=normal_style, fontSize=10,
                       textColor=colors.HexColor("#1a2e1a"))
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()


# ── PDF C: HOODIE REPORT ──────────────────────────────────────────────────────
def generate_hoodie_pdf(merch_orders):
    """
    Exports the hoodie orders: full list + summary by size and color.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    title_style, subtitle_style, heading_style, normal_style = _base_styles()
    header_style = ParagraphStyle("Header", parent=normal_style,
                                  fontSize=9, textColor=colors.white, fontName="Helvetica-Bold")
    cell_style = ParagraphStyle("Cell", parent=normal_style, fontSize=9)

    story = []
    story.append(Paragraph("Hoodie Bestellungen – Übersicht", title_style))
    story.append(Paragraph(
        f"Erstellt am {datetime.now().strftime('%d.%m.%Y um %H:%M')} Uhr  ·  "
        f"{len(merch_orders)} Bestellungen",
        subtitle_style
    ))
    story.append(HRFlowable(width="100%", thickness=1,
                 color=colors.HexColor("#dddddd"), spaceAfter=16))

    # ── Summary: sizes ───────────────────────────────────
    story.append(Paragraph("Größen", heading_style))
    size_counts = defaultdict(int)
    for o in merch_orders:
        size_counts[o.get("size", "?")] += 1

    size_rows = [[Paragraph("Größe", header_style),
                  Paragraph("Anzahl", header_style)]]
    for size in SIZE_OPTIONS:
        count = size_counts.get(size, 0)
        size_rows.append([
            Paragraph(size, cell_style),
            Paragraph(str(count), cell_style),
        ])
    size_rows.append([
        Paragraph("GESAMT", ParagraphStyle(
            "T", parent=cell_style, fontName="Helvetica-Bold")),
        Paragraph(str(len(merch_orders)), ParagraphStyle(
            "T", parent=cell_style, fontName="Helvetica-Bold")),
    ])

    t_size = Table(size_rows, colWidths=[4*cm, 4*cm])
    t_size.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2),
         [colors.HexColor("#f9f9f9"), colors.white]),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#eaf4ee")),
        ("LINEABOVE", (0, -1), (-1, -1), 1, colors.HexColor("#1a7a5a")),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#dddddd")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t_size)
    story.append(Spacer(1, 14))

    # ── Summary: colors ───────────────────────────────────
    story.append(Paragraph("Farben", heading_style))
    color_counts = defaultdict(int)
    for o in merch_orders:
        color_counts[o.get("color", "?")] += 1

    color_rows = [[Paragraph("Farbe", header_style),
                   Paragraph("Anzahl", header_style)]]
    for color in COLOR_OPTIONS:
        count = color_counts.get(color, 0)
        color_rows.append([
            Paragraph(color, cell_style),
            Paragraph(str(count), cell_style),
        ])
    color_rows.append([
        Paragraph("GESAMT", ParagraphStyle(
            "T", parent=cell_style, fontName="Helvetica-Bold")),
        Paragraph(str(len(merch_orders)), ParagraphStyle(
            "T", parent=cell_style, fontName="Helvetica-Bold")),
    ])

    t_color = Table(color_rows, colWidths=[4*cm, 4*cm])
    t_color.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2),
         [colors.HexColor("#f9f9f9"), colors.white]),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#eaf4ee")),
        ("LINEABOVE", (0, -1), (-1, -1), 1, colors.HexColor("#1a7a5a")),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#dddddd")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t_color)
    story.append(Spacer(1, 20))

    # ── Full order list ───────────────────────────────────
    story.append(Paragraph("Alle Bestellungen", heading_style))
    list_rows = [[
        Paragraph("Name", header_style),
        Paragraph("Größe", header_style),
        Paragraph("Farbe", header_style),
        Paragraph("Bestellt am", header_style),
    ]]
    for o in sorted(merch_orders, key=lambda x: x.get("name", "")):
        created = o.get("created_at", "")[:10]
        list_rows.append([
            Paragraph(o.get("name", "?"), cell_style),
            Paragraph(o.get("size", "?"), cell_style),
            Paragraph(o.get("color", "?"), cell_style),
            Paragraph(created, cell_style),
        ])

    t_list = Table(list_rows, colWidths=[5.5*cm, 2.5*cm, 4*cm, 4.5*cm])
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


# ── SUPABASE HELPERS ──────────────────────────────────────────────────────────
def create_zip_all(images_list, order_lookup):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        for img in images_list:
            url = img["url"]
            order_id = img["order_id"]
            pos = img.get("position", 0)
            person_name = order_lookup.get(
                order_id, "unknown").replace(" ", "_")
            response = requests.get(url)
            if response.status_code == 200:
                filename = f"{person_name}_{order_id[:8]}_{pos:02d}.jpg"
                z.writestr(filename, response.content)
    buffer.seek(0)
    return buffer


def upload_image_to_supabase(file, filename: str) -> str | None:
    upload_url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET_NAME}/{filename}"
    upload_headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": file.type,
    }
    response = requests.post(
        upload_url, headers=upload_headers, data=file.getvalue())
    if response.status_code in [200, 201]:
        return f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{filename}"
    else:
        st.error(f"❌ Bild-Upload fehlgeschlagen ({filename}): {response.text}")
        return None


def fetch_images():
    resp = requests.get(
        IMAGES_URL, headers=BASE_HEADERS,
        params={"select": "*", "order": "order_id,position.asc"}
    )
    return resp.json() if resp.status_code == 200 else []


def archive_order(order_id, archived: bool):
    resp = requests.patch(
        f"{ORDERS_URL}?id=eq.{order_id}",
        json={"archived": archived},
        headers={**BASE_HEADERS, "Prefer": "return=minimal"}
    )
    return resp.status_code in [200, 201, 204]


def fetch_orders():
    resp = requests.get(
        ORDERS_URL, headers=BASE_HEADERS,
        params={"select": "*", "order": "created_at.asc", "archived": "eq.false"}
    )
    return resp.json() if resp.status_code == 200 else []


def fetch_archived_orders():
    resp = requests.get(
        ORDERS_URL, headers=BASE_HEADERS,
        params={"select": "*", "order": "created_at.asc", "archived": "eq.true"}
    )
    return resp.json() if resp.status_code == 200 else []


def fetch_merch_orders():
    if not SUPABASE_URL or not SUPABASE_KEY:
        return []
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/abimerch",
        headers=BASE_HEADERS,
        params={"select": "*", "order": "created_at.asc"}
    )
    return resp.json() if resp.status_code == 200 else []
