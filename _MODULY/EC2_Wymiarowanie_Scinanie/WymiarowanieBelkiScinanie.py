# ==============================================================================
# SCINANIE BELKI – EC2 (PN-EN 1992-1-1)
# Zakres: SGN + zbrojenie minimalne (bez SGU)
# ==============================================================================

import streamlit as st
import math

# --- TABLICE ---
try:
    from TABLICE.ParametryBetonu import CONCRETE_TABLE, list_concrete_classes
    from TABLICE.ParametryStali import STEEL_TABLE
except Exception:
    st.error("Błąd importu TABLICE")
    st.stop()


def StronaScinanieBelki():

    # ------------------------------------------------------------------
    # STYL
    # ------------------------------------------------------------------
    st.markdown(
        """
        <style>
        .block-container { padding-top: 1.5rem; padding-bottom: 1.5rem; }

        button[kind="primary"] {
            background: #ff4b4b !important;
            border-radius: 12px !important;
            height: 52px !important;
            font-size: 17px !important;
            font-weight: 900 !important;
        }

        .ok-box {
            background:#123d2b;
            border:2px solid #2ecc71;
            border-radius:8px;
            padding:12px;
            text-align:center;
            font-weight:700;
            color:#d1fae5;
            font-size:15px;
            min-height:78px;
            display:flex;
            align-items:center;
            justify-content:center;
        }

        .bad-box {
            background:#4a1c1c;
            border:2px solid #ef4444;
            border-radius:8px;
            padding:12px;
            text-align:center;
            font-weight:700;
            color:#fee2e2;
            font-size:15px;
            min-height:78px;
            display:flex;
            align-items:center;
            justify-content:center;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # ------------------------------------------------------------------
    # TYTUŁ
    # ------------------------------------------------------------------
    st.markdown(
        """
        <div style="text-align:center; margin-top:0.4rem; margin-bottom:0rem;">
            <span style="font-size:42px; font-weight:800; letter-spacing:1px; color:#dddddd;">
                OBLICZENIA ŚCINANIA ELEMENTU ŻELBETOWEGO
            </span>
        </div>
        <div style="text-align:center; font-size:14px; color:#aaaaaa; margin-top:-12px; margin-bottom:0.6rem;">
            wg PN-EN 1992-1-1
        </div>
        """,
        unsafe_allow_html=True
    )

    if "sb_calc" not in st.session_state:
        st.session_state.sb_calc = False
        st.session_state.sb = None

    def reset():
        st.session_state.sb_calc = False
        st.session_state.sb = None

    # ------------------------------------------------------------------
    # DANE WEJŚCIOWE
    # ------------------------------------------------------------------
    st.markdown("### DANE WEJŚCIOWE")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        concrete_name = st.selectbox("Klasa betonu", list_concrete_classes(), index=4, on_change=reset)
    with c2:
        steel_name = st.selectbox("Klasa stali zbrojeniowej", list(STEEL_TABLE.keys()), index=1, on_change=reset)
    with c3:
        bw_cm = st.number_input("Szerokość elementu $b_w$ [cm]", value=30.0, step=1.0, on_change=reset)
    with c4:
        h_cm = st.number_input("Wysokość elementu $h$ [cm]", value=50.0, step=1.0, on_change=reset)

    c5, c6, c7, c8 = st.columns(4)
    with c5:
        phi_w = st.selectbox("Średnica strzemion $\\phi_w$ [mm]", [6, 8, 10, 12, 16], index=1, on_change=reset)
    with c6:
        n_legs = st.selectbox("Liczba ramion strzemion", [1, 2, 3, 4, 5, 6], index=1, on_change=reset)
    with c7:
        As1_cm2 = st.number_input("Pole zbrojenia podłużnego $A_{s1}$ [cm²]", value=6.0, step=0.5, on_change=reset)
    with c8:
        a1_mm = st.number_input("Odległość osi pręta $a_1$ [mm]", value=45, step=5, on_change=reset)

    c9, c10 = st.columns(2)
    with c9:
        V_Ed = st.number_input("Siła poprzeczna $V_{Ed}$ [kN]", value=150.0, step=10.0, on_change=reset)
    with c10:
        cot_theta = st.slider("Kotangens kąta $\\theta$ ($\\cot\\theta$)", 1.0, 2.5, 2.0, 0.1, on_change=reset)

    # ------------------------------------------------------------------
    # OBLICZENIA
    # ------------------------------------------------------------------
    _, c_btn, _ = st.columns([1, 2, 1])
    with c_btn:
        oblicz = st.button("OBLICZ", type="primary", use_container_width=True)

    if oblicz:
        beton = CONCRETE_TABLE[concrete_name]
        stal = STEEL_TABLE[steel_name]

        fck = beton.fck
        fyk = stal.fyk
        gamma_c = 1.4
        gamma_s = 1.15  # Norma zaleca 1.15 dla stali

        d_mm = h_cm * 10 - a1_mm
        d_m = d_mm / 1000
        z_m = 0.9 * d_m
        bw_m = bw_cm / 100

        nu1 = 0.6 * (1 - fck / 250)
        tan_theta = 1 / cot_theta
        fcd = fck / gamma_c
        fywd = fyk / gamma_s
        
        # V_Rd,max
        # Przyjęto alpha_cw = 1.0
        V_Rd_max = (bw_m * z_m * nu1 * fcd / (cot_theta + tan_theta)) * 1000

        As1_mm2 = As1_cm2 * 100
        rho_l = min(As1_mm2 / (bw_cm * 10 * d_mm), 0.02)
        k = min(1 + math.sqrt(200 / d_mm), 2.0)
        C_Rd_c = 0.18 / gamma_c
        v_min = 0.035 * k**1.5 * math.sqrt(fck)
        
        # Obliczenie v_Rd_c [MPa]
        val_calc = C_Rd_c * k * (100 * rho_l * fck) ** (1 / 3)
        v_Rd_c_val = max(val_calc, v_min)
        
        V_Rd_c = v_Rd_c_val * bw_m * d_m * 1000

        rho_w_min = 0.08 * math.sqrt(fck) / fyk
        a_sw_min = rho_w_min * bw_m * 10000

        Asw = n_legs * math.pi * (phi_w / 20) ** 2
        
        # Zbrojenie obliczeniowe
        if V_Ed > V_Rd_c:
            V_Ed_MN = V_Ed / 1000.0
            a_sw_req = (V_Ed_MN / (z_m * fywd * cot_theta)) * 10000 # cm2/m
        else:
            a_sw_req = 0.0

        a_sw_design = max(a_sw_min, a_sw_req)

        # Rozstaw
        if a_sw_design > 0:
            s_cal = (Asw / a_sw_design) * 100
        else:
            s_cal = 100.0
            
        s_max = min(0.75 * d_mm / 10, 40)
        s = math.floor(min(s_cal, s_max))

        if s > 0:
            a_sw_prov = Asw / s * 100
        else:
            a_sw_prov = 999.0

        # ZAPIS DO SESJI (w tym zmienne pomocnicze do szczegółów)
        st.session_state.sb = {
            "V_Ed": V_Ed,
            "V_Rd_c": V_Rd_c,
            "V_Rd_max": V_Rd_max,
            "phi_w": phi_w,
            "n_legs": n_legs,
            "s": s,
            "a_sw_min": a_sw_min,
            "a_sw_prov": a_sw_prov,
            "bw_cm": bw_cm,
            "h_cm": h_cm,
            "fck": fck,
            "fyk": fyk,

            # Zmienne do szczegółów:
            "d_cm": d_mm/10, "z_cm": z_m*100, "fcd": fcd, "fywd": fywd,
            "nu1": nu1, "cot_theta": cot_theta, "tan_theta": tan_theta,
            "k": k, "rho_l": rho_l, "v_min": v_min, "v_Rd_c_val": v_Rd_c_val,
            "shear_needed": (V_Ed > V_Rd_c),
            "a_sw_req": a_sw_req, "a_sw_design": a_sw_design,
            "s_cal": s_cal, "s_max": s_max, "Asw": Asw
        }

        st.session_state.sb_calc = True

    # ------------------------------------------------------------------
    # WYNIKI
    # ------------------------------------------------------------------
    if st.session_state.sb_calc:
        r = st.session_state.sb
        util_c = r["V_Ed"] / r["V_Rd_c"]
        util_max = r["V_Ed"] / r["V_Rd_max"]

        st.markdown("### WYNIKI")

        col1, col2, col3 = st.columns([0.315, 0.315, 0.37])

        with col1:
            st.markdown(
                """
                <div style="
                    text-align:center;
                    font-weight:600;
                    font-size:18px;
                    color:#e5e7eb;
                ">
                    Nośność przekroju betonowego
                </div>
                """,
                unsafe_allow_html=True
            )           
            st.latex(rf"V_{{Rd,c}} = {r['V_Rd_c']:.2f}\ \text{{kN}}")
            st.markdown(
                f"<div class='{'ok-box' if util_c <= 1 else 'bad-box'}'>"
                f"{'Przekrój odpowiedni' if util_c <= 1 else 'Konieczne wyliczenie strzemion'}"
                f"<br>Wytężenie: {util_c:.1%}</div>",
                unsafe_allow_html=True
            )

        with col2:
            st.markdown(
                """
                <div style="
                    text-align:center;
                    font-weight:600;
                    font-size:18px;
                    color:#e5e7eb;
                ">
                    Nośność ściskanego krzyżulca betonowego
                </div>
                """,
                unsafe_allow_html=True
            )
            st.latex(rf"V_{{Rd,max}} = {r['V_Rd_max']:.2f}\ \text{{kN}}")
            st.markdown(
                f"<div class='{'ok-box' if util_max <= 1 else 'bad-box'}'>"
                f"{'Przekrój odpowiedni' if util_max <= 1 else 'Należy zwiększyć przekrój lub klasę betonu'}"
                f"<br>Wytężenie: {util_max:.1%}</div>",
                unsafe_allow_html=True
            )

        with col3:
            st.markdown(
                """
                <div style="
                    text-align:center;
                    font-weight:600;
                    font-size:18px;
                    color:#e5e7eb;
                ">
                    Rozstaw obliczeniowy strzemion
                </div>
                """,
                unsafe_allow_html=True
            )     
            st.latex(rf"\Phi {r['phi_w']} \ ({r['n_legs']}\text{{-cięte}}) \ \text{{co}} \ {r['s']} \ \text{{cm}}")
            st.latex(
                rf"A_{{sw,prov}} = {r['a_sw_prov']:.2f}\;\mathrm{{cm}}^2/\mathrm{{m}} \ge "
                rf"A_{{sw,design}} = {r['a_sw_design']:.2f}\;\mathrm{{cm}}^2/\mathrm{{m}}"
            )
    
        # ------------------------------------------------------------------
        # SZCZEGÓŁY OBLICZEŃ (DODANO NA PROŚBĘ)
        # ------------------------------------------------------------------
        
        st.markdown("")
        with st.expander("🔍 Szczegóły obliczeń", expanded=False):
            
            st.markdown("#### 1. Podstawowe dane")
            # Wymiary geometryczne
            st.latex(rf"b_w = {r['bw_cm']:.1f} \, \text{{cm}}, \quad h = {r['h_cm']:.1f} \, \text{{cm}}")
            st.latex(rf"d = {r['d_cm']:.1f} \, \text{{cm}}, \quad z \approx 0.9d = {r['z_cm']:.1f} \, \text{{cm}}")
            # Parametry materiałowe (charakterystyczne -> obliczeniowe)
            st.latex(rf"f_{{ck}} = {r['fck']} \, \text{{MPa}} \rightarrow f_{{cd}} = {r['fcd']:.1f} \, \text{{MPa}}")
            st.latex(rf"f_{{yk}} = {r['fyk']} \, \text{{MPa}} \rightarrow f_{{ywd}} = {r['fywd']:.0f} \, \text{{MPa}}")            
            
            st.markdown("#### 2. Wyniki obliczeń")
            st.markdown("#### 2.1 Nośność krzyżulca ściskanego ($V_{Rd,max}$)")
            st.write("Warunek miażdżenia betonu (EC2 wzór 6.9):")
            st.latex(r"\nu_1 = 0.6 \left( 1 - \frac{f_{ck}}{250} \right) = " + f"{r['nu1']:.3f}")
            denom = r['cot_theta'] + r['tan_theta']         
            st.latex(rf"V_{{Rd,max}} = \frac{{\alpha_{{cw}} b_w z \nu_1 f_{{cd}}}}{{\cot\theta + \tan\theta}} = "
                     rf"\frac{{1.0 \cdot {r['bw_cm']/100:.2f}\,\text{{m}} \cdot {r['z_cm']/100:.3f}\,\text{{m}} \cdot {r['nu1']:.3f} \cdot {r['fcd']:.1f}\,\text{{MPa}} \cdot 10^3}}{{{denom:.2f}}} = "
                     rf"\mathbf{{{r['V_Rd_max']:.2f} \, \text{{kN}}}}")

            st.markdown("#### 2.2 Nośność bez zbrojenia na ścinanie ($V_{Rd,c}$)")
            st.write("Wg wzoru 6.2.a:")
            st.latex(rf"k = 1 + \sqrt{{\frac{{200}}{{d}}}} = 1 + \sqrt{{\frac{{200}}{{ {r['d_cm']*10:.0f}\,\text{{mm}} }}}} = {r['k']:.3f} \le 2.0")
            st.latex(rf"\rho_l = \frac{{A_{{s1}}}}{{b_w d}} = \frac{{ {As1_cm2:.2f}\,\text{{cm}}^2 }}{{ {r['bw_cm']:.1f}\,\text{{cm}} \cdot {r['d_cm']:.1f}\,\text{{cm}} }} = {r['rho_l']*100:.2f}\% \le 2\%")
            st.latex(rf"v_{{min}} = 0.035 k^{{1.5}} \sqrt{{f_{{ck}}}} = 0.035 \cdot {r['k']:.3f}^{{1.5}} \cdot \sqrt{{ {r['fck']}\,\text{{MPa}} }} = {r['v_min']:.3f} \, \text{{MPa}}")
            st.latex(rf"v_{{Rd,c}} = \max \left( C_{{Rd,c}} k (100\rho_l f_{{ck}})^{{1/3}} ; v_{{min}} \right) = \mathbf{{{r['v_Rd_c_val']:.3f} \, \text{{MPa}}}}")
            st.latex(rf"V_{{Rd,c}} = v_{{Rd,c}} \cdot b_w \cdot d = {r['v_Rd_c_val']:.3f}\,\text{{MPa}} \cdot {r['bw_cm']:.1f}\,\text{{cm}} \cdot {r['d_cm']:.1f}\,\text{{cm}} \cdot 10^{{-1}} = \mathbf{{{r['V_Rd_c']:.2f} \, \text{{kN}}}}")

            st.markdown("#### 2.3 Dobór zbrojenia ($A_{sw}/s$)")

            st.write("Zbrojenie minimalne (wzór 9.5N):")
            # Wzór = Podstawienie = Wynik
            st.latex(rf"A_{{sw,min}} = \frac{{0.08 \sqrt{{f_{{ck}}}}}}{{f_{{yk}}}} b_w = \frac{{0.08 \sqrt{{ {r['fck']}\,\text{{MPa}} }} }}{{ {r['fyk']}\,\text{{MPa}} }} \cdot {r['bw_cm']:.1f}\,\text{{cm}} = \mathbf{{{r['a_sw_min']:.2f} \, \text{{cm}}^2/\text{{m}}}}")

            if r['shear_needed']:
                st.write(f"Ponieważ $V_{{Ed}} = {V_Ed:.1f} > V_{{Rd,c}}$, wymagane jest zbrojenie obliczeniowe:")
                # Wzór = Podstawienie = Wynik
                st.latex(rf"A_{{sw,req}} = \frac{{V_{{Ed}}}}{{z \cdot f_{{ywd}} \cdot \cot\theta}} = \frac{{ {V_Ed:.1f}\,\text{{kN}} }}{{ {r['z_cm']/100:.3f}\,\text{{m}} \cdot {r['fywd']:.0f}\,\text{{MPa}} \cdot {r['cot_theta']} }} = \mathbf{{{r['a_sw_req']:.2f} \, \text{{cm}}^2/\text{{m}}}}")
            else:
                st.write(f"Ponieważ $V_{{Ed}} = {V_Ed:.1f} \le V_{{Rd,c}}$, teoretycznie $a_{{sw,req}} = 0$.")

            # --- ZMIANA TUTAJ: POKAZANIE FUNKCJI MAX ---
            st.write("Przyjęte zbrojenie miarodajne:")
            st.latex(rf"A_{{sw,design}} = \max(a_{{sw,min}}; a_{{sw,req}}) = \max({r['a_sw_min']:.2f}\text{{ cm}}^2/\text{{m }} ; {r['a_sw_req']:.2f}\text{{ cm}}^2/\text{{m}}) = \mathbf{{{r['a_sw_design']:.2f} \, \text{{cm}}^2/\text{{m}}}}")
            # -------------------------------------------

            st.markdown("#### 2.4 Rozstaw strzemion")
            
            st.write("Maksymalny rozstaw konstrukcyjny:")
            # Wzór = Podstawienie = Wynik
            st.latex(rf"s_{{max}} = \min(0.75d ; 40\text{{cm}}) = \min(0.75 \cdot {r['d_cm']:.1f}\,\text{{cm}} ; 40\text{{cm}}) = \mathbf{{{r['s_max']:.1f} \, \text{{cm}}}}")
            
            st.write("Rozstaw obliczeniowy:")
            # Wzór = Podstawienie = Wynik
            st.latex(rf"s_{{cal}} = \frac{{A_{{sw,1}}}}{{a_{{sw,design}}}} = \frac{{ {r['Asw']:.2f}\,\text{{cm}}^2 }}{{ {r['a_sw_design']:.2f}\,\text{{cm}}^2/\text{{m}} }} = {r['s_cal']:.1f} \, \text{{cm}}")
            
            st.latex(rf"s = \min(s_{{cal}}, s_{{max}}) \rightarrow \mathbf{{{r['s']} \, \text{{cm}}}}")


def run():
    StronaScinanieBelki()


if __name__ == "__main__":
    run()