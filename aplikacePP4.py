import json
import os
from datetime import date, timedelta
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Ping Pong Dobrovíz", layout="centered", page_icon="🏓"
)

# EXTRA VELKÉ PÍSMO PRO TABLETY (BEZ BRÝLÍ)
st.markdown(
    """
<style>
    html, body, [class*="css"], div, p, span { 
        font-size: 26px !important; 
        line-height: 1.4 !important;
    }
    div.stButton > button { 
        font-size: 30px !important; 
        font-weight: bold !important; 
        padding: 22px 24px !important; 
        border-radius: 16px !important; 
        margin-bottom: 12px !important;
        width: 100% !important;
    }
    button[data-baseweb="tab"] { 
        font-size: 26px !important; 
        font-weight: bold !important; 
        padding: 16px 12px !important; 
    }
    div[data-testid="stDataFrame"] { 
        font-size: 22px !important; 
    }
    input { 
        font-size: 32px !important; 
        font-weight: bold !important; 
        text-align: center !important;
        height: 60px !important;
    }
</style>
""",
    unsafe_allow_html=True,
)

DB_FILE = "databaze_pingpong.json"
CENA_ZA_SESSION = 30  # Kč za osobu

DEFAULT_HRACI = [
    "Sofka",
    "Jindra",
    "Tibor",
    "Pavel",
    "Jarda",
    "Vláďa",
    "Jirka",
    "Petr",
    "Miro",
    "Franta",
    "Fred",
    "Jirka S.",
    "Mirek",
    "Petr W.",
    "Přespolní",
]

HISTORIE_PODLE_ROKU = {
    2026: {
        "Sofka": {"Výhry": 79, "Středy": 23},
        "Jindra": {"Výhry": 78, "Středy": 21},
        "Tibor": {"Výhry": 74, "Středy": 19},
        "Pavel": {"Výhry": 69, "Středy": 21},
        "Jarda": {"Výhry": 63, "Středy": 18},
        "Vláďa": {"Výhry": 55, "Středy": 19},
        "Jirka": {"Výhry": 33, "Středy": 22},
        "Petr": {"Výhry": 23, "Středy": 7},
        "Miro": {"Výhry": 5, "Středy": 4},
        "Franta": {"Výhry": 4, "Středy": 1},
        "Fred": {"Výhry": 1, "Středy": 2},
    },
    2025: {
        "Pavel": {"Výhry": 114, "Středy": 37},
        "Jindra": {"Výhry": 110, "Středy": 32},
        "Tibor": {"Výhry": 99, "Středy": 30},
        "Vláďa": {"Výhry": 97, "Středy": 37},
        "Petr": {"Výhry": 92, "Středy": 27},
        "Sofka": {"Výhry": 73, "Středy": 24},
        "Jarda": {"Výhry": 45, "Středy": 14},
        "Jirka": {"Výhry": 34, "Středy": 28},
        "Mirek": {"Výhry": 15, "Středy": 6},
        "Miro": {"Výhry": 8, "Středy": 7},
        "Franta": {"Výhry": 5, "Středy": 2},
        "Jirka S.": {"Výhry": 4, "Středy": 2},
    },
    2024: {
        "Petr": {"Výhry": 165, "Středy": 41},
        "Pavel": {"Výhry": 144, "Středy": 47},
        "Vláďa": {"Výhry": 128, "Středy": 44},
        "Tibor": {"Výhry": 118, "Středy": 38},
        "Sofka": {"Výhry": 98, "Středy": 36},
        "Jindra": {"Výhry": 87, "Středy": 29},
        "Jarda": {"Výhry": 84, "Středy": 20},
        "Mirek": {"Výhry": 41, "Středy": 15},
        "Jirka": {"Výhry": 32, "Středy": 32},
    },
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
    {"Datum": "02.09.2025", "Hráčů": 6, "Vybráno (Kč)": 210},
]


def nacti_databazi():
  if os.path.exists(DB_FILE):
    with open(DB_FILE, "r", encoding="utf-8") as f:
      data = json.load(f)
      if isinstance(data, dict):
        return (
            data.get("zapasy", []),
            data.get("hraci", DEFAULT_HRACI),
            data.get("vydaje", []),
        )
      else:
        return data, DEFAULT_HRACI, []
  return [], DEFAULT_HRACI, []


