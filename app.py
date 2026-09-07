from pathlib import Path

import streamlit as st

from pretprocesiranje import ocisti_komentar
from predikcija import KLASE, predvidi, ucitaj_model

stilovi = (Path(__file__).parent / "stilovi.css").read_text(encoding="utf-8")

st.set_page_config(
    page_title="Predikcija govora mržnje komentara na srpskom jeziku",
    layout="wide",
)


@st.cache_resource(show_spinner="Model se učitava...")
def _model():
    return ucitaj_model()


if "rezultat" not in st.session_state:
    st.session_state.rezultat = None

ima_rezultat = st.session_state.rezultat is not None
if ima_rezultat:
    forma, graf = st.columns(2, gap="large")
else:
    st.markdown(f"<style>{stilovi}</style>", unsafe_allow_html=True)
    _leva, forma, _desna = st.columns([1, 2, 1])
    graf = None

with forma:
    st.title("Predikcija govora mržnje komentara na srpskom jeziku")
    st.caption(
        "Model: classla/bcms-bertic, fino podešen na skupu komentara sa r/serbia. "
        "Klase: Veoma pozitivno (1) - Veoma negativno (5 - govor mržnje)."
    )
    komentar = st.text_area(
        "Unesite komentar",
        height=180,
        placeholder="Npr. Ovo je najbolja vest danas.",
        key="komentar",
    )
    _leva, sredina, _desna = st.columns([2, 1, 2])
    with sredina:
        klasifikuj = st.button("Klasifikuj", type="primary", use_container_width=True)

    if klasifikuj:
        sirovi = (komentar or "").strip()
        if len(sirovi) < 2:
            st.error("Unesite komentar od najmanje 2 karaktera.")
        else:
            ociscen = ocisti_komentar(sirovi)
            if len(ociscen) < 2:
                st.error(
                    "Posle čišćenja (linkovi, emoji, specijalni znakovi) komentar je prekratak za predikciju."
                )
            else:
                with st.spinner("Klasifikacija je u toku..."):
                    try:
                        tokenizator, model, uredjaj = _model()
                        st.session_state.rezultat = predvidi(
                            sirovi, tokenizator, model, uredjaj
                        )
                    except Exception as exc:
                        st.error(str(exc))
                    else:
                        st.rerun()

    rezultat = st.session_state.rezultat
    if rezultat is not None:
        st.subheader(f"Predviđena klasa: {rezultat['klasa']}")
        if rezultat["presecen"]:
            st.warning(
                f"Komentar je predugačak za predikciju, jer ima {rezultat['broj_tokena']} tokena. "
            )

if graf is not None:
    with graf:
        rezultat = st.session_state.rezultat
        st.subheader("Verovatnoće po klasama")
        redosled = [KLASE[i] for i in range(5)]
        st.vega_lite_chart(
            {
                "height": 320,
                "data": {
                    "values": [
                        {
                            "klasa": klasa,
                            "verovatnoća": rezultat["verovatnoce"][klasa],
                        }
                        for klasa in redosled
                    ]
                },
                "mark": "bar",
                "encoding": {
                    "x": {
                        "field": "klasa",
                        "type": "nominal",
                        "sort": redosled,
                        "title": None,
                    },
                    "y": {
                        "field": "verovatnoća",
                        "type": "quantitative",
                        "title": None,
                    },
                },
            },
            use_container_width=True,
        )
