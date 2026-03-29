import streamlit as st
import requests
from datetime import datetime
from constants import (
    BASE_HEADERS,
    LK_OPTIONS,
    GK_OPTIONS,
    MOTTO_LABELS,
    PREVIEW_IMAGES
)
from config import (
    MAX_IMAGES,
    NORMAL_IMAGE_PRICE,
    STUFENFOTO_PRICE,
    EXTRA_PHOTO_PRICE
)

from constants import (
    SUPABASE_URL
)

from utils import (
    upload_image_to_supabase
)


st.set_page_config(page_title="Fotobestellung")
st.title("📸 Fotobestellung")
st.write(
    f"3 Bilder sind inklusive. Jedes weitere Bild kostet {NORMAL_IMAGE_PRICE:.2f}€. Größere Stufenfotos kosten {STUFENFOTO_PRICE:.2f}€. Eigene Fotos kosten {EXTRA_PHOTO_PRICE:.2f}€.")

# Name
name = st.text_input("Name")

# Leistungskurs
st.subheader("Leistungskurs Foto")
lk_choice = st.radio("Leistungskurs auswählen", LK_OPTIONS)
st.write("Typ auswählen:")
lk_tpy = []
if st.checkbox("Normalbild", key="lk_normal"):
    lk_tpy.append("Normalbild")
if st.checkbox("Spaßbild", key="lk_spass"):
    lk_tpy.append("Spaßbild")

# Grundkurs
st.subheader("Grundkurs Foto")
gk_choice = st.radio("Grundkurs auswählen", GK_OPTIONS)
st.write("Typ auswählen:")
gk_tpy = []
if st.checkbox("Normalbild", key="gk_normal"):
    gk_tpy.append("Normalbild")
if st.checkbox("Spaßbild", key="gk_spass"):
    gk_tpy.append("Spaßbild")

# Mottowoche
st.subheader("Mottowoche")

for label in MOTTO_LABELS.values():
    st.checkbox(label, key=f"{label}_checkbox")
selected_mottos = [v for l, v in MOTTO_LABELS.items()
                   if st.session_state.get(f"{l}_checkbox")]

# Stufenfotos
st.subheader(f"Stufenfotos ({STUFENFOTO_PRICE:.2f}€)")
st.write(f"{STUFENFOTO_PRICE:.2f}€ pro Bild - 12,7 x 17,8cm - matt")
stufen_options = {"Pausenhof": 1, "Abau Treppe": 2}
for label in stufen_options:
    st.checkbox(label, key=f"{label}_checkbox")
selected_stufen = [v for l, v in stufen_options.items(
) if st.session_state.get(f"{l}_checkbox")]

# ── IMAGE UPLOAD ───────────────────────────────────────────────────────────────
st.subheader(
    f"Eigene Fotos hochladen")
st.write(f"{EXTRA_PHOTO_PRICE:.2f}€ pro Bild - 10,2 x 15,2cm - matt")
uploaded_files = st.file_uploader(
    "Fotos auswählen",
    type=["jpg", "jpeg", "png", "webp"],
    accept_multiple_files=True
)

if uploaded_files and len(uploaded_files) > MAX_IMAGES:
    uploaded_files = uploaded_files[:MAX_IMAGES]
    st.error(f"❌ Maximal {MAX_IMAGES} Bilder erlaubt.")
anzahl_eigener_fotos = len(uploaded_files) if uploaded_files else 0

# Cost calculation
num_images = len(lk_tpy) + len(gk_tpy) + len(selected_mottos)
extra_cost = 0.0
if num_images > 3:
    extra_cost = (num_images - 3) * NORMAL_IMAGE_PRICE
for _ in selected_stufen:
    extra_cost += STUFENFOTO_PRICE
# Commented out as extra_photos_count is no longer used
extra_cost += anzahl_eigener_fotos * EXTRA_PHOTO_PRICE


