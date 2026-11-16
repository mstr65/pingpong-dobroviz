import base64
import itertools
import json
import math
import os
from datetime import date, datetime, timedelta
import pandas as pd
import requests
import streamlit as st

# ROZTAŽENÍ APLIKACE NA PLNOU ŠÍŘKU (IDEÁLNÍ PRO TABLET NA ŠÍŘKU)
st.set_page_config(
    page_title="Ping Pong Dobrovíz", layout="wide", page_icon="🏓"
)

# EXTRA VELKÉ PÍSMO PRO TABLETY A OPTIMALIZACE PROSTORU
st.markdown(
    """
<style>
    html, body, [class*="css"], div, p, span { 
        font-size: 24px !important; 
        line-height: 1.4 !important;
    }
    .block-container {
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 100% !important;
    }
    div.stButton > button { 
        font-size: 28px !important; 
        font-weight: bold !important; 
        padding: 18px 20px !important; 
        border-radius: 14px !important; 
        margin-bottom: 10px !important;
        width: 100% !important;
    }
    button[data-baseweb="tab"] { 
        font-size: 26px !important; 
        font-weight: bold !important; 
        padding: 16px 12px !important; 
    }
    div[data-testid="stDataFrame"], div[data-testid="stDataEditor"] { 
        font-size: 22px !important; 
        width: 100% !important;
    }
    input { 
        font-size: 28px !important; 
        font-weight: bold !important; 
        text-align: center !important;
        height: 55px !important;
    }
</style>
""",
    unsafe_allow_html=True,
)

DB_FILE = "databaze_pingpong.json"
CENA_ZA_SESSION = 30  # Kč za osobu

# Výpočet výchozí středy pro celou aplikaci
dnes = date.today()
dny_do_stredy = (2 - dnes.weekday()) % 7
vychozi_streda = dnes + timedelta(days=dny_do_stredy)

DEFAULT_HRACI = [
    {"id": 1, "hrac": "Sofka"},
    {"id": 2, "hrac": "Jindra"},
    {"id": 3, "hrac": "Tibor"},
    {"id": 4, "hrac": "Pavel"},
    {"id": 5, "hrac": "Jarda"},
    {"id": 6, "hrac": "Vláďa"},
    {"id": 7, "hrac": "Jirka"},
    {"id": 8, "hrac": "Petr"},
    {"id": 9, "hrac": "Miro"},
    {"id": 10, "hrac": "Franta"},
    {"id": 11, "hrac": "Fred"},
    {"id": 12, "hrac": "Jirka S."},
    {"id": 13, "hrac": "Mirek"},
    {"id": 14, "hrac": "Petr W."},
    {"id": 15, "hrac": "Přespolní"},
]

