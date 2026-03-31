# 🏠 Property Finder Agent

> Search real MLS listings through natural conversation — no forms, no filters, just chat.

---

## What it does

**Property Finder** connects to live MLS data via the Repliers API and lets you search, refine, and explore real estate listings in plain English. Save favorites to a wishlist, get full property reports, and export results — all from a single chat window on ASI1.

---

## ✨ Capabilities

- 🔍 **Natural language search** — describe what you want, and the agent figures out the filters
- 🔄 **Refine on the fly** — update price, beds, property type mid-conversation
- 📄 **Pagination** — ask for "more" to see the next batch of listings
- ❤️ **Wishlist** — save listings you like during a session
- 📧 **Email export** — send your wishlist to any email address
- 📊 **Full report** — export up to 50 listings as a formatted Google Sheet
- 💳 **Premium details** — unlock full listing info via a quick Stripe checkout

---

## 💬 Example Queries

**Basic search**
- *"Find 2 bedroom homes under $600k in Austin"*
- *"Show me condos in Miami under $400k"*

**Refinement**
- *"under 550k"*
- *"only condos"*
- *"change to 3 bedrooms"*

**Pagination & wishlist**
- *"more"*
- *"save that one"*
- *"show my wishlist"*

**Export**
- *"export wishlist to you@example.com"*
- *"generate a full report"*

---

## 📋 Sample Interaction

**User:** Find 3 bed homes under $700k in Austin

**Agent:**
> Here are 3 listings in Austin, TX:
>
> 🏡 **123 Maple St** — $689,000 | 3 bed / 2 bath | 1,850 sqft | 12 days on market
> 🏡 **456 Oak Ave** — $645,000 | 3 bed / 2.5 bath | 2,100 sqft | 5 days on market
> 🏡 **789 Pine Rd** — $599,000 | 3 bed / 1 bath | 1,620 sqft | 30 days on market
>
> Say **"more"** for the next page, **"save [number]"** to wishlist, or refine — e.g. *"under 650k"* or *"only newer builds"*.

---

## ⚠️ Notes

- Listing availability depends on Repliers MLS coverage. Austin, TX works well in most setups. If a city returns no results, try a nearby major market or broaden the search.
- Session state (wishlist, filters) resets when the conversation ends — no data is stored.
