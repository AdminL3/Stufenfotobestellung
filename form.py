import streamlit as st
import requests
from datetime import datetime

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_ANON_KEY"]
TABLE_URL = f"{SUPABASE_URL}/rest/v1/orders"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

st.set_page_config(page_title="Fotobestellung")
st.title("📸 Fotobestellung")
st.write("3 Bilder sind inklusive. Jedes weitere Bild kostet 0,15 €. Stufenfotos kosten 0,20 € extra. Eigene Fotos kosten 0,50 € extra.")

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
    "Montag - Mafia": 1,
    "Dienstag - Gender Swap": 2,
    "Mittwoch - Kindheitshelden": 3,
    "Donnerstag - Straight out of Bed": 4,
    "Freitag - Gruppenkostüm": 5,
}
for label in motto_options:
    st.checkbox(label, key=f"{label}_checkbox")
selected_mottos = [
    value for label, value in motto_options.items()
    if st.session_state.get(f"{label}_checkbox", False)
]

# Stufenfotos
st.subheader("Stufenfotos (0,20 € extra)")
stufen_options = {
    "Pausenhof": 1,
    "Abau Treppe": 2,
}
for label in stufen_options:
    st.checkbox(label, key=f"{label}_checkbox")
selected_stufen = [
    value for label, value in stufen_options.items()
    if st.session_state.get(f"{label}_checkbox", False)
]

# Extra fotos
st.subheader("Zusätzliche Fotos (0,50 € extra)")
extra_photos_count = st.number_input("Anzahl zusätzlicher Fotos", min_value=0,
                                     max_value=10, key="extra_photos", value=0, step=1)

# Cost calculation (internal only, not shown to user beyond the warning)
num_images = len(lk_tpy) + len(gk_tpy) + len(selected_mottos)
extra_cost = 0.0
if num_images > 3:
    extra_cost = (num_images - 3) * 0.15
    covered_payments = 3 * 0.15
else:
    covered_payments = num_images * 0.15
for _ in selected_stufen:
    extra_cost += 0.20
extra_cost += extra_photos_count * 0.50
if extra_cost > 0:
    st.warning(f"⚠️ Zusatzkosten: {extra_cost:.2f} €")

# ── SUBMIT ────────────────────────────────────────────────────────────────────
if st.button("Absenden"):
    if not name:
        st.error("Bitte Namen eingeben.")
        st.stop()

    data = {
        "name": name,
        "leistungskurs": lk_choice,
        "lk_typ": lk_tpy,
        "grundkurs": gk_choice,
        "gk_tpy": gk_tpy,
        "mottowoche": selected_mottos,
        "stufenfotos": selected_stufen,
        "extra_photos": extra_photos_count,
        "image_count": num_images,
        "extra_cost": extra_cost,
        "covered_payments": covered_payments,
        "paid": extra_cost == 0,
        "created_at": datetime.now().isoformat(),
    }

    response = requests.post(TABLE_URL, json=data, headers=HEADERS)

    if response.status_code in [200, 201, 204]:
        st.success("✅ Bestellung gespeichert!")
    else:
        st.error(f"❌ Fehler: {response.text}")
