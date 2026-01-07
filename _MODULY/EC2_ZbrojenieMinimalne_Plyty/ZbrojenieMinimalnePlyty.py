import streamlit as st
import math
import sys
import re
from pathlib import Path
from io import BytesIO
import streamlit.components.v1 as components

# --- KONFIGURACJA ŚCIEŻEK (WERSJA UNIWERSALNA) ---
SCIEZKA_PLIKU = Path(__file__).resolve()
SCIEZKA_FOLDERU_LOKALNEGO = SCIEZKA_PLIKU.parent

def znajdz_sciezke_do_zasobu(nazwa_folderu, nazwa_pliku=""):
    """
    Szuka folderu w bieżącej lokalizacji i w folderach nadrzędnych.
    Działa jak 'Auto-Wykrywanie' na budowie.
    """
    biezaca_sciezka = SCIEZKA_PLIKU

# Szukamy folderu TABLICE
SCIEZKA_TABLICE = znajdz_sciezke_do_zasobu("TABLICE")
if SCIEZKA_TABLICE and str(SCIEZKA_TABLICE.parent) not in sys.path:
    sys.path.append(str(SCIEZKA_TABLICE.parent))

# --- SYMBOLE UNICODE (jak w zakładzie) ---
SYM = {
    "fi": "\u03A6", "alpha": "\u03B1", "sigma": "\u03C3",
    "dot": "\u00B7", "ge": "\u2265", "le": "\u2264", "Delta": "\u0394"
}

# =============================================================================
# TABLICE
# =============================================================================
# Beton – preferuj TABLICE.ParametryBetonu (fallback zostaje)
BETON_FCTM_FALLBACK = {
    "C12/15": 1.6, "C16/20": 1.9, "C20/25": 2.2,
    "C25/30": 2.6, "C30/37": 2.9, "C35/45": 3.2,
    "C40/50": 3.5, "C45/55": 3.8, "C50/60": 4.1
}

try:
    from TABLICE.ParametryBetonu import CONCRETE_TABLE, list_concrete_classes  # type: ignore
    BETON_CLASSES = list_concrete_classes()
    BETON_FCTM = {k: float(v.fctm) for k, v in CONCRETE_TABLE.items()}
except Exception:
    BETON_CLASSES = list(BETON_FCTM_FALLBACK.keys())
    BETON_FCTM = BETON_FCTM_FALLBACK

STAL_DATA_FALLBACK = {"B500B": 500, "B500A": 500, "B500C": 500, "RB500W": 500}
try:
    from TABLICE.ParametryStali import STEEL_TABLE  # type: ignore
    STAL_DATA = {k: float(v.fyk) for k, v in STEEL_TABLE.items()}
except Exception:
    STAL_DATA = STAL_DATA_FALLBACK

try:
    from TABLICE.ParametryPretowZbrojeniowych import list_bar_diameters  # type: ignore
    FI_LIST = list_bar_diameters()
except Exception:
    FI_LIST = [6, 8, 10, 12, 14, 16, 18, 20, 22, 25, 28, 32, 40]

# PN-EN 1992-1-1:2004+AC:2008 – Tablica 7.2N
TAB_7_2N = {
    0.4: [(160, 40), (200, 32), (240, 20), (280, 16), (320, 12), (360, 10), (400, 8), (450, 6)],
    0.3: [(160, 32), (200, 25), (240, 16), (280, 12), (320, 10), (360, 8), (400, 6), (450, 5)],
    0.2: [(160, 25), (200, 16), (240, 12), (280, 8), (320, 6), (360, 5), (400, 4)],
}

# =============================================================================
# FUNKCJE
# =============================================================================
def k_from_h_mm(h_mm: float) -> float:
    if h_mm <= 300.0:
        return 1.0
    if h_mm >= 800.0:
        return 0.65
    return 1.0 - (h_mm - 300.0) / 500.0 * 0.35


def fcteff_label(alpha: float) -> str:
    if abs(alpha - 1.0) < 1e-9:
        return "1.00 · fctm — po 28 dniach"
    if abs(alpha - 0.9) < 1e-9:
        return "0.90 · fctm — ~12–14 dni"
    if abs(alpha - 0.8) < 1e-9:
        return "0.80 · fctm — ~6–7 dni"
    if abs(alpha - 0.7) < 1e-9:
        return "0.70 · fctm — ~3–5 dni"
    if abs(alpha - 0.6) < 1e-9:
        return "0.60 · fctm — ~2 dni"
    return "0.50 · fctm — ~1 dzień"


