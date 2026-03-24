"""
Fetch all Repliers listings matching the given filters and create a Google Sheet.
Uses the same Repliers API as the Property-FInder chat agent so results always match.
No HomeHarvest scraping — single source of truth.
"""
import asyncio
import os
import sys
from pathlib import Path
from typing import Any

import pandas as pd

# Make sure repliers_client (which lives in Property-FInder/) is importable
_dir = Path(__file__).resolve().parent          # real_estate_agent/
_project_root = _dir.parent                     # Property-FInder/
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from repliers_client.client import search_listings as _repliers_search
from real_estate_agent.sheets import GoogleAuthRequiredError, create_listings_sheet


def _listings_to_dataframe(listings: list[dict[str, Any]]) -> pd.DataFrame:
    """Convert simplified Repliers listing dicts to a DataFrame for Google Sheets."""
    rows = []
    for lst in listings:
        rows.append({
            "MLS Number": lst.get("mls", ""),
            "Address": lst.get("address", ""),
            "Price ($)": lst.get("price"),
            "Beds": lst.get("beds"),
            "Baths": lst.get("baths"),
            "Size (sqft)": lst.get("sqft"),
            "Year Built": lst.get("year_built"),
            "Property Type": lst.get("property_type", ""),
            "Neighborhood": lst.get("neighborhood", ""),
            "Days on Market": lst.get("days_on_market"),
            "Description": (lst.get("description") or "")[:500],
        })
    return pd.DataFrame(rows)


async def run_report_workflow(
    filters: dict[str, Any],
    user_id: str = "report_agent",
) -> dict[str, Any]:
    """
    Fetch up to 50 Repliers listings matching filters, export to Google Sheet.

    Returns a dict:
        sheet_url  — public Google Sheet URL (empty string on failure)
        count      — number of listings in the sheet
        location   — location string from filters
        error      — non-empty string if something went wrong
    """
    location = filters.get("location", "Unknown")
    deal_type = filters.get("deal_type", "buy")
    listing_type = "for_rent" if deal_type == "rent" else "for_sale"

    try:
        # Reset to page 1 for a full export (user may have been on page 3 in chat)
        report_filters = dict(filters)
        report_filters["page"] = 1

        # export_page_size=50 fetches up to 50 listings from the API
        _, meta = await asyncio.to_thread(_repliers_search, report_filters, 50)
        all_listings: list[dict[str, Any]] = meta.get("all_listings", [])
        count = len(all_listings)

        if not all_listings:
            return {
                "sheet_url": "",
                "count": 0,
                "location": location,
                "error": "No listings found matching your criteria.",
            }

        df = _listings_to_dataframe(all_listings)
        sheet_user_id = os.getenv("GOOGLE_SHEET_USER_ID", user_id)

        sheet_url = await asyncio.to_thread(
            create_listings_sheet, df, location, listing_type, sheet_user_id
        )

        return {
            "sheet_url": sheet_url,
            "count": count,
            "location": location,
            "error": "",
        }

    except GoogleAuthRequiredError as exc:
        return {
            "sheet_url": "",
            "count": 0,
            "location": location,
            "error": (
                "Google Sheets is not yet authorized. Complete OAuth setup first. "
                f"Details: {exc}"
            ),
        }
    except Exception as exc:
        return {
            "sheet_url": "",
            "count": 0,
            "location": location,
            "error": str(exc),
        }
