import sys
import os
import streamlit as st
from pathlib import Path
import importlib.util

# --- FUNKCJA WYSZUKUJĄCA ŚCIEŻKĘ GŁÓWNĄ ---
def get_base_path_safe():
    """Wyszukuje katalog 'KALKULATORY' niezależnie od głębokości zagnieżdżenia."""
    current_path = Path(os.path.abspath(__file__))
    for parent in current_path.parents:
        if parent.name.upper() == "KALKULATORY":
            return str(parent)
    return str(current_path.parent)

# --- 1. KONFIGURACJA STRONY ---
st.set_page_config(
    page_title="PLATFORMA OBLICZEŃ INŻYNIERSKICH – Bartłomiej Konopka",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- 2. STYLE CSS ---
st.markdown(
    """
<style>
/* --- OGÓLNE USTAWIENIA --- */
.block-container {
    padding-top: 1rem !important;
    padding-bottom: 2rem !important;
}

/* --- SIDEBAR - STRUKTURA I KOLORY --- */
section[data-testid="stSidebar"] {
    background-color: #0e1117; /* Ciemne tło */
    border-right: 1px solid #262730;
    min-width: 350px !important; /* ZMIANA SZEROKOŚCI NA 350px */
    max-width: 350px !important; /* ZMIANA SZEROKOŚCI NA 350px */
}

/* UKRYCIE UCHWYTU DO ZMIANY ROZMIARU SIDEBARA */
div[data-testid="stSidebar"] + div {
    display: none;
}

/* Wymuszenie układu flex w sidebarze, aby stopka była na dole */
section[data-testid="stSidebar"] > div {
    display: flex;
    flex-direction: column;
    height: 100%;
    justify-content: space-between;
}

/* Kontener na treść nawigacji (żeby nie rozciągał się na całą wysokość, zostawiając miejsce stopce) */
.nav-content {
    flex-grow: 1;
    overflow-y: auto; /* przewijanie środka nawigacji */
}

/* GŁÓWNY POZIOM 1 – PRZYKLEJONY NA GÓRZE SIDEBARA */
.nav-top-level {
    /* Usunięto sticky, aby sekcje przewijały się naturalnie, skoro są dwie */
    background-color: #0e1117; 
}

/* --- STYLIZACJA RADIO BUTTONÓW JAKO MENU (KAFELKI) --- */
/* Ukrycie standardowych kółek radio */
.stRadio div[role="radiogroup"] > label > div:first-child {
    display: none !important;
}

/* Kontener radia na pełną szerokość */
.stRadio div[role="radiogroup"] {
    width: 100%;
}

/* Stylizacja etykiety (całego przycisku menu) */
.stRadio div[role="radiogroup"] > label {
    display: block;
    background-color: transparent;
    border: 1px solid transparent;
    border-left: 4px solid transparent;  /* stała szerokość paska z lewej */
    padding: 8px 12px;
    margin: 2px -6px;  /* tło na pełną szerokość do krawędzi sidebara */
    border-radius: 6px;
    box-sizing: border-box;
    transition: background-color 0.2s, color 0.2s, border-left-color 0.2s;
    cursor: pointer;
    font-size: 0.9rem;
    color: #a0a0a0; /* Domyślny kolor tekstu */
}

/* Efekt Hover (najechanie myszką) */
.stRadio div[role="radiogroup"] > label:hover {
    background-color: #1c1e26;
    color: #ffffff;
}

/* STYL DLA AKTYWNEGO ELEMENTU (wybranego) */
.stRadio div[role="radiogroup"] > label:has(input:checked) {
    background-color: #1f2937;       /* Ciemnoniebieskie tło */
    border-left-color: #3b82f6;      /* tylko kolor, szerokość stała */
    color: #ffffff !important;
    font-weight: 600;
}

/* --- NAGŁÓWKI W SIDEBARZE (PODTYTUŁY POZIOMU 2) --- */
.sidebar-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 1.05rem;        /* większa czcionka */
    font-weight: 800;          /* mocny nagłówek */
    color: #e5e7eb;            /* jasny tekst */
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-top: 1.8rem;
    margin-bottom: 0.7rem;
    padding-left: 2px;
    border-bottom: 1px solid #3a3f47;
    padding-bottom: 6px;
}

.sidebar-header-icon {
    font-size: 1.1rem;
}

/* --- NAGŁÓWKI SEKCJI GŁÓWNYCH (PN-EN / IBC) --- */
.main-section-header {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    color: #e5e7eb;
    font-weight: 700;
    font-size: 0.95rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    padding: 0.75rem 0.25rem 0.2rem 0.25rem;
    margin-top: 10px;
}

/* --- STOPKA SIDEBARA --- */
.sidebar-footer-container {
    margin-top: auto;
    padding-top: 25px;
    border-top: 1px solid #262730;
}

.platform-info {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 15px;
    text-align: center;
    margin-bottom: 15px;
}

.platform-title {
    font-size: 1.1rem;
    font-weight: 800;
    color: #e6edf3;
    letter-spacing: 0.5px;
    margin-bottom: 6px;
    line-height: 1.3;
}

.platform-author {
    font-size: 0.9rem;
    color: #8b949e;
    font-weight: 500;
}

/* Stylizacja przycisku Wyloguj */
.logout-btn-container button {
    background-color: #1d4ed8 !important;
    color: white !important;
    border: none !important;
    font-weight: 700 !important;
    border-radius: 6px !important;
    transition: background-color 0.2s !important;
    height: 45px !important;
    font-size: 1rem !important;
}

.logout-btn-container button:hover {
    background-color: #2563eb !important;
}

/* --- STYLIZACJA ELEMENTÓW FORMULARZA GŁÓWNEGO --- */
.stNumberInput input {
    font-weight: 500;
}
</style>
""",
    unsafe_allow_html=True,
)

# --- 3. USTAWIANIE ŚCIEŻEK ---
KATALOG_GLOWNY = os.path.dirname(os.path.abspath(__file__))

# Standardowe moduły w _MODULY
sciezka_moduly = os.path.join(KATALOG_GLOWNY, "_MODULY")

# Ścieżki do konkretnych folderów z modułami - ZAKTUALIZOWANE NAZWY (BEZ SPACJI)
sciezka_zaklad       = os.path.join(sciezka_moduly, "EC2_PodstawoweDane_DlugoscZakladu")
sciezka_zakotwienie  = os.path.join(sciezka_moduly, "EC2_PodstawoweDane_DlugoscZakotwienia")
sciezka_otulina      = os.path.join(sciezka_moduly, "EC2_PodstawoweDane_OtulinaZbrojenia")
sciezka_beton        = os.path.join(sciezka_moduly, "EC2_PodstawoweDane_ParametryBetonu")
sciezka_stal         = os.path.join(sciezka_moduly, "EC2_PodstawoweDane_ParametryStali")
sciezka_powierzchnia = os.path.join(sciezka_moduly, "EC2_PodstawoweDane_PowierzchniaPretowZbrojeniowych")

# Ścieżki - ZBROJENIE MINIMALNE
sciezka_min_plyty    = os.path.join(sciezka_moduly, "EC2_ZbrojenieMinimalne_Plyty")
sciezka_min_belki    = os.path.join(sciezka_moduly, "EC2_ZbrojenieMinimalne_Belki")
sciezka_min_slupy    = os.path.join(sciezka_moduly, "EC2_ZbrojenieMinimalne_Slupy")  
sciezka_min_sciany   = os.path.join(sciezka_moduly, "EC2_ZbrojenieMinimalne_Sciany")

# Ścieżki - WYMIAROWANIE
sciezka_dim_scinanie           	= os.path.join(sciezka_moduly, "EC2_Wymiarowanie_Scinanie")
sciezka_dim_zginanie           	= os.path.join(sciezka_moduly, "EC2_Wymiarowanie_Zginanie")
sciezka_dim_sciskanie_zginanie 	= os.path.join(sciezka_moduly, "EC2_Wymiarowanie_SciskanieZeZginaniem")
sciezka_dim_przebicie		= os.path.join(sciezka_moduly, "EC2_Wymiarowanie_Przebicie")


# Ścieżki - OBCIĄŻENIA
sciezka_obc_komb_folder     = os.path.join(sciezka_moduly, "OBCIAZENIA_KombinacjeObciazen")
sciezka_obc_uzytkowe_folder = os.path.join(sciezka_moduly, "OBCIAZENIA_ObciazeniaUzytkowe")
sciezka_obc_snieg_folder    = os.path.join(sciezka_moduly, "OBCIAZENIA_ObciazeniaSniegiem")
sciezka_obc_wiatr_folder    = os.path.join(sciezka_moduly, "OBCIAZENIA_ObciazeniaWiatrem")
sciezka_obc_grunt_folder    = os.path.join(sciezka_moduly, "OBCIAZENIA_ObciazeniaGruntem")


# --- FUNKCJA ŁADUJĄCA MODUŁ Z PODANEJ ŚCIEŻKI ---
def load_module_from_path(module_name: str, file_path: str):
    """Dynamiczne ładowanie modułu z podanej ścieżki."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None:
        raise ImportError(f"Nie można utworzyć specyfikacji dla modułu: {module_name}")
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise ImportError(f"Brak loadera dla modułu: {module_name}")
    spec.loader.exec_module(module)
    return module

# --- 4. IMPORTY MODUŁÓW ISTNIEJĄCYCH (lokalne PROGRAMY) ---
try:
    from DlugoscZakladu import StronaDlugoscZakladu
    from DlugoscZakotwienia import StronaDlugoscZakotwienia
    from OtulinaZbrojenia import StronaOtulinaZbrojenia
    from ParametryBetonuStrona import StronaParametryBetonu
    from ParametryStaliStrona import StronaParametryStali
except ImportError:
    pass

# --- 5. EKRAN LOGOWANIA ---
if "zalogowany" not in st.session_state:
    st.session_state["zalogowany"] = False

if not st.session_state["zalogowany"]:
    st.markdown(
        """
        <div style="text-align:center; margin-top:2rem; margin-bottom:0rem;">
            <span style="font-size:42px; font-weight:800; letter-spacing:1px; color:#dddddd;">
                PLATFORMA OBLICZEŃ INŻYNIERSKICH
            </span>
        </div>
        <div style="text-align:center; font-size:14px; color:#aaaaaa; margin-top:-5px; margin-bottom:0.6rem;">
            made by Bartłomiej Konopka
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        login_input = st.text_input("Login")
        haslo_input = st.text_input("Hasło", type="password")

        if st.button("Zaloguj się", type="primary", use_container_width=True):
            # POPRAWKA: Dodano obsługę drugiego użytkownika b3k
            if (login_input == "BARTEK" and haslo_input == "12345") or (login_input == "b3k" and haslo_input == "biurob3k"):
                st.session_state["zalogowany"] = True
                st.rerun()
            else:
                st.error("Błędny login lub hasło!")
    st.stop()

# --- 6. CALLBACKI I STANY SESJI (OBSŁUGA MENU) ---

if "pnen_selection" not in st.session_state:
    st.session_state["pnen_selection"] = "1. OBCIĄŻENIA I KOMBINACJE" # Domyślna opcja

# Callbacki do podmenu
def clear_ec0_obc():
    st.session_state["ec0_obc_key"] = None

def clear_ec0_komb():
    st.session_state["ec0_komb_key"] = None

def clear_ec2_others_for_basic():
    st.session_state["ec2_dim_key"] = None
    st.session_state["ec2_min_key"] = None

def clear_ec2_others_for_dim():
    st.session_state["ec2_base_key"] = None
    st.session_state["ec2_min_key"] = None

def clear_ec2_others_for_min():
    st.session_state["ec2_base_key"] = None
    st.session_state["ec2_dim_key"] = None

# Inicjalizacja kluczy stanu podmenu, jeśli nie istnieją
if "ec0_all_key" not in st.session_state:
    st.session_state["ec0_all_key"] = "Kombinacje obciążeń (SGN / SGU)"

if "ec2_base_key" not in st.session_state:
    st.session_state["ec2_base_key"] = "Parametry betonu"
if "ec2_dim_key" not in st.session_state:
    st.session_state["ec2_dim_key"] = None
if "ec2_min_key" not in st.session_state:
    st.session_state["ec2_min_key"] = None

if "ec3_key" not in st.session_state:
    st.session_state["ec3_key"] = "Elementy stalowe - ogólne"
if "ec5_key" not in st.session_state:
    st.session_state["ec5_key"] = "Elementy drewniane - ogólne"

wybrane_narzedzie = None
dzial = None

# --- 7. PANEL BOCZNY (NAWIGACJA) ---
with st.sidebar:
    
    # 7.1. SEKCJA GŁÓWNA NAWIGACJI (GÓRA)
    st.markdown("<div class='nav-content'>", unsafe_allow_html=True)
    # ----------------------------------------------------
    # SEKCJA 1: DZIAŁY PROJEKTOWE WG PN-EN
    # ----------------------------------------------------
    st.markdown(
        """
        <div class="main-section-header">
            <span style="font-size:1.1rem;">📂</span>
            <span>DZIAŁY PROJEKTOWE WG PN-EN</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Określenie indeksu dla radia PN-EN
    pnen_opts = [
        "1. OBCIĄŻENIA I KOMBINACJE",
        "2. KONSTRUKCJE ŻELBETOWE",
        "3. KONSTRUKCJE STALOWE",
        "4. KONSTRUKCJE DREWNIANE"
    ]
    
    curr = st.session_state["pnen_selection"]
    if curr in pnen_opts:
        pnen_index = pnen_opts.index(curr)
    else:
        pnen_index = 0

    val_pnen = st.radio(
        "nav_pnen_hidden",
        options=pnen_opts,
        index=pnen_index,
        key="pnen_selection",
        label_visibility="collapsed"
    )

    st.markdown("---", unsafe_allow_html=True)
    
    # Ustalenie aktywnego działu
    dzial = val_pnen

    # 7.2. PODMENU DLA WYBRANEGO DZIAŁU
    
    # --- DZIAŁ 1: OBCIĄŻENIA (PN-EN) ---
    if dzial == "1. OBCIĄŻENIA I KOMBINACJE":
        st.markdown(
            """
            <div class="sidebar-header">
                <span class="sidebar-header-icon">⚖️</span>
                <span>OBCIĄŻENIA / KOMBINACJE</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        sel_all = st.radio(
            "ec0_nav",
            options=[
                "Kombinacje obciążeń (SGN / SGU)",
                "Obciążenia użytkowe",
                "Obciążenia śniegiem",
                "Obciążenia wiatrem",
                "Obciążenia parciem gruntu ścian",
            ],
            key="ec0_all_key",
            label_visibility="collapsed"
        )
        wybrane_narzedzie = sel_all

    # --- DZIAŁ 2: ŻELBET (PN-EN) ---
    elif dzial == "2. KONSTRUKCJE ŻELBETOWE":
        # 1) PODSTAWOWE DANE
        st.markdown(
            """
            <div class="sidebar-header">
                <span class="sidebar-header-icon">🧱</span>
                <span>PODSTAWOWE DANE</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        sel_base = st.radio(
            "ec2_base_nav",
            options=[
                "Parametry betonu",
                "Parametry stali",
                "Otulina zbrojenia",
                "Długość zakotwienia",
                "Długość zakładu",
                "Powierzchnia zbrojenia"
            ],
            key="ec2_base_key",
            on_change=clear_ec2_others_for_basic,
            label_visibility="collapsed",
            index=0
        )

        # 2) ZBROJENIE MINIMALNE / MAKSYMALNE
        st.markdown(
            """
            <div class="sidebar-header">
                <span class="sidebar-header-icon">➕</span>
                <span>ZBROJENIE MIN / MAX</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        sel_min = st.radio(
            "ec2_min_nav",
            options=["Płyty żelbetowe", "Belki żelbetowe", "Słupy żelbetowe", "Ściany żelbetowe"],
            key="ec2_min_key",
            on_change=clear_ec2_others_for_min,
            label_visibility="collapsed",
            index=None
        )

        # 3) WYMIAROWANIE ZBROJENIA
        st.markdown(
            """
            <div class="sidebar-header">
                <span class="sidebar-header-icon">📐</span>
                <span>WYMIAROWANIE ZBROJENIA</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        sel_dim = st.radio(
            "ec2_dim_nav",
            options=["Zginanie jednokierunkowe", "Ściskanie ze zginaniem", "Ścinanie", "Przebicie płyty"],
            key="ec2_dim_key",
            on_change=clear_ec2_others_for_dim,
            label_visibility="collapsed",
            index=None
        )

        # Priorytet: PODSTAWOWE DANE → ZBROJENIE MINIMALNE → WYMIAROWANIE ZBROJENIA
        if sel_base:
            wybrane_narzedzie = sel_base
        elif sel_min:
            wybrane_narzedzie = sel_min
        elif sel_dim:
            wybrane_narzedzie = sel_dim

    # --- DZIAŁ 3: STAL (PN-EN) ---
    elif dzial == "3. KONSTRUKCJE STALOWE":
        st.markdown(
            """
            <div class="sidebar-header">
                <span class="sidebar-header-icon">🧲</span>
                <span>KONSTRUKCJE STALOWE</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        sel_ec3 = st.radio(
            "ec3_nav",
            options=["Elementy stalowe - ogólne"],
            key="ec3_key",
            label_visibility="collapsed",
            index=0
        )
        wybrane_narzedzie = sel_ec3

    # --- DZIAŁ 4: DREWNO (PN-EN) ---
    elif dzial == "4. KONSTRUKCJE DREWNIANE":
        st.markdown(
            """
            <div class="sidebar-header">
                <span class="sidebar-header-icon">🌲</span>
                <span>KONSTRUKCJE DREWNIANE</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        sel_ec5 = st.radio(
            "ec5_nav",
            options=["Elementy drewniane - ogólne"],
            key="ec5_key",
            label_visibility="collapsed",
            index=0
        )
        wybrane_narzedzie = sel_ec5

    st.markdown("</div>", unsafe_allow_html=True)  # Koniec kontenera nav-content

    # 7.3. STOPKA (NA SAMYM DOLE)
    st.markdown("<div class='sidebar-footer-container'>", unsafe_allow_html=True)
    
    st.markdown(
        """
        <div class="platform-info">
            <div class="platform-title">PLATFORMA OBLICZEŃ INŻYNIERSKICH</div>
            <div class="platform-author">made by Bartłomiej Konopka</div>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    st.markdown("<div class='logout-btn-container'>", unsafe_allow_html=True)
    if st.button("WYLOGUJ SIĘ", key="logout_main", use_container_width=True, type="primary"):
        st.session_state["zalogowany"] = False
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)  # Koniec stopki

# --- 8. FUNKCJA „W OPRACOWANIU” ---
def show_w_opracowaniu(tytul: str):
    # POPRAWKA: Skopiowano styl nagłówka z kalkulatora długości zakładu
    st.markdown(
        f"""
        <div style="text-align:center; margin-top:0.4rem; margin-bottom:0rem;">
            <span style="font-size:42px; font-weight:800; letter-spacing:1px; color:#dddddd;">
                {tytul.upper()}
            </span>
        </div>
        <div style="text-align:center; font-size:14px; color:#aaaaaa; margin-top:-12px; margin-bottom:0.6rem;">
            wg norm projektowych PN-EN
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div style="
            background-color: #f0f2f6;
            border-left: 5px solid #ffbd45;
            padding: 20px;
            border-radius: 5px;
            margin-top: 20px;
        ">
            <h4 style="color: #31333F; margin-top:0;">🚧 MODUŁ W TRAKCIE BUDOWY</h4>
            <p style="color: #555; margin-bottom:0;">
                Ta funkcjonalność jest obecnie implementowana. Zapraszamy wkrótce.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# --- 9. ROUTING GŁÓWNY (ŁADOWANIE TREŚCI) ---

if wybrane_narzedzie:

    # A. KOMBINACJE (PN-EN 1990)
    if wybrane_narzedzie == "Kombinacje obciążeń (SGN / SGU)":
        try:
            plik_komb = os.path.join(sciezka_obc_komb_folder, "KombinacjeObciazen.py")
            if not os.path.exists(plik_komb):
                st.error("Brak pliku modułu: KombinacjeObciazen.py")
            else:
                mod_komb = load_module_from_path("KombinacjeObciazen", plik_komb)
                if hasattr(mod_komb, "StronaKombinacjeObciazen"):
                    mod_komb.StronaKombinacjeObciazen()
        except Exception as e:
            st.error(f"Błąd ładowania modułu: {e}")

    # B. OBCIĄŻENIA (PN-EN 1991)
    elif wybrane_narzedzie == "Obciążenia użytkowe":
        try:
            plik = os.path.join(sciezka_obc_uzytkowe_folder, "ObciazeniaUzytkowe.py")
            if os.path.exists(plik):
                mod = load_module_from_path("mod_obciazenia_uzytkowe", plik)
                mod.StronaObciazeniaUzytkowe()
            else:
                st.error("Brak pliku modułu.")
        except Exception as e:
            st.error(f"Błąd: {e}")

    elif wybrane_narzedzie == "Obciążenia śniegiem":
        try:
            plik = os.path.join(sciezka_obc_snieg_folder, "ObciazeniaSniegiemApp.py")
            if os.path.exists(plik):
                mod = load_module_from_path("mod_obciazenia_snieg", plik)
                mod.StronaObciazeniaSniegiem()
            else:
                st.error(f"Brak pliku modułu w ścieżce: {plik}")
        except Exception as e:
            st.error(f"Błąd: {e}")

    elif wybrane_narzedzie == "Obciążenia wiatrem":
        try:
            plik = os.path.join(sciezka_obc_wiatr_folder, "ObciazeniaWiatremApp.py")
            if os.path.exists(plik):
                mod = load_module_from_path("mod_obciazenia_wiatr", plik)
                mod.StronaObciazeniaWiatrem()
            else:
                st.error("Brak pliku modułu.")
        except Exception as e:
            st.error(f"Błąd: {e}")

    elif wybrane_narzedzie == "Obciążenia parciem gruntu ścian":
        try:
            plik = os.path.join(sciezka_obc_grunt_folder, "ObciazenieParciemSpoczynkowymGruntu.py")
            if os.path.exists(plik):
                mod = load_module_from_path("mod_obciazenia_grunt", plik)
                mod.run()
            else:
                st.error("Brak pliku modułu.")
        except Exception as e:
            st.error(f"Błąd: {e}")

    # C. ŻELBET – PODSTAWOWE DANE
    elif wybrane_narzedzie == "Parametry betonu":
        plik = os.path.join(sciezka_beton, "ParametryBetonuStrona.py")
        try:
            mod = load_module_from_path("ParametryBetonuStrona", plik)
            mod.StronaParametryBetonu()
        except Exception as e:
            st.error(f"Błąd: {e}")

    elif wybrane_narzedzie == "Parametry stali":
        plik = os.path.join(sciezka_stal, "ParametryStaliStrona.py")
        try:
            mod = load_module_from_path("ParametryStaliStrona", plik)
            mod.StronaParametryStali()
        except Exception as e:
            st.error(f"Błąd: {e}")

    elif wybrane_narzedzie == "Otulina zbrojenia":
        plik = os.path.join(sciezka_otulina, "OtulinaZbrojenia.py")
        try:
            mod = load_module_from_path("OtulinaZbrojenia", plik)
            mod.StronaOtulinaZbrojenia()
        except Exception as e:
            st.error(f"Błąd: {e}")

    elif wybrane_narzedzie == "Długość zakotwienia":
        plik = os.path.join(sciezka_zakotwienie, "DlugoscZakotwienia.py")
        try:
            mod = load_module_from_path("DlugoscZakotwienia", plik)
            mod.StronaDlugoscZakotwienia()
        except Exception as e:
            st.error(f"Błąd: {e}")

    elif wybrane_narzedzie == "Długość zakładu":
        plik = os.path.join(sciezka_zaklad, "DlugoscZakladu.py")
        try:
            mod = load_module_from_path("DlugoscZakladu", plik)
            mod.StronaDlugoscZakladu()
        except Exception as e:
            st.error(f"Błąd: {e}")
            
    elif wybrane_narzedzie == "Powierzchnia zbrojenia":
        plik = os.path.join(sciezka_powierzchnia, "PowierzchniaZbrojenia.py")
        try:
            mod = load_module_from_path("PowierzchniaZbrojenia", plik)
            mod.StronaPowierzchniaZbrojenia()
        except Exception as e:
            st.error(f"Błąd: {e}")
            
    # C.2 ŻELBET - ZBROJENIE MINIMALNE / MAKSYMALNE
    elif wybrane_narzedzie == "Płyty żelbetowe":
        try:
            plik = os.path.join(sciezka_min_plyty, "ZbrojenieMinimalnePlyty.py")
            if os.path.exists(plik):
                mod = load_module_from_path("ZbrojenieMinimalnePlyty", plik)
                if hasattr(mod, "StronaZbrojenieMinimalnePlyty"):
                    mod.StronaZbrojenieMinimalnePlyty()
                else:
                    st.error("Moduł nie posiada funkcji StronaZbrojenieMinimalnePlyty.")
            else:
                st.error(f"Brak pliku modułu: {plik}")
        except Exception as e:
            st.error(f"Błąd: {e}")

    elif wybrane_narzedzie == "Belki żelbetowe":
        try:
            plik = os.path.join(sciezka_min_belki, "ZbrojenieMinimalneBelki.py")
            if os.path.exists(plik):
                mod = load_module_from_path("ZbrojenieMinimalneBelki", plik)
                if hasattr(mod, "StronaZbrojenieMinimalneBelki"):
                    mod.StronaZbrojenieMinimalneBelki()
                else:
                    st.error("Moduł nie posiada funkcji StronaZbrojenieMinimalneBelki.")
            else:
                st.error(f"Brak pliku modułu: {plik}")
        except Exception as e:
            st.error(f"Błąd: {e}")

    elif wybrane_narzedzie == "Słupy żelbetowe":
        try:
            plik = os.path.join(sciezka_min_slupy, "ZbrojenieMinimalneSlupy.py")
            if os.path.exists(plik):
                mod = load_module_from_path("ZbrojenieMinimalneSlupy", plik)
                if hasattr(mod, "StronaZbrojenieMinimalneSlupy"):
                    mod.StronaZbrojenieMinimalneSlupy()
                else:
                    st.error("Moduł nie posiada funkcji StronaZbrojenieMinimalneSlupy.")
            else:
                st.error(f"Brak pliku modułu: {plik}")
        except Exception as e:
            st.error(f"Błąd: {e}")

    elif wybrane_narzedzie == "Ściany żelbetowe":
        try:
            plik = os.path.join(sciezka_min_sciany, "ZbrojenieMinimalneSciany.py")
            if os.path.exists(plik):
                mod = load_module_from_path("ZbrojenieMinimalneSciany", plik)
                if hasattr(mod, "StronaZbrojenieMinimalneSciany"):
                    mod.StronaZbrojenieMinimalneSciany()
                else:
                    st.error("Moduł nie posiada funkcji StronaZbrojenieMinimalneSciany.")
            else:
                st.error(f"Brak pliku modułu: {plik}")
        except Exception as e:
            st.error(f"Błąd: {e}")

    # C.3 ŻELBET - WYMIAROWANIE
    elif wybrane_narzedzie == "Ścinanie":
        try:
            plik = os.path.join(sciezka_dim_scinanie, "WymiarowanieBelkiScinanie.py")
            if os.path.exists(plik):
                mod = load_module_from_path("WymiarowanieBelkiScinanie", plik)
                if hasattr(mod, "run"):
                    mod.run()
                else:
                    st.error("Moduł nie posiada funkcji run().")
            else:
                st.error(f"Brak pliku modułu: {plik}")
        except Exception as e:
            st.error(f"Błąd: {e}")

    elif wybrane_narzedzie == "Zginanie jednokierunkowe":
        try:
            plik = os.path.join(sciezka_dim_zginanie, "WymiarowanieZginanieApp.py")
            if os.path.exists(plik):
                mod = load_module_from_path("WymiarowanieZginanieApp", plik)
                if hasattr(mod, "run"):
                    mod.run()
                else:
                    st.error("Moduł nie posiada funkcji run().")
            else:
                st.error(f"Brak pliku modułu: {plik}")
        except Exception as e:
            st.error(f"Błąd: {e}")

    elif wybrane_narzedzie == "Ściskanie ze zginaniem":
        try:
            plik = os.path.join(sciezka_dim_sciskanie_zginanie, "WymiarowanieSciskanieZeZginaniemApp.py")
            if os.path.exists(plik):
                mod = load_module_from_path("WymiarowanieSciskanieZeZginaniemApp", plik)
                if hasattr(mod, "run"):
                    mod.run()
                else:
                    st.error("Moduł nie posiada funkcji run().")
            else:
                st.error(f"Brak pliku modułu: {plik}")
        except Exception as e:
            st.error(f"Błąd: {e}")

    elif wybrane_narzedzie == "Przebicie płyty":
        try:
            plik = os.path.join(sciezka_dim_przebicie, "WymiarowaniePrzebiciaPlytyApp.py")
            if os.path.exists(plik):
                mod = load_module_from_path("WymiarowaniePrzebiciaPlytyApp.py", plik)
                if hasattr(mod, "run"):
                    mod.run()
                else:
                    st.error("Moduł nie posiada funkcji run().")
            else:
                st.error(f"Brak pliku modułu: {plik}")
        except Exception as e:
            st.error(f"Błąd: {e}")

    # E. POZOSTAŁE (PLACEHOLDERY)
    elif wybrane_narzedzie in ["Elementy stalowe - ogólne", "Elementy drewniane - ogólne"]:
        show_w_opracowaniu(wybrane_narzedzie) 
    else:
        st.info("Wybierz moduł z menu po lewej stronie.")

else:
    st.markdown(
        """
        <div style="text-align:center; margin-top:50px;">
            <h3>Wybierz dział projektowy i narzędzie z menu po lewej stronie.</h3>
        </div>
        """,
        unsafe_allow_html=True
    )