# ==============================================================================
# WYMIAROWANIE PŁYTY NA ZGINANIE – EC2
# WERSJA: PŁYTA (b = 100 cm, wynik w rozstawie prętów)
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


def calculate_slab_bending_ec2(
    concrete_name, 
    steel_name, 
    height_cm, 
    cover_nom_mm, 
    diameter_bar_mm, 
    layer_type, 
    moment_ed_kNm, 
    moment_qp_kNm, 
    crack_limit_mm
):
    """
    Funkcja obliczeniowa dla PŁYTY (EC2).
    Szerokość b przyjęta na sztywno 100 cm.
    Wynik podawany jako rozstaw prętów co 1 cm.
    """
    
    # ---------------------------------------------------------
    # 0. STAŁE I ZABEZPIECZENIA
    # ---------------------------------------------------------
    width_cm = 100.0  # Płyta obliczana na pasmo 1 m
    width_m = 1.0
    
    moment_qp_kNm = min(moment_qp_kNm, moment_ed_kNm)
    
    warnings = {
        "compression_low": False,
        "max_reinforcement": False,
        "spacing_too_small": False,
        "spacing_info": ""
    }

    # ---------------------------------------------------------
    # 1. DANE MATERIAŁOWE
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
    
    if raw_fck > 200: fck = raw_fck / 1_000_000.0
    else: fck = raw_fck

    if raw_fctm > 200: fctm = raw_fctm / 1_000_000.0
    else: fctm = raw_fctm

    if raw_ecm > 1000: ecm_modulus_mpa = raw_ecm
    else: ecm_modulus_mpa = raw_ecm * 1000.0
    
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
    
    if raw_es > 1000: es_modulus_mpa = raw_es
    else: es_modulus_mpa = raw_es * 1000.0

    fyd = fyk / GAMMA_S
    eps_yd = fyd / es_modulus_mpa
    alpha_e = es_modulus_mpa / ecm_modulus_mpa

    # ---------------------------------------------------------
    # 2. GEOMETRIA
    # ---------------------------------------------------------
    height_m = height_cm / 100.0
    
    # Obliczenie a1 (odległość osi pręta od krawędzi)
    # Warstwa 1: c + phi/2
    # Warstwa 2: c + phi + phi/2 (zakładając siatkę z prętów o tej samej średnicy)
    
    dist_to_axis_mm = cover_nom_mm + diameter_bar_mm / 2.0
    if layer_type == "2-ga warstwa":
        dist_to_axis_mm += diameter_bar_mm
        
    a1_m = dist_to_axis_mm / 1000.0
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
    
    is_doubly_reinforced = False
    zeta_val = 0.0
    z_arm_val = 0.0
    moment_rd_lim_val = 0.0
    
    # --- POJEDYNCZO ZBROJONA ---
    if mu_ed <= mu_lim:
        omega_req = 1 - math.sqrt(max(0, 1 - 2 * mu_ed))
        omega_req = min(omega_req, omega_lim)
        zeta = 1 - 0.5 * omega_req
        z_arm = zeta * effective_depth_d
        area_s1_req_m2 = moment_ed_mnm / (z_arm * fyd)
        area_s1_sgn_cm2 = area_s1_req_m2 * 10000
        
        zeta_val = zeta
        z_arm_val = z_arm

    # --- PODWÓJNIE ZBROJONA ---
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
        
        moment_rd_lim_val = moment_rd_lim
        z_arm_val = z_lim

    # Ostateczne zbrojenie ze statyki (bez min)
    area_s1_sgn_final_cm2 = area_s1_sgn_cm2
    
    # Obliczamy rozstaw SGN z ograniczeniem do praktycznego minimum 3 cm
    if area_s1_sgn_final_cm2 > 0:
        s_sgn_cm = math.floor((100.0 * area_one_bar_cm2) / area_s1_sgn_final_cm2)
    else:
        s_sgn_cm = 40
    s_sgn_cm = max(3, min(s_sgn_cm, 40))

    # ---------------------------------------------------------
    # KROK 2: DOBÓR ROZSTAWU (SGN + SGU)
    # ---------------------------------------------------------
    
    # Moment rysujący
    modulus_section_wc = (width_m * height_m**2) / 6.0
    moment_cracking = fct_eff * modulus_section_wc
    moment_cracking_kNm = moment_cracking * 1000.0

    # Funkcja pomocnicza: parametry rysy
    def calculate_crack_width(area_steel_m2, spacing_cm):
        if area_steel_m2 <= 1e-9: return 999.0, 0, 0, 0, 0

        # Faza II
        coeff_aa = 0.5 * width_m
        coeff_bb = alpha_e * area_steel_m2
        coeff_cc = -alpha_e * area_steel_m2 * effective_depth_d
        
        delta = coeff_bb**2 - 4 * coeff_aa * coeff_cc
        x_ii = (-coeff_bb + math.sqrt(delta)) / (2 * coeff_aa)

        inertia_ii = (width_m * x_ii**3) / 3 + alpha_e * area_steel_m2 * (effective_depth_d - x_ii)**2
        if inertia_ii == 0: return 0.0, 0, 0, 0, 0

        sigma_s = alpha_e * moment_qp_mnm * (effective_depth_d - x_ii) / inertia_ii

        hc_eff = min(2.5 * a1_m, (height_m - x_ii) / 3.0, height_m / 2.0)
        ac_eff = width_m * hc_eff
        rho_p_eff = area_steel_m2 / ac_eff if ac_eff > 0 else 0.0

        val_term = 0.4 * (fct_eff / rho_p_eff) * (1 + alpha_e * rho_p_eff)
        eps_diff = max(
            0.6 * sigma_s / es_modulus_mpa,
            (sigma_s - val_term) / es_modulus_mpa
        )

        # s_r,max dla płyty zależny od rozstawu s
        s_curr = spacing_cm
        s_clear_m = (s_curr * 10.0 - diameter_bar_mm) / 1000.0
        c_m = cover_nom_mm / 1000.0
        phi_m = diameter_bar_mm / 1000.0
        limit_spacing_m = 5.0 * (c_m + phi_m/2.0)
        
        if s_clear_m > limit_spacing_m:
             sr_max_val = 1.3 * (height_m - x_ii)
        else:
             k1, k2, k3, k4 = 0.8, 0.5, 3.4, 0.425
             sr_max_val = k3 * c_m + k4 * k1 * k2 * phi_m / rho_p_eff
        
        wk = sr_max_val * eps_diff * 1000.0
        
        return wk, x_ii, sigma_s, sr_max_val, eps_diff

    # 1. Sprawdzenie SGU dla rozstawu SGN
    area_sgn_prov_cm2 = (100.0 / s_sgn_cm) * area_one_bar_cm2
    is_cracked = (moment_qp_mnm > moment_cracking)
    wk_sgn_only = 0.0
    
    if is_cracked:
        wk_sgn_only, _, _, _, _ = calculate_crack_width(area_sgn_prov_cm2 / 10000.0, s_sgn_cm)

    # 2. Iteracja (jeśli SGN nie wystarcza)
    final_s_cm = s_sgn_cm
    final_wk = wk_sgn_only
    found_spacing = False
    
    # Przechowywanie danych SGU dla ostatecznego wyboru
    sgu_results = {
        "x_ii": 0.0, "sigma_s": 0.0, "sr_max": 0.0, "eps_diff": 0.0, "wk": 0.0
    }
    
    if wk_sgn_only > crack_limit_mm and is_cracked:
        for s_curr in range(s_sgn_cm, 2, -1):
             area_curr_cm2 = (100.0 / s_curr) * area_one_bar_cm2
             wk_curr, x_ii, sig_s, sr, eps = calculate_crack_width(area_curr_cm2 / 10000.0, s_curr)
             
             if wk_curr <= crack_limit_mm:
                 final_s_cm = s_curr
                 final_wk = wk_curr
                 sgu_results = {"x_ii": x_ii, "sigma_s": sig_s, "sr_max": sr, "eps_diff": eps, "wk": wk_curr}
                 found_spacing = True
                 break
        if not found_spacing:
            final_s_cm = 3
            final_wk = wk_curr 
    else:
        final_s_cm = s_sgn_cm
        final_wk = wk_sgn_only
        if is_cracked:
             _, x_ii, sig_s, sr, eps = calculate_crack_width(area_sgn_prov_cm2 / 10000.0, s_sgn_cm)
             sgu_results = {"x_ii": x_ii, "sigma_s": sig_s, "sr_max": sr, "eps_diff": eps, "wk": wk_sgn_only}
            
    # Obliczenie ostatecznych parametrów dla wybranego 's'
    area_prov_final_cm2 = (100.0 / final_s_cm) * area_one_bar_cm2
    
    s_clear_mm = (final_s_cm * 10.0) - diameter_bar_mm
    min_clear_norm_mm = max(20.0, diameter_bar_mm)
    
    if s_clear_mm < min_clear_norm_mm:
        warnings["spacing_too_small"] = True
        warnings["spacing_info"] = f"Rozstaw w świetle {s_clear_mm:.1f} mm < {min_clear_norm_mm:.0f} mm (normowe minimum)."

    if area_prov_final_cm2 > (0.04 * 100.0 * height_cm):
        warnings["max_reinforcement"] = True

    if final_s_cm < s_sgn_cm:
        governing_case = "SGU (Zarysowanie)"
    else:
        governing_case = "SGN (Nośność)"

    return {
        "area_sgn": area_s1_sgn_final_cm2,
        "wk_final": final_wk,
        "wk_sgn_only": wk_sgn_only,
        "M_cr_kNm": moment_cracking_kNm,
        "area_s2_req": area_s2_req_cm2,
        
        "spacing_final": final_s_cm,
        "spacing_sgn": s_sgn_cm,
        "area_prov": area_prov_final_cm2,
        
        "governing_case": governing_case,
        "warnings": warnings,
        "debug": {
            "xi_lim": xi_lim,
            "omega_lim": omega_lim,
            "mu_ed": mu_ed,
            "Ecm_used_MPa": ecm_modulus_mpa,
            "Es_used_MPa": es_modulus_mpa,
            "alpha_e": alpha_e,
            # Dane do raportu SGN
            "fcd_val": fcd,
            "fyd_val": fyd,
            "fctm_val": fctm,
            "d_val": effective_depth_d,
            "a2_val": a2_m,
            "zeta_val": zeta_val,
            "z_arm_val": z_arm_val,
            "eta_bet": eta_bet,
            "is_doubly_reinforced": is_doubly_reinforced,
            "M_rd_lim": moment_rd_lim_val,
            "lambda_bet": lambda_bet,
            # Dane do raportu SGU
            "sgu": {
                "is_cracked": (moment_qp_mnm > moment_cracking),
                "x_ii": sgu_results["x_ii"],
                "sigma_s": sgu_results["sigma_s"],
                "sr_max": sgu_results["sr_max"],
                "eps_diff": sgu_results["eps_diff"]
            }
        }
    }


