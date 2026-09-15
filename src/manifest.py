import json


class Manifest:
    def __init__(self, path):
        self.path = path
        try:
            self.entries = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
        except json.JSONDecodeError:
            self.entries = []

    def get_or_create(self, name, email, prefix, year):
        for entry in self.entries:
            if entry.get("email", "").casefold() == email.casefold():
                return entry
        entry = {
            "name": name, "email": email,
            "certificate_id": f"{prefix}-{year}-{len(self.entries) + 1:04d}",
            "filename": f"{prefix}-{year}-{len(self.entries) + 1:04d}.pdf",
            "email_sent_at": None,
        }
        self.entries.append(entry)
        return entry

    def save(self):
        self.path.write_text(json.dumps(self.entries, indent=2), encoding="utf-8")
