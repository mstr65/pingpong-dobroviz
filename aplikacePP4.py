import base64
import json
import os
from datetime import date, datetime, timedelta
import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="Ping Pong Dobrovíz", layout="centered", page_icon="🏓"
)

# EXTRA VELKÉ PÍSMO PRO TABLETY
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
    div[data-testid="stDataFrame"], div[data-testid="stDataEditor"] { 
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

    return zapasy, hraci, vydaje

  return [], DEFAULT_HRACI, []


def uloz_databazi(zapasy, hraci, vydaje):
  data = {"zapasy": zapasy, "hraci": hraci, "vydaje": vydaje}

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


if (
    "odehrane_zapasy" not in st.session_state
    or "tabulka_hraci" not in st.session_state
):
  zapasy, hraci, vydaje = nacti_databazi()
  st.session_state.odehrane_zapasy = zapasy
  st.session_state.tabulka_hraci = hraci
  st.session_state.vydaje = vydaje

seznam_jmen_hracu = [h["hrac"] for h in st.session_state.tabulka_hraci]

if "dnesni_zapasy" not in st.session_state:
  st.session_state.dnesni_zapasy = []

if "prihlaseni" not in st.session_state:
  st.session_state.prihlaseni = {h: False for h in seznam_jmen_hracu}

if "aktualni_datum_stredy" not in st.session_state:
  st.session_state.aktualni_datum_stredy = vychozi_streda


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
    rok_zapasu = (
        int(z["datum"].split("-")[0])
        if "-" in z["datum"]
        else int(z["datum"].split(".")[-1])
    )
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

  for h in seznam_jmen_hracu:
    nove_stredy = len(stredy_mnozina[h])
    jednotlivci[h]["Středy"] += nove_stredy
    jednotlivci[h]["Vybráno"] = jednotlivci[h]["Středy"] * CENA_ZA_SESSION

  return jednotlivci, dvojice


def generuj_kolo_zapasu(pritomni_hraci, zvoleny_rok, cislo_bloku):
  jednotlivci, _ = spocitej_statistiky(zvoleny_rok)

  def ziskej_prumer(hrac):
    st_ = jednotlivci[hrac]
    return (st_["Výhry"] / st_["Středy"]) if st_["Středy"] > 0 else 0.5

  hraci_serazeni = sorted(pritomni_hraci, key=ziskej_prumer, reverse=True)
  pocet = len(hraci_serazeni)
  zapasy = []

  def vytvor_zapas_dict(
      stul, h1, h2, h3, h4, blok, stojici="", odehrano=False
  ):
    return {
        "blok": blok,
        "stul": stul,
        "team1_hrac1": h1,
        "team1_hrac2": h2,
        "team2_hrac1": h3,
        "team2_hrac2": h4,
        "skoreTeam1": 0,
        "skoreTeam2": 0,
        "odehrano": odehrano,
        "stojici": stojici,
    }

  if pocet == 4:
    g = hraci_serazeni
    zapasy.append(
        vytvor_zapas_dict(1, g[0], g[3], g[1], g[2], cislo_bloku)
    )
    zapasy.append(
        vytvor_zapas_dict(1, g[0], g[2], g[1], g[3], cislo_bloku)
    )
    zapasy.append(
        vytvor_zapas_dict(1, g[0], g[1], g[2], g[3], cislo_bloku)
    )

  elif pocet == 5:
    for i in range(5):
      stojici = hraci_serazeni[i % 5]
      a = [h for h in hraci_serazeni if h != stojici]
      zapasy.append(
          vytvor_zapas_dict(
              1, a[0], a[3], a[1], a[2], cislo_bloku, stojici=stojici
          )
      )

  elif pocet == 6:
    par_pauz = [(0, 1), (2, 3), (4, 5), (0, 3), (1, 4), (2, 5)]
    for idx_stojici in par_pauz:
      stojici = [hraci_serazeni[i] for i in idx_stojici]
      a = [
          h for idx, h in enumerate(hraci_serazeni) if idx not in idx_stojici
      ]
      zapasy.append(
          vytvor_zapas_dict(
              1, a[0], a[3], a[1], a[2], cislo_bloku, stojici=", ".join(stojici)
          )
      )

  elif pocet == 7:
    for i in range(7):
      rot = hraci_serazeni[i:] + hraci_serazeni[:i]
      st1, st2, stojici = rot[:4], rot[4:6], rot[6]
      zapasy.append(
          vytvor_zapas_dict(
              1, st1[0], st1[3], st1[1], st1[2], cislo_bloku, stojici=stojici
          )
      )
      zapasy.append(
          vytvor_zapas_dict(2, st2[0], "", st2[1], "", cislo_bloku)
      )

  elif pocet == 8:
    shift = ((cislo_bloku - 1) * 2) % 8
    rot = hraci_serazeni[shift:] + hraci_serazeni[:shift]
    g1 = [rot[0], rot[3], rot[4], rot[7]]
    g2 = [rot[1], rot[2], rot[5], rot[6]]

    for stul_id, g in [(1, g1), (2, g2)]:
      zapasy.append(
          vytvor_zapas_dict(stul_id, g[0], g[3], g[1], g[2], cislo_bloku)
      )
      zapasy.append(
          vytvor_zapas_dict(stul_id, g[0], g[2], g[1], g[3], cislo_bloku)
      )
      zapasy.append(
          vytvor_zapas_dict(stul_id, g[0], g[1], g[2], g[3], cislo_bloku)
      )

  elif pocet == 9:
    for i in range(9):
      stojici = hraci_serazeni[i % 9]
      a = [h for h in hraci_serazeni if h != stojici]
      t1 = [a[0], a[3], a[4], a[7]]
      t2 = [a[1], a[2], a[5], a[6]]
      zapasy.append(
          vytvor_zapas_dict(
              1, t1[0], t1[3], t1[1], t1[2], cislo_bloku, stojici=stojici
          )
      )
      zapasy.append(
          vytvor_zapas_dict(2, t2[0], t2[3], t2[1], t2[2], cislo_bloku)
      )

  elif pocet >= 10:
    for i in range(5):
      idx1, idx2 = (2 * i) % pocet, (2 * i + 1) % pocet
      stojici = [hraci_serazeni[idx1], hraci_serazeni[idx2]]
      a = [
          h for idx, h in enumerate(hraci_serazeni) if idx not in (idx1, idx2)
      ][:8]
      t1, t2 = [a[0], a[3], a[4], a[7]], [a[1], a[2], a[5], a[6]]
      zapasy.append(
          vytvor_zapas_dict(
              1,
              t1[0],
              t1[3],
              t1[1],
              t1[2],
              cislo_bloku,
              stojici=", ".join(stojici),
          )
      )
      zapasy.append(
          vytvor_zapas_dict(2, t2[0], t2[3], t2[1], t2[2], cislo_bloku)
      )

  return zapasy


st.title("🏓 Ping Pong Dobrovíz")

tab1, tab2, tab3, tab4 = st.tabs(
    ["📋 Přihlášení", "⚔️ Zápasy", "🏆 Žebříčky", "🛠️ Správa"]
)

# TAB 1: PŘIHLÁŠENÍ
with tab1:
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

  st.session_state.aktualni_datum_stredy = datum_session
  aktualni_rok = datum_session.year

  jednotlivci_stat, _ = spocitej_statistiky(aktualni_rok)
  HRACI_DLE_UCASTI = sorted(
      seznam_jmen_hracu,
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
        t1_str = (
            f"{z['team1_hrac1']} + {z['team1_hrac2']}"
            if z["team1_hrac2"]
            else z["team1_hrac1"]
        )
        t2_str = (
            f"{z['team2_hrac1']} + {z['team2_hrac2']}"
            if z["team2_hrac2"]
            else z["team2_hrac1"]
        )

        stojici_info = (
            f" (💡 Odpočívá: {z['stojici']})" if z.get("stojici") else ""
        )

        with st.expander(
            f"Kolo {z['blok']} - Zápas {idx+1}: {t1_str} vs {t2_str}{stojici_info}",
            expanded=not z["odehrano"],
        ):
          if z["odehrano"]:
            st.success(
                f"Výsledek: **{z.get('skoreTeam1', 0)} :"
                f" {z.get('skoreTeam2', 0)}**"
            )
          else:
            c1, c2 = st.columns(2)
            s1 = c1.number_input(
                f"Sety {z['team1_hrac1']}",
                0,
                3,
                0,
                key=f"s1_{stul_id}_{z['blok']}_{idx}",
            )
            s2 = c2.number_input(
                f"Sety {z['team2_hrac1']}",
                0,
                3,
                0,
                key=f"s2_{stul_id}_{z['blok']}_{idx}",
            )

            if st.button(
                "Uložit výsledek",
                key=f"btn_{stul_id}_{z['blok']}_{idx}",
                use_container_width=True,
            ):
              if s1 == 3 or s2 == 3:
                z["skoreTeam1"] = s1
                z["skoreTeam2"] = s2
                z["odehrano"] = True

                # Výpočet nového automatického ID
                existujici_ids = [
                    z.get("id", 0)
                    for z in st.session_state.odehrane_zapasy
                    if isinstance(z.get("id"), int)
                ]
                nove_id = max(existujici_ids) + 1 if existujici_ids else 1

                záznam = {
                    "id": nove_id,
                    "datum": str(st.session_state.aktualni_datum_stredy),
                    "stul": stul_id,
                    "team1_hrac1": z["team1_hrac1"],
                    "team1_hrac2": z["team1_hrac2"],
                    "team2_hrac1": z["team2_hrac1"],
                    "team2_hrac2": z["team2_hrac2"],
                    "skoreTeam1": s1,
                    "skoreTeam2": s2,
                }
                st.session_state.odehrane_zapasy.append(záznam)
                uloz_databazi(
                    st.session_state.odehrane_zapasy,
                    st.session_state.tabulka_hraci,
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

# TAB 4: SPRÁVA & DATABÁZE
with tab4:
  st.subheader("🗄️ Správa databázových tabulek")

  tab_db1, tab_db2 = st.tabs(["⚔️ Tabulka Zápasů", "👤 Tabulka Hráčů"])

  with tab_db1:
    st.markdown(
        "**Tabulka `zapasy`**  \n*(ID se generuje automaticky. Při kliknutí na"
        " datum se zobrazí kalendář)*"
    )

    if st.session_state.odehrane_zapasy:
      rows = []
      for z in st.session_state.odehrane_zapasy:
        d_val = z.get("datum", "")
        try:
          if "-" in str(d_val):
            d_obj = datetime.strptime(str(d_val), "%Y-%m-%d").date()
          elif "." in str(d_val):
            d_obj = datetime.strptime(str(d_val), "%d.%m.%Y").date()
          else:
            d_obj = st.session_state.aktualni_datum_stredy
        except Exception:
          d_obj = st.session_state.aktualni_datum_stredy

        rows.append({
            "id": z.get("id"),
            "datum": d_obj,
            "stul": z.get("stul", 1),
            "team1_hrac1": z.get("team1_hrac1", ""),
            "team1_hrac2": z.get("team1_hrac2", ""),
            "team2_hrac1": z.get("team2_hrac1", ""),
            "team2_hrac2": z.get("team2_hrac2", ""),
            "skoreTeam1": z.get("skoreTeam1", 0),
            "skoreTeam2": z.get("skoreTeam2", 0),
        })
      df_edit = pd.DataFrame(rows)
    else:
      df_edit = pd.DataFrame(
          columns=[
              "id",
              "datum",
              "stul",
              "team1_hrac1",
              "team1_hrac2",
              "team2_hrac1",
              "team2_hrac2",
              "skoreTeam1",
              "skoreTeam2",
          ]
      )

    options_hraci = [""] + seznam_jmen_hracu

    edited_df = st.data_editor(
        df_edit,
        num_rows="dynamic",
        use_container_width=True,
        key="db_editor_zapasy",
        column_config={
            "id": st.column_config.NumberColumn(
                "ID", disabled=True, help="ID se generuje automaticky"
            ),
            "datum": st.column_config.DateColumn(
                "Datum",
                default=st.session_state.aktualni_datum_stredy,
                format="YYYY-MM-DD",
                required=True,
            ),
            "stul": st.column_config.NumberColumn(
                "Stůl", min_value=1, max_value=2, default=1
            ),
            "team1_hrac1": st.column_config.SelectboxColumn(
                "Tým 1 - Hráč 1", options=options_hraci, required=True
            ),
            "team1_hrac2": st.column_config.SelectboxColumn(
                "Tým 1 - Hráč 2", options=options_hraci
            ),
            "team2_hrac1": st.column_config.SelectboxColumn(
                "Tým 2 - Hráč 1", options=options_hraci, required=True
            ),
            "team2_hrac2": st.column_config.SelectboxColumn(
                "Tým 2 - Hráč 2", options=options_hraci
            ),
            "skoreTeam1": st.column_config.NumberColumn(
                "Skóre T1", min_value=0, max_value=3, default=0
            ),
            "skoreTeam2": st.column_config.NumberColumn(
                "Skóre T2", min_value=0, max_value=3, default=0
            ),
        },
    )

    if st.button(
        "💾 Uložit tabulku ZÁPASŮ", type="primary", use_container_width=True
    ):
      nove_zapasy = []
      chyba_duplicita = False

      # Zjištění nejvyššího dosavadního ID pro autoincrement
      platna_ids = [
          z.get("id", 0)
          for z in st.session_state.odehrane_zapasy
          if isinstance(z.get("id"), int)
      ]
      next_id = max(platna_ids) + 1 if platna_ids else 1

      for idx, row in edited_df.iterrows():
        h1, h2 = str(row.get("team1_hrac1", "")).strip(), str(
            row.get("team1_hrac2", "")
        ).strip()
        h3, h4 = str(row.get("team2_hrac1", "")).strip(), str(
            row.get("team2_hrac2", "")
        ).strip()

        # Kontrola duplicity
        vybrani_hraci = [h for h in [h1, h2, h3, h4] if h != ""]
        if len(vybrani_hraci) != len(set(vybrani_hraci)):
          st.error(
              f"⛔ CHYBA na řádku {idx+1}: Hráč nemůže hrát vícekrát v jednom"
              " zápase!"
          )
          chyba_duplicita = True
          break

        # Automatické generování ID pokud chybí
        raw_id = row.get("id")
        if pd.notnull(raw_id) and str(raw_id).isdigit() and int(raw_id) > 0:
          z_id = int(raw_id)
        else:
          z_id = next_id
          next_id += 1

        # Formátování datumu
        raw_datum = row.get("datum")
        if pd.notnull(raw_datum):
          datum_str = str(raw_datum).split(" ")[0]
        else:
          datum_str = str(st.session_state.aktualni_datum_stredy)

        if h1 and h3:
          nove_zapasy.append({
              "id": z_id,
              "datum": datum_str,
              "stul": (
                  int(row.get("stul", 1)) if pd.notnull(row.get("stul")) else 1
              ),
              "team1_hrac1": h1,
              "team1_hrac2": h2 if h2 != "nan" else "",
              "team2_hrac1": h3,
              "team2_hrac2": h4 if h4 != "nan" else "",
              "skoreTeam1": (
                  int(row.get("skoreTeam1", 0))
                  if pd.notnull(row.get("skoreTeam1"))
                  else 0
              ),
              "skoreTeam2": (
                  int(row.get("skoreTeam2", 0))
                  if pd.notnull(row.get("skoreTeam2"))
                  else 0
              ),
          })

      if not chyba_duplicita:
        st.session_state.odehrane_zapasy = nove_zapasy
        uloz_databazi(
            st.session_state.odehrane_zapasy,
            st.session_state.tabulka_hraci,
            st.session_state.vydaje,
        )
        st.success("Tabulka ZÁPASŮ byla úspěšně uložena!")
        st.rerun()

  with tab_db2:
    st.markdown("**Tabulka `hraci`**  \n*(Správa seznamu hráčů a jejich ID)*")
    df_hraci = pd.DataFrame(st.session_state.tabulka_hraci)

    edited_hraci = st.data_editor(
        df_hraci,
        num_rows="dynamic",
        use_container_width=True,
        key="db_editor_hraci",
        column_config={
            "id": st.column_config.NumberColumn(
                "ID", disabled=True, help="ID se generuje automaticky"
            ),
            "hrac": st.column_config.TextColumn("Jméno hráče", required=True),
        },
    )

    if st.button(
        "💾 Uložit tabulku HRÁČŮ", type="primary", use_container_width=True
    ):
      novi_hraci = []
      platna_ids_h = [
          h.get("id", 0)
          for h in st.session_state.tabulka_hraci
          if isinstance(h.get("id"), int)
      ]
      next_h_id = max(platna_ids_h) + 1 if platna_ids_h else 1

      for idx, row in edited_hraci.iterrows():
        jmeno = str(row.get("hrac", "")).strip()
        raw_id = row.get("id")

        if pd.notnull(raw_id) and str(raw_id).isdigit() and int(raw_id) > 0:
          h_id = int(raw_id)
        else:
          h_id = next_h_id
          next_h_id += 1

        if jmeno and jmeno != "nan":
          novi_hraci.append({"id": h_id, "hrac": jmeno})

      st.session_state.tabulka_hraci = novi_hraci
      uloz_databazi(
          st.session_state.odehrane_zapasy,
          st.session_state.tabulka_hraci,
          st.session_state.vydaje,
      )
      st.success("Tabulka HRÁČŮ byla úspěšně uložena!")
      st.rerun()

  st.markdown("---")
  db_json_data = json.dumps(
      {
          "zapasy": st.session_state.odehrane_zapasy,
          "hraci": st.session_state.tabulka_hraci,
          "vydaje": st.session_state.vydaje,
      },
      ensure_ascii=False,
      indent=4,
  )

  st.download_button(
      label="📥 Stáhnout databázi (JSON záloha)",
      data=db_json_data,
      file_name="databaze_pingpong_backup.json",
      mime="application/json",
      use_container_width=True,
  )

  nahrany_soubor = st.file_uploader(
      "Obnovit databázi ze záložního JSON souboru:", type=["json"]
  )
  if nahrany_soubor is not None:
    try:
      nactena_db = json.load(nahrany_soubor)
      st.session_state.odehrane_zapasy = nactena_db.get("zapasy", [])
      st.session_state.tabulka_hraci = normalizuj_hrace(
          nactena_db.get("hraci", DEFAULT_HRACI)
      )
      st.session_state.vydaje = nactena_db.get("vydaje", [])
      uloz_databazi(
          st.session_state.odehrane_zapasy,
          st.session_state.tabulka_hraci,
          st.session_state.vydaje,
      )
      st.success("Databáze byla úspěšně obnovena!")
      st.rerun()
    except Exception as e:
      st.error(f"Chyba při načítání souboru: {e}")

  st.markdown("---")
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
          st.session_state.tabulka_hraci,
          st.session_state.vydaje,
      )
      st.success(f"Výdaj **{polozka_vydaj} ({castka_vydaj} Kč)** byl uložen!")
      st.rerun()