HISTORIE_PODLE_ROKU = {
    2026: {
        "Jindra": {"Výhry": 84, "Středy": 22},
        "Sofka": {"Výhry": 82, "Středy": 24},
        "Tibor": {"Výhry": 74, "Středy": 19},
        "Pavel": {"Výhry": 73, "Středy": 22},
        "Jarda": {"Výhry": 63, "Středy": 18},
        "Vláďa": {"Výhry": 58, "Středy": 20},
        "Jirka": {"Výhry": 33, "Středy": 22},
        "Petr": {"Výhry": 27, "Středy": 8},
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


def normalizuj_hrace(hraci_raw):
  if not hraci_raw:
    return DEFAULT_HRACI
  if isinstance(hraci_raw[0], str):
    return [{"id": i + 1, "hrac": name} for i, name in enumerate(hraci_raw)]
  return hraci_raw


def nacti_databazi():
  data = None
  if "GITHUB_TOKEN" in st.secrets and "GITHUB_REPO" in st.secrets:
    try:
      token = st.secrets["GITHUB_TOKEN"]
      repo = st.secrets["GITHUB_REPO"]
      url = f"https://api.github.com/repos/{repo}/contents/{DB_FILE}"
      headers = {"Authorization": f"token {token}"}
      res = requests.get(url, headers=headers)
      if res.status_code == 200:
        content = res.json().get("content", "")
        data = json.loads(base64.b64decode(content).decode("utf-8"))
    except Exception as e:
      print(f"Chyba při načítání z GitHubu: {e}")

  if not data and os.path.exists(DB_FILE):
    with open(DB_FILE, "r", encoding="utf-8") as f:
      data = json.load(f)

  if data and isinstance(data, dict):
    zapasy = data.get("zapasy", [])
    hraci = normalizuj_hrace(data.get("hraci", DEFAULT_HRACI))
    vydaje = data.get("vydaje", [])
    dnesni_session = data.get("dnesni_session", {})

    for z in zapasy:
      if "team1_hrac1" not in z:
        t1 = z.get("tym1", [])
        t2 = z.get("tym2", [])
        z["team1_hrac1"] = t1[0] if len(t1) > 0 else ""
        z["team1_hrac2"] = t1[1] if len(t1) > 1 else ""
        z["team2_hrac1"] = t2[0] if len(t2) > 0 else ""
        z["team2_hrac2"] = t2[1] if len(t2) > 1 else ""
        z["skoreTeam1"] = z.get("skore1", 0)
        z["skoreTeam2"] = z.get("skore2", 0)

    return zapasy, hraci, vydaje, dnesni_session

  return [], DEFAULT_HRACI, [], {}


def ziskej_dnesni_session_dict():
  return {
      "datum": str(
          st.session_state.get("aktualni_datum_stredy", vychozi_streda)
      ),
      "prihlaseni": st.session_state.get("prihlaseni", {}),
      "dnesni_zapasy": st.session_state.get("dnesni_zapasy", []),
  }


def uloz_databazi(zapasy, hraci, vydaje, dnesni_session=None):
  data = {
      "zapasy": zapasy,
      "hraci": hraci,
      "vydaje": vydaje,
      "dnesni_session": (
          dnesni_session
          if dnesni_session is not None
          else ziskej_dnesni_session_dict()
      ),
  }

  with open(DB_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

  if "GITHUB_TOKEN" in st.secrets and "GITHUB_REPO" in st.secrets:
    try:
      token = st.secrets["GITHUB_TOKEN"]
      repo = st.secrets["GITHUB_REPO"]
      url = f"https://api.github.com/repos/{repo}/contents/{DB_FILE}"
      headers = {"Authorization": f"token {token}"}

      res = requests.get(url, headers=headers)
      sha = res.json().get("sha", "") if res.status_code == 200 else ""

      content = base64.b64encode(
          json.dumps(data, ensure_ascii=False, indent=4).encode("utf-8")
      ).decode("utf-8")

      payload = {
          "message": "Automatická aktualizace databáze zápasů",
          "content": content,
          "sha": sha,
      }

      requests.put(url, json=payload, headers=headers)
    except Exception as e:
      print(f"Chyba při ukládání na GitHub: {e}")


# INICIALIZACE A OBNOVENÍ STAVU
if (
    "odehrane_zapasy" not in st.session_state
    or "tabulka_hraci" not in st.session_state
):
  zapasy, hraci, vydaje, dnesni_session = nacti_databazi()
  st.session_state.odehrane_zapasy = zapasy
  st.session_state.tabulka_hraci = hraci
  st.session_state.vydaje = vydaje
  st.session_state.dnesni_session_db = dnesni_session

seznam_jmen_hracu = [h["hrac"] for h in st.session_state.tabulka_hraci]

if "aktualni_datum_stredy" not in st.session_state:
  st.session_state.aktualni_datum_stredy = vychozi_streda

dnesni_session_db = st.session_state.get("dnesni_session_db", {})
datum_str = str(st.session_state.aktualni_datum_stredy)

if "dnesni_zapasy" not in st.session_state:
  if dnesni_session_db.get("datum") == datum_str:
    st.session_state.dnesni_zapasy = dnesni_session_db.get("dnesni_zapasy", [])
  else:
    st.session_state.dnesni_zapasy = []

if "prihlaseni" not in st.session_state:
  if (
      dnesni_session_db.get("datum") == datum_str
      and "prihlaseni" in dnesni_session_db
  ):
    st.session_state.prihlaseni = dnesni_session_db.get("prihlaseni", {})
  else:
    st.session_state.prihlaseni = {h: False for h in seznam_jmen_hracu}


def spocitej_statistiky(zvoleny_rok):
  historie = HISTORIE_PODLE_ROKU.get(zvoleny_rok, {})

  jednotlivci = {
      h: {
          "Středy": historie.get(h, {}).get("Středy", 0),
          "Výhry": historie.get(h, {}).get("Výhry", 0),
          "Prohry_App": 0,
          "Vybráno": historie.get(h, {}).get("Středy", 0) * CENA_ZA_SESSION,
      }
      for h in seznam_jmen_hracu
  }

  dvojice = {}
  stredy_mnozina = {h: set() for h in seznam_jmen_hracu}

  for z in st.session_state.odehrane_zapasy:
    d = z.get("datum", "")
    try:
      rok_zapasu = int(d.split("-")[0]) if "-" in d else int(d.split(".")[-1])
    except Exception:
      continue

    if rok_zapasu != zvoleny_rok:
      continue

    s1, s2 = z.get("skoreTeam1", 0), z.get("skoreTeam2", 0)
    t1 = [
        h
        for h in [z.get("team1_hrac1", ""), z.get("team1_hrac2", "")]
        if h != ""
    ]
    t2 = [
        h
        for h in [z.get("team2_hrac1", ""), z.get("team2_hrac2", "")]
        if h != ""
    ]

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

  for h in seznam_jmen_hracu:
    nove_stredy = len(stredy_mnozina[h])
    jednotlivci[h]["Středy"] += nove_stredy
    jednotlivci[h]["Vybráno"] = jednotlivci[h]["Středy"] * CENA_ZA_SESSION

  return jednotlivci, dvojice


def skontroluj_zapasy_bloky(zapasy):
  """Kontrola, že v žádném bloku (kole) nehraje stejný hráč na dvou stolech současně."""
  bloky = {}
  for z in zapasy:
    b = z.get("blok", 1)
    if b not in bloky:
      bloky[b] = []
    bloky[b].append(z)

  for b, lista in bloky.items():
    stoly_hraci = []
    for z in lista:
      hraci = [
          z.get("team1_hrac1", ""),
          z.get("team1_hrac2", ""),
          z.get("team2_hrac1", ""),
          z.get("team2_hrac2", ""),
      ]
      hraci = [h for h in hraci if h]
      if len(hraci) != len(set(hraci)):
        return False, f"Hráč je duplicitní v zápase bloku #{b}!"
      stoly_hraci.append(set(hraci))

    if len(stoly_hraci) > 1:
      for i in range(len(stoly_hraci)):
        for j in range(i + 1, len(stoly_hraci)):
          prunik = stoly_hraci[i].intersection(stoly_hraci[j])
          if prunik:
            return (
                False,
                f"Hráč(i) {', '.join(prunik)} hrají současně na Stole"
                f" {i+1} a Stole {j+1} v bloku #{b}!",
            )

  return True, "OK"


def generuj_vsechny_zapasy(pritomni_hraci):
  pocet = len(pritomni_hraci)
  if pocet < 4:
    return []

  vsechny_zapasy = []

  # POUZE 1 STŮL PRO 4 AŽ 7 HRÁČŮ
  if pocet < 8:
    vsechny_ctverice = list(itertools.combinations(pritomni_hraci, 4))
    blok = 1

    for ctverice in vsechny_ctverice:
      stojici = [h for h in pritomni_hraci if h not in ctverice]
      stojici_str = ", ".join(stojici) if stojici else "nikdo"

      p1, p2, p3, p4 = ctverice

      parovani = [
          (p1, p2, p3, p4),  # (p1+p2) vs (p3+p4)
          (p1, p3, p2, p4),  # (p1+p3) vs (p2+p4)
          (p1, p4, p2, p3),  # (p1+p4) vs (p2+p3)
      ]

      for h1, h2, h3, h4 in parovani:
        vsechny_zapasy.append({
            "blok": blok,
            "stul": 1,
            "team1_hrac1": h1,
            "team1_hrac2": h2,
            "team2_hrac1": h3,
            "team2_hrac2": h4,
            "skoreTeam1":
