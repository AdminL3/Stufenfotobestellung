import streamlit as st
import requests
from config import (
    NORMAL_IMAGE_PRICE_THAT_ABIKASSE_PAYS,
    AMOUNT_OF_FREE_IMAGES
)
from constants import (
    MOTTO_LABELS,
    STUFEN_LABELS,
    BADGE_CSS,
    TAG_PAID,
    TAG_UNPAID,
    BASE_HEADERS
)
from utils import (
    calculate_extra_cost,
    format_label,
    update_payment,
    build_image_map,
    build_picture_map,
    generate_pdf,
    create_zip_all,
    fetch_orders,
    fetch_images
)

st.set_page_config(page_title="Bestellungsverwaltung", layout="wide")
st.markdown(BADGE_CSS, unsafe_allow_html=True)


# ── LOAD DATA ─────────────────────────────────────────────────────────────────
if "orders" not in st.session_state or "images" not in st.session_state:
    st.session_state["orders"] = []
    st.session_state["images"] = []

orders = st.session_state["orders"]
images = st.session_state["images"]

# Add these:
image_map = build_image_map(images)
picture_map = build_picture_map(orders)

# ═══════════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════════
st.markdown("## Bestellungsverwaltung")

col_title, col_refresh, col_pdf = st.columns([7, 2, 2])
with col_title:
    st.caption(f"{len(orders)} Bestellungen gesamt")
with col_refresh:
    if st.button("🔄 Daten aktualisieren"):
        st.session_state["orders"] = fetch_orders()
        st.session_state["images"] = fetch_images()
        st.rerun()
