"""
Format listing objects into readable ASI1 chat text.
"""
from typing import Any


def _extract_urls(obj: Any, *, max_urls: int = 10) -> list[str]:
    """
    Best-effort extraction of URL-like strings from a nested dict/list payload.
    This helps surface listing/virtual-tour links when the MLS feed provides them.
    """
    urls: list[str] = []
    seen: set[str] = set()

    def _add(v: Any):
        if not isinstance(v, str):
            return
        s = v.strip()
        if not (s.startswith("http://") or s.startswith("https://")):
            return
        if s in seen:
            return
        seen.add(s)
        urls.append(s)

    def _walk(x: Any):
        if len(urls) >= max_urls:
            return
        if isinstance(x, dict):
            for k, v in x.items():
                # Prefer keys that look like links
                if isinstance(k, str) and "url" in k.lower():
                    _add(v)
                _walk(v)
                if len(urls) >= max_urls:
                    return
        elif isinstance(x, list):
            for it in x:
                _walk(it)
                if len(urls) >= max_urls:
                    return
        else:
            _add(x)

    _walk(obj)
    return urls


def format_listing(index: int, listing: dict[str, Any]) -> str:
    """Format a single listing for chat display with richer details."""
    address = listing.get("address") or "Address not available"
    price = listing.get("price")
    price_str = f"${price:,}" if price is not None else "Price N/A"
    beds = listing.get("beds")
    baths = listing.get("baths")
    beds_str = str(beds) if beds is not None else "?"
    baths_str = str(baths) if baths is not None else "?"
    mls = listing.get("mls") or "—"
    sqft = listing.get("sqft")
    year_built = listing.get("year_built")
    prop_type = listing.get("property_type")
    dom = listing.get("days_on_market")
    neighborhood = listing.get("neighborhood")
    image_url = listing.get("image_url")
    images = listing.get("images") or []

    # Build a compact detail line
    detail_parts: list[str] = [f"{beds_str} Beds", f"{baths_str} Baths"]
    if sqft:
        try:
            detail_parts.append(f"{int(float(sqft)):,} sqft")
        except (TypeError, ValueError):
            detail_parts.append(f"{sqft} sqft")
    if prop_type:
        detail_parts.append(str(prop_type))
    if year_built:
        detail_parts.append(f"Built {year_built}")
    if dom:
        detail_parts.append(f"{dom} days on market")
    detail_line = " | ".join(detail_parts)

    # Short description snippet if available
    desc = listing.get("description") or ""
    desc_snippet = ""
    if isinstance(desc, str) and desc.strip():
        snippet = desc.strip().replace("\n", " ")
        max_len = 160
        if len(snippet) > max_len:
            snippet = snippet[: max_len - 1].rstrip() + "…"
        desc_snippet = f"\n   {snippet}"

    # Neighborhood / area line
    neighborhood_line = ""
    if neighborhood:
        neighborhood_line = f"\n   Neighborhood: {neighborhood}"

    # Image line (render markdown image embeds so ASI1 can show inline images)
    image_line = ""
    if isinstance(images, list) and images:
        # Show up to 3 images in the main card; "details N" has the rest
        show = images[:3]
        photo_lines = [f"   Photo {i + 1}:\n   ![Listing {index} Photo {i + 1}]({url})" for i, url in enumerate(show)]
        image_line = "\n" + "\n".join(photo_lines)
        if len(images) > 3:
            image_line += f"\n   (+{len(images) - 3} more — say \"details {index}\" for all)"
    elif image_url:
        image_line = f"\n   Photo:\n   ![Listing {index} Photo]({image_url})"

    return (
        f"### Listing {index}\n"
        f"**{address}**\n"
        f"**Price:** {price_str}\n"
        f"**Specs:** {detail_line}"
        f"{desc_snippet}"
        f"{neighborhood_line}"
        f"{image_line}\n"
        f"**MLS:** `{mls}`"
    )


def format_listing_details(listing: dict[str, Any], index: int | None = None) -> str:
    """
    More verbose detail view for a single listing.
    Shows all key specs and multiple photos.
    """
    # Reuse summary card and add a details heading
    header = f"## Full Details\n\n{format_listing(index or 1, listing)}"

    # Additional photos (main card shows first 3; here show the rest)
    images = listing.get("images") or []
    photos_block = ""
    if isinstance(images, list) and len(images) > 3:
        extra = images[3:]
        photos_block = (
            "\n\n**More photos:**\n"
            + "\n\n".join(
                f"   Photo {i + 4}:\n   ![Listing {index or 1} Photo {i + 4}]({url})"
                for i, url in enumerate(extra)
            )
        )

    # For now we don't have reviews data from MLS, so we omit that section.
    return header + photos_block


