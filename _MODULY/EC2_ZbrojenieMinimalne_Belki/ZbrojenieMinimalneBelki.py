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

# PN-EN 1992-1-1 Tablica 7.2N
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

def phi_transform_factor(fct_eff: float, kc: float, hcr_mm: float, h_minus_d_mm: float) -> float:
    if h_minus_d_mm <= 0: return 0.0
    base = fct_eff / 2.9
    return base * (kc * hcr_mm) / (2.0 * h_minus_d_mm)

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

    html = """
    <div style="width:100%; overflow-x:auto; padding:10px 0;">
      <style>
        table.ec2 { width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 14px; background: #111827; color: #E5E7EB; }
        table.ec2 th, table.ec2 td { border: 1px solid #374151; padding: 10px 8px; text-align: center; white-space: nowrap; }
        table.ec2 th { background: #1F2937; font-weight: 800; }
        table.ec2 tr:nth-child(even) td { background: #0F172A; }
      </style>
      <table class="ec2">
        <tr>
          <th>σ<sub>s</sub> [MPa]</th>
          <th>w<sub>k</sub>=0.4<br>φ* [mm]</th>
          <th>w<sub>k</sub>=0.3<br>φ* [mm]</th>
          <th>w<sub>k</sub>=0.2<br>φ* [mm]</th>
        </tr>
    """
    for s in sigmas:
        html += f"<tr><td>{s:.0f}</td><td>{fmt(0.4, s)}</td><td>{fmt(0.3, s)}</td><td>{fmt(0.2, s)}</td></tr>"
    html += "</table></div>"
    return html


