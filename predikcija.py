"""Ucitavanje bcms-bertic-mini modela i predikcija sentimenta"""

import os
import shutil
import zipfile
from pathlib import Path

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from pretprocesiranje import ocisti_komentar

KLASE = {
    0: "Veoma pozitivno (1)",
    1: "Pozitivno (2)",
    2: "Neutralno (3)",
    3: "Negativno (4)",
    4: "Veoma negativno (5)",
}


def _secret(key, default=None):
    v = os.environ.get(key)
    if v:
        return v
    try:
        import streamlit as st
        return st.secrets.get(key, default)
    except Exception:
        return default


def _nadji_checkpoint(folder):
    if (folder / "config.json").exists():
        return folder
    for p in folder.rglob("config.json"):
        return p.parent
    raise FileNotFoundError("Nema config.json u " + str(folder))


def ucitaj_model():
    # Model dobija ulaze fiksne dužine, pa tokenizator mora imati token punjenja
    # čak i kada ga osnovni checkpoint nije definisao.
    gdrive_id = _secret("GDRIVE_ID_MODELA")
    putanja = str(_skini_model(gdrive_id))
    tok = AutoTokenizer.from_pretrained(putanja, trust_remote_code=True)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token 

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    mdl = AutoModelForSequenceClassification.from_pretrained(
        putanja, num_labels=5, trust_remote_code=True
    )
    if mdl.config.pad_token_id is None:
        mdl.config.pad_token_id = tok.pad_token_id
    mdl.to(device)
    # Predikcija mora biti deterministička - dropout i ostali trening slojevi
    # ne smeju menjati rezultat između dva ista unosa.
    mdl.eval()
    return tok, mdl, device


def _skini_model(file_id):
    # Skidanje modela sa Google Drive-a
    import gdown

    kes = Path.home() / ".cache" / "bertic_app" / "bcms-bertic-mini"
    folder_modela = kes / "model"
    if folder_modela.exists() and any(folder_modela.rglob("config.json")):
        return _nadji_checkpoint(folder_modela)

    kes.mkdir(parents=True, exist_ok=True)
    model_zip = kes / "bcms-bertic-mini.zip"
    gdown.download(id=file_id, output=str(model_zip), quiet=False)
    if folder_modela.exists():
        shutil.rmtree(folder_modela)
    folder_modela.mkdir()
    with zipfile.ZipFile(model_zip) as zf:
        zf.extractall(folder_modela)
    model_zip.unlink(missing_ok=True)
    return _nadji_checkpoint(folder_modela)


def predvidi(komentar, tokenizator, model, uredjaj):
    # Ciscenje komentara, brojanje tokena i predikcija sentimenta
    ociscen = ocisti_komentar(komentar)

    n_tok = len(
        tokenizator(ociscen, add_special_tokens=True, truncation=False, padding=False)[
            "input_ids"
        ]
    )

    x = tokenizator(
        ociscen,
        padding="max_length",
        truncation=True,
        max_length=256,
        return_tensors="pt",
    )
    x = {k: v.to(uredjaj) for k, v in x.items()}
    # Aplikacija samo zaključuje rezultat, ne čuva gradijetne
    with torch.no_grad():
        logits = model(**x).logits[0]
    probs = torch.softmax(logits, dim=-1)
    idx = int(torch.argmax(probs).item())

    probs_po_klasi = {}
    for i in range(5):
        probs_po_klasi[KLASE[i]] = float(probs[i].item())

    return {
        "ociscen": ociscen,
        "indeks": idx,
        "sentiment": idx + 1,
        "klasa": KLASE[idx],
        "verovatnoce": probs_po_klasi,
        "broj_tokena": n_tok,
        "presecen": n_tok > 256,
    }