def phi_transform_factor(fct_eff: float, kc: float, hcr_mm: float, h_minus_d_mm: float, mode: str) -> float:
    # (7.6N) i (7.7N)
    if h_minus_d_mm <= 0:
        return 0.0
    base = fct_eff / 2.9
    if mode == "Zginanie":
        return base * (kc * hcr_mm) / (2.0 * h_minus_d_mm)
    return base * (hcr_mm) / (8.0 * h_minus_d_mm)


def sigma_from_tab72N(phi_star_req: float, wk: float):
    if wk not in TAB_7_2N:
        return None

    pts = [(float(s), float(p)) for s, p in TAB_7_2N[wk]]
    pts.sort(key=lambda x: x[0])  # σ rosnąco

    # Jeżeli potrzebujemy większej średnicy niż największa w tabeli (dla najmniejszego σ) – brak
    if phi_star_req > pts[0][1]:
        return None

    # Jeżeli potrzeba średnicy <= najmniejszej w tabeli (dla największego σ) – przyjmij największe σ
    if phi_star_req <= pts[-1][1]:
        return pts[-1][0]

    for i in range(len(pts) - 1):
        s1, p1 = pts[i]
        s2, p2 = pts[i + 1]
        if p1 >= phi_star_req >= p2:
            if abs(p1 - p2) < 1e-12:
                return s1
            frac = (p1 - phi_star_req) / (p1 - p2)
            return s1 + (s2 - s1) * frac

    return None


def sigma_s_din(fi_mm: float, wk_mm: float, k: float, fct_eff_mpa: float, fy_mpa: float) -> float:
    # Es stałe – nie pokazujemy w UI
    Es = 200000.0  # MPa
    fi_mm = max(fi_mm, 1e-6)
    wk_mm = max(wk_mm, 0.0)
    val = math.sqrt(max(0.0, (6.0 * wk_mm * k * fct_eff_mpa * Es) / fi_mm))
    return min(val, fy_mpa)


def render_table_72N_html() -> str:
    sigmas = sorted({s for wk, rows in TAB_7_2N.items() for s, _ in rows})
    cols = [0.4, 0.3, 0.2]

    map_phi = {wk: {s: None for s in sigmas} for wk in cols}
    for wk in cols:
        for s, p in TAB_7_2N.get(wk, []):
            map_phi[wk][float(s)] = float(p)

    def fmt(wk, s):
        v = map_phi[wk].get(s, None)
        return "–" if v is None else f"{v:.0f}"

    html = """
    <div style="width:100%; overflow-x:auto; padding:10px 0;">
      <style>
        table.ec2 {
          width: 100%;
          border-collapse: collapse;
          font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial;
          font-size: 14px;
          background: #111827;
          color: #E5E7EB;
        }
        table.ec2 th, table.ec2 td {
          border: 1px solid #374151;
          padding: 10px 8px;
          text-align: center;
          vertical-align: middle;
          white-space: nowrap;
        }
        table.ec2 th {
          background: #1F2937;
          font-weight: 800;
        }
        table.ec2 tr:nth-child(even) td { background: #0F172A; }
        table.ec2 tr:nth-child(odd) td { background: #111827; }
      </style>

      <table class="ec2">
        <tr>
          <th>σ<sub>s</sub> [MPa]</th>
          <th>w<sub>k</sub> = 0.4 mm<br>φ* [mm]</th>
          <th>w<sub>k</sub> = 0.3 mm<br>φ* [mm]</th>
          <th>w<sub>k</sub> = 0.2 mm<br>φ* [mm]</th>
        </tr>
    """
    for s in sigmas:
        html += f"""
        <tr>
          <td>{s:.0f}</td>
          <td>{fmt(0.4, s)}</td>
          <td>{fmt(0.3, s)}</td>
          <td>{fmt(0.2, s)}</td>
        </tr>
        """
    html += """
      </table>
    </div>
    """
    return html

