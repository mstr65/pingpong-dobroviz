import streamlit as st
import pandas as pd
import json
import os
from datetime import date

st.set_page_config(page_title="Ping Pong Dobrovíz", layout="wide", page_icon="🏓")

DB_FILE = "databaze_pingpong.json"

# Seznam hráčů
VSECHNI_HRACI = [
    "Pavel", "Jindra", "Vláďa", "Petr", "Sofka", 
    "Tibor", "Jarda", "Jirka", "Mirek", "Franta", 
    "Fred", "Jirka S.", "Miro", "Petr W.", "Přespolní"
]

# --- NAČÍTÁNÍ A UKLÁDÁNÍ DAT (Trvalá databáze) ---
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

# --- POMOCNÉ FUNKCE PRO VÝPOČET ŽEBŘÍČKŮ ---
def spocitej_statistiky():
    jednotlivci = {h: {"Odehráno": 0, "Výhry": 0, "Prohry": 0, "Sety+": 0, "Sety-": 0} for h in VSECHNI_HRACI}
    dvojice = {}

    for z in st.session_state.odehrane_zapasy:
        s1, s2 = z["skore1"], z["skore2"]
        t1, t2 = z["tym1"], z["tym2"]
        
        # Klíč pro dvojici (abecedně seřazený)
        p1_key = " + ".join(sorted(t1))
        p2_key = " + ".join(sorted(t2))

        if p1_key not in dvojice:
            dvojice[p1_key] = {"Odehráno": 0, "Výhry": 0, "Prohry": 0, "Sety+": 0, "Sety-": 0}
        if p2_key not in dvojice:
            dvojice[p2_key] = {"Odehráno": 0, "Výhry": 0, "Prohry": 0, "Sety+": 0, "Sety-": 0}

        # Aktualizace Jednotlivců
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

        # Aktualizace Dvojic
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

# --- ALGORITMUS PRO VYROVNANÉ SESTAVENÍ DVOJIC ---
def generuj_vyrovnane_zapasy(pritomni_hraci):
    jednotlivci, _ = spocitej_statistiky()
    
    # Seřadit přítomné hráče podle jejich celoroční úspěšnosti
    def ziskej_uspesnost(hrac):
        st = jednotlivci[hrac]
        return (st["Výhry"] / st["Odehráno"]) if st["Odehráno"] > 0 else 0.5

    serazeni = sorted(pritomni_hraci, key=ziskej_uspesnost, reverse=True)
    
    zapasy = []
    
    if len(serazeni) >= 8:
        # 8 hráčů: Vytvořit 2 vyrovnané čtveřice
        # Čtveřice A: 1., 4., 5., 8. hráč z žebříčku
        # Čtveřice B: 2., 3., 6., 7. hráč z žebříčku
        g1 = [serazeni[0], serazeni[3], serazeni[4], serazeni[7]]
        g2 = [serazeni[1], serazeni[2], serazeni[5], serazeni[6]]
        
        # BLOK 1 (Vyrovnané zápasy na začátek: 1.+8. vs 4.+5. atd.)
        for stul_id, g in [(1, g1), (2, g2)]:
            zapasy.append({"blok": 1, "stul": stul_id, "tym1": [g[0], g[3]], "tym2": [g[1], g[2]], "odehrano": False})
            zapasy.append({"blok": 1, "stul": stul_id, "tym1": [g[0], g[2]], "tym2": [g[1], g[3]], "odehrano": False})
            zapasy.append({"blok": 1, "stul": stul_id, "tym1": [g[0], g[1]], "tym2": [g[2], g[3]], "odehrano": False})

        # BLOK 2 (Promíchání stolu – rotace zbývajících kombinací)
        g3 = [serazeni[0], serazeni[2], serazeni[4], serazeni[6]]
        g4 = [serazeni[1], serazeni[3], serazeni[5], serazeni[7]]
        for stul_id, g in [(1, g3), (2, g4)]:
            zapasy.append({"blok": 2, "stul": stul_id, "tym1": [g[0], g[3]], "tym2": [g[1], g[2]], "odehrano": False})
            zapasy.append({"blok": 2, "stul": stul_id, "tym1": [g[0], g[2]], "tym2": [g[1], g[3]], "odehrano": False})

    else:
        # Pro 4–7 hráčů: Standardní rotace čtveřice
        g = serazeni[:4]
        zapasy.append({"blok": 1, "stul": 1, "tym1": [g[0], g[3]], "tym2": [g[1], g[2]], "odehrano": False})
        zapasy.append({"blok": 1, "stul": 1, "tym1": [g[0], g[2]], "tym2": [g[1], g[3]], "odehrano": False})
        zapasy.append({"blok": 1, "stul": 1, "tym1": [g[0], g[1]], "tym2": [g[2], g[3]], "odehrano": False})

    return zapasy

