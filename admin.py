import streamlit as st
import requests
from collections import defaultdict

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_ANON_KEY"]
ORDERS_URL = f"{SUPABASE_URL}/rest/v1/orders"
IMAGES_URL = f"{SUPABASE_URL}/rest/v1/order_images"

BASE_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}

MOTTO_LABELS = {
    1: "Mo - Mafia",
    2: "Di - Gender Swap",
    3: "Mi - Kindheitshelden",
    4: "Do - Straight out of Bed",
    5: "Fr - Gruppenkostüm",
}

STUFEN_LABELS = {
    1: "Pausenhof",
    2: "Abau Treppe",
}

BADGE_CSS = """
<style>
.paid-badge {
    background: #0d3b2e; border: 1px solid #1a7a5a; color: #4dffa6;
    border-radius: 4px; padding: 2px 8px; font-size: 0.75rem; font-weight: 600;
}
.unpaid-badge {
    background: #3b1a1a; border: 1px solid #7a3030; color: #ff7070;
    border-radius: 4px; padding: 2px 8px; font-size: 0.75rem; font-weight: 600;
}
.free-badge {
    background: #1a2a3b; border: 1px solid #3a6a9a; color: #70c0ff;
    border-radius: 4px; padding: 2px 8px; font-size: 0.75rem; font-weight: 600;
}
</style>
"""

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


def update_payment(order_id, paid: bool):
    resp = requests.patch(
        f"{ORDERS_URL}?id=eq.{order_id}",
        json={"paid": paid},
        headers={**BASE_HEADERS, "Prefer": "return=minimal"}
    )
    return resp.status_code in [200, 201, 204]


def build_image_map(images):
    """Returns dict of order_id -> list of image URLs sorted by position."""
    img_map = defaultdict(list)
    for img in sorted(images, key=lambda x: x.get("position") or 0):
        img_map[img["order_id"]].append(img["url"])
    return img_map


st.button("🔄 Daten aktualisieren", on_click=lambda: st.cache_data.clear())

orders = fetch_orders()
images = fetch_images()
image_map = build_image_map(images)

# ── AUTO-PATCH free orders ────────────────────────────────────────────────────
for o in orders:
    if (o.get("extra_cost") or 0) == 0 and not o.get("paid", False):
        update_payment(o["id"], True)

orders = fetch_orders()

# ── BUILD PICTURE INDEX ───────────────────────────────────────────────────────
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

# ── PAGE HEADER ───────────────────────────────────────────────────────────────
st.markdown("## Bestellungsverwaltung")
st.caption(f"{len(orders)} Bestellungen gesamt")

tab1, tab2, tab3 = st.tabs(
    ["📸 Bildübersicht", "💶 Zahlungen", "🖼️ Uploads"])

# ═══════════════════════════════════════════════════════════════════
# TAB 1 — PICTURE OVERVIEW
# ═══════════════════════════════════════════════════════════════════
with tab1:
    if not picture_map:
        st.info("Noch keine Bestellungen vorhanden.")
    else:
        sorted_pics = sorted(picture_map.items(), key=lambda x: -len(x[1]))

        for label, entries in sorted_pics:
            with st.expander(f"**{label}** — {len(entries)} Stück"):
                st.markdown("**Bestellungen von:**")
                tags = "".join(
                    f'<span class="person-tag" style="background:#3b1a1a;border-color:#7a3030;color:#ff7070">{n}</span>'
                    if not paid else
                    f'<span class="person-tag">{n}</span>'
                    for n, paid in entries
                )
                st.markdown(tags, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════
# TAB 2 — PAYMENTS
# ════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("### Zahlungsstatus")

    total_outstanding = sum(
        (o.get("extra_cost") or 0) for o in orders
        if not o.get("paid", False) and (o.get("extra_cost") or 0) > 0
    )
    num_paid = sum(1 for o in orders if o.get("paid", False)
                   or (o.get("extra_cost") or 0) == 0)
    covered_payments = sum(o.get("covered_payments", 0) or 0 for o in orders)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Bezahlt / Gratis", num_paid)
    c2.metric("Ausstehend", len(orders) - num_paid)
    c3.metric("Offen gesamt", f"{total_outstanding:.2f} €")
    c4.metric("Wird von Kasse gezahlt", f"{covered_payments:.2f} €")

    st.divider()

    show_filter = st.selectbox(
        "Anzeigen", ["Alle", "Nur Ausstehende", "Nur Bezahlte"])

    for o in orders:
        extra = o.get("extra_cost") or 0
        is_free = extra == 0
        is_paid = o.get("paid", False) or is_free
        order_id = o["id"]
        name = o.get("name", "?")

        if show_filter == "Nur Ausstehende" and is_paid:
            continue
        if show_filter == "Nur Bezahlte" and not is_paid:
            continue

        lk_typ = o.get("lk_typ") or []
        gk_tpy = o.get("gk_tpy") or []
        all_pics = (
            [f"{o.get('leistungskurs', '')} {t}" for t in lk_typ] +
            [f"{o.get('grundkurs', '')} {t}" for t in gk_tpy] +
            [MOTTO_LABELS.get(m, f"Motto {m}") for m in (o.get("mottowoche") or [])] +
            [STUFEN_LABELS.get(s, f"Stufen {s}")
             for s in (o.get("stufenfotos") or [])]
        )
        extra_photos = o.get("extra_photos", 0) or 0
        if extra_photos > 0:
            all_pics.append(f"{extra_photos}x Zusatzfoto")

        badge = (
            '<span class="free-badge">GRATIS</span>' if is_free else
            '<span class="paid-badge">✓ BEZAHLT</span>' if is_paid else
            f'<span class="unpaid-badge">⏳ {extra:.2f} €</span>'
        )

        with st.expander(f"{name}  ·  {o.get('image_count', 0)} Bilder"):
            st.write("**Bilder:** " + " · ".join(all_pics))
            st.markdown(badge, unsafe_allow_html=True)

            # Show uploaded images inline
            order_imgs = image_map.get(order_id, [])
            if order_imgs:
                st.write("**Hochgeladene Fotos:**")
                img_cols = st.columns(min(len(order_imgs), 4))
                for i, url in enumerate(order_imgs):
                    img_cols[i % 4].image(url)

            st.write("")
            if not is_free:
                if is_paid:
                    if st.button("Als unbezahlt markieren", key=f"unpay_{order_id}"):
                        update_payment(order_id, False)
                        st.cache_data.clear()
                        st.rerun()
                else:
                    if st.button(f"✅ Als bezahlt markieren ({extra:.2f} €)", key=f"pay_{order_id}"):
                        update_payment(order_id, True)
                        st.cache_data.clear()
                        st.rerun()
            else:
                st.caption(
                    "Keine Zusatzkosten - automatisch als bezahlt markiert.")

# ═══════════════════════════════════════════════════════════════════
# TAB 3 — UPLOADS (all images in a gallery)
# ═══════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("### Alle hochgeladenen Fotos")

    order_lookup = {o["id"]: o.get("name", "?") for o in orders}
    all_uploads = [(img["url"], order_lookup.get(img["order_id"], "?"), img.get("position", 0))
                   for img in images]

    if not all_uploads:
        st.info("Noch keine Fotos hochgeladen.")
    else:
        st.caption(f"{len(all_uploads)} Fotos insgesamt")
        cols = st.columns(4)
        for i, (url, name, pos) in enumerate(all_uploads):
            with cols[i % 4]:
                st.image(url)
                st.caption(f"{name} · #{pos}")