def uloz_databazi(zapasy, hraci, vydaje):
  with open(DB_FILE, "w", encoding="utf-8") as f:
    json.dump(
        {"zapasy": zapasy, "hraci": hraci, "vydaje": vydaje},
        f,
        ensure_ascii=False,
        indent=4,
    )


if (
    "odehrane_zapasy" not in st.session_state
    or "vsechni_hraci" not in st.session_state
):
  zapasy, hraci, vydaje = nacti_databazi()
  st.session_state.odehrane_zapasy = zapasy
  st.session_state.vsechni_hraci = hraci
  st.session_state.vydaje = vydaje

if "dnesni_zapasy" not in st.session_state:
  st.session_state.dnesni_zapasy = []

if "prihlaseni" not in st.session_state:
  st.session_state.prihlaseni = {
      h: False for h in st.session_state.vsechni_hraci
  }


def spocitej_statistiky(zvoleny_rok):
  historie = HISTORIE_PODLE_ROKU.get(zvoleny_rok, {})

  jednotlivci = {
      h: {
          "Středy": historie.get(h, {}).get("Středy", 0),
          "Výhry": historie.get(h, {}).get("Výhry", 0),
          "Prohry_App": 0,
          "Vybráno": historie.get(h, {}).get("Středy", 0) * CENA_ZA_SESSION,
      }
      for h in st.session_state.vsechni_hraci
  }

  dvojice = {}
  stredy_mnozina = {h: set() for h in st.session_state.vsechni_hraci}

  for z in st.session_state.odehrane_zapasy:
    rok_zapasu = (
        int(z["datum"].split("-")[0])
        if "-" in z["datum"]
        else int(z["datum"].split(".")[-1])
    )
    if rok_zapasu != zvoleny_rok:
      continue

    s1, s2 = z["skore1"], z["skore2"]
    t1, t2 = z["tym1"], z["tym2"]
    d = z["datum"]

    p1_key = " + ".join(sorted(t1))
    p2_key = " + ".join(sorted(t2))

    if p1_key not in dvojice:
      dvojice[p1_key] = {"Odehráno": 0, "Výhry": 0, "Prohry": 0}
    if p2_key not in dvojice:
      dvojice[p2_key] = {"Odehráno": 0, "Výhry": 0, "Prohry": 0}

    for h in t1:
      if h in jednotlivci:
        stredy_mnozina[h].add(d)
        if s1 > s2:
          jednotlivci[h]["Výhry"] += 1
        else:
          jednotlivci[h]["Prohry_App"] += 1

    for h in t2:
      if h in jednotlivci:
        stredy_mnozina[h].add(d)
        if s2 > s1:
          jednotlivci[h]["Výhry"] += 1
        else:
          jednotlivci[h]["Prohry_App"] += 1

    dvojice[p1_key]["Odehráno"] += 1
    dvojice[p2_key]["Odehráno"] += 1
    if s1 > s2:
      dvojice[p1_key]["Výhry"] += 1
      dvojice[p2_key]["Prohry"] += 1
    else:
      dvojice[p2_key]["Výhry"] += 1
      dvojice[p1_key]["Prohry"] += 1

  for h in st.session_state.vsechni_hraci:
    nove_stredy = len(stredy_mnozina[h])
    jednotlivci[h]["Středy"] += nove_stredy
    jednotlivci[h]["Vybráno"] = jednotlivci[h]["Středy"] * CENA_ZA_SESSION

  return jednotlivci, dvojice


