import streamlit as st
import requests
from collections import defaultdict

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_ANON_KEY"]
TABLE_URL = f"{SUPABASE_URL}/rest/v1/orders"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
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

# Minimal CSS — only for badges, which have no native equivalent
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

st.set_page_config(page_title="📋 Bestellungen", layout="wide")
st.markdown(BADGE_CSS, unsafe_allow_html=True)

# ── DATA FETCH ────────────────────────────────────────────────────────────────


@st.cache_data(ttl=30)
def fetch_orders():
    resp = requests.get(
        TABLE_URL,
        headers={**HEADERS, "Prefer": ""},
        params={"select": "*", "order": "created_at.asc"}
    )
    if resp.status_code == 200:
        return resp.json()
    return []


def update_payment(order_id, paid: bool):
    resp = requests.patch(
        f"{TABLE_URL}?id=eq.{order_id}",
        json={"paid": paid},
        headers=HEADERS
    )
    return resp.status_code in [200, 201, 204]


st.button("Daten aktualisieren", on_click=lambda: st.cache_data.clear())

orders = fetch_orders()

# ── AUTO-PATCH free orders ────────────────────────────────────────────────────
for o in orders:
    extra = o.get("extra_cost", 0) or 0
    if extra == 0 and not o.get("paid", False):
        update_payment(o["id"], True)

orders = fetch_orders()

# ── BUILD PICTURE INDEX ───────────────────────────────────────────────────────
picture_map = defaultdict(list)

for o in orders:
    name = o.get("name", "?")
    is_paid = o.get("paid", False) or (o.get("extra_cost") or 0) == 0
    lk = o.get("leistungskurs", "")
    gk = o.get("grundkurs", "")
    lk_typ = o.get("lk_typ") or []
    gk_tpy = o.get("gk_tpy") or []
    mottos = o.get("mottowoche") or []
    stufen = o.get("stufenfotos") or []
    extra_photos = o.get("extra_photos", 0) or 0

    for t in lk_typ:
        picture_map[f"{lk} - {t}"].append((name, is_paid))
    for t in gk_tpy:
        picture_map[f"{gk} - {t}"].append((name, is_paid))
    for m in mottos:
        label = MOTTO_LABELS.get(m, f"Motto {m}")
        picture_map[f"Mottowoche: {label}"].append((name, is_paid))
    for s in stufen:
        label = STUFEN_LABELS.get(s, f"Stufen {s}")
        picture_map[f"Stufenfoto: {label}"].append((name, is_paid))
    if extra_photos > 0:
        picture_map["Zusatzfotos"].append(
            (f"{name} (x{extra_photos})", is_paid))

# ── PAGE HEADER ───────────────────────────────────────────────────────────────
st.markdown("## 📋 Admin Dashboard - Fotobestellungen")
st.caption(f"{len(orders)} Bestellungen gesamt")

tab1, tab2 = st.tabs(["📸 Bildübersicht", "💶 Zahlungen"])

# ═══════════════════════════════════════════════════════════════════
# TAB 1 — PICTURE OVERVIEW
# ═══════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("### Gesamtanzahl pro Bild")
    st.caption(
        "Klicke auf ein Bild um zu sehen, wer es bestellt hat. 🔴 = noch nicht bezahlt")

    if not picture_map:
        st.info("Noch keine Bestellungen vorhanden.")
    else:
        sorted_pics = sorted(picture_map.items(), key=lambda x: -len(x[1]))

        for label, entries in sorted_pics:
            with st.expander(f"**{label}** — {len(entries)} Stück"):
                st.write("**Bestellungen von:**")
                # Paid and unpaid names as separate pill groups
                paid_names = [n for n, paid in entries if paid]
                unpaid_names = [n for n, paid in entries if not paid]
                if paid_names:
                    st.pills("✅ Bezahlt", paid_names,
                             disabled=True, key=f"paid_{label}")
                if unpaid_names:
                    st.pills("🔴 Ausstehend", unpaid_names,
                             disabled=True, key=f"unpaid_{label}")

# ═══════════════════════════════════════════════════════════════════
# TAB 2 — PAYMENTS
# ═══════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("### Zahlungsstatus")

    total_outstanding = sum(
        (o.get("extra_cost") or 0)
        for o in orders
        if not o.get("paid", False) and (o.get("extra_cost") or 0) > 0
    )
    num_paid = sum(1 for o in orders if o.get("paid", False)
                   or (o.get("extra_cost") or 0) == 0)
    num_unpaid = len(orders) - num_paid
    # covered_payments comes from the last order iterated above — keep same logic as original
    covered_payments = sum(o.get("covered_payments", 0) or 0 for o in orders)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Bezahlt / Gratis",        num_paid)
    c2.metric("Ausstehend",              num_unpaid)
    c3.metric("Offen gesamt",            f"{total_outstanding:.2f} €")
    c4.metric("Wird von Kasse gezahlt",  f"{covered_payments:.2f} €")

    st.divider()

    filter_col, _ = st.columns([2, 3])
    with filter_col:
        show_filter = st.selectbox(
            "Anzeigen", ["Alle", "Nur Ausstehende", "Nur Bezahlte"])

    for o in orders:
        extra = o.get("extra_cost") or 0
        is_free = extra == 0
        is_paid = o.get("paid", False) or is_free
        order_id = o.get("id")
        name = o.get("name", "?")

        if show_filter == "Nur Ausstehende" and is_paid:
            continue
        if show_filter == "Nur Bezahlte" and not is_paid:
            continue

        lk = o.get("leistungskurs", "")
        gk = o.get("grundkurs", "")
        lk_typ = o.get("lk_typ") or []
        gk_tpy = o.get("gk_tpy") or []
        mottos = o.get("mottowoche") or []
        stufen = o.get("stufenfotos") or []
        extra_photos = o.get("extra_photos", 0) or 0
        img_count = o.get("image_count", 0)

        all_pics = []
        for t in lk_typ:
            all_pics.append(f"{lk} {t}")
        for t in gk_tpy:
            all_pics.append(f"{gk} {t}")
        for m in mottos:
            all_pics.append(MOTTO_LABELS.get(m, f"Motto {m}"))
        for s in stufen:
            all_pics.append(STUFEN_LABELS.get(s, f"Stufen {s}"))
        if extra_photos > 0:
            all_pics.append(f"{extra_photos}x Zusatzfoto")

        if is_free:
            badge = '<span class="free-badge">GRATIS</span>'
        elif is_paid:
            badge = '<span class="paid-badge">✓ BEZAHLT</span>'
        else:
            badge = f'<span class="unpaid-badge">⏳ {extra:.2f} €</span>'

        with st.expander(f"{name}  ·  {img_count} Bilder"):
            st.write("**Bilder:** " + " · ".join(all_pics))
            st.markdown(badge, unsafe_allow_html=True)
            st.write("")

            if not is_free:
                if is_paid:
                    if st.button("Als unbezahlt markieren", key=f"unpay_{order_id}"):
                        update_payment(order_id, False)
                        st.cache_data.clear()
                        st.rerun()
                else:
                    col_a, _ = st.columns([2, 3])
                    with col_a:
                        if st.button(f"✅ Als bezahlt markieren ({extra:.2f} €)", key=f"pay_{order_id}"):
                            update_payment(order_id, True)
                            st.cache_data.clear()
                            st.rerun()
            else:
                st.caption(
                    "Keine Zusatzkosten - automatisch als bezahlt markiert.")
