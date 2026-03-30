import streamlit as st
import requests
from datetime import datetime
from constants import (
    BASE_HEADERS,
    LK_OPTIONS,
    GK_OPTIONS,
    MOTTO_LABELS,
    PREVIEW_IMAGES,
    STUFEN_LABELS,
    SUPABASE_URL
)
from config import (
    MAX_IMAGES,
    NORMAL_IMAGE_PRICE,
    UPLOAD_PHOTO_PRICE,
    AMOUNT_OF_FREE_IMAGES
)
from utils import (
    upload_image_to_supabase,
    calculate_extra_cost
)


st.set_page_config(page_title="Fotobestellung")
st.title("📸 Fotobestellung")
st.write(
    f"{AMOUNT_OF_FREE_IMAGES} Bilder sind gratis. Jedes weitere Bild kostet {NORMAL_IMAGE_PRICE:.2f}€. Eigene Fotos kosten {UPLOAD_PHOTO_PRICE:.2f}€.")

st.write(f"12,7 x 17,8cm - matt")
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

for k, label in MOTTO_LABELS.items():
    st.checkbox(label, key=f"{k}_motto_checkbox")

selected_mottos = [
    k for k in MOTTO_LABELS
    if st.session_state.get(f"{k}_motto_checkbox")
]

# Stufenfotos
st.subheader(f"Stufenfotos")
for k, label in STUFEN_LABELS.items():
    st.checkbox(label, key=f"{k}_stufen_checkbox")

selected_stufen = [
    k for k in STUFEN_LABELS
    if st.session_state.get(f"{k}_stufen_checkbox")
]


# ── IMAGE UPLOAD ───────────────────────────────────────────────────────────────
st.subheader(
    f"Eigene Fotos hochladen zum drucken (optional)")
st.write(f"{UPLOAD_PHOTO_PRICE:.2f}€ pro Bild")
uploaded_files = st.file_uploader(
    "Fotos auswählen",
    type=["jpg", "jpeg", "png", "webp"],
    accept_multiple_files=True
)

if uploaded_files and len(uploaded_files) > MAX_IMAGES:
    uploaded_files = uploaded_files[:MAX_IMAGES]
    st.error(f"❌ Maximal {MAX_IMAGES} Bilder erlaubt.")
amount_uploaded_fotos = len(uploaded_files) if uploaded_files else 0

# Overview
st.divider()

with st.expander("Überblick deiner Bestellung"):
    # Kursfotos
    for t in lk_tpy:
        img_url = PREVIEW_IMAGES["lk"].get(lk_choice, {}).get(t)
        if img_url:
            st.image(
                img_url,
                caption=f"{lk_choice} - {t}",
            )
    for t in gk_tpy:
        img_url = PREVIEW_IMAGES["gk"].get(gk_choice, {}).get(t)
        if img_url:
            st.image(
                img_url,
                caption=f"{gk_choice} - {t}",
            )

    # Mottowoche
    for m in selected_mottos:
        img_url = PREVIEW_IMAGES["mottowoche"].get(m)
        if img_url:
            st.image(
                img_url,
                caption=f"Mottowoche - {MOTTO_LABELS.get(m, m)}",
            )

    # Stufenfotos
    for s in selected_stufen:
        img_url = PREVIEW_IMAGES["stufenfotos"].get(s)
        if img_url:
            st.image(
                img_url,
                caption=f"Stufenfoto - {STUFEN_LABELS.get(s, s)}",
            )

    # Uploaded images
    if uploaded_files:
        for image in uploaded_files:
            st.image(
                image,
                caption=f"Eigenes Foto - {image.name}",
            )

# Cost calculation
num_images = len(lk_tpy) + len(gk_tpy) + \
    len(selected_mottos) + len(selected_stufen)
extra_cost = calculate_extra_cost(
    num_images=num_images, extra_photos=amount_uploaded_fotos)
covered_images = min(num_images, AMOUNT_OF_FREE_IMAGES)

if extra_cost > 0:
    st.warning(
        f"⚠️ Zusatzkosten: **{extra_cost:.2f}€** - {num_images} Bilder ausgewählt, {covered_images} gratis")
else:
    st.success("✅ Alle Bilder sind gratis!")


# ── SUBMIT ────────────────────────────────────────────────────────────────────
if st.button("Absenden", type="primary"):
    if not name:
        st.error("Bitte Namen eingeben.")
        st.stop()
    if extra_cost > 0:
        st.session_state["pending_order"] = True
    else:
        st.session_state["pending_order"] = False
        st.session_state["confirmed"] = True

if st.session_state.get("pending_order") and not st.session_state.get("confirmed"):
    st.warning(
        f"⚠️ Du musst **{extra_cost:.2f}€** bezahlen. "
        f"Deine Fotos werden nur gedruckt, wenn du bezahlt hast. "
    )
    st.info(f"PayPal an: l-blu@outlook.de oder gib Levi das Geld persönlich.")
    if st.button("✅ Bestätigen", type="primary"):
        st.session_state["confirmed"] = True
        st.rerun()
    if st.button("❌ Abbrechen"):
        st.session_state["pending_order"] = False
        st.rerun()

if st.session_state.get("confirmed"):
    st.session_state["pending_order"] = False
    st.session_state["confirmed"] = False

    # 1. Insert order, get back the new row's id
    order_data = {
        "name": name,
        "leistungskurs": lk_choice,
        "lk_typ": lk_tpy,
        "grundkurs": gk_choice,
        "gk_tpy": gk_tpy,
        "mottowoche": selected_mottos,
        "stufenfotos": selected_stufen,
        "extra_photos": amount_uploaded_fotos,
        "image_count": num_images,
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

    order_id = order_response.json()[0]["id"]

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