# =============================================================================
# STRONA
# =============================================================================
def StronaZbrojenieMinimalneBelki():
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
                ZBROJENIE MINIMALNE I MAKSYMALNE BELEK
            </span>
        </div>
        <div style="text-align:center; font-size:14px; color:#aaaaaa; margin-top:-12px; margin-bottom:0.6rem;">
            wg PN-EN 1992-1-1
        </div>
        """,
        unsafe_allow_html=True
    )

    # --- RESET FUNKCJA ---
    if "zmb_calculated" not in st.session_state:
        st.session_state.zmb_calculated = False
    if "zmb_payload" not in st.session_state:
        st.session_state.zmb_payload = None

    def reset_results():
        st.session_state.zmb_calculated = False
        st.session_state.zmb_payload = None

    st.markdown("### DANE WEJŚCIOWE")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        klasa_betonu = st.selectbox("Klasa betonu", BETON_CLASSES, index=BETON_CLASSES.index("C30/37") if "C30/37" in BETON_CLASSES else 0, on_change=reset_results)
        fctm = BETON_FCTM.get(klasa_betonu, 2.9)
    with c2:
        # Default B500 if exists
        def_idx = 0
        if "B500" in STAL_GRADES: def_idx = STAL_GRADES.index("B500")
        elif "B500B" in STAL_GRADES: def_idx = STAL_GRADES.index("B500B")
        stal_nazwa = st.selectbox("Klasa stali", STAL_GRADES, index=def_idx, on_change=reset_results)
        fyk = STAL_FYK.get(stal_nazwa, 500.0)
    with c3:
        fi = int(st.selectbox(f"Średnica pręta {SYM['fi']} [mm]", FI_LIST, index=FI_LIST.index(16) if 16 in FI_LIST else 0, on_change=reset_results))

    c4, c5, c6 = st.columns(3)
    with c4:
        b_cm = st.number_input("Szerokość b [cm]", value=30.0, step=5.0, on_change=reset_results)         
    with c5:
        h_cm = st.number_input("Wysokość h [cm]", value=50.0, step=5.0, on_change=reset_results)  
    with c6:        
        c_nom = st.number_input(r"Otulina nominalna $c_{nom}$ [mm]", value=30, step=5, on_change=reset_results)
       
    c_rys1, c_rys2, c_rys3 = st.columns(3)
    with c_rys1:
        fi_strz = st.selectbox(r"Strzemiona $\Phi_{strz}$ [mm]", [6,8,10,12], index=1, on_change=reset_results)
    with c_rys2:    
        wk = float(st.selectbox(r"Dopuszczalna szerokość rysy $w_k$ [mm]", [0.10, 0.20, 0.30, 0.40], index=2, on_change=reset_results))
    with c_rys3:
        ALPHAS = [0.50, 0.60, 0.70, 0.80, 0.90, 1.00]
        alpha_val = float(st.selectbox(
            f"Wartość $f_{{ct,eff}}$ jako część $f_{{ctm}}$ betonu", 
            ALPHAS, 
            index=ALPHAS.index(1.00), 
            format_func=lambda a: fcteff_label(a),
            on_change=reset_results
        ))

    # -------------------------------------------------------------------------
    # Podejście do wyznaczenia σs
    # -------------------------------------------------------------------------
    st.markdown(f"**Podejście do wyznaczenia {SYM['sigma']}ₛ**")

    # POPRAWKA STAŁYCH OPCJI
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

    # NOWA WSKAZÓWKA
    st.info(
        "ℹ️ **Wskazówka:** Podejście obliczeniowe do wyznaczanaie naprężeń w stali według PN-EN daje, zgodnie z dostępną literaturą, "
        "bardzo konserwatywne wartości naprężeń stali. W praktyce wielu inżynierów stosowany jest "
        "dokładny wzór zaczerpnięty z normy niemieckiej (**DIN 1045-1**), który wyznacza bardziej "
        "realistyczne wartości naprężeń w stali."
    )
  
    # wyświetlenie σs dopiero po obliczeniu (ZMB_CALCULATED)
    if st.session_state.get("zmb_calculated") and st.session_state.get("zmb_payload"):
        payload = st.session_state.zmb_payload
        if not payload.get("error"):
            sigma_s_disp = payload["sigma_s"]
            st.text_input(f"Wartość naprężeń w stali {SYM['sigma']}ₛ", value=f"{sigma_s_disp:.1f} MPa", disabled=True, key="dp_ct_disp_yes")

    sigma_mode = sigma_choice
    
    # POPRAWKA WARUNKU IF
    if abs(wk - 0.10) < 1e-12 and sigma_choice == OPCJA_PN:
        sigma_mode = OPCJA_DIN
        st.info("Dla $w_k = 0.10$ mm Tablica 7.2N nie ma zastosowania (obejmuje $w_k = 0.2/0.3/0.4$ mm). Obliczenia wykonano wg DIN.")

    # POPRAWKA WARUNKU IF
    if sigma_mode == OPCJA_PN:
        with st.expander("ℹ️ Pomoc: Ograniczenie zarysowania wg PN-EN 1992-1-1 (Tablica 7.2N)", expanded=False):
            components.html(render_table_72N_html(), height=420, scrolling=True)  

    # --- BUTTON ---
    _, c_btn, _ = st.columns([1, 2, 1])
    with c_btn:
        if st.button("OBLICZ", type="primary", use_container_width=True):
            st.session_state.zmb_calculated = True
            
            d_cm = h_cm - (c_nom/10) - (fi_strz/10) - (fi/20)
            fct_eff = alpha_val * fctm
            
            if d_cm <= 0:
                st.session_state.zmb_payload = {"error": "Błąd geometrii: d <= 0"}
            else:
                # 1. KRUCHE
                val_1 = 0.26 * (fctm/fyk) * b_cm * d_cm
                val_2 = 0.0013 * b_cm * d_cm
                As_min_brittle = max(val_1, val_2)
                
                # 2. ZARYSOWANIE
                k = k_from_h_mm(h_cm * 10)
                kc = 0.4 # Zginanie proste
                hcr_mm = 0.5 * h_cm * 10
                Act_cm2 = 0.5 * b_cm * h_cm
                h_minus_d_mm = (h_cm*10) - (d_cm*10)
                
                sigma_s = fyk
                As_min_crack = 0.0
                error_crack = None
                
                # POPRAWKA WARUNKU
                if sigma_mode == OPCJA_PN:
                    if wk not in TAB_7_2N:
                        error_crack = "Niewłaściwe wk dla PN-EN"
                    else:
                        F = phi_transform_factor(fct_eff, kc, hcr_mm, h_minus_d_mm)
                        if F <= 0:
                            error_crack = "Błąd geometrii (h-d <= 0)"
                        else:
                            phi_star = fi / F
                            s_lim = sigma_from_tab72N(phi_star, wk)
                            if s_lim is None:
                                error_crack = "Brak rozwiązania w tabeli (zbyt duża średnica)"
                            else:
                                sigma_s = min(float(s_lim), fyk)
                else:
                    # DIN
                    sigma_s = sigma_s_din(float(fi), float(wk), k, fct_eff, fyk)
                
                if not error_crack:
                    As_min_crack = (kc * k * fct_eff * Act_cm2) / sigma_s
                
                As_min = max(As_min_brittle, As_min_crack)
                As_max = 0.04 * b_cm * h_cm
                
                st.session_state.zmb_payload = {
                    "b_cm": b_cm, "h_cm": h_cm, "d_cm": d_cm,
                    "klasa_betonu": klasa_betonu, "fctm": fctm, "fct_eff": fct_eff,
                    "stal_nazwa": stal_nazwa, "fyk": fyk, "wk": wk,
                    "As_min_brittle": As_min_brittle, "As_min_crack": As_min_crack,
                    "As_min": As_min, "As_max": As_max,
                    "sigma_mode": sigma_mode, "sigma_s": sigma_s,
                    "k": k, "kc": kc, "Act": Act_cm2, "error_crack": error_crack,
                    "val_1": val_1, "val_2": val_2, "alpha_val": alpha_val
                }
            st.rerun()

    # --- WYNIKI Z SESSION STATE ---
    if st.session_state.zmb_calculated and st.session_state.zmb_payload:
        wynik = st.session_state.zmb_payload
        
        if wynik.get("error"):
            st.error(wynik["error"])
        else:
            st.markdown("### WYNIKI")
            
            st.markdown(f"""
            <div class="big-result">
                <span>Zbrojenie minimalne</span>
                <span><i>A</i><sub>s,min</sub> = {wynik['As_min']:.2f} cm²/m</span>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="max-result">
                <span>Zbrojenie maksymalne</span>
                <span><i>A</i><sub>s,max</sub> = {wynik['As_max']:.2f} cm²/m</span>
            </div>
            """, unsafe_allow_html=True)
            
            if wynik.get('error_crack'):
                st.warning(f"Warunek zarysowania pominięty: {wynik['error_crack']}")
            
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                                  
            with st.expander("Szczegóły obliczeń", expanded=False):
                st.markdown("#### 1. Parametry geometryczne i materiałowe")
                st.write(f"Przekrój: **b = {wynik['b_cm']:.0f} cm**, **h = {wynik['h_cm']:.1f} cm**, **d = {wynik['d_cm']:.2f} cm**")
                st.write(f"Beton: **{wynik['klasa_betonu']}** ($f_{{ctm}} = {wynik['fctm']:.2f}$ MPa)")
                st.write(f"Stal: **{wynik['stal_nazwa']}** ($f_{{yk}} = {wynik['fyk']:.0f}$ MPa)")
                
                st.markdown("#### 2. Parametry do obliczeń zarysowania")
                st.write("Efektywna wytrzymałość betonu na rozciąganie:")
                st.latex(rf"f_{{ct,eff}} = \alpha \cdot f_{{ctm}} = {wynik['alpha_val']:.2f} \cdot {wynik['fctm']:.2f} = \mathbf{{{wynik['fct_eff']:.2f}}} \text{{ MPa}}")
                st.write("Pole strefy rozciąganej ($A_{ct}$) i współczynniki:")
                st.latex(rf"A_{{ct}} = 0.5 \cdot b \cdot h = {wynik['Act']:.1f} \text{{ cm}}^2, \quad k = {wynik['k']:.3f}, \quad k_c = {wynik['kc']:.1f}")
                
                if not wynik.get('error_crack'):
                    st.write(f"Naprężenia w stali ({wynik['sigma_mode']}):")
                    st.latex(rf"\sigma_s = \mathbf{{{wynik['sigma_s']:.1f}}} \text{{ MPa}}")
                
                st.markdown("#### 3. Warunek kruchego zniszczenia ($A_{s,min,1}$)")
                st.latex(rf"A_{{s,min,1}} = \max\left( 0.26 \frac{{f_{{ctm}}}}{{f_{{yk}}}} b d ; 0.0013 b d \right) = \mathbf{{{wynik['As_min_brittle']:.2f}}} \text{{ cm}}^2")
                
                st.markdown("#### 4. Warunek ograniczenia zarysowania ($A_{s,min,2}$)")
                if wynik.get('error_crack'):
                    st.error(wynik['error_crack'])
                else:
                    st.latex(
                        rf"A_{{s,min,2}} = \frac{{k_c \cdot k \cdot f_{{ct,eff}} \cdot A_{{ct}}}}{{\sigma_s}} "
                        rf"= \frac{{{wynik['kc']:.1f} \cdot {wynik['k']:.3f} \cdot {wynik['fct_eff']:.2f} \cdot {wynik['Act']:.1f}}}{{{wynik['sigma_s']:.1f}}} "
                        rf"= \mathbf{{{wynik['As_min_crack']:.2f}}} \text{{ cm}}^2"
                    )

                st.markdown("#### 5. Wyniki końcowe")
                st.latex(rf"A_{{s,min}} = \max(A_{{s,min,1}}; A_{{s,min,2}}) = \mathbf{{{wynik['As_min']:.2f}}} \text{{ cm}}^2")
                st.latex(rf"A_{{s,max}} = 0.04 \cdot A_c = \mathbf{{{wynik['As_max']:.2f}}} \text{{ cm}}^2")

if __name__ == "__main__":
    StronaZbrojenieMinimalneBelki()