# =============================================================================
# STRONA
# =============================================================================
def StronaZbrojenieMinimalnePlyty():

    st.markdown(
        """
        <style>
        .block-container { padding-top: 1.5rem; padding-bottom: 1.5rem; }
        h3 { margin-top: 1.0rem !important; margin-bottom: 0.4rem !important; font-size: 1.1rem; }
        div.row-widget.stRadio > div { flex-direction: row; gap: 16px; }

        /* Guzik OBLICZ – mniejszy */
        button[kind="primary"] {
            background: #ff4b4b !important;
            border: none !important;
            border-radius: 12px !important;
            height: 52px !important;
            font-size: 17px !important;
            font-weight: 900 !important;
            letter-spacing: 0.5px !important;
        }
        button[kind="primary"]:hover { filter: brightness(0.95); }

        .result-card {
            background:#1f2937; border:1px solid #374151; border-radius:10px;
            padding:18px 14px; text-align:center;
        }
        .result-title {
            font-size: 14px; font-weight: 800; color:#e5e7eb;
            margin-bottom: 8px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
        }
        .result-sym { font-size: 14px; font-weight: 900; color:#cbd5e1; margin-bottom: 8px; }
        .result-val { font-size: 30px; font-weight: 900; color:#ffffff; line-height: 1.1; }
        .result-unit { font-size: 16px; font-weight: 800; color:#cbd5e1; }

        /* Styl wyniku głównego – JEDNA LINIA */
        .big-result {
            font-size: 24px; font-weight: bold; color: #2E8B57; background-color: #f0f2f6;
            padding: 15px; border-radius: 8px; text-align: center; margin-top: 20px; border: 2px solid #2E8B57;
            display: flex; align-items: center; justify-content: center; gap: 10px; flex-wrap: wrap;
        }
        .max-result {
            font-size: 24px; font-weight: bold; color: #856404; background-color: #fff3cd;
            padding: 15px; border-radius: 8px; text-align: center; margin-top: 20px; border: 2px solid #ffeeba;
            display: flex; align-items: center; justify-content: center; gap: 10px; flex-wrap: wrap;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # TYTUŁ
    st.markdown(
        """
        <div style="text-align:center; margin-top:0.4rem; margin-bottom:0rem;">
            <span style="font-size:36px; font-weight:800; letter-spacing:1px; color:#dddddd;">
                ZBROJENIE MINIMALNE I MAKSYMALNE PŁYT
            </span>
        </div>
        <div style="text-align:center; font-size:14px; color:#aaaaaa; margin-top:-12px; margin-bottom:0.6rem;">
            wg PN-EN 1992-1-1
        </div>
        """,
        unsafe_allow_html=True
    )

    # Inicjalizacja stanu i funkcja resetująca
    if "zmpp_calculated" not in st.session_state:
        st.session_state.zmpp_calculated = False
    if "zmpp_payload" not in st.session_state:
        st.session_state.zmpp_payload = None

    def reset_results():
        st.session_state.zmpp_calculated = False
        st.session_state.zmpp_payload = None

    # -------------------------------------------------------------------------
    # DANE WEJŚCIOWE
    # -------------------------------------------------------------------------
    st.markdown("### DANE WEJŚCIOWE")

    r1c1, r1c2, r1c3, r1c4  = st.columns(4)
    with r1c1:
        idx_c30 = BETON_CLASSES.index("C30/37") if "C30/37" in BETON_CLASSES else 0
        beton = st.selectbox("Klasa betonu", BETON_CLASSES, index=idx_c30, on_change=reset_results)
        fctm = float(BETON_FCTM[beton])
    with r1c2:
        h_cm = float(st.number_input("Grubość płyty h [cm]", value=20.0, step=1.0, on_change=reset_results))
    with r1c3:
        def_fi_idx = FI_LIST.index(12) if 12 in FI_LIST else 0
        fi = float(st.selectbox(f"Średnica pręta {SYM['fi']} [mm]", FI_LIST, index=def_fi_idx, on_change=reset_results))
    with r1c4:
        stal_opts = list(STAL_DATA.keys())
        if "B500B" in stal_opts:
            def_idx = stal_opts.index("B500B")
        elif "B500" in stal_opts:
            def_idx = stal_opts.index("B500")
        else:
            def_idx = 0
        stal = st.selectbox("Klasa stali", stal_opts, index=def_idx, on_change=reset_results)
        fyk = float(STAL_DATA.get(stal, 500.0))


    r2c1, r2c2, r2c3, r2c4 = st.columns(4)
    
    with r2c1:
        c_nom = int(st.number_input("Otulina nominalna $c_{nom}$ [mm]", value=30, step=1, on_change=reset_results))  
    with r2c2:
        wk = float(st.selectbox("Dopuszczalna szerokość rysy $w_k$ [mm]", [0.10, 0.20, 0.30, 0.40], index=2, on_change=reset_results))
    with r2c3:
        ALPHAS = [0.50, 0.60, 0.70, 0.80, 0.90, 1.00]
        alpha_fct = float(
            st.selectbox(
                "Wartość $f_{ct,eff}$ jako część $f_{ctm}$ betonu",
                options=ALPHAS,
                index=ALPHAS.index(1.00),
                format_func=lambda a: fcteff_label(float(a)),
                on_change=reset_results
            )
        )
    with r2c4:
        tryb = st.radio("Rodzaj oddziaływania", ["Zginanie", "Rozciąganie"], index=0, horizontal=True, on_change=reset_results)

    fct_eff = alpha_fct * fctm

    
    # -------------------------------------------------------------------------
    # Podejście do wyznaczenia σs
    # -------------------------------------------------------------------------
    st.markdown(f"**Podejście do wyznaczenia {SYM['sigma']}ₛ**")
    
    # NOWA WSKAZÓWKA
    st.info(
        "ℹ️ **Wskazówka:** Podejście obliczeniowe do wyznaczania naprężeń w stali według PN-EN daje, zgodnie z dostępną literaturą, "
        "bardzo konserwatywne wartości. W praktyce wielu inżynierów stosuje "
        "dokładny wzór zaczerpnięty z normy niemieckiej (**DIN 1045-1**), który wyznacza bardziej "
        "realistyczne wartości naprężeń w stali."
    )

    # Definicja opcji - zapamiętujemy dokładne nazwy
    OPCJA_PN = "Wg PN-EN-1992-1-1"
    OPCJA_DIN = "Wg DIN-1045-1"

    sigma_choice = st.radio(
        "sigma_choice_hidden",
        [OPCJA_PN, OPCJA_DIN],
        index=0,
        horizontal=True,
        label_visibility="collapsed",
        on_change=reset_results
    )

    # TU WRÓCIŁ OPIS "Przyjęte naprężenia w stali..." Z ODPOWIEDNIĄ CZCIONKĄ
    if st.session_state.get("zmpp_calculated") and st.session_state.get("zmpp_payload"):
        payload = st.session_state.zmpp_payload
        if not payload.get("error"):
            sigma_s_disp = payload["sigma_s"]
            # To jest to, co chciałeś przywrócić
            st.text_input(f"Wartość naprężeń w stali {SYM['sigma']}ₛ", value=f"{sigma_s_disp:.1f} MPa", disabled=True, key="dp_ct_disp_yes")
           
    sigma_mode = sigma_choice
    
    # POPRAWKA: Używamy pełnej nazwy zmiennej OPCJA_PN
    if abs(wk - 0.10) < 1e-12 and sigma_choice == OPCJA_PN:
        sigma_mode = OPCJA_DIN
        st.info("Dla $w_k = 0.10$ mm Tablica 7.2N nie ma zastosowania (obejmuje $w_k = 0.2/0.3/0.4$ mm). Obliczenia wykonano wg DIN.")

    # POPRAWKA: Używamy pełnej nazwy zmiennej OPCJA_PN
    if sigma_mode == OPCJA_PN:
        with st.expander("ℹ️ Pomoc: Ograniczenie zarysowania wg PN-EN 1992-1-1 (Tablica 7.2N)", expanded=False):
            components.html(render_table_72N_html(), height=420, scrolling=True)

    # -------------------------------------------------------------------------
    # PRZYCISK OBLICZ
    # -------------------------------------------------------------------------
    
    _, c_btn, _ = st.columns([1, 2, 1])
    with c_btn:
        # Kliknięcie przycisku
        if st.button("OBLICZ", type="primary", use_container_width=True):
            st.session_state.zmpp_calculated = True

            b = 100.0  # cm (pasmo 1 m)
            d_cm = h_cm - (c_nom / 10.0) - (fi / 20.0)  # cm

            if d_cm <= 0:
                st.session_state.zmpp_payload = {"error": "Błąd geometrii: d ≤ 0. Sprawdź h, cnom oraz Φ."}
                st.rerun()

            h_mm = h_cm * 10.0
            d_mm = d_cm * 10.0
            h_minus_d_mm = h_mm - d_mm
            if h_minus_d_mm <= 0:
                st.session_state.zmpp_payload = {"error": "Błąd geometrii: (h − d) ≤ 0."}
                st.rerun()

            k = k_from_h_mm(h_mm)
            kc = 0.4 if tryb == "Zginanie" else 1.0
            hcr_mm = (0.5 * h_mm) if tryb == "Zginanie" else (1.0 * h_mm)
            Act = (0.5 if tryb == "Zginanie" else 1.0) * b * h_cm  # cm²

            phi_star_req = None
            sigma_lim = None

            # LOGIKA OBLICZENIOWA
            if sigma_mode == OPCJA_PN:
                if wk not in (0.2, 0.3, 0.4):
                    st.session_state.zmpp_payload = {"error": "Dla podejścia wg PN-EN dostępne jest wk = 0.2/0.3/0.4 mm."}
                    st.rerun()

                F = phi_transform_factor(fct_eff=fct_eff, kc=kc, hcr_mm=hcr_mm, h_minus_d_mm=h_minus_d_mm, mode=tryb)
                if F <= 0:
                    st.session_state.zmpp_payload = {"error": "Nie można wyznaczyć przekształcenia średnicy (F ≤ 0)."}
                    st.rerun()

                phi_star_req = fi / F
                sigma_lim = sigma_from_tab72N(phi_star_req=phi_star_req, wk=wk)
                if sigma_lim is None:
                    # Rozbudowany komunikat błędu
                    st.session_state.zmpp_payload = {"error": "Brak rozwiązania w zakresie Tablicy 7.2N dla przyjętych danych (zbyt duże wymagane naprężenia dla tej szerokości rysy). Zaleca się użycie metody DIN."}
                    st.rerun()

                sigma_s = min(float(sigma_lim), float(fyk))
            else:
                # DIN
                sigma_s = float(sigma_s_din(fi_mm=fi, wk_mm=wk, k=k, fct_eff_mpa=fct_eff, fy_mpa=fyk))

            # ZAPIS WYNIKÓW
            st.session_state.zmpp_payload = {
                "k": k, "kc": kc, "Act": Act, "d_cm": d_cm, "sigma_s": sigma_s,
                "b": b, "h": h_cm, "beton": beton, "fctm": fctm, "stal": stal,
                "fyk": fyk, "fct_eff": fct_eff, "As_min_1": 0.0, "As_min_2": 0.0, # obliczane przy wyświetlaniu
                "sigma_mode": sigma_mode
            }
            # WYMUSZENIE ODŚWIEŻENIA STRONY
            st.rerun()

    # -------------------------------------------------------------------------
    # WYNIKI + RAPORTY + SZCZEGÓŁY
    # -------------------------------------------------------------------------
    if st.session_state.zmpp_calculated and st.session_state.zmpp_payload is not None:
        payload = st.session_state.zmpp_payload

        if payload.get("error"):
            st.error(payload["error"])
            return

        k = float(payload["k"])
        kc = float(payload["kc"])
        Act = float(payload["Act"])
        d_cm = float(payload["d_cm"])
        sigma_s = float(payload["sigma_s"])
        b = float(payload["b"])
        sigma_mode = str(payload.get("sigma_mode", sigma_mode))

        As_min_1 = max(0.26 * (fctm / fyk) * b * d_cm, 0.0013 * b * d_cm)
        As_min_2 = (kc * k * fct_eff * Act) / max(float(sigma_s), 1e-12)
        As_min = max(As_min_1, As_min_2)
        
        # As max
        Ac_slab = b * h_cm
        As_max = 0.04 * Ac_slab

        st.markdown("### WYNIKI")

        def card(title: str, sym_html: str, value: float):
            return f"""
            <div class="result-card">
                <div class="result-title">{title}</div>
                <div class="result-sym">{sym_html}</div>
                <div class="result-val">{value:.2f} <span class="result-unit">cm²/m</span></div>
            </div>
            """

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(card("Zbrojenie minimalne — kruche zniszczenie", "A<sub>s,min,1</sub>", As_min_1), unsafe_allow_html=True)
        with col2:
            st.markdown(card("Zbrojenie minimalne — zarysowanie", "A<sub>s,min,2</sub>", As_min_2), unsafe_allow_html=True)

        st.markdown(
            f"""
            <div class="big-result">
                <span>Zbrojenie minimalne</span>
                <span><i>A</i><sub>s,min</sub> = {As_min:.2f} cm²/m</span>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            f"""
            <div class="max-result">
                <span>Zbrojenie maksymalne</span>
                <span><i>A</i><sub>s,max</sub> = {As_max:.2f} cm²/m</span>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

        wynik = {
            "As_min_1": As_min_1,
            "As_min_2": As_min_2,
            "As_min": As_min,
            "As_max": As_max,
            "b": b,
            "h": h_cm,
            "d": d_cm,
            "beton": beton,
            "fctm": fctm,
            "stal": stal,
            "fyk": fyk,
            "fct_eff": fct_eff,
            "Act": Act,
            "k": k,
            "kc": kc,
            "sigma_s": sigma_s
        }
         
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        with st.expander("Szczegóły obliczeń", expanded=False):
            st.markdown("#### 1. Parametry geometryczne i materiałowe")
            st.write(f"Przekrój: **b = {b:.0f} cm**, **h = {h_cm:.1f} cm**, **d = {d_cm:.2f} cm**")
            st.write(f"Beton: **{beton}** ($f_{{ctm}} = {fctm:.2f}$ MPa)")
            st.write(f"Stal: **{stal}** ($f_{{yk}} = {fyk:.0f}$ MPa)")

            st.markdown("#### 2. Parametry do obliczeń zarysowania")
            st.write("Efektywna wytrzymałość betonu na rozciąganie:")
            st.latex(rf"f_{{ct,eff}} = \alpha \cdot f_{{ctm}} = {alpha_fct:.2f} \cdot {fctm:.2f} \text{{ MPa}} = \mathbf{{{fct_eff:.2f}}} \text{{ MPa}}")
            st.write("Pole strefy rozciąganej ($A_{{ct}}$) i współczynniki:")
            st.latex(rf"A_{{ct}} = {Act:.1f} \text{{ cm}}^2, \quad k = {k:.3f}, \quad k_c = {kc:.1f}")
            st.write("Naprężenia w stali:")
            st.latex(rf"\sigma_s = \mathbf{{{sigma_s:.1f}}} \text{{ MPa}}")

            st.markdown("#### 3. Warunek kruchego zniszczenia ($A_{{s,min,1}}$)")
            st.latex(
                rf"A_{{s,min,1}} = \max\left( 0.26 \frac{{f_{{ctm}}}}{{f_{{yk}}}} b d ; 0.0013 b d \right) "
                rf"= \max\left( 0.26 \frac{{{fctm:.2f} \text{{ MPa}}}}{{{fyk:.0f} \text{{ MPa}}}} \cdot {b:.0f} \text{{ cm}} \cdot {d_cm:.2f} \text{{ cm}} ; "
                rf"0.0013 \cdot {b:.0f} \text{{ cm}} \cdot {d_cm:.2f} \text{{ cm}} \right) "
                rf"= \mathbf{{{As_min_1:.2f}}} \text{{ cm}}^2/\text{{m}}"
            )

            st.markdown("#### 4. Warunek ograniczenia zarysowania ($A_{{s,min,2}}$)")
            st.latex(
                rf"A_{{s,min,2}} = \frac{{k_c \cdot k \cdot f_{{ct,eff}} \cdot A_{{ct}}}}{{\sigma_s}} "
                rf"= \frac{{{kc:.1f} \cdot {k:.3f} \cdot {fct_eff:.2f} \text{{ MPa}} \cdot {Act:.1f} \text{{ cm}}^2}}{{{sigma_s:.1f} \text{{ MPa}}}} "
                rf"= \mathbf{{{As_min_2:.2f}}} \text{{ cm}}^2/\text{{m}}"
            )

            st.markdown("#### 5. Wyniki końcowe")
            st.latex(rf"A_{{s,min}} = \max(A_{{s,min,1}}; A_{{s,min,2}}) = \max({As_min_1:.2f}; {As_min_2:.2f}) = \mathbf{{{As_min:.2f}}} \text{{ cm}}^2/\text{{m}}")
            st.latex(rf"A_{{s,max}} = 0.04 \cdot A_c = 0.04 \cdot {b:.0f} \cdot {h_cm:.1f} = \mathbf{{{As_max:.2f}}} \text{{ cm}}^2/\text{{m}}")


if __name__ == "__main__":
    StronaZbrojenieMinimalnePlyty()