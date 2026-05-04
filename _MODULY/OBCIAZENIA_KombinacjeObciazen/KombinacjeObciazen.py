"""
KombinacjeObciazen.py
Wspólny kalkulator: SGN + SGU na zakładkach

Środek kalkulatorów (SGN i SGU) skopiowany 1:1 z:
- KombinacjeObciazenSGN.py
- KombinacjeObciazenSGU.py
"""

import streamlit as st
from pathlib import Path
import sys
from typing import List, Dict, Tuple, Any

# --- KONFIGURACJA ŚCIEŻEK (jak w oryginalnych plikach) ---
SCIEZKA_PLIKU = Path(__file__).resolve()

SCIEZKA_BAZOWA = None
for parent in SCIEZKA_PLIKU.parents:
    if parent.name.upper() == "KALKULATORY":
        SCIEZKA_BAZOWA = parent
        break

if SCIEZKA_BAZOWA is None:
    SCIEZKA_BAZOWA = SCIEZKA_PLIKU.parents[2]

if str(SCIEZKA_BAZOWA) not in sys.path:
    sys.path.append(str(SCIEZKA_BAZOWA))


# =============================================================================
# GENERATORY TABEL HTML (STYLIZACJA ANALOGICZNA DO OBCIĄŻEŃ UŻYTKOWYCH)
# =============================================================================

def generate_sgn_html_table(data_dict: Dict[str, Tuple[float, float, float]], ui_map: Dict[str, str]) -> str:
    """
    Generuje tabelę HTML dla SGN (kolumny: Oddziaływania, psi0).
    """
    html = """
    <style>
        .custom-table {
            width: 100%;
            border-collapse: collapse;
            font-family: sans-serif;
            font-size: 14px;
            color: #ffffff;
            background-color: #2b2b2b;
        }
        .custom-table th {
            background-color: #000000;
            color: #ffffff;
            border: 1px solid #555;
            padding: 8px;
            text-align: left;
            font-weight: 600;
        }
        .custom-table td {
            border: 1px solid #555;
            padding: 8px;
            vertical-align: middle;
        }
        .center-text {
            text-align: center;
        }
    </style>
    <table class="custom-table">
        <thead>
            <tr>
                <th style="width: 80%;">Oddziaływania</th>
                <th style="width: 20%; text-align: center;">ψ₀</th>
            </tr>
        </thead>
        <tbody>
    """
    
    for key, values in data_dict.items():
        psi0 = values[0]
        # Pobranie ładnej nazwy i zamiana \n na <br>
        name = ui_map.get(key, key).replace("\n", "<br>")
        
        row_html = "<tr>"
        row_html += f'<td>{name}</td>'
        row_html += f'<td class="center-text">{psi0:.1f}</td>'
        row_html += "</tr>"
        html += row_html
        
    html += "</tbody></table>"
    return html


def generate_sgu_html_table(data_dict: Dict[str, Tuple[float, float]], ui_map: Dict[str, str]) -> str:
    """
    Generuje tabelę HTML dla SGU (kolumny: Oddziaływania, psi1, psi2).
    """
    html = """
    <style>
        .custom-table {
            width: 100%;
            border-collapse: collapse;
            font-family: sans-serif;
            font-size: 14px;
            color: #ffffff;
            background-color: #2b2b2b;
        }
        .custom-table th {
            background-color: #000000;
            color: #ffffff;
            border: 1px solid #555;
            padding: 8px;
            text-align: left;
            font-weight: 600;
        }
        .custom-table td {
            border: 1px solid #555;
            padding: 8px;
            vertical-align: middle;
        }
        .center-text {
            text-align: center;
        }
    </style>
    <table class="custom-table">
        <thead>
            <tr>
                <th style="width: 70%;">Oddziaływania</th>
                <th style="width: 15%; text-align: center;">ψ₁</th>
                <th style="width: 15%; text-align: center;">ψ₂</th>
            </tr>
        </thead>
        <tbody>
    """
    
    for key, values in data_dict.items():
        psi1 = values[0]
        psi2 = values[1]
        name = ui_map.get(key, key).replace("\n", "<br>")
        
        row_html = "<tr>"
        row_html += f'<td>{name}</td>'
        row_html += f'<td class="center-text">{psi1:.1f}</td>'
        row_html += f'<td class="center-text">{psi2:.1f}</td>'
        row_html += "</tr>"
        html += row_html
        
    html += "</tbody></table>"
    return html


