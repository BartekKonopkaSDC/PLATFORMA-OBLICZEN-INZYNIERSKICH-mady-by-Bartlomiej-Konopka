import streamlit as st
import math
import sys
import re
from pathlib import Path
from io import BytesIO

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

# =============================================================================
# TABLICE (Kompatybilność)
# =============================================================================
try:
    from TABLICE.ParametryBetonu import list_concrete_classes, get_concrete_params, CONCRETE_TABLE  # type: ignore
except Exception:
    list_concrete_classes = None
    get_concrete_params = None

try:
    from TABLICE.ParametryStali import list_steel_grades, get_steel_params, STEEL_TABLE  # type: ignore
except Exception:
    list_steel_grades = None
    get_steel_params = None

def _fallback_concrete_classes():
    return ["C12/15", "C16/20", "C20/25", "C25/30", "C30/37", "C35/45", "C40/50", "C45/55", "C50/60"]

def _fallback_steel_grades():
    return ["B500", "B500B", "RB500W"]

def _fallback_steel_params(grade: str):
    return 500.0, 200000.0

# =============================================================================
# STRONA STREAMLIT
# =============================================================================
def StronaZbrojenieMinimalneSlupy():

    # -------------------------------------------------------------------------
    # STYLE CSS
    # -------------------------------------------------------------------------
    st.markdown(
        """
        <style>
        .block-container { padding-top: 1.5rem; padding-bottom: 1.5rem; }
        h3 { margin-top: 1.0rem !important; margin-bottom: 0.4rem !important; font-size: 1.1rem; }

        /* Guzik OBLICZ */
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

        /* Styl wyników (Flexbox - jedna linia) */
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

    # -------------------------------------------------------------------------
    # TYTUŁ
    # -------------------------------------------------------------------------
    st.markdown(
        """
        <div style="text-align:center; margin-top:0.4rem; margin-bottom:0rem;">
            <span style="font-size:36px; font-weight:800; letter-spacing:1px; color:#dddddd;">
                ZBROJENIE MINIMALNE I MAKSYMALNE SŁUPÓW
            </span>
        </div>
        <div style="text-align:center; font-size:14px; color:#aaaaaa; margin-top:-12px; margin-bottom:0.6rem;">
            wg PN-EN 1992-1-1
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- RESET FUNKCJA ---
    def reset_results():
        st.session_state["pokaz_zms"] = False

    # -------------------------------------------------------------------------
    # DANE WEJŚCIOWE
    # -------------------------------------------------------------------------
    st.markdown("### DANE WEJŚCIOWE")

    beton_classes = list_concrete_classes() if callable(list_concrete_classes) else _fallback_concrete_classes()
    stal_grades = list_steel_grades() if callable(list_steel_grades) else _fallback_steel_grades()

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        idx_c30 = beton_classes.index("C30/37") if "C30/37" in beton_classes else 0
        klasa_betonu = st.selectbox("Klasa betonu", beton_classes, index=idx_c30, on_change=reset_results)

    with c2:
        idx_def = 0
        if "B500" in stal_grades: idx_def = stal_grades.index("B500")
        elif "B500B" in stal_grades: idx_def = stal_grades.index("B500B")
        stal_nazwa = st.selectbox("Klasa stali", stal_grades, index=idx_def, on_change=reset_results)
        
        if callable(get_steel_params):
            sp = get_steel_params(stal_nazwa)
            fyk = float(sp.fyk)
        else:
            fyk, _ = _fallback_steel_params(stal_nazwa)
                
    with c3:
        b_cm = float(st.number_input(r"Szerokość przekroju $b$ [cm]", value=30.0, step=5.0, on_change=reset_results))

    with c4:
        h_cm = float(st.number_input(r"Wysokość przekroju $h$ [cm]", value=30.0, step=5.0, on_change=reset_results))

    with c5:
        N_Ed = st.number_input(r"Siła ściskająca $N_{Ed}$ [kN]", value=1000.0, step=50.0, on_change=reset_results)

    # -------------------------------------------------------------------------
    # OBLICZENIA
    # -------------------------------------------------------------------------
    _, c_btn, _ = st.columns([1, 2, 1])
    with c_btn:
        oblicz = st.button("OBLICZ", type="primary", use_container_width=True)

    if oblicz:
        Ac_cm2 = b_cm * h_cm
        fyd = fyk / 1.15
        
        # As min
        # Warunek 1: 0.10 NEd / fyd
        # NEd [kN], fyd [MPa = N/mm2]
        # (0.10 * NEd_kN * 10) / fyd_MPa = cm2
        As_min_1 = (0.10 * N_Ed * 10.0) / fyd
        
        # Warunek 2: 0.002 Ac
        As_min_2 = 0.002 * Ac_cm2
        
        As_min = max(As_min_1, As_min_2)
        
        # As max
        As_max = 0.04 * Ac_cm2

        st.session_state["wynik_zms"] = {
            "As_min": As_min, "As_max": As_max,
            "As_min_1": As_min_1, "As_min_2": As_min_2,
            "N_Ed": N_Ed, "fyk": fyk, "fyd": fyd,
            "b_cm": b_cm, "h_cm": h_cm, "Ac_cm2": Ac_cm2,
            "klasa_betonu": klasa_betonu, "stal_nazwa": stal_nazwa
        }
        st.session_state["pokaz_zms"] = True

    # -------------------------------------------------------------------------
    # WYNIKI
    # -------------------------------------------------------------------------
    if st.session_state.get("pokaz_zms", False):
        res = st.session_state["wynik_zms"]
        
        # WYNIKI GŁÓWNE - JEDNA LINIA
        st.markdown(f"""
            <div class="big-result">
                <span>Zbrojenie minimalne</span>
                <span><i>A</i><sub>s,min</sub> = {res["As_min"]:.2f} cm²</span>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown(f"""
            <div class="max-result">
                <span>Zbrojenie maksymalne</span>
                <span><i>A</i><sub>s,max</sub> = {res["As_max"]:.2f} cm²</span>
            </div>
            """, unsafe_allow_html=True)

        # SZCZEGÓŁY
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        with st.expander("Szczegóły obliczeń", expanded=False):
            st.markdown("#### 1. DANE WEJŚCIOWE")
            st.write(rf"- Beton: **{res['klasa_betonu']}**")
            st.write(rf"- Stal: **{res['stal_nazwa']}** ($f_{{yk}} = {res['fyk']:.0f}$ MPa)")
            st.write(rf"- Przekrój: $b = {res['b_cm']:.1f}$ cm, $h = {res['h_cm']:.1f}$ cm")
            st.write(rf"- Siła podłużna: $N_{{Ed}} = {res['N_Ed']:.2f}$ kN")

            st.markdown("#### 2. OBLICZENIE ZBROJENIA MINIMALNEGO")
            st.latex(rf"f_{{yd}} = \frac{{f_{{yk}}}}{{1.15}} = \frac{{{res['fyk']:.0f}}}{{1.15}} = {res['fyd']:.2f} \, \text{{MPa}}")
            st.latex(rf"A_c = b \cdot h = {res['b_cm']:.1f} \cdot {res['h_cm']:.1f} = {res['Ac_cm2']:.1f} \, \text{{cm}}^2")

            st.write("Warunek 1: na podstawie siły ściskającej ($0.10 N_{Ed}$)")
            st.latex(
                rf"A_{{s,min,1}} = \frac{{0.10 N_{{Ed}}}}{{f_{{yd}}}} = "
                rf"\frac{{0.10 \cdot {res['N_Ed']:.2f} \, \text{{kN}}}}{{ {res['fyd']:.2f} \, \text{{MPa}} }} = "
                rf"\mathbf{{{res['As_min_1']:.2f}}} \, \text{{cm}}^2"
            )

            st.write("Warunek 2: geometryczny ($0.002 A_c$)")
            st.latex(
                rf"A_{{s,min,2}} = 0.002 A_c = 0.002 \cdot {res['Ac_cm2']:.1f} = \mathbf{{{res['As_min_2']:.2f}}} \, \text{{cm}}^2"
            )

            st.latex(
                rf"A_{{s,min}} = \max(A_{{s,min,1}}; A_{{s,min,2}}) = \mathbf{{{res['As_min']:.2f}}} \, \text{{cm}}^2"
            )

            st.markdown("#### 3. OBLICZENIE ZBROJENIA MAKSYMALNEGO")
            st.latex(rf"A_{{s,max}} = 0.04 \cdot A_c = 0.04 \cdot {res['Ac_cm2']:.1f} = \mathbf{{{res['As_max']:.2f}}} \, \text{{cm}}^2")


if __name__ == "__main__":
    StronaZbrojenieMinimalneSlupy()