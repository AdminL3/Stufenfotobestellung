import os
import streamlit as st
LK_OPTIONS = ["Englisch", "Geschichte", "Geo",
              "Sport", "Kunst", "Französisch", "Physik"]
GK_OPTIONS = ["Grundkurs 1", "Grundkurs 2", "Grundkurs 3", "Grundkurs 4"]

MOTTO_LABELS = {
    1: "Mafia",
    2: "Gender Swap",
    3: "Kindheitshelden",
    4: "Straight out of Bed",
    5: "Gruppenkostüm",
}

STUFEN_LABELS = {
    1: "Pausenhof",
    2: "Abau Treppe",
    3: "Abau Spaßbild",
}

BUCKET_NAME = "images"

SUPABASE_URL = os.environ.get("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY")
ORDERS_URL = f"{SUPABASE_URL}/rest/v1/orders"
IMAGES_URL = f"{SUPABASE_URL}/rest/v1/order_images"

NAME_OPTIONS = [
    "Adam Loose",
    "Ahmed Lagha",
    "Aleksandar Kohler",
    "Aliou Kpekpassi",
    "Angelina Ross",
    "Anna Le",
    "Anna Pöpperl",
    "Anna Riemer",
    "Baton Berisha",
    "Benno Gleim",
    "Bilal Salman",
    "Bogdan Orha",
    "Cara Rosener",
    "Carolin Schwab",
    "Celine Aslan",
    "Christiana Mihaita",
    "Shrevan Daqo",
    "Denis Haziraj",
    "Ecem Sairoglu",
    "Edgar Heilmann",
    "Emanuel Sathmar",
    "Emily Sterle",
    "Emre Folkers",
    "Ferdinand Zanker",
    "Florian Leibl",
    "Carlos Frießner",
    "Helge Rummler",
    "Ipek Demir",
    "Jana Paul",
    "Johannes Hanafi",
    "Jonah Blumenwitz",
    "Jonah Thomas",
    "Jonas Erd",
    "Jonas Opitz",
    "Julian Bilz",
    "Julian Geiß",
    "Julian Widmer",
    "Julius Heienbrok",
    "Julius Henkel",
    "Katja Schmid",
    "Klara Scheidl",
    "Lars Oswald",
    "Lazara Zdravic",
    "Ledion Jashari",
    "Lekdup Ernst",
    "Len Swoboda",
    "Leon Gundel",
    "Leonard Beinlich",
    "Leonardo Manetto",
    "Levi Blumenwitz",
    "Lilly Hinmüller",
    "Loni Rottner",
    "Lorena Aliji",
    "Lorenz Sellmaier",
    "Luca Carbone",
    "Luan Jusufi",
    "Lukas Matt",
    "Luis Göhrle",
    "Marie-Sophie Mohr",
    "Marlon King",
    "Martin Matov",
    "Mathilde Hudelmaier",
    "Matthias Plabst",
    "Max Elbel",
    "Merle Beuter",
    "Mia Henschel",
    "Michelle Leiker",
    "Milo Eriksson",
    "Mubarak Arshe",
    "Nils Frör",
    "Nina Hochecker",
    "Nirosh Ganeshalingam",
    "Omar Hussein",
    "Oliver Hanich",
    "Paul Grünwald",
    "Paula Singer",
    "Rana Göksügür",
    "Rashu Nakarmi",
    "Salih Hassan",
    "Sarah Tariq",
    "Sebastian Gebert",
    "Sophie Greve",
    "Stefan Sysoltsev",
    "Tasfia Hossain",
    "Theo Keller",
    "Theo Tenkmann",
    "Tizian Marchesini",
    "Valentin Schorpp",
    "Veronika Neumaier",
    "Victor Todorov",
    "Violetta Schmieder",
    "Ylva von Küstenfeld",
    "Zeynep Sarikan",
    "Zoe Barth",
    "Zoe Lehmann"
]

SIZE_OPTIONS = ["XS", "S", "M", "L", "XL", "XXL"]

COLOR_OPTIONS = [
    "Black",
    "Stormy Gray",
    "New French Navy",
    "Purple",
    "Burgundy"
]


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

/* Person tags in Tab 1 - inline-flex fixes vertical offset */
.tag-wrap {
    display: flex; flex-wrap: wrap; gap: 6px;
    margin-top: 4px; align-items: center;
}
.tag-paid {
    display: inline-flex; align-items: center;
    background: #0d3b2e; border: 1px solid #1a7a5a; color: #4dffa6;
    border-radius: 20px; padding: 3px 12px; font-size: 0.82rem; font-weight: 500;
    line-height: 1.4;
}
.tag-unpaid {
    display: inline-flex; align-items: center;
    background: #3b1a1a; border: 1px solid #7a3030; color: #ff7070;
    border-radius: 20px; padding: 3px 12px; font-size: 0.82rem; font-weight: 500;
    line-height: 1.4;
}

/* Expander border colors for Tab 2 */
.expander-green details {
    border-left: 4px solid #1a7a5a !important;
}
.expander-blue details {
    border-left: 4px solid #3a6a9a !important;
}
.expander-red details {
    border-left: 4px solid #7a3030 !important;
}
</style>
"""

TAG_PAID = "display:flex;align-items:center;background:#0d3b2e;border:1px solid #1a7a5a;color:#4dffa6;border-radius:20px;padding:3px 12px;font-size:0.82rem;font-weight:500;line-height:1.4;margin-bottom:10px;"
TAG_UNPAID = "display:flex;align-items:center;background:#3b1a1a;border:1px solid #7a3030;color:#ff7070;border-radius:20px;padding:3px 12px;font-size:0.82rem;font-weight:500;line-height:1.4;margin-bottom:10px;"


BASE_URL = "https://arhkqltxvrrkpkyxyfoe.supabase.co/storage/v1/object/public/images/"


def img(name):
    return f"{BASE_URL}{name}.JPG"


PREVIEW_IMAGES = {
    "lk": {
        "Englisch":    {"Normalbild": img("E1"), "Spaßbild": img("E2")},
        "Geschichte":  {"Normalbild": img("Ge1"), "Spaßbild": img("Ge2")},
        "Geo":         {"Normalbild": img("G1"), "Spaßbild": img("G2")},
        "Sport":       {"Normalbild": img("S1"), "Spaßbild": img("S2")},
        "Kunst":       {"Normalbild": img("K1"), "Spaßbild": img("K2")},
        "Französisch": {"Normalbild": img("F1"), "Spaßbild": img("F2")},
        "Physik":      {"Normalbild": img("P1"), "Spaßbild": img("P2")},
    },
    "gk": {
        f"Grundkurs {i}": {"Normalbild": img(f"{i}1"), "Spaßbild": img(f"{i}2")}
        for i in range(1, 5)
    },
    "mottowoche": {
        i: img(f"M{i}") for i in range(1, 6)
    },
    "stufenfotos": {
        1: img("Pausenhof"),
        2: img("Treppe"),
        3: img("Spass"),
    }
}
