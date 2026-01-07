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

# --- SYMBOLE ---
SYM = {
    "fi": "\u03A6", "alpha": "\u03B1", "sigma": "\u03C3",
    "dot": "\u00B7", "ge": "\u2265", "le": "\u2264"
}

# =============================================================================
# TABLICE I DANE
# =============================================================================
try:
    from TABLICE.ParametryBetonu import list_concrete_classes, get_concrete_params, CONCRETE_TABLE
    BETON_CLASSES = list_concrete_classes()
    BETON_FCTM = {k: float(get_concrete_params(k).fctm) for k in BETON_CLASSES}
except Exception:
    BETON_CLASSES = ["C12/15", "C16/20", "C20/25", "C25/30", "C30/37", "C35/45", "C40/50", "C45/55", "C50/60"]
    BETON_FCTM = {"C30/37": 2.9}

try:
    from TABLICE.ParametryStali import list_steel_grades, get_steel_params, STEEL_TABLE
    STAL_GRADES = list_steel_grades()
    STAL_FYK = {k: float(get_steel_params(k).fyk) for k in STAL_GRADES}
except Exception:
    STAL_GRADES = ["B500", "B500B", "RB500W"]
    STAL_FYK = {"B500": 500.0, "B500B": 500.0}

try:
    from TABLICE.ParametryPretowZbrojeniowych import list_bar_diameters
    FI_LIST = list_bar_diameters()
except Exception:
    FI_LIST = [6, 8, 10, 12, 14, 16, 20, 25, 32]

# PN-EN 1992-1-1 Tablica 7.2N (do zarysowania)
TAB_7_2N = {
    0.4: [(160, 40), (200, 32), (240, 20), (280, 16), (320, 12), (360, 10), (400, 8), (450, 6)],
    0.3: [(160, 32), (200, 25), (240, 16), (280, 12), (320, 10), (360, 8), (400, 6), (450, 5)],
    0.2: [(160, 25), (200, 16), (240, 12), (280, 8), (320, 6), (360, 5), (400, 4)],
}

# =============================================================================
# FUNKCJE POMOCNICZE
# =============================================================================
def k_from_h_mm(h_mm: float) -> float:
    if h_mm <= 300.0: return 1.0
    if h_mm >= 800.0: return 0.65
    return 1.0 - (h_mm - 300.0) / 500.0 * 0.35

def fcteff_label(alpha: float) -> str:
    if abs(alpha - 1.0) < 1e-9: return "1.00 · fctm — po 28 dniach"
    if abs(alpha - 0.9) < 1e-9: return "0.90 · fctm — ~12–14 dni"
    if abs(alpha - 0.8) < 1e-9: return "0.80 · fctm — ~6–7 dni"
    if abs(alpha - 0.7) < 1e-9: return "0.70 · fctm — ~3–5 dni"
    if abs(alpha - 0.6) < 1e-9: return "0.60 · fctm — ~2 dni"
    return "0.50 · fctm — ~1 dzień"

def phi_transform_factor_tension(fct_eff: float, hcr_mm: float, h_minus_d_mm: float) -> float:
    # Wzór (7.7N) dla rozciągania: F = fct,eff/2.9 * hcr / (8(h-d))
    if h_minus_d_mm <= 0: return 0.0
    base = fct_eff / 2.9
    return base * (hcr_mm) / (8.0 * h_minus_d_mm)

def sigma_from_tab72N(phi_star_req: float, wk: float):
    if wk not in TAB_7_2N: return None
    pts = [(float(s), float(p)) for s, p in TAB_7_2N[wk]]
    pts.sort(key=lambda x: x[0])
    if phi_star_req > pts[0][1]: return None
    if phi_star_req <= pts[-1][1]: return pts[-1][0]
    for i in range(len(pts) - 1):
        s1, p1 = pts[i]
        s2, p2 = pts[i + 1]
        if p1 >= phi_star_req >= p2:
            frac = (p1 - phi_star_req) / (p1 - p2)
            return s1 + (s2 - s1) * frac
    return None

