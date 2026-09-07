"""Isti lanac ciscenja podataka kao u i u pretprocesiranju podataka za trening"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

import cyrtranslit

ROOT_PUTANJA = Path(__file__).resolve().parent
PUTANJA_IZUZETAKA = ROOT_PUTANJA / "resursi" / "dupli_samoglasnici.txt"

URL_SABLON = re.compile(r"https?://[^\s]+")
GIF_SABLON = re.compile(r"!\[.*?\]\([^\)]+\)")
UNICODE_EMOJI_SABLON = (
    r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF"
    r"\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U000024C2-\U0001F251"
    r"\U0001F601-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF"
    r"\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF"
    r"\U00002600-\U000026FF\U00002700-\U000027BF\u2600-\u26FF\u2700-\u27BF]"
)
TEKSTUALNI_EMOJI_SABLON = (
    r":[-]?[\)\*\>\/\\DdPpOo\[\]xX8]|[-]?[\)\*\>\/\\Oo\[\]xX8][-]?:"
    r"|[\(\)\[\]<>\/\\]+\s*"
)
EMOJI_SABLON = re.compile(UNICODE_EMOJI_SABLON + "|" + TEKSTUALNI_EMOJI_SABLON)
SPOMINJANJE_SABLON = re.compile(r"\s[ru]/\w+", flags=re.IGNORECASE)
SPECIJALNI_ZNACI = re.compile(r'[/\\\[\]{}~"^&%#@_+\=\|<>\*:\[\]]')
DUPLA_SLOVA = re.compile(r"([^\W\d_])\1+", flags=re.IGNORECASE)
VISESTRUKI_RAZMAK = re.compile(r"\s{2,}")

# Pravljenje izuzetaka od skraćivanja samoglasnika
@lru_cache(maxsize=1)
def _izuzeci() -> set[str]:
    return {
        linija.strip().lower()
        for linija in PUTANJA_IZUZETAKA.read_text(encoding="utf-8").splitlines()
        if linija.strip()
    }


def _normalizuj_rec(rec: str) -> str:
    smanjena = rec.lower()
    if smanjena in _izuzeci() or "najj" in smanjena:
        return rec
    return DUPLA_SLOVA.sub(r"\1", rec)

# Čišćenje mora ostati usklađeno sa postupkom korišćenim pri treniranju
def ocisti_komentar(tekst: str) -> str:
    tekst = str(tekst)
    tekst = SPOMINJANJE_SABLON.sub(" ", tekst)
    tekst = URL_SABLON.sub(" ", tekst)
    tekst = GIF_SABLON.sub(" ", tekst)
    tekst = EMOJI_SABLON.sub(" ", tekst)
    tekst = cyrtranslit.to_latin(tekst, "sr")
    tekst = SPECIJALNI_ZNACI.sub(" ", tekst)
    tekst = VISESTRUKI_RAZMAK.sub(" ", tekst).strip()
    if not tekst:
        return tekst
    return " ".join(_normalizuj_rec(rec) for rec in tekst.split())
