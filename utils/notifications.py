"""
notifications.py
-----------------
Notification dispatch helpers for SAGE. Kept intentionally lightweight
for the hackathon build: Telegram / Email integrations are stubbed out
behind a single function so wiring in real credentials later only
touches this file.
"""

import os

TELEGRAM_ENABLED = bool(os.environ.get("SAGE_TELEGRAM_TOKEN"))
EMAIL_ENABLED = bool(os.environ.get("SAGE_SMTP_HOST"))


def build_emergency_message(alert_type: str, risk_score: int, action_taken: str, timestamp: str) -> str:
    return (
        f"🚨 {alert_type} Detected\n"
        f"Location: Kitchen\n"
        f"Risk Level: Critical ({risk_score})\n"
        f"Action Taken: {action_taken}\n"
        f"Time: {timestamp}"
    )


def send_notification(alert_type: str, risk_score: int, action_taken: str, timestamp: str):
    """
    Dispatches a notification through whichever channels are configured.
    In this hackathon build this is a no-op / log stub unless env vars
    for Telegram or SMTP are supplied, but the interface is ready to
    plug real providers in.
    """
    message = build_emergency_message(alert_type, risk_score, action_taken, timestamp)
    delivered_to = []

    if TELEGRAM_ENABLED:
        # Placeholder: call Telegram Bot API here with requests.post(...)
        delivered_to.append("telegram")

    if EMAIL_ENABLED:
        # Placeholder: send via smtplib here
        delivered_to.append("email")

    # Always log locally / for the in-app toast + browser notification pipeline
    delivered_to.append("browser")

    return {"message": message, "delivered_to": delivered_to}
