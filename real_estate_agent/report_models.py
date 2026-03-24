"""
Shared message models for Property-FInder ↔ Real Estate Report Agent communication.
Both agents import from here so uAgents schema hashes match.
"""
from uagents import Model


class ReportRequest(Model):
    """Sent by Property-FInder to trigger a full report."""
    session_id: str           # chat session ID (used to route the reply back)
    filters: dict             # current Property-FInder state dict (location, max_price, etc.)
    user_email: str           # where to email the finished report


class ReportResponse(Model):
    """Sent by Real Estate Report Agent back to Property-FInder."""
    session_id: str
    success: bool
    message: str              # human-readable status shown in chat
    email_sent_to: str = ""   # non-empty if email was delivered
    sheet_url: str = ""       # Google Sheet URL (populated even if email failed)