def generuj_kolo_zapasu(pritomni_hraci, zvoleny_rok, cislo_bloku):
  # 1. Spočítat, kolik zápasů DNEŠNÍ SESSION už jednotliví přítomní hráči odehráli
  odehrano_dnes = {h: 0 for h in pritomni_hraci}
  for z in st.session_state.dnesni_zapasy:
    for h in z["tym1"] + z["tym2"]:
      if h in odehrano_dnes:
        odehrano_dnes[h] += 1

  # 2. Celoroční úspěšnost pro vyrovnané namíchání týmů
  jednotlivci, _ = spocitej_statistiky(zvoleny_rok)

  def ziskej_prumer(hrac):
    st_ = jednotlivci[hrac]
    return (st_["Výhry"] / st_["Středy"]) if st_["Středy"] > 0 else 0.5

  # Seřazení hráčů:
  # 1) Nejprve ti, kteří DNES hrál NEJMÉNĚKRÁT (priorita pro odpočaté)
  # 2) Dále podle celoročního průměru (pro vyrovnanost)
  serazeni = sorted(
      pritomni_hraci, key=lambda h: (odehrano_dnes[h], -ziskej_prumer(h))
  )

  pocet = len(serazeni)
  zapasy = []

  if pocet >= 8:
    g1 = [serazeni[0], serazeni[3], serazeni[4], serazeni[7]]
    g2 = [serazeni[1], serazeni[2], serazeni[5], serazeni[6]]

    for stul_id, g in [(1, g1), (2, g2)]:
      zapasy.append({
          "blok": cislo_bloku,
          "stul": stul_id,
          "tym1": [g[0], g[3]],
          "tym2": [g[1], g[2]],
          "odehrano": False,
      })
      zapasy.append({
          "blok": cislo_bloku,
          "stul": stul_id,
          "tym1": [g[0], g[2]],
          "tym2": [g[1], g[3]],
          "odehrano": False,
      })
      zapasy.append({
          "blok": cislo_bloku,
          "stul": stul_id,
          "tym1": [g[0], g[1]],
          "tym2": [g[2], g[3]],
          "odehrano": False,
      })

  elif pocet == 4:
    g = serazeni
    zapasy.append({
        "blok": cislo_bloku,
        "stul": 1,
        "tym1": [g[0], g[3]],
        "tym2": [g[1], g[2]],
        "odehrano": False,
    })
    zapasy.append({
        "blok": cislo_bloku,
        "stul": 1,
        "tym1": [g[0], g[2]],
        "tym2": [g[1], g[3]],
        "odehrano": False,
    })
    zapasy.append({
        "blok": cislo_bloku,
        "stul": 1,
        "tym1": [g[0], g[1]],
        "tym2": [g[2], g[3]],
        "odehrano": False,
    })

  elif pocet in [5, 6, 7]:
    # První 4 hráči v pořadí (ti co nehráli + vyrovnání) jdou na Stůl 1
    stul1_hraci = serazeni[:4]
    stul2_hraci = serazeni[4:]

    g = stul1_hraci
    zapasy.append({
        "blok": cislo_bloku,
        "stul": 1,
        "tym1": [g[0], g[3]],
        "tym2": [g[1], g[2]],
        "odehrano": False,
    })
    zapasy.append({
        "blok": cislo_bloku,
        "stul": 1,
        "tym1": [g[0], g[2]],
        "tym2": [g[1], g[3]],
        "odehrano": False,
    })
    zapasy.append({
        "blok": cislo_bloku,
        "stul": 1,
        "tym1": [g[0], g[1]],
        "tym2": [g[2], g[3]],
        "odehrano": False,
    })

    # Pro 6–7 hráčů doplníme Stůl 2 vypůjčením hráčů ze stolu 1
    if len(stul2_hraci) >= 2:
      doplneni = stul2_hraci + stul1_hraci[: (4 - len(stul2_hraci))]
      g2 = doplneni
      zapasy.append({
          "blok": cislo_bloku,
          "stul": 2,
          "tym1": [g2[0], g2[3]],
          "tym2": [g2[1], g2[2]],
          "odehrano": False,
      })
      zapasy.append({
          "blok": cislo_bloku,
          "stul": 2,
          "tym1": [g2[0], g2[2]],
          "tym2": [g2[1], g2[3]],
          "odehrano": False,
      })

  return zapasy


st.title("🏓 Ping Pong Dobrovíz")

tab1, tab2, tab3, tab4 = st.tabs(
    ["📋 Přihlášení", "⚔️ Zápasy", "🏆 Žebříčky", "🛠️ Správa"]
)

