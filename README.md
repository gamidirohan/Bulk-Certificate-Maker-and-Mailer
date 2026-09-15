# Certificate generator

## Required font

The workbook and all four certificate images are already present in this folder. Before generating, add only this deleted font file:

- `Fonts/PinyonScript-Regular.ttf`

## Run locally

```powershell
uv venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
.\.venv\Scripts\python.exe app.py
```

With `uv`, you can install from `pyproject.toml` instead:

```powershell
uv sync
.\.venv\Scripts\python.exe app.py
```

Before sending email, add your real `RESEND_API_KEY` and `EMAIL_FROM` values to `.env`. The restored `.env` file is empty, so no email can be sent accidentally.

Open http://127.0.0.1:5000.

The award categories are fixed to the specified X members. All other workbook participants receive `Templates/Participant.png`. Choose a category, edit or drag text directly on the certificate, generate PDFs, then use the email-delivery table to search recipients, see sent status, select rows, and explicitly send or resend certificates.
