import streamlit as st
import random
import itertools
import pandas as pd

st.set_page_config(page_title="Ping Pong Dobrovíz", layout="centered", page_icon="🏓")

st.title("🏓 Ping Pong Dobrovíz")
st.caption("Čtyřhry na 2 stoly – 3 vítězné sety do 11")

# Seznam hráčů ze stávající Google Tabulky
VSECHNI_HRACI = [
    "Pavel", "Jindra", "Vláďa", "Petr", "Sofka", 
    "Tibor", "Jarda", "Jirka", "Mirek", "Franta", 
    "Fred", "Jirka S.", "Miro", "Petr W.", "Přespolní"
]

# --- INICIALIZACE STAVU ---
if "prihlaseni" not in st.session_state:
    st.session_state.prihlaseni = {h: False for h in VSECHNI_HRACI}

if "stul1_zapasy" not in st.session_state:
    st.session_state.stul1_zapasy = []
if "stul2_zapasy" not in st.session_state:
    st.session_state.stul2_zapasy = []

if "statistiky_hraci" not in st.session_state:
    st.session_state.statistiky_hraci = {h: {"Odehráno": 0, "Výhry": 0, "Prohry": 0, "Sety+": 0, "Sety-": 0} for h in VSECHNI_HRACI}

if "statistiky_dvojice" not in st.session_state:
    st.session_state.statistiky_dvojice = {}

# Funkce pro generování 3 zápasů pro 4 hráče na jednom stole
def vygeneruj_trojblok(hraci_4):
    a, b, c, d = hraci_4
    return [
        {"Tým 1": (a, b), "Tým 2": (c, d), "Odehráno": False, "Skóre 1": 0, "Skóre 2": 0},
        {"Tým 1": (a, c), "Tým 2": (b, d), "Odehráno": False, "Skóre 1": 0, "Skóre 2": 0},
        {"Tým 1": (a, d), "Tým 2": (b, c), "Odehráno": False, "Skóre 1": 0, "Skóre 2": 0},
    ]

tab1, tab2, tab3 = st.tabs(["📋 Přihlášení", "⚔️ Stoly a Zápasy", "📊 Žebříček"])

# --- ZÁLOŽKA 1: PŘIHLÁŠENÍ ---
with tab1:
    st.subheader("Kdo dnes přijde na středeční session?")
    st.write("Kliknutím potvrdíte / zrušíte účast:")

    cols = st.columns(2)
    for idx, hrac in enumerate(VSECHNI_HRACI):
        col = cols[idx % 2]
        je_prihlasen = st.session_state.prihlaseni[hrac]
        btn_label = f"✅ {hrac}" if je_prihlasen else f"❌ {hrac}"
        
        if col.button(btn_label, key=f"btn_{hrac}", use_container_width=True):
            st.session_state.prihlaseni[hrac] = not je_prihlasen
            st.rerun()

    pritomni = [h for h, stav in st.session_state.prihlaseni.items() if stav]
    st.info(f"Přihlášeno hráčů: **{len(pritomni)}** ({', '.join(pritomni)})")

    if len(pritomni) >= 4:
        if st.button("🎲 Rozdělit na stoly a vygenerovat zápasy", type="primary", use_container_width=True):
            random.shuffle(pritomni)
            
            # Pokud je 8 hráčů: 4 na Stůl 1, 4 na Stůl 2
            # Pokud je 6–7 hráčů: Stůl 1 má 4 hráče, Stůl 2 má zbytek
            stul1_hraci = pritomni[:4]
            stul2_hraci = pritomni[4:] if len(pritomni) >= 6 else []

            st.session_state.stul1_zapasy = vygeneruj_trojblok(stul1_hraci)
            
            if len(stul2_hraci) >= 4:
                st.session_state.stul2_zapasy = vygeneruj_trojblok(stul2_hraci[:4])
            elif len(stul2_hraci) == 3:
                # Pro 3 hráče na Stole 2: střídavá dvouhra nebo rotační debl
                st.session_state.stul2_zapasy = vygeneruj_trojblok(stul2_hraci + [stul1_hraci[0]])
            else:
                st.session_state.stul2_zapasy = []

            st.success("Zápasy vygenerovány! Přejděte na záložku 'Stoly a Zápasy'.")

