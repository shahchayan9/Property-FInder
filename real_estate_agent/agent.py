"""
Real Estate Report Agent — deep research backend for Property-FInder.

Receives ReportRequest from Property-FInder, fetches all Repliers listings,
creates a Google Sheet, emails the sheet URL, and replies with ReportResponse.

Run via: python run_real_estate_agent.py
"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from uagents import Agent, Context, Protocol

# Path setup — must happen before any local imports
_dir = Path(__file__).resolve().parent      # real_estate_agent/
_project_root = _dir.parent                # Property-FInder/
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# Load shared .env (same file used by Property-FInder agent)
load_dotenv(_project_root / "asi1_agent" / ".env")

from real_estate_agent.report_models import ReportRequest, ReportResponse
from real_estate_agent.workflow import run_report_workflow
from real_estate_agent.report_email import send_report_email

# ── Agent setup ──────────────────────────────────────────────────────────────

agent_seed = os.getenv("AGENT_SECRET_KEY_2", "").strip()
if not agent_seed:
    raise ValueError(
        "AGENT_SECRET_KEY_2 not set in asi1_agent/.env — "
        "add a unique 32-char seed for the Real Estate Report Agent."
    )

agent_port = int(os.getenv("RE_AGENT_PORT", "8001"))
use_mailbox = os.getenv("USE_MAILBOX", "true").lower() == "true"

_agent_kwargs: dict = {
    "name": "Real Estate Report Agent",
    "seed": agent_seed,
    "port": agent_port,
}
if use_mailbox:
    _agent_kwargs["mailbox"] = True

agent = Agent(**_agent_kwargs)


# ── Report protocol ──────────────────────────────────────────────────────────

report_proto = Protocol(name="ReportProtocol", version="1.0")


@report_proto.on_message(ReportRequest)
async def handle_report_request(ctx: Context, sender: str, msg: ReportRequest):
    """
    1. Fetch all Repliers listings for the given filters.
    2. Export to a Google Sheet.
    3. Email the sheet URL to msg.user_email.
    4. Reply with ReportResponse so Property-FInder can update the chat.
    """
    ctx.logger.info(
        "report_request session=%s email=%s location=%s",
        msg.session_id,
        msg.user_email,
        msg.filters.get("location", "?"),
    )

    result = await run_report_workflow(
        filters=msg.filters,
        user_id=msg.session_id,
    )

    if not result.get("sheet_url"):
        await ctx.send(
            sender,
            ReportResponse(
                session_id=msg.session_id,
                success=False,
                message=f"Report generation failed: {result.get('error', 'unknown error')}",
            ),
        )
        return

    # Email the sheet URL
    email_sent = False
    if msg.user_email:
        email_sent = send_report_email(
            to_email=msg.user_email,
            sheet_url=result["sheet_url"],
            count=result["count"],
            location=result["location"],
        )
        ctx.logger.info(
            "report_email email_sent=%s to=%s sheet=%s",
            email_sent, msg.user_email, result["sheet_url"],
        )

    if email_sent:
        message = (
            f"Your full property report is ready — {result['count']} listings in "
            f"{result['location']} have been emailed to {msg.user_email}."
        )
    else:
        message = (
            f"Report ready: {result['count']} listings in {result['location']}.\n"
            f"Sheet: {result['sheet_url']}\n"
            f"(Email delivery failed — check EMAIL_API_KEY or resend package)"
        )

    await ctx.send(
        sender,
        ReportResponse(
            session_id=msg.session_id,
            success=True,
            message=message,
            email_sent_to=msg.user_email if email_sent else "",
            sheet_url=result["sheet_url"],
        ),
    )


agent.include(report_proto, publish_manifest=True)


@agent.on_event("startup")
async def on_startup(ctx: Context):
    ctx.logger.info("Real Estate Report Agent started: %s", agent.address)
    ctx.logger.info(
        "Google Sheets: %s | Email: %s",
        "configured" if os.getenv("GOOGLE_OAUTH_CLIENT_JSON") or os.getenv("GOOGLE_OAUTH_CLIENT_FILE") else "NOT configured",
        "configured" if os.getenv("EMAIL_API_KEY") else "NOT configured",
    )
