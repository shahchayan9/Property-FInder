"""Send report email with Google Sheet URL via Resend."""
import os

try:
    import resend as _resend  # type: ignore[import]
except ImportError:
    _resend = None  # type: ignore[assignment]


def send_report_email(to_email: str, sheet_url: str, count: int, location: str) -> bool:
    """
    Email a link to the Google Sheet report via Resend.
    Requires EMAIL_API_KEY in environment. Returns True on success.
    """
    api_key = (os.getenv("EMAIL_API_KEY") or "").strip()
    if not api_key or not _resend:
        return False

    _resend.api_key = api_key

    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #1a3a5c; margin-bottom: 8px;">Your Property Report is Ready</h2>
        <p style="color: #444; margin-top: 0;">
            We found <strong>{count} listings</strong> in <strong>{location}</strong>
            matching your search criteria.
        </p>
        <p style="margin: 24px 0;">
            <a href="{sheet_url}"
               style="display: inline-block; background-color: #1a3a5c; color: #ffffff;
                      padding: 12px 28px; text-decoration: none; border-radius: 5px;
                      font-weight: bold; font-size: 15px;">
                Open Full Report in Google Sheets
            </a>
        </p>
        <p style="color: #666; font-size: 13px; line-height: 1.5;">
            The sheet contains all listings with prices, sizes, neighborhoods,
            days on market, and property descriptions — sourced from Repliers MLS.
        </p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;">
        <p style="color: #aaa; font-size: 11px;">
            Sent by Property Finder &middot; Powered by Repliers MLS API
        </p>
    </div>
    """

    try:
        _resend.Emails.send({  # type: ignore[union-attr]
            "from": "Property Finder <onboarding@resend.dev>",
            "to": to_email,
            "subject": f"Your Property Report: {count} listings in {location}",
            "html": html_body,
        })
        return True
    except Exception as exc:
        import traceback
        print(f"[report_email] ERROR sending email: {exc}")
        traceback.print_exc()
        return False
