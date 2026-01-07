"""
PROGRAMY/DlugoscZakotwienia.py
Wersja: ENGINEERING_STANDARD_V33 (Horizontal Alpha 4 Compression Input)
"""

import streamlit as st
from pathlib import Path
from io import BytesIO
import sys
import math
import re

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
# IMPORT DANYCH Z TABLIC
# =============================================================================

STAL_DATA_FALLBACK = {
    "B500B": 500,
    "B500A": 500,
    "B500C": 500,
    "RB500W": 500,
}

try:
    from TABLICE.ParametryStali import STEEL_TABLE
    STAL_DATA = {k: v.fyk for k, v in STEEL_TABLE.items()}
except ImportError:
    STAL_DATA = STAL_DATA_FALLBACK

BETON_DATA = {
    "C12/15":  [12, 1.6],
    "C16/20":  [16, 1.9],
    "C20/25":  [20, 2.2],
    "C25/30":  [25, 2.6],
    "C30/37":  [30, 2.9],
    "C35/45":  [35, 3.2],
    "C40/50":  [40, 3.5],
    "C45/55":  [45, 3.8],
    "C50/60":  [50, 4.1],
    "C55/67":  [55, 4.2],
    "C60/75":  [60, 4.4],
    "C70/85":  [70, 4.6],
    "C80/95":  [80, 4.8],
    "C90/105": [90, 5.0],
}

FI_LIST = [6, 8, 10, 12, 14, 16, 20, 25, 28, 32, 40]

# --- SYMBOLE UNICODE DLA PDF ---
SYM = {
    "fi": "\u03A6", "alpha": "\u03B1", "sigma": "\u03C3", "eta": "\u03B7",
    "rho": "\u03C1", "dot": "\u00B7", "bullet": "\u2022", "ge": "\u2265", "le": "\u2264",
    "ra": "\u2192"
}

# =============================================================================
# LOGIKA OBLICZENIOWA
# =============================================================================

def ObliczDlugoscZakotwienia(
    fi_mm: float,
    klasa_betonu: str,
    stal_nazwa: str,
    procent_naprezenia: float,
    warunki_przyczepnosci: str,
    rodzaj_preta: str,
    ksztalt_preta: str,
    alfa2: float = 1.0,
    alfa3: float = 1.0,
    alfa4: float = 1.0,
    alfa5: float = 1.0
) -> dict:
    
    fck, fctm = BETON_DATA.get(klasa_betonu, [20, 2.2])
    fyk = STAL_DATA.get(stal_nazwa, 500)
    
    gamma_c = 1.4
    gamma_s = 1.15
    
    fctk_005 = 0.7 * fctm
    fctd = fctk_005 / gamma_c
    
    eta1 = 1.0 if warunki_przyczepnosci == "Dobre" else 0.7
    eta2 = 1.0
    if fi_mm > 32:
        eta2 = (132 - fi_mm) / 100.0
        
    fbd = 2.25 * eta1 * eta2 * fctd
    
    fyd = fyk / gamma_s
    sigma_sd = (procent_naprezenia / 100.0) * fyd
    lb_rqd = (fi_mm / 4.0) * (sigma_sd / fbd)
    
    alfa1 = 1.0
    if rodzaj_preta == "Rozciągany":
        if ksztalt_preta != "Proste":
            alfa1 = 0.7
    
    if rodzaj_preta == "Ściskany":
        alfa1 = 1.0
        alfa2 = 1.0
        alfa3 = 1.0
        alfa5 = 1.0

    alfa_global = alfa1 * alfa2 * alfa3 * alfa4 * alfa5
    
    warning_alfa = False
    if rodzaj_preta == "Rozciągany":
        prod_a235 = alfa2 * alfa3 * alfa5
        if prod_a235 < 0.7:
            alfa_global = alfa1 * alfa4 * 0.7
            warning_alfa = True
            
    lb_calc = alfa_global * lb_rqd
    
    if rodzaj_preta == "Rozciągany":
        lb_min_val = max(0.3 * lb_rqd, 10.0 * fi_mm, 100.0)
    else:
        lb_min_val = max(0.6 * lb_rqd, 10.0 * fi_mm, 100.0)
        
    lb_final = max(lb_calc, lb_min_val)
    
    return {
        "fi_mm": fi_mm,
        "klasa_betonu": klasa_betonu,
        "fctd": fctd,
        "stal_nazwa": stal_nazwa,
        "fyk": fyk,
        "fyd": fyd,
        "sigma_sd": sigma_sd,
        "eta1": eta1,
        "eta2": eta2,
        "fbd": fbd,
        "lb_rqd": lb_rqd,
        "alfa1": alfa1,
        "alfa2": alfa2,
        "alfa3": alfa3,
        "alfa4": alfa4,
        "alfa5": alfa5,
        "alfa_global": alfa_global,
        "warning_alfa": warning_alfa,
        "lb_calc": lb_calc,
        "lb_min": lb_min_val,
        "lb_final": lb_final,
        "rodzaj_preta": rodzaj_preta,
        "ksztalt_preta": ksztalt_preta
    }


