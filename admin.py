import streamlit as st
import requests
from config import (
    MAX_IMAGES,
    NORMAL_IMAGE_PRICE,
    NORMAL_IMAGE_PRICE_THAT_ABIKASSE_PAYS,
    STUFENFOTO_PRICE,
    EXTRA_PHOTO_PRICE
)
from constants import (
    MOTTO_LABELS,
    STUFEN_LABELS,
    BADGE_CSS,
    TAG_PAID,
    TAG_UNPAID,
    ORDERS_URL,
    IMAGES_URL,
    BASE_HEADERS,
)
from utils import (
    update_payment,
    build_image_map,
    build_picture_map,
    generate_pdf,
    create_zip_all,
)


st.set_page_config(page_title="Bestellungsverwaltung", layout="wide")
st.markdown(BADGE_CSS, unsafe_allow_html=True)


# ── DATA FETCH ────────────────────────────────────────────────────────────────
@st.cache_data(ttl=30)
def fetch_orders():
    resp = requests.get(
        ORDERS_URL,
        headers={**BASE_HEADERS, "Prefer": "return=representation"},
        params={"select": "*", "order": "created_at.asc"}
    )
    return resp.json() if resp.status_code == 200 else []


@st.cache_data(ttl=30)
def fetch_images():
    resp = requests.get(
        IMAGES_URL,
        headers={**BASE_HEADERS, "Prefer": "return=representation"},
        params={"select": "*", "order": "order_id,position.asc"}
    )
    return resp.json() if resp.status_code == 200 else []


# ── LOAD DATA ─────────────────────────────────────────────────────────────────
orders = fetch_orders()
images = fetch_images()
image_map = build_image_map(images)

# Auto-patch free orders
for o in orders:
    if (o.get("extra_cost") or 0) == 0 and not o.get("paid", False):
        update_payment(o["id"], True, ORDERS_URL, BASE_HEADERS)

picture_map = build_picture_map(orders, MOTTO_LABELS, STUFEN_LABELS)


# ═══════════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════════
st.markdown("## Bestellungsverwaltung")

col_title, col_refresh, col_pdf,  = st.columns([7, 2, 2])
with col_title:
    st.caption(f"{len(orders)} Bestellungen gesamt")
with col_refresh:
    st.button("🔄 Daten aktualisieren", on_click=lambda: st.cache_data.clear())
