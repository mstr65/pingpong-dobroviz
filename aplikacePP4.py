import base64
import json
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


def cisty_text(val):
    """Převede None, NaN nebo textové 'None'/'nan' bezpečně na prázdný řetězec."""
    if val is None:
        return ""
    s = str(val).strip()
    return "" if s.lower() in ("none", "nan", "null") else s


def ciste_cislo(val, default=0):
    """Bezpečně převede hodnotu (včetně None/NaN) na celé číslo."""
    if val is None:
        return default
    try:
        if pd.isna(val):
            return default
        return int(float(val))
    except (ValueError, TypeError):
        return default


def parsuj_rok(datum_val):
    """Bezpečně vytáhne rok z formátu YYYY-MM-DD nebo DD.MM.YYYY."""
    d = cisty_text(datum_val)
    if not d:
        return None
    try:
        if "-" in d:
            return int(d.split("-")[0])
        if "." in d:
            return int(d.split(".")[-1])
        return int(d[:4])
    except (ValueError, IndexError):
        return None


def normalizuj_hrace(hraci_raw):
    if not hraci_raw:
        return DEFAULT_HRACI
    if isinstance(hraci_raw[0], str):
        return [
            {"id": i + 1, "hrac": cisty_text(name)}
            for i, name in enumerate(hraci_raw)
            if cisty_text(name)
        ]
    vysledek = []
    for i, h in enumerate(hraci_raw):
        jmeno = cisty_text(h.get("hrac"))
        if jmeno:
            vysledek.append({"id": ciste_cislo(h.get("id"), i + 1), "hrac": jmeno})
    return vysledek if vysledek else DEFAULT_HRACI


def preved_stare_zapasy_na_vysledky(zapasy_raw):
    """Převede starší detailní záznamy zápasů na čistý formát (datum, hrac, vyhry)."""
    agregace = {}  # (datum, hrac) -> pocet_vyher
    for z in zapasy_raw:
        if not isinstance(z, dict):
            continue
        d = cisty_text(z.get("datum"))
        if not d:
            continue

        # Pokud už jde o nový formát
        if "hrac" in z and "vyhry" in z:
            h = cisty_text(z.get("hrac"))
            if h:
                agregace[(d, h)] = agregace.get((d, h), 0) + ciste_cislo(z.get("vyhry"), 0)
            continue

        # Převod ze staršího formátu zápasů / Rychlého zadání
        if "team1_hrac1" not in z and ("tym1" in z or "tym2" in z):
            t1 = [cisty_text(x) for x in z.get("tym1", []) if cisty_text(x)]
            t2 = [cisty_text(x) for x in z.get("tym2", []) if cisty_text(x)]
            s1 = ciste_cislo(z.get("skore1"), 0)
            s2 = ciste_cislo(z.get("skore2"), 0)
        else:
            t1 = [
                h for h in [cisty_text(z.get("team1_hrac1")), cisty_text(z.get("team1_hrac2"))]
                if h and h != "Rychlé zadání"
            ]
            t2 = [
                h for h in [cisty_text(z.get("team2_hrac1")), cisty_text(z.get("team2_hrac2"))]
                if h and h != "Rychlé zadání"
            ]
            s1 = ciste_cislo(z.get("skoreTeam1"), 0)
            s2 = ciste_cislo(z.get("skoreTeam2"), 0)

        for h in t1:
            agregace.setdefault((d, h), 0)
            if s1 > s2:
                agregace[(d, h)] += 1
        for h in t2:
            agregace.setdefault((d, h), 0)
            if s2 > s1:
                agregace[(d, h)] += 1

    vysledky = []
    for idx, ((d, h), pocet_v) in enumerate(sorted(agregace.items()), start=1):
        vysledky.append({
            "id": idx,
            "datum": d,
            "hrac": h,
            "vyhry": pocet_v,
        })
    return vysledky


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
        hraci = normalizuj_hrace(data.get("hraci", DEFAULT_HRACI))
        vydaje_raw = data.get("vydaje", [])
        dnesni_session = data.get("dnesni_session", {})

        # Načtení nového formátu 'vysledky' nebo automatická migrace ze starého 'zapasy'
        if "vysledky" in data and isinstance(data["vysledky"], list):
            vysledky = [
                {
                    "id": ciste_cislo(r.get("id"), idx + 1),
                    "datum": cisty_text(r.get("datum")) or str(vychozi_streda),
                    "hrac": cisty_text(r.get("hrac")),
                    "vyhry": ciste_cislo(r.get("vyhry"), 0),
                }
                for idx, r in enumerate(data["vysledky"])
                if isinstance(r, dict) and cisty_text(r.get("hrac"))
            ]
        else:
            vysledky = preved_stare_zapasy_na_vysledky(data.get("zapasy", []))

        vydaje = [
            {
                "datum": cisty_text(v.get("datum")) or str(date.today()),
                "polozka": cisty_text(v.get("polozka")),
                "castka": ciste_cislo(v.get("castka"), 0),
            }
            for v in vydaje_raw
            if isinstance(v, dict)
        ]

        return vysledky, hraci, vydaje, dnesni_session

    return [], DEFAULT_HRACI, [], {}


