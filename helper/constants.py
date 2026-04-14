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


BASE_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
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


PREVIEW_IMAGES = {
    "lk": {
        "Englisch": {
            "Normalbild": "https://arhkqltxvrrkpkyxyfoe.supabase.co/storage/v1/object/public/images/Freitag.jpeg",
            "Spaßbild": "https://arhkqltxvrrkpkyxyfoe.supabase.co/storage/v1/object/public/images/Freitag.jpeg"
        },
        "Geschichte": {
            "Normalbild": "https://arhkqltxvrrkpkyxyfoe.supabase.co/storage/v1/object/public/images/Freitag.jpeg",
            "Spaßbild": "https://arhkqltxvrrkpkyxyfoe.supabase.co/storage/v1/object/public/images/Freitag.jpeg"
        },
        "Geo": {
            "Normalbild": "https://arhkqltxvrrkpkyxyfoe.supabase.co/storage/v1/object/public/images/Freitag.jpeg",
            "Spaßbild": "https://arhkqltxvrrkpkyxyfoe.supabase.co/storage/v1/object/public/images/Freitag.jpeg"
        },
        "Sport": {
            "Normalbild": "https://arhkqltxvrrkpkyxyfoe.supabase.co/storage/v1/object/public/images/Freitag.jpeg",
            "Spaßbild": "https://arhkqltxvrrkpkyxyfoe.supabase.co/storage/v1/object/public/images/Freitag.jpeg"
        },
        "Kunst": {
            "Normalbild": "https://arhkqltxvrrkpkyxyfoe.supabase.co/storage/v1/object/public/images/Freitag.jpeg",
            "Spaßbild": "https://arhkqltxvrrkpkyxyfoe.supabase.co/storage/v1/object/public/images/Freitag.jpeg"
        },
        "Französisch": {
            "Normalbild": "https://arhkqltxvrrkpkyxyfoe.supabase.co/storage/v1/object/public/images/Freitag.jpeg",
            "Spaßbild": "https://arhkqltxvrrkpkyxyfoe.supabase.co/storage/v1/object/public/images/Freitag.jpeg"
        },
        "Physik": {
            "Normalbild": "https://arhkqltxvrrkpkyxyfoe.supabase.co/storage/v1/object/public/images/Freitag.jpeg",
            "Spaßbild": "https://arhkqltxvrrkpkyxyfoe.supabase.co/storage/v1/object/public/images/Freitag.jpeg"
        }
    },
    "gk": {
        "Grundkurs 1": {
            "Normalbild": "https://arhkqltxvrrkpkyxyfoe.supabase.co/storage/v1/object/public/images/Freitag.jpeg",
            "Spaßbild": "https://arhkqltxvrrkpkyxyfoe.supabase.co/storage/v1/object/public/images/Freitag.jpeg"
        },
        "Grundkurs 2": {
            "Normalbild": "https://arhkqltxvrrkpkyxyfoe.supabase.co/storage/v1/object/public/images/Freitag.jpeg",
            "Spaßbild": "https://arhkqltxvrrkpkyxyfoe.supabase.co/storage/v1/object/public/images/Freitag.jpeg"
        },
        "Grundkurs 3": {
            "Normalbild": "https://arhkqltxvrrkpkyxyfoe.supabase.co/storage/v1/object/public/images/Freitag.jpeg",
            "Spaßbild": "https://arhkqltxvrrkpkyxyfoe.supabase.co/storage/v1/object/public/images/Freitag.jpeg"
        },
        "Grundkurs 4": {
            "Normalbild": "https://arhkqltxvrrkpkyxyfoe.supabase.co/storage/v1/object/public/images/Freitag.jpeg",
            "Spaßbild": "https://arhkqltxvrrkpkyxyfoe.supabase.co/storage/v1/object/public/images/Freitag.jpeg"
        }
    },
    "mottowoche": {
        1: "https://arhkqltxvrrkpkyxyfoe.supabase.co/storage/v1/object/public/images/Freitag.jpeg",
        2: "https://arhkqltxvrrkpkyxyfoe.supabase.co/storage/v1/object/public/images/Freitag.jpeg",
        3: "https://arhkqltxvrrkpkyxyfoe.supabase.co/storage/v1/object/public/images/Freitag.jpeg",
        4: "https://arhkqltxvrrkpkyxyfoe.supabase.co/storage/v1/object/public/images/Freitag.jpeg",
        5: "https://arhkqltxvrrkpkyxyfoe.supabase.co/storage/v1/object/public/images/Freitag.jpeg"
    },
    "stufenfotos": {
        1: "https://arhkqltxvrrkpkyxyfoe.supabase.co/storage/v1/object/public/images/Freitag.jpeg",
        2: "https://arhkqltxvrrkpkyxyfoe.supabase.co/storage/v1/object/public/images/Freitag.jpeg"
    }
}