with col_pdf:
    st.download_button(
        label="⬇️ PDF Exportieren",
        data=generate_pdf(picture_map),
        file_name="Bestellungsübersicht.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

tab1, tab2, tab3, tab4 = st.tabs(
    ["📸 Bildübersicht", "💶 Zahlungen", "🖼️ Uploads", "⚙️ Einstellungen"])


# ═══════════════════════════════════════════════════════════════════
# TAB 1 - PICTURE OVERVIEW
# ═══════════════════════════════════════════════════════════════════
with tab1:
    if not picture_map:
        st.info("Noch keine Bestellungen vorhanden.")
    else:
        for key, entries in picture_map.items():
            title = f"{format_label(key)} - {len(entries)} Bestellungen"
            with st.expander(title):
                tags = [
                    f'<span style="{TAG_PAID if paid else TAG_UNPAID}">{name}</span>'
                    for name, paid in entries
                ]
                html = (
                    '<div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:4px;">'
                    + "".join(tags) +
                    "</div>"
                )
                st.markdown(html, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# TAB 2 - PAYMENTS
# ═══════════════════════════════════════════════════════════════════
with tab2:
    total_outstanding = 0.0
    total_paid_orders = 0
    total_unpaid_orders = 0
    total_covered_payments = 0.0

    for order in orders:
        extra_cost = calculate_extra_cost(order=order)
        is_paid = order.get("paid", False)

        if is_paid:
            total_paid_orders += 1
        else:
            total_outstanding += extra_cost
            total_unpaid_orders += 1

        num_images = order.get("image_count") or 0
        covered_images = min(num_images, AMOUNT_OF_FREE_IMAGES)
        total_covered_payments += covered_images * NORMAL_IMAGE_PRICE_THAT_ABIKASSE_PAYS

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Bezahlt / Gratis", total_paid_orders)
    c2.metric("Ausstehend", total_unpaid_orders)
    c3.metric("Offen gesamt", f"{total_outstanding:.2f}€")
    c4.metric("Wird von Kasse gezahlt", f"{total_covered_payments:.2f}€")

    st.divider()

    filter_col, search_col = st.columns([3, 5])
    with filter_col:
        show_filter = st.selectbox(
            "Anzeigen", ["Alle", "Nur Ausstehende", "Nur Bezahlte"])
    with search_col:
        search_query = st.text_input(
            "🔍 Name suchen", placeholder="Max Mustermann")

    filtered_orders = []
    for order in orders:
        is_paid = order.get("paid", False)
        if show_filter == "Nur Ausstehende" and is_paid:
            continue
        if show_filter == "Nur Bezahlte" and not is_paid:
            continue
        if search_query and search_query.lower() not in order.get("name", "").lower():
            continue
        filtered_orders.append(order)

    if search_query and not filtered_orders:
        st.warning(f"Keine Bestellung für '{search_query}' gefunden.")

    for order in filtered_orders:
        extra_cost = calculate_extra_cost(order=order)
        is_free = extra_cost == 0
        is_paid = order.get("paid", False)
        order_id = order["id"]
        name = order.get("name", "?")

        lk_typ = order.get("lk_typ") or []
        gk_tpy = order.get("gk_tpy") or []

        badge = (
            '<span class="free-badge">GRATIS</span>' if is_free else
            f'<span class="paid-badge">{extra_cost:.2f}€</span>' if is_paid else
            f'<span class="unpaid-badge">{extra_cost:.2f}€</span>'
        )
        status_label = "🟦 GRATIS" if is_free else "✅ BEZAHLT" if is_paid else f"❌ {extra_cost:.2f}€"

        with st.expander(f"{name}: {status_label}"):
            st.markdown(badge, unsafe_allow_html=True)

            kurs_pics = (
                [f"{order.get('leistungskurs', '')} {t}" for t in lk_typ] +
                [f"{order.get('grundkurs', '')} {t}" for t in gk_tpy]
            )
            if kurs_pics:
                st.write("**Kursfotos:** " + "  ·  ".join(kurs_pics))

            mottos = [MOTTO_LABELS.get(m, f"Motto {m}") for m in (
                order.get("mottowoche") or [])]
            if mottos:
                st.write("**Mottowoche:** " + "  ·  ".join(mottos))

            stufen = [STUFEN_LABELS.get(s, f"Stufen {s}") for s in (
                order.get("stufenfotos") or [])]
            if stufen:
                st.write("**Stufenfotos:** " + "  ·  ".join(stufen))

            amount_uploaded_fotos = order.get("extra_photos") or 0
            if amount_uploaded_fotos > 0:
                st.write(f"**Eigene Fotos:** {amount_uploaded_fotos}x")

            order_imgs = image_map.get(order_id, [])
            if order_imgs:
                with st.expander(f"Hochgeladene Fotos ({len(order_imgs)})"):
                    img_cols = st.columns(min(len(order_imgs), 4))
                    for i, url in enumerate(order_imgs):
                        img_cols[i % 4].image(url)

            if not is_free:
                if is_paid:
                    if st.button("Als unbezahlt markieren", key=f"unpay_{order_id}"):
                        update_payment(order_id, False)
                        st.session_state["orders"] = fetch_orders()
                        st.session_state["images"] = fetch_images()
                        st.rerun()
                else:
                    if st.button(f"✅ Als bezahlt markieren ({extra_cost:.2f}€)", key=f"pay_{order_id}"):
                        update_payment(
                            order_id, True)
                        st.session_state["orders"] = fetch_orders()
                        st.session_state["images"] = fetch_images()
                        st.rerun()


# ═══════════════════════════════════════════════════════════════════
# TAB 3 - UPLOADS
# ═══════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("### Alle hochgeladenen Fotos")

    order_lookup = {order["id"]: order.get("name", "?") for order in orders}
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

        cols = st.columns(4)
        for i, (url, name, pos, _) in enumerate(all_uploads):
            with cols[i % 4]:
                st.image(url)
                st.caption(f"{name} · #{pos}")

# ═══════════════════════════════════════════════════════════════════
# TAB 4 - SETTINGS
# ═══════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("### Preise & Einstellungen")

    from config import load_config, CONFIG_URL
    cfg = load_config()

    with st.form("config_form"):
        new_max = st.number_input(
            "Max. Bilder pro Bestellung", value=cfg["MAX_IMAGES"], step=1)
        new_price = st.number_input(
            "Preis pro Bild (€)", value=cfg["NORMAL_IMAGE_PRICE"], step=0.01, format="%.2f")
        # new_kasse = st.number_input("Preis den die Abikasse zahlt (€)",
        #                             value=cfg["NORMAL_IMAGE_PRICE_THAT_ABIKASSE_PAYS"], step=0.01, format="%.2f")
        new_upload = st.number_input(
            "Preis eigene Fotos (€)", value=cfg["UPLOAD_PHOTO_PRICE"], step=0.01, format="%.2f")
        new_free = st.number_input(
            "Anzahl gratis Bilder", value=cfg["AMOUNT_OF_FREE_IMAGES"], step=1)

        if st.form_submit_button("💾 Speichern"):
            updates = {
                "MAX_IMAGES": str(new_max),
                "NORMAL_IMAGE_PRICE": str(new_price),
                # No update for this one
                "NORMAL_IMAGE_PRICE_THAT_ABIKASSE_PAYS": cfg["NORMAL_IMAGE_PRICE_THAT_ABIKASSE_PAYS"],
                "UPLOAD_PHOTO_PRICE": str(new_upload),
                "AMOUNT_OF_FREE_IMAGES": str(new_free),
            }
            success = True
            for key, value in updates.items():
                resp = requests.patch(
                    f"{CONFIG_URL}?key=eq.{key}",
                    json={"value": value},
                    headers={**BASE_HEADERS, "Prefer": "return=minimal"}
                )
                if resp.status_code not in [200, 201, 204]:
                    st.error(f"❌ Fehler beim Speichern von {key}")
                    success = False
            if success:
                st.cache_data.clear()
                st.success("✅ Einstellungen gespeichert!")
