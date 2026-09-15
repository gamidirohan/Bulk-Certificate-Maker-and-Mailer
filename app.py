import os
import re
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, send_from_directory

from src.certificate_generator import generate_certificate
from src.email_sender import send_certificate
from src.excel_reader import read_participants
from src.manifest import Manifest

load_dotenv()
BASE = Path(__file__).parent
CERTIFICATES = BASE / "Templates"
FONTS = BASE / "Fonts"
OUTPUT = BASE / "output"
PDFS = OUTPUT / "certificates"
DEFAULT_FONT = FONTS / "PinyonScript-Regular.ttf"
DEFAULT_WORKBOOK = next(iter(BASE.glob("*.xlsx")), BASE / "participants.xlsx")
for path in (PDFS, OUTPUT / "logs"):
    path.mkdir(parents=True, exist_ok=True)

app = Flask(__name__, template_folder=".")
manifest = Manifest(OUTPUT / "manifest.json")

EXCLUDED_NAMES = {
    "shubh das", "soumya gupta", "nishant raghuvanshi", "anmol sen",
    "krrish setty a.m.", "keerthan s reddy", "kaushik manjunath",
    "vignesh", "harish raj", "anto joel valan mutharasu",
    "nishant", "harish",
}
EXCLUDED_EMAILS = {"dasshriyans2802@gmail.com", "krrishsetty08@gmail.com"}

CERTIFICATE_PRESETS = {
    "participation": {
        "label": "Participation certificates",
        "background": "Participant.png",
        "uses_workbook": True,
    },
    "first_place": {
        "label": "First place — 3E1P", "background": "1st prize team.png",
        "recipients": [
            {"name": "Shubh Das", "email": "dasshriyans2802@gmail.com"},
            {"name": "Soumya Gupta", "email": "soumya0343@gmail.com"},
            {"name": "Nishant Raghuvanshi", "email": "nishantraghuvanshi501@gmail.com"},
            {"name": "Anmol Sen", "email": "senanmol24@gmail.com"},
        ],
    },
    "second_place": {
        "label": "Second place — Vyasa Tech", "background": "2nd prize team.png",
        "recipients": [
            {"name": "Krrish Setty A.M.", "email": "krrishsetty08@gmail.com"},
            {"name": "Keerthan S Reddy", "email": "keerthansreddy7@gmail.com"},
            {"name": "Kaushik Manjunath", "email": "kaushikm0905@gmail.com"},
        ],
    },
    "third_place": {
        "label": "Third place — Vanta Protocol", "background": "3rd prize team.png",
        "recipients": [
            {"name": "Vignesh", "email": "vigneshm01430@gmail.com"},
            {"name": "Harish Raj", "email": "hari19rex@gmail.com"},
            {"name": "Anto Joel Valan Mutharasu", "email": "antojoel8020@gmail.com"},
        ],
    },
}


def normalized(value):
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").casefold()).strip()


def formatted_name(value):
    """Capitalize the first letter of every name word while preserving initials."""
    return str(value or "").strip().title()


def is_excluded(name, email):
    names = {normalized(item) for item in EXCLUDED_NAMES}
    return normalized(name) in names or str(email or "").casefold().strip() in EXCLUDED_EMAILS


def entry_category(entry):
    category = entry.get("certificate_type")
    if category in CERTIFICATE_PRESETS:
        return category
    for key, preset in CERTIFICATE_PRESETS.items():
        for person in preset.get("recipients", []):
            if str(entry.get("email", "")).casefold() == person["email"].casefold():
                return key
    return "participation"


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/certificate-presets")
def presets():
    return jsonify({
        key: {"label": preset["label"], "background": preset["background"],
              "uses_workbook": bool(preset.get("uses_workbook")),
              "count": len(preset.get("recipients", []))}
        for key, preset in CERTIFICATE_PRESETS.items()
    })


@app.get("/certificate-images/<path:name>")
def certificate_image(name):
    return send_from_directory(CERTIFICATES, name)


@app.get("/fonts/<path:name>")
def font_file(name):
    return send_from_directory(FONTS, name)


