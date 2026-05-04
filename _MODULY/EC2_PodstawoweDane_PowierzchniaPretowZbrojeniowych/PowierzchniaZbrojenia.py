import streamlit as st
import math
import sys
import os
import pandas as pd

# --- KOREKTA DLA FOLDERÓW ---
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

def get_bar_area(diameter_mm):
    """Zwraca pole przekroju jednego pręta w cm2"""
    return (math.pi * (diameter_mm / 2)**2) / 100

def StronaPowierzchniaZbrojenia():
    # --- STYLIZACJA (CSS) ---
    st.markdown("""
        <style>
        div[data-baseweb="input"] {
            margin-bottom: 0px;
        }
        </style>
    """, unsafe_allow_html=True)

    # --- TYTUŁ GŁÓWNY ---
    # h1, wyśrodkowany, wielkie litery
    st.markdown("<h1 style='text-align: center; margin-bottom: 20px;'>POWIERZCHNIA PRĘTÓW ZBROJENIOWYCH</h1>", unsafe_allow_html=True)

    # --- ZAKŁADKI ---
    tab1, tab2 = st.tabs([
        "POWIERZCHNIA ZBROJENIA ELEMENTÓW POWIERZCHNIOWYCH (PŁYTY / ŚCIANY)", 
        "POWIERZCHNIA ZBROJENIA ELEMENTÓW PRĘTOWYCH (BELKI, SŁUPY)"
    ])

    # =========================================================================
    # ZAKŁADKA 1: PŁYTY / ŚCIANY
    # =========================================================================
    with tab1:
        # 1. SEKCJA WYMAGAŃ
        st.markdown("### DANE WEJŚCIOWE (WYMAGANE ZBROJENIE)")
        
        col_req1, col_req2 = st.columns([1, 2])
        with col_req1:
            as_req_slab = st.number_input(
                "Wymagane $A_{s,req}$ [cm²/mb]", 
                min_value=0.0, value=0.0, step=0.1, format="%.2f",
                help="Wpisz wartość z obliczeń statycznych, aby uzyskać podpowiedzi."
            )
        
        # Sugestie w NIEBIESKIM PASKU (jedna linia)
        if as_req_slab > 0:
            suggestions = []
            for d in [8, 10, 12, 16]:
                area_1 = get_bar_area(d)
                s_max = (area_1 * 100.0) / as_req_slab
                # Zaokrąglenie w dół do 0.5 cm
                s_pract = math.floor(s_max * 2) / 2.0
                
                if 5.0 <= s_pract <= 35.0:
                    as_prov_sug = area_1 * (100.0 / s_pract)
                    # Format: fi 8/15 (As=3.35 cm2)
                    suggestions.append(f"$\phi {d}/{s_pract:.1f} \ (A_s={as_prov_sug:.2f} \ cm^2)$")
            
            if suggestions:
                final_text = " &nbsp;&nbsp; | &nbsp;&nbsp; ".join(suggestions)
                st.info(f"💡 **Szybkie sugestie:** &nbsp;&nbsp; {final_text}")
            else:
                st.warning("Duże zbrojenie. Rozważ większe średnice lub gęstszy rozstaw.")
        else:
            st.info("☝️ Wpisz $A_{s,req}$, aby zobaczyć sugestie doboru prętów.")

        # 2. KONFIGURATOR
        st.markdown("### DOBÓR RZECZYWISTY (KONFIGURATOR)")
        
        # a) Zbrojenie podstawowe
        c1, c2, c3 = st.columns([2, 2, 2])
        with c1:
            st.markdown("**PODSTAWOWE**")
            fi_podst = st.selectbox("$\phi_{podst}$ [mm]", [6, 8, 10, 12, 14, 16, 20, 25], index=2, key="p_fi1")
            s_podst = st.number_input("$s_{podst}$ [cm]", 5.0, 50.0, 15.0, 1.0, key="p_s1")
            As_podst = get_bar_area(fi_podst) * (100.0 / s_podst)
            st.caption(f"$A_s = {As_podst:.2f}$ cm²/mb")

        # b) Dozbrojenie 1
        with c2:
            use_add1 = st.checkbox("Dozbrojenie 1", key="p_c1")
            if use_add1:
                fi_add1 = st.selectbox("$\phi_{dod1}$ [mm]", [6, 8, 10, 12, 14, 16, 20, 25], index=2, key="p_fi2")
                s_add1 = st.number_input("$s_{dod1}$ [cm]", 5.0, 50.0, 15.0, 1.0, key="p_s2")
                As_add1 = get_bar_area(fi_add1) * (100.0 / s_add1)
                st.caption(f"$A_s = {As_add1:.2f}$ cm²/mb")
            else:
                As_add1 = 0.0

        # c) Dozbrojenie 2
        with c3:
            use_add2 = st.checkbox("Dozbrojenie 2", key="p_c2")
            if use_add2:
                fi_add2 = st.selectbox("$\phi_{dod2}$ [mm]", [6, 8, 10, 12, 14, 16, 20, 25], index=2, key="p_fi3")
                s_add2 = st.number_input("$s_{dod2}$ [cm]", 5.0, 50.0, 15.0, 1.0, key="p_s3")
                As_add2 = get_bar_area(fi_add2) * (100.0 / s_add2)
                st.caption(f"$A_s = {As_add2:.2f}$ cm²/mb")
            else:
                As_add2 = 0.0

        # 3. WYNIKI
        As_total = As_podst + As_add1 + As_add2
        
        if as_req_slab > 0:
            utilization = (as_req_slab / As_total) * 100 if As_total > 0 else 999
            is_ok = As_total >= as_req_slab
            
            col_res1, col_res2 = st.columns([2, 1])
            with col_res1:
                st.markdown(f"#### PRZYJĘTE: $A_{{s,prov}} = {As_total:.2f} \ cm^2/mb$")
                if is_ok:
                    st.success(f"✅ WARUNEK SPEŁNIONY ($A_{{s,req}} = {as_req_slab:.2f}$)")
                else:
                    st.error(f"❌ BRAKUJE {(as_req_slab - As_total):.2f} cm²/mb")
            
            with col_res2:
                st.metric("Wykorzystanie", f"{utilization:.0f}%", delta_color="inverse" if is_ok else "normal")
        else:
            st.info(f"**☝️WYNIK CAŁKOWITY:** $A_{{s,prov}} = {As_total:.2f} \ cm^2/mb$")

        # --- PEŁNA TABELA POMOCNICZA PŁYTY ---
        with st.expander("📋 TABELA POMOCNICZA: PŁYTY [cm²/mb]"):
            s_range_full = [
                5.0, 6.0, 7.0, 7.5, 8.0, 9.0, 10.0, 11.0, 12.0, 12.5, 
                13.0, 14.0, 15.0, 16.0, 17.0, 17.5, 18.0, 19.0, 20.0, 
                21.0, 22.0, 22.5, 23.0, 24.0, 25.0, 30.0, 35.0, 40.0
            ]
            d_range_full = [6, 8, 10, 12, 14, 16, 20, 25, 32]
            
            data_slab = {}
            for d in d_range_full:
                col_name = f"ϕ {d}"
                vals = []
                for s in s_range_full:
                    val = get_bar_area(d) * (100.0 / s)
                    vals.append(f"{val:.2f}")
                data_slab[col_name] = vals
                
            df_plyty = pd.DataFrame(data_slab, index=[f"s={s} cm" for s in s_range_full])
            st.dataframe(df_plyty, use_container_width=True, height=500)

    # =========================================================================
    # ZAKŁADKA 2: BELKI / SŁUPY
    # =========================================================================
    with tab2:
        # 1. SEKCJA WYMAGAŃ
        st.markdown("### DANE WEJŚCIOWE (WYMAGANE ZBROJENIE)")
        
        col_b_req1, col_b_req2 = st.columns([1, 2])
        with col_b_req1:
            # Dodano parametr help, aby był identyczny jak w płytach
            as_req_beam = st.number_input(
                "Wymagane $A_{s,req}$ [cm²]", 
                min_value=0.0, value=0.0, step=0.1, format="%.2f", key="b_req",
                help="Wpisz wartość z obliczeń statycznych, aby uzyskać podpowiedzi."
            )
        
        # Sugestie w NIEBIESKIM PASKU (st.info)
        if as_req_beam > 0:
            suggestions_b = []
            for d in [12, 16, 20, 25, 32]:
                area_1 = get_bar_area(d)
                n_needed = math.ceil(as_req_beam / area_1)
                as_prov_sug = n_needed * area_1
                # Format: 3fi12 (3.39 cm2)
                suggestions_b.append(f"{n_needed}$\phi{d} \ ({as_prov_sug:.2f} \ cm^2)$")
            
            final_text_b = " &nbsp;&nbsp; | &nbsp;&nbsp; ".join(suggestions_b)
            st.info(f"💡 **Szybkie sugestie:** &nbsp;&nbsp; {final_text_b}")
        else:
            # Komunikat identyczny jak w płytach
            st.info("☝️ Wpisz $A_{s,req}$, aby zobaczyć sugestie doboru prętów.")

        # 2. KONFIGURATOR
        st.markdown("### DOBÓR RZECZYWISTY (KONFIGURATOR)")

        c1, c2, c3 = st.columns([2, 2, 2])
        with c1:
            st.markdown("**PODSTAWOWE**")
            fi_b_podst = st.selectbox("$\phi_{podst}$ [mm]", [8, 10, 12, 14, 16, 20, 25, 32], index=4, key="b_fi1")
            n_podst = st.number_input("sztuk $n_{podst}$", 1, 50, 2, 1, key="b_n1")
            As_b_podst = get_bar_area(fi_b_podst) * n_podst
            st.caption(f"$A_s = {As_b_podst:.2f}$ cm²")

        with c2:
            use_b_add1 = st.checkbox("Dozbrojenie 1", key="b_c1")
            if use_b_add1:
                fi_b_add1 = st.selectbox("$\phi_{dod1}$ [mm]", [8, 10, 12, 14, 16, 20, 25, 32], index=2, key="b_fi2")
                n_add1 = st.number_input("sztuk $n_{dod1}$", 1, 50, 1, 1, key="b_n2")
                As_b_add1 = get_bar_area(fi_b_add1) * n_add1
                st.caption(f"$A_s = {As_b_add1:.2f}$ cm²")
            else:
                As_b_add1 = 0.0

        with c3:
            use_b_add2 = st.checkbox("Dozbrojenie 2", key="b_c2")
            if use_b_add2:
                fi_b_add2 = st.selectbox("$\phi_{dod2}$ [mm]", [8, 10, 12, 14, 16, 20, 25, 32], index=2, key="b_fi3")
                n_add2 = st.number_input("sztuk $n_{dod2}$", 1, 50, 1, 1, key="b_n3")
                As_b_add2 = get_bar_area(fi_b_add2) * n_add2
                st.caption(f"$A_s = {As_b_add2:.2f}$ cm²")
            else:
                As_b_add2 = 0.0

        # 3. WYNIKI
        st.markdown("---")
        As_b_total = As_b_podst + As_b_add1 + As_b_add2
        
        if as_req_beam > 0:
            is_ok_b = As_b_total >= as_req_beam
            col_res1, col_res2 = st.columns([2, 1])
            with col_res1:
                st.markdown(f"#### PRZYJĘTE: $A_{{s,prov}} = {As_b_total:.2f} \ cm^2$")
                if is_ok_b:
                    st.success(f"✅ WARUNEK SPEŁNIONY ($A_{{s,req}} = {as_req_beam:.2f}$)")
                else:
                    st.error(f"❌ BRAKUJE {(as_req_beam - As_b_total):.2f} cm²")
            with col_res2:
                 util_b = (as_req_beam / As_b_total) * 100 if As_b_total > 0 else 999
                 st.metric("Wykorzystanie", f"{util_b:.0f}%", delta_color="inverse" if is_ok_b else "normal")
        else:
             st.info(f"**WYNIK CAŁKOWITY:** $A_{{s,prov}} = {As_b_total:.2f} \ cm^2$")

        # --- PEŁNA TABELA POMOCNICZA BELKI ---
        with st.expander("📋 TABELA POMOCNICZA: BELKI [cm²]"):
            n_range_full = range(1, 16)
            d_range_full_b = [6, 8, 10, 12, 14, 16, 20, 25, 32]
            
            data_beam = {}
            for d in d_range_full_b:
                col_name = f"ϕ {d}"
                vals = []
                for n in n_range_full:
                    val = get_bar_area(d) * n
                    vals.append(f"{val:.2f}")
                data_beam[col_name] = vals
                
            df_belki = pd.DataFrame(data_beam, index=[f"{n} szt." for n in n_range_full])
            st.dataframe(df_belki, use_container_width=True)

if __name__ == "__main__":
    StronaPowierzchniaZbrojenia()