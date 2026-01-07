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

def StronaObciazeniaWiatrem():
    """
    Główna funkcja widoku Obciążenia Wiatrem.
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
                OBCIĄŻENIE WIATREM
            </span>
        </div>
        <div style="text-align:center; font-size:14px; color:#aaaaaa; margin-top:-12px; margin-bottom:1.5rem;">
            wg PN-EN 1991-1-4
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # Lista nazw zakładek
    tab_names = [
        "Ściany pionowe",
        "Ściany wolnostojące i attyki",
        "Dachy płaskie",
        "Dachy jednospadowe",
        "Dachy dwuspadowe",
        "Dachy czterospadowe",
        "Dachy łukowe",
        "Kopuły",
        "Wiaty jednospadowe",
        "Wiaty dwuspadowe",
        "Wiaty wielospadowe",     
        "Tablice wolnostojące",
        "Flagi"
    ]

    # Tworzenie kontenera zakładek
    tabs = st.tabs(tab_names)

    # 1. Ściany pionowe budynków na rzucie prostokąta
    with tabs[0]:
        load_and_run_module("ObciazeniaWiatrem_ScianyPionowe.py")

    # 2. Ściany wolnostojące i attyki
    with tabs[1]:
        load_and_run_module("ObciazeniaWiatrem_ScianyWolnostojace.py")

    # 3. Dachy płaskie
    with tabs[2]:
        load_and_run_module("ObciazeniaWiatrem_DachyPlaskie.py")

    # 34 Dachy jednospadowe
    with tabs[3]:
        load_and_run_module("ObciazeniaWiatrem_DachyJednospadowe.py")

    # 5. Dachy dwuspadowe
    with tabs[4]:
        load_and_run_module("ObciazeniaWiatrem_DachyDwuspadowe.py")

    # 6. Dachy czterospadowe
    with tabs[5]:
        load_and_run_module("ObciazeniaWiatrem_DachyCzterospadowe.py")

    # 7. Dachy łukowe
    with tabs[6]:
        load_and_run_module("ObciazeniaWiatrem_DachyLukowe.py")

    # 8. Kopuły na rzucie kołowym
    with tabs[7]:
        load_and_run_module("ObciazeniaWiatrem_Kopuly.py")

    # 9. Wiaty jednospadowe
    with tabs[8]:
        load_and_run_module("ObciazeniaWiatrem_WiatyJednospadowe.py")
    
    # 10. Wiaty dwuspadowe
    with tabs[9]:
        load_and_run_module("ObciazeniaWiatrem_WiatyDwuspadowe.py")
        
    # 11. Wiaty wielospadowe
    with tabs[10]:
        load_and_run_module("ObciazeniaWiatrem_WiatyWielospadowe.py") 

    # 12. Tablice wolnostojące
    with tabs[11]:
        load_and_run_module("ObciazeniaWiatrem_Tablice.py")

    # 13. Flagi
    with tabs[12]:
        load_and_run_module("ObciazeniaWiatrem_Flagi.py")

# Ten blok pozwala uruchomić plik samodzielnie w celach testowych
if __name__ == "__main__":
    st.set_page_config(page_title="Obciążenie wiatrem", layout="wide")
    StronaObciazeniaWiatrem()