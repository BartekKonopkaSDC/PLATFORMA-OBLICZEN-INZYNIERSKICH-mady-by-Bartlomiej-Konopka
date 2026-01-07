import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import sys
from pathlib import Path

# --- KONFIGURACJA ŚCIEŻEK ---
SCIEZKA_PLIKU = Path(__file__).resolve()
SCIEZKA_BAZOWA = SCIEZKA_PLIKU.parents[2] # Zakładamy strukturę: GLOWNY / _MODULY / KATALOG / plik.py

if str(SCIEZKA_BAZOWA) not in sys.path:
    sys.path.append(str(SCIEZKA_BAZOWA))

def StronaParametryStali():
    # --- STYL ---
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 1.5rem;
        }
        h3 {
            margin-top: 1.0rem !important;
            margin-bottom: 0.4rem !important;
            font-size: 1.1rem;
        }
        div.row-widget.stRadio > div {
            flex-direction: row;
            align-items: center;
        }
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

    # --- TYTUŁ GŁÓWNY ---
    st.markdown(
        """
        <div style="text-align:center; margin-top:0.4rem; margin-bottom:0rem;">
            <span style="font-size:42px; font-weight:800; letter-spacing:1px; color:#dddddd;">
                PARAMETRY STALI ZBROJENIOWEJ
            </span>
        </div>
        <div style="text-align:center; font-size:14px; color:#aaaaaa; margin-top:-12px; margin-bottom:0.6rem;">
            wg PN-EN 1992-1-1
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- IMPORTY ZABEZPIECZONE (Wewnątrz funkcji) ---
    try:
        from TABLICE.ParametryStali import get_steel_params, list_steel_grades
    except ImportError as e:
        st.error(f"⚠️ Błąd importu modułu `TABLICE.ParametryStali`: {e}. \n\nUpewnij się, że folder `TABLICE` znajduje się w katalogu głównym aplikacji.")
        return

    # --- STAŁE NORMOWE ---
    GAMMA_S = 1.15

    # --- UKŁAD KOLUMNOWY (WEJŚCIE + TABELA) ---
    col1, col2 = st.columns([1, 2])

    # ---------------------------------------
    # LEWA KOLUMNA: DANE WEJŚCIOWE
    # ---------------------------------------
    with col1:
        st.subheader("DANE WEJŚCIOWE")
        stale_lista = list_steel_grades()
        idx_def = stale_lista.index("B500") if "B500" in stale_lista else 0
        wybrana_nazwa = st.selectbox("Gatunek stali:", stale_lista, index=idx_def)

        # Obliczenia
        stal = get_steel_params(wybrana_nazwa)
        fyk_val = stal.fyk           # [MPa]
        Es_val = stal.Es             # [MPa]
        fyd = fyk_val / GAMMA_S      # [MPa]
        epsilon_yd = (fyd / Es_val) * 1000  # [‰]

    # ---------------------------------------
    # PRAWA KOLUMNA: ZESTAWIENIE PARAMETRÓW
    # ---------------------------------------
    with col2:
        st.markdown(
            """
            <div style="display:flex;align-items:center;gap:6px; margin-bottom: 10px;">
                <h3 style="margin:0;">ZESTAWIENIE PARAMETRÓW STALI</h3>
                <span class="header-help-icon"
                    title="Przyjęto współczynnik bezpieczeństwa stali γs = 1.15.">
                    ?
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        md_table_stal = f"""
        | Symbol | Opis | Wartość | Jedn. |
        | :--- | :--- | :--- | :--- |
        | $f_{{yk}}$ | Charakterystyczna granica plastyczności | {fyk_val:.0f} | MPa |
        | $f_{{yd}}$ | Obliczeniowa granica plastyczności ($f_{{yk}}/\\gamma_s$) | {fyd:.2f} | MPa |
        | $E_s$ | Moduł sprężystości stali | {Es_val/1000:.0f} | GPa |
        | $\\varepsilon_{{yd}}$ | Odkształcenie przy $f_{{yd}}$ | {epsilon_yd:.2f} | ‰ |
        """
        st.markdown(md_table_stal)

    # ---------------------------------------
    # TABELA KLAS STALI A/B/C WG EC2 (NAD WYKRESEM)
    # ---------------------------------------
    with st.expander("ℹ️ Pomoc: Klasyfikacja stali zbrojeniowej (A, B, C) wg PN-EN 1992-1-1", expanded=False):
        st.markdown(
            """
            | Klasa stali | Granica plastyczności $f_{yk}$ [MPa] | Stosunek $f_{tk}/f_{yk}$ [-] | Wydłużenie pod maks. obciążeniem $\\varepsilon_{uk}$ [%] |
            | :---: | :---: | :---: | :---: |
            | A | 400 – 600 | $\\geq 1{,}05$ | $\\geq 2{,}5$ |
            | B | 400 – 600 | $\\geq 1{,}08$ | $\\geq 5{,}0$ |
            | C | 400 – 600 | 1,15 – 1,35 | $\\geq 7{,}5$ |
            """,
            unsafe_allow_html=True,
        )

    # ---------------------------------------
    # WYKRES σ–ε (IDEALNIE SPRĘŻYSTO–PLASTYCZNY)
    # ---------------------------------------
    with st.expander("📈 Wykres σ–ε (idealnie sprężysto–plastyczny)", expanded=False):
        eps_max = 25.0
        strains = np.linspace(0, eps_max, 200)

        # Es_val [MPa], strains [‰]
        stresses = [e * (Es_val / 1000) if e < epsilon_yd else fyd for e in strains]

        fig, ax = plt.subplots(figsize=(7, 4))

        # Krzywa obliczeniowa (fyd)
        ax.plot(strains, stresses, linewidth=2.5, label="Stal – model obliczeniowy (fyd)")

        # Linie pomocnicze dla fyk (charakt.)
        eps_yk = fyk_val / (Es_val / 1000)  # [‰]
        ax.plot(
            [0, eps_yk, eps_max],
            [0, fyk_val, fyk_val],
            color="gray",
            linestyle="--",
            alpha=0.4,
            label="fyk (charakt.)",
        )

        # Pion przy epsilon_yd
        ax.axvline(x=epsilon_yd, color="black", linestyle=":", linewidth=1)

        # Podpis symbol + wartość przy osi odkształceń (na dole wykresu)
        ax.text(
            epsilon_yd,
            0,
            f"εyd = {epsilon_yd:.2f} ‰",
            fontsize=9,
            ha="center",
            va="bottom",
        )

        # Podpis fyd
        ax.annotate(
            f"fyd = {fyd:.1f} MPa",
            xy=(0, fyd),
            xytext=(1.0, fyd * 1.05),
            fontsize=9,
            va="bottom",
        )

        ax.set_xlabel("Odkształcenie εs [‰]", fontsize=11)
        ax.set_ylabel("Naprężenie σs [MPa]", fontsize=11)

        ax.grid(True, linestyle="--", alpha=0.4)
        ax.set_ylim(bottom=0, top=fyk_val * 1.20)
        ax.set_xlim(left=0, right=eps_max)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.legend(loc="lower right")
        fig.tight_layout()
        st.pyplot(fig)