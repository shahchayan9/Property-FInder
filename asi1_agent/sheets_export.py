"""
Export listing results to a new Google Sheet and return a shareable link.
Requires GOOGLE_APPLICATION_CREDENTIALS (path to service account JSON) and
optionally GOOGLE_SHEETS_EXPORT_PAGE_SIZE (default 50).
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

try:
    import gspread
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
except ImportError:
    gspread = None
    Credentials = None
    build = None


_SHEETS_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

_HEADERS = [
    "Address",
    "Price",
    "Beds",
    "Baths",
    "Sqft",
    "Property Type",
    "Year Built",
    "Days on Market",
    "Neighborhood",
    "MLS",
    "Photo URL",
    "Description",
]


def _row_from_listing(listing: dict[str, Any]) -> list[Any]:
    def _str(v: Any) -> str:
        if v is None:
            return ""
        if isinstance(v, (list, dict)):
            return str(v)
        return str(v).strip()

    def _num(v: Any) -> str:
        if v is None:
            return ""
        try:
            return str(int(float(v)))
        except (TypeError, ValueError):
            return _str(v)

    desc = listing.get("description") or ""
    if isinstance(desc, str) and len(desc) > 500:
        desc = desc[:497] + "…"
    return [
        _str(listing.get("address")),
        _num(listing.get("price")),
        _num(listing.get("beds")),
        _num(listing.get("baths")),
        _num(listing.get("sqft")),
        _str(listing.get("property_type")),
        _num(listing.get("year_built")),
        _num(listing.get("days_on_market")),
        _str(listing.get("neighborhood")),
        _str(listing.get("mls")),
        _str(listing.get("image_url")),
        _str(desc),
    ]


def get_listings_table(listings: list[dict[str, Any]]) -> tuple[list[str], list[list[Any]]]:
    """Return (headers, rows) for the given listings, same format used when writing to a sheet."""
    if not listings:
        return (list(_HEADERS), [])
    return (list(_HEADERS), [_row_from_listing(lst) for lst in listings])


def write_listings_to_sheet(
    listings: list[dict[str, Any]],
    search_summary: str = "Property search",
) -> str | None:
    """
    Create a new Google Sheet, write all listings, share as "anyone with link can view",
    and return the sheet URL. Returns None if credentials are missing or an error occurs.
    """
    if not listings:
        return None
    if gspread is None or Credentials is None or build is None:
        return None

    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or os.getenv(
        "GOOGLE_SHEETS_CREDENTIALS_PATH"
    )
    if not creds_path or not os.path.isfile(creds_path):
        return None

    try:
        creds = Credentials.from_service_account_file(creds_path, scopes=_SHEETS_SCOPES)
        gc = gspread.authorize(creds)

        title = f"Property Finder – {search_summary} – {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
        spreadsheet = gc.create(title)

        sheet = spreadsheet.sheet1
        sheet.update("A1:L1", [_HEADERS])
        rows = [_row_from_listing(lst) for lst in listings]
        if rows:
            sheet.update(f"A2:L{1 + len(rows)}", rows)

        # Share with "anyone with link can view" via Drive API
        drive = build("drive", "v3", credentials=creds)
        drive.permissions().create(
            fileId=spreadsheet.id,
            body={"type": "anyone", "role": "reader"},
            supportsAllDrives=True,
        ).execute()

        return spreadsheet.url
    except Exception:
        return None


def create_simple_sheet(title: str, rows: list[list[Any]]) -> str | None:
    """
    Create a new Google Sheet with the given title and rows (list of lists),
    share as "anyone with link can view", and return the sheet URL.
    Used for ad-hoc requests like "create a sheet and add my name Chayan Shah".
    """
    if gspread is None or Credentials is None or build is None:
        return None

    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or os.getenv(
        "GOOGLE_SHEETS_CREDENTIALS_PATH"
    )
    if not creds_path or not os.path.isfile(creds_path):
        return None

    if not rows:
        rows = [["(empty)"]]

    try:
        creds = Credentials.from_service_account_file(creds_path, scopes=_SHEETS_SCOPES)
        gc = gspread.authorize(creds)
        spreadsheet = gc.create(title)
        sheet = spreadsheet.sheet1
        sheet.update("A1", rows)
        drive = build("drive", "v3", credentials=creds)
        drive.permissions().create(
            fileId=spreadsheet.id,
            body={"type": "anyone", "role": "reader"},
            supportsAllDrives=True,
        ).execute()
        return spreadsheet.url
    except Exception:
        return None
