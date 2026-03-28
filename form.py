import streamlit as st
import requests
from datetime import datetime

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_ANON_KEY"]
BUCKET_NAME = "images"
MAX_IMAGES = 10
# Prices
NORMAL_IMAGE_PRICE = 0.15
STUFENFOTO_PRICE = 0.20
EXTRA_PHOTO_PRICE = 0.80

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    # 👈 needed to get the inserted row back (incl. id)
    "Prefer": "return=representation"
}


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


st.set_page_config(page_title="Fotobestellung")
st.title("📸 Fotobestellung")
st.write(
    f"3 Bilder sind inklusive. Jedes weitere Bild kostet {NORMAL_IMAGE_PRICE:.2f} €. Stufenfotos kosten {STUFENFOTO_PRICE:.2f} € extra. Eigene Fotos kosten {EXTRA_PHOTO_PRICE:.2f} € extra.")

# Name
name = st.text_input("Name")

# Leistungskurs
st.subheader("Leistungskurs Foto")
lk_options = ["Englisch", "Geschichte", "Geo",
              "Sport", "Kunst", "Französisch", "Physik"]
lk_choice = st.radio("Leistungskurs auswählen", lk_options)
st.write("Typ auswählen:")
lk_tpy = []
if st.checkbox("Normalbild", key="lk_normal"):
    lk_tpy.append("Normalbild")
if st.checkbox("Spaßbild", key="lk_spass"):
    lk_tpy.append("Spaßbild")

# Grundkurs
st.subheader("Grundkurs Foto")
gk_options = ["Grundkurs 1", "Grundkurs 2", "Grundkurs 3", "Grundkurs 4"]
gk_choice = st.radio("Grundkurs auswählen", gk_options)
st.write("Typ auswählen:")
gk_tpy = []
if st.checkbox("Normalbild", key="gk_normal"):
    gk_tpy.append("Normalbild")
if st.checkbox("Spaßbild", key="gk_spass"):
    gk_tpy.append("Spaßbild")

# Mottowoche
st.subheader("Mottowoche")
motto_options = {
    "Montag - Mafia": 1, "Dienstag - Gender Swap": 2,
    "Mittwoch - Kindheitshelden": 3, "Donnerstag - Straight out of Bed": 4,
    "Freitag - Gruppenkostüm": 5,
}
for label in motto_options:
    st.checkbox(label, key=f"{label}_checkbox")
selected_mottos = [v for l, v in motto_options.items(
) if st.session_state.get(f"{l}_checkbox")]

# Stufenfotos
st.subheader(f"Stufenfotos ({STUFENFOTO_PRICE:.2f} € extra)")
stufen_options = {"Pausenhof": 1, "Abau Treppe": 2}
for label in stufen_options:
    st.checkbox(label, key=f"{label}_checkbox")
selected_stufen = [v for l, v in stufen_options.items(
) if st.session_state.get(f"{l}_checkbox")]

# ── IMAGE UPLOAD ───────────────────────────────────────────────────────────────
st.subheader(f"Eigene Fotos hochladen ({EXTRA_PHOTO_PRICE:.2f} € extra)")
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
    covered_payments = 3 * NORMAL_IMAGE_PRICE
else:
    covered_payments = num_images * NORMAL_IMAGE_PRICE
for _ in selected_stufen:
    extra_cost += STUFENFOTO_PRICE
# Commented out as extra_photos_count is no longer used
extra_cost += anzahl_eigener_fotos * EXTRA_PHOTO_PRICE
if extra_cost > 0:
    st.warning(f"⚠️ Zusatzkosten: {extra_cost:.2f} €")

# ── SUBMIT ────────────────────────────────────────────────────────────────────
if st.button("Absenden"):
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
        "covered_payments": covered_payments,
        "paid": extra_cost == 0,
        "created_at": datetime.now().isoformat(),
    }

    order_response = requests.post(
        f"{SUPABASE_URL}/rest/v1/orders",
        json=order_data,
        headers=HEADERS
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
                    headers={**HEADERS, "Prefer": "return=minimal"}
                )
                if img_response.status_code not in [200, 201, 204]:
                    st.error(
                        f"❌ Bilddaten konnten nicht gespeichert werden: {img_response.text}")
                    st.stop()

    st.success("✅ Bestellung gespeichert!")