# =============================================================================
# CZĘŚĆ 1 – SGN (kopiuj-wklej z KombinacjeObciazenSGN.py)
# =============================================================================

# --- STAŁE NORMATYWNE DLA SGN (PN-EN 1990 A1.3) ---
GAMMA_G_SUP = 1.35
GAMMA_G_INF = 1.00
GAMMA_Q_SUP_VAL = 1.50
GAMMA_Q_INF_VAL = 0.00
GAMMA_P = 1.00
XI_RECOM = 0.85

# Wartości Psi z PN-EN 1990 (Tabela A1.1) - [psi0, psi1, psi2]
PSI_TABLE_RAW_SGN: Dict[str, Tuple[float, float, float]] = {
    "A: Mieszkalne": [0.7, 0.5, 0.3],
    "B: Biurowe": [0.7, 0.5, 0.3],
    "C: Zebrań": [0.7, 0.7, 0.6],
    "D: Handlowe": [0.7, 0.7, 0.6],
    "E: Magazynowe": [1.0, 0.9, 0.8],
    "F: Ruch Pojazdow lekki": [0.7, 0.7, 0.6],
    "G: Ruch Pojazdow ciezki": [0.7, 0.7, 0.6],
    "H: Dachy (inne niz snieg)": [0.0, 0.0, 0.0],
    "Snieg (H <= 1000m)": [0.5, 0.2, 0.0],
    "Snieg (H > 1000m)": [0.7, 0.5, 0.2],
    "Wiatr": [0.6, 0.2, 0.0],
    "Temperatura": [0.6, 0.5, 0.0],
}

# MAPOWANIE NAZWA_ASCII -> NAZWA_UI
UI_CATEGORIES_SGN: Dict[str, str] = {
    "A: Mieszkalne": "KATEGORIA A: powierzchnie mieszkalne",
    "B: Biurowe": "KATEGORIA B: powierzchnie biurowe",
    "C: Zebrań": "KATEGORIA C: miejsca zebrań",
    "D: Handlowe": "KATEGORIA D: powierzchnie handlowe",
    "E: Magazynowe": "KATEGORIA E: powierzchnie magazynowe",
    "F: Ruch Pojazdow lekki": "KATEGORIA F: ruchu pojazdów ≤30kN",
    "G: Ruch Pojazdow ciezki": "KATEGORIA G: ruchu pojazdów 30kN < P ≤160kN",
    "H: Dachy (inne niz snieg)": "KATEGORIA H: dachy",
    "Snieg (H <= 1000m)": "OBCIĄŻENIE ŚNIEGIEM (H ≤ 1000 m n.p.m.)",
    "Snieg (H > 1000m)": "OBCIĄŻENIE ŚNIEGIEM (H > 1000 m n.p.m.)",
    "Wiatr": "OBCIĄŻENIE WIATREM",
    "Temperatura": "OBCIĄŻENIE TEMPERATURĄ",
}


