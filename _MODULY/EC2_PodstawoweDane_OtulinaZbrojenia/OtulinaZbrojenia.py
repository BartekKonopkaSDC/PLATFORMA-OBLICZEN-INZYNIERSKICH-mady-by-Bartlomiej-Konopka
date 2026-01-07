"""
PROGRAMY/OtulinaZbrojenia.py
Wersja: ENGINEERING_STANDARD_V57 (Button Fix)
"""

import streamlit as st
from pathlib import Path
from io import BytesIO
import sys

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
# MODUŁ OBLICZENIOWY
# =============================================================================

def get_structural_class_adjustment(
    klasa_betonu: str,
    klasa_ekspozycji: str,
    zywotnosc_100_lat: bool,
    element_plytowy: bool,
    kontrola_jakosci: bool,
) -> int:
    zmiana = 0

    # +2 za okres 100 lat
    if zywotnosc_100_lat:
        zmiana += 2

    # fck z klasy betonu
    try:
        fck = int(klasa_betonu.split("/")[0].replace("C", ""))
    except Exception:
        fck = 20

    redukcja_wytrzymalosc = False

    # Kryteria z Tablicy 4.3N
    if klasa_ekspozycji == "XC1" and fck >= 30:
        redukcja_wytrzymalosc = True
    elif klasa_ekspozycji in ["XC2", "XC3"] and fck >= 35:
        redukcja_wytrzymalosc = True
    elif klasa_ekspozycji == "XC4" and fck >= 40:
        redukcja_wytrzymalosc = True
    elif klasa_ekspozycji in ["XD1", "XD2", "XS1"] and fck >= 40:
        redukcja_wytrzymalosc = True
    elif klasa_ekspozycji in ["XD3", "XS2", "XS3"] and fck >= 45:
        redukcja_wytrzymalosc = True

    if redukcja_wytrzymalosc:
        zmiana -= 1

    # -1 za płytę w XC1
    if element_plytowy and klasa_ekspozycji == "XC1":
        zmiana -= 1

    # -1 za specjalną kontrolę
    if kontrola_jakosci:
        zmiana -= 1

    return zmiana


def get_c_min_dur_value(klasa_ekspozycji: str, klasa_konstrukcji: str) -> float:
    # Tablica 4.4N (pręty zbrojeniowe)
    mapa_S = {"S1": 0, "S2": 1, "S3": 2, "S4": 3, "S5": 4, "S6": 5}
    idx = mapa_S.get(klasa_konstrukcji, 3)

    tabela_4_4N = [
        [10, 10, 10, 15, 20, 25, 30],  # S1
        [10, 10, 15, 20, 25, 30, 35],  # S2
        [10, 10, 20, 25, 30, 35, 40],  # S3
        [10, 15, 25, 30, 35, 40, 45],  # S4
        [15, 20, 30, 35, 40, 45, 50],  # S5
        [20, 25, 35, 40, 45, 55, 55],  # S6
    ]

    mapa_col = {
        "X0": 0,
        "XC1": 1,
        "XC2": 2,
        "XC3": 2,
        "XC4": 3,
        "XD1": 4,
        "XS1": 4,
        "XD2": 5,
        "XS2": 5,
        "XD3": 6,
        "XS3": 6,
    }

    col_idx = mapa_col.get(klasa_ekspozycji, 1)
    return float(tabela_4_4N[idx][col_idx])