def render_slab_page():

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

    if "slab_calc_done" not in st.session_state:
        st.session_state.slab_calc_done = False
    
    if "slab_results" not in st.session_state:
        st.session_state.slab_results = None

    def reset_state():
        st.session_state.slab_calc_done = False
        st.session_state.slab_results = None

    # ------------------------------------------------------------------
    # DANE WEJŚCIOWE
    # ------------------------------------------------------------------
    st.markdown("### DANE WEJŚCIOWE")

    col_concrete, col_steel, col_dim_h = st.columns([1,1,1])      
    with col_concrete:
        concrete_name = st.selectbox("Klasa betonu", list_concrete_classes(), index=4, key="inp_slab_concrete", on_change=reset_state)
    with col_steel:
        steel_name = st.selectbox("Klasa stali zbrojeniowej", list(STEEL_TABLE.keys()), index=1, key="inp_slab_steel", on_change=reset_state)
    with col_dim_h:
        height_cm = st.number_input("Grubość płyty $h$ [cm]", value=20.0, step=1.0, key="inp_slab_h", on_change=reset_state) 
      
    col_phi_s, col_layer, col_cover = st.columns(3)
    with col_phi_s:
        diameter_bar_mm = st.selectbox("Średnica prętów $\\phi_s$ [mm]", [8, 10, 12, 16, 18, 20, 22, 25], index=2, key="inp_slab_phi_s", on_change=reset_state)   
    with col_layer:
        layer_type = st.selectbox("Warstwa zbrojenia", ["1-sza warstwa", "2-ga warstwa"], index=0, key="inp_slab_layer", 
                                  help="1-sza warstwa oznacza warstwę bliżej krawędzi betonu.", on_change=reset_state)
    with col_cover:
        cover_nom_mm = st.number_input("Otulina zbrojenia $c_{nom}$ [mm]", value=25, step=5, key="inp_slab_cnom", on_change=reset_state) 

    col_med, col_mqp, col_wk = st.columns(3)    
    with col_med:
        moment_ed_kNm = st.number_input("Moment obliczeniowy $M_{Ed}$ [kNm/m]", value=40.0, step=1.0, key="inp_slab_med", on_change=reset_state)
    
    with col_mqp:
        if "inp_slab_mqp" in st.session_state:
            if st.session_state.inp_slab_mqp > moment_ed_kNm:
                st.session_state.inp_slab_mqp = moment_ed_kNm
        
        moment_qp_kNm = st.number_input("Moment quasi-stały $M_{qp}$ [kNm/m]", value=min(30.0, moment_ed_kNm), max_value=moment_ed_kNm, step=1.0, key="inp_slab_mqp", on_change=reset_state) 
        
    with col_wk:
        crack_limit_mm = st.selectbox("Dopuszczalna szerokość rozwarcia rysy $w_{lim}$ [mm]", [0.1, 0.2, 0.3, 0.4], index=2, key="inp_slab_wk", on_change=reset_state)    

    # ------------------------------------------------------------------
    # PRZYCISK OBLICZ
    # ------------------------------------------------------------------
    _, col_btn, _ = st.columns([1, 2, 1])
    with col_btn:
        calc_button = st.button("OBLICZ", type="primary", use_container_width=True, key="btn_calc_slab")

    if calc_button:
        results_data = calculate_slab_bending_ec2(
            concrete_name, 
            steel_name, 
            height_cm, 
            cover_nom_mm, 
            diameter_bar_mm, 
            layer_type,
            moment_ed_kNm, 
            moment_qp_kNm, 
            crack_limit_mm
        )
        st.session_state.slab_results = results_data
        st.session_state.slab_calc_done = True

    # ------------------------------------------------------------------
    # WYNIKI
    # ------------------------------------------------------------------
    if st.session_state.slab_calc_done and st.session_state.slab_results:
        res = st.session_state.slab_results
        dbg = res['debug']
        warns = res['warnings']
        
        st.markdown("### WYNIKI OBLICZEŃ")
        
        # --- 1. KARTA GŁÓWNA ---
        COLOR_GREEN = "#22c55e"
        main_border = COLOR_GREEN
        
        # Format rozstawu
        s_res = res['spacing_final']
        
        st.markdown(
            f"""
            <div class="result-card-main" style="border-left: 6px solid {main_border};">
                <div class="res-label">DOBRANE ZBROJENIE (WYNIK KOŃCOWY)</div>
                <div style="font-size: 2.5rem; font-weight: 800; color: #ffffff; margin: 5px 0;">
                    ⌀{diameter_bar_mm} co {s_res} cm
                </div>
                <div style="color: #9ca3af; margin-bottom: 15px;">
                    A<sub>s,prov</sub> = {res['area_prov']:.2f} <span class="res-unit">cm²/m</span>
                    <span style="margin-left: 15px; color: {main_border}; font-weight: bold;">Decyduje: {res['governing_case']}</span>
                </div>
                <div style="font-size: 0.85rem; color: #6b7280; border-top: 1px solid #374151; padding-top: 10px; font-style: italic;">
                    ℹ️ Podana wartość wynika z obliczeń statycznych (SGN i SGU) dla pasma 1 m. Należy dodatkowo zweryfikować zbrojenie minimalne płyty.
                </div>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        if warns["spacing_too_small"]:
             st.error(f"⛔ **ZBYT MAŁY ROZSTAW W ŚWIETLE!** {warns['spacing_info']} Zwiększ średnicę prętów lub grubość płyty.")

        # --- 2. ANALIZA SGN ---
        st.markdown('<div class="result-section-header">ANALIZA STANU GRANICZNEGO NOŚNOŚCI</div>', unsafe_allow_html=True)
        c_sgn1, c_sgn2 = st.columns(2)
        with c_sgn1:
            st.markdown(f"""
            <div class="metric-box" style="border-left: 3px solid #22c55e;">
                <div class="res-label">WYMAGANE ZBROJENIE ZE WZGLĘDU NA SGN</div>
                <div class="res-val">A<sub>s,SGN</sub> = {res['area_sgn']:.2f} cm²/m</div>
            </div>
            """, unsafe_allow_html=True)
        with c_sgn2:
            # Rozstaw SGN
            s_sgn = res['spacing_sgn']
            st.markdown(f"""
            <div class="metric-box">
                <div class="res-label">ROZSTAW SPEŁNIAJĄCY WARUNEK SGN</div>
                <div class="res-val">⌀{diameter_bar_mm} co {s_sgn} cm</div>
            </div>
            """, unsafe_allow_html=True)

        if res['area_s2_req'] > 0:
            st.error(f"⚠️ Wymagane dodatkowo zbrojenie ściskane $A_{{s2}} = {res['area_s2_req']:.2f}$ cm²/m")

        # --- 3. ANALIZA SGU ---
        st.markdown(
            f'<div class="result-section-header">ANALIZA STANU GRANICZNEGO UŻYTKOWALNOŚCI (ZARYSOWANIE) <span style="font-size:0.9rem; color:#6b7280; font-weight:400; margin-left:10px;">(M<sub>cr</sub> = {res["M_cr_kNm"]:.1f} kNm)</span></div>', 
            unsafe_allow_html=True
        )
        
        wk_sgn = res['wk_sgn_only']
        if moment_qp_kNm <= res["M_cr_kNm"]:
             st.success(f"✅ Przekrój niezarysowany ($M_{{qp}} \le M_{{cr}}$). Szerokość rysy $w_k = 0.00$ mm.")
        else:
            c_sgu1, c_sgu2 = st.columns(2)
            
            with c_sgu1:
                color_sgn_wk = "#22c55e" if wk_sgn <= crack_limit_mm else "#ef4444"
                status_sgn = "Warunek spełniony" if wk_sgn <= crack_limit_mm else "Warunek niespełniony 👉"
                
                st.markdown(f"""
                <div class="metric-box" style="border-left: 3px solid {color_sgn_wk};">
                    <div class="res-label">SZEROKOŚĆ ROZWARCIA RYSY PRZY ZBROJENIU SGN (⌀{diameter_bar_mm}/{res['spacing_sgn']} cm)</div>
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
                        <div class="res-label">ROZSTAW SPEŁNIAJĄCY WARUNEK SGU (ZARYSOWANIE)</div>
                        <div class="res-val" style="font-size: 1.1rem;">
                             ⌀{diameter_bar_mm} co {res['spacing_final']} cm &rArr; w<sub>k</sub> = {wk_final:.3f} mm
                        </div>
                    </div>
                    """, unsafe_allow_html=True)


        # 4. OSTRZEŻENIA
        if warns['compression_low']:
            st.warning("⚠️ **SGN:** Zbrojenie ściskane jest słabo wykorzystane ($\sigma_{s2} < 0.1 f_{yd}$). Zwiększ grubość płyty.")

        if warns['max_reinforcement']:
            st.warning("⚠️ **KONSTR:** Przekroczono 4% stopnia zbrojenia. Problemy z betonowaniem!")
        
        st.markdown("")
        # 5. DEBUG
        with st.expander("🔍 Szczegóły obliczeń"):
            st.markdown("#### 1. Podstawowe dane")
            st.latex(f"b = 100 \\text{{ cm}}, \\quad h = {height_cm} \\text{{ cm}}, \\quad c_{{nom}} = {cover_nom_mm} \\text{{ mm}}, \\quad \\phi_s = {diameter_bar_mm} \\text{{ mm}}")
            st.latex(f"Beton: {concrete_name} => f_{{ck}} = {CONCRETE_TABLE[concrete_name].fck:.1f} \\text{{ MPa}}, \\quad Stal: {steel_name} => f_{{yk}} = {STEEL_TABLE[steel_name].fyk:.0f} \\text{{ MPa}}")
            st.latex(f"M_{{Ed}} = {moment_ed_kNm:.2f} \\text{{ kNm}}, \\quad M_{{qp}} = {moment_qp_kNm:.2f} \\text{{ kNm}}")

            st.markdown("#### 2. Wyniki obliczeń")
            
            # 2.1 d
            d_val_m = dbg['d_val']
            d_val_cm = d_val_m * 100
            st.markdown("##### 2.1 Wysokość użyteczna przekroju")
            
            # Formuła zależna od warstwy
            if layer_type == "1-sza warstwa":
                st.latex(f"d = h - c_{{nom}} - \\frac{{\\phi_s}}{{2}} = {height_cm} \\text{{ cm}} - {cover_nom_mm/10} \\text{{ cm}} - \\frac{{{diameter_bar_mm/10} \\text{{ cm}}}}{{2}} = {d_val_cm:.2f} \\text{{ cm}}")
            else:
                st.latex(f"d = h - c_{{nom}} - \\phi_s - \\frac{{\\phi_s}}{{2}} = {height_cm} \\text{{ cm}} - {cover_nom_mm/10} \\text{{ cm}} - {diameter_bar_mm/10} \\text{{ cm}} - \\frac{{{diameter_bar_mm/10} \\text{{ cm}}}}{{2}} = {d_val_cm:.2f} \\text{{ cm}}")

            # 2.2 Wytrzymałości
            st.markdown("##### 2.2 Wytrzymałość obliczeniowa materiałów")
            fcd_val = dbg['fcd_val']
            fyd_val = dbg['fyd_val']
            
            raw_fck = CONCRETE_TABLE[concrete_name].fck
            val_fck = raw_fck / 1_000_000.0 if raw_fck > 200 else raw_fck
            val_fyk = STEEL_TABLE[steel_name].fyk
            
            st.latex(f"f_{{cd}} = \\frac{{\\alpha_{{cc}} f_{{ck}}}}{{\\gamma_c}} = \\frac{{1.0 \\cdot {val_fck:.1f} \\text{{ MPa}}}}{{1.4}} = {fcd_val:.2f} \\text{{ MPa}}")
            st.latex(f"f_{{yd}} = \\frac{{f_{{yk}}}}{{\\gamma_s}} = \\frac{{{val_fyk:.0f} \\text{{ MPa}}}}{{1.15}} = {fyd_val:.2f} \\text{{ MPa}}")

            # 2.3 SGN
            st.markdown("##### 2.3 Wymagane zbrojenie (SGN)")
            mu_ed = dbg['mu_ed']
            eta_bet = dbg['eta_bet']
            omega_lim = dbg['omega_lim']
            fcd_MN = fcd_val 
            width_m = 1.0 # Płyta
            
            mu_lim_calc = omega_lim * (1 - 0.5 * omega_lim)
            
            st.latex(f"\\mu_{{Ed}} = \\frac{{M_{{Ed}}}}{{b d^2 \\eta f_{{cd}}}} = \\frac{{{moment_ed_kNm * 0.001:.4f} \\text{{ MNm}}}}{{{width_m:.2f} \\text{{ m}} \\cdot ({d_val_m:.3f} \\text{{ m}})^2 \\cdot {eta_bet:.1f} \\cdot {fcd_MN:.2f} \\text{{ MPa}}}} = {mu_ed:.4f}")
            st.latex(f"\\mu_{{lim}} = \\omega_{{lim}} (1 - 0.5 \\omega_{{lim}}) = {omega_lim:.4f} \\cdot (1 - 0.5 \\cdot {omega_lim:.4f}) = {mu_lim_calc:.4f}")

            if not dbg['is_doubly_reinforced']:
                zeta = dbg['zeta_val']
                z_arm = dbg['z_arm_val']
                area_req_m2 = res['area_sgn'] / 10000.0
                
                st.latex(f"\\mu_{{Ed}} \\le \\mu_{{lim}} \\implies \\text{{przekrój pojedynczo zbrojony}}")
                st.latex(f"\\zeta = 1 - 0.5 (1 - \\sqrt{{1 - 2 \\mu_{{Ed}}}}) = 1 - 0.5 (1 - \\sqrt{{1 - 2 \\cdot {mu_ed:.4f}}}) = {zeta:.4f}")
                st.latex(f"z = \\zeta \\cdot d = {zeta:.4f} \\cdot {d_val_cm:.2f} \\text{{ cm}} = {z_arm*100:.2f} \\text{{ cm}}")
                st.latex(f"A_{{s1,req}} = \\frac{{M_{{Ed}}}}{{z \\cdot f_{{yd}}}} = \\frac{{{moment_ed_kNm * 0.001:.4f} \\text{{ MNm}}}}{{{z_arm:.4f} \\text{{ m}} \\cdot {fyd_val:.2f} \\text{{ MPa}}}} = {res['area_sgn']:.2f} \\text{{ cm}}^2/m")
            else:
                m_rd_lim = dbg['M_rd_lim']
                delta_m = (moment_ed_kNm * 0.001) - m_rd_lim
                area_s2 = res['area_s2_req']
                area_s1 = res['area_sgn']
                
                st.latex(f"\\mu_{{Ed}} > \\mu_{{lim}} \\implies \\text{{przekrój podwójnie zbrojony}}")
                st.latex(f"M_{{Rd,lim}} = \\mu_{{lim}} b d^2 \\eta f_{{cd}} = {m_rd_lim*1000:.1f} \\text{{ kNm}}")
                st.latex(f"\\Delta M = M_{{Ed}} - M_{{Rd,lim}} = {moment_ed_kNm:.1f} - {m_rd_lim*1000:.1f} = {delta_m*1000:.1f} \\text{{ kNm}}")
                st.latex(f"A_{{s2,req}} = \\frac{{\\Delta M}}{{\\sigma_{{s2}} (d - d_2)}} = {area_s2:.2f} \\text{{ cm}}^2/m")
                st.latex(f"A_{{s1,req}} = \\frac{{M_{{Rd,lim}}}}{{z_{{lim}} f_{{yd}}}} + A_{{s2,req}} \\frac{{\\sigma_{{s2}}}}{{f_{{yd}}}} = {area_s1:.2f} \\text{{ cm}}^2/m")

            # 2.4 SGU
            st.markdown("##### 2.4 Stan Graniczny Użytkowalności (SGU)")
            sgu = dbg['sgu']
            m_cr = res['M_cr_kNm']
            fctm_val = dbg['fctm_val']
            width_m = 1.0
            height_m = height_cm / 100.0
            
            W_c_m3 = (width_m * height_m**2) / 6.0
            
            st.latex(f"W_c = \\frac{{b h^2}}{{6}} = \\frac{{{width_m:.2f} \\text{{ m}} \\cdot ({height_m:.2f} \\text{{ m}})^2}}{{6}} = {W_c_m3:.4f} \\text{{ m}}^3")
            st.latex(f"M_{{cr}} = f_{{ctm}} \\cdot W_c = {fctm_val:.2f} \\text{{ MPa}} \\cdot {W_c_m3:.4f} \\text{{ m}}^3 \\cdot 1000 = {m_cr:.2f} \\text{{ kNm}}")
            
            if not sgu['is_cracked']:
                st.markdown(f"**Przekrój niezarysowany** ($M_{{qp}} < M_{{cr}}$)")
                st.latex(r"w_k = 0.00 \text{ mm}")
            else:
                st.markdown(f"**Przekrój zarysowany** ($M_{{qp}} \ge M_{{cr}}$)")
                
                alpha_e = dbg['alpha_e']
                Es_MPa = dbg['Es_used_MPa']
                Ecm_MPa = dbg['Ecm_used_MPa']
                
                st.latex(f"\\alpha_e = \\frac{{E_s}}{{E_{{cm}}}} = \\frac{{{Es_MPa:.0f} \\text{{ MPa}}}}{{{Ecm_MPa:.0f} \\text{{ MPa}}}} = {alpha_e:.2f}")
                
                area_prov_m2 = res['area_prov'] / 10000.0
                d_val_m = dbg['d_val']
                x_ii_m = sgu['x_ii']
                x_ii_cm = x_ii_m * 100
                
                st.latex(f"A_{{s,prov}} = {res['area_prov']:.2f} \\text{{ cm}}^2/m = {area_prov_m2 * 10000:.2f} \\cdot 10^{{-4}} \\text{{ m}}^2")
                
                st.markdown("Wysokość strefy ściskanej $x_{II}$:")
                st.latex(r"x_{II} = \frac{-\alpha_e A_s + \sqrt{(\alpha_e A_s)^2 + 2 b \alpha_e A_s d}}{b}")
                
                as_formatted = f"{area_prov_m2 * 10000:.2f} \\cdot 10^{{-4}}"
                st.latex(
                    f"x_{{II}} = \\frac{{-{alpha_e:.2f} \\cdot {as_formatted} \\text{{ m}}^2 + \\sqrt{{({alpha_e:.2f} \\cdot {as_formatted} \\text{{ m}}^2)^2 + 2 \\cdot {width_m:.2f} \\text{{ m}} \\cdot {alpha_e:.2f} \\cdot {as_formatted} \\text{{ m}}^2 \\cdot {d_val_m:.3f} \\text{{ m}}}}}}{{{width_m:.2f} \\text{{ m}}}}"
                    f" = {x_ii_m:.4f} \\text{{ m}}"
                )
                            
                I_ii = (width_m * x_ii_m**3)/3.0 + alpha_e * area_prov_m2 * (d_val_m - x_ii_m)**2
                
                st.latex(
                    f"I_{{II}} = \\frac{{b x_{{II}}^3}}{{3}} + \\alpha_e A_s (d - x_{{II}})^2"
                    f" = \\frac{{{width_m:.2f} \\text{{ m}} \\cdot ({x_ii_m:.3f} \\text{{ m}})^3}}{{3}} + {alpha_e:.2f} \\cdot {as_formatted} \\text{{ m}}^2 \\cdot ({d_val_m:.3f} \\text{{ m}} - {x_ii_m:.3f} \\text{{ m}})^2 = {I_ii:.6f} \\text{{ m}}^4"
                )
                
                sigma_s = sgu['sigma_s']
                M_qp_MNm = moment_qp_kNm * 0.001
                st.latex(f"\\sigma_s = \\alpha_e \\frac{{M_{{qp}}}}{{I_{{II}}}} (d - x_{{II}}) = {alpha_e:.2f} \\cdot \\frac{{{M_qp_MNm:.4f} \\text{{ MNm}}}}{{{I_ii:.6f} \\text{{ m}}^4}} \\cdot ({d_val_m:.3f} \\text{{ m}} - {x_ii_m:.3f} \\text{{ m}}) = {sigma_s:.2f} \\text{{ MPa}}")
                
                sr_max = sgu['sr_max'] * 1000 
                eps_diff = sgu['eps_diff']
                wk_val = res['wk_final']
                
                st.latex(f"w_k = s_{{r,max}} (\\varepsilon_{{sm}} - \\varepsilon_{{cm}}) = {sr_max:.1f} \\text{{ mm}} \\cdot {eps_diff:.5f} = {wk_val:.3f} \\text{{ mm}}")

            # 2.5 ZBROJENIE KOŃCZOWE
            st.markdown("##### 2.5. Zbrojenie końcowe")
            governing = res['governing_case']
            
            if "SGN" in governing:
                st.markdown(f"Decyduje warunek **{governing}**.")
            else:
                st.markdown(f"Decyduje warunek **{governing}** (zagęszczono rozstaw).")
            
            st.latex(f"A_{{s,prov}} = \\phi {diameter_bar_mm} \\text{{ co }} {res['spacing_final']} \\text{{ cm}} = {res['area_prov']:.2f} \\text{{ cm}}^2/m")


def run():
    render_slab_page()

if __name__ == "__main__":
    run()
