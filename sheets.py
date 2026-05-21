"""
Работа с Google Таблицей: каталог товаров и FAQ.
"""

import json
import logging
from typing import Optional

import gspread
from google.oauth2.service_account import Credentials

from config import GOOGLE_CREDENTIALS_JSON, GOOGLE_SHEET_ID, SHEET_CATALOG, SHEET_FAQ

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


def _get_or_create(title: str, headers: list):
    ss = _get_spreadsheet()
    try:
        ws = ss.worksheet(title)
    except gspread.WorksheetNotFound:
        ws = ss.add_worksheet(title=title, rows=200, cols=len(headers))
        ws.append_row(headers, value_input_option="USER_ENTERED")
        return ws
    if not ws.row_values(1):
        ws.append_row(headers, value_input_option="USER_ENTERED")
    return ws


def get_product(article: str) -> Optional[dict]:
    ws = _get_or_create(SHEET_CATALOG, ["Артикул", "Название", "Материал", "Уход"])
    rows = ws.get_all_records()
    article = str(article).strip()
    for row in rows:
        if str(row.get("Артикул", "")).strip() == article:
            return {
                "article":  article,
                "name":     str(row.get("Название", "")).strip(),
                "material": str(row.get("Материал", "")).strip(),
                "care":     str(row.get("Уход", "")).strip(),
            }
    return None


def get_faq() -> list:
    ws = _get_or_create(SHEET_FAQ, ["Вопрос", "Ответ"])
    rows = ws.get_all_records()
    items = []
    for row in rows:
        q = str(row.get("Вопрос", "")).strip()
        a = str(row.get("Ответ", "")).strip()
        if q and a:
            items.append({"q": q, "a": a})
    return items