def ObliczOtuline(
    klasa_ekspozycji: str,
    fi_mm: float,
    klasa_betonu: str,
    zywotnosc_100_lat: bool,
    element_plytowy: bool,
    kontrola_jakosci: bool,
    beton_na_gruncie: str,
    dg_gt_32: bool,
    delta_dur_gamma: float,
    delta_dur_st: float,
    delta_dur_add: float,
    delta_dev: float,
) -> dict:
    zmiana = get_structural_class_adjustment(
        klasa_betonu,
        klasa_ekspozycji,
        zywotnosc_100_lat,
        element_plytowy,
        kontrola_jakosci,
    )
    final_num = max(1, min(6, 4 + zmiana))
    klasa_konstrukcji_final = f"S{final_num}"

    c_min_dur = get_c_min_dur_value(klasa_ekspozycji, klasa_konstrukcji_final)

    c_min_b = fi_mm
    if dg_gt_32:
        c_min_b += 5.0

    c_min_dur_mod = c_min_dur + delta_dur_gamma - delta_dur_st - delta_dur_add
    c_min = max(c_min_b, c_min_dur_mod, 10.0)

    c_nom = c_min + delta_dev

    k1 = 40.0
    k2 = 75.0
    limit_gruntu = 0.0
    if beton_na_gruncie == "Na przygotowanym podłożu":
        limit_gruntu = k1
    elif beton_na_gruncie == "Bezpośrednio na gruncie":
        limit_gruntu = k2

    c_nom = max(c_nom, limit_gruntu)

    return {
        "klasa_ekspozycji": klasa_ekspozycji,
        "klasa_konstrukcji_final": klasa_konstrukcji_final,
        "c_min_dur": c_min_dur,
        "c_min_b": c_min_b,
        "c_min": c_min,
        "c_nom": c_nom,
        "zmiana_klasy": zmiana,
        "limit_gruntu": limit_gruntu,
    }


# =============================================================================
# STRONA GŁÓWNA STREAMLIT
# =============================================================================


