# ==============================================================================
# ZGINANIE BELKI – EC2 (PN-EN 1992-1-1)
# WERSJA REFERENCYJNA (PRODUKCYJNA)
# ==============================================================================
import streamlit as st
import math

# --- TABLICE ---
try:
    from TABLICE.ParametryBetonu import CONCRETE_TABLE, list_concrete_classes
    from TABLICE.ParametryStali import STEEL_TABLE
except Exception:
    st.error("Błąd importu TABLICE. Sprawdź pliki w folderze TABLICE.")
    st.stop()


def calculate_bending_ec2(
    concrete_name, 
    steel_name, 
    width_cm, 
    height_cm, 
    cover_nom_mm, 
    diameter_bar_mm, 
    diameter_stirrup_mm, 
    moment_ed_kNm, 
    moment_qp_kNm, 
    crack_limit_mm
):
    """
    Funkcja obliczeniowa (EC2) - wersja REFERENCYJNA.
    """
    
    # ---------------------------------------------------------
    # 0. ZABEZPIECZENIE DANYCH
    # ---------------------------------------------------------
    moment_qp_kNm = min(moment_qp_kNm, moment_ed_kNm)
    
    warnings = {
        "layers_exceeded": False,
        "compression_low": False,
        "max_reinforcement": False,
        "spacing_issue": False
    }

    # ---------------------------------------------------------
    # 1. DANE MATERIAŁOWE + AUTO-KOREKTA JEDNOSTEK
    # ---------------------------------------------------------
    concrete_props = CONCRETE_TABLE[concrete_name]
    steel_props = STEEL_TABLE[steel_name]

    GAMMA_C = 1.4   
    GAMMA_S = 1.15  
    ALPHA_CC = 1.0  
    
    # --- BETON ---
    raw_fck = concrete_props.fck
    raw_fctm = concrete_props.fctm
    raw_ecm = concrete_props.Ecm
    
    # Zabezpieczenie przed jednostkami w Pa
    if raw_fck > 200: fck = raw_fck / 1_000_000.0
    else: fck = raw_fck

    if raw_fctm > 200: fctm = raw_fctm / 1_000_000.0
    else: fctm = raw_fctm

    # Zabezpieczenie przed Ecm w MPa vs GPa
    if raw_ecm > 1000:
        ecm_modulus_mpa = raw_ecm
    else:
        ecm_modulus_mpa = raw_ecm * 1000.0
    
    fct_eff = fctm 
    fcd = (ALPHA_CC * fck) / GAMMA_C

    if fck <= 50:
        lambda_bet = 0.8
        eta_bet = 1.0
        eps_cu3 = 3.5 / 1000.0
    else:
        lambda_bet = 0.8 - (fck - 50) / 400
        eta_bet = 1.0 - (fck - 50) / 200
        eps_cu3 = (2.6 + 35 * ((90 - fck) / 100)**4) / 1000.0

    # --- STAL ---
    if isinstance(steel_props, dict):
        fyk = steel_props.get('fyk', 500)
        raw_es = steel_props.get('Es', 200)
    else:
        fyk = getattr(steel_props, 'fyk', 500)
        raw_es = getattr(steel_props, 'Es', 200)
    
    # Zabezpieczenie przed Es w MPa vs GPa
    if raw_es > 1000:
        es_modulus_mpa = raw_es
    else:
        es_modulus_mpa = raw_es * 1000.0

    fyd = fyk / GAMMA_S
    eps_yd = fyd / es_modulus_mpa
    alpha_e = es_modulus_mpa / ecm_modulus_mpa

    # ---------------------------------------------------------
    # 2. GEOMETRIA
    # ---------------------------------------------------------
    width_m = width_cm / 100.0
    height_m = height_cm / 100.0
    
    a1_m = (cover_nom_mm + diameter_stirrup_mm + diameter_bar_mm / 2.0) / 1000.0
    a2_m = a1_m 
    
    effective_depth_d = height_m - a1_m

    moment_ed_mnm = moment_ed_kNm / 1000.0
    moment_qp_mnm = moment_qp_kNm / 1000.0

    area_one_bar_cm2 = math.pi * (diameter_bar_mm/20)**2

    # ---------------------------------------------------------
    # KROK 1: OBLICZENIE As_SGN (Nośność)
    # ---------------------------------------------------------
    xi_lim = eps_cu3 / (eps_cu3 + eps_yd)
    omega_lim = lambda_bet * xi_lim
    mu_lim = omega_lim * (1 - 0.5 * omega_lim)
    
    denominator = eta_bet * fcd * width_m * effective_depth_d**2
    mu_ed = moment_ed_mnm / denominator

    area_s1_sgn_cm2 = 0.0
    area_s2_req_cm2 = 0.0
    sigma_s2_real = 0.0
    
    # Zmienne do raportowania
    is_doubly_reinforced = False
    zeta_val = 0.0
    z_arm_val = 0.0
    moment_rd_lim_val = 0.0
    
    # --- POJEDYNCZO ZBROJONY ---
    if mu_ed <= mu_lim:
        omega_req = 1 - math.sqrt(max(0, 1 - 2 * mu_ed))
        omega_req = min(omega_req, omega_lim)
        zeta = 1 - 0.5 * omega_req
        z_arm = zeta * effective_depth_d
        area_s1_req_m2 = moment_ed_mnm / (z_arm * fyd)
        area_s1_sgn_cm2 = area_s1_req_m2 * 10000
        
        # Raport
        zeta_val = zeta
        z_arm_val = z_arm

    # --- PODWÓJNIE ZBROJONY ---
    else:
        is_doubly_reinforced = True
        moment_rd_lim = mu_lim * denominator
        delta_moment = moment_ed_mnm - moment_rd_lim
        x_lim = xi_lim * effective_depth_d
        
        if x_lim > a2_m:
            eps_s2 = eps_cu3 * (x_lim - a2_m) / x_lim
            sigma_s2 = min(eps_s2 * es_modulus_mpa, fyd)
        else:
            sigma_s2 = 0.0 
        
        sigma_s2_real = sigma_s2
        effective_sigma_s2 = sigma_s2
        if sigma_s2 < 0.1 * fyd:
             warnings["compression_low"] = True
             effective_sigma_s2 = max(sigma_s2, 0.1 * fyd)

        area_s2_req_m2 = delta_moment / (effective_sigma_s2 * (effective_depth_d - a2_m))
        area_s2_req_cm2 = area_s2_req_m2 * 10000
        
        z_lim = effective_depth_d * (1 - 0.5 * omega_lim)
        area_s1_part1 = moment_rd_lim / (z_lim * fyd)
        area_s1_part2 = area_s2_req_m2 * (effective_sigma_s2 / fyd)
        area_s1_req_m2 = area_s1_part1 + area_s1_part2
        area_s1_sgn_cm2 = area_s1_req_m2 * 10000
        
        # Raport
        moment_rd_lim_val = moment_rd_lim
        z_arm_val = z_lim

    # Ostateczne zbrojenie (tylko ze statyki, bez warunku min)
    area_s1_sgn_final_cm2 = area_s1_sgn_cm2

    # ---------------------------------------------------------
    # KROK 2: OBLICZENIE As_SGU (Rysy) - METODA PRĘTOWA
    # ---------------------------------------------------------
    
    # Moment rysujący
    modulus_section_wc = (width_m * height_m**2) / 6.0
    moment_cracking = fct_eff * modulus_section_wc
    moment_cracking_kNm = moment_cracking * 1000.0

    def calculate_crack_width(area_steel_m2):
        if area_steel_m2 <= 1e-9: return 999.0

        # Faza II
        coeff_aa = 0.5 * width_m
        coeff_bb = alpha_e * area_steel_m2
        coeff_cc = -alpha_e * area_steel_m2 * effective_depth_d
        
        delta = coeff_bb**2 - 4 * coeff_aa * coeff_cc
        x_ii = (-coeff_bb + math.sqrt(delta)) / (2 * coeff_aa)

        inertia_ii = (width_m * x_ii**3) / 3 + alpha_e * area_steel_m2 * (effective_depth_d - x_ii)**2
        if inertia_ii == 0: return 0.0

        sigma_s = alpha_e * moment_qp_mnm * (effective_depth_d - x_ii) / inertia_ii

        hc_eff = min(2.5 * a1_m, (height_m - x_ii) / 3.0, height_m / 2.0)
        ac_eff = width_m * hc_eff
        rho_p_eff = area_steel_m2 / ac_eff if ac_eff > 0 else 0.0

        val_term = 0.4 * (fct_eff / rho_p_eff) * (1 + alpha_e * rho_p_eff)
        eps_diff = max(
            0.6 * sigma_s / es_modulus_mpa,
            (sigma_s - val_term) / es_modulus_mpa
        )

        # s_r,max
        area_one_bar_m2 = math.pi * (diameter_bar_mm / 2000.0)**2
        num_bars_real = max(2, math.ceil(area_steel_m2 / area_one_bar_m2))
        
        width_available = width_m - 2*(cover_nom_mm + diameter_stirrup_mm)/1000.0
        phi_m = diameter_bar_mm / 1000.0
        
        s_clear = (width_available - num_bars_real * phi_m) / (num_bars_real - 1)
        limit_spacing = 5 * (cover_nom_mm + diameter_bar_mm/2.0) / 1000.0
        
        if s_clear > limit_spacing:
            sr_max = 1.3 * (height_m - x_ii)
        else:
            k1, k2, k3, k4 = 0.8, 0.5, 3.4, 0.425
            sr_max = k3 * a1_m + k4 * k1 * k2 * phi_m / rho_p_eff

        return sr_max * eps_diff * 1000.0


    # --- PRZELICZENIE NA RZECZYWISTE PRĘTY (SGN) ---
    num_bars_sgn = math.ceil(area_s1_sgn_final_cm2 / area_one_bar_cm2)
    area_prov_sgn_cm2 = num_bars_sgn * area_one_bar_cm2
    
    # 1. Sprawdzamy rysę dla zbrojenia RZECZYWISTEGO z SGN
    wk_real_sgn = 0.0
    if moment_qp_mnm > moment_cracking:
        wk_real_sgn = calculate_crack_width(area_prov_sgn_cm2 / 10000.0)
    
    # 2. Dobór końcowy (Iteracyjnie dodajemy pręty jeśli rysa za duża)
    num_bars_final = num_bars_sgn
    wk_final = wk_real_sgn
    
    if moment_qp_mnm > moment_cracking:
        while wk_final > crack_limit_mm:
            num_bars_final += 1
            area_current_cm2 = num_bars_final * area_one_bar_cm2
            
            # Bezpiecznik: 4% zbrojenia
            if (area_current_cm2 / (width_cm * height_cm)) > 0.04:
                break
                
            wk_final = calculate_crack_width(area_current_cm2 / 10000.0)
    else:
        wk_final = 0.0

    area_prov_final_cm2 = num_bars_final * area_one_bar_cm2

    # --- SGU DEBUG DATA (Dla raportu) ---
    sgu_debug_data = {
        "x_ii": 0.0,
        "sigma_s": 0.0,
        "sr_max": 0.0,
        "eps_diff": 0.0,
        "is_cracked": (moment_qp_mnm > moment_cracking)
    }

    if sgu_debug_data["is_cracked"] and area_prov_final_cm2 > 0:
        # Przeliczenie raz jeszcze dla ostatecznego zbrojenia, aby wyciągnąć parametry
        area_steel_final_m2 = area_prov_final_cm2 / 10000.0
        
        coeff_aa = 0.5 * width_m
        coeff_bb = alpha_e * area_steel_final_m2
        coeff_cc = -alpha_e * area_steel_final_m2 * effective_depth_d
        
        delta = coeff_bb**2 - 4 * coeff_aa * coeff_cc
        x_ii_val = (-coeff_bb + math.sqrt(delta)) / (2 * coeff_aa)
        
        inertia_ii_val = (width_m * x_ii_val**3) / 3 + alpha_e * area_steel_final_m2 * (effective_depth_d - x_ii_val)**2
        
        if inertia_ii_val > 0:
            sigma_s_val = alpha_e * moment_qp_mnm * (effective_depth_d - x_ii_val) / inertia_ii_val
            
            # Parametry do wk
            hc_eff = min(2.5 * a1_m, (height_m - x_ii_val) / 3.0, height_m / 2.0)
            ac_eff = width_m * hc_eff
            rho_p_eff = area_steel_final_m2 / ac_eff if ac_eff > 0 else 0.0
            
            val_term = 0.4 * (fct_eff / rho_p_eff) * (1 + alpha_e * rho_p_eff)
            eps_diff_val = max(
                0.6 * sigma_s_val / es_modulus_mpa,
                (sigma_s_val - val_term) / es_modulus_mpa
            )

            # sr_max
            num_bars_final_calc = max(2, num_bars_final)
            width_available = width_m - 2*(cover_nom_mm + diameter_stirrup_mm)/1000.0
            phi_m = diameter_bar_mm / 1000.0
            s_clear = (width_available - num_bars_final_calc * phi_m) / (num_bars_final_calc - 1)
            limit_spacing = 5 * (cover_nom_mm + diameter_bar_mm/2.0) / 1000.0
            
            if s_clear > limit_spacing:
                sr_max_val = 1.3 * (height_m - x_ii_val)
            else:
                k1, k2, k3, k4 = 0.8, 0.5, 3.4, 0.425
                sr_max_val = k3 * a1_m + k4 * k1 * k2 * phi_m / rho_p_eff
                
            sgu_debug_data["x_ii"] = x_ii_val
            sgu_debug_data["sigma_s"] = sigma_s_val
            sgu_debug_data["sr_max"] = sr_max_val
            sgu_debug_data["eps_diff"] = eps_diff_val

    # --- WERYFIKACJA WARSTW I ODSTĘPU ---
    width_avail_cm = width_cm - 2*(cover_nom_mm + diameter_stirrup_mm)/10.0
    space_occupied = num_bars_final * (diameter_bar_mm/10.0) + (num_bars_final - 1) * max(2.0, diameter_bar_mm/10.0)
    
    s_clear_real_mm = 0.0
    if num_bars_final > 1:
        space_for_gaps_cm = width_avail_cm - (num_bars_final * (diameter_bar_mm/10.0))
        s_clear_cm = space_for_gaps_cm / (num_bars_final - 1)
        s_clear_real_mm = s_clear_cm * 10.0
    else:
        s_clear_real_mm = 999.0 

    if space_occupied > width_avail_cm:
        warnings["layers_exceeded"] = True

    if area_prov_final_cm2 > (0.04 * width_cm * height_cm):
        warnings["max_reinforcement"] = True

    if num_bars_final > num_bars_sgn:
        governing_case = "SGU (Zarysowanie)"
    else:
        governing_case = "SGN (Nośność)"

    return {
        "area_sgn": area_s1_sgn_final_cm2,
        "wk_final": wk_final,
        "wk_sgn_only": wk_real_sgn,
        "M_cr_kNm": moment_cracking_kNm,
        "area_s2_req": area_s2_req_cm2,
        "bar_count_final": num_bars_final,
        "bar_count_sgn": num_bars_sgn,
        "area_prov": area_prov_final_cm2,
        "governing_case": governing_case,
        "s_clear_real": s_clear_real_mm,
        "warnings": warnings,
        "debug": {
            "xi_lim": xi_lim,
            "omega_lim": omega_lim,
            "mu_ed": mu_ed,
            "Ecm_used_MPa": ecm_modulus_mpa,
            "Es_used_MPa": es_modulus_mpa,
            "alpha_e": alpha_e,
            "ALPHA_CC": ALPHA_CC,
            "GAMMA_C": GAMMA_C,
            "GAMMA_S": GAMMA_S,
            "fck": fck,
            "fyk": fyk,
            "fctm_val": fctm,
            # Dane do raportu SGN
            "fcd_val": fcd,
            "fyd_val": fyd,
            "d_val": effective_depth_d,
            "zeta_val": zeta_val,
            "z_arm_val": z_arm_val,
            "eta_bet": eta_bet,
            "is_doubly_reinforced": is_doubly_reinforced,
            "M_rd_lim": moment_rd_lim_val,
            "lambda_bet": lambda_bet,
            # Dane do raportu SGU
            "sgu": sgu_debug_data
        }
    }