@app.post("/api/generate")
def generate():
    data = request.get_json(force=True)
    category = data.get("preset", "participation")
    preset = CERTIFICATE_PRESETS.get(category)
    if not preset:
        return jsonify(error="Unknown certificate category"), 400
    background = CERTIFICATES / preset["background"]
    if not background.is_file() or not DEFAULT_FONT.is_file():
        return jsonify(error="Add the configured certificate PNG and PinyonScript-Regular.ttf before generating."), 400
    if preset.get("uses_workbook"):
        if not DEFAULT_WORKBOOK.is_file():
            return jsonify(error="Add the configured participant workbook before generating participation certificates."), 400
        try:
            rows = read_participants(DEFAULT_WORKBOOK)
        except Exception as error:
            return jsonify(error=str(error)), 400
    else:
        rows = preset["recipients"]

    result = {"preset": category, "total": len(rows), "generated": 0, "skipped": 0, "warnings": []}
    for row in rows:
        if not row.get("email") or (category == "participation" and is_excluded(row["name"], row["email"])):
            result["skipped"] += 1
            continue
        display_name = formatted_name(row["name"])
        entry = manifest.get_or_create(display_name, row["email"], "HIVE", os.getenv("CERTIFICATE_YEAR", "2026"))
        entry["name"] = display_name
        entry["certificate_type"] = category
        output = PDFS / entry["filename"]
        try:
            if data.get("overwrite") or not output.exists():
                warning = generate_certificate(background, DEFAULT_FONT, output, display_name, data.get("config", {}))
                entry["generated_at"] = datetime.now(timezone.utc).isoformat()
                if warning:
                    result["warnings"].append(f"{row['name']}: {warning}")
            manifest.save()
            result["generated"] += 1
        except Exception as error:
            result["warnings"].append(f"{row['name']}: {error}")
            result["skipped"] += 1
    return jsonify(result)


@app.get("/api/send-preview")
def send_preview():
    entries = []
    for entry in manifest.entries:
        category = entry_category(entry)
        certificate = PDFS / entry.get("filename", "")
        if not entry.get("email") or not certificate.is_file():
            continue
        if category == "participation" and is_excluded(entry.get("name"), entry.get("email")):
            continue
        entries.append({
            "name": formatted_name(entry.get("name", "")), "email": entry["email"],
            "filename": certificate.name, "category": category,
            "sent": bool(entry.get("email_sent_at")),
            "send_error": entry.get("send_error"),
        })
    return jsonify(sender=os.getenv("EMAIL_FROM") or os.getenv("FROM_EMAIL") or "Not configured", entries=entries)


@app.post("/api/send")
def send():
    if not (os.getenv("RESEND_API_KEY") or os.getenv("EMAIL_API_KEY")):
        return jsonify(error="Email API key is not configured in .env"), 400
    options = request.get_json(silent=True) or {}
    selected = {str(email).casefold() for email in options.get("emails", [])}
    category_filter = options.get("category")
    sent = skipped = 0
    errors = []
    for entry in manifest.entries:
        category = entry_category(entry)
        certificate = PDFS / entry.get("filename", "")
        if not entry.get("email") or not certificate.is_file():
            continue
        if selected and entry["email"].casefold() not in selected:
            continue
        if category_filter and category != category_filter:
            continue
        if category == "participation" and is_excluded(entry.get("name"), entry.get("email")):
            skipped += 1
            continue
        if entry.get("email_sent_at") and not options.get("resend"):
            skipped += 1
            continue
        try:
            send_certificate(entry["email"], formatted_name(entry["name"]), certificate, category)
            entry["email_sent_at"] = datetime.now(timezone.utc).isoformat()
            entry["send_error"] = None
            manifest.save()
            sent += 1
        except Exception as error:
            # A provider error (including quota exhaustion) is never a sent
            # confirmation. Persist it so the table remains honest after refresh.
            entry["send_error"] = str(error)
            entry["last_send_attempt_at"] = datetime.now(timezone.utc).isoformat()
            manifest.save()
            errors.append(f"{entry.get('name')}: {error}")
    return jsonify(sent=sent, skipped=skipped, errors=errors)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "5000")), debug=False)
