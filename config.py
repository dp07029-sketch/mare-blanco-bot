"""
Настройки и константы бота Mare Blanco.
"""

import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "")
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON", "")

SHEET_CATALOG = "Каталог"
SHEET_FAQ = "FAQ"

SIZE_CHART = [
    {"size": "XS", "chest": (78, 82),   "waist": (60, 64),  "height": (150, 165)},
    {"size": "S",  "chest": (84, 88),   "waist": (66, 70),  "height": (155, 170)},
    {"size": "M",  "chest": (90, 94),   "waist": (72, 76),  "height": (160, 175)},
    {"size": "L",  "chest": (96, 100),  "waist": (78, 82),  "height": (165, 180)},
    {"size": "XL", "chest": (102, 106), "waist": (84, 88),  "height": (170, 185)},
]

AVAILABLE_SIZES = ["S", "M", "L", "XL"]