def _format_extra_details(raw: dict[str, Any]) -> str:
    """
    Build a richer details block from the raw Repliers listing object.
    We keep it compact but expose the most useful extra fields.
    """
    parts: list[str] = []

    status = raw.get("status")
    last_status = raw.get("lastStatus")
    list_date = raw.get("listDate")
    original_price = raw.get("originalPrice")
    sold_price = raw.get("soldPrice")
    sold_date = raw.get("soldDate")
    photo_count = raw.get("photoCount")

    details = raw.get("details") or {}
    if not isinstance(details, dict):
        details = {}

    lot = raw.get("lot") or {}
    if not isinstance(lot, dict):
        lot = {}

    taxes = raw.get("taxes") or {}
    if not isinstance(taxes, dict):
        taxes = {}

    nearby = raw.get("nearby") or {}
    if not isinstance(nearby, dict):
        nearby = {}

    open_houses = raw.get("openHouse") or []
    if not isinstance(open_houses, list):
        open_houses = []

    condo = raw.get("condominium") or {}
    if not isinstance(condo, dict):
        condo = {}

    occup = raw.get("occupancy")

    # High-level listing lifecycle
    lifecycle_lines: list[str] = []
    if status:
        lifecycle_lines.append(f"Status: {status}")
    if last_status:
        lifecycle_lines.append(f"Last status: {last_status}")
    if list_date:
        lifecycle_lines.append(f"Listed on: {list_date}")
    if original_price:
        lifecycle_lines.append(f"Original price: ${original_price:,}" if isinstance(original_price, (int, float)) else f"Original price: {original_price}")
    if sold_price:
        sold_str = f"${sold_price:,}" if isinstance(sold_price, (int, float)) else str(sold_price)
        lifecycle_lines.append(f"Sold price: {sold_str}")
    if sold_date:
        lifecycle_lines.append(f"Sold date: {sold_date}")
    if photo_count:
        lifecycle_lines.append(f"Photo count: {photo_count}")
    if occup:
        lifecycle_lines.append(f"Occupancy: {occup}")
    if lifecycle_lines:
        parts.append("### Status & history")
        parts.append("  " + "\n  ".join(lifecycle_lines))

    # Property details
    detail_lines: list[str] = []
    style = details.get("style")
    heating = details.get("heating")
    ac = details.get("airConditioning")
    fireplace = details.get("numFireplaces")
    garages = details.get("numGarageSpaces")
    parking = details.get("numParkingSpaces")
    flooring = details.get("flooringType")
    pool = details.get("swimmingPool")
    water = details.get("waterSource")
    sewer = details.get("sewer")

    if style:
        detail_lines.append(f"Style: {style}")
    if heating:
        detail_lines.append(f"Heating: {heating}")
    if ac:
        detail_lines.append(f"Cooling: {ac}")
    if fireplace:
        detail_lines.append(f"Fireplaces: {fireplace}")
    if garages:
        detail_lines.append(f"Garage spaces: {garages}")
    if parking:
        detail_lines.append(f"Parking spaces: {parking}")
    if flooring:
        detail_lines.append(f"Flooring: {flooring}")
    if pool:
        detail_lines.append(f"Pool: {pool}")
    if water:
        detail_lines.append(f"Water: {water}")
    if sewer:
        detail_lines.append(f"Sewer: {sewer}")

    if detail_lines:
        parts.append("\n### Property details")
        parts.append("  " + "\n  ".join(detail_lines))

    # Lot
    lot_lines: list[str] = []
    acres = lot.get("acres")
    sqft_lot = lot.get("squareFeet") or lot.get("size")
    lot_desc = lot.get("dimensions") or lot.get("dimensionsSource")
    if acres:
        lot_lines.append(f"Lot size: {acres} acres")
    if sqft_lot:
        lot_lines.append(f"Lot area: {sqft_lot} sq ft")
    if lot_desc:
        lot_lines.append(f"Lot details: {lot_desc}")
    if lot_lines:
        parts.append("\n### Lot")
        parts.append("  " + "\n  ".join(lot_lines))

    # Taxes
    tax_lines: list[str] = []
    tax_amount = taxes.get("annualAmount")
    tax_year = taxes.get("assessmentYear")
    if tax_amount:
        tax_lines.append(f"Annual taxes: {tax_amount}")
    if tax_year:
        tax_lines.append(f"Tax assessment year: {tax_year}")
    if tax_lines:
        parts.append("\n### Taxes")
        parts.append("  " + "\n  ".join(tax_lines))

    # Nearby amenities
    amenities = nearby.get("amenities") or []
    if isinstance(amenities, list) and amenities:
        top_amenities = amenities[:6]
        parts.append("\n### Nearby amenities")
        parts.append("  " + ", ".join(str(a) for a in top_amenities))

    # Open houses
    if open_houses:
        lines: list[str] = []
        for oh in open_houses[:3]:
            date = oh.get("date") or oh.get("startTime")
            start = oh.get("startTime")
            end = oh.get("endTime")
            oh_type = oh.get("type")
            status_oh = oh.get("status")
            pieces = []
            if date:
                pieces.append(str(date))
            if start and end:
                pieces.append(f"{start} – {end}")
            if oh_type:
                pieces.append(str(oh_type))
            if status_oh:
                pieces.append(f"({status_oh})")
            if pieces:
                lines.append(" - " + " ".join(pieces))
        if lines:
            parts.append("\n### Open houses")
            parts.extend(lines)

    # Condo-specific (fees & parking)
    condo_lines: list[str] = []
    fees = condo.get("fees") or {}
    if not isinstance(fees, dict):
        fees = {}
    maint = fees.get("maintenance")
    taxes_incl = fees.get("taxesIncl")
    heat_incl = fees.get("heatIncl")
    water_incl = fees.get("waterIncl")
    hydro_incl = fees.get("hydroIncl")
    parking_incl = fees.get("parkingIncl")
    pets = condo.get("pets")
    parking_type = condo.get("parkingType")

    if maint:
        condo_lines.append(f"Maintenance fee: {maint}")
    inclusions: list[str] = []
    if taxes_incl:
        inclusions.append("taxes")
    if heat_incl:
        inclusions.append("heat")
    if water_incl:
        inclusions.append("water")
    if hydro_incl:
        inclusions.append("hydro")
    if parking_incl:
        inclusions.append("parking")
    if inclusions:
        condo_lines.append("Fees include: " + ", ".join(inclusions))
    if parking_type:
        condo_lines.append(f"Parking type: {parking_type}")
    if pets:
        condo_lines.append(f"Pets: {pets}")

    if condo_lines:
        parts.append("\n### Condo")
        parts.append("  " + "\n  ".join(condo_lines))

    if not parts:
        return ""

    return "\n\n" + "\n".join(parts)