# TAB 1: PŘIHLÁŠENÍ
with tab1:
  dnes = date.today()
  dny_do_stredy = (2 - dnes.weekday()) % 7
  vychozi_streda = dnes + timedelta(days=dny_do_stredy)

  zvolene_datum = st.date_input("Datum hrací středy:", vychozi_streda)

  if zvolene_datum.weekday() != 2:
    streda_tydne = zvolene_datum + timedelta(days=(2 - zvolene_datum.weekday()))
    st.warning(
        "⚠️ Ping pong se hraje pouze ve středu! Datum bylo upraveno na"
        f" **{streda_tydne.strftime('%d.%m.%Y')}**."
    )
    datum_session = streda_tydne
  else:
    datum_session = zvolene_datum

  aktualni_rok = datum_session.year

  jednotlivci_stat, _ = spocitej_statistiky(aktualni_rok)
  HRACI_DLE_UCASTI = sorted(
      st.session_state.vsechni_hraci,
      key=lambda h: jednotlivci_stat[h]["Středy"],
      reverse=True,
  )

  st.subheader("Přihlášení hráčů")
  st.caption("Seřazeno od nejčastějších účastníků:")

  for hrac in HRACI_DLE_UCASTI:
    je_prihlasen = st.session_state.prihlaseni.get(hrac, False)
    ucast_count = jednotlivci_stat[hrac]["Středy"]

    btn_label = (
        f"✅ {hrac} ({ucast_count}x)"
        if je_prihlasen
        else f"❌ {hrac} ({ucast_count}x)"
    )

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
    if st.button(
        "🎲 Vygenerovat zápasy (1. kolo)",
        type="primary",
        use_container_width=True,
    ):
      st.session_state.dnesni_zapasy = generuj_kolo_zapasu(
          pritomni, aktualni_rok, cislo_bloku=1
      )
      st.success("Zápasy pro 1. kolo vygenerovány!")

# TAB 2: ZÁPASY
with tab2:
  if not st.session_state.dnesni_zapasy:
    st.warning("Zatím nejsou vygenerovány žádné zápasy.")
  else:
    pritomni = [h for h, stav in st.session_state.prihlaseni.items() if stav]

    def vykresli_stul_ui(stul_id, nazev_stolu):
      st.subheader(nazev_stolu)
      stul_zapasy = [
          z for z in st.session_state.dnesni_zapasy if z["stul"] == stul_id
      ]

      if not stul_zapasy:
        st.caption("Na tomto stole zatím nejsou zápasy.")
        return

      for idx, z in enumerate(stul_zapasy):
        t1_s = f"{z['tym1'][0]} + {z['tym1'][1]}"
        t2_s = f"{z['tym2'][0]} + {z['tym2'][1]}"

        with st.expander(
            f"Kolo {z['blok']} - Zápas {idx+1}: {t1_s} vs {t2_s}",
            expanded=not z["odehrano"],
        ):
          if z["odehrano"]:
            st.success(
                f"Výsledek: **{z.get('skore1', 0)} : {z.get('skore2', 0)}**"
            )
          else:
            c1, c2 = st.columns(2)
            s1 = c1.number_input(
                f"Sety {z['tym1'][0]}", 0, 3, 0, key=f"s1_{stul_id}_{idx}"
            )
            s2 = c2.number_input(
                f"Sety {z['tym2'][0]}", 0, 3, 0, key=f"s2_{stul_id}_{idx}"
            )

            if st.button(
                "Uložit výsledek",
                key=f"btn_{stul_id}_{idx}",
                use_container_width=True,
            ):
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
                    "skore2": s2,
                }
                st.session_state.odehrane_zapasy.append(záznam)
                uloz_databazi(
                    st.session_state.odehrane_zapasy,
                    st.session_state.vsechni_hraci,
                    st.session_state.vydaje,
                )
                st.success("Výsledek uložen!")
                st.rerun()
              else:
                st.error("Hraje se na 3 vítězné sety!")

    vykresli_stul_ui(1, "🟢 Stůl 1")
    st.markdown("---")
    vykresli_stul_ui(2, "🔵 Stůl 2")

    st.markdown("---")
    max_blok = max(
        [z["blok"] for z in st.session_state.dnesni_zapasy], default=1
    )
    dalsi_blok = max_blok + 1

    if st.button(
        f"➕ Vygenerovat další kolo (Kolo {dalsi_blok})",
        type="primary",
        use_container_width=True,
    ):
      nove_zapasy = generuj_kolo_zapasu(
          pritomni, aktualni_rok, cislo_bloku=dalsi_blok
      )
      st.session_state.dnesni_zapasy.extend(nove_zapasy)
      st.success(f"Kolo {dalsi_blok} bylo úspěšně přidáno!")
      st.rerun()

