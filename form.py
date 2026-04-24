import streamlit as st
import requests
from datetime import datetime
from helper.constants import (
    COLOR_OPTIONS,
    LK_OPTIONS,
    GK_OPTIONS,
    MOTTO_LABELS,
    NAME_OPTIONS,
    PREVIEW_IMAGES,
    SIZE_OPTIONS,
    STUFEN_LABELS,
    SUPABASE_URL
)
from helper.auth import get_headers
from helper.config import (
    NORMAL_IMAGE_PRICE,
    AMOUNT_OF_FREE_IMAGES
)
from helper.utils import (
    calculate_extra_cost,
    upload_image_to_supabase
)

# ── PAGE ──────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Bestellung")
st.title("Hoodie und Foto Bestellung")

# ── TABS ──────────────────────────────────────────────────────────────────────
tab_merch, tab_foto = st.tabs(["Hoodies", "Fotos"])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 - HOODIE BESTELLUNG
# ══════════════════════════════════════════════════════════════════════════════
with tab_merch:

    merch_name = st.selectbox(
        "Name auswählen", [""] + NAME_OPTIONS, key="merch_name")

    st.subheader("Größe")
    size = st.radio("Größe auswählen", SIZE_OPTIONS, horizontal=True)

    st.subheader("Farbe")
    color = st.radio("Farbe auswählen", COLOR_OPTIONS)

    st.subheader("Unterschrift hochladen (wenn nicht auf Design)")
    st.write("Schwarz-Weiß, Digitalisiert, Bild oder Pdf")
    design_file = st.file_uploader(
        "Design auswählen",
        type=["jpg", "jpeg", "png", "webp", "pdf"],
        key="merch_design"
    )
    if design_file:
        st.image(design_file, caption="Vorschau",
                 use_container_width=True)

    if st.button("Speichern", type="primary", key="merch_submit"):
        if not merch_name:
            st.error("Bitte Namen auswählen.")
            st.stop()

        # Check for duplicate orders
        existing = requests.get(
            f"{SUPABASE_URL}/rest/v1/abimerch",
            headers={**get_headers()},
            params={"name": f"eq.{merch_name}"},
            timeout=10
        )
        if existing.status_code == 200 and len(existing.json()) > 0:
            st.warning(
                f"⚠️ Es existiert bereits eine Hoodie-Bestellung für {merch_name}. Eine neue Bestellung wird erstellt.")

        design_url = None
        if design_file:
            with st.spinner("Unterschrift wird hochgeladen..."):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S%f")
                safe_name = merch_name.replace(" ", "_")
                ext = design_file.name.split(".")[-1]
                filename = f"hoodie_{safe_name}_{timestamp}.{ext}"
                design_url = upload_image_to_supabase(design_file, filename)
                if design_url is None:
                    st.stop()

        order_data = {
            "name": merch_name,
            "size": size,
            "color": color,
            "design_image": design_url,
            "created_at": datetime.now().isoformat(),
        }

        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/abimerch",
            json=order_data,
            headers={**get_headers(), "Prefer": "return=minimal"},
            timeout=10
        )

        if response.status_code in [200, 201, 204]:
            st.success(
                f"✅ Bestellung gespeichert! ({merch_name} - {size} - {color})")
        else:
            st.error(f"❌ Fehler beim Speichern: {response.text}")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 - FOTOBESTELLUNG