# --- ZÁLOŽKA 2: ZÁPASY PO STOLECH ---
with tab2:
    col_stul1, col_stul2 = st.columns(2)

    # Funkce pro vykreslení zápasů jednoho stolu
    def vykresli_stul(titulek, zapasy, key_prefix):
        st.subheader(titulek)
        if not zapasy:
            st.write("Žádné zápasy.")
            return

        for idx, z in enumerate(zapasy):
            t1_str = f"{z['Tým 1'][0]} + {z['Tým 1'][1]}"
            t2_str = f"{z['Tým 2'][0]} + {z['Tým 2'][1]}"
            
            with st.expander(f"Zápas {idx+1}: {t1_str} vs {t2_str}", expanded=not z["Odehráno"]):
                if z["Odehráno"]:
                    st.success(f"Výsledek: **{z['Skóre 1']} : {z['Skóre 2']}** na sety")
                else:
                    c1, c2 = st.columns(2)
                    s1 = c1.number_input(f"Sety {z['Tým 1'][0]}", min_value=0, max_value=3, value=0, key=f"{key_prefix}_s1_{idx}")
                    s2 = c2.number_input(f"Sety {z['Tým 2'][0]}", min_value=0, max_value=3, value=0, key=f"{key_prefix}_s2_{idx}")

                    if st.button("Uložit výsledek", key=f"{key_prefix}_btn_{idx}"):
                        if s1 == 3 or s2 == 3:
                            z["Skóre 1"] = s1
                            z["Skóre 2"] = s2
                            z["Odehráno"] = True
                            
                            # Aktualizace statistik jednotlivců
                            for h in z['Tým 1']:
                                st.session_state.statistiky_hraci[h]["Odehráno"] += 1
                                st.session_state.statistiky_hraci[h]["Sety+"] += s1
                                st.session_state.statistiky_hraci[h]["Sety-"] += s2
                                if s1 > s2:
                                    st.session_state.statistiky_hraci[h]["Výhry"] += 1
                                else:
                                    st.session_state.statistiky_hraci[h]["Prohry"] += 1

                            for h in z['Tým 2']:
                                st.session_state.statistiky_hraci[h]["Odehráno"] += 1
                                st.session_state.statistiky_hraci[h]["Sety+"] += s2
                                st.session_state.statistiky_hraci[h]["Sety-"] += s1
                                if s2 > s1:
                                    st.session_state.statistiky_hraci[h]["Výhry"] += 1
                                else:
                                    st.session_state.statistiky_hraci[h]["Prohry"] += 1

                            st.success("Výsledek uložen!")
                            st.rerun()
                        else:
                            st.error("Hraje se na 3 vítězné sety (jeden tým musí mít 3 sety)!")

    with col_stul1:
        vykresli_stul("🟢 Stůl 1", st.session_state.stul1_zapasy, "s1")

    with col_stul2:
        vykresli_stul("🔵 Stůl 2", st.session_state.stul2_zapasy, "s2")

# --- ZÁLOŽKA 3: ŽEBRÍČEK ---
with tab3:
    st.subheader("🏆 Průběžný žebříček jednotlivců")
    
    data = []
    for hrac, stat in st.session_state.statistiky_hraci.items():
        if stat["Odehráno"] > 0:
            usp = round((stat["Výhry"] / stat["Odehráno"]) * 100, 1)
            data.append({
                "Hráč": hrac,
                "Odehráno": stat["Odehráno"],
                "Výhry": stat["Výhry"],
                "Prohry": stat["Prohry"],
                "Sety": f"{stat['Sety+']}:{stat['Sety-']}",
                "Úspěšnost (%)": usp
            })
    
    if data:
        df = pd.DataFrame(data).sort_values(by=["Výhry", "Úspěšnost (%)"], ascending=False)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Zatím nebyly odehrány žádné zápasy.")