# TAB 3: ŽEBRÍČKY & POKLADNA
with tab3:
  st.subheader("📅 Výběr roku pro žebříček")
  zvoleny_rok = st.selectbox(
      "Zobrazit data pro rok:", [2026, 2025, 2024], index=0
  )

  jednotlivci_stat, dvojice_stat = spocitej_statistiky(zvoleny_rok)

  celkem_vybrano = sum(st_["Vybráno"] for st_ in jednotlivci_stat.values())
  celkem_vydaje = sum(
      v["castka"]
      for v in st.session_state.vydaje
      if int(v["datum"].split("-")[0]) == zvoleny_rok
  )
  zustatek = celkem_vybrano - celkem_vydaje

  col_m1, col_m2, col_m3 = st.columns(3)
  col_m1.metric("💰 Vybráno", f"{celkem_vybrano} Kč")
  col_m2.metric("🛒 Výdaje", f"{celkem_vydaje} Kč")
  col_m3.metric("💵 Zůstatek v pokladně", f"{zustatek} Kč")

  st.markdown("---")
  st.subheader(f"🏆 Žebříček jednotlivců ({zvoleny_rok})")
  data_j = []
  for hrac, st_ in jednotlivci_stat.items():
    if st_["Středy"] > 0:
      prumer = round(st_["Výhry"] / st_["Středy"], 2)
      data_j.append({
          "Hráč": hrac,
          "Účastí (Středy)": st_["Středy"],
          "Celkem Výher": st_["Výhry"],
          "Prohry (z App)": st_["Prohry_App"],
          "Průměr výher/středa": prumer,
          "Vybráno (Kč)": st_["Vybráno"],
      })

  if data_j:
    st.dataframe(
        pd.DataFrame(data_j).sort_values(
            by=["Celkem Výher", "Průměr výher/středa"], ascending=False
        ),
        use_container_width=True,
        hide_index=True,
    )
  else:
    st.info(f"Pro rok {zvoleny_rok} nejsou evidována žádná data.")

  st.markdown("---")
  st.subheader(f"👥 Žebříček dvojic ({zvoleny_rok})")
  data_d = []
  for dvojice_nazev, st_ in dvojice_stat.items():
    if st_["Odehráno"] > 0:
      usp = round((st_["Výhry"] / st_["Odehráno"]) * 100, 1)
      data_d.append({
          "Dvojice": dvojice_nazev,
          "Zápasů": st_["Odehráno"],
          "Výhry": st_["Výhry"],
          "Prohry": st_["Prohry"],
          "Úspěšnost (%)": usp,
      })

  if data_d:
    st.dataframe(
        pd.DataFrame(data_d).sort_values(
            by=["Výhry", "Úspěšnost (%)"], ascending=False
        ),
        use_container_width=True,
        hide_index=True,
    )

  st.markdown("---")
  st.subheader("🛒 Přehled výdajů (Nákupy)")
  vydaje_roku = [
      v
      for v in st.session_state.vydaje
      if int(v["datum"].split("-")[0]) == zvoleny_rok
  ]
  if vydaje_roku:
    st.dataframe(
        pd.DataFrame(vydaje_roku)[["datum", "polozka", "castka"]].rename(
            columns={
                "datum": "Datum",
                "polozka": "Položka/Nákup",
                "castka": "Částka (Kč)",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )
  else:
    st.info("Zatím nebyly zadány žádné výdaje.")

# TAB 4: SPRÁVA & NÁKUPY
with tab4:
  st.subheader("🛒 Přidat drobný výdaj (Nákup)")
  col_v1, col_v2 = st.columns(2)
  polozka_vydaj = col_v1.text_input("Za co se platilo (např. Míčky):").strip()
  castka_vydaj = col_v2.number_input(
      "Částka v Kč:", min_value=1, value=150, step=10
  )

  if st.button("Uložit výdaj do pokladny", use_container_width=True):
    if polozka_vydaj:
      novy_vydaj = {
          "datum": str(date.today()),
          "polozka": polozka_vydaj,
          "castka": int(castka_vydaj),
      }
      st.session_state.vydaje.append(novy_vydaj)
      uloz_databazi(
          st.session_state.odehrane_zapasy,
          st.session_state.vsechni_hraci,
          st.session_state.vydaje,
      )
      st.success(f"Výdaj **{polozka_vydaj} ({castka_vydaj} Kč)** byl uložen!")
      st.rerun()

  st.markdown("---")
  st.subheader("➕ Přidat nového hráče")
  novy_hrac = st.text_input("Jméno nového hráče:").strip()
  if st.button("Přidat hráče do seznamu", use_container_width=True):
    if novy_hrac and novy_hrac not in st.session_state.vsechni_hraci:
      st.session_state.vsechni_hraci.append(novy_hrac)
      st.session_state.prihlaseni[novy_hrac] = False
      uloz_databazi(
          st.session_state.odehrane_zapasy,
          st.session_state.vsechni_hraci,
          st.session_state.vydaje,
      )
      st.success(f"Hráč **{novy_hrac}** byl úspěšně přidán!")
      st.rerun()

  st.markdown("---")
  st.subheader("🔍 Vyhledávání a editace zápasů")
  filter_hrac = st.selectbox(
      "Filtr podle hráče:", ["Všichni"] + st.session_state.vsechni_hraci
  )

  filtrovane_zapasy = []
  for orig_idx, z in enumerate(st.session_state.odehrane_zapasy):
    if (
        filter_hrac == "Všichni"
        or filter_hrac in z["tym1"]
        or filter_hrac in z["tym2"]
    ):
      filtrovane_zapasy.append((orig_idx, z))

  if not filtrovane_zapasy:
    st.info("Žádné odehrané zápasy neodpovídají zadanému filtru.")
  else:
    for orig_idx, z in reversed(filtrovane_zapasy):
      t1_nazev = f"{z['tym1'][0]} + {z['tym1'][1]}"
      t2_nazev = f"{z['tym2'][0]} + {z['tym2'][1]}"

      with st.expander(
          f"📝 {z['datum']} | Stůl {z['stul']}: {t1_nazev} ({z['skore1']}) vs"
          f" {t2_nazev} ({z['skore2']})"
      ):
        c1, c2 = st.columns(2)
        novy_s1 = c1.number_input(
            f"Sety {t1_nazev}",
            0,
            3,
            value=z["skore1"],
            key=f"edit_s1_{orig_idx}",
        )
        novy_s2 = c2.number_input(
            f"Sety {t2_nazev}",
            0,
            3,
            value=z["skore2"],
            key=f"edit_s2_{orig_idx}",
        )

        col_save, col_del = st.columns(2)
        if col_save.button(
            "💾 Uložit změnu", key=f"save_{orig_idx}", use_container_width=True
        ):
          st.session_state.odehrane_zapasy[orig_idx]["skore1"] = novy_s1
          st.session_state.odehrane_zapasy[orig_idx]["skore2"] = novy_s2
          uloz_databazi(
              st.session_state.odehrane_zapasy,
              st.session_state.vsechni_hraci,
              st.session_state.vydaje,
          )
          st.success("Změna byla úspěšně uložena!")
          st.rerun()

        if col_del.button(
            "❌ Smazat zápas", key=f"del_{orig_idx}", use_container_width=True
        ):
          st.session_state.odehrane_zapasy.pop(orig_idx)
          uloz_databazi(
              st.session_state.odehrane_zapasy,
              st.session_state.vsechni_hraci,
              st.session_state.vydaje,
          )
          st.success("Zápas byl smazán!")
          st.rerun()

  st.markdown("---")
  if st.button(
      "🗑️ SMAZAT VŠECHNA CVIČNÁ DATA", type="primary", use_container_width=True
  ):
    st.session_state.odehrane_zapasy = []
    uloz_databazi([], st.session_state.vsechni_hraci, st.session_state.vydaje)
    st.success("Všechna odehraná data byla smazána!")
    st.rerun()