def format_listing_full(
    simplified: dict[str, Any],
    raw: dict[str, Any],
    index: int | None = None,
) -> str:
    """
    Full details view: reuse the existing detailed card, plus a richer block
    of extra fields from the raw Repliers listing.
    """
    card = format_listing_details(simplified, index)
    extras = _format_extra_details(raw)

    # Surface any public/virtual-tour links provided by the feed
    urls = _extract_urls(raw, max_urls=8)
    links_block = ""
    if urls:
        links_block = "\n\n### Links\n" + "\n".join(f"- [Open link {i + 1}]({u})" for i, u in enumerate(urls))
    else:
        links_block = "\n\n### Links\n- (No public listing/virtual-tour links were provided by this MLS feed.)"

    if extras:
        return card + extras + links_block
    return card + links_block


def format_listings(
    listings: list[dict[str, Any]],
    location: str | None = None,
    max_price: int | None = None,
    page: int = 1,
    has_more: bool = False,
) -> str:
    """
    Convert a list of simplified listing dicts into one readable message.
    Includes header and footer with refinement hints.
    """
    if not listings:
        return (
            "## No matches yet\n\n"
            "I could not find listings for those filters.\n\n"
            "**Try this next:**\n"
            "- Increase max price (e.g. `under $2600`)\n"
            "- Reduce bedroom requirement (e.g. `2 bedrooms`)\n"
            "- Switch area (e.g. `in Austin`)\n"
            "- Change type (e.g. `only condos`)\n\n"
            "_Note: some cities may not be included in your MLS coverage._"
        )

    parts = []
    if location or max_price is not None:
        desc = "## Property matches\n\n"
        scope_parts: list[str] = []
        if location:
            scope_parts.append(f"in **{location}**")
        if max_price is not None:
            scope_parts.append(f"under **${max_price:,}**")
        if scope_parts:
            desc += f"Showing results {' '.join(scope_parts)}.\n\n"
        desc += f"**Page:** {max(1, int(page))}\n\n"
        parts.append(desc)
    else:
        parts.append(f"## Property matches\n\n**Page:** {max(1, int(page))}\n\n")

    for i, listing in enumerate(listings, 1):
        parts.append(format_listing(i, listing))
        parts.append("\n\n")

    text = "".join(parts).strip()
    text += "\n\n"
    text += (
        "## Quick actions\n"
        "- `more` -> next page\n"
        "- `under $X` -> update budget\n"
        "- `X bedrooms` -> change bedrooms\n"
        "- `only condos` -> filter property type\n"
        "- `details N` -> full photos + extra details\n"
        "- `save N to my wishlist` -> save a listing\n"
        "- `show my wishlist` -> view saved listings\n"
    )
    if has_more:
        text += "\n**More available:** yes (say `more`)"
    else:
        text += "\n**More available:** no (refine filters for new matches)"
    return text
