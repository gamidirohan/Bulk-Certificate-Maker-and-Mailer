import base64
from html import escape
import os

import requests


def send_certificate(recipient, name, certificate_path, certificate_type="participation"):
    key = os.getenv("RESEND_API_KEY") or os.getenv("EMAIL_API_KEY")
    sender = os.getenv("EMAIL_FROM") or os.getenv("FROM_EMAIL")
    if not key or not sender:
        raise RuntimeError("RESEND_API_KEY and EMAIL_FROM must be configured")
    safe_name = escape(name)
    award_labels = {
        "first_place": "winning first place with 3E1P",
        "second_place": "winning second place with Vyasa Tech",
        "third_place": "winning third place with Vanta Protocol",
    }
    if certificate_type in award_labels:
        subject = "Congratulations on your THE HIVE hackathon win!"
        opening = f"Congratulations on {award_labels[certificate_type]}!"
    else:
        subject = "Thank you for participating in THE HIVE hackathon"
        opening = "Thank you so much for participating in THE HIVE hackathon."
    html = (
        f"<p>Hi {safe_name},</p>"
        f"<p>{opening}</p>"
        "<p>THE HIVE was a 24-hour AI hackathon conducted on 29 and 30 August at Startup Park. "
        "Your enthusiasm, time, and ideas helped make the event special.</p>"
        "<p>We are grateful to our sponsors: Emergent AI, AI Grants India, and Startup Park India.</p>"
        "<p>Please find your certificate attached. Thank you for coming and being part of the HIVE community!</p>"
        "<p>Warm regards,<br>THE HIVE Team</p>"
    )
    response = requests.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={
            "from": sender, "to": [recipient],
            "subject": subject,
            "html": html,
            "attachments": [{"filename": certificate_path.name, "content": base64.b64encode(certificate_path.read_bytes()).decode()}],
        },
        timeout=30,
    )
    response.raise_for_status()
