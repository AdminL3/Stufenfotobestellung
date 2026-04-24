from __future__ import annotations

from collections import defaultdict
from typing import Any

import pandas as pd
import requests
import streamlit as st

from helper.config import (
    AMOUNT_OF_FREE_IMAGES,
    NORMAL_IMAGE_PRICE,
    PRINTING_COST,
    UPLOAD_PHOTO_PRICE,
)
from helper.constants import (
    BADGE_CSS,
    COLOR_OPTIONS,
    MOTTO_LABELS,
    NAME_OPTIONS,
    SIZE_OPTIONS,
    STUFEN_LABELS,
    TAG_PAID,
    TAG_UNPAID,
    TEILNAHME_PRESET,
)
from helper.utils import (
    archive_order,
    build_image_map,
    build_picture_map,
    calculate_extra_cost,
    fetch_archived_orders,
    fetch_images,
    fetch_merch_orders,
    fetch_orders,
    format_label,
    generate_abikasse_pdf,
    generate_hoodie_pdf,
    generate_teilnahme_pdf,
    generate_teilnahme_pdf_foto,
    generate_teilnahme_pdf_hoodie,
    generate_teilnahme_pdf_all,
    update_payment,
    get_headers
)

st.set_page_config(page_title="Bestellungsverwaltung", layout="wide")
st.markdown(BADGE_CSS, unsafe_allow_html=True)


# region Session State
def _load_all() -> None:
    st.session_state["orders"] = fetch_orders()
    st.session_state["images"] = fetch_images()
    st.session_state["archived_orders"] = fetch_archived_orders()
    st.session_state["merch_orders"] = fetch_merch_orders()


for _key, _fetcher in [
    ("orders", fetch_orders),
    ("images", fetch_images),
    ("archived_orders", fetch_archived_orders),
    ("merch_orders", fetch_merch_orders),
]:
    if _key not in st.session_state:
        st.session_state[_key] = _fetcher()

orders: list[dict] = st.session_state["orders"]
images: list[dict] = st.session_state["images"]
archived_orders: list[dict] = st.session_state["archived_orders"]
merch_orders: list[dict] = st.session_state["merch_orders"]

image_map = build_image_map(images)
picture_map = build_picture_map(orders)


# region Header
st.markdown("## Bestellungsverwaltung")

col_title, col_refresh = st.columns([9, 2])
with col_title:
    st.caption(
        f"{len(orders)} Fotobestellungen · {len(merch_orders)} Hoodie-Bestellungen")
with col_refresh:
    if st.button("🔄 Aktualisieren", use_container_width=True):
        _load_all()
        st.rerun()

tab_foto, tab_hoodie, tab_extra = st.tabs(
    ["Fotobestellung", "Hoodiebestellung", "Extra"]
)