with col_pdf:
    st.download_button(
        label="⬇️ PDF Exportieren",
        data=generate_pdf(picture_map),
        file_name=f"Bestellungsübersicht.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

tab1, tab2, tab3 = st.tabs(["📸 Bildübersicht", "💶 Zahlungen", "🖼️ Uploads"])

# ═══════════════════════════════════════════════════════════════════
# TAB 1 - PICTURE OVERVIEW
# ═══════════════════════════════════════════════════════════════════
with tab1:
    if not picture_map:
        st.info("Noch keine Bestellungen vorhanden.")
    else:
        for label, entries in sorted(picture_map.items(), key=lambda x: -len(x[1])):
            paid_names = [n for n, paid in entries if paid]
            unpaid_names = [n for n, paid in entries if not paid]

            with st.expander(f"{label} - {len(entries)} Bestellungen"):
                html = '<div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:4px;align-items:center;">'
                for n, paid in entries:
                    html += f'<span style="{TAG_PAID if paid else TAG_UNPAID}">{n}</span>'
                html += '</div>'
                st.markdown(html, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# TAB 2 - PAYMENTS
# ═══════════════════════════════════════════════════════════════════
with tab2:
    total_outstanding = sum(
        (o.get("extra_cost") or 0) for o in orders
        if not o.get("paid", False) and (o.get("extra_cost") or 0) > 0
    )
    num_paid = sum(1 for o in orders if o.get("paid", False)
                   or (o.get("extra_cost") or 0) == 0)
    covered_payments = 0
    NORMAL_IMAGE_PRICE_THAT_ABIKASSE_PAY = 0.15
    for o in orders:
        num_images = o.get("image_count", 0)
        covered_payments += min(3, num_images) * \
            NORMAL_IMAGE_PRICE_THAT_ABIKASSE_PAY

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Bezahlt / Gratis", num_paid)
    c2.metric("Ausstehend", len(orders) - num_paid)
    c3.metric("Offen gesamt", f"{total_outstanding:.2f}€")
    c4.metric("Wird von Kasse gezahlt", f"{covered_payments:.2f}€")

    st.divider()

    filter_col, search_col = st.columns([3, 5])
    with filter_col:
        show_filter = st.selectbox(
            "Anzeigen", ["Alle", "Nur Ausstehende", "Nur Bezahlte"])
    with search_col:
        search_query = st.text_input(
            "🔍 Name suchen", placeholder="Max Mustermann")

    filtered_orders = []
    for o in orders:
        extra = o.get("extra_cost") or 0
        is_free = extra == 0
        is_paid = o.get("paid", False) or is_free

        if show_filter == "Nur Ausstehende" and is_paid:
            continue
        if show_filter == "Nur Bezahlte" and not is_paid:
            continue
        if search_query and search_query.lower() not in o.get("name", "").lower():
            continue

        filtered_orders.append(o)

    if search_query and not filtered_orders:
        st.warning(f"Keine Bestellung für '{search_query}' gefunden.")

    for o in filtered_orders:
        extra = o.get("extra_cost") or 0
        is_free = extra == 0
        is_paid = o.get("paid", False) or is_free
        order_id = o["id"]
        name = o.get("name", "?")

        lk_typ = o.get("lk_typ") or []
        gk_tpy = o.get("gk_tpy") or []
        extra_photos = o.get("extra_photos", 0) or 0

        badge = (
            '<span class="free-badge">GRATIS</span>' if is_free else
            '<span class="paid-badge">BEZAHLT</span>' if is_paid else
            f'<span class="unpaid-badge">{extra:.2f}€</span>'
        )
        status_label = "🟦 GRATIS" if is_free else "✅ BEZAHLT" if is_paid else f"❌ {extra:.2f}€"
        created = o.get("created_at", "")[:16].replace("T", " ")

        with st.expander(f"{name}: {status_label}"):
            st.markdown(badge, unsafe_allow_html=True)

            kurs_pics = (
                [f"{o.get('leistungskurs', '')} {t}" for t in lk_typ] +
                [f"{o.get('grundkurs', '')} {t}" for t in gk_tpy]
            )
            if kurs_pics:
                st.write("**Kursfotos:** " + "  ·  ".join(kurs_pics))

            mottos = [MOTTO_LABELS.get(m, f"Motto {m}") for m in (
                o.get("mottowoche") or [])]
            if mottos:
                st.write("**Mottowoche:** " + "  ·  ".join(mottos))

            stufen = [STUFEN_LABELS.get(s, f"Stufen {s}") for s in (
                o.get("stufenfotos") or [])]
            if stufen:
                st.write("**Stufenfotos:** " + "  ·  ".join(stufen))

            if extra_photos > 0:
                st.write(f"**Eigene Fotos:** {extra_photos}x")

            order_imgs = image_map.get(order_id, [])
            if order_imgs:
                with st.expander(f"Hochgeladene Fotos ({len(order_imgs)})"):
                    img_cols = st.columns(min(len(order_imgs), 4))
                    for i, url in enumerate(order_imgs):
                        img_cols[i % 4].image(url)

            st.write("")
            if not is_free:
                if is_paid:
                    if st.button("Als unbezahlt markieren", key=f"unpay_{order_id}"):
                        update_payment(order_id, False,
                                       ORDERS_URL, BASE_HEADERS)
                        st.cache_data.clear()
                        st.rerun()
                else:
                    if st.button(f"✅ Als bezahlt markieren ({extra:.2f}€)", key=f"pay_{order_id}"):
                        update_payment(
                            order_id, True, ORDERS_URL, BASE_HEADERS)
                        st.cache_data.clear()
                        st.rerun()


# ═══════════════════════════════════════════════════════════════════
# TAB 3 - UPLOADS
# ═══════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("### Alle hochgeladenen Fotos")

    order_lookup = {o["id"]: o.get("name", "?") for o in orders}
    all_uploads = [
        (img["url"], order_lookup.get(img["order_id"], "?"),
         img.get("position", 0), img["order_id"])
        for img in images
    ]

    if not all_uploads:
        st.info("Noch keine Fotos hochgeladen.")
    else:
        st.caption(f"{len(all_uploads)} Fotos insgesamt")
        if st.button("📦 ZIP vorbereiten"):
            with st.spinner("Bilder werden heruntergeladen..."):
                st.session_state["zip_buffer"] = create_zip_all(
                    images, order_lookup)

        if "zip_buffer" in st.session_state:
            st.download_button(
                label="📥 Alle Bilder herunterladen (ZIP)",
                data=st.session_state["zip_buffer"],
                file_name="Bilder.zip",
                mime="application/zip",
            )

        st.divider()

        # ── GRID ──────────────────────────────────────────────────
        cols = st.columns(4)
        for i, (url, name, pos, _) in enumerate(all_uploads):
            with cols[i % 4]:
                st.image(url)
                st.caption(f"{name} · #{pos}")
