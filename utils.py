from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from collections import defaultdict
from reportlab.lib.units import cm
from reportlab.lib import colors
from datetime import datetime
import requests
import zipfile
import io


def update_payment(order_id, paid: bool, ORDERS_URL, BASE_HEADERS):
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


def build_picture_map(orders, MOTTO_LABELS, STUFEN_LABELS):
    picture_map = defaultdict(list)
    for o in orders:
        name = o.get("name", "?")
        is_paid = o.get("paid", False) or (o.get("extra_cost") or 0) == 0
        lk = o.get("leistungskurs", "")
        gk = o.get("grundkurs", "")
        for t in (o.get("lk_typ") or []):
            picture_map[f"{lk} - {t}"].append((name, is_paid))
        for t in (o.get("gk_tpy") or []):
            picture_map[f"{gk} - {t}"].append((name, is_paid))
        for m in (o.get("mottowoche") or []):
            picture_map[f"Mottowoche: {MOTTO_LABELS.get(m, f'Motto {m}')}"].append(
                (name, is_paid))
        for s in (o.get("stufenfotos") or []):
            picture_map[f"Stufenfoto: {STUFEN_LABELS.get(s, f'Stufen {s}')}"].append(
                (name, is_paid))
        extra_photos = o.get("extra_photos", 0) or 0
        if extra_photos > 0:
            picture_map["Zusatzfotos"].append(
                (f"{name} (x{extra_photos})", is_paid))
    return picture_map


# ── PDF EXPORT ────────────────────────────────────────────────────────────────
def generate_pdf(picture_map):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title", parent=styles["Title"],
                                 fontSize=18, spaceAfter=6, alignment=TA_LEFT)
    subtitle_style = ParagraphStyle("Sub", parent=styles["Normal"],
                                    fontSize=9, textColor=colors.grey, spaceAfter=16)
    heading_style = ParagraphStyle("Heading", parent=styles["Heading2"],
                                   fontSize=12, spaceBefore=14, spaceAfter=6,
                                   textColor=colors.HexColor("#1a1a2e"))
    normal_style = ParagraphStyle(
        "Normal", parent=styles["Normal"], fontSize=10)

    story = []

    # Title
    story.append(Paragraph("Fotobestellung - Bildübersicht", title_style))
    story.append(Paragraph(
        f"Erstellt am {datetime.now().strftime('%d.%m.%Y um %H:%M')} Uhr  ·  {sum(len(v) for v in picture_map.values())} Bestellungen",
        subtitle_style
    ))
    story.append(HRFlowable(width="100%", thickness=1,
                 color=colors.HexColor("#dddddd"), spaceAfter=16))

    sorted_pics = sorted(picture_map.items(), key=lambda x: -len(x[1]))

    for label, entries in sorted_pics:
        story.append(
            Paragraph(f"{label}  -  {len(entries)} Bestellungen", heading_style))

        paid_names = [n for n, paid in entries if paid]
        unpaid_names = [n for n, paid in entries if not paid]

        table_data = []

        if paid_names:
            table_data.append([
                Paragraph("<b>✓ Bezahlt</b>", ParagraphStyle("", parent=normal_style,
                          textColor=colors.HexColor("#1a7a5a"), fontSize=9)),
                Paragraph(", ".join(paid_names), normal_style)
            ])

        if unpaid_names:
            table_data.append([
                Paragraph("<b>⏳ Ausstehend</b>", ParagraphStyle("", parent=normal_style,
                          textColor=colors.HexColor("#cc3333"), fontSize=9)),
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