def StronaKombinacjeSGN():
    # --- TYTUŁ W SEKCJACH USUNIĘTY NA RZECZ TYTUŁU GŁÓWNEGO ---
    st.markdown("### Stan Graniczny Nośności (SGN)")

    # TREŚĆ WPROWADZAJĄCA
    st.markdown(
        r"""
        Stan graniczny nośności to stan, w którym konstrukcja, jej element lub podłoże **tracą zdolność do przenoszenia obciążeń** (np. zniszczenie materiału, utrata stateczności). Sprawdzenia SGN mają na celu zapewnienie bezpieczeństwa.
        
        **Główne Stany Graniczne Nośności:**
        * **STR (Nośność przekroju/elementu):** Sprawdzenie wewnętrznego zniszczenia elementu konstrukcyjnego (np. zginanie, ścinanie, ściskanie). Decydująca jest **wytrzymałość materiałów konstrukcji**.
        * **GEO (Nośność podłoża):** Sprawdzenie zniszczenia lub nadmiernego odkształcenia podłoża (np. nośność gruntu, stateczność fundamentów). Decydująca jest **wytrzymałość gruntu/skały**.
        * **EQU (Równowaga statyczna):** Utrata równowagi sztywnej konstrukcji (sprawdzana wg *innej* kombinacji PN-EN 1990, Tablica A1.2(A)).
        * **FAT (Zmęczenie):** Zniszczenie zmęczeniowe na skutek powtarzalnych obciążeń.
        """
    )

    st.markdown("---")

    # 2. Kombinacje Obciążeń
    st.markdown("### Kombinacje Obciążeń w sytuacjach trwałych i przejściowych")

    st.markdown(
        r"""
        W projektowaniu stanów granicznych nośności wykorzystuje się **albo** kombinację podstawową **6.10** **albo** analizę dwóch kombinacji **6.10a i 6.10b** (wybieramy z nich efekt obciążenia $E_d$ mniej korzystny).
        
        #### Wyrażenie (6.10) - Kombinacja Podstawowa
        """
    )
    st.latex(
        r"E_d = \sum_{j\ge 1}\gamma_{G,j}G_{k,j} + \gamma_{P}P + \gamma_{Q,1}Q_{k,1} + \sum_{i>1}\gamma_{Q,i}\psi_{0,i}Q_{k,i}"
    )

    st.markdown(r"#### Wyrażenie (6.10a) - Pełne $\gamma_{G,sup}$")
    st.latex(
        r"E_d = \sum_{j\ge 1} (\gamma_{G,j} \cdot G_{k,j}) + \gamma_{P} \cdot P + \gamma_{Q} \cdot Q_{k,1} + \sum_{i>1} (\gamma_{Q} \cdot \psi_{0,i} \cdot Q_{k,i})"
    )

    st.markdown(
        r"#### Wyrażenie (6.10b) - Zredukowane $\gamma_{G,sup}$ przez $\mathbf{\xi}$"
    )
    st.latex(
        r"E_d = \sum_{j\ge 1} (\mathbf{\xi} \cdot \gamma_{G,j,sup} \cdot G_{k,j,sup}) + \sum_{j\ge 1} (\gamma_{G,j,inf} \cdot G_{k,j,inf}) + \gamma_{P} \cdot P + \gamma_{Q} \cdot Q_{k,1} + \sum_{i>1} (\gamma_{Q} \cdot \psi_{0,i} \cdot Q_{k,i})"
    )

    # 3. Legenda
    st.markdown(
        rf"""
        ### gdzie:
        * $E_d$ - Obliczeniowa wartość efektu obciążeń ($\max(E_{{d,(6.10a)}}), E_{{d,(6.10b)}})$).
        * $G_{{k,j}}$ - Charakterystyczna wartość obciążenia stałego j.
        * $\gamma_{{G,sup}} = {GAMMA_G_SUP:.2f}$ - Współczynnik dla $G_k$ niekorzystnych.
        * $\gamma_{{G,inf}} = {GAMMA_G_INF:.2f}$ - Współczynnik dla $G_k$ korzystnych.
        * $\xi = {XI_RECOM:.2f}$ - Współczynnik redukcyjny dla $\gamma_{{G,sup}}$ w kombinacji 6.10b.
        * $\gamma_{{Q,sup}} = {GAMMA_Q_SUP_VAL:.2f}$ - Współczynnik dla $Q_k$ **niekorzystnych**.
        * $\gamma_{{Q,inf}} = {GAMMA_Q_INF_VAL:.2f}$ - Współczynnik dla $Q_k$ **korzystnych**.
        * $Q_{{k,1}}, Q_{{k,i}}$ - Obciążenia zmienne (wiodące i towarzyszące).
        * $\psi_{{0,i}}$ - Współczynnik kombinacyjny obciążenia zmiennego i.
        * $P$ - Obciążenie sprężające.
        * $\gamma_{{P}} = {GAMMA_P:.2f}$ - Współczynnik częściowy dla oddziaływań sprężających (wartość zalecana).
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # 4. TABELA PSI — SGN (ψ₀)
    st.markdown("### Tabela współczynników ψ₀ (PN-EN 1990 Tabela A1.1)")

    # Wywołanie generatora HTML dla tabeli SGN
    st.markdown(generate_sgn_html_table(PSI_TABLE_RAW_SGN, UI_CATEGORIES_SGN), unsafe_allow_html=True)


# =============================================================================
# CZĘŚĆ 2 – SGU (kopiuj-wklej z KombinacjeObciazenSGU.py)
# =============================================================================

# --- STAŁE NORMOWE SGU ---
GAMMA_G_SGU = 1.00
GAMMA_P_SGU = 1.00
GAMMA_Q_SGU = 1.00

# PN-EN 1990 — tylko ψ1 i ψ2 dla SGU
PSI_TABLE_RAW_SGU: Dict[str, Tuple[float, float]] = {
    "A: Mieszkalne":             (0.5, 0.3),
    "B: Biurowe":                (0.5, 0.3),
    "C: Zebrań":                 (0.7, 0.6),
    "D: Handlowe":               (0.7, 0.6),
    "E: Magazynowe":             (0.9, 0.8),
    "F: Ruch Pojazdow lekki":    (0.7, 0.6),
    "G: Ruch Pojazdow ciezki":   (0.5, 0.3),
    "H: Dachy (inne niz snieg)": (0.0, 0.0),
    "Snieg (H <= 1000m)":        (0.2, 0.0),
    "Snieg (H > 1000m)":         (0.5, 0.2),
    "Wiatr":                     (0.2, 0.0),
    "Temperatura":               (0.5, 0.0),
}

UI_CATEGORIES_SGU: Dict[str, str] = {
    "A: Mieszkalne": "KATEGORIA A:\npowierzchnie mieszkalne",
    "B: Biurowe": "KATEGORIA B:\npowierzchnie biurowe",
    "C: Zebrań": "KATEGORIA C:\nmiejsca zebrań",
    "D: Handlowe": "KATEGORIA D:\npowierzchnie handlowe",
    "E: Magazynowe": "KATEGORIA E:\npowierzchnie magazynowe",
    "F: Ruch Pojazdow lekki": "KATEGORIA F:\nruchu pojazdów ≤30kN",
    "G: Ruch Pojazdow ciezki": "KATEGORIA G:\nruch pojazdów 30kN < P ≤160kN",
    "H: Dachy (inne niz snieg)": "KATEGORIA H:\ndachy",
    "Snieg (H <= 1000m)": "OBCIĄŻENIE ŚNIEGIEM\nw miejscowościach H ≤ 1000 m n.p.m.",
    "Snieg (H > 1000m)": "OBCIĄŻENIE ŚNIEGIEM\nw miejscowościach H > 1000 m n.p.m.",
    "Wiatr": "OBCIĄŻENIE WIATREM",
    "Temperatura": "OBCIĄŻENIE TEMPERATURĄ",
}


def StronaKombinacjeSGU():
    # --- TYTUŁ W SEKCJACH USUNIĘTY NA RZECZ TYTUŁU GŁÓWNEGO ---
    st.markdown("### Stan Graniczny Użytkowalności (SGU)")

    # OPIS
    st.markdown(
        r"""
    Stan graniczny użytkowalności dotyczy takich efektów jak ugięcia, drgania oraz zarysowanie.
    """
    )

    st.markdown("---")

    # ============================================================
    # KOMBINACJE
    # ============================================================

    st.markdown("### Kombinacje Obciążeń Stanów Granicznych Użytkowalności (SGU)")

    st.markdown(
        r"Weryfikacja SGU wymaga analizy obciążeń w **trzech kombinacjach**, "
        r"określających stopień redukcji obciążeń zmiennych ($Q_{k,i}$) "
        r"przy pomocy współczynników $\psi$."
    )

    # --- Charakterystyczna ---
    st.markdown("#### Kombinacja Charakterystyczna")
    st.latex(r"E_d = \sum G_k + P + Q_{k,1} + \sum \psi_{0,i} Q_{k,i}")

    st.markdown(
        "**Definicja normowa:** Stosowana zwykle dla **nieodwracalnych stanów granicznych**, "
        "w których pewne konsekwencje oddziaływań pozostają po ich ustąpieniu."
        "  \n\n"
        "**Zastosowanie praktyczne:** Sprawdzenie granicznych naprężeń, trwałych odkształceń lub ugieć."
    )

    # --- Częsta ---
    st.markdown("#### Kombinacja Częsta")
    st.latex(r"E_d = \sum G_k + P + \psi_{1,1}Q_{k,1} + \sum \psi_{2,i}Q_{k,i}")

    st.markdown(
        "**Definicja normowa:** Stosowana zwykle dla **odwracalnych stanów granicznych**, "
        "w których nie pozostają żadne trwałe konsekwencje oddziaływań po ich ustąpieniu."
        "  \n\n"
        "**Zastosowanie praktyczne:** Drgania konstrukcji oraz inne aspekty wpływające na komfort uzytkowania"
    )

    # --- Quasi-stała ---
    st.markdown("#### Kombinacja Quasi-stała")
    st.latex(r"E_d = \sum G_k + P + \sum \psi_{2,i}Q_{k,i}")

    st.markdown(
        "**Definicja normowa:** Stosowana zwykle dla oceny **efektów długotrwałych** "
        "(np. pełzanie) oraz **wyglądu konstrukcji**."
        "  \n\n"
        "**Zastosowanie praktyczne:** Ugięcia końcowe oraz zarysowania konstrukcji żelbetowych, pełzanie betonu."
    )

    st.markdown("---")

    # ============================================================
    # TABELA PSI — SGU (ψ1 i ψ2)
    # ============================================================

    st.markdown("### Tabela współczynników ψ₁ oraz ψ₂ (PN-EN 1990)")

    # Wywołanie generatora HTML dla tabeli SGU
    st.markdown(generate_sgu_html_table(PSI_TABLE_RAW_SGU, UI_CATEGORIES_SGU), unsafe_allow_html=True)


# =============================================================================
# CZĘŚĆ 3 – WSPÓLNA FUNKCJA DLA APLIKACJI
# =============================================================================

def StronaKombinacjeObciazen():
    """
    Główna strona: zakładki SGN / SGU.
    Środek kalkulatorów jest identyczny jak w oryginalnych plikach.
    """
    # STYLISTYKA I TYTUŁ GŁÓWNY (NAD ZAKŁADKAMI)
    st.markdown(
        """
        <style>
        .block-container { padding-top: 1.5rem; padding-bottom: 1.5rem; }
        h3 { margin-top: 1rem !important; margin-bottom: 0.5rem !important; font-size: 1.2rem; }
        div[data-testid="stForm"] > div { margin-bottom: 0 !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # TYTUŁ GŁÓWNY
    st.markdown(
        r"""
        <div style="text-align:center; margin-top:0.4rem; margin-bottom:0rem;">
            <span style="font-size:42px; font-weight:800; letter-spacing:1px; color:#dddddd;">
                KOMBINACJE OBCIĄŻEŃ
            </span>
        </div>
        <div style="text-align:center; font-size:14px; color:#aaaaaa; margin-top:-12px; margin-bottom:1.5rem;">
            wg PN-EN 1990:2002 (Załącznik A1)
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ZAKŁADKI (TERAZ POD TYTUŁEM)
    tab_sgn, tab_sgu = st.tabs(
        ["STAN GRANICZNY NOŚNOŚCI (SGN)", "STAN GRANICZNY UŻYTKOWALNOŚCI (SGU)"]
    )

    with tab_sgn:
        StronaKombinacjeSGN()

    with tab_sgu:
        StronaKombinacjeSGU()