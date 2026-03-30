import streamlit as st
import requests
from constants import ORDERS_URL, BASE_HEADERS

CONFIG_URL = ORDERS_URL.replace("/orders", "/config")


@st.cache_data(ttl=60)
def load_config():
    resp = requests.get(
        CONFIG_URL,
        headers=BASE_HEADERS,
        params={"select": "key,value"}
    )
    raw = resp.json() if resp.status_code == 200 else []
    data = {row["key"]: row["value"] for row in raw}
    return {
        "MAX_IMAGES": int(data.get("MAX_IMAGES", 20)),
        "NORMAL_IMAGE_PRICE": float(data.get("NORMAL_IMAGE_PRICE", 0.25)),
        "NORMAL_IMAGE_PRICE_THAT_ABIKASSE_PAYS": float(data.get("NORMAL_IMAGE_PRICE_THAT_ABIKASSE_PAYS", 0.25)),
        "UPLOAD_PHOTO_PRICE": float(data.get("UPLOAD_PHOTO_PRICE", 0.49)),
        "AMOUNT_OF_FREE_IMAGES": int(data.get("AMOUNT_OF_FREE_IMAGES", 2)),
    }


_config = load_config()
MAX_IMAGES = _config["MAX_IMAGES"]
NORMAL_IMAGE_PRICE = _config["NORMAL_IMAGE_PRICE"]
NORMAL_IMAGE_PRICE_THAT_ABIKASSE_PAYS = _config["NORMAL_IMAGE_PRICE_THAT_ABIKASSE_PAYS"]
UPLOAD_PHOTO_PRICE = _config["UPLOAD_PHOTO_PRICE"]
AMOUNT_OF_FREE_IMAGES = _config["AMOUNT_OF_FREE_IMAGES"]
