import streamlit as st
import pandas as pd
import json
import os
from datetime import date

st.set_page_config(page_title="Ping Pong Dobrovíz", layout="centered", page_icon="🏓")

# CSS PRO MOBILE-FIRST (Extra velká tlačítka a čisté zobrazení na výšku)
st.markdown("""
<style>
    html, body, [class*="css"] { 
        font-size: 22px !important; 
    }
    div.stButton > button { 
        font-size: 26px !important; 
        font-weight: bold !important; 
        padding: 18px 20px !important; 
        border-radius: 12px !important; 
        margin-bottom: 10px !important;
        width: 100% !important;
    }
    button[data-baseweb="tab"] { 
        font-size: 22px !important; 
        font-weight: bold !important; 
        padding: 12px 10px !important; 
    }
    div[data-testid="stDataFrame"] { 
        font-size: 18px !important; 
    }
    input { 
        font-size: 26px !important; 
        font-weight: bold !important; 
        text-align: center !important;
    }
</style>
""", unsafe_allow_html=True)

DB_FILE = "databaze_pingpong.json"
CENA_ZA_SESSION = 30  # Kč za osobu

# HISTORICKÁ DATA Z TABULKY (Aktualizováno)
HISTORIE_TABULKA = {
    "Sofka": {"Výhry": 79, "Účast": 23},
    "Jindra": {"Výhry": 78, "Účast": 21},
    "Tibor": {"Výhry": 74, "Účast": 19},
    "Pavel": {"Výhry": 69, "Účast": 21},
    "Jarda": {"Výhry": 63, "Účast": 18},
    "Vláďa": {"Výhry": 55, "Účast": 19},
    "Jirka": {"Výhry": 33, "Účast": 22},
    "Petr": {"Výhry": 23, "Účast": 7},
    "Miro": {"Výhry": 5, "Účast": 4},
    "Franta": {"Výhry": 4, "Účast": 1},
    "Fred": {"Výhry": 1, "Účast": 2},
    "Jirka S.": {"Výhry": 0, "Účast": 0},
    "Mirek": {"Výhry": 0, "Účast": 0},
    "Petr W.": {"Výhry": 0, "Účast": 0},
    "Přespolní": {"Výhry": 0, "Účast": 0}
}

HISTORIE_DNY = [
    {"Datum": "07.01.2025", "Hráčů": 8, "Vybráno (Kč)": 240},
    {"Datum": "14.01.2025", "Hráčů": 9, "Vybráno (Kč)": 270},
    {"Datum": "21.01.2025", "Hráčů": 5, "Vybráno (Kč)": 150},
    {"Datum": "28.01.2025", "Hráčů": 6, "Vybráno (Kč)": 180},
    {"Datum": "04.02.2025", "Hráčů": 7, "Vybráno (Kč)": 210},
    {"Datum": "11.02.2025", "Hráčů": 6, "Vybráno (Kč)": 180},
    {"Datum": "25.02.2025", "Hráčů": 4, "Vybráno (Kč)": 120},
    {"Datum": "04.03.2025", "Hráčů": 4, "Vybráno (Kč)": 120},
    {"Datum": "11.03.2025", "Hráčů": 5, "Vybráno (Kč)": 150},
    {"Datum": "18.03.2025", "Hráčů": 5, "Vybráno (Kč)": 150},
    {"Datum": "25.03.2025", "Hráčů": 5, "Vybráno (Kč)": 150},
    {"Datum": "01.04.2025", "Hráčů": 6, "Vybráno (Kč)": 180},
    {"Datum": "08.04.2025", "Hráčů": 6, "Vybráno (Kč)": 180},
    {"Datum": "15.04.2025", "Hráčů": 8, "Vybráno (Kč)": 240},
    {"Datum": "22.04.2025", "Hráčů": 7, "Vybráno (Kč)": 210},
    {"Datum": "29.04.2025", "Hráčů": 4, "Vybráno (Kč)": 120},
    {"Datum": "06.05.2025", "Hráčů": 4, "Vybráno (Kč)": 120},
    {"Datum": "13.05.2025", "Hráčů": 6, "Vybráno (Kč)": 180},
    {"Datum": "27.05.2025", "Hráčů": 5, "Vybráno (Kč)": 150},
    {"Datum": "03.06.2025", "Hráčů": 7, "Vybráno (Kč)": 210},
    {"Datum": "10.06.2025", "Hráčů": 8, "Vybráno (Kč)": 240},
    {"Datum": "17.06.2025", "Hráčů": 7, "Vybráno (Kč)": 210},
    {"Datum": "24.06.2025", "Hráčů": 8, "Vybráno (Kč)": 240},
    {"Datum": "19.08.2025", "Hráčů": 4, "Vybráno (Kč)": 120},
    {"Datum": "26.08.2025", "Hráčů": 8, "Vybráno (Kč)": 240},
    {"Datum": "02.09.2025", "Hráčů": 6, "Vybráno (Kč)": 210}
]

