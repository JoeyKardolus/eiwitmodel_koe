# eiwitmodel.py
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import importlib.metadata
import streamlit 

# Workaround voor PyInstaller fout bij streamlit
try:
    importlib.metadata.version("streamlit")
except importlib.metadata.PackageNotFoundError:
    pass

# CVB-data per kg droge stof met DVE-waardes als WE
FEEDS = {
    "Kuilgras":     {"RE": 160, "WE": 96,  "RC": 250},  # DVE gemiddeld ~96
    "Snijmaïs":     {"RE": 80,  "WE": 53,  "RC": 220},  # DVE gemiddeld ~53
    "Hooi":         {"RE": 170, "WE": 92,  "RC": 300}   # DVE gemiddeld ~92
}

# Droge stof opname per koe per dag (in kg)
DS_OPNAME = 18

st.title("Interactief model voor eiwitbenutting en stikstofverliezen bij melkvee")
st.write("Pas de voerpercentages aan en zie het effect op stikstofuitstoot en rantsoenkwaliteit.")

# Defaultwaarden voor optimale verhouding
OPTIMAAL_KG = 70
OPTIMAAL_SM = 15
OPTIMAAL_HO = 15

# Init sliders met session_state
if "kg" not in st.session_state:
    st.session_state.kg = 50
    st.session_state.sm = 30
    st.session_state.ho = 20

# Optimalisatieknop
if st.button("🔧 Zet op optimale samenstelling"):
    best_score = 0
    best_combination = (0, 0, 0)
    for kg in range(40, 81, 5):
        for sm in range(0, 51, 5):
            ho = 100 - kg - sm
            if ho < 0 or ho > 60:
                continue
            kg_f = kg / 100
            sm_f = sm / 100
            ho_f = ho / 100
            RE = FEEDS["Kuilgras"]["RE"] * kg_f + FEEDS["Snijmaïs"]["RE"] * sm_f + FEEDS["Hooi"]["RE"] * ho_f
            WE = FEEDS["Kuilgras"]["WE"] * kg_f + FEEDS["Snijmaïs"]["WE"] * sm_f + FEEDS["Hooi"]["WE"] * ho_f
            RC = FEEDS["Kuilgras"]["RC"] * kg_f + FEEDS["Snijmaïs"]["RC"] * sm_f + FEEDS["Hooi"]["RC"] * ho_f
            if WE >= 90 and RC >= 200 and RE > 0:
                benutting = WE / RE
                if benutting > best_score:
                    best_score = benutting
                    best_combination = (kg, sm, ho)
    st.session_state.kg, st.session_state.sm, st.session_state.ho = best_combination
    st.success(f"Optimale samenstelling ingesteld: {best_combination[0]}% kuilgras, {best_combination[1]}% snijmaïs, {best_combination[2]}% hooi. Benuttingsgraad: {best_score*100:.1f}% binnen gezondheidsgrenzen.")

# Input: sliders
kg = st.slider("% Kuilgras", 0, 100, st.session_state.kg, key="kg")
sm = st.slider("% Snijmaïs", 0, 100, st.session_state.sm, key="sm")
ho = st.slider("% Hooi", 0, 100, st.session_state.ho, key="ho")

# Normaliseren als de som niet 100 is
total = kg + sm + ho
if total == 0:
    st.warning("Verdeel minimaal één voedermiddel boven 0%.")
    st.stop()
kg_frac = kg / total
sm_frac = sm / total
ho_frac = ho / total

# Berekening RE, WE en RC
RE = (FEEDS["Kuilgras"]["RE"] * kg_frac +
      FEEDS["Snijmaïs"]["RE"] * sm_frac +
      FEEDS["Hooi"]["RE"]     * ho_frac)

WE = (FEEDS["Kuilgras"]["WE"] * kg_frac +
      FEEDS["Snijmaïs"]["WE"] * sm_frac +
      FEEDS["Hooi"]["WE"]     * ho_frac)

RC = (FEEDS["Kuilgras"]["RC"] * kg_frac +
      FEEDS["Snijmaïs"]["RC"] * sm_frac +
      FEEDS["Hooi"]["RC"]     * ho_frac)

