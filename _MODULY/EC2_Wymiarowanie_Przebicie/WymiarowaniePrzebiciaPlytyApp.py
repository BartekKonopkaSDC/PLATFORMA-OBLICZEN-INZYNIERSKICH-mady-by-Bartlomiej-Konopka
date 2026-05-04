# ==============================================================================
# WymiarowaniePrzebiciaPlytyApp.py
# FINAL CLEAN VERSION
# Poprawka:
# - zachowane mniejsze odstępy pionowe między sekcjami tabs
# - zwiększone odstępy poziome między nazwami zakładek
# - poprawiona czytelność tekstów typu:
#   Wewnętrzny | Krawędziowy | Narożny
# ==============================================================================

import streamlit as st
import os
import importlib.util


# ==============================================================================
# LOAD MODULE
# ==============================================================================
def load_and_run_module(filename):

    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, filename)

    if not os.path.exists(file_path):
        st.info(f"Brak pliku modułu: {filename}")
        return

    try:
        spec = importlib.util.spec_from_file_location("dynamic_module", file_path)

        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            if hasattr(module, "run"):
                module.run()

    except Exception as e:
        st.warning(f"Błąd modułu {filename}: {e}")


# ==============================================================================
# MAIN
# ==============================================================================
def run():

    st.markdown(
        """
        <style>

        /* ==============================================================
           GŁÓWNY KONTENER
        ============================================================== */
        .block-container{
            padding-top:1.0rem !important;
            padding-bottom:1.5rem !important;
        }

        /* ==============================================================
           TABS - pionowo kompaktowo, poziomo czytelnie
        ============================================================== */

        div[data-testid="stTabs"]{
            margin-top:0rem !important;
            margin-bottom:0rem !important;
            padding-top:0rem !important;
            padding-bottom:0rem !important;
        }

        div[data-baseweb="tab-list"]{
            gap:1.25rem !important;          /* <<< KLUCZOWE */
            margin-bottom:0rem !important;
            flex-wrap:wrap !important;
        }

        div[role="tablist"]{
            margin-bottom:0rem !important;
            padding-bottom:0rem !important;
            min-height:auto !important;
        }

        button[data-baseweb="tab"]{
            padding-top:0.20rem !important;
            padding-bottom:0.20rem !important;
            padding-left:0rem !important;
            padding-right:0rem !important;
            height:auto !important;
            white-space:nowrap !important;
        }

        div[data-baseweb="tab-panel"]{
            padding-top:0.15rem !important;
            margin-top:0rem !important;
        }

        </style>
        """,
        unsafe_allow_html=True
    )

    # ==========================================================================
    # HEADER
    # ==========================================================================
    st.markdown("""
    <div style="text-align:center; margin-top:0.35rem; margin-bottom:0rem;">
        <span style="
            font-size:42px;
            font-weight:800;
            letter-spacing:1px;
            color:#dddddd;">
            WYMIAROWANIE PRZEBICIA PŁYT
        </span>
    </div>

    <div style="
        text-align:center;
        font-size:14px;
        color:#aaaaaa;
        margin-top:-12px;
        margin-bottom:1rem;">
        wg PN-EN 1992-1-1
    </div>
    """, unsafe_allow_html=True)

    # ==========================================================================
    # TABS GŁÓWNE
    # ==========================================================================
    main_tabs = st.tabs([
        "Słup prostokątny / kwadratowy",
        "Słup okrągły",
        "Narożnik ściany",
        "Zakończenie ściany"
    ])

    # ==========================================================================
    # TAB 1
    # ==========================================================================
    with main_tabs[0]:

        t2 = st.tabs(["Wewnętrzny", "Krawędziowy", "Narożny"])

        with t2[0]:

            t3 = st.tabs(["Płyta stropowa", "Płyta fundamentowa"])

            with t3[0]:
                load_and_run_module(
                    "WymiarowaniePrzebiciaPlytySlupProstokatnyKwadratowyWewnetrznyPS.py"
                )

            with t3[1]:
                load_and_run_module(
                    "WymiarowaniePrzebiciaPlytySlupProstokatnyKwadratowyWewnetrznyPF.py"
                )

        with t2[1]:

            t3 = st.tabs(["Płyta stropowa", "Płyta fundamentowa"])

            with t3[0]:
                load_and_run_module(
                    "WymiarowaniePrzebiciaPlytySlupProstokatnyKwadratowyKrawedziowyPS.py"
                )

            with t3[1]:
                load_and_run_module(
                    "WymiarowaniePrzebiciaPlytySlupProstokatnyKwadratowyKrawedziowyPF.py"
                )

        with t2[2]:

            t3 = st.tabs(["Płyta stropowa", "Płyta fundamentowa"])

            with t3[0]:
                load_and_run_module(
                    "WymiarowaniePrzebiciaPlytySlupProstokatnyKwadratowyNaroznyPS.py"
                )

            with t3[1]:
                load_and_run_module(
                    "WymiarowaniePrzebiciaPlytySlupProstokatnyKwadratowyNaroznyPF.py"
                )

    # ==========================================================================
    # TAB 2
    # ==========================================================================
    with main_tabs[1]:

        t2 = st.tabs(["Wewnętrzny", "Krawędziowy", "Narożny"])

        with t2[0]:

            t3 = st.tabs(["Płyta stropowa", "Płyta fundamentowa"])

            with t3[0]:
                load_and_run_module(
                    "WymiarowaniePrzebiciaPlytySlupOkraglyWewnetrznyPS.py"
                )

            with t3[1]:
                load_and_run_module(
                    "WymiarowaniePrzebiciaPlytySlupOkraglyWewnetrznyPF.py"
                )

        with t2[1]:

            t3 = st.tabs(["Płyta stropowa", "Płyta fundamentowa"])

            with t3[0]:
                load_and_run_module(
                    "WymiarowaniePrzebiciaPlytySlupOkraglyKrawedziowyPS.py"
                )

            with t3[1]:
                load_and_run_module(
                    "WymiarowaniePrzebiciaPlytySlupOkraglyKrawedziowyPF.py"
                )

        with t2[2]:

            t3 = st.tabs(["Płyta stropowa", "Płyta fundamentowa"])

            with t3[0]:
                load_and_run_module(
                    "WymiarowaniePrzebiciaPlytySlupOkraglyNaroznyPS.py"
                )

            with t3[1]:
                load_and_run_module(
                    "WymiarowaniePrzebiciaPlytySlupOkraglyNaroznyPF.py"
                )

    # ==========================================================================
    # TAB 3
    # ==========================================================================
    with main_tabs[2]:

        t3 = st.tabs(["Płyta stropowa", "Płyta fundamentowa"])

        with t3[0]:
            load_and_run_module("WymiarowaniePrzebiciaPlytyNaroznikScianyPS.py")

        with t3[1]:
            load_and_run_module("WymiarowaniePrzebiciaPlytyNaroznikScianyPF.py")

    # ==========================================================================
    # TAB 4
    # ==========================================================================
    with main_tabs[3]:

        t3 = st.tabs(["Płyta stropowa", "Płyta fundamentowa"])

        with t3[0]:
            load_and_run_module("WymiarowaniePrzebiciaPlytyZakonczenieScianyPS.py")

        with t3[1]:
            load_and_run_module("WymiarowaniePrzebiciaPlytyZakonczenieScianyPF.py")


if __name__ == "__main__":
    run()