# =============================================================================
# STRONA STREAMLIT
# =============================================================================

def StronaDlugoscZakotwienia():
    # USUNIĘTO CSS STYLU PRZYCISKU (div.stButton > button:first-child)
    st.markdown(
        """
        <style>
        .block-container { padding-top: 1.5rem; padding-bottom: 1.5rem; }
        h3 { margin-top: 1.0rem !important; margin-bottom: 0.4rem !important; font-size: 1.1rem; }
        
        .big-result {
            font-size: 26px; font-weight: bold; color: #2E8B57; background-color: #f0f2f6;
            padding: 15px; border-radius: 8px; text-align: center; margin-top: 20px; border: 2px solid #2E8B57;
        }
        div.row-widget.stRadio > div { flex-direction: row; gap: 16px; }
        .warning-box {
            background-color: #3e1f1f; color: #ffcccc; padding: 10px; border-radius: 5px; 
            margin-top: 10px; margin-bottom: 10px; border: 1px solid #ff4444; font-size: 14px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # TYTUŁ
    st.markdown(
        """
        <div style="text-align:center; margin-top:0.4rem; margin-bottom:0rem;">
            <span style="font-size:42px; font-weight:800; letter-spacing:1px; color:#dddddd;">
                DŁUGOŚĆ ZAKOTWIENIA PRĘTÓW ZBROJENIOWYCH
            </span>
        </div>
        <div style="text-align:center; font-size:14px; color:#aaaaaa; margin-top:-12px; margin-bottom:0.6rem;">
            wg PN-EN 1992-1-1
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 1. DANE WEJŚCIOWE
    st.markdown("### DANE WEJŚCIOWE")

    c1, c2, c3, c4 = st.columns([0.9,0.9,1.3,0.9])
    with c1:
        fi_mm = st.selectbox("Średnica pręta Φ [mm]", FI_LIST, index=3)
    with c2:
        klasa_betonu = st.selectbox("Klasa betonu", list(BETON_DATA.keys()), index=4)
    with c3:
        stal_opts = list(STAL_DATA.keys())
        def_idx = 0
        if "B500B" in stal_opts:
            def_idx = stal_opts.index("B500B")
        elif "B500" in stal_opts:
            def_idx = stal_opts.index("B500")
        stal_nazwa = st.selectbox("Klasa stali", stal_opts, index=def_idx)
    with c4:
        naprezenie = st.number_input("Naprężenia w stali $\\sigma_{sd}/f_{yd}$ [%]", 0, 100, 100, 5)

    c5, c6, c_a4_glob, c_rodzaj = st.columns([0.9,0.9,1.3,0.9])
    with c5:    
        st.markdown("Warunki przyczepności", unsafe_allow_html=True)        
        c6_str = st.radio(
            "c5_label", 
            ["Dobre", "Złe"], 
            index=0, 
            label_visibility="collapsed", 
            horizontal=True,
            key="radio_c5"  # Dobra praktyka: unikalny klucz
        )
    with c6:
        st.markdown("Kształt pręta", unsafe_allow_html=True)        
        c6_str = st.radio(
            "c6_label", 
            ["Proste", "Inne (haki, pętle)"], 
            index=0, 
            label_visibility="collapsed", 
            horizontal=True,
            key="radio_c6"  # Dobra praktyka: unikalny klucz
        )              
    with c_a4_glob:
        st.markdown(r"$\alpha_4$: Czy występuje zbrojenie poprzeczne przyspojone?", unsafe_allow_html=True)        
        u_a4_str = st.radio(
            "a4_label", 
            ["Tak", "Nie"], 
            index=1, 
            label_visibility="collapsed", 
            horizontal=True,
            key="radio_a4_glob"  # Dobra praktyka: unikalny klucz
        )
    with c_rodzaj:
        st.markdown("Rodzaj pręta", unsafe_allow_html=True)
        rodzaj_preta = st.radio(
        "rodzaj_preta_label", 
        ["Ściskany", "Rozciągany"], 
        index=0, 
        label_visibility="collapsed",
        horizontal=True
    )   
    
    # Logika wyciągnięta na poziom główny (zgodnie z wcięciem with)
    if u_a4_str == "Tak":
        a4_val = 0.7
    else:
        a4_val = 1.0

    # Inicjalizacja pozostałych współczynników
    a2_val, a3_val, a5_val = 1.0, 1.0, 1.0

    if rodzaj_preta == "Rozciągany":
         # 3 kolumny dla pozostałych współczynników: alfa2, alfa3, alfa5
        col_a2, col_a3, col_a5 = st.columns([0.9,1.55,1.55])
    
        with col_a2:
            st.markdown("""$\\alpha_2$: Czy uwzględnić wpływ otuliny ($c_d$)""", unsafe_allow_html=True)       
            u_a2_str = st.radio("a2_yn", ["Tak", "Nie"], index=1, label_visibility="collapsed", horizontal=True)
            u_a2 = (u_a2_str == "Tak")
        
            cd_in = 30.0
            if u_a2:
                with st.expander("ℹ️ Pomoc: Rysunek $c_d$"):
                    img_cd = SCIEZKA_FOLDERU_LOKALNEGO / "DlugoscZakotwienia_Wspolczynnik cd.png"
                    if img_cd.exists(): st.image(str(img_cd), use_container_width=True)
                cd_in = st.number_input("$c_d$ [mm]", value=30.0, step=1.0)
            
            val = 1.0 - 0.15 * (cd_in - fi_mm) / fi_mm
            if not u_a2: val = 1.0
            a2_val = max(0.7, min(1.0, val))

        with col_a3:
            st.markdown("""$\\alpha_3$: Czy występuje zbrojenie poprzeczne nieprzyspojone?""", unsafe_allow_html=True)
            u_a3_str = st.radio("a3_yn", ["Tak", "Nie"], index=1, label_visibility="collapsed", horizontal=True)
            u_a3 = (u_a3_str == "Tak")
        
            K_in, sum_ast_in, sum_ast_min_in = 0.05, 0.0, 2.5
            if u_a3:
                with st.expander("ℹ️ Pomoc: Rysunek $K$"):
                    img_k = SCIEZKA_FOLDERU_LOKALNEGO / "DlugoscZakotwienia_Wspolczynnik K.png"
                    if img_k.exists(): st.image(str(img_k), use_container_width=True)
                K_in = st.selectbox("Współczynnik $K$", [0.1, 0.05, 0.0], index=1)
                sum_ast_in = st.number_input("$\\Sigma A_{st}$ [cm²]", value=0.0, step=0.1)
                sum_ast_min_in = st.number_input("$\\Sigma A_{st,min}$", value=2.5, step=0.1)
        
            As_1 = (math.pi * fi_mm**2)/400.0
            val_a3 = 1.0
            if u_a3 and As_1 > 0:
                lamb = (sum_ast_in - sum_ast_min_in) / As_1
                val_a3 = 1.0 - K_in * lamb
            a3_val = max(0.7, min(1.0, val_a3))

        with col_a5:
            st.markdown("""$\\alpha_5$: Czy uwzględnić nacisk poprzeczny?""", unsafe_allow_html=True)         
            u_a5_str = st.radio("a5_yn", ["Tak", "Nie"], index=1, label_visibility="collapsed", horizontal=True)
            u_a5 = (u_a5_str == "Tak")
        
            p_in = 8.0 
            if u_a5:
                st.write("p - nacisk poprzeczny w [MPa] wzdłuż lbd w stanie granicznym nośności")
                p_in = st.number_input("p_input", value=8.0, step=0.5, label_visibility="collapsed")
        
            val_a5 = 1.0
            if u_a5:
                val_a5 = 1.0 - 0.04 * p_in
                a5_val = max(0.7, min(1.0, val_a5))
                   
            
    # UI CLEANUP - Usunięto zbędne nagłówki nad rysunkami

    col_rys1, col_rys2 = st.columns([3,4])

    with col_rys1:    
        with st.expander("ℹ️ Pomoc: Warunki przyczepności (Rysunek 8.2)"):
            rys_eksp = SCIEZKA_FOLDERU_LOKALNEGO / "DlugoscZakotwienia_WarunkiPrzyczepnosci.png"
            if rys_eksp.exists():
                st.image(str(rys_eksp), use_container_width=True)
            else:
                st.info(f"Brak pliku pomocy: {rys_eksp.name}")
    with col_rys2:   
        with st.expander("ℹ️ Pomoc: Wartości współczynników $\\alpha$ (Tablica 8.2)"):
           rys_eksp = SCIEZKA_FOLDERU_LOKALNEGO / "DlugoscZakotwienia_alfa1-alfa5.png"
           if rys_eksp.exists():
                st.image(str(rys_eksp), use_container_width=True)
           else:
                st.info(f"Brak pliku pomocy: {rys_eksp.name}")
             

    # PRZYCISK - DODANO TYPE PRIMARY
    _, c_btn, _ = st.columns([1, 2, 1])
    with c_btn:
        oblicz = st.button("OBLICZ", type="primary", use_container_width=True)

    if oblicz:
        wynik = ObliczDlugoscZakotwienia(
            fi_mm=float(fi_mm),
            klasa_betonu=klasa_betonu,
            stal_nazwa=stal_nazwa,
            procent_naprezenia=float(naprezenie),
            warunki_przyczepnosci=warunki,
            rodzaj_preta=rodzaj_preta,
            ksztalt_preta=ksztalt_preta,
            alfa2=a2_val,
            alfa3=a3_val,
            alfa4=a4_val,
            alfa5=a5_val
        )
        
        st.session_state["wynik_kotw"] = wynik
        st.session_state["inputs_kotw"] = {
            "naprezenie": naprezenie,
            "warunki": warunki,
            "stal_nazwa": stal_nazwa
        }
        st.session_state["pokaz_kotw"] = True

    # WYNIKI
    if st.session_state.get("pokaz_kotw", False):
        res = st.session_state["wynik_kotw"]
        inp = st.session_state["inputs_kotw"]
        
        st.markdown(
            f"""
            <div class="big-result">
                Długość zakotwienia <i>l</i><sub>bd,req</sub> = {res['lb_final']:.0f} mm
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)             
        with st.expander("Szczegóły obliczeń", expanded=False):
            
            st.markdown("#### 1. Parametry materiałowe")
            st.write(f"Średnica pręta: **Φ = {res['fi_mm']:.0f} mm**")
            st.write(f"Beton: **{res['klasa_betonu']}** ($f_{{ctd}} = {res['fctd']:.2f}$ MPa)")
            st.write(f"Stal: **{res['stal_nazwa']}** ($f_{{yk}} = {res['fyk']:.0f}$ MPa, $f_{{yd}} = {res['fyd']:.1f}$ MPa)")
            
            st.markdown("#### 2. Podstawowa długość zakotwienia ($l_{b,rqd}$)")
            st.write(f"Warunki przyczepności: **{inp['warunki']}** ($\\eta_1 = {res['eta1']}$)")
            st.write(f"Współczynnik średnicy: $\\eta_2 = {res['eta2']:.2f}$")
            
            st.latex(rf"f_{{bd}} = 2.25 \cdot \eta_1 \cdot \eta_2 \cdot f_{{ctd}} = 2.25 \cdot {res['eta1']} \cdot {res['eta2']:.2f} \cdot {res['fctd']:.2f} = \mathbf{{{res['fbd']:.2f}}} \text{{ MPa}}")
            st.latex(rf"l_{{b,rqd}} = \frac{{\Phi}}{{4}} \cdot \frac{{\sigma_{{sd}}}}{{f_{{bd}}}} = \frac{{{res['fi_mm']:.0f}}}{{4}} \cdot \frac{{{res['sigma_sd']:.1f}}}{{{res['fbd']:.2f}}} = \mathbf{{{res['lb_rqd']:.1f}}} \text{{ mm}}")
            
            st.markdown("#### 3. Współczynniki wpływu $\\alpha$")
            st.write(f"$\\alpha_1 = {res['alfa1']:.2f}$")
            st.write(f"$\\alpha_2 = {res['alfa2']:.2f}$")
            st.write(f"$\\alpha_3 = {res['alfa3']:.2f}$")
            st.write(f"$\\alpha_4 = {res['alfa4']:.2f}$")
            st.write(f"$\\alpha_5 = {res['alfa5']:.2f}$")
            
            if res['warning_alfa']:
                val = res['alfa2']*res['alfa3']*res['alfa5']
                st.markdown(
                    f"""
                    <div class="warning-box">
                    ⚠️ Warunek EC2 8.4.4(1): α₂ · α₃ · α₅ = {val:.3f} < 0.7
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
                st.latex(r"\rightarrow \text{Przyjęto iloczyn } (\alpha_2 \cdot \alpha_3 \cdot \alpha_5) = 0.7")
            
            st.latex(rf"\alpha_{{global}} = \alpha_1 \cdot \alpha_2 \cdot \alpha_3 \cdot \alpha_4 \cdot \alpha_5 = {res['alfa_global']:.2f}")
            
            st.markdown("#### 4. Minimalna długość zakotwienia ($l_{b,min}$)")
            wsp = 0.3 if res['rodzaj_preta'] == "Rozciągany" else 0.6
            val1 = wsp * res['lb_rqd']
            val2 = 10.0 * res['fi_mm']
            st.latex(rf"l_{{b,min}} = \max({wsp} \cdot l_{{b,rqd}}; 10\Phi; 100) = \max({val1:.1f} \text{{ mm}}; {val2:.1f} \text{{ mm}}; 100 \text{{ mm}}) = {res['lb_min']:.1f} \text{{ mm}}")
            
            st.markdown("#### 5. Obliczenie długości zakotwienia ($l_{bd}$)")
            st.latex(rf"l_{{bd}} = \alpha_{{global}} \cdot l_{{b,rqd}} = {res['alfa_global']:.2f} \cdot {res['lb_rqd']:.1f} = {res['lb_calc']:.1f} \text{{ mm}}")
            st.latex(rf"l_{{bd,req}} = \max(l_{{bd}}; l_{{b,min}}) = \mathbf{{{res['lb_final']:.1f}}} \text{{ mm}}")

if __name__ == "__main__":
    StronaDlugoscZakotwienia()