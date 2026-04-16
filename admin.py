import streamlit as st
import requests
import pandas as pd
from collections import defaultdict
from helper.config import (
    NORMAL_IMAGE_PRICE,
    AMOUNT_OF_FREE_IMAGES,
    UPLOAD_PHOTO_PRICE,
    PRINTING_COST
)
from helper.constants import (
    MOTTO_LABELS,
    STUFEN_LABELS,
    NAME_OPTIONS,
    SIZE_OPTIONS,
    COLOR_OPTIONS,
    BADGE_CSS,
    TAG_PAID,
    TAG_UNPAID,
    BASE_HEADERS
)
from helper.utils import (
    calculate_extra_cost,
    format_label,
    update_payment,
    archive_order,
    build_image_map,
    build_picture_map,
    generate_pdf,
    generate_abikasse_pdf,
    generate_hoodie_pdf,
    generate_teilnahme_pdf,
    create_zip_all,
    fetch_orders,
    fetch_images,
    fetch_archived_orders,
    fetch_merch_orders,
)

st.set_page_config(page_title="Bestellungsverwaltung", layout="wide")
st.markdown(BADGE_CSS, unsafe_allow_html=True)


# ── LOAD DATA ─────────────────────────────────────────────────────────────────
if "orders" not in st.session_state:
    st.session_state["orders"] = fetch_orders()
if "images" not in st.session_state:
    st.session_state["images"] = fetch_images()
if "archived_orders" not in st.session_state:
    st.session_state["archived_orders"] = fetch_archived_orders()
if "merch_orders" not in st.session_state:
    st.session_state["merch_orders"] = fetch_merch_orders()

orders = st.session_state["orders"]
images = st.session_state["images"]
archived_orders = st.session_state["archived_orders"]
merch_orders = st.session_state["merch_orders"]

image_map = build_image_map(images)
picture_map = build_picture_map(orders)

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("## Bestellungsverwaltung")

col_title, col_refresh = st.columns([9, 2])
with col_title:
    st.caption(
        f"{len(orders)} Fotobestellungen · {len(merch_orders)} Hoodie-Bestellungen")
with col_refresh:
    if st.button("🔄 Aktualisieren", use_container_width=True):
        st.session_state["orders"] = fetch_orders()
        st.session_state["images"] = fetch_images()
        st.session_state["archived_orders"] = fetch_archived_orders()
        st.session_state["merch_orders"] = fetch_merch_orders()
        st.rerun()

Fotobestellung, Hoodiebestellung, Extra = st.tabs(
    ["Fotobestellung", "Hoodiebestellung", "Extra"])


