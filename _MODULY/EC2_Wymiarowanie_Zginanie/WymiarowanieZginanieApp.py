import streamlit as st
import os
import importlib.util

def load_and_run_module(filename):
    """
    Pomocnicza funkcja do dynamicznego ładowania i uruchamiania modułu z pliku.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, filename)

    if not os.path.exists(file_path):
        st.info(f"Moduł '{filename}' nie został jeszcze utworzony.")
        return

    try:
        spec = importlib.util.spec_from_file_location("dynamic_module", file_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            if hasattr(module, "run"):
                module.run()
            
    except Exception as e:
        st.warning(f"🚧 Moduł w trakcie wdrażania lub wystąpił błąd: {e}")

# ZMIANA NAZWY FUNKCJI PONIŻEJ na 'run'
def run():
    """
    Główna funkcja widoku Wymiarowania na Zginanie.
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

    # 1. TYTUŁ GŁÓWNY
    st.markdown(
        """
        <div style="text-align:center; margin-top:0.4rem; margin-bottom:0rem;">
            <span style="font-size:42px; font-weight:800; letter-spacing:1px; color:#dddddd;">
                WYMIAROWANIE ELEMENTÓW ZGINANYCH
            </span>
        </div>
        <div style="text-align:center; font-size:14px; color:#aaaaaa; margin-top:-12px; margin-bottom:1.5rem;">
            wg PN-EN 1992-1-1
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    tab_names = [
        "Belki żelbetowe",
        "Płyty żelbetowe",
     ]

    tabs = st.tabs(tab_names)

    with tabs[0]:
        load_and_run_module("WymiarowanieBelkiZginanie.py")

    with tabs[1]:
        load_and_run_module("WymiarowaniePlytyZginanie.py")