def sigma_s_din(fi_mm: float, wk_mm: float, k: float, fct_eff_mpa: float, fy_mpa: float) -> float:
    Es = 200000.0
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
    html = """<div style="width:100%; overflow-x:auto; padding:10px 0;"><style>table.ec2 { width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 14px; background: #111827; color: #E5E7EB; } table.ec2 th, table.ec2 td { border: 1px solid #374151; padding: 10px 8px; text-align: center; white-space: nowrap; } table.ec2 th { background: #1F2937; font-weight: 800; } table.ec2 tr:nth-child(even) td { background: #0F172A; }</style><table class="ec2"><tr><th>σ<sub>s</sub> [MPa]</th><th>w<sub>k</sub>=0.4<br>φ* [mm]</th><th>w<sub>k</sub>=0.3<br>φ* [mm]</th><th>w<sub>k</sub>=0.2<br>φ* [mm]</th></tr>"""
    for s in sigmas:
        html += f"<tr><td>{s:.0f}</td><td>{fmt(0.4, s)}</td><td>{fmt(0.3, s)}</td><td>{fmt(0.2, s)}</td></tr>"
    html += "</table></div>"
    return html


# =============================================================================
# STRONA GŁÓWNA
# =============================================================================
def StronaZbrojenieMinimalneSciany():
    # CSS IDENTYCZNY JAK W PŁYTACH
    st.markdown("""
        <style>
        .block-container { padding-top: 1.5rem; padding-bottom: 1.5rem; }
        h3 { margin-top: 1.0rem !important; margin-bottom: 0.4rem !important; font-size: 1.1rem; }
        div.row-widget.stRadio > div { flex-direction: row; gap: 16px; }
        
        button[kind="primary"] { 
            background: #ff4b4b !important; 
            border: none !important; 
            border-radius: 12px !important; 
            height: 52px !important; 
            font-weight: 900 !important; 
            font-size: 17px !important; 
            letter-spacing: 0.5px !important; 
        }
        button[kind="primary"]:hover { filter: brightness(0.95); }

        .big-result { 
            font-size: 24px; font-weight: bold; color: #2E8B57; background-color: #f0f2f6; 
            padding: 15px; border-radius: 8px; text-align: center; margin-top: 20px; 
            border: 2px solid #2E8B57; display: flex; align-items: center; justify-content: center; 
            gap: 10px; flex-wrap: wrap; 
        }
        .max-result { 
            font-size: 24px; font-weight: bold; color: #856404; background-color: #fff3cd; 
            padding: 15px; border-radius: 8px; text-align: center; margin-top: 20px; 
            border: 2px solid #ffeeba; display: flex; align-items: center; justify-content: center; 
            gap: 10px; flex-wrap: wrap; 
        }
        </style>
    """, unsafe_allow_html=True)

    # NAGŁÓWEK
    st.markdown(
        """
        <div style="text-align:center; margin-top:0.4rem; margin-bottom:0rem;">
            <span style="font-size:36px; font-weight:800; letter-spacing:1px; color:#dddddd;">
                ZBROJENIE MINIMALNE ŚCIAN I TARCZ
            </span>
        </div>
        <div style="text-align:center; font-size:14px; color:#aaaaaa; margin-top:-12px; margin-bottom:0.6rem;">
            wg PN-EN 1992-1-1
        </div>
        """,
        unsafe_allow_html=True
    )

    # --- ZMIENNE SESJI I FUNKCJE RESETUJĄCE ---
    # Dla ściany (Tab 1)
    if "zms_w_calculated" not in st.session_state:
        st.session_state.zms_w_calculated = False
    if "zms_w_payload" not in st.session_state:
        st.session_state.zms_w_payload = None

    # Dla tarczy (Tab 2)
    if "zms_t_calculated" not in st.session_state:
        st.session_state.zms_t_calculated = False
    if "zms_t_payload" not in st.session_state:
        st.session_state.zms_t_payload = None

    def reset_wall():
        st.session_state.zms_w_calculated = False
        st.session_state.zms_w_payload = None

    def reset_tension():
        st.session_state.zms_t_calculated = False
        st.session_state.zms_t_payload = None

    # ZAKŁADKI
    tab1, tab2 = st.tabs(["ŚCIANA ŻELBETOWA (ELEMENT ŚCISKANY)", "TARCZA ŻELBETOWA (ELEMENT ROZCIĄGANY)"])

    # === ZAKŁADKA 1: ŚCIANA ŚCISKANA (9.6) ===
    with tab1:
        st.markdown("### DANE WEJŚCIOWE")
        c1, c2 = st.columns(2)
        with c1:
            h_cm_w = st.number_input("Grubość ściany h [cm]", value=20.0, step=1.0, key="w_h", on_change=reset_wall)
        with c2:
            b_cm_w = st.number_input("Szerokość rozpatrywana b [cm]", value=100.0, step=10.0, help="Zazwyczaj 100 cm", key="w_b", on_change=reset_wall)

        # Button (50% width)
        _, c_btn_t1, _ = st.columns([1, 2, 1])
        with c_btn_t1:
            if st.button("OBLICZ", type="primary", use_container_width=True, key="btn_t1"):
                st.session_state.zms_w_calculated = True
                Ac_cm2 = b_cm_w * h_cm_w
                # Obliczenia
                As_vmin = 0.002 * Ac_cm2
                As_hmin = max(0.25 * As_vmin, 0.001 * Ac_cm2)
                As_max = 0.04 * Ac_cm2
                
                st.session_state.zms_w_payload = {
                    "mode": "sciana", "typ": "Ściana ściskana (9.6)",
                    "h_cm": h_cm_w, "b_cm": b_cm_w, "Ac_cm2": Ac_cm2,
                    "As_vmin": As_vmin, "cond1": 0.25*As_vmin, "cond2": 0.001*Ac_cm2,
                    "As_hmin": As_hmin, "As_max": As_max
                }
                st.rerun()

        # Wyniki - WYŚWIETLANE POZA KOLUMNAMI (FULL WIDTH)
        if st.session_state.zms_w_calculated and st.session_state.zms_w_payload:
            res_w = st.session_state.zms_w_payload
            
            st.markdown("### WYNIKI")
            st.markdown(f"""
                <div class="big-result">
                    <span>Zbrojenie pionowe (całkowite)</span>
                    <span><i>A</i><sub>s,vmin</sub> = {res_w['As_vmin']:.2f} cm²</span>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
                <div class="big-result" style="border-color: #4682B4; color: #4682B4;">
                    <span>Zbrojenie poziome (całkowite)</span>
                    <span><i>A</i><sub>s,hmin</sub> = {res_w['As_hmin']:.2f} cm²</span>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
                <div class="max-result">
                    <span>Zbrojenie maksymalne</span>
                    <span><i>A</i><sub>s,max</sub> = {res_w['As_max']:.2f} cm²</span>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown("")
            st.warning("☝️ Podane wyniki to **całkowite zbrojenie w przekroju**. Zgodnie z normą, połowę tego zbrojenia należy umieścić przy każdej powierzchni ściany.")


            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            with st.expander("Szczegóły obliczeń"):
                st.write("**1. Zbrojenie pionowe minimalne:**")
                st.latex(rf"A_{{s,vmin}} = 0.002 \cdot A_c = 0.002 \cdot {res_w['Ac_cm2']:.1f} = {res_w['As_vmin']:.2f}\ cm^2")
                st.write("**2. Zbrojenie poziome minimalne:**")
                st.latex(rf"A_{{s,hmin}} = \max(0.25 A_{{s,v}}; 0.001 A_c) = \max({0.25*res_w['As_vmin']:.2f}; {0.001*res_w['Ac_cm2']:.2f}) = {res_w['As_hmin']:.2f}\ cm^2")


    # === ZAKŁADKA 2: TARCZA / ROZCIĄGANIE (PEŁNA PROCEDURA) ===
    with tab2:
        st.markdown("### DANE WEJŚCIOWE")
        
        # Default C30/37 and B500
        idx_c30 = BETON_CLASSES.index("C30/37") if "C30/37" in BETON_CLASSES else 0
        def_idx_stal = STAL_GRADES.index("B500") if "B500" in STAL_GRADES else 0

        r1c1, r1c2, r1c3, r1c4 = st.columns(4)
        with r1c1:
            klasa_betonu_t = st.selectbox("Klasa betonu", BETON_CLASSES, index=idx_c30, key="t_bet", on_change=reset_tension)
            fctm_t = BETON_FCTM.get(klasa_betonu_t, 2.9)
        with r1c2:
            stal_nazwa_t = st.selectbox("Klasa stali", STAL_GRADES, index=def_idx_stal, key="t_stal", on_change=reset_tension)
            fyk_t = STAL_FYK.get(stal_nazwa_t, 500.0)
        with r1c3:
            fi_t = int(st.selectbox(f"Średnica pręta {SYM['fi']} [mm]", FI_LIST, index=FI_LIST.index(12) if 12 in FI_LIST else 0, key="t_fi", on_change=reset_tension))
        with r1c4:
            c_nom_t = st.number_input(r"Otulina $c_{nom}$ [mm]", value=30, step=5, key="t_c", on_change=reset_tension)

        r2c1, r2c2, r2c3, r2c4 = st.columns(4)
        with r2c1:
            h_cm_t = st.number_input("Grubość tarczy h [cm]", value=20.0, step=1.0, key="t_h", on_change=reset_tension)
        with r2c2:
            b_cm_t = st.number_input("Szerokość pasma b [cm]", value=100.0, step=10.0, help="Pasmo obliczeniowe, zazwyczaj 100 cm", key="t_b", on_change=reset_tension)
        with r2c3:
            wk_t = float(st.selectbox(r"Dopuszczalna szerokość rysy $w_k$ [mm]", [0.10, 0.20, 0.30, 0.40], index=2, key="t_wk", on_change=reset_tension))
        with r2c4:       
            ALPHAS = [0.50, 0.60, 0.70, 0.80, 0.90, 1.00]
            alpha_val_t = float(st.selectbox(
                f"Wartość $f_{{ct,eff}}$ jako część $f_{{ctm}}$ betonu", 
                ALPHAS, 
                index=ALPHAS.index(1.00), 
                format_func=lambda a: fcteff_label(a),
                key="t_alpha",
                on_change=reset_tension
            ))
   
        st.markdown(f"**Podejście do wyznaczenia {SYM['sigma']}ₛ**")
        
        # POPRAWKA STAŁYCH OPCJI
        OPCJA_PN = "Wg PN-EN-1992-1-1"
        OPCJA_DIN = "Wg DIN-1045-1"

        sigma_mode_t = st.radio(
            "sigma_mode", 
            [OPCJA_PN, OPCJA_DIN], 
            horizontal=True, 
            label_visibility="collapsed", 
            key="t_mode",
            on_change=reset_tension
        )
        
        # NOWA WSKAZÓWKA
        st.info(
            "ℹ️ **Wskazówka:** Podejście obliczeniowe do wyznaczania naprężeń w stali według PN-EN daje, zgodnie z dostępną literaturą, "
            "bardzo konserwatywne wartości. W praktyce wielu inżynierów stosuje "
            "dokładny wzór zaczerpnięty z normy niemieckiej (**DIN 1045-1**), który wyznacza bardziej "
            "realistyczne wartości naprężeń w stali."
        )
        
        # POPRAWKA WARUNKU IF
        if abs(wk_t - 0.10) < 1e-12 and sigma_mode_t == OPCJA_PN:
            st.info("Dla wk=0.10 mm Tablica 7.2N nie ma zastosowania. Obliczenia wykonano wg DIN.")
            sigma_mode_t = OPCJA_DIN # override logic locally

        if st.session_state.zms_t_calculated and st.session_state.zms_t_payload:
            payload = st.session_state.zms_t_payload
            if not payload.get("error_crack") and "sigma_s" in payload:
                st.text_input(f"Wartość naprężeń w stali {SYM['sigma']}ₛ", value=f"{payload['sigma_s']:.1f} MPa", disabled=True, key="zms_sigma_s_display")

        # POPRAWKA WARUNKU IF
        if sigma_mode_t == OPCJA_PN:
            with st.expander("ℹ️ Pomoc: Ograniczenie zarysowania wg PN-EN 1992-1-1 (Tablica 7.2N)"):
                components.html(render_table_72N_html(), height=420, scrolling=True)

        _, c_btn_t, _ = st.columns([1, 2, 1])
        with c_btn_t:
            if st.button("OBLICZ", type="primary", use_container_width=True, key="btn_t"):
                st.session_state.zms_t_calculated = True
                
                # --- OBLICZENIA TARCZA (ROZCIĄGANIE) ---
                d_cm = h_cm_t - (c_nom_t/10) - (fi_t/20) # d dla jednej warstwy, ale przy rozciąganiu liczy się cała sekcja
                Ac_cm2 = b_cm_t * h_cm_t
                fct_eff = alpha_val_t * fctm_t
                
                # Parametry do zarysowania (Rozciąganie)
                # kc = 1.0 dla czystego rozciągania (EC2 7.3.2(2))
                kc = 1.0 
                
                # k interpolowane z h (EC2 7.3.2(2)) - h to mniejszy wymiar lub grubość. Tutaj grubość tarczy.
                h_mm = h_cm_t * 10.0
                k = k_from_h_mm(h_mm)
                
                # Act = Ac (cała strefa rozciągana w tarczy rozciąganej)
                Act_cm2 = Ac_cm2 
                
                # Obliczenie Sigma
                sigma_s = fyk_t
                error_crack = None
                
                # POPRAWKA WARUNKU
                if sigma_mode_t == OPCJA_PN:
                    if wk_t not in TAB_7_2N:
                        error_crack = "Niewłaściwe wk dla PN-EN"
                    else:
                        h_minus_d_mm = (h_cm_t * 10) - (d_cm * 10)
                        hcr_mm = h_cm_t * 10 # Cała wysokość
                        
                        F = phi_transform_factor_tension(fct_eff, hcr_mm, h_minus_d_mm)
                        
                        if F <= 0:
                            error_crack = "Geometria (h-d<=0)"
                        else:
                            phi_star = fi_t / F
                            s_lim = sigma_from_tab72N(phi_star, wk_t)
                            if s_lim is None:
                                error_crack = "Brak rozwiązania w Tab 7.2N (zbyt duża średnica)"
                            else:
                                sigma_s = min(float(s_lim), fyk_t)
                else:
                    # DIN
                    sigma_s = sigma_s_din(float(fi_t), float(wk_t), k, fct_eff, fyk_t)
                
                As_min_crack = 0.0
                if not error_crack:
                    # As_min * sigma_s = kc * k * fct,eff * Act
                    As_min_crack = (kc * k * fct_eff * Act_cm2) / sigma_s
                
                # Minimum geometryczne dla tarczy (0.1%)
                As_min_mesh = 0.001 * Ac_cm2
                
                As_min = max(As_min_crack, As_min_mesh)
                As_max = 0.04 * Ac_cm2
                
                st.session_state.zms_t_payload = {
                    "mode": "tarcza", "typ": "Tarcza (Element rozciągany)",
                    "h_cm": h_cm_t, "b_cm": b_cm_t, "Ac_cm2": Ac_cm2,
                    "beton": klasa_betonu_t, "fctm": fctm_t, "fct_eff": fct_eff,
                    "stal": stal_nazwa_t, "fyk": fyk_t,
                    "wk": wk_t, "sigma_mode": sigma_mode_t, "sigma_s": sigma_s,
                    "k": k, "kc": kc, "Act": Act_cm2, "error_crack": error_crack,
                    "As_min_crack": As_min_crack, "As_min_mesh": As_min_mesh,
                    "As_min": As_min, "As_max": As_max
                }
                st.rerun()

        # WYNIKI TARCZA
        if st.session_state.zms_t_calculated and st.session_state.zms_t_payload:
            res_t = st.session_state.zms_t_payload
            
            st.markdown("### WYNIKI")
            st.markdown(f"""
            <div class="big-result">
                <span>Zbrojenie minimalne (całkowite)</span>
                <span><i>A</i><sub>s,min</sub> = {res_t['As_min']:.2f} cm²</span>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="max-result">
                <span>Zbrojenie maksymalne</span>
                <span><i>A</i><sub>s,max</sub> = {res_t['As_max']:.2f} cm²</span>
            </div>
            """, unsafe_allow_html=True)
            
            if res_t.get('error_crack'):
                st.warning(f"Warunek zarysowania pominięty: {res_t['error_crack']}")
            else:
                st.markdown("")
                st.warning("☝️ Podane wyniki to **całkowite zbrojenie w przekroju**. Zgodnie z normą, połowę tego zbrojenia należy umieścić przy każdej powierzchni ściany.")

            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            with st.expander("Szczegóły obliczeń", expanded=False):
                st.markdown("#### 1. Parametry zarysowania")
                st.latex(rf"f_{{ct,eff}} = {res_t['fct_eff']:.2f} \text{{ MPa}}, \quad k = {res_t['k']:.3f}, \quad k_c = {res_t['kc']:.1f}")
                st.write(f"Naprężenia w stali ({res_t['sigma_mode']}):")
                if not res_t.get('error_crack'):
                    st.latex(rf"\sigma_s = \mathbf{{{res_t['sigma_s']:.1f}}} \text{{ MPa}}")
                
                st.markdown("#### 2. Warunek ograniczenia zarysowania")
                if not res_t.get('error_crack'):
                    st.latex(rf"A_{{s,min,cr}} = \frac{{k_c \cdot k \cdot f_{{ct,eff}} \cdot A_{{ct}}}}{{\sigma_s}} = \frac{{1.0 \cdot {res_t['k']:.3f} \cdot {res_t['fct_eff']:.2f} \cdot {res_t['Act']:.1f}}}{{{res_t['sigma_s']:.1f}}} = \mathbf{{{res_t['As_min_crack']:.2f}}} \text{{ cm}}^2")
                
                st.markdown("#### 3. Minimum geometryczne (Siatka 9.7)")
                st.latex(rf"A_{{s,min,mesh}} = 0.001 \cdot A_c = \mathbf{{{res_t['As_min_mesh']:.2f}}} \text{{ cm}}^2")
                
                st.markdown("#### 4. Wynik końcowy")
                st.latex(rf"A_{{s,min}} = \max(A_{{s,min,cr}}; A_{{s,min,mesh}}) = \mathbf{{{res_t['As_min']:.2f}}} \text{{ cm}}^2")

if __name__ == "__main__":
    StronaZbrojenieMinimalneSciany()