def ziskej_dnesni_session_dict():
    return {
        "datum": str(st.session_state.get("aktualni_datum_stredy", vychozi_streda)),
        "prihlaseni": st.session_state.get("prihlaseni", {}),
    }


def uloz_databazi(vysledky, hraci, vydaje, dnesni_session=None):
    data = {
        "vysledky": vysledky,
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
                "message": "Aktualizace databáze ping pongu",
                "content": content,
                "sha": sha,
            }

            requests.put(url, json=payload, headers=headers)
        except Exception as e:
            print(f"Chyba při ukládání na GitHub: {e}")


# ==============================================================================
# INICIALIZACE STAVU APLIKACE
# ==============================================================================
if (
    "vysledky_db" not in st.session_state
    or "tabulka_hraci" not in st.session_state
):
    vysledky, hraci, vydaje, dnesni_session = nacti_databazi()
    st.session_state.vysledky_db = vysledky
    st.session_state.tabulka_hraci = hraci
    st.session_state.vydaje = vydaje
    st.session_state.dnesni_session_db = dnesni_session

seznam_jmen_hracu = [h["hrac"] for h in st.session_state.tabulka_hraci]

if "aktualni_datum_stredy" not in st.session_state:
    st.session_state.aktualni_datum_stredy = vychozi_streda


def spocitej_statistiky(zvoleny_rok):
    historie = HISTORIE_PODLE_ROKU.get(zvoleny_rok, {})

    jednotlivci = {
        h: {
            "Středy": historie.get(h, {}).get("Středy", 0),
            "Výhry": historie.get(h, {}).get("Výhry", 0),
            "Vybráno": historie.get(h, {}).get("Středy", 0) * CENA_ZA_SESSION,
        }
        for h in seznam_jmen_hracu
    }

    stredy_mnozina = {h: set() for h in seznam_jmen_hracu}

    for r in st.session_state.vysledky_db:
        d = cisty_text(r.get("datum"))
        if parsuj_rok(d) != zvoleny_rok:
            continue

        h = cisty_text(r.get("hrac"))
        v = ciste_cislo(r.get("vyhry"), 0)

        if h in jednotlivci:
            stredy_mnozina[h].add(d)
            jednotlivci[h]["Výhry"] += v

    for h in seznam_jmen_hracu:
        jednotlivci[h]["Středy"] += len(stredy_mnozina[h])
        jednotlivci[h]["Vybráno"] = jednotlivci[h]["Středy"] * CENA_ZA_SESSION

    return jednotlivci


st.title("🏓 Ping Pong Dobrovíz")

tab1, tab2, tab3 = st.tabs(
    ["📋 Přihlášení & Výhry", "🏆 Žebříčky & Pokladna", "🛠️ Správa"]
)