# Overview
st.divider()
bestellung = []
with st.expander("Überblick deiner Bestellung"):

    # Kursfotos
    for t in lk_tpy:
        img_url = PREVIEW_IMAGES["lk"].get(lk_choice, {}).get(t)
        if img_url:
            st.image(
                img_url,
                caption=f"{lk_choice} - {t}",
                use_container_width=True
            )
    for t in gk_tpy:
        img_url = PREVIEW_IMAGES["gk"].get(gk_choice, {}).get(t)
        if img_url:
            st.image(
                img_url,
                caption=f"{gk_choice} - {t}",
                use_container_width=True
            )

    # Mottowoche
    motto_label_map = {v: k for k, v in MOTTO_LABELS.items()}
    for m in selected_mottos:
        img_url = PREVIEW_IMAGES["mottowoche"].get(m)
        if img_url:
            st.image(
                img_url,
                caption=f"Mottowoche - {motto_label_map.get(m, m)}",
                use_container_width=True
            )

    # Stufenfotos
    stufen_label_map = {v: k for k, v in stufen_options.items()}
    for s in selected_stufen:
        img_url = PREVIEW_IMAGES["stufenfotos"].get(s)
        if img_url:
            st.image(
                img_url,
                caption=f"Stufenfoto - {stufen_label_map.get(s, s)}",
                use_container_width=True
            )

    for item in bestellung:
        st.write(item)

    # Uploaded images
    if uploaded_files:
        for image in uploaded_files:
            st.image(
                image,
                caption=f"Eigenes Foto - {image.name}",
                use_container_width=True
            )

if extra_cost > 0:
    st.warning(f"⚠️ Zusatzkosten: **{extra_cost:.2f}€**")
else:
    st.success("✅ Keine Zusatzkosten - alles inklusive!")

# ── SUBMIT ────────────────────────────────────────────────────────────────────
if st.button("Absenden", type="primary"):
    if not name:
        st.error("Bitte Namen eingeben.")
        st.stop()

    if uploaded_files and anzahl_eigener_fotos > MAX_IMAGES:
        st.error(f"❌ Maximal {MAX_IMAGES} Bilder erlaubt.")
        st.stop()

    # 1. Insert order, get back the new row's id
    order_data = {
        "name": name,
        "leistungskurs": lk_choice,
        "lk_typ": lk_tpy,
        "grundkurs": gk_choice,
        "gk_tpy": gk_tpy,
        "mottowoche": selected_mottos,
        "stufenfotos": selected_stufen,
        "extra_photos": anzahl_eigener_fotos,
        "image_count": num_images,
        "extra_cost": extra_cost,
        "paid": extra_cost == 0,
        "created_at": datetime.now().isoformat(),
    }

    order_response = requests.post(
        f"{SUPABASE_URL}/rest/v1/orders",
        json=order_data,
        headers={**BASE_HEADERS, "Prefer": "return=representation"}
    )

    if order_response.status_code not in [200, 201]:
        st.error(f"❌ Bestellung fehlgeschlagen: {order_response.text}")
        st.stop()

    order_id = order_response.json()[0]["id"]  # uuid of the new order

    # 2. Upload each image and insert a row into order_images
    if uploaded_files:
        with st.spinner("Bilder werden hochgeladen..."):
            for i, file in enumerate(uploaded_files):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S%f")
                safe_name = name.replace(" ", "_")
                ext = file.name.split(".")[-1]
                filename = f"{safe_name}_{timestamp}.{ext}"

                url = upload_image_to_supabase(file, filename)
                if url is None:
                    st.stop()

                img_data = {
                    "order_id": order_id,
                    "url": url,
                    "filename": filename,
                    "position": i + 1
                }
                img_response = requests.post(
                    f"{SUPABASE_URL}/rest/v1/order_images",
                    json=img_data,
                    headers={**BASE_HEADERS, "Prefer": "return=minimal"}
                )
                if img_response.status_code not in [200, 201, 204]:
                    st.error(
                        f"❌ Bilddaten konnten nicht gespeichert werden: {img_response.text}")
                    st.stop()

    st.success("✅ Bestellung gespeichert!")