# Innameberekeningen
RE_inname = RE * DS_OPNAME
WE_inname = WE * DS_OPNAME
N_inname = RE_inname / 6.25
benutting = WE / RE
N_benut = N_inname * benutting
N_verlies = N_inname - N_benut
N_urine = N_verlies * 0.8
N_faeces = N_verlies * 0.2

# Resultaten weergeven
st.subheader("Resultaten")
st.markdown(f"**Ruw eiwit in rantsoen**: {RE:.1f} g/kg DS")
st.markdown(f"**Werkelijk eiwit (WE)** (DVE): {WE:.1f} g/kg DS")
st.markdown(f"**RE-inname per dag**: {RE_inname:.0f} g/dag")
st.markdown(f"**WE-inname per dag**: {WE_inname:.0f} g/dag")
st.markdown(f"**Stikstofinname per dag**: {N_inname:.0f} g/dag")
st.markdown(f"**Benutte stikstof** ({benutting*100:.1f}%): {N_benut:.0f} g/dag")
st.markdown(f"**Stikstofverlies totaal**: {N_verlies:.0f} g/dag")
st.markdown(f"- via urine (ureum/amiden): {N_urine:.0f} g/dag")
st.markdown(f"- via faeces (onverteerd eiwit): {N_faeces:.0f} g/dag")
st.markdown(f"**Ruwe celstof**: {RC:.1f} g/kg DS")

# Gezondheidstoets op basis van WE en RC
st.subheader("Gezondheidstoets van het rantsoen")

if WE < 90 and RC < 200:
    st.error("Zeer ongunstig: zowel het werkelijk eiwit als de ruwe celstof zijn te laag. Dit leidt tot risico op pensverzuring, onvoldoende penswerking, en eiwittekort voor melkproductie. Lage RC betekent minder speekselproductie, slechtere pensfermentatie en verlaagde voeropname.")
elif WE < 90:
    st.warning("Werkelijk eiwit (WE) is te laag (<90 g/kg DS). Er is risico op aminozuurtekort, onvoldoende pensmicrobieel eiwit en daling van melkproductie.")
elif RC < 200:
    st.warning("Ruwe celstof is te laag (<200 g/kg DS). Dit kan leiden tot pensverzuring, verminderde herkauwactiviteit, slechtere vezelfermentatie en een instabiele pens-pH. RC is cruciaal voor speekselproductie en het in stand houden van pensmotiliteit.")
elif WE > 110 and RC >= 200:
    st.info("Hoog WE-gehalte (>110 g/kg DS) met voldoende structuur. Goed benutbaar mits voldoende energie beschikbaar is, anders kans op verhoogd stikstofverlies.")
elif 90 <= WE <= 110 and RC >= 200:
    st.success("Rantsoen is optimaal: voldoende benutbaar eiwit en structuur voor gezonde pensfunctie en eiwitbenutting. De celstof ondersteunt een stabiel pensmilieu en voorkomt verteringsstoornissen.")
else:
    st.warning("Let op: het rantsoen zit in een overgangsgebied. Controleer energievoorziening en eiwitkwaliteit.")

# Visualisatie stikstofverdeling
fig, ax = plt.subplots()
ax.bar(["Benut", "Urineverlies", "Faecesverlies"], [N_benut, N_urine, N_faeces], color=["green", "red", "orange"])
ax.set_ylabel("g stikstof per koe per dag")
ax.set_title("Stikstofverdeling in het rantsoen")
st.pyplot(fig)

# Beschrijving onder de grafiek
st.markdown("""
**Toelichting:**
- De groene balk toont de hoeveelheid stikstof die benut wordt door het dier.
- De rode en oranje balken geven de stikstofverliezen via urine (ureum/amiden) en faeces weer.
- Door de voerkeuze aan te passen, kun je deze verliezen beperken en de efficiëntie verhogen.
- Deze balans is sterk afhankelijk van de verhouding tussen ruw eiwit (RE) en werkelijk eiwit (WE), maar ook van voldoende structuur (RC) in het rantsoen.
""")

import webbrowser
webbrowser.open("http://localhost:8501")