# --- HLAVNÍ ROZHRANÍ APLIKACE ---
st.title("🏓 Ping Pong Dobrovíz")

tab1, tab2, tab3 = st.tabs(["📋 Přihlášení & Generování", "⚔️ Zápasy na stolech", "🏆 Roční žebříčky"])

# --- ZÁLOŽKA 1: PŘIHLÁŠENÍ ---
with tab1:
    datum_session = st.date_input("Datum hracího dne:", date.today())
    st.subheader("Přihlášení hráčů na středu")
    
    cols = st.columns(3)
    for idx, hrac in enumerate(VSECHNI_HRACI):
        col = cols[idx % 3]
        je_prihlasen = st.session_state.prihlaseni[hrac]
        btn_label = f"✅ {hrac}" if je_prihlasen else f"❌ {hrac}"
        if col.button(btn_label, key=f"btn_{hrac}", use_container_width=True):
            st.session_state.prihlaseni[hrac] = not je_prihlasen
            st.rerun()

    pritomni = [h for h, stav in st.session_state.prihlaseni.items() if stav]
    st.info(f"Přihlášeno hráčů: **{len(pritomni)}** ({', '.join(pritomni)})")

    if len(pritomni) >= 4:
        if st.button("🎲 Vygenerovat vyrovnané zápasy", type="primary", use_container_width=True):
            st.session_state.dnesni_zapasy = generuj_vyrovnane_zapasy(pritomni)
            st.success("Rozpis vytvořen! Nejvyrovnanější zápasy (1.+8. vs 4.+5.) jsou zařazeny na začátek.")

# --- ZÁLOŽKA 2: ZÁPASY NA STOLECH ---
with tab2:
    if not st.session_state.dnesni_zapasy:
        st.warning("Nejdříve přihlaste hráče a vygenerujte zápasy na první záložce.")
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
                                    
                                    # Uložení do celoroční databáze
                                    záznam = {
                                        "datum": str(datum_session),
                                        "stul": stul_id,
                                        "tym1": z["tym1"],
                                        "tym2": z["tym2"],
                                        "skore1": s1,
                                        "skore2": s2
                                    }
                                    st.session_state.odehrane_zapasy.append(záznam)
                                    uloz_databazi(st.session_state.odehrane_zapasy)
                                    st.success("Uloženo do celoročních statistik!")
                                    st.rerun()
                                else:
                                    st.error("Hraje se na 3 vítězné sety!")

        vykresli_stul_ui(1, col_s1)
        vykresli_stul_ui(2, col_s2)

# --- ZÁLOŽKA 3: ROČNÍ ŽEBŘÍČKY ---
with tab3:
    jednotlivci_stat, dvojice_stat = spocitej_statistiky()
    
    st.subheader("🏆 Celoroční žebříček jednotlivců")
    data_j = []
    for hrac, st_ in jednotlivci_stat.items():
        if st_["Odehráno"] > 0:
            usp = round((st_["Výhry"] / st_["Odehráno"]) * 100, 1)
            data_j.append({"Hráč": hrac, "Odehráno": st_["Odehráno"], "Výhry": st_["Výhry"], "Prohry": st_["Prohry"], "Sety": f"{st_['Sety+']}:{st_['Sety-']}", "Úspěšnost (%)": usp})
    
    if data_j:
        st.dataframe(pd.DataFrame(data_j).sort_values(by=["Výhry", "Úspěšnost (%)"], ascending=False), use_container_width=True, hide_index=True)
    else:
        st.info("Zatím nejsou odehrány žádné zápasy.")

    st.markdown("---")
    st.subheader("👥 Celoroční žebříček dvojic")
    data_d = []
    for dvojice_nazev, st_ in dvojice_stat.items():
        if st_["Odehráno"] > 0:
            usp = round((st_["Výhry"] / st_["Odehráno"]) * 100, 1)
            data_d.append({"Dvojice": dvojice_nazev, "Odehráno": st_["Odehráno"], "Výhry": st_["Výhry"], "Prohry": st_["Prohry"], "Sety": f"{st_['Sety+']}:{st_['Sety-']}", "Úspěšnost (%)": usp})
    
    if data_d:
        st.dataframe(pd.DataFrame(data_d).sort_values(by=["Výhry", "Úspěšnost (%)"], ascending=False), use_container_width=True, hide_index=True)
    else:
        st.info("Zatím nebyl odehrán žádný zápas dvojic.")