# ==============================================================================
# TAB 1: PŘIHLÁŠENÍ & ZADÁNÍ VÝHER
# ==============================================================================
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
    datum_str = str(datum_session)

    # Načtení uložených výher pro zvolené datum
    ulozene_vyhry_dne = {
        cisty_text(r.get("hrac")): ciste_cislo(r.get("vyhry"), 0)
        for r in st.session_state.vysledky_db
        if cisty_text(r.get("datum")) == datum_str
    }

    # Při změně data synchronizujeme přihlášení podle uložených výsledků (nebo session)
    if st.session_state.get("naposledy_zvolene_datum") != datum_str:
        st.session_state.naposledy_zvolene_datum = datum_str
        dnesni_session_db = st.session_state.get("dnesni_session_db", {})

        if ulozene_vyhry_dne:
            st.session_state.prihlaseni = {
                h: (h in ulozene_vyhry_dne) for h in seznam_jmen_hracu
            }
        elif dnesni_session_db.get("datum") == datum_str and "prihlaseni" in dnesni_session_db:
            st.session_state.prihlaseni = dnesni_session_db.get("prihlaseni", {})
        else:
            st.session_state.prihlaseni = {h: False for h in seznam_jmen_hracu}

    if "prihlaseni" not in st.session_state:
        st.session_state.prihlaseni = {h: False for h in seznam_jmen_hracu}

    jednotlivci_stat = spocitej_statistiky(aktualni_rok)
    hraci_dle_ucasti = sorted(
        seznam_jmen_hracu,
        key=lambda h: jednotlivci_stat[h]["Středy"],
        reverse=True,
    )

    st.subheader("1️⃣ Kdo dnes hraje (Přihlášení)")
    st.caption("Kliknutím označ přítomné hráče (seřazeno od nejčastějších účastníků):")

    cols = st.columns(3)
    for idx, hrac in enumerate(hraci_dle_ucasti):
        je_prihlasen = st.session_state.prihlaseni.get(hrac, False)
        ucast_count = jednotlivci_stat[hrac]["Středy"]

        btn_label = (
            f"✅ {hrac} ({ucast_count}x)"
            if je_prihlasen
            else f"❌ {hrac} ({ucast_count}x)"
        )

        with cols[idx % 3]:
            if st.button(btn_label, key=f"btn_{hrac}", use_container_width=True):
                st.session_state.prihlaseni[hrac] = not je_prihlasen
                uloz_databazi(
                    st.session_state.vysledky_db,
                    st.session_state.tabulka_hraci,
                    st.session_state.vydaje,
                    ziskej_dnesni_session_dict(),
                )
                st.rerun()

    pritomni = [h for h in hraci_dle_ucasti if st.session_state.prihlaseni.get(h, False)]
    pocet = len(pritomni)
    dnes_vybrano = pocet * CENA_ZA_SESSION

    st.markdown("---")
    st.success(f"💰 **Dnes vybráno: {dnes_vybrano} Kč** ({pocet} hráčů × {CENA_ZA_SESSION} Kč)")

    # SEKCE 2: ZADÁNÍ POČTU VÝHER PRO PŘIHLÁŠENÉ HRÁČE
    st.subheader(f"2️⃣ Zadání a úprava výher ({datum_session.strftime('%d.%m.%Y')})")

    if ulozene_vyhry_dne:
        st.info(
            f"✏️ Pro datum **{datum_session.strftime('%d.%m.%Y')}** už jsou výsledky"
            " uložené. Můžeš je libovolně upravit a znovu uložit – staré záznamy"
            " pro tento den se bezpečně přepíší."
        )

    if not pritomni:
        st.warning("Nejprve nahoře kliknutím označ hráče, kteří dnes hráli.")
    else:
        zadane_vyhry = {}
        cols_v = st.columns(3)
        for idx_h, hrac_jmeno in enumerate(pritomni):
            with cols_v[idx_h % 3]:
                zadane_vyhry[hrac_jmeno] = st.number_input(
                    f"🏆 {hrac_jmeno}",
                    min_value=0,
                    max_value=40,
                    value=ulozene_vyhry_dne.get(hrac_jmeno, 0),
                    step=1,
                    key=f"win_input_{datum_str}_{hrac_jmeno}",
                )

        celkem_zadano_vyher = sum(zadane_vyhry.values())
        st.caption(f"Součet zadaných výher za dnešek: **{celkem_zadano_vyher}**")

        if st.button(
            f"💾 Uložit výsledky pro {datum_session.strftime('%d.%m.%Y')}",
            type="primary",
            use_container_width=True,
        ):
            # Odstraníme staré záznamy pro toto datum (prevence duplicit při opravách)
            st.session_state.vysledky_db = [
                r for r in st.session_state.vysledky_db
                if cisty_text(r.get("datum")) != datum_str
            ]

            existujici_ids = [
                ciste_cislo(r.get("id"), 0) for r in st.session_state.vysledky_db
            ]
            next_id = max(existujici_ids) + 1 if existujici_ids else 1

            # Uložíme všechny přihlášené hráče (i s 0 výhrami, aby se započítala účast a 30 Kč)
            for hrac_jmeno, pocet_vyher in zadane_vyhry.items():
                st.session_state.vysledky_db.append({
                    "id": next_id,
                    "datum": datum_str,
                    "hrac": hrac_jmeno,
                    "vyhry": int(pocet_vyher),
                })
                next_id += 1

            uloz_databazi(
                st.session_state.vysledky_db,
                st.session_state.tabulka_hraci,
                st.session_state.vydaje,
                ziskej_dnesni_session_dict(),
            )
            st.success(
                f"Výsledky pro **{datum_session.strftime('%d.%m.%Y')}** byly"
                f" uloženy ({len(zadane_vyhry)} hráčů, celkem {celkem_zadano_vyher} výher)!"
            )
            st.rerun()

