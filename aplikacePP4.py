import streamlit as st
import pandas as pd
import json
import os
from datetime import date

st.set_page_config(page_title="Ping Pong Dobrovíz", layout="wide", page_icon="🏓")

DB_FILE = "databaze_pingpong.json"

# HISTORICKÝ ZÁKLAD NAČTENÝ Z VAŠÍ GOOGLE TABULKY
HISTORIE_TABULKA = {
    "Sofka": {"Výhry": 79, "Účast": 23},
    "Jindra": {"Výhry": 78, "Účast": 21},
    "Tibor": {"Výhry": 74, "Účast": 19},
    "Pavel": {"Výhry": 69, "Účast": 21},
    "Jarda": {"Výhry": 63, "Účast": 18},
    "Vláďa": {"Výhry": 55, "Účast": 19},
    "Jirka": {"Výhry": 33, "Účast": 22},
    "Petr": {"Výhry": 20, "Účast": 6},
    "Miro": {"Výhry": 5, "Účast": 4},
    "Franta": {"Výhry": 4, "Účast": 1},
    "Fred": {"Výhry": 1, "Účast": 2},
    "Jirka S.": {"Výhry": 0, "Účast": 0},
    "Mirek": {"Výhry": 0, "Účast": 0},
    "Petr W.": {"Výhry": 0, "Účast": 0},
    "Přespolní": {"Výhry": 0, "Účast": 0}
}

VSECHNI_HRACI = list(HISTORIE_TABULKA.keys())

