import streamlit as st
import os
import importlib.util

def load_and_run_module(filename):
    """
    Pomocnicza funkcja do dynamicznego ładowania i uruchamiania modułu z pliku.
    Zakłada, że plik znajduje się w tym samym katalogu co plik główny.
    """
    # Ścieżka do katalogu, w którym znajduje się bieżący plik
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, filename)

    # Sprawdzenie czy plik istnieje
    if not os.path.exists(file_path):
        st.info(f"Moduł '{filename}' nie został jeszcze utworzony.")
        return

    try:
        # Dynamiczne ładowanie modułu
        spec = importlib.util.spec_from_file_location("dynamic_module", file_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Opcja A: Jeśli moduł ma funkcję 'run()', uruchom ją.
            if hasattr(module, "run"):
                module.run()
            # Opcja B: Jeśli moduł to po prostu skrypt (top-level code), 
            # samo exec_module powyżej już go wykonało.
            
    except Exception as e:
        # Obsługa błędów (np. pusty plik, błąd składni w podmodule)
        st.warning(f"🚧 Moduł w trakcie wdrażania lub wystąpił błąd: {e}")

def StronaObciazeniaSniegiem():
    """
    Główna funkcja widoku Obciążenia Śniegiem.
    Tworzy zakładki i ładuje odpowiednie podmoduły.
    """
    
    # --- NAGŁÓWEK STYLI ---
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

    # 1. TYTUŁ GŁÓWNY (NA GÓRZE STRONY)
    st.markdown(
        """
        <div style="text-align:center; margin-top:0.4rem; margin-bottom:0rem;">
            <span style="font-size:42px; font-weight:800; letter-spacing:1px; color:#dddddd;">
                OBCIĄŻENIE ŚNIEGIEM
            </span>
        </div>
        <div style="text-align:center; font-size:14px; color:#aaaaaa; margin-top:-12px; margin-bottom:1.5rem;">
            wg PN-EN 1991-1-3
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Lista nazw zakładek (Zaktualizowane nazwy)
    tab_names = [
        "Dach jednopołaciowy",
        "Dach dwupołaciowy",
        "Dach wielopołaciowy",
        "Dach walcowy",
        "Dach przylegający do wyższego budynku",
        "Zaspy przy przeszkodach",
        "Nawisy śnieżne",
        "Bariery przeciwśnieżne"
    ]

    # Tworzenie kontenera zakładek
    tabs = st.tabs(tab_names)

    # 1. Dach jednopołaciowy
    with tabs[0]:
        load_and_run_module("ObciazeniaSniegiem_DachJednopolaciowy.py")

    # 2. Dach dwupołaciowy
    with tabs[1]:
        load_and_run_module("ObciazeniaSniegiem_DachDwupolaciowy.py")

    # 3. Dach wielopołaciowy
    with tabs[2]:
        load_and_run_module("ObciazeniaSniegiem_DachWielopolaciowe.py")

    # 4. Dach walcowy
    with tabs[3]:
        load_and_run_module("ObciazeniaSniegiem_DachWalcowe.py")

    # 5. Dach przylegający do wyższego budynku
    with tabs[4]:
        load_and_run_module("ObciazeniaSniegiem_DachPrzylegajacy.py")

    # 6. Zaspy przy przeszkodach
    with tabs[5]:
        load_and_run_module("ObciazeniaSniegiem_Przeszkody.py")

    # 7. Nawisy śnieżne
    with tabs[6]:
        load_and_run_module("ObciazeniaSniegiem_Nawisy.py")

    # 8. Bariery przeciwśnieżne
    with tabs[7]:
        load_and_run_module("ObciazeniaSniegiem_DachBarieryPrzeciwsniezne.py")

# Ten blok pozwala uruchomić plik samodzielnie w celach testowych
if __name__ == "__main__":
    st.set_page_config(page_title="Obciążenie śniegiem", layout="wide")
    StronaObciazeniaSniegiem()