# Aplikacija za predikciju govora mržnje (model bcms-bertic sa manjim skupom komentara)

Streamlit aplikacija koja klasifikuje komentar na skali od **1 (veoma pozitivno) - 5 (veoma negativno - govor mržnje)**. Koristi fino podešeni `classla/bcms-bertic` treniran na manjem skupu komentara.

## Lokalno pokretanje

Python 3.11+:

```bash
cd hate_speech_serbia_application
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Model se uvek skida sa Google Drive-a. U `.streamlit/secrets.toml`:

```toml
GDRIVE_ID_MODELA = "FILE_ID"
```

Ili preko environment varijable:

```bash
GDRIVE_ID_MODELA="FILE_ID" streamlit run app.py
```

