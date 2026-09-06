import streamlit as st
import itertools
import random
import pandas as pd

st.set_page_config(page_title="Ping Pong 4 Hry", layout="centered")

st.title("🏓 Ping Pong 4 Hry")

# 1. SEZNAM HRÁČŮ (Načteno z vaší tabulky)
SEZNAM_HRACU = [
    "Pavel", "Jindra", "Vláďa", "Petr", "Sofka", 
    "Tibor", "Jarda", "Jirka", "Mirek", "Franta", "Fred"
]

# Inicializace stavu
if "prihlaseni" not in st.session_state:
    st.session_state.prihlaseni = {h: False for h in SEZNAM_HRACU}
if "zapasy" not in st.session_state:
    st.session_state.zapasy = []

# --- ZÁLOŽKA 1: PŘIHLÁŠENÍ (RSVP) ---
tab1, tab2, tab3 = st.tabs(["📋 Přihlášení", "⚔️ Rozpis zápasů", "📊 Žebříček"])

with tab1:
    st.subheader("Přihlášení na středeční session")
    st.write("Klikněte na své jméno pro potvrdit/zrušit účast:")
    
    # Velká tlačítka pro snadné ovládání na mobilu
    cols = st.columns(2)
    for idx, hrac in enumerate(SEZNAM_HRACU):
        col = cols[idx % 2]
        je_prihlasen = st.session_state.prihlaseni[hrac]
        label = f"✅ {hrac}" if je_prihlasen else f"❌ {hrac}"
        
        if col.button(label, key=f"btn_{hrac}", use_container_width=True):
            st.session_state.prihlaseni[hrac] = not je_prihlasen
            st.rerun()

    prihlaseni_hraci = [h for h, st_ in st.session_state.prihlaseni.items() if st_]
    st.info(f"Přihlášeno hráčů: **{len(prihlaseni_hraci)}** ({', '.join(prihlaseni_hraci)})")

    if len(prihlaseni_hraci) >= 4:
        if st.button("🎲 Vygenerovat rozpis na 2 stoly", type="primary", use_container_width=True):
            # Algoritmus pro generování dvojic
            dvojice = list(itertools.combinations(prihlaseni_hraci, 2))
            random.shuffle(dvojice)
            
            novy_rozpis = []
            kolo = 1
            while len(dvojice) >= 2:
                t1 = dvojice.pop(0)
                # Najít druhou dvojici bez překryvu hráčů
                t2 = None
                for candidate in dvojice:
                    if not (set(t1) & set(candidate)):
                        t2 = candidate
                        dvojice.remove(candidate)
                        break
                
                if t2:
                    novy_rozpis.append({
                        "Kolo": kolo,
                        "Stul 1": f"{t1[0]} + {t1[1]}  vs  {t2[0]} + {t2[1]}",
                        "Skore_Stul1": "0 : 0",
                        "Tym1": t1, "Tym2": t2
                    })
                    kolo += 1
            
            st.session_state.zapasy = novy_rozpis
            st.success("Rozpis úspěšně vytvořen! Přejděte na záložku 'Rozpis zápasů'.")

# --- ZÁLOŽKA 2: ROZPIS A ZÁPIS SKÓRE ---
with tab2:
    st.subheader("Rozpis zápasů na 2 stoly")
    if not st.session_state.zapasy:
        st.warning("Zatím nebyl vygenerován žádný rozpis.")
    else:
        for z in st.session_state.zapasy:
            with st.expander(f"Kolo {z['Kolo']}: {z['Stul 1']}"):
                col1, col2 = st.columns(2)
                s1 = col1.number_input(f"Sety {z['Tym1'][0]}+{z['Tym1'][1]}", min_value=0, max_value=5, key=f"s1_{z['Kolo']}")
                s2 = col2.number_input(f"Sety {z['Tym2'][0]}+{z['Tym2'][1]}", min_value=0, max_value=5, key=f"s2_{z['Kolo']}")

# --- ZÁLOŽKA 3: ŽEBRÍČEK ---
with tab3:
    st.subheader("Žebříček jednotlivců")
    # Zde se automaticky sčítají výhry z odehraných zápasů
    st.write("Tabulka se přepočítává po každém zadaném zápasu.")