VSECHNI_HRACI = list(HISTORIE_TABULKA.keys())

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

def spocitej_statistiky():
    jednotlivci = {h: {
        "Odehráno": HISTORIE_TABULKA[h]["Účast"], 
        "Výhry": HISTORIE_TABULKA[h]["Výhry"], 
        "Prohry": HISTORIE_TABULKA[h]["Účast"] - HISTORIE_TABULKA[h]["Výhry"], 
        "Sety+": 0, "Sety-": 0,
        "Vybráno": HISTORIE_TABULKA[h]["Účast"] * CENA_ZA_SESSION
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

# SEŘAZENÍ HRÁČŮ PODLE ÚČASTI
jednotlivci_stat, dvojice_stat = spocitej_statistiky()
HRACI_DLE_UCASTI = sorted(
    VSECHNI_HRACI, 
    key=lambda h: jednotlivci_stat[h]["Odehráno"], 
    reverse=True
)

st.title("🏓 Ping Pong Dobrovíz")

tab1, tab2, tab3, tab4 = st.tabs(["📋 Přihlášení", "⚔️ Zápasy", "🏆 Žebříčky", "🛠️ Správa"])

# TAB 1: PŘIHLÁŠENÍ (Jediný sloupec pod sebou)
with tab1:
    datum_session = st.date_input("Datum hracího dne:", date.today())
    st.subheader("Přihlášení hráčů")
    st.caption("Seřazeno od nejčastějších účastníků:")
    
    for hrac in HRACI_DLE_UCASTI:
        je_prihlasen = st.session_state.prihlaseni[hrac]
        ucast_count = jednotlivci_stat[hrac]["Odehráno"]
        
        btn_label = f"✅ {hrac} ({ucast_count}x)" if je_prihlasen else f"❌ {hrac} ({ucast_count}x)"
        
        if st.button(btn_label, key=f"btn_{hrac}", use_container_width=True):
            st.session_state.prihlaseni[hrac] = not je_prihlasen
            st.rerun()

    pritomni = [h for h, stav in st.session_state.prihlaseni.items() if stav]
    pocet = len(pritomni)
    dnes_vybrano = pocet * CENA_ZA_SESSION

    st.markdown("---")
    st.success(f"💰 **Dnes vybráno: {dnes_vybrano} Kč** ({pocet} hráčů × 30 Kč)")
    st.info(f"Přihlášeno: **{pocet}** ({', '.join(pritomni)})")

    if pocet >= 4:
        if st.button("🎲 Vygenerovat zápasy", type="primary", use_container_width=True):
            st.session_state.dnesni_zapasy = generuj_vyrovnane_zapasy(pritomni)
            st.success("Zápasy vygenerovány!")

# TAB 2: ZÁPASY
with tab2:
    if not st.session_state.dnesni_zapasy:
        st.warning("Zatím nejsou vygenerovány žádné zápasy.")
    else:
        def vykresli_stul_ui(stul_id, nazev_stolu):
            st.subheader(nazev_stolu)
            stul_zapasy = [z for z in st.session_state.dnesni_zapasy if z["stul"] == stul_id]
            
            for idx, z in enumerate(stul_zapasy):
                t1_s = f"{z['tym1'][0]} + {z['tym1'][1]}"
                t2_s = f"{z['tym2'][0]} + {z['tym2'][1]}"
                
                with st.expander(f"Zápas {idx+1}: {t1_s} vs {t2_s}", expanded=not z["odehrano"]):
                    if z["odehrano"]:
                        st.success(f"Výsledek: **{z.get('skore1', 0)} : {z.get('skore2', 0)}**")
                    else:
                        c1, c2 = st.columns(2)
                        s1 = c1.number_input(f"Sety {z['tym1'][0]}", 0, 3, 0, key=f"s1_{stul_id}_{idx}")
                        s2 = c2.number_input(f"Sety {z['tym2'][0]}", 0, 3, 0, key=f"s2_{stul_id}_{idx}")
                        
                        if st.button("Uložit výsledek", key=f"btn_{stul_id}_{idx}", use_container_width=True):
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

        vykresli_stul_ui(1, "🟢 Stůl 1")
        st.markdown("---")
        vykresli_stul_ui(2, "🔵 Stůl 2")

# TAB 3: ŽEBRÍČKY
with tab3:
    celkem_vybrano = sum(st_["Vybráno"] for st_ in jednotlivci_stat.values())
    st.metric(label="💰 CELKEM VYBRÁNO V SEZÓNĚ", value=f"{celkem_vybrano} Kč")

    st.subheader("🏆 Celoroční žebříček jednotlivců")
    data_j = []
    for hrac, st_ in jednotlivci_stat.items():
        if st_["Odehráno"] > 0:
            usp = round((st_["Výhry"] / st_["Odehráno"]) * 100, 1)
            data_j.append({
                "Hráč": hrac, 
                "Účastí": st_["Odehráno"], 
                "Výhry": st_["Výhry"], 
                "Prohry": st_["Prohry"], 
                "Úspěšnost (%)": usp,
                "Vybráno (Kč)": st_["Vybráno"]
            })
    
    if data_j:
        st.dataframe(pd.DataFrame(data_j).sort_values(by=["Výhry", "Úspěšnost (%)"], ascending=False), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("👥 Žebříček dvojic")
    data_d = []
    for dvojice_nazev, st_ in dvojice_stat.items():
        if st_["Odehráno"] > 0:
            usp = round((st_["Výhry"] / st_["Odehráno"]) * 100, 1)
            data_d.append({"Dvojice": dvojice_nazev, "Odehráno": st_["Odehráno"], "Výhry": st_["Výhry"], "Prohry": st_["Prohry"], "Úspěšnost (%)": usp})
    
    if data_d:
        st.dataframe(pd.DataFrame(data_d).sort_values(by=["Výhry", "Úspěšnost (%)"], ascending=False), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("📅 Přehled vybraných peněz po střechách")
    
    prehled_dny = list(HISTORIE_DNY)
    nove_dny = {}
    for z in st.session_state.odehrane_zapasy:
        d = z["datum"]
        if d not in nove_dny:
            nove_dny[d] = set()
        nove_dny[d].update(z["tym1"])
        nove_dny[d].update(z["tym2"])

    for d, hraci in nove_dny.items():
        pocet_h = len(hraci)
        prehled_dny.append({
            "Datum": d,
            "Hráčů": pocet_h,
            "Vybráno (Kč)": pocet_h * CENA_ZA_SESSION
        })

    df_dny = pd.DataFrame(prehled_dny)
    st.dataframe(df_dny, use_container_width=True, hide_index=True)

# TAB 4: SPRÁVA
with tab4:
    st.subheader("🛠️ Správa zápasů")
    
    if st.button("🗑️ SMAZAT VŠECHNA CVIČNÁ DATA", type="primary", use_container_width=True):
        st.session_state.odehrane_zapasy = []
        uloz_databazi([])
        st.success("Cvičná data smazána!")
        st.rerun()

    st.markdown("---")
    if st.session_state.odehrane_zapasy:
        for idx, z in enumerate(st.session_state.odehrane_zapasy):
            st.write(f"**{z['datum']}** | {z['tym1'][0]}+{z['tym1'][1]} vs {z['tym2'][0]}+{z['tym2'][1]} ({z['skore1']}:{z['skore2']})")
            if st.button("❌ Smazat zápas", key=f"del_{idx}", use_container_width=True):
                st.session_state.odehrane_zapasy.pop(idx)
                uloz_databazi(st.session_state.odehrane_zapasy)
                st.rerun()