def render_bending_page():

    # ------------------------------------------------------------------
    # STYL CSS
    # ------------------------------------------------------------------
    st.markdown(
        """
        <style>
        .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
        
        .result-card-main {
            background-color: #1e2329; 
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            margin-bottom: 20px;
        }
        
        .result-section-header {
            font-size: 1.1rem;
            font-weight: 600;
            color: #e5e7eb;
            margin-top: 20px;
            margin-bottom: 10px;
            padding-bottom: 5px;
        }
        
        .metric-box {
            background-color: #262730;
            padding: 10px;
            border-radius: 8px;
            border: 1px solid #3f3f46;
        }
        
        .res-label { font-size: 0.8rem; color: #9ca3af; text-transform: uppercase; margin-bottom: 2px; }
        .res-val { font-size: 1.1rem; font-weight: 700; color: #ffffff; }
        .res-unit { font-size: 0.9rem; color: #6b7280; font-weight: 400; }
        
        .status-ok { color: #22c55e; font-weight: bold; }
        .status-warn { color: #f59e0b; font-weight: bold; }
        </style>
        """,
        unsafe_allow_html=True
    )

    if "bending_calc_done" not in st.session_state:
        st.session_state.bending_calc_done = False
    
    if "results" not in st.session_state:
        st.session_state.results = None

    def reset_state():
        st.session_state.bending_calc_done = False
        st.session_state.results = None

    # ------------------------------------------------------------------
    # DANE WEJŚCIOWE
    # ------------------------------------------------------------------
    st.markdown("### DANE WEJŚCIOWE")

    col_concrete, col_steel, col_phi_s, col_phi_w = st.columns([1,1,0.5,0.5])      
    with col_concrete:
        concrete_name = st.selectbox("Klasa betonu", list_concrete_classes(), index=4, key="inp_bending_concrete", on_change=reset_state)
    with col_steel:
        steel_name = st.selectbox("Klasa stali zbrojeniowej", list(STEEL_TABLE.keys()), index=1, key="inp_bending_steel", on_change=reset_state)
    with col_phi_s:
        diameter_bar_mm = st.selectbox("Średnica prętów $\\phi_s$ [mm]", [8, 10, 12, 16, 18, 20, 22, 25, 32], index=3, key="inp_bending_phi_s", on_change=reset_state)   
    with col_phi_w:
        diameter_stirrup_mm = st.selectbox("Średnica strzemion $\\phi_w$ [mm]", [6, 8, 10, 12, 16], index=1, key="inp_bending_phi_w", on_change=reset_state)
        

    col_dim_b, col_dim_h, col_cover = st.columns(3)
    with col_dim_b:
        width_cm = st.number_input("Szerokość belki $b$ [cm]", value=30.0, step=1.0, key="inp_bending_b", on_change=reset_state)
    with col_dim_h:
        height_cm = st.number_input("Wysokość belki $h$ [cm]", value=50.0, step=1.0, key="inp_bending_h", on_change=reset_state) 
    with col_cover:
        cover_nom_mm = st.number_input("Otulina zbrojenia $c_{nom}$ [mm]", value=30, step=5, key="inp_bending_cnom", on_change=reset_state) 

    col_med, col_mqp, col_wk = st.columns(3)    
    with col_med:
        moment_ed_kNm = st.number_input("Moment obliczeniowy $M_{Ed}$ [kNm]", value=150.0, step=1.0, key="inp_bending_med", on_change=reset_state)
    
    with col_mqp:
        if "inp_bending_mqp" in st.session_state:
            if st.session_state.inp_bending_mqp > moment_ed_kNm:
                st.session_state.inp_bending_mqp = moment_ed_kNm
        
        moment_qp_kNm = st.number_input("Moment quasi-stały $M_{qp}$ [kNm]", value=min(110.0, moment_ed_kNm), max_value=moment_ed_kNm, step=1.0, key="inp_bending_mqp", on_change=reset_state) 
        
    with col_wk:
        crack_limit_mm = st.selectbox("Dopuszczalna szerokość rozwarcia rysy $w_{lim}$ [mm]", [0.1, 0.2, 0.3, 0.4], index=2, key="inp_bending_wk", on_change=reset_state)    

    # ------------------------------------------------------------------
    # PRZYCISK OBLICZ
    # ------------------------------------------------------------------
    _, col_btn, _ = st.columns([1, 2, 1])
    with col_btn:
        calc_button = st.button("OBLICZ", type="primary", use_container_width=True, key="btn_calc_bending")

    if calc_button:
        results_data = calculate_bending_ec2(
            concrete_name, 
            steel_name, 
            width_cm, 
            height_cm, 
            cover_nom_mm, 
            diameter_bar_mm, 
            diameter_stirrup_mm, 
            moment_ed_kNm, 
            moment_qp_kNm, 
            crack_limit_mm
        )
        st.session_state.results = results_data
        st.session_state.bending_calc_done = True

    # ------------------------------------------------------------------
    # WYNIKI
    # ------------------------------------------------------------------
    if st.session_state.bending_calc_done and st.session_state.results:
        res = st.session_state.results
        dbg = res['debug']
        warns = res['warnings']
        
        st.markdown("### WYNIKI OBLICZEŃ")
        
        # --- 1. KARTA GŁÓWNA ---
        COLOR_GREEN = "#22c55e"
        main_border = COLOR_GREEN
        
        st.markdown(
            f"""
            <div class="result-card-main" style="border-left: 6px solid {main_border};">
                <div class="res-label">DOBRANE ZBROJENIE (WYNIK KOŃCOWY)</div>
                <div style="font-size: 2.5rem; font-weight: 800; color: #ffffff; margin: 5px 0;">
                    {res['bar_count_final']} szt. ⌀{diameter_bar_mm}
                </div>
                <div style="color: #9ca3af; margin-bottom: 15px;">
                    A<sub>s,prov</sub> = {res['area_prov']:.2f} <span class="res-unit">cm²</span>
                    <span style="margin-left: 15px; color: {main_border}; font-weight: bold;">Decyduje: {res['governing_case']}</span>
                </div>
                <div style="font-size: 0.85rem; color: #6b7280; border-top: 1px solid #374151; padding-top: 10px; font-style: italic;">
                    ℹ️ Podana wartość wynika z obliczeń statycznych (SGN i SGU). Należy dodatkowo zweryfikować zbrojenie minimalne belki według odrębnego modułu.
                </div>
            </div>
            """, 
            unsafe_allow_html=True
        )

        # --- 2. ANALIZA SGN ---
        st.markdown('<div class="result-section-header">ANALIZA STANU GRANICZNEGO NOŚNOŚCI</div>', unsafe_allow_html=True)
        c_sgn1, c_sgn2 = st.columns(2)
        with c_sgn1:
            st.markdown(f"""
            <div class="metric-box" style="border-left: 3px solid #22c55e;">
                <div class="res-label">WYMAGANE ZBROJENIE ZE WZGLĘDU NA SGN</div>
                <div class="res-val">A<sub>s,SGN</sub> = {res['area_sgn']:.2f} cm²</div>
            </div>
            """, unsafe_allow_html=True)
        with c_sgn2:
            st.markdown(f"""
            <div class="metric-box">
                <div class="res-label">ILOŚĆ PRĘTÓW SPEŁNIAJĄCA WARUNEK SGN</div>
                <div class="res-val">{res['bar_count_sgn']} szt. ⌀{diameter_bar_mm}</div>
            </div>
            """, unsafe_allow_html=True)

        if res['area_s2_req'] > 0:
            st.error(f"⚠️ Wymagane dodatkowo zbrojenie ściskane $A_{{s2}} = {res['area_s2_req']:.2f}$ cm²")

        # --- 3. ANALIZA SGU ---
        st.markdown(
            f'<div class="result-section-header">ANALIZA STANU GRANICZNEGO UŻYTKOWALNOŚCI (ZARYSOWANIE) <span style="font-size:0.9rem; color:#6b7280; font-weight:400; margin-left:10px;">(M<sub>cr</sub> = {res["M_cr_kNm"]:.1f} kNm)</span></div>', 
            unsafe_allow_html=True
        )
        
        if moment_qp_kNm <= res["M_cr_kNm"]:
            st.success(f"✅ Przekrój niezarysowany ($M_{{qp}} \le M_{{cr}}$). Szerokość rysy $w_k = 0.00$ mm.")
        else:
            c_sgu1, c_sgu2 = st.columns(2)
            
            with c_sgu1:
                wk_sgn = res['wk_sgn_only']
                color_sgn_wk = "#22c55e" if wk_sgn <= crack_limit_mm else "#ef4444"
                status_sgn = "Warunek spełniony" if wk_sgn <= crack_limit_mm else "Warunek niespełniony 👉"
                
                st.markdown(f"""
                <div class="metric-box" style="border-left: 3px solid {color_sgn_wk};">
                    <div class="res-label">SZEROKOŚĆ ROZWARCIA RYSY PRZY ZBROJENIU SGN ({res['bar_count_sgn']} szt. ⌀{diameter_bar_mm})</div>
                    <div class="res-val">
                        w<sub>k</sub> = {wk_sgn:.3f} mm
                        <span style="font-size: 0.75em; margin-left: 10px; color: {color_sgn_wk}; font-weight: 600;">{status_sgn}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with c_sgu2:
                if wk_sgn <= crack_limit_mm:
                    st.info("ℹ️ Zbrojenie z SGN wystarcza do ograniczenia zarysowania.")
                else:
                    wk_final = res['wk_final']
                    st.markdown(f"""
                    <div class="metric-box" style="border-left: 3px solid #22c55e;">
                        <div class="res-label">ILOŚĆ PRĘTÓW SPEŁNIAJĄCA WARUNEK SGU (ZARYSOWANIE)</div>
                        <div class="res-val" style="font-size: 1.1rem;">
                            {res['bar_count_final']} szt. ⌀{diameter_bar_mm} &rArr; w<sub>k</sub> = {wk_final:.3f} mm
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        # 4. OSTRZEŻENIA
        if warns['compression_low']:
            st.warning("⚠️ **SGN:** Zbrojenie ściskane jest słabo wykorzystane ($\sigma_{s2} < 0.1 f_{yd}$). Zwiększ wysokość przekroju lub otulinę.")

        if warns['max_reinforcement']:
            st.warning("⚠️ **KONSTR:** Przekroczono 4% stopnia zbrojenia. Problemy z betonowaniem!")

        if warns['layers_exceeded']:
            st.markdown("")
            st.warning(f"⚠️ SGU: Liczba prętów prawdopodobnie nie zmieści się w jednej warstwie (szacowany odstęp w świetle: $s_{{clear}} \\approx {res['s_clear_real']:.1f}$ mm). Model SGU może być niedokładny.")
        
        st.markdown("")
        # 5. DEBUG
        with st.expander("🔍 Szczegóły obliczeń"):
            st.markdown("#### 1. Podstawowe dane")
            st.latex(f"b = {width_cm} \\text{{ cm}}, \\quad h = {height_cm} \\text{{ cm}}, \\quad c_{{nom}} = {cover_nom_mm} \\text{{ mm}}, \\quad \\phi_s = {diameter_bar_mm} \\text{{ mm}}, \\quad \\phi_w = {diameter_stirrup_mm} \\text{{ mm}}")
            st.latex(f"Beton: {concrete_name} => f_{{ck}} = {CONCRETE_TABLE[concrete_name].fck:.1f} \\text{{ MPa}}, \\quad Stal: {steel_name} => f_{{yk}} = {STEEL_TABLE[steel_name].fyk:.0f} \\text{{ MPa}}")
            st.latex(f"M_{{Ed}} = {moment_ed_kNm:.2f} \\text{{ kNm}}, \\quad M_{{qp}} = {moment_qp_kNm:.2f} \\text{{ kNm}}")
            st.markdown("#### 2. Wyniki obliczeń")
            
            # 2.1 d
            d_val_m = dbg['d_val']
            d_val_cm = d_val_m * 100
            st.markdown("##### 2.1 Wysokość użyteczna przekroju")
            st.latex(
                r"d = h - c_{nom} - \phi_w - \frac{\phi_s}{2}"
                f" = {height_cm} \\text{{ cm}} - {cover_nom_mm/10} \\text{{ cm}} - {diameter_stirrup_mm/10} \\text{{ cm}} - \\frac{{{diameter_bar_mm/10}}}{{2}} \\text{{ cm}} = {d_val_cm:.2f} \\text{{ cm}}"
            )
            # 2.2 Wytrzymałości
            st.markdown("##### 2.2 Wytrzymałość obliczeniowa materiałów")
            fcd_val = dbg['fcd_val']
            fyd_val = dbg['fyd_val']
            st.latex(
                rf"f_{{cd}} = \frac{{\alpha_{{cc}} f_{{ck}}}}{{\gamma_c}}"
                rf" = \frac{{{dbg['ALPHA_CC']:.2f}\cdot {dbg['fck']:.1f}\,\text{{MPa}}}}{{{dbg['GAMMA_C']:.2f}}}"
                rf" = {fcd_val:.2f}\,\text{{MPa}}"
            )
            st.latex(
                rf"f_{{yd}} = \frac{{f_{{yk}}}}{{\gamma_s}}"
                rf" = \frac{{{dbg['fyk']:.1f}\,\text{{MPa}}}}{{{dbg['GAMMA_S']:.2f}}}"
                rf" = {dbg['fyd_val']:.2f}\,\text{{MPa}}"
            )

            # 2.3 SGN
            st.markdown("##### 2.3 Wymagane zbrojenie (SGN)")
            mu_ed = dbg['mu_ed']
            eta_bet = dbg['eta_bet']
            omega_lim = dbg['omega_lim']
            fcd_MN = fcd_val 
            width_m = width_cm / 100.0
            
            # Obliczenie mu_lim z omega_lim (dla celów prezentacji)
            mu_lim_calc = omega_lim * (1 - 0.5 * omega_lim)
            
            # 1. Względny moment zginający
            st.latex(f"\\mu_{{Ed}} = \\frac{{M_{{Ed}}}}{{b d^2 \\eta f_{{cd}}}} = \\frac{{{moment_ed_kNm * 0.001:.4f} \\text{{ MNm}}}}{{{width_m:.2f} \\text{{ m}} \\cdot ({d_val_m:.3f} \\text{{ m}})^2 \\cdot {eta_bet:.1f} \\cdot {fcd_MN:.2f} \\text{{ MPa}}}} = {mu_ed:.4f}")

            # 2. Graniczny względny moment zginający
            st.latex(f"\\mu_{{lim}} = \\omega_{{lim}} (1 - 0.5 \\omega_{{lim}}) = {omega_lim:.4f} \\cdot (1 - 0.5 \\cdot {omega_lim:.4f}) = {mu_lim_calc:.4f}")

            if not dbg['is_doubly_reinforced']:
                # Pojedynczo zbrojona
                zeta = dbg['zeta_val']
                z_arm = dbg['z_arm_val']
                area_req_m2 = res['area_sgn'] / 10000.0
                
                st.latex(f"\\mu_{{Ed}} \\le \\mu_{{lim}} \\implies \\text{{przekrój pojedynczo zbrojony}}")
                st.latex(f"\\zeta = 1 - 0.5 (1 - \\sqrt{{1 - 2 \\mu_{{Ed}}}}) = 1 - 0.5 (1 - \\sqrt{{1 - 2 \\cdot {mu_ed:.4f}}}) = {zeta:.4f}")
                st.latex(f"z = \\zeta \\cdot d = {zeta:.4f} \\cdot {d_val_cm:.2f} \\text{{ cm}} = {z_arm*100:.2f} \\text{{ cm}}")
                st.latex(f"A_{{s1,req}} = \\frac{{M_{{Ed}}}}{{z \\cdot f_{{yd}}}} = \\frac{{{moment_ed_kNm * 0.001:.4f} \\text{{ MNm}}}}{{{z_arm:.4f} \\text{{ m}} \\cdot {fyd_val:.2f} \\text{{ MPa}}}} = {res['area_sgn']:.2f} \\text{{ cm}}^2")
            else:
                # Podwójnie zbrojona
                m_rd_lim = dbg['M_rd_lim']
                delta_m = (moment_ed_kNm * 0.001) - m_rd_lim
                area_s2 = res['area_s2_req']
                area_s1 = res['area_sgn']
                d_2_m = a1_m 
                
                st.latex(f"\\mu_{{Ed}} > \\mu_{{lim}} \\implies \\text{{przekrój podwójnie zbrojony}}")
                st.latex(f"M_{{Rd,lim}} = \\mu_{{lim}} b d^2 \\eta f_{{cd}} = {m_rd_lim*1000:.1f} \\text{{ kNm}}")
                st.latex(f"\\Delta M = M_{{Ed}} - M_{{Rd,lim}} = {moment_ed_kNm:.1f} - {m_rd_lim*1000:.1f} = {delta_m*1000:.1f} \\text{{ kNm}}")
                st.latex(f"A_{{s2,req}} = \\frac{{\\Delta M}}{{\\sigma_{{s2}} (d - d_2)}} = \\frac{{{delta_m:.4f} \\text{{ MNm}}}}{{{fcd_MN:.2f} \\text{{ MPa}} \\cdot ({d_val_m:.3f} - {d_2_m:.3f}) \\text{{ m}}}} = {area_s2:.2f} \\text{{ cm}}^2")
                st.latex(f"A_{{s1,req}} = \\frac{{M_{{Rd,lim}}}}{{z_{{lim}} f_{{yd}}}} + A_{{s2,req}} \\frac{{\\sigma_{{s2}}}}{{f_{{yd}}}} = {area_s1:.2f} \\text{{ cm}}^2")
            
            # 2.4 SGU
            st.markdown("##### 2.4 Stan Graniczny Użytkowalności (SGU)")
            sgu = dbg['sgu']
            m_cr = res['M_cr_kNm']
            fctm_val = dbg['fctm_val']
            width_m = width_cm / 100.0
            height_m = height_cm / 100.0
            
            # Wzór na Wc i M_cr
            W_c_m3 = (width_m * height_m**2) / 6.0
            
            st.latex(f"W_c = \\frac{{b h^2}}{{6}} = \\frac{{{width_m:.2f} \\text{{ m}} \\cdot ({height_m:.2f} \\text{{ m}})^2}}{{6}} = {W_c_m3:.4f} \\text{{ m}}^3")
            st.latex(f"M_{{cr}} = f_{{ctm}} \\cdot W_c = {fctm_val:.2f} \\text{{ MPa}} \\cdot {W_c_m3:.4f} \\text{{ m}}^3 \\cdot 1000 = {m_cr:.2f} \\text{{ kNm}}")
            
            if not sgu['is_cracked']:
                st.markdown(f"**Przekrój niezarysowany** ($M_{{qp}} < M_{{cr}}$)")
                st.latex(r"w_k = 0.00 \text{ mm}")
            else:
                st.markdown(f"**Przekrój zarysowany** ($M_{{qp}} \ge M_{{cr}}$)")
                
                # --- 1. Współczynnik ekwiwalentności (Alpha_e) ---
                alpha_e = dbg['alpha_e']
                Es_MPa = dbg['Es_used_MPa']
                Ecm_MPa = dbg['Ecm_used_MPa']
                
                st.latex(f"\\alpha_e = \\frac{{E_s}}{{E_{{cm}}}} = \\frac{{{Es_MPa:.0f} \\text{{ MPa}}}}{{{Ecm_MPa:.0f} \\text{{ MPa}}}} = {alpha_e:.2f}")
                
                # --- 2. Wysokość strefy ściskanej (x_II) ---
                area_prov_m2 = res['area_prov'] / 10000.0
                d_val_m = dbg['d_val']
                x_ii_m = sgu['x_ii']
                x_ii_cm = x_ii_m * 100
                
                st.latex(f"A_{{s,prov}} = {res['area_prov']:.2f} \\text{{ cm}}^2 = {area_prov_m2 * 10000:.2f} \\cdot 10^{{-4}} \\text{{ m}}^2")
                
                st.markdown("Wysokość strefy ściskanej $x_{II}$ (z rozwiązania równania kwadratowego momentów statycznych):")
                st.latex(r"x_{II} = \frac{-\alpha_e A_s + \sqrt{(\alpha_e A_s)^2 + 2 b \alpha_e A_s d}}{b}")
                
                # Formatowanie As we wzorze: zamiana 0.00xxxx na xx.xx * 10^-4
                as_formatted = f"{area_prov_m2 * 10000:.2f} \\cdot 10^{{-4}}"
                
                # WZÓR NA x_II Z PEŁNYMI JEDNOSTKAMI
                st.latex(
                    f"x_{{II}} = \\frac{{-{alpha_e:.2f} \\cdot {as_formatted} \\text{{ m}}^2 + \\sqrt{{({alpha_e:.2f} \\cdot {as_formatted} \\text{{ m}}^2)^2 + 2 \\cdot {width_m:.2f} \\text{{ m}} \\cdot {alpha_e:.2f} \\cdot {as_formatted} \\text{{ m}}^2 \\cdot {d_val_m:.3f} \\text{{ m}}}}}}{{{width_m:.2f} \\text{{ m}}}}"
                    f" = {x_ii_m:.4f} \\text{{ m}}"                
                ) 
                
                # --- 3. Moment bezwładności (I_II) ---
                # Obliczenie lokalne dla wyświetlenia podstawienia
                I_ii = (width_m * x_ii_m**3)/3.0 + alpha_e * area_prov_m2 * (d_val_m - x_ii_m)**2
                
                st.latex(
                    f"I_{{II}} = \\frac{{b x_{{II}}^3}}{{3}} + \\alpha_e A_s (d - x_{{II}})^2"
                    f" = \\frac{{{width_m:.2f} \\text{{ m}} \\cdot ({x_ii_m:.3f} \\text{{ m}})^3}}{{3}} + {alpha_e:.2f} \\cdot {as_formatted} \\text{{ m}}^2 \\cdot ({d_val_m:.3f} \\text{{ m}} - {x_ii_m:.3f} \\text{{ m}})^2 = {I_ii:.6f} \\text{{ m}}^4"
                )
                
                # --- 4. Naprężenia w stali (Sigma_s) ---
                sigma_s = sgu['sigma_s']
                M_qp_MNm = moment_qp_kNm * 0.001
                st.latex(f"\\sigma_s = \\alpha_e \\frac{{M_{{qp}}}}{{I_{{II}}}} (d - x_{{II}}) = {alpha_e:.2f} \\cdot \\frac{{{M_qp_MNm:.4f} \\text{{ MNm}}}}{{{I_ii:.6f} \\text{{ m}}^4}} \\cdot ({d_val_m:.3f} \\text{{ m}} - {x_ii_m:.3f} \\text{{ m}}) = {sigma_s:.2f} \\text{{ MPa}}")
                
                # --- 5. Szerokość rysy (w_k) ---
                sr_max = sgu['sr_max'] * 1000 # mm
                eps_diff = sgu['eps_diff']
                wk_val = res['wk_final']
                
                st.latex(f"w_k = s_{{r,max}} (\\varepsilon_{{sm}} - \\varepsilon_{{cm}}) = {sr_max:.1f} \\text{{ mm}} \\cdot {eps_diff:.5f} = {wk_val:.3f} \\text{{ mm}}")



            # 2.5 ZBROJENIE KOŃCZOWE
            st.markdown("##### 2.5. Zbrojenie końcowe")
            governing = res['governing_case']
            
            if "SGN" in governing:
                st.markdown(f"Decyduje warunek **{governing}**.")
                st.latex(f"A_{{s,prov}} = {res['bar_count_sgn']} \\cdot \\phi {diameter_bar_mm} = {res['area_prov']:.2f} \\text{{ cm}}^2")
            else:
                st.markdown(f"Decyduje warunek **{governing}** (zwiększono zbrojenie względem SGN).")
                st.latex(f"A_{{s,prov}} = {res['bar_count_final']} \\cdot \\phi {diameter_bar_mm} = {res['area_prov']:.2f} \\text{{ cm}}^2")



def run():
    render_bending_page()

if __name__ == "__main__":
    run()