# region Fotobestellung
with tab_foto:
    sub_bilder, sub_zahlungen, sub_archiv, sub_abikasse = st.tabs(
        ["Bilder", "Zahlungen", "Archiv", "Abikasse"]
    )

    with sub_bilder:
        if not picture_map:
            st.info("Noch keine Bestellungen vorhanden.")
        else:
            for key, entries in picture_map.items():
                with st.expander(f"{format_label(key)} - {len(entries)} Bestellungen"):
                    tags = [
                        f'<span style="{TAG_PAID if paid else TAG_UNPAID}">{name}</span>'
                        for name, paid in entries
                    ]
                    st.markdown(
                        '<div style="display:flex;flex-wrap:wrap;gap:6px;margin-top:4px;">'
                        + "".join(tags)
                        + "</div>",
                        unsafe_allow_html=True,
                    )

    # region Bezahlungen
    with sub_zahlungen:
        total_outstanding = 0.0
        total_paid = 0
        total_unpaid = 0

        for order in orders:
            extra_cost = calculate_extra_cost(order=order)
            if order.get("paid", False):
                total_paid += 1
            else:
                total_outstanding += extra_cost
                total_unpaid += 1

        c1, c2, c3 = st.columns(3)
        c1.metric("Bezahlt / Gratis", total_paid)
        c2.metric("Ausstehend", total_unpaid)
        c3.metric("Offen gesamt", f"{total_outstanding:.2f}€")

        st.divider()

        filter_col, search_col = st.columns([3, 5])
        with filter_col:
            show_filter = st.selectbox(
                "Anzeigen", ["Alle", "Nur Ausstehende", "Nur Bezahlte"])
        with search_col:
            search_query = st.text_input(
                "🔍 Name suchen", placeholder="Max Mustermann")

        filtered_orders = [
            o for o in orders
            if not (show_filter == "Nur Ausstehende" and o.get("paid", False))
            and not (show_filter == "Nur Bezahlte" and not o.get("paid", False))
            and (not search_query or search_query.lower() in o.get("name", "").lower())
        ]

        if search_query and not filtered_orders:
            st.warning(f"Keine Bestellung für '{search_query}' gefunden.")

        for order in filtered_orders:
            extra_cost = calculate_extra_cost(order=order)
            is_free = extra_cost == 0
            is_paid = order.get("paid", False)
            order_id = order["id"]
            name = order.get("name", "?")

            if is_free:
                status_label = "🟦 GRATIS"
                badge = '<span class="free-badge">GRATIS</span>'
            elif is_paid:
                status_label = "✅ BEZAHLT"
                badge = f'<span class="paid-badge">{extra_cost:.2f}€</span>'
            else:
                status_label = f"❌ {extra_cost:.2f}€"
                badge = f'<span class="unpaid-badge">{extra_cost:.2f}€</span>'

            with st.expander(f"{name}: {status_label}"):
                st.markdown(badge, unsafe_allow_html=True)

                lk_typ = order.get("lk_typ") or []
                gk_typ = order.get("gk_typ") or []
                kurs_pics = (
                    [f"{order.get('leistungskurs', '')} {t}" for t in lk_typ]
                    + [f"{order.get('grundkurs', '')} {t}" for t in gk_typ]
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

    # region Archiv
    with sub_archiv:
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

                if extra_cost == 0:
                    status = "🟦 GRATIS"
                elif is_paid:
                    status = "✅ BEZAHLT"
                else:
                    status = f"❌ {extra_cost:.2f}€"

                with st.expander(f"{name}: {status}"):
                    lk_typ = order.get("lk_typ") or []
                    gk_typ = order.get("gk_typ") or []
                    kurs_pics = (
                        [f"{order.get('leistungskurs', '')} {t}" for t in lk_typ]
                        + [f"{order.get('grundkurs', '')} {t}" for t in gk_typ]
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

                    st.markdown("")
                    if st.button("↩️ Wiederherstellen", key=f"unarchive_{order_id}"):
                        archive_order(order_id, False)
                        st.session_state["orders"] = fetch_orders()
                        st.session_state["archived_orders"] = fetch_archived_orders(
                        )
                        st.rerun()

    # region Abikasse
    with sub_abikasse:
        st.markdown("### Abikasse Abrechnung")
        st.caption(f"Gratis-Bilder bis {AMOUNT_OF_FREE_IMAGES} pro Person")

        abikasse_data = []
        total_free_count = 0
        total_abikasse_cost = 0.0

        for order in orders:
            num_images = order.get("image_count") or 0
            free_images = min(num_images, AMOUNT_OF_FREE_IMAGES)
            if free_images == 0:
                continue
            cost = free_images * NORMAL_IMAGE_PRICE
            abikasse_data.append({
                "Name": order.get("name", "?"),
                "Bilder (gesamt)": num_images,
                "Gratis": free_images,
                "Abikasse zahlt": f"{cost:.2f}€",
            })
            total_free_count += free_images
            total_abikasse_cost += cost
            if abikasse_data:
                st.dataframe(pd.DataFrame(abikasse_data),
                             use_container_width=True, hide_index=True)
                abikasse_c1, abikasse_c2 = st.columns([2, 2])
                abikasse_c1.metric("Gesamt Gratis-Bilder", total_free_count)
                abikasse_c2.metric("Abikasse zahlt gesamt",
                                   f"{total_abikasse_cost:.2f}€")
            else:
                st.info("Keine Bestellungen mit Gratis-Bildern vorhanden.")

        st.download_button(
            label="📥 Als PDF herunterladen",
            data=generate_abikasse_pdf(orders),
            file_name="Abikasse_Abrechnung.pdf",
            mime="application/pdf",
            use_container_width=True,
            key="download_abikasse_tab",
        )


# region Hoodiebestellung

with tab_hoodie:
    st.download_button(
        label="⬇️ PDF Hoodies",
        data=generate_hoodie_pdf(merch_orders),
        file_name="Hoodie_Bestellungen.pdf",
        mime="application/pdf",
    )
    hoodie_all, hoodie_overview, hoodie_unterschriften = st.tabs(
        ["Einzeln", "Gesamt", "Unterschriften"])

    with hoodie_all:
        if not merch_orders:
            st.info("Noch keine Hoodie-Bestellungen vorhanden.")
        else:
            st.markdown("#### Alle Bestellungen")
            hoodie_rows = [
                {"Name": o.get("name", "?"), "Größe": o.get(
                    "size", "?"), "Farbe": o.get("color", "?")}
                for o in sorted(merch_orders, key=lambda x: x.get("name", ""))
            ]
            st.dataframe(pd.DataFrame(hoodie_rows),
                         use_container_width=True, hide_index=True)

# Hoodie-Bestellungen — Detailübersicht
    with hoodie_overview:
        st.markdown("### Hoodie Bestellungen - Übersicht")

        if not merch_orders:
            st.info("Noch keine Hoodie-Bestellungen vorhanden.")
        else:
            color_size_matrix: dict[str, dict[str, int]
                                    ] = defaultdict(lambda: defaultdict(int))
            for o in merch_orders:
                color_size_matrix[o.get("color", "?")][o.get("size", "?")] += 1

            matrix_data: list[dict[str, Any]] = []
            for color in COLOR_OPTIONS:
                row: dict[str, Any] = {"Farbe": color}
                for size in SIZE_OPTIONS:
                    row[size] = color_size_matrix[color][size]
                row["Summe"] = sum(color_size_matrix[color].values())
                matrix_data.append(row)

            st.dataframe(pd.DataFrame(matrix_data),
                         use_container_width=True, hide_index=True)

    with hoodie_unterschriften:
        st.markdown("### Hochgeladene Unterschriften")

        orders_with_design = [
            o for o in merch_orders if o.get("design_image")
        ]
        if not orders_with_design:
            st.info("Noch keine Designs hochgeladen.")
        else:
            cols = st.columns(3)
            for i, order in enumerate(sorted(orders_with_design, key=lambda x: x.get("name", ""))):
                with cols[i % 3]:
                    st.image(order["design_image"], use_container_width=True)
                    st.caption(
                        f"{order.get('name', '?')} · {order.get('size', '?')} · {order.get('color', '?')}")


# region Extra
with tab_extra:
    sub_teilnahme, sub_einstellungen, sub_berechnungen = st.tabs(
        ["Teilnahme", "Einstellungen", "Berechnungen"]
    )

    foto_names_submitted = {o.get("name") for o in orders}
    merch_names_submitted = {o.get("name") for o in merch_orders}
    names_with_unterschrift = {
        o.get("name") for o in merch_orders if o.get("design_image")
    }

    # region Teilnahme
    with sub_teilnahme:
        tab_teilnahme_foto, tab_teilnahme_hoodie, tab_teilnahme_unterschriften = st.tabs(
            ["📸 Fotos", "🧥 Hoodies", "🖊️ Unterschriften"])

        with tab_teilnahme_foto:
            st.download_button(
                label="Fotobestellung Teilnahme PDF",
                data=generate_teilnahme_pdf_foto(orders),
                file_name="Teilnahme_Fotos.pdf",
                mime="application/pdf"
            )
            st.markdown("### 📸 Fotobestellung")
            foto_submitted = sorted(
                n for n in NAME_OPTIONS if n in foto_names_submitted)
            foto_missing = sorted(
                n for n in NAME_OPTIONS if n not in foto_names_submitted)

            fc1, fc2, fc3 = st.columns(3)
            fc1.metric("Bestellt", len(foto_submitted))
            fc2.metric("Ausstehend", len(foto_missing))
            fc3.metric("Gesamt", len(NAME_OPTIONS))

            col_done, col_missing = st.columns(2)
            with col_done:
                st.markdown(f"**✅ Abgegeben ({len(foto_submitted)})**")
                for name in foto_submitted:
                    st.markdown(
                        f'<span style="{TAG_PAID}">{name}</span>', unsafe_allow_html=True)
            with col_missing:
                st.markdown(f"**⏳ Noch nicht bestellt ({len(foto_missing)})**")
                for name in foto_missing:
                    st.markdown(
                        f'<span style="{TAG_UNPAID}">{name}</span>', unsafe_allow_html=True)

        with tab_teilnahme_hoodie:
            st.download_button(
                label="Hoodie Teilnahme PDF",
                data=generate_teilnahme_pdf_hoodie(merch_orders),
                file_name="Teilnahme_Hoodies.pdf",
                mime="application/pdf"
            )
            st.markdown("### 🧥 Hoodie Bestellung")
            merch_submitted = sorted(
                n for n in NAME_OPTIONS if n in merch_names_submitted)
            merch_missing = sorted(
                n for n in NAME_OPTIONS if n not in merch_names_submitted)

            mc1, mc2, mc3 = st.columns(3)
            mc1.metric("Bestellt", len(merch_submitted))
            mc2.metric("Ausstehend", len(merch_missing))
            mc3.metric("Gesamt", len(NAME_OPTIONS))

            col_done2, col_missing2 = st.columns(2)
            with col_done2:
                st.markdown(f"**✅ Abgegeben ({len(merch_submitted)})**")
                for name in merch_submitted:
                    st.markdown(
                        f'<span style="{TAG_PAID}">{name}</span>', unsafe_allow_html=True)
            with col_missing2:
                st.markdown(
                    f"**⏳ Noch nicht bestellt ({len(merch_missing)})**")
                for name in merch_missing:
                    st.markdown(
                        f'<span style="{TAG_UNPAID}">{name}</span>', unsafe_allow_html=True)

        with tab_teilnahme_unterschriften:
            st.download_button(
                label="Unterschriften Teilnahme PDF",
                data=generate_teilnahme_pdf_all(orders, merch_orders),
                file_name="Teilnahme_Unterschriften.pdf",
                mime="application/pdf"
            )
            st.markdown("### 🎯 Teilnahme Unterschriften")
            preset_and_unterschrift = sorted(
                n for n in NAME_OPTIONS
                if n in TEILNAHME_PRESET or n in names_with_unterschrift
            )
            not_in_preset = sorted(
                n for n in NAME_OPTIONS
                if n not in preset_and_unterschrift
            )

            ac1, ac2, ac3 = st.columns(3)
            ac1.metric("Auf Liste / Mit Unterschrift",
                       len(preset_and_unterschrift))
            ac2.metric("Nicht auf Liste", len(not_in_preset))
            ac3.metric("Gesamt", len(NAME_OPTIONS))

            col_done3, col_missing3 = st.columns(2)
            with col_done3:
                st.markdown(
                    f"**✅ Auf Liste / Mit Unterschrift ({len(preset_and_unterschrift)})**")
                for name in preset_and_unterschrift:
                    st.markdown(
                        f'<span style="{TAG_PAID}">{name}</span>', unsafe_allow_html=True)
            with col_missing3:
                st.markdown(f"**⏳ Nicht auf Liste ({len(not_in_preset)})**")
                for name in not_in_preset:
                    st.markdown(
                        f'<span style="{TAG_UNPAID}">{name}</span>', unsafe_allow_html=True)

    # region Einstellungen
    with sub_einstellungen:
        st.markdown("### Preise & Einstellungen")

        from helper.config import CONFIG_URL, load_config  # noqa: PLC0415

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
                    "MAX_IMAGES": str(int(new_max)),
                    "NORMAL_IMAGE_PRICE": str(new_price),
                    "UPLOAD_PHOTO_PRICE": str(new_upload),
                    "AMOUNT_OF_FREE_IMAGES": str(int(new_free)),
                    "PRINTING_COST": str(cfg["PRINTING_COST"]),
                }
                success = all(
                    requests.patch(
                        f"{CONFIG_URL}?key=eq.{key}",
                        json={"value": value},
                        headers={**get_headers(), "Prefer": "return=minimal"},
                        timeout=10
                    ).status_code in {200, 201, 204}
                    for key, value in updates.items()
                )
                if success:
                    st.cache_data.clear()
                    st.success("✅ Einstellungen gespeichert!")
                else:
                    st.error("❌ Fehler beim Speichern — bitte Logs prüfen.")

    # region Berechnungen
    with sub_berechnungen:
        total_standard = 0
        total_mottowoche = 0
        total_stufenfotos = 0
        total_free_imgs = 0

        for order in orders:
            total_standard += len(order.get("lk_typ") or []) + \
                len(order.get("gk_typ") or [])
            total_mottowoche += len(order.get("mottowoche") or [])
            total_stufenfotos += len(order.get("stufenfotos") or [])
            total_free_imgs += min(order.get("image_count")
                                   or 0, AMOUNT_OF_FREE_IMAGES)

        total_extra_images = total_standard + total_mottowoche + total_stufenfotos
        total_all_images = total_extra_images

        rev_free = total_free_imgs * NORMAL_IMAGE_PRICE
        rev_extra = sum(
            max((o.get("image_count") or 0) -
                AMOUNT_OF_FREE_IMAGES, 0) * NORMAL_IMAGE_PRICE
            for o in orders
        )
        total_revenue = rev_free + rev_extra
        total_print_cost = total_all_images * PRINTING_COST
        total_profit = total_revenue - total_print_cost

        # Forecast
        st.markdown("#### Gewinnvorhersage")
        fc1, fc2 = st.columns(2)
        forecast_normal = fc1.number_input(
            "Anzahl Normalbilder (Vorhersage)", min_value=0, value=total_extra_images, step=1
        )
        forecast_uploads = fc2.number_input(
            "Anzahl Uploads (Vorhersage)", min_value=0, value=0, step=1
        )

        forecast_revenue = forecast_normal * NORMAL_IMAGE_PRICE + \
            forecast_uploads * UPLOAD_PHOTO_PRICE
        forecast_cost = (forecast_normal + forecast_uploads) * PRINTING_COST
        forecast_profit = forecast_revenue - forecast_cost

        f1, f2, f3 = st.columns(3)
        f1.metric("Erwartete Einnahmen", f"{forecast_revenue:.2f}€")
        f2.metric("Erwartete Druckkosten", f"{forecast_cost:.2f}€")
        f3.metric("Erwarteter Gewinn", f"{forecast_profit:.2f}€")

        st.divider()

        # Gratis images (Abikasse)
        st.markdown("#### Gratis-Bilder (Abikasse zahlt)")
        _h = st.columns([3, 1, 1, 1, 1])
        for col, label in zip(_h, ["**Typ**", "**Anzahl**", "**Verkaufspreis**", "**Druckkosten**", "**Gewinn**"]):
            col.markdown(label)

        rev = total_free_imgs * NORMAL_IMAGE_PRICE
        cost = total_free_imgs * PRINTING_COST
        _c = st.columns([3, 1, 1, 1, 1])
        _c[0].write(f"Normalbild ({AMOUNT_OF_FREE_IMAGES} gratis)")
        _c[1].write(str(total_free_imgs))
        _c[2].write(f"{rev:.2f}€")
        _c[3].write(f"{cost:.2f}€")
        _c[4].write(f"**{rev - cost:.2f}€**")

        st.divider()

        # Extra images (student pays)
        st.markdown("#### Extra-Bilder (Student zahlt)")
        _h2 = st.columns([3, 1, 1, 1, 1])
        for col, label in zip(_h2, ["**Typ**", "**Anzahl**", "**Verkaufspreis**", "**Druckkosten**", "**Gewinn**"]):
            col.markdown(label)

        breakdown_rows = [
            ("LK / GK Fotos",  total_standard,    NORMAL_IMAGE_PRICE),
            ("Mottowoche",      total_mottowoche,  NORMAL_IMAGE_PRICE),
            ("Stufenfotos",     total_stufenfotos, NORMAL_IMAGE_PRICE),
        ]
        for row_label, count, price in breakdown_rows:
            rev = count * price
            cost = count * PRINTING_COST
            _c = st.columns([3, 1, 1, 1, 1])
            _c[0].write(row_label)
            _c[1].write(str(count))
            _c[2].write(f"{rev:.2f}€")
            _c[3].write(f"{cost:.2f}€")
            _c[4].write(f"**{rev - cost:.2f}€**")

        s0, s1, s2, s3, s4 = st.columns([3, 1, 1, 1, 1])
        s1.metric("Anzahl Bilder", str(total_all_images))
        s2.metric("Gesamteinnahmen", f"{total_revenue:.2f}€")
        s3.metric("Druckkosten gesamt", f"{total_print_cost:.2f}€")
        s4.metric("Gewinn", f"{total_profit:.2f}€")

        st.divider()

        # Per-image price structure
        st.markdown("#### Preisstruktur pro Bild")
        margin_normal = NORMAL_IMAGE_PRICE - PRINTING_COST
        margin_upload = UPLOAD_PHOTO_PRICE - PRINTING_COST
        pct_normal = (margin_normal / NORMAL_IMAGE_PRICE *
                      100) if NORMAL_IMAGE_PRICE else 0
        pct_upload = (margin_upload / UPLOAD_PHOTO_PRICE *
                      100) if UPLOAD_PHOTO_PRICE else 0

        pu1, pu2 = st.columns(2)
        with pu1:
            st.markdown("**Normalbild / Mottowoche / Stufenfoto**")
            p1, p2, p3 = st.columns(3)
            p1.metric("Verkaufspreis", f"{NORMAL_IMAGE_PRICE:.2f}€")
            p2.metric("Druckkosten",   f"{PRINTING_COST:.2f}€")
            p3.metric("Marge", f"{margin_normal:.2f}€",
                      delta=f"{pct_normal:.0f}%")
        with pu2:
            st.markdown("**Eigener Upload**")
            p1, p2, p3 = st.columns(3)
            p1.metric("Verkaufspreis", f"{UPLOAD_PHOTO_PRICE:.2f}€")
            p2.metric("Druckkosten",   f"{PRINTING_COST:.2f}€")
            p3.metric("Marge", f"{margin_upload:.2f}€",
                      delta=f"{pct_upload:.0f}%")