# ══════════════════════════════════════════════════════════════════════════════
with tab_foto:
    st.write(
        f"{AMOUNT_OF_FREE_IMAGES} Bilder sind gratis. "
        f"Jedes weitere Bild kostet {NORMAL_IMAGE_PRICE:.2f}€."
    )
    st.write("12,7 x 17,8cm - matt")

    # Name
    foto_name = st.selectbox(
        "Name auswählen", [""] + NAME_OPTIONS, key="foto_name")

    # Leistungskurs
    st.subheader("Leistungskurs Foto")
    lk_choice = st.radio("Leistungskurs auswählen", LK_OPTIONS)
    st.write("Typ auswählen:")
    lk_typ = []
    if st.checkbox("Normalbild", key="lk_normal"):
        lk_typ.append("Normalbild")
    if st.checkbox("Spaßbild", key="lk_spass"):
        lk_typ.append("Spaßbild")

    if lk_typ:
        cols = st.columns(2)
        for idx, t in enumerate(lk_typ):
            img_url = PREVIEW_IMAGES["lk"].get(lk_choice, {}).get(t)
            if img_url:
                with cols[idx]:
                    st.image(img_url, caption=t)

    # Grundkurs
    st.subheader("Grundkurs Foto")
    gk_choice = st.radio("Grundkurs auswählen", GK_OPTIONS)
    st.write("Typ auswählen:")
    gk_typ = []
    if st.checkbox("Normalbild", key="gk_normal"):
        gk_typ.append("Normalbild")
    if st.checkbox("Spaßbild", key="gk_spass"):
        gk_typ.append("Spaßbild")

    if gk_typ:
        cols = st.columns(2)
        for idx, t in enumerate(gk_typ):
            img_url = PREVIEW_IMAGES["gk"].get(gk_choice, {}).get(t)
            if img_url:
                with cols[idx]:
                    st.image(img_url, caption=t)

    # Mottowoche
    st.subheader("Mottowoche")
    for k, label in MOTTO_LABELS.items():
        st.checkbox(label, key=f"{k}_motto_checkbox")

    selected_mottos = [
        k for k in MOTTO_LABELS
        if st.session_state.get(f"{k}_motto_checkbox")
    ]

    if selected_mottos:
        cols = st.columns(2)
        for idx, m in enumerate(selected_mottos):
            img_url = PREVIEW_IMAGES["mottowoche"].get(m)
            if img_url:
                with cols[idx % 2]:
                    st.image(img_url, caption=MOTTO_LABELS.get(m, str(m)))

    # Stufenfotos
    st.subheader("Stufenfotos")
    for k, label in STUFEN_LABELS.items():
        st.checkbox(label, key=f"{k}_stufen_checkbox")

    selected_stufen = [
        k for k in STUFEN_LABELS
        if st.session_state.get(f"{k}_stufen_checkbox")
    ]

    if selected_stufen:
        cols = st.columns(2)
        for idx, s in enumerate(selected_stufen):
            img_url = PREVIEW_IMAGES["stufenfotos"].get(s)
            if img_url:
                with cols[idx % 2]:
                    st.image(img_url, caption=STUFEN_LABELS.get(s, str(s)))

    # Cost calculation
    num_images = len(lk_typ) + len(gk_typ) + \
        len(selected_mottos) + len(selected_stufen)
    extra_cost = calculate_extra_cost(
        num_images=num_images, extra_photos=0)
    covered_images = min(num_images, AMOUNT_OF_FREE_IMAGES)

    if extra_cost > 0:
        st.warning(
            f"⚠️ Zusatzkosten: **{extra_cost:.2f}€** - "
            f"{num_images} Bilder ausgewählt, {covered_images} gratis"
        )
    else:
        st.success("✅ Alle Bilder sind gratis!")

    # Submit
    if st.button("Absenden", type="primary", key="foto_submit"):
        if not foto_name:
            st.error("Bitte Namen eingeben.")
            st.stop()

        # Check for duplicate orders
        existing = requests.get(
            f"{SUPABASE_URL}/rest/v1/orders",
            headers={**get_headers()},
            params={"name": f"eq.{foto_name}", "archived": "eq.false"},
            timeout=10
        )
        if existing.status_code == 200 and len(existing.json()) > 0:
            st.warning(
                f"⚠️ Es existiert bereits eine Bestellung für {foto_name}. Eine neue Bestellung wird erstellt.")

        if extra_cost > 0:
            st.session_state["foto_pending"] = True
        else:
            st.session_state["foto_pending"] = False
            st.session_state["foto_confirmed"] = True

    if st.session_state.get("foto_pending") and not st.session_state.get("foto_confirmed"):
        st.warning(
            f"⚠️ Du musst **{extra_cost:.2f}€** bezahlen. "
            f"Deine Fotos werden nur gedruckt, wenn du bezahlt hast."
        )
        st.info("PayPal an: l-blu@outlook.de oder gib Levi das Geld persönlich.")
        if st.button("✅ Bestätigen", type="primary", key="foto_confirm"):
            st.session_state["foto_confirmed"] = True
            st.rerun()
        if st.button("❌ Abbrechen", key="foto_cancel"):
            st.session_state["foto_pending"] = False
            st.rerun()

    if st.session_state.get("foto_confirmed"):
        st.session_state["foto_pending"] = False
        st.session_state["foto_confirmed"] = False

        order_data = {
            "name": foto_name,
            "leistungskurs": lk_choice,
            "lk_typ": lk_typ,
            "grundkurs": gk_choice,
            "gk_typ": gk_typ,
            "mottowoche": selected_mottos,
            "stufenfotos": selected_stufen,
            "extra_photos": 0,
            "image_count": num_images,
            "paid": extra_cost == 0,
            "created_at": datetime.now().isoformat(),
        }

        order_response = requests.post(
            f"{SUPABASE_URL}/rest/v1/orders",
            json=order_data,
            headers={**get_headers(), "Prefer": "return=representation"},
            timeout=10
        )

        if order_response.status_code not in [200, 201]:
            st.error(f"❌ Bestellung fehlgeschlagen: {order_response.text}")
            st.stop()

        order_id = order_response.json()[0]["id"]

        st.success("✅ Bestellung gespeichert!")
