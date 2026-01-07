import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import sys
from pathlib import Path

# --- KONFIGURACJA ŚCIEŻEK ---
SCIEZKA_PLIKU = Path(__file__).resolve()
SCIEZKA_BAZOWA = SCIEZKA_PLIKU.parents[2] # Zakładamy strukturę: GLOWNY / _MODULY / EC2_PODSTAWOWE DANE_PARAMETRY BETONU / plik.py

if str(SCIEZKA_BAZOWA) not in sys.path:
    sys.path.append(str(SCIEZKA_BAZOWA))

def StronaParametryBetonu():
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
                PARAMETRY BETONU
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
        from TABLICE.ParametryBetonu import get_concrete_params, list_concrete_classes
    except ImportError as e:
        st.error(f"⚠️ Błąd importu modułu `TABLICE.ParametryBetonu`: {e}. \n\nUpewnij się, że folder `TABLICE` znajduje się w katalogu głównym aplikacji.")
        return

    # --- STAŁE NORMOWE ---
    GAMMA_C = 1.4
    ACC = 1.0

    # --- UKŁAD KOLUMNOWY (WEJŚCIE + TABELA) ---
    col1, col2 = st.columns([1, 2])

    # ---------------------------------------
    # LEWA KOLUMNA: DANE WEJŚCIOWE
    # ---------------------------------------
    with col1:
        st.subheader("DANE WEJŚCIOWE")
        dostepne_klasy = list_concrete_classes()
        idx_def = dostepne_klasy.index("C30/37") if "C30/37" in dostepne_klasy else 0
        wybrana_klasa = st.selectbox("Klasa betonu:", dostepne_klasy, index=idx_def)

        # Obliczenia
        beton = get_concrete_params(wybrana_klasa)
        fcd = (ACC * beton.fck) / GAMMA_C

    # ---------------------------------------
    # PRAWA KOLUMNA: ZESTAWIENIE PARAMETRÓW
    # ---------------------------------------
    with col2:
        st.markdown(
            """
            <div style="display:flex;align-items:center;gap:6px; margin-bottom: 10px;">
                <h3 style="margin:0;">ZESTAWIENIE PARAMETRÓW BETONU</h3>
                <span class="header-help-icon"
                    title="Przyjęto: γc = 1.40 oraz αcc = 1.00.">
                    ?
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        md_table = f"""
        | Symbol | Opis | Wartość | Jedn. |
        | :--- | :--- | :--- | :--- |
        | $f_{{ck}}$ | Charakt. wytrz. na ściskanie (walec) | {beton.fck} | MPa |
        | $f_{{ck,cube}}$ | Charakt. wytrz. na ściskanie (kostka) | {beton.fck_cube} | MPa |
        | $f_{{cm}}$ | Średnia wytrz. na ściskanie | {beton.fcm} | MPa |
        | $f_{{ctm}}$ | Średnia wytrz. na rozciąganie | {beton.fctm} | MPa |
        | $f_{{ctk,0.05}}$ | Charakt. wytrz. na rozc. (5%) | {beton.fctk_0_05} | MPa |
        | $f_{{ctk,0.95}}$ | Charakt. wytrz. na rozc. (95%) | {beton.fctk_0_95} | MPa |
        | $E_{{cm}}$ | Sieczny moduł sprężystości | {beton.Ecm:.0f} | MPa |
        | $\\varepsilon_{{c1}}$ | Odkształcenie przy $\\sigma_{{max}}$ | {beton.eps_c1} | ‰ |
        | $\\varepsilon_{{cu1}}$ | Odkształcenie graniczne | {beton.eps_cu1} | ‰ |
        | $\\varepsilon_{{c2}}$ | Odkształcenie $\\sigma_{{max}}$ (parabola) | {beton.eps_c2} | ‰ |
        | $\\varepsilon_{{cu2}}$ | Odkształcenie gran. (parabola) | {beton.eps_cu2} | ‰ |
        """
        st.markdown(md_table)

    # ---------------------------------------
    # WYKRES σ–ε (PARABOLA–PROSTOKĄT)
    # ---------------------------------------
    with st.expander("📈 Wykres σ–ε (parabola–prostokąt)", expanded=False):
        eps_c2 = beton.eps_c2   # [‰]
        eps_cu2 = beton.eps_cu2 # [‰]
        n_exp = beton.n

        strain = np.linspace(0, eps_cu2, 200)
        stress = []
        for e in strain:
            if e <= eps_c2:
                # model parabola–prostokąt w ujęciu obliczeniowym (kształt z EC2)
                val = fcd * (1 - (1 - e / eps_c2) ** n_exp)
                stress.append(val)
            else:
                stress.append(fcd)

        fig, ax = plt.subplots(figsize=(7, 4))
        ax.plot(strain, stress, linewidth=2.5, label="Beton (obliczeniowy)")
        ax.fill_between(strain, stress, alpha=0.08)

        # Pozioma linia przy fcd
        ax.axhline(y=fcd, linestyle="-.", linewidth=1, alpha=0.6)
        # Piony przy eps_c2 i eps_cu2
        ax.axvline(x=eps_c2, linestyle=":", linewidth=1, alpha=0.7)
        ax.axvline(x=eps_cu2, linestyle="--", linewidth=1, alpha=0.7)

        # Podpisy symboli + wartości przy osi odkształceń (na dole wykresu)
        ax.text(
            eps_c2,
            0,
            f"εc2 = {eps_c2:.2f} ‰",
            fontsize=9,
            ha="center",
            va="bottom",
        )
        ax.text(
            eps_cu2,
            0,
            f"εcu2 = {eps_cu2:.2f} ‰",
            fontsize=9,
            ha="center",
            va="bottom",
        )

        # Podpis fcd
        ax.annotate(
            f"fcd = {fcd:.1f} MPa",
            xy=(0, fcd),
            xytext=(0.2 * eps_cu2, fcd * 1.03),
            fontsize=9,
            va="bottom",
        )

        # Bez LaTeXa w osiach dla czytelności w matplotlib
        ax.set_xlabel("Odkształcenie εc [‰]", fontsize=11)
        ax.set_ylabel("Naprężenie σc [MPa]", fontsize=11)

        ax.grid(True, linestyle="--", alpha=0.4)
        ax.set_xlim(left=0, right=eps_cu2 * 1.05)
        ax.set_ylim(bottom=0, top=fcd * 1.25)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        fig.tight_layout()
        st.pyplot(fig)