# ==============================================================================
# TAB 2: ŽEBŘÍČKY & POKLADNA
# ==============================================================================
with tab2:
    try:
        st.subheader("📅 Výběr roku pro žebříček")
        zvoleny_rok = st.selectbox(
            "Zobrazit data pro rok:", [2026, 2025, 2024], index=0
        )

        jednotlivci_stat = spocitej_statistiky(zvoleny_rok)

        celkem_vybrano = sum(st_["Vybráno"] for st_ in jednotlivci_stat.values())
        celkem_vydaje = sum(
            ciste_cislo(v.get("castka"), 0)
            for v in st.session_state.vydaje
            if parsuj_rok(v.get("datum")) == zvoleny_rok
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
        st.subheader(
            f"📅 Výhry v jednotlivých středečních hracích dnech ({zvoleny_rok})"
        )

        vyhry_dny = []
        for r in st.session_state.vysledky_db:
            d = cisty_text(r.get("datum"))
            if parsuj_rok(d) != zvoleny_rok:
                continue
            h = cisty_text(r.get("hrac"))
            v = ciste_cislo(r.get("vyhry"), 0)
            if h:
                vyhry_dny.append({"Hráč": h, "Datum": d, "Výhry": v})

        df_v = pd.DataFrame(vyhry_dny)
        if not df_v.empty:
            vsechny_datumy = sorted(df_v["Datum"].astype(str).unique())
            vybrane_datumy = st.multiselect(
                "Filtrovat středeční datumy:",
                options=vsechny_datumy,
                default=vsechny_datumy,
            )

            df_v_filtered = df_v[df_v["Datum"].isin(vybrane_datumy)]
            if not df_v_filtered.empty:
                pivot_df = pd.pivot_table(
                    df_v_filtered,
                    index="Hráč",
                    columns="Datum",
                    values="Výhry",
                    aggfunc="sum",
                    fill_value=0,
                )
                pivot_df["Celkem"] = pivot_df.sum(axis=1)
                pivot_df = pivot_df.sort_values(by="Celkem", ascending=False)
                st.dataframe(pivot_df, use_container_width=True)
            else:
                st.info("Vyberte alespoň jedno datum pro zobrazení tabulky.")
        else:
            st.info(f"Pro rok {zvoleny_rok} nejsou v databázi zapsány žádné nové středy.")
    except Exception as e:
        st.error(f"Chyba při vykreslování žebříčků: {e}")

# ==============================================================================
# TAB 3: SPRÁVA & DATABÁZE
# ==============================================================================
with tab3:
    try:
        st.subheader("🗄️ Správa databázových tabulek")

        tab_db1, tab_db2 = st.tabs(["📊 Tabulka Výsledků", "👤 Tabulka Hráčů"])

        with tab_db1:
            st.markdown(
                "**Tabulka `vysledky`**  \n*(Přímá editace výher po dnech. Řádek"
                " smažeš zaškrtnutím vlevo a kliknutím na ikonu popelnice 🗑️ vpravo"
                " nahoře nad tabulkou)*"
            )

            # Rychlé smazání celého hracího dne
            with st.expander("🗑️ Smazat celý hrací den podle data"):
                dostupna_data = sorted(
                    list({cisty_text(r.get("datum")) for r in st.session_state.vysledky_db if cisty_text(r.get("datum"))}),
                    reverse=True,
                )
                if dostupna_data:
                    col_del1, col_del2 = st.columns([2, 1])
                    datum_ke_smazani = col_del1.selectbox(
                        "Vyber datum ke smazání:", options=dostupna_data
                    )
                    if col_del2.button("❌ Smazat den", use_container_width=True):
                        st.session_state.vysledky_db = [
                            r for r in st.session_state.vysledky_db
                            if cisty_text(r.get("datum")) != datum_ke_smazani
                        ]
                        uloz_databazi(
                            st.session_state.vysledky_db,
                            st.session_state.tabulka_hraci,
                            st.session_state.vydaje,
                            ziskej_dnesni_session_dict(),
                        )
                        st.success(f"Všechny záznamy pro datum {datum_ke_smazani} byly smazány!")
                        st.rerun()
                else:
                    st.info("V databázi zatím nejsou žádné záznamy.")

            if st.session_state.vysledky_db:
                rows = []
                for r in st.session_state.vysledky_db:
                    d_val = cisty_text(r.get("datum"))
                    try:
                        if "-" in d_val:
                            d_obj = datetime.strptime(d_val, "%Y-%m-%d").date()
                        elif "." in d_val:
                            d_obj = datetime.strptime(d_val, "%d.%m.%Y").date()
                        else:
                            d_obj = st.session_state.aktualni_datum_stredy
                    except Exception:
                        d_obj = st.session_state.aktualni_datum_stredy

                    rows.append({
                        "id": ciste_cislo(r.get("id"), 0),
                        "datum": d_obj,
                        "hrac": cisty_text(r.get("hrac")),
                        "vyhry": ciste_cislo(r.get("vyhry"), 0),
                    })
                df_edit = pd.DataFrame(rows).sort_values(
                    by=["datum", "vyhry"], ascending=[False, False]
                )
            else:
                df_edit = pd.DataFrame(columns=["id", "datum", "hrac", "vyhry"])

            edited_df = st.data_editor(
                df_edit,
                num_rows="dynamic",
                use_container_width=True,
                hide_index=True,
                key="db_editor_vysledky",
                column_config={
                    "id": st.column_config.NumberColumn(
                        "ID", disabled=True, help="Generuje se automaticky"
                    ),
                    "datum": st.column_config.DateColumn(
                        "Datum",
                        default=st.session_state.aktualni_datum_stredy,
                        format="YYYY-MM-DD",
                        required=True,
                    ),
                    "hrac": st.column_config.SelectboxColumn(
                        "Hráč", options=seznam_jmen_hracu, required=True
                    ),
                    "vyhry": st.column_config.NumberColumn(
                        "Výhry", min_value=0, max_value=40, default=0, required=True
                    ),
                },
            )

            if st.button(
                "💾 Uložit tabulku VÝSLEDKŮ", type="primary", use_container_width=True
            ):
                nove_vysledky = []
                kontrola_duplicit = set()
                chyba = False

                platna_ids = [
                    ciste_cislo(r.get("id"), 0) for r in st.session_state.vysledky_db
                ]
                next_id = max(platna_ids) + 1 if platna_ids else 1

                for idx, row in edited_df.iterrows():
                    h = cisty_text(row.get("hrac"))
                    if not h:
                        continue

                    raw_datum = row.get("datum")
                    if raw_datum is not None and not pd.isna(raw_datum):
                        datum_clean = str(raw_datum).split(" ")[0]
                    else:
                        datum_clean = str(st.session_state.aktualni_datum_stredy)

                    if (datum_clean, h) in kontrola_duplicit:
                        st.error(
                            f"⛔ CHYBA: Hráč **{h}** je pro datum **{datum_clean}**"
                            " v tabulce uveden vícekrát!"
                        )
                        chyba = True
                        break
                    kontrola_duplicit.add((datum_clean, h))

                    raw_id = ciste_cislo(row.get("id"), 0)
                    z_id = raw_id if raw_id > 0 else next_id
                    if raw_id <= 0:
                        next_id += 1

                    nove_vysledky.append({
                        "id": z_id,
                        "datum": datum_clean,
                        "hrac": h,
                        "vyhry": ciste_cislo(row.get("vyhry"), 0),
                    })

                if not chyba:
                    st.session_state.vysledky_db = nove_vysledky
                    uloz_databazi(
                        st.session_state.vysledky_db,
                        st.session_state.tabulka_hraci,
                        st.session_state.vydaje,
                        ziskej_dnesni_session_dict(),
                    )
                    st.success("Tabulka VÝSLEDKŮ byla úspěšně uložena!")
                    st.rerun()

        with tab_db2:
            st.markdown("**Tabulka `hraci`**  \n*(Správa seznamu hráčů)*")
            df_hraci = pd.DataFrame(st.session_state.tabulka_hraci)

            edited_hraci = st.data_editor(
                df_hraci,
                num_rows="dynamic",
                use_container_width=True,
                hide_index=True,
                key="db_editor_hraci",
                column_config={
                    "id": st.column_config.NumberColumn(
                        "ID", disabled=True, help="Generuje se automaticky"
                    ),
                    "hrac": st.column_config.TextColumn("Jméno hráče", required=True),
                },
            )

            if st.button(
                "💾 Uložit tabulku HRÁČŮ", type="primary", use_container_width=True
            ):
                novi_hraci = []
                platna_ids_h = [
                    ciste_cislo(h.get("id"), 0)
                    for h in st.session_state.tabulka_hraci
                ]
                next_h_id = max(platna_ids_h) + 1 if platna_ids_h else 1

                for idx, row in edited_hraci.iterrows():
                    jmeno = cisty_text(row.get("hrac"))
                    raw_id = ciste_cislo(row.get("id"), 0)

                    h_id = raw_id if raw_id > 0 else next_h_id
                    if raw_id <= 0:
                        next_h_id += 1

                    if jmeno:
                        novi_hraci.append({"id": h_id, "hrac": jmeno})

                st.session_state.tabulka_hraci = novi_hraci
                uloz_databazi(
                    st.session_state.vysledky_db,
                    st.session_state.tabulka_hraci,
                    st.session_state.vydaje,
                    ziskej_dnesni_session_dict(),
                )
                st.success("Tabulka HRÁČŮ byla úspěšně uložena!")
                st.rerun()

        st.markdown("---")
        db_json_data = json.dumps(
            {
                "vysledky": st.session_state.vysledky_db,
                "hraci": st.session_state.tabulka_hraci,
                "vydaje": st.session_state.vydaje,
                "dnesni_session": ziskej_dnesni_session_dict(),
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
                if "vysledky" in nactena_db:
                    st.session_state.vysledky_db = nactena_db.get("vysledky", [])
                else:
                    st.session_state.vysledky_db = preved_stare_zapasy_na_vysledky(
                        nactena_db.get("zapasy", [])
                    )
                st.session_state.tabulka_hraci = normalizuj_hrace(
                    nactena_db.get("hraci", DEFAULT_HRACI)
                )
                st.session_state.vydaje = nactena_db.get("vydaje", [])
                uloz_databazi(
                    st.session_state.vysledky_db,
                    st.session_state.tabulka_hraci,
                    st.session_state.vydaje,
                    ziskej_dnesni_session_dict(),
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
                    st.session_state.vysledky_db,
                    st.session_state.tabulka_hraci,
                    st.session_state.vydaje,
                    ziskej_dnesni_session_dict(),
                )
                st.success(f"Výdaj **{polozka_vydaj} ({castka_vydaj} Kč)** byl uložen!")
                st.rerun()
    except Exception as e:
        st.error(f"Chyba při vykreslování správy: {e}")