# --- PRÁCE S DATABÁZÍ ---
def nacti_databazi():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def uloz_databazi(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if "odehrane_zapasy" not in st.session_state:
    st.session_state.odehrane_zapasy = nacti_databazi()

if "dnesni_zapasy" not in st.session_state:
    st.session_state.dnesni_zapasy = []

if "prihlaseni" not in st.session_state:
    st.session_state.prihlaseni = {h: False for h in VSECHNI_HRACI}

# --- VÝPOČET CELKOVÉHO ŽEBŘÍČKU (HISTORIE + NOVÉ ZÁPASY) ---
def spocitej_statistiky():
    jednotlivci = {h: {
        "Odehráno": HISTORIE_TABULKA[h]["Účast"], 
        "Výhry": HISTORIE_TABULKA[h]["Výhry"], 
        "Prohry": HISTORIE_TABULKA[h]["Účast"] - HISTORIE_TABULKA[h]["Výhry"], 
        "Sety+": 0, "Sety-": 0
    } for h in VSECHNI_HRACI}
    
    dvojice = {}

    for z in st.session_state.odehrane_zapasy:
        s1, s2 = z["skore1"], z["skore2"]
        t1, t2 = z["tym1"], z["tym2"]
        
        p1_key = " + ".join(sorted(t1))
        p2_key = " + ".join(sorted(t2))

        if p1_key not in dvojice:
            dvojice[p1_key] = {"Odehráno": 0, "Výhry": 0, "Prohry": 0, "Sety+": 0, "Sety-": 0}
        if p2_key not in dvojice:
            dvojice[p2_key] = {"Odehráno": 0, "Výhry": 0, "Prohry": 0, "Sety+": 0, "Sety-": 0}

        for h in t1:
            jednotlivci[h]["Odehráno"] += 1
            jednotlivci[h]["Sety+"] += s1
            jednotlivci[h]["Sety-"] += s2
            if s1 > s2: jednotlivci[h]["Výhry"] += 1
            else: jednotlivci[h]["Prohry"] += 1

        for h in t2:
            jednotlivci[h]["Odehráno"] += 1
            jednotlivci[h]["Sety+"] += s2
            jednotlivci[h]["Sety-"] += s1
            if s2 > s1: jednotlivci[h]["Výhry"] += 1
            else: jednotlivci[h]["Prohry"] += 1

        dvojice[p1_key]["Odehráno"] += 1
        dvojice[p1_key]["Sety+"] += s1
        dvojice[p1_key]["Sety-"] += s2
        if s1 > s2: dvojice[p1_key]["Výhry"] += 1
        else: dvojice[p1_key]["Prohry"] += 1

        dvojice[p2_key]["Odehráno"] += 1
        dvojice[p2_key]["Sety+"] += s2
        dvojice[p2_key]["Sety-"] += s1
        if s2 > s1: dvojice[p2_key]["Výhry"] += 1
        else: dvojice[p2_key]["Prohry"] += 1

    return jednotlivci, dvojice

# --- GENERÁTOR VYROVNANÝCH DVOJIC ---
def generuj_vyrovnane_zapasy(pritomni_hraci):
    jednotlivci, _ = spocitej_statistiky()
    
    def ziskej_uspesnost(hrac):
        st_ = jednotlivci[hrac]
        return (st_["Výhry"] / st_["Odehráno"]) if st_["Odehráno"] > 0 else 0.5

    serazeni = sorted(pritomni_hraci, key=ziskej_uspesnost, reverse=True)
    zapasy = []
    
    if len(serazeni) >= 8:
        g1 = [serazeni[0], serazeni[3], serazeni[4], serazeni[7]]
        g2 = [serazeni[1], serazeni[2], serazeni[5], serazeni[6]]
        
        for stul_id, g in [(1, g1), (2, g2)]:
            zapasy.append({"blok": 1, "stul": stul_id, "tym1": [g[0], g[3]], "tym2": [g[1], g[2]], "odehrano": False})
            zapasy.append({"blok": 1, "stul": stul_id, "tym1": [g[0], g[2]], "tym2": [g[1], g[3]], "odehrano": False})
            zapasy.append({"blok": 1, "stul": stul_id, "tym1": [g[0], g[1]], "tym2": [g[2], g[3]], "odehrano": False})

        g3 = [serazeni[0], serazeni[2], serazeni[4], serazeni[6]]
        g4 = [serazeni[1], serazeni[3], serazeni[5], serazeni[7]]
        for stul_id, g in [(1, g3), (2, g4)]:
            zapasy.append({"blok": 2, "stul": stul_id, "tym1": [g[0], g[3]], "tym2": [g[1], g[2]], "odehrano": False})
            zapasy.append({"blok": 2, "stul": stul_id, "tym1": [g[0], g[2]], "tym2": [g[1], g[3]], "odehrano": False})
    else:
        g = serazeni[:4]
        zapasy.append({"blok": 1, "stul": 1, "tym1": [g[0], g[3]], "tym2": [g[1], g[2]], "odehrano": False})
        zapasy.append({"blok": 1, "stul": 1, "tym1": [g[0], g[2]], "tym2": [g[1], g[3]], "odehrano": False})
        zapasy.append({"blok": 1, "stul": 1, "tym1": [g[0], g[1]], "tym2": [g[2], g[3]], "odehrano": False})

    return zapasy

# --- HLAVNÍ STRÁNKA ---
st.title("🏓 Ping Pong Dobrovíz")

tab1, tab2, tab3, tab4 = st.tabs(["📋 Přihlášení", "⚔️ Zápasy na stolech", "🏆 Roční žebříčky", "🛠️ Správa & Editace"])

# TAB 1: PŘIHLÁŠENÍ
with tab1:
    datum_session = st.date_input("Datum hracího dne:", date.today())
    st.subheader("Přihlášení hráčů")
    
    cols = st.columns(3)
    for idx, hrac in enumerate(VSECHNI_HRACI):
        col = cols[idx % 3]
        je_prihlasen = st.session_state.prihlaseni[hrac]
        btn_label = f"✅ {hrac}" if je_prihlasen else f"❌ {hrac}"
        if col.button(btn_label, key=f"btn_{hrac}", use_container_width=True):
            st.session_state.prihlaseni[hrac] = not je_prihlasen
            st.rerun()

    pritomni = [h for h, stav in st.session_state.prihlaseni.items() if stav]
    st.info(f"Přihlášeno: **{len(pritomni)}** ({', '.join(pritomni)})")

    if len(pritomni) >= 4:
        if st.button("🎲 Vygenerovat zápasy", type="primary", use_container_width=True):
            st.session_state.dnesni_zapasy = generuj_vyrovnane_zapasy(pritomni)
            st.success("Zápasy vygenerovány podle úspěšnosti z žebříčku!")

# TAB 2: ZÁPASY
with tab2:
    if not st.session_state.dnesni_zapasy:
        st.warning("Zatím nejsou vygenerovány žádné zápasy.")
    else:
        col_s1, col_s2 = st.columns(2)
        
        def vykresli_stul_ui(stul_id, container):
            with container:
                st.subheader(f"🟢 Stůl {stul_id}")
                stul_zapasy = [z for z in st.session_state.dnesni_zapasy if z["stul"] == stul_id]
                
                for idx, z in enumerate(stul_zapasy):
                    t1_s = f"{z['tym1'][0]} + {z['tym1'][1]}"
                    t2_s = f"{z['tym2'][0]} + {z['tym2'][1]}"
                    
                    with st.expander(f"Blok {z['blok']} - Zápas {idx+1}: {t1_s} vs {t2_s}", expanded=not z["odehrano"]):
                        if z["odehrano"]:
                            st.success(f"Výsledek: **{z.get('skore1', 0)} : {z.get('skore2', 0)}**")
                        else:
                            c1, c2 = st.columns(2)
                            s1 = c1.number_input(f"Sety {z['tym1'][0]}", 0, 3, 0, key=f"s1_{stul_id}_{idx}")
                            s2 = c2.number_input(f"Sety {z['tym2'][0]}", 0, 3, 0, key=f"s2_{stul_id}_{idx}")
                            
                            if st.button("Uložit výsledek", key=f"btn_{stul_id}_{idx}"):
                                if s1 == 3 or s2 == 3:
                                    z["skore1"] = s1
                                    z["skore2"] = s2
                                    z["odehrano"] = True
                                    
                                    záznam = {
                                        "id": len(st.session_state.odehrane_zapasy) + 1,
                                        "datum": str(datum_session),
                                        "stul": stul_id,
                                        "tym1": z["tym1"],
                                        "tym2": z["tym2"],
                                        "skore1": s1,
                                        "skore2": s2
                                    }
                                    st.session_state.odehrane_zapasy.append(záznam)
                                    uloz_databazi(st.session_state.odehrane_zapasy)
                                    st.success("Výsledek uložen!")
                                    st.rerun()
                                else:
                                    st.error("Hraje se na 3 vítězné sety!")

        vykresli_stul_ui(1, col_s1)
        vykresli_stul_ui(2, col_s2)

# TAB 3: ŽEBRÍČKY
with tab3:
    jednotlivci_stat, dvojice_stat = spocitej_statistiky()
    
    st.subheader("🏆 Celoroční žebříček jednotlivců (Historie z tabulky + Nové zápasy)")
    data_j = []
    for hrac, st_ in jednotlivci_stat.items():
        if st_["Odehráno"] > 0:
            usp = round((st_["Výhry"] / st_["Odehráno"]) * 100, 1)
            data_j.append({"Hráč": hrac, "Celkem zápasů": st_["Odehráno"], "Výhry": st_["Výhry"], "Prohry": st_["Prohry"], "Sety": f"{st_['Sety+']}:{st_['Sety-']}", "Úspěšnost (%)": usp})
    
    if data_j:
        st.dataframe(pd.DataFrame(data_j).sort_values(by=["Výhry", "Úspěšnost (%)"], ascending=False), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("👥 Žebříček dvojic (Z odehraných aplikací)")
    data_d = []
    for dvojice_nazev, st_ in dvojice_stat.items():
        if st_["Odehráno"] > 0:
            usp = round((st_["Výhry"] / st_["Odehráno"]) * 100, 1)
            data_d.append({"Dvojice": dvojice_nazev, "Odehráno": st_["Odehráno"], "Výhry": st_["Výhry"], "Prohry": st_["Prohry"], "Sety": f"{st_['Sety+']}:{st_['Sety-']}", "Úspěšnost (%)": usp})
    
    if data_d:
        st.dataframe(pd.DataFrame(data_d).sort_values(by=["Výhry", "Úspěšnost (%)"], ascending=False), use_container_width=True, hide_index=True)
    else:
        st.info("Zatím nebyl odehrán žádný nový zápas dvojic v aplikaci.")

# TAB 4: SPRÁVA A EDITACE (MAZÁNÍ & ÚPRAVA CHYB)
with tab4:
    st.subheader("🛠️ Správa uložených zápasů")
    
    # 1. Tlačítko pro kompletní smazání cvičných dat
    if st.button("🗑️ SMAZAT VŠECHNA CVIČNÁ DATA", type="primary"):
        st.session_state.odehrane_zapasy = []
        uloz_databazi([])
        st.success("Všechna cvičná data byla smazána! Žebříček je nyní resetován na čistá historická data.")
        st.rerun()

    st.markdown("---")
    st.write("### Seznam odehraných zápasů (možnost smazat konkrétní zápas):")
    
    if not st.session_state.odehrane_zapasy:
        st.info("Databáze nových zápasů je prázdná.")
    else:
        for idx, z in enumerate(st.session_state.odehrane_zapasy):
            c1, c2, c3 = st.columns([3, 2, 1])
            c1.write(f"**{z['datum']}** | {z['tym1'][0]}+{z['tym1'][1]} vs {z['tym2'][0]}+{z['tym2'][1]}")
            c2.write(f"Skóre: **{z['skore1']} : {z['skore2']}**")
            
            if c3.button("❌ Smazat zápas", key=f"del_{idx}"):
                st.session_state.odehrane_zapasy.pop(idx)
                uloz_databazi(st.session_state.odehrane_zapasy)
                st.success("Zápas smazán!")
                st.rerun()