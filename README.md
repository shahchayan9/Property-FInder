# Property Finder — Conversational Real Estate Agent (MVP)

A conversational property search agent built on **ASI1** (Agentverse). Users chat in natural language to search MLS listings via the **Repliers API**, refine results, save a wishlist, and optionally export full reports to Google Sheets — with **Stripe** payment gating for premium features.

---

## Features

- **Conversational search** — natural language queries: *"2 bed homes under $600k in Austin"*
- **Refine on the fly** — *"under 550k"*, *"only condos"*, *"3 bedrooms"*
- **Pagination** — say *"more"* to see the next page
- **Wishlist** — save favorites during a session
- **Email export** — send your wishlist via email (Resend)
- **Full report generation** — export up to 50 listings to a Google Sheet (separate Report Agent)
- **Payment gating** — Stripe embedded checkout for premium listing details and full reports

---

## Project Structure

```
Property-FInder/
├── asi1_agent/                  # Conversational Property Finder agent
│   ├── property_agent.py        # Main agent: chat handler, state, Repliers calls
│   ├── nl_parser.py             # Regex-based filter extraction
│   ├── llm_parser.py            # OpenAI-based parsing (optional fallback)
│   ├── state_manager.py         # In-memory session state
│   ├── stripe_payments.py       # Stripe checkout session creation
│   ├── payment_proto.py         # Payment protocol schema
│   ├── requirements.txt
│   └── .env.example
├── repliers_client/             # MLS API client
│   ├── client.py                # search_listings(filters) -> listings + meta
│   ├── filters.py               # Internal filters -> Repliers API params
│   └── formatter.py             # Listings -> readable chat text
├── real_estate_agent/           # Background Report Generation agent
│   ├── agent.py                 # Agent setup
│   ├── workflow.py              # Fetch listings, create Google Sheet
│   ├── sheets.py                # Google Sheets OAuth + sheet creation
│   ├── report_models.py         # ReportRequest / ReportResponse schemas
│   └── report_email.py          # Email delivery of reports
├── run_agent.py                 # Entry point: Property Finder (port 8000)
├── run_real_estate_agent.py     # Entry point: Report Agent (port 8001)
└── .env.example                 # Configuration template
```

---

## Setup

**1. Create a virtualenv and install dependencies:**

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r asi1_agent/requirements.txt
```

**2. Configure environment variables:**

```bash
cp asi1_agent/.env.example .env
# Edit .env with your API keys (see Environment Variables below)
```

---

## Running the Agents

Open two terminals from the project root:

```bash
# Terminal 1 — Property Finder agent (port 8000)
python run_agent.py

# Terminal 2 — Report Generation agent (port 8001)
python run_real_estate_agent.py
```

Copy the Report Agent's printed address (e.g. `agent1q...`) and set it as `REAL_ESTATE_AGENT_ADDRESS` in `.env`, then restart Terminal 1.

**Access:** Open [https://asi1.ai](https://asi1.ai), find the "Property Finder" agent by name or address, and start chatting.

---

## Usage

| What you say | What happens |
|---|---|
| *"Find 2 bed homes under $600k in Austin"* | Parses filters, queries Repliers, returns top 3 listings |
| *"under 550k"* or *"refine under 550k"* | Updates `max_price`, re-queries |
| *"only condos"* or *"3 bedrooms"* | Updates property type / beds, re-queries |
| *"more"* | Next page of results (same filters) |
| *"wishlist"* | Shows saved listings |
| *"export wishlist to you@example.com"* | Emails wishlist via Resend |
| *"full report"* | Triggers Stripe checkout; on payment, generates Google Sheet |

---

## Environment Variables

| Variable | Required | Purpose |
|---|---|---|
| `AGENT_SECRET_KEY_1` | Yes | 32-char hex seed for Property Finder agent identity |
| `AGENTVERSE_API_KEY` | Yes | Mailbox/Almanac key from [Agentverse](https://agentverse.ai) |
| `REPLIERS_API_KEY` | Yes | MLS listings API key from [Repliers](https://repliers.io) |
| `OPENAI_API_KEY` | No | Enables GPT-based NLP; falls back to regex if unset |
| `EMAIL_API_KEY` | No | [Resend](https://resend.com) key (`re_...`) for wishlist/report emails |
| `EMAIL_TO` | No | Default recipient for `export wishlist` (no address needed in chat) |
| `STRIPE_SECRET_KEY` | No | Stripe secret key for payment gating |
| `STRIPE_PUBLISHABLE_KEY` | No | Stripe publishable key |
| `STRIPE_AMOUNT_CENTS` | No | Charge amount in cents (default: `199` = $1.99) |
| `AGENT_SECRET_KEY_2` | No | Seed for the Report Agent |
| `REAL_ESTATE_AGENT_ADDRESS` | No | Address of running Report Agent |
| `GOOGLE_OAUTH_CLIENT_FILE` | No | Path to `google_oauth_client.json` |
| `GOOGLE_SHEET_SHARE_EMAIL` | No | Email to share generated Google Sheets with |
| `USE_MAILBOX` | No | Use Agentverse Mailbox (default: `true`) |
| `AGENT_PORT` | No | Local agent port (default: `8000`) |

---

## Notes

- **No database** — all session state (filters, wishlist) is in-memory and resets on restart.
- **MLS coverage** — search results depend on your Repliers subscription. If a city returns nothing, try a covered market (Austin, TX works in most setups).
- **Stripe is in test mode** by default — use Stripe test card numbers.
- **Google Sheets OAuth** uses device flow; authenticate once and tokens are cached in `google_user_tokens.json`.

---

## Success Criteria (MVP)

1. *"2 bed under 600k in Austin"* → returns 3 listings
2. *"under 550k"* → returns updated listings
3. *"more"* → returns next page