with Fotobestellung:
    Bilder, Zahlungen, Uploads, Archiv, Abikasse = st.tabs([
        "Bilder", "Zahlungen", "Uploads", "Archiv", "Abikasse"])
    # ═══════════════════════════════════════════════════════════════════
    # TAB 1 - BILDER
    # ═══════════════════════════════════════════════════════════════════
    with Bilder:
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
                        + "".join(tags)
                        + "</div>"
                    )
                    st.markdown(html, unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════
    # TAB 2 - ZAHLUNGEN
    # ═══════════════════════════════════════════════════════════════════
    with Zahlungen:
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
            total_covered_payments += covered_images * NORMAL_IMAGE_PRICE

        c1, c2, c3 = st.columns(3)
        c1.metric("Bezahlt / Gratis", total_paid_orders)
        c2.metric("Ausstehend", total_unpaid_orders)
        c3.metric("Offen gesamt", f"{total_outstanding:.2f}€")

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
            gk_typ = order.get("gk_typ") or []

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
                    [f"{order.get('grundkurs', '')} {t}" for t in gk_typ]
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
                            update_payment(order_id, True)
                            st.session_state["orders"] = fetch_orders()
                            st.session_state["images"] = fetch_images()
                            st.rerun()

                st.markdown("")
                if st.button("🗃️ Archivieren", key=f"archive_{order_id}"):
                    archive_order(order_id, True)
                    st.session_state["orders"] = fetch_orders()
                    st.session_state["archived_orders"] = fetch_archived_orders()
                    st.rerun()

    # ═══════════════════════════════════════════════════════════════════
    # TAB 3 - UPLOADS
    # ═══════════════════════════════════════════════════════════════════
    with Uploads:
        st.markdown("### Alle hochgeladenen Fotos")

        order_lookup = {order["id"]: order.get(
            "name", "?") for order in orders}
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
    # TAB 4 - ARCHIV
    # ═══════════════════════════════════════════════════════════════════
    with Archiv:
        st.markdown("### Archivierte Bestellungen")

        if not archived_orders:
            st.info("Keine archivierten Bestellungen.")
        else:
            st.caption(f"{len(archived_orders)} archivierte Bestellungen")

            for order in archived_orders:
                order_id = order["id"]
                name = order.get("name", "?")
                extra_cost = calculate_extra_cost(order=order)
                is_paid = order.get("paid", False)
                status = (
                    "🟦 GRATIS" if extra_cost == 0 else
                    "✅ BEZAHLT" if is_paid else
                    f"❌ {extra_cost:.2f}€"
                )

                with st.expander(f"{name}: {status}"):
                    lk_typ = order.get("lk_typ") or []
                    gk_typ = order.get("gk_typ") or []
                    kurs_pics = (
                        [f"{order.get('leistungskurs', '')} {t}" for t in lk_typ] +
                        [f"{order.get('grundkurs', '')} {t}" for t in gk_typ]
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

                    extra_photos = order.get("extra_photos") or 0
                    if extra_photos > 0:
                        st.write(f"**Eigene Fotos:** {extra_photos}x")

                    st.markdown("")
                    if st.button("↩️ Wiederherstellen", key=f"unarchive_{order_id}"):
                        archive_order(order_id, False)
                        st.session_state["orders"] = fetch_orders()
                        st.session_state["archived_orders"] = fetch_archived_orders(
                        )
                        st.rerun()
    # ═══════════════════════════════════════════════════════════════════
    # TAB 5 - HOODIES
    # ═══════════════════════════════════════════════════════════════════
    with Abikasse:
        st.markdown("### Abikasse Abrechnung")
        st.caption(f"Gratis-Bilder bis {AMOUNT_OF_FREE_IMAGES} pro Person")

        # Build table data
        abikasse_data = []
        total_free = 0
        total_revenue = 0.0
        total_cost = 0.0

        for order in orders:
            num_images = order.get("image_count") or 0
            free_images = min(num_images, AMOUNT_OF_FREE_IMAGES)
            if free_images == 0:
                continue

            name = order.get("name", "?")
            cost = free_images * NORMAL_IMAGE_PRICE

            abikasse_data.append({
                "Name": name,
                "Bilder (gesamt)": num_images,
                "Gratis": free_images,
                "Abikasse zahlt": f"{cost:.2f}€",
            })
            total_cost += cost
            total_free += free_images

        if abikasse_data:
            df = pd.DataFrame(abikasse_data)
            st.dataframe(df, use_container_width=True, hide_index=True)

            st.divider()
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Gesamt Gratis-Bilder", total_free)
            c3.metric("Abikasse zahlt gesamt", f"{total_cost:.2f}€")
        else:
            st.info("Keine Bestellungen mit Gratis-Bildern vorhanden.")

        st.divider()
        st.download_button(
            label="📥 Als PDF herunterladen",
            data=generate_abikasse_pdf(orders),
            file_name="Abikasse_Abrechnung.pdf",
            mime="application/pdf",
            use_container_width=True,
            key="download_abikasse_tab"
        )


# ═══════════════════════════════════════════════════════════════════
# HOODIES SECTION
# ═══════════════════════════════════════════════════════════════════
with Hoodiebestellung:
    Hoodies, HoodieOrders = st.tabs([
        "Übersicht", "Bestellungen"
    ])

    # ─────────────────────────────────────────────────────────────────
    # TAB 1 - HOODIES ÜBERSICHT
    # ─────────────────────────────────────────────────────────────────
    with Hoodies:
        if not merch_orders:
            st.info("Noch keine Hoodie-Bestellungen vorhanden.")
        else:
            st.download_button(
                label="⬇️ PDF Hoodies",
                data=generate_hoodie_pdf(merch_orders),
                file_name="Hoodie_Bestellungen.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

            # Build organization by color and size
            hoodie_map = defaultdict(lambda: defaultdict(list))
            for o in merch_orders:
                color = o.get("color", "?")
                size = o.get("size", "?")
                name = o.get("name", "?")
                hoodie_map[color][size].append(name)

            for color in COLOR_OPTIONS:
                if not hoodie_map[color]:
                    continue

                color_title = f"{color} - {sum(len(names) for names in hoodie_map[color].values())} Bestellungen"
                with st.expander(color_title):
                    for size in SIZE_OPTIONS:
                        names = hoodie_map[color][size]
                        if names:
                            sizes_str = "  ·  ".join(sorted(names))
                            st.markdown(f"**{size}:** {sizes_str}")

    # ─────────────────────────────────────────────────────────────────
    # TAB 2 - HOODIE BESTELLUNGEN (ORDERS TABLE)
    # ─────────────────────────────────────────────────────────────────
    with HoodieOrders:
        st.markdown("### Hoodie Bestellungen - Übersicht")

        if not merch_orders:
            st.info("Noch keine Hoodie-Bestellungen vorhanden.")
        else:
            st.download_button(
                label="⬇️ PDF Hoodies",
                data=generate_hoodie_pdf(merch_orders),
                file_name="Hoodie_Bestellungen.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="download_hoodie_orders_tab"
            )

            # Farben × Größen Matrix
            st.markdown("#### Übersicht nach Farbe und Größe")

            color_size_matrix = defaultdict(lambda: defaultdict(int))
            for o in merch_orders:
                color = o.get("color", "?")
                size = o.get("size", "?")
                color_size_matrix[color][size] += 1

            # Create table
            matrix_data = []
            for color in COLOR_OPTIONS:
                row = {"Farbe": color}
                for size in SIZE_OPTIONS:
                    count = color_size_matrix[color][size]
                    row[size] = count
                row["Σ"] = sum(color_size_matrix[color].values())
                matrix_data.append(row)

            df_matrix = pd.DataFrame(matrix_data)
            st.dataframe(df_matrix, use_container_width=True, hide_index=True)

            st.divider()

            # Detailed list
            st.markdown("#### Alle Bestellungen")
            hoodie_data = []
            for o in sorted(merch_orders, key=lambda x: x.get("name", "")):
                created = o.get("created_at", "")[:10]
                hoodie_data.append({
                    "Name": o.get("name", "?"),
                    "Größe": o.get("size", "?"),
                    "Farbe": o.get("color", "?"),
                })

            df_list = pd.DataFrame(hoodie_data)
            st.dataframe(df_list, use_container_width=True, hide_index=True)

            st.divider()
            st.download_button(
                label="📥 Als PDF herunterladen",
                data=generate_hoodie_pdf(merch_orders),
                file_name="Hoodie_Bestellungen.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="download_hoodies_tab"
            )


with Extra:
    Teilnahme, Einstellungen, Berechnungen = st.tabs([
        "Teilnahme", "Einstellungen", "Berechnungen"])

    TeilnahmeFoto, TeilnahmeHoodie = st.tabs(["📸 Fotos", "🧥 Hoodies"])

    foto_names_submitted = {o.get("name") for o in orders}
    merch_names_submitted = {o.get("name") for o in merch_orders}
    # ═══════════════════════════════════════════════════════════════════
    # TAB 6 - TEILNAHME
    # ═══════════════════════════════════════════════════════════════════
    with Teilnahme:
        st.download_button(
            label="⬇️ PDF Teilnahme",
            data=generate_teilnahme_pdf(orders, merch_orders),
            file_name="Teilnahme.pdf",
            mime="application/pdf",
            use_container_width=False,
        )
        with TeilnahmeFoto:
            st.markdown("### 📸 Fotobestellung")
            foto_submitted = sorted(
                [n for n in NAME_OPTIONS if n in foto_names_submitted])
            foto_missing = sorted(
                [n for n in NAME_OPTIONS if n not in foto_names_submitted])

            fc1, fc2, fc3 = st.columns(3)
            fc1.metric("Bestellt", len(foto_submitted))
            fc2.metric("Ausstehend", len(foto_missing))
            fc3.metric("Gesamt", len(NAME_OPTIONS))

            col_done, col_missing = st.columns(2)

            with col_done:
                st.markdown(f"**✅ Abgegeben ({len(foto_submitted)})**")
                for name in foto_submitted:
                    st.markdown(
                        f'<span style="{TAG_PAID}">{name}</span>',
                        unsafe_allow_html=True
                    )

            with col_missing:
                st.markdown(f"**⏳ Noch nicht bestellt ({len(foto_missing)})**")
                for name in foto_missing:
                    st.markdown(
                        f'<span style="{TAG_UNPAID}">{name}</span>',
                        unsafe_allow_html=True
                    )

        with TeilnahmeHoodie:
            st.markdown("### 🧥 Hoodie Bestellung")
            merch_submitted = sorted(
                [n for n in NAME_OPTIONS if n in merch_names_submitted])
            merch_missing = sorted(
                [n for n in NAME_OPTIONS if n not in merch_names_submitted])

            mc1, mc2, mc3 = st.columns(3)
            mc1.metric("Bestellt", len(merch_submitted))
            mc2.metric("Ausstehend", len(merch_missing))
            mc3.metric("Gesamt", len(NAME_OPTIONS))

            col_done2, col_missing2 = st.columns(2)

            with col_done2:
                st.markdown(f"**✅ Abgegeben ({len(merch_submitted)})**")
                for name in merch_submitted:
                    st.markdown(
                        f'<span style="{TAG_PAID}">{name}</span>',
                        unsafe_allow_html=True
                    )

            with col_missing2:
                st.markdown(
                    f"**⏳ Noch nicht bestellt ({len(merch_missing)})**")
                for name in merch_missing:
                    st.markdown(
                        f'<span style="{TAG_UNPAID}">{name}</span>',
                        unsafe_allow_html=True
                    )

    # ═══════════════════════════════════════════════════════════════════
    # TAB 8 - EINSTELLUNGEN
    # ═══════════════════════════════════════════════════════════════════
    with Einstellungen:
        st.markdown("### Preise & Einstellungen")

        from helper.config import load_config, CONFIG_URL
        cfg = load_config()

        with st.form("config_form"):
            new_max = st.number_input(
                "Max. Bilder pro Bestellung", value=cfg["MAX_IMAGES"], step=1)
            new_price = st.number_input(
                "Preis pro Bild (€)", value=cfg["NORMAL_IMAGE_PRICE"], step=0.01, format="%.2f")
            new_upload = st.number_input(
                "Preis eigene Fotos (€)", value=cfg["UPLOAD_PHOTO_PRICE"], step=0.01, format="%.2f")
            new_free = st.number_input(
                "Anzahl gratis Bilder", value=cfg["AMOUNT_OF_FREE_IMAGES"], step=1)

            if st.form_submit_button("💾 Speichern"):
                updates = {
                    "MAX_IMAGES": str(new_max),
                    "NORMAL_IMAGE_PRICE": str(new_price),
                    "UPLOAD_PHOTO_PRICE": str(new_upload),
                    "AMOUNT_OF_FREE_IMAGES": str(new_free),
                    "PRINTING_COST": str(cfg["PRINTING_COST"]),
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

    # ═══════════════════════════════════════════════════════════════════
    # TAB 9 - BERECHNUNGEN
    # ═══════════════════════════════════════════════════════════════════
    with Berechnungen:
        total_standard = 0
        total_mottowoche = 0
        total_stufenfotos = 0
        total_uploads = 0
        total_free = 0

        for order in orders:
            lk_typ = order.get("lk_typ") or []
            gk_typ = order.get("gk_typ") or []
            mottos = order.get("mottowoche") or []
            stufen = order.get("stufenfotos") or []
            uploads = order.get("extra_photos") or 0
            num_images = order.get("image_count") or 0

            total_standard += len(lk_typ) + len(gk_typ)
            total_mottowoche += len(mottos)
            total_stufenfotos += len(stufen)
            total_uploads += uploads
            total_free += min(num_images, AMOUNT_OF_FREE_IMAGES)

        total_extra_images = total_standard + total_mottowoche + total_stufenfotos

        rev_free = total_free * NORMAL_IMAGE_PRICE
        rev_extra = sum(
            max((o.get("image_count") or 0) -
                AMOUNT_OF_FREE_IMAGES, 0) * NORMAL_IMAGE_PRICE
            for o in orders
        )
        rev_uploads = total_uploads * UPLOAD_PHOTO_PRICE
        total_revenue = rev_free + rev_extra + rev_uploads

        total_all_images = total_extra_images + total_uploads
        total_PRINTING_COST = total_all_images * PRINTING_COST
        total_profit = total_revenue - total_PRINTING_COST

        st.markdown("#### Gewinnvorhersage")
        fc1, fc2 = st.columns(2)
        with fc1:
            forecast_normal = st.number_input(
                "Anzahl Normalbilder (Vorhersage)", min_value=0, value=total_extra_images, step=1)
        with fc2:
            forecast_uploads = st.number_input(
                "Anzahl Uploads (Vorhersage)", min_value=0, value=total_uploads, step=1)

        forecast_revenue = (forecast_normal * NORMAL_IMAGE_PRICE) + \
            (forecast_uploads * UPLOAD_PHOTO_PRICE)
        forecast_cost = (forecast_normal + forecast_uploads) * PRINTING_COST
        forecast_profit = forecast_revenue - forecast_cost

        f1, f2, f3 = st.columns(3)
        f1.metric("Erwartete Einnahmen", f"{forecast_revenue:.2f}€")
        f2.metric("Erwartete Druckkosten", f"{forecast_cost:.2f}€")
        f3.metric("Erwarteter Gewinn", f"{forecast_profit:.2f}€")

        st.divider()

        st.markdown("#### Gratis-Bilder (Abikasse zahlt)")
        h1, h2, h3, h4, h5 = st.columns([3, 1, 1, 1, 1])
        h1.markdown("**Typ**")
        h2.markdown("**Anzahl**")
        h3.markdown("**Verkaufspreis**")
        h4.markdown("**Druckkosten**")
        h5.markdown("**Gewinn**")

        rev = total_free * NORMAL_IMAGE_PRICE
        cost = total_free * PRINTING_COST
        c1, c2, c3, c4, c5 = st.columns([3, 1, 1, 1, 1])
        c1.write(f"Normalbild ({AMOUNT_OF_FREE_IMAGES} gratis)")
        c2.write(str(total_free))
        c3.write(f"{rev:.2f}€")
        c4.write(f"{cost:.2f}€")
        c5.write(f"**{rev - cost:.2f}€**")

        st.divider()

        st.markdown("#### Extra-Bilder (Student zahlt)")
        h1, h2, h3, h4, h5 = st.columns([3, 1, 1, 1, 1])
        h1.markdown("**Typ**")
        h2.markdown("**Anzahl**")
        h3.markdown("**Verkaufspreis**")
        h4.markdown("**Druckkosten**")
        h5.markdown("**Gewinn**")

        rows = [
            ("LK / GK Fotos",  total_standard,    NORMAL_IMAGE_PRICE),
            ("Mottowoche",      total_mottowoche,  NORMAL_IMAGE_PRICE),
            ("Stufenfotos",     total_stufenfotos, NORMAL_IMAGE_PRICE),
            ("Eigene Uploads",  total_uploads,     UPLOAD_PHOTO_PRICE),
        ]

        for label, count, price in rows:
            rev = count * price
            cost = count * PRINTING_COST
            c1, c2, c3, c4, c5 = st.columns([3, 1, 1, 1, 1])
            c1.write(label)
            c2.write(str(count))
            c3.write(f"{rev:.2f}€")
            c4.write(f"{cost:.2f}€")
            c5.write(f"**{rev - cost:.2f}€**")

        s0, s1, s2, s3, s4 = st.columns([3, 1, 1, 1, 1])
        s1.metric("Anzahl Bilder", str(total_all_images))
        s2.metric("Gesamteinnahmen", f"{total_revenue:.2f}€")
        s3.metric("Druckkosten gesamt", f"{total_PRINTING_COST:.2f}€")
        s4.metric("Gewinn", f"{total_profit:.2f}€")

        st.divider()
        st.markdown("#### Preisstruktur pro Bild")

        margin_normal = NORMAL_IMAGE_PRICE - PRINTING_COST
        margin_upload = UPLOAD_PHOTO_PRICE - PRINTING_COST
        margin_pct_normal = (margin_normal / NORMAL_IMAGE_PRICE *
                             100) if NORMAL_IMAGE_PRICE else 0
        margin_pct_upload = (margin_upload / UPLOAD_PHOTO_PRICE *
                             100) if UPLOAD_PHOTO_PRICE else 0

        pu1, pu2 = st.columns(2)
        with pu1:
            st.markdown("**Normalbild / Mottowoche / Stufenfoto**")
            p1, p2, p3 = st.columns(3)
            p1.metric("Verkaufspreis", f"{NORMAL_IMAGE_PRICE:.2f}€")
            p2.metric("Druckkosten",   f"{PRINTING_COST:.2f}€")
            p3.metric("Marge", f"{margin_normal:.2f}€",
                      delta=f"{margin_pct_normal:.0f}%", delta_color="normal")
        with pu2:
            st.markdown("**Eigener Upload**")
            p1, p2, p3 = st.columns(3)
            p1.metric("Verkaufspreis", f"{UPLOAD_PHOTO_PRICE:.2f}€")
            p2.metric("Druckkosten",   f"{PRINTING_COST:.2f}€")
            p3.metric("Marge", f"{margin_upload:.2f}€",
                      delta=f"{margin_pct_upload:.0f}%", delta_color="normal")