def StronaOtulinaZbrojenia():
    st.markdown(
        """
        <style>
        .block-container { padding-top: 1.5rem; padding-bottom: 1.5rem; }
        h3 { margin-top: 1.0rem !important; margin-bottom: 0.4rem !important; font-size: 1.1rem; }
        
        /* USUNIĘTO AGRESYWNY STYL DLA PRZYCISKÓW */
        
        .big-result {
            font-size: 26px; font-weight: bold; color: #2E8B57; background-color: #f0f2f6;
            padding: 15px; border-radius: 8px; text-align: center; margin-top: 20px; border: 2px solid #2E8B57;
        }
        div.row-widget.stRadio > div { flex-direction: row; gap: 16px; }

        .header-help-icon {
            display:inline-flex;
            align-items:center;
            justify-content:center;
            width:18px;
            height:18px;
            border-radius:50%;
            border:1px solid #aaa;
            color:#aaa;
            font-size:11px;
            font-weight:600;
            cursor:help;
            transform:translateY(1px);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Tytuł kalkulatora
    st.markdown(
        """
        <div style="text-align:center; margin-top:0.4rem; margin-bottom:0rem;">
            <span style="font-size:42px; font-weight:800; letter-spacing:1px; color:#dddddd;">
                OTULINA PRĘTÓW ZBROJENIOWYCH
            </span>
        </div>
        <div style="text-align:center; font-size:14px; color:#aaaaaa; margin-top:-12px; margin-bottom:0.6rem;">
            wg PN-EN 1992-1-1
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Dane wejściowe
    # REORDERED INPUTS: 1. Exposure, 2. Concrete, 3. Diameter
    st.markdown("### DANE WEJŚCIOWE")

    col_eksp, col_beton, col_fi = st.columns([1.9,1.05,1.05])
    
    with col_eksp:
        klasy_ekspozycji = [
            "X0",
            "XC1",
            "XC2",
            "XC3",
            "XC4",
            "XD1",
            "XD2",
            "XD3",
            "XS1",
            "XS2",
            "XS3",
        ]
        idx_eksp = klasy_ekspozycji.index("XC1")
        klasa_ekspozycji = st.selectbox(
            "Klasa ekspozycji", klasy_ekspozycji, index=idx_eksp
        )

    with col_beton:
        try:
            from TABLICE.ParametryBetonu import list_concrete_classes

            klasy_betonu = list_concrete_classes()
            idx_bet = klasy_betonu.index("C30/37") if "C30/37" in klasy_betonu else 0
        except ImportError:
            klasy_betonu = ["C25/30", "C30/37"]
            idx_bet = 1
        klasa_betonu = st.selectbox("Klasa betonu", klasy_betonu, index=idx_bet)

    with col_fi:
        try:
            from TABLICE.ParametryPretowZbrojeniowych import list_bar_diameters

            dostepne_fi = list_bar_diameters()
        except ImportError:
            dostepne_fi = [6, 8, 10, 12, 14, 16, 18, 20, 22, 25, 28, 32, 40]
        fi_mm = st.selectbox("Średnica pręta Φ [mm]", dostepne_fi, index=3)

       
  # Uwarunkowania konstrukcyjne / wykonawcze
    col_okres, col_geom, col_kontrola, c_krusz = st.columns([0.95, 0.95, 1.05, 1.05])

    with col_okres:
        st.markdown("Projektowy okres użytkowania")
        okres_uzytkowania = st.radio(
            "okres",
            ["50 lat", "100 lat"],
            index=0,
            label_visibility="collapsed",
            key="radio_okres",
            horizontal=True
        )
        is_100_lat = okres_uzytkowania == "100 lat"

    with col_geom:
        st.markdown("Geometria elementu")
        geometria = st.radio(
            "geometria",
            ["Płyta", "Belka / Słup / Inne"],
            index=0,
            label_visibility="collapsed",
            key="radio_geom",
            horizontal=True
        )
        is_plyta = geometria == "Płyta"

    with col_kontrola:
        st.markdown("Specjalna kontrola jakości")
        kontrola_jakosci_str = st.radio(
            "kontrola",
            ["Nie", "Tak"],
            index=0,
            label_visibility="collapsed",
            key="radio_kontrola",
            horizontal=True
        )
        kontrola = kontrola_jakosci_str == "Tak"

    with c_krusz:
        st.markdown("Maksymalny wymiar kruszywa")
        kruszywo_opts = ["$d_g \\le 32$ mm", "$d_g > 32$ mm"]
        kruszywo_str = st.radio(
            "kruszywo",
            kruszywo_opts,
            index=0,
            label_visibility="collapsed",
            key="radio_kruszywo",
            horizontal=True
        )
        dg_gt_32 = kruszywo_str == "$d_g > 32$ mm"
    kruszywo_opis = "d_g ≤ 32 mm" if not dg_gt_32 else "d_g > 32 mm"
     
    # --- POPRAWKA: Inicjalizacja zmiennych przed użyciem ---
    dc_gamma = 0.0
    dc_st = 0.0
    dc_add = 0.0
    # -------------------------------------------------------

    c_grunt, c_odchylki_w, c_odchylki_q  = st.columns([1.9, 1.05, 1.05])

    with c_grunt:
        st.markdown("Betonowanie na gruncie")
        grunt_opts = ["Nie", "Na przygotowanym podłożu", "Bezpośrednio na gruncie"]
        betonowanie_grunt = st.radio(
            "grunt",
            grunt_opts,
            index=0,
            label_visibility="collapsed",
            key="radio_grunt",
            horizontal=True
        )

    with c_odchylki_w:
        # Poprawiony kod HTML i nagłówek dla 4 kolumny
        st.markdown(
            """
            <div style="display:flex;align-items:center;gap:6px;">
                <span style="font-weight:400; font-size:1rem;">Odchyłka wykonawcza Δc<sub>dev</sub></span>
                <span class="header-help-icon"
                    title="Domyślnie 10 mm (EC2). Można zmniejszyć do 5 lub 0 mm przy wysokiej kontroli.">?</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
                
        delta_dev = st.selectbox(
            "delta_dev_label",
            [0, 5, 10],
            index=2,
            key="delta_dev",
            label_visibility="collapsed"
        )

    with c_odchylki_q:
        # Styled Header with Help Icon
        st.markdown(
            """
            <div style="display:flex;align-items:center;gap:6px;">
              <span style="font-weight:400; font-size:1rem;">Odchyłki dodatkowe</span>
              <span class="header-help-icon"
                  title="Wg Załącznika Krajowego do PN-EN 1992-1-1 zalecane wartości wynoszą: Δc_dur,γ = 0 mm, Δc_dur,st = 0 mm, Δc_dur,add = 0 mm.">?</span>
            </div>
            <div style="font-size: 13px; color: #888; margin-bottom: 5px;">
            (Δc<sub>dur,γ</sub>, Δc<sub>dur,st</sub>, Δc<sub>dur,add</sub>)
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Explicit Question Label (Cleaned)
        st.write("Czy przyjąć inne wartości niż zalecane w NA?")
        
        u_odchylki_str = st.radio(
            "odchylki_yn",
            ["Nie", "Tak"],
            index=0,
            label_visibility="collapsed",
            horizontal=True
        )
        
        if u_odchylki_str == "Tak":
            st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
            dc_gamma = st.number_input(r"$\Delta c_{dur,\gamma}$ [mm]", value=0.0, step=1.0)
            dc_st = st.number_input(r"$\Delta c_{dur,st}$ [mm]", value=0.0, step=1.0)
            dc_add = st.number_input(r"$\Delta c_{dur,add}$ [mm]", value=0.0, step=1.0)

    col_rys1, col_rys2 = st.columns(2)

    with col_rys1:    
        with st.expander("ℹ️ Pomoc: Opis klas ekspozycji (Tablica 4.1)", expanded=False):
            rys_eksp = SCIEZKA_FOLDERU_LOKALNEGO / "Otulina_klasy ekspozycji.png"
            if rys_eksp.exists():
                st.image(str(rys_eksp), use_container_width=True)
            else:
                st.info(f"Brak pliku pomocy: {rys_eksp.name}")

    with col_rys2:   
        with st.expander("ℹ️ Pomoc: Klasyfikacja konstrukcji (Tablica 4.3N)", expanded=False):
            rys_klasy = SCIEZKA_FOLDERU_LOKALNEGO / "Otulina_klasy konstrukcji.png"
            if rys_klasy.exists():
                st.image(str(rys_klasy), use_container_width=True)
            else:
                st.info(f"Brak pliku: {rys_klasy.name}")
    
    # OBLICZENIA - DODANO TYPE PRIMARY
    _, c_center, _ = st.columns([1, 2, 1])
    with c_center:
        oblicz = st.button("OBLICZ", type="primary", use_container_width=True)
        
    if oblicz:
        try:
            wynik = ObliczOtuline(
                klasa_ekspozycji=klasa_ekspozycji,
                fi_mm=float(fi_mm),
                klasa_betonu=klasa_betonu,
                zywotnosc_100_lat=is_100_lat,
                element_plytowy=is_plyta,
                kontrola_jakosci=kontrola,
                beton_na_gruncie=betonowanie_grunt,
                dg_gt_32=dg_gt_32,
                delta_dur_gamma=dc_gamma,
                delta_dur_st=dc_st,
                delta_dur_add=dc_add,
                delta_dev=float(delta_dev),
            )

            st.session_state["wynik_otuliny"] = wynik
            st.session_state["inputs_otuliny"] = {
                "klasa_betonu": klasa_betonu,
                "klasa_ekspozycji": klasa_ekspozycji,
                "fi_mm": fi_mm,
                "zywotnosc_100": is_100_lat,
                "plyta": is_plyta,
                "delta_dev": delta_dev,
                "betonowanie_grunt": betonowanie_grunt,
                "kontrola_jakosci_str": kontrola_jakosci_str,
                "kruszywo_opis": kruszywo_opis,
                "dc_gamma": dc_gamma,
                "dc_st": dc_st,
                "dc_add": dc_add,
            }
            st.session_state["pokaz_otuline"] = True

        except Exception as e:
            st.error(f"Wystąpił błąd podczas obliczeń: {e}")
            st.session_state["pokaz_otuline"] = False

    # WYNIKI
    if st.session_state.get("pokaz_otuline", False):
        wynik = st.session_state["wynik_otuliny"]
        inputs = st.session_state["inputs_otuliny"]
        c_nom = wynik["c_nom"]
        c_min = wynik["c_min"]

        st.markdown(
            f"""
            <div class="big-result">
                Nominalna otulina <i>c</i><sub>nom</sub> = {c_nom:.0f} mm
            </div>
            """,
            unsafe_allow_html=True,
        )
               
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        with st.expander("Szczegóły obliczeń", expanded=False):
            st.write("**1. Klasa konstrukcji (Tablica 4.3N):**")

            zmiana = wynik["zmiana_klasy"]
            skladniki = []

            if inputs.get("zywotnosc_100"):
                skladniki.append(
                    (2, "Zwiększenie okresu użytkowania (100 lat)")
                )

            try:
                fck_local = int(
                    str(inputs["klasa_betonu"]).split("/")[0].replace("C", "")
                )
            except Exception:
                fck_local = 20

            eksp_local = wynik.get("klasa_ekspozycji", inputs["klasa_ekspozycji"])
            redukcja_wytrz = False
            if eksp_local == "XC1" and fck_local >= 30:
                redukcja_wytrz = True
            elif eksp_local in ["XC2", "XC3"] and fck_local >= 35:
                redukcja_wytrz = True
            elif eksp_local == "XC4" and fck_local >= 40:
                redukcja_wytrz = True
            elif eksp_local in ["XD1", "XD2", "XS1"] and fck_local >= 40:
                redukcja_wytrz = True
            elif eksp_local in ["XD3", "XS2", "XS3"] and fck_local >= 45:
                redukcja_wytrz = True

            if redukcja_wytrz:
                skladniki.append(
                    (-1, f"Redukcja ze względu na klasę wytrzymałości ({inputs['klasa_betonu']})")
                )

            if inputs.get("plyta") and eksp_local == "XC1":
                skladniki.append(
                    (-1, "Element płytowy w klasie ekspozycji XC1")
                )

            if inputs.get("kontrola_jakosci_str") == "Tak":
                skladniki.append(
                    (-1, "Specjalna kontrola jakości produkcji betonu")
                )

            st.markdown("Bazowa klasa konstrukcji: S4.")
            st.markdown("Modyfikacja klasy konstrukcji ze względu na warunki projektowe:")

            if not skladniki:
                st.markdown("&nbsp;&nbsp;&nbsp;&nbsp;- Brak modyfikacji", unsafe_allow_html=True)
            else:
                for delta, opis in skladniki:
                    znak = "+" if delta > 0 else ""
                    st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;ΔS = {znak}{delta}: {opis}", unsafe_allow_html=True)

            st.markdown(f"Obliczeniowa klasa konstrukcji: **{wynik['klasa_konstrukcji_final']}**")

            st.markdown("<br>", unsafe_allow_html=True)

            st.write("**2. Składowe $c_{min}$:**")
            st.latex(rf"c_{{min,b}} = {wynik['c_min_b']:.0f}\text{{ mm }}")
            st.latex(rf"c_{{min,dur}} = {wynik['c_min_dur']:.0f}\text{{ mm }}")
            st.latex(
                r"c_{min} = \max\Big(c_{min,b};\; c_{min,dur} + \Delta c_{dur,\gamma} - \Delta c_{dur,st} - \Delta c_{dur,add};\; 10\text{ mm}\Big)"
            )

            st.latex(
                rf"c_{{min}} = \max\Big({wynik['c_min_b']:.0f}\text{{ mm}};\; "
                rf"{wynik['c_min_dur']:.0f}\text{{ mm}} + {inputs['dc_gamma']:.0f}\text{{ mm}} - {inputs['dc_st']:.0f}\text{{ mm}} - {inputs['dc_add']:.0f}\text{{ mm}};\; "
                r"10\text{ mm}\Big)"
                rf" = \mathbf{{{c_min:.0f}\text{{ mm}}}}"
            )

            if wynik["limit_gruntu"] > 0:
                st.write("**3. Warunek gruntowy (betonowanie na gruncie):**")
                st.write(
                    f"- Sposób betonowania: **{inputs['betonowanie_grunt']}** \n"
                    f"- Wymagana minimalna otulina ze względu na warunki gruntowe: "
                    f"$c_{{nom}} \\ge {wynik['limit_gruntu']:.0f} \\text{{ mm}}$"
                )

            st.write("**4. Wynik końcowy:**")
            st.latex("c_{nom} = c_{min} + \\Delta c_{dev}")
            st.latex(
                rf"c_{{nom}} = {c_min:.0f}\text{{ mm}} + "
                rf"{float(inputs['delta_dev']):.0f}\text{{ mm}}"
                rf" = \mathbf{{{c_nom:.0f}\text{{ mm}}}}"
            )


if __name__ == "__main__":
    StronaOtulinaZbrojenia()