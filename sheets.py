"""
Работа с Google Таблицей: каталог товаров (поиск инструкции по уходу по артикулу).
"""

import json
import logging
from typing import Optional

import gspread
from google.oauth2.service_account import Credentials

from config import GOOGLE_CREDENTIALS_JSON, GOOGLE_SHEET_ID, SHEET_CATALOG

logger = logging.getLogger(__name__)

_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

_spreadsheet = None


def _get_spreadsheet():
    global _spreadsheet
    if _spreadsheet is None:
        creds_info = json.loads(GOOGLE_CREDENTIALS_JSON)
        creds = Credentials.from_service_account_info(creds_info, scopes=_SCOPES)
        client = gspread.authorize(creds)
        _spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)
    return _spreadsheet


def _get_catalog_sheet():
    ss = _get_spreadsheet()
    headers = ["Артикул", "Название", "Материал", "Уход"]
    try:
        ws = ss.worksheet(SHEET_CATALOG)
    except gspread.WorksheetNotFound:
        ws = ss.add_worksheet(title=SHEET_CATALOG, rows=1000, cols=len(headers))
        ws.append_row(headers, value_input_option="USER_ENTERED")
        return ws
    if not ws.row_values(1):
        ws.append_row(headers, value_input_option="USER_ENTERED")
    return ws


def get_product(article: str) -> Optional[dict]:
    """Ищет товар по артикулу в листе 'Каталог'. Возвращает dict или None."""
    ws = _get_catalog_sheet()
    rows = ws.get_all_records()
    article = str(article).strip()
    for row in rows:
        if str(row.get("Артикул", "")).strip() == article:
            return {
                "article": article,
                "name": str(row.get("Название", "")).strip(),
                "material": str(row.get("Материал", "")).strip(),
                "care": str(row.get("Уход", "")).strip(),
            }
    return None
