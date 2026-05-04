# ==============================================================================
# WYMIAROWANIE SŁUPA PROSTOKĄTNEGO – EC2 (PN-EN 1992-1-1)
# SEKCJA: DANE WEJŚCIOWE I SOLVER
# ==============================================================================

import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import math

try:
    from TABLICE.ParametryBetonu import CONCRETE_TABLE, list_concrete_classes
    from TABLICE.ParametryStali import STEEL_TABLE
except Exception:
    st.error("Błąd importu TABLICE. Sprawdź pliki w folderze TABLICE.")
    st.stop()

# ==============================================================================
# SOLVER - OBLICZENIA POMOCNICZE EC2
# ==============================================================================

def get_MRd(N_Ed, As_half, width, height, d, d2, fcd, fyd, Es, fck):
    if N_Ed < 0: 
        return 0.0
        
    lam = 0.8 if fck <= 50 else 0.8 - (fck - 50) / 400.0
    eta_c = 1.0 if fck <= 50 else 1.0 - (fck - 50) / 200.0
    
    def calc_N_M(x):
        eps_top = 0.0035
        eps_s2 = eps_top * (x - d2) / x if x != 0 else 0
        eps_s1 = eps_top * (x - d) / x if x != 0 else 0
        
        sigma_s2 = max(-fyd, min(fyd, eps_s2 * Es))
        sigma_s1 = max(-fyd, min(fyd, eps_s1 * Es))
        
        x_eff = min(height, lam * x)
        Nc = eta_c * fcd * width * x_eff
        
        N = Nc + As_half * sigma_s2 + As_half * sigma_s1
        M = Nc * (height/2 - x_eff/2) + As_half * sigma_s2 * (height/2 - d2) + As_half * sigma_s1 * (height/2 - d)
        return N, M

    N_max, M_max = calc_N_M(10.0 * height)
    if N_Ed >= N_max:
        return 0.0
        
    x_min_bisect = 0.0001
    x_max_bisect = 10.0 * height
    
    for _ in range(60):
        x_mid = (x_min_bisect + x_max_bisect) / 2
        N_mid, M_mid = calc_N_M(x_mid)
        if N_mid > N_Ed:
            x_max_bisect = x_mid
        else:
            x_min_bisect = x_mid
            
    _, M_Rd = calc_N_M((x_min_bisect + x_max_bisect) / 2)
    return M_Rd

def solve_1D(N_Ed, M_Ed, width, height, d, d2, fcd, fyd, Es, fck):
    """Zwraca wymagane pole zbrojenia (całkowite dla kierunku) dla zadanego M_Ed."""
    if M_Ed <= 0: return 0.0
    As_req = 0.0
    step = 0.002 # Skok 20 cm2
    for _ in range(1000):
        MRd = get_MRd(N_Ed, As_req / 2, width, height, d, d2, fcd, fyd, Es, fck)
        if MRd >= M_Ed:
            if step <= 0.00001: # Dokładność 0.1 cm2
                return As_req
            else:
                As_req = max(0.0, As_req - step)
                step /= 10.0
        As_req += step
    return As_req

# ==============================================================================
# POMOCNICZA FUNKCJA DO ETYKIET Z IKONĄ "?" 
# ==============================================================================

def label_with_help(label, help_text):
    return st.markdown(
        f"""
        <div style="display:flex; align-items:center; justify-content:space-between; width:100%; margin-bottom:-10px;">
            <span style="font-weight:400; font-size:0.9rem; color:#e5e7eb;">{label}</span>
            <span class="header-help-icon" title="{help_text}">?</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ==============================================================================
# RYSUNEK PRZEKROJU
# ==============================================================================

def generate_column_schematic():
    b_plot, h_plot, cnom_plot = 20.0, 42.0, 1.5
    fig, ax = plt.subplots(figsize=(5, 7.5))
    ax.set_aspect('equal')
    c_concrete, c_line, c_bar, c_dim = '#f3f4f6', '#111827', '#111827', '#6b7280'

    ax.add_patch(patches.Rectangle((0, 0), b_plot, h_plot,
                                   linewidth=2, edgecolor=c_line, facecolor=c_concrete))

    x_pos = [cnom_plot, b_plot / 2, b_plot - cnom_plot]
    y_pos = [
        cnom_plot,
        cnom_plot + (h_plot - 2 * cnom_plot) / 3,
        cnom_plot + 2 * (h_plot - 2 * cnom_plot) / 3,
        h_plot - cnom_plot
    ]

    for x in x_pos:
        ax.add_patch(patches.Circle((x, cnom_plot), radius=0.45, color=c_bar))
        ax.add_patch(patches.Circle((x, h_plot - cnom_plot), radius=0.45, color=c_bar))
    for y in y_pos:
        ax.add_patch(patches.Circle((cnom_plot, y), radius=0.45, color=c_bar))
        ax.add_patch(patches.Circle((b_plot - cnom_plot, y), radius=0.45, color=c_bar))

    ax.text(b_plot / 2, h_plot - 3.5, "$A_{s1}$", ha='center', fontsize=11, fontweight='bold')
    ax.text(b_plot / 2, 3, "$A_{s1}$", ha='center', fontsize=11, fontweight='bold')
    ax.text(2.0, h_plot / 2, "$A_{s2}$", va='center', rotation=90, fontsize=11, fontweight='bold')
    ax.text(b_plot - 4, h_plot / 2, "$A_{s2}$", va='center', rotation=90, fontsize=11, fontweight='bold')

    def draw_tech_dim_final(p1, p2, dim_pos, edge_pos, text, is_horiz=True):
        ext = 1.4
        gap = 0.4
        if is_horiz:
            ax.plot([p1, p2], [dim_pos, dim_pos], color=c_dim, linewidth=1.0)
            for p in [p1, p2]:
                ax.plot([p, p], [edge_pos, dim_pos - ext if dim_pos < edge_pos else dim_pos + ext], color=c_dim, linewidth=0.8)
                ax.plot([p - 0.4, p + 0.4], [dim_pos - 0.4, dim_pos + 0.4], color=c_dim, linewidth=1.2)
            ax.text((p1+p2)/2, dim_pos - gap, text, ha='center', va='top', fontsize=11)
        else:
            ax.plot([dim_pos, dim_pos], [p1, p2], color=c_dim, linewidth=1.0)
            for p in [p1, p2]:
                ax.plot([edge_pos, dim_pos - ext if dim_pos < edge_pos else dim_pos + ext], [p, p], color=c_dim, linewidth=0.8)
                ax.plot([dim_pos - 0.4, dim_pos + 0.4], [p - 0.4, p + 0.4], color=c_dim, linewidth=1.2)
            ax.text(dim_pos - gap, (p1+p2)/2, text, ha='right', va='center', rotation=90, fontsize=11)

    draw_tech_dim_final(0, b_plot, -2.5, 0, "$b$", True)
    draw_tech_dim_final(0, h_plot, -2.5, 0, "$h$", False)

    ax.annotate('', xy=(-5, h_plot/2), xytext=(-9, h_plot/2),
                arrowprops=dict(arrowstyle='-|>,head_width=0.3', lw=1.5))
    ax.annotate('', xy=(-5.8, h_plot/2), xytext=(-9, h_plot/2),
                arrowprops=dict(arrowstyle='-|>,head_width=0.3', lw=1.5))
    ax.text(-7.5, h_plot/2 + 1.2, "$M_{Ed,y}$", ha='center', fontsize=10)

    ax.annotate('', xy=(b_plot/2, -5), xytext=(b_plot/2, -9),
                arrowprops=dict(arrowstyle='-|>,head_width=0.3', lw=1.5))
    ax.annotate('', xy=(b_plot/2, -5.8), xytext=(b_plot/2, -9),
                arrowprops=dict(arrowstyle='-|>,head_width=0.3', lw=1.5))
    ax.text(b_plot/2 + 1.5, -7.5, "$M_{Ed,z}$", rotation=90, va='center', fontsize=10)

    ax.plot(b_plot/2, h_plot/2, 'kx', markersize=6, markeredgewidth=1.5)
    ax.annotate('$N_{Ed}$',
                xy=(b_plot/2, h_plot/2),
                xytext=(b_plot/2 + 2.5, h_plot/2 + 2.5),
                arrowprops=dict(arrowstyle='->', color='black', lw=1.5),
                fontsize=11, fontweight='bold')

    ax.set_xlim(-11, b_plot + 8)
    ax.set_ylim(-11, h_plot + 6)
    ax.axis('off')
    st.pyplot(fig)

# ==============================================================================
# RENDER PAGE
# ==============================================================================

def render_column_page():

    st.markdown("""
        <style>
        .block-container { padding-top: 1rem; }
        .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; height: 3.2em; }
        .header-help-icon {
            display: inline-flex; justify-content: center; align-items: center;
            width: 14px; height: 14px; border-radius: 50%; background-color: #4b5563;
            color: white; font-size: 10px; cursor: help;
        }
        /* STYLE WYNIKOWE Z BELEK */
        .result-section-header {
            background-color: #1e293b;
            padding: 0.5rem 1rem;
            border-radius: 0.25rem;
            font-weight: 600;
            color: #ffffff;
            margin-top: 1.5rem;
            margin-bottom: 1rem;
            font-size: 1.1rem;
            text-transform: uppercase;
        }
        .metric-box {
            background-color: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 0.5rem;
            padding: 1rem;
            margin-bottom: 1rem;
            box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        }
        .res-label {
            font-size: 0.75rem;
            font-weight: 600;
            color: #6b7280;
            margin-bottom: 0.25rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .res-val {
            font-size: 1.25rem;
            font-weight: 700;
            color: #111827;
        }
        </style>
    """, unsafe_allow_html=True)

    if "column_calc_done" not in st.session_state:
        st.session_state.column_calc_done = False

    def reset_state():
        st.session_state.column_calc_done = False

    st.markdown("### DANE WEJŚCIOWE")
    c_vis, c_f1, c_f2 = st.columns([1, 1, 1])

    with c_vis:
        generate_column_schematic()

    # LEWA
    with c_f1:
        st.selectbox("Klasa betonu", list_concrete_classes(), index=4, key="c_class", on_change=reset_state)
        st.number_input("Szerokość $b$ [cm]", value=30.0, key="b_cm", on_change=reset_state)
        st.selectbox("Średnica prętów $\\phi_s$ [mm]", [12, 16, 20, 25, 32], index=1, key="p_s", on_change=reset_state)
        st.number_input("Otulina $c_{nom}$ [mm]", value=35, key="c_mm", on_change=reset_state)

        st.number_input("$\\beta_y$",
                        value=1.0,
                        step=0.05,
                        key="beta_y",
                        on_change=reset_state,
                        help="Współczynnik wyboczeniowy względem silnej osi przekroju.")

        st.selectbox("Wilgotność względna $RH$ [%]", [50, 80], index=0, key="rh_val", on_change=reset_state)
        st.selectbox("Rodzaj cementu", ["S - wolnotwardniejący", "N - normalnie twardniejący", "R - szybkotwardniejący"], index=1, key="cem_val", on_change=reset_state)

    # PRAWA
    with c_f2:
        st.selectbox("Klasa stali", list(STEEL_TABLE.keys()), index=1, key="s_class", on_change=reset_state)
        st.number_input("Wysokość $h$ [cm]", value=40.0, key="h_cm", on_change=reset_state)
        st.selectbox("Średnica strzemion $\\phi_w$ [mm]", [6, 8, 10, 12], index=1, key="p_w", on_change=reset_state)
        st.number_input("Długość słupa $L$ [m]", value=3.0, key="l_m", on_change=reset_state)

        st.number_input("$\\beta_z$",
                        value=1.0,
                        step=0.05,
                        key="beta_z",
                        on_change=reset_state,
                        help="Współczynnik wyboczeniowy względem słabej osi przekroju.")

        st.number_input("Wiek betonu $t_0$ [dni]", value=28, key="t0_val", on_change=reset_state)

        st.number_input("$M_{0Eqp}/M_{0Ed}$",
                        value=0.7,
                        step=0.05,
                        key="m_rat",
                        on_change=reset_state,
                        help="Stosunek momentu quasi-stałego do obliczeniowego.")

    if st.session_state.h_cm < st.session_state.b_cm:
        st.error("❌ Wysokość $h$ musi być ≥ $b$.")
        st.stop()

    cn, cmy, cmz = st.columns(3)
    with cn:
        st.number_input("$N_{Ed}$ [kN]", value=1000.0, key="n_ed", on_change=reset_state)
    with cmy:
        st.number_input("$M_{Ed,y}$ [kNm]", value=50.0, key="m_ey", on_change=reset_state)
    with cmz:
        st.number_input("$M_{Ed,z}$ [kNm]", value=10.0, key="m_ez", on_change=reset_state)

    # SUWAK NA PEŁNĄ SZEROKOŚĆ (POD SIŁAMI)
    st.slider("Dopuszczalne wytężenie $\\eta_{max}$ [%]", 
              min_value=10, max_value=100, value=100, step=10, 
              key="eta_max", on_change=reset_state,
              help="Pozwala na wymuszenie zapasu nośności (np. pod kątem wymogów P-poż).")
              
    st.markdown("<br>", unsafe_allow_html=True)

    _, col_btn, _ = st.columns([1, 2, 1])
    with col_btn:
        if st.button("OBLICZ", type="primary", use_container_width=True):
            st.session_state.column_calc_done = True

    # ==========================================================================
    # OBLICZENIA I WYNIKI (ZAJMUJĄCE 100% SZEROKOŚCI STRONY)
    # ==========================================================================
    if st.session_state.column_calc_done:
        st.markdown("### WYNIKI OBLICZEŃ")
        
        # --- POBRANIE DANYCH ---
        concrete = CONCRETE_TABLE[st.session_state.c_class]
        steel = STEEL_TABLE[st.session_state.s_class]
        
        b = st.session_state.b_cm / 100.0
        h = st.session_state.h_cm / 100.0
        c_nom = st.session_state.c_mm / 1000.0
        phi_s = st.session_state.p_s / 1000.0
        phi_w = st.session_state.p_w / 1000.0
        
        L_m = st.session_state.l_m
        beta_y = st.session_state.beta_y
        beta_z = st.session_state.beta_z
        rh = st.session_state.rh_val
        t0 = st.session_state.t0_val
        cement_type = st.session_state.cem_val
        m_ratio = st.session_state.m_rat
        eta_limit = st.session_state.eta_max / 100.0
        
        NEd = st.session_state.n_ed / 1000.0
        M0y = st.session_state.m_ey / 1000.0
        M0z = st.session_state.m_ez / 1000.0
        
        # --- PARAMETRY MATERIAŁOWE I GEOMETRYCZNE ---
        fck = concrete.fck
        fcm = fck + 8
        Ecm = concrete.Ecm * 1000 if concrete.Ecm < 1000 else concrete.Ecm
        fyk = steel.fyk
        Es = steel.Es * 1000 if steel.Es < 1000 else steel.Es
        
        fcd = fck / 1.5
        fyd = fyk / 1.15
        
        Ac = b * h
        # h0 spójne w mm
        Ac_mm2 = (b * 1000) * (h * 1000)
        u_mm = 2 * (b * 1000 + h * 1000)
        h0 = 2 * Ac_mm2 / u_mm
        
        Ic_y = b * h**3 / 12
        Ic_z = h * b**3 / 12
        
        iy = h / math.sqrt(12)
        iz = b / math.sqrt(12)
        
        d2 = c_nom + phi_w + phi_s / 2
        d_y = h - d2
        d_z = b - d2
        area_bar = math.pi * (phi_s / 2)**2
        
        # --- PEŁZANIE ---
        alpha_1 = (35/fcm)**0.7
        alpha_2 = (35/fcm)**0.2
        if fcm <= 35:
            phi_RH = 1 + (1 - rh/100) / (0.1 * (h0)**(1/3))
        else:
            phi_RH = (1 + ((1 - rh/100) / (0.1 * (h0)**(1/3))) * alpha_1) * alpha_2
            
        beta_fcm = 16.8 / math.sqrt(fcm)
        alpha_cem = -1 if cement_type.startswith("S") else (0 if cement_type.startswith("N") else 1)
        t0_adj = max(0.5, t0 * (9 / (2 + t0**1.2) + 1)**alpha_cem)
        beta_t0 = 1 / (0.1 + t0_adj**0.2)
        
        phi_eff = (phi_RH * beta_fcm * beta_t0) * m_ratio
        
        # Sztywność betonu Ecd wg 5.8.7.2(2)
        Ecd = Ecm / 1.2
        
        # --- SOLVER: EFEKTY II RZĘDU & ZBROJENIE ---
        l0_y = beta_y * L_m
        l0_z = beta_z * L_m
        
        lambda_y = l0_y / iy if iy > 0 else 0
        lambda_z = l0_z / iz if iz > 0 else 0
        
        n_rel_N = NEd / (Ac * fcd) if (Ac * fcd) > 0 else 0
        k1 = math.sqrt(fck / 20.0)
        k2_y = min(n_rel_N * lambda_y / 170.0, 0.20)
        k2_z = min(n_rel_N * lambda_z / 170.0, 0.20)
        
        # Dokładny współczynnik Kc wg normy 5.8.7.2 (Wzór 5.21)
        Kc_y = (k1 * k2_y) / (1 + phi_eff)
        Kc_z = (k1 * k2_z) / (1 + phi_eff)
        
        As_min_ec2 = max(0.10 * NEd / fyd, 0.002 * Ac)
        As_min_user = 4 * area_bar  # Minimum 4 pręty (po 1 w narożniku)
        As_min_tot = max(As_min_ec2, As_min_user)
        As_max = 0.04 * Ac
        
        # Start iteracji od minimalnego zbrojenia
        As1 = As_min_tot / 2.0
        As2 = As_min_tot / 2.0
        eta = 999.0
        
        for step in range(150):
            Is_y = As1 * (h/2 - d2)**2 + As2 * (1/3) * (h/2 - d2)**2
            Is_z = As2 * (b/2 - d2)**2 + As1 * (1/3) * (b/2 - d2)**2
            
            EI_y = Kc_y * Ecd * Ic_y + Es * Is_y
            EI_z = Kc_z * Ecd * Ic_z + Es * Is_z
            
            NB_y = (math.pi**2 * EI_y) / (l0_y**2) if l0_y > 0 else 1e9
            NB_z = (math.pi**2 * EI_z) / (l0_z**2) if l0_z > 0 else 1e9
            
            # Bezpiecznik przed zerowym mianownikiem (jeśli utrata stateczności)
            NB_y = max(NB_y, NEd + 0.0001)
            NB_z = max(NB_z, NEd + 0.0001)
                
            M_Ed_y = M0y / (1 - NEd/NB_y)
            M_Ed_z = M0z / (1 - NEd/NB_z)
            
            # 1. Oblicz bazowe zapotrzebowanie 1D
            req_As1 = solve_1D(NEd, M_Ed_y, b, h, d_y, d2, fcd, fyd, Es, fck)
            req_As2 = solve_1D(NEd, M_Ed_z, h, b, d_z, d2, fcd, fyd, Es, fck)
            
            test_As1 = max(req_As1, As_min_tot / 2.0)
            test_As2 = max(req_As2, As_min_tot / 2.0)
            
            # 2. Wewnętrzna pętla poszukująca interakcji 2D (Dystrybucja proporcjonalna/ważona)
            for _ in range(30):
                MRd_y = get_MRd(NEd, test_As1/2, b, h, d_y, d2, fcd, fyd, Es, fck)
                MRd_z = get_MRd(NEd, test_As2/2, h, b, d_z, d2, fcd, fyd, Es, fck)
                
                N_Rd = Ac * fcd + (test_As1 + test_As2) * fyd
                n_rel = NEd / N_Rd if N_Rd > 0 else 1.0
                
                if n_rel <= 0.1: a_exp = 1.0
                elif n_rel <= 0.7: a_exp = 1.0 + (n_rel - 0.1) * (0.5 / 0.6)
                elif n_rel <= 1.0: a_exp = 1.5 + (n_rel - 0.7) * (0.5 / 0.3)
                else: a_exp = 2.0
                
                eta_y = (M_Ed_y / MRd_y)**a_exp if MRd_y > 0 else 999.0
                eta_z = (M_Ed_z / MRd_z)**a_exp if MRd_z > 0 else 999.0
                eta = eta_y + eta_z
                
                if eta <= eta_limit or (test_As1 + test_As2) > As_max:
                    break
                
                # Ustalenie proporcji "winy" za przekroczenie wytężenia
                w_y = eta_y / eta if eta > 0 else 0.5
                w_z = eta_z / eta if eta > 0 else 0.5
                
                # Obliczenie potrzebnego globalnego zapasu stali dla osiągnięcia warunku eta_limit
                scale = min(1.2, max(1.02, (eta / eta_limit)**(1/a_exp)))
                delta_As = (test_As1 + test_As2) * (scale - 1.0)
                
                # Aplikacja zapasu proporcjonalnie do udziału osi
                test_As1 += delta_As * w_y
                test_As2 += delta_As * w_z
                
            target_As1 = test_As1
            target_As2 = test_As2
                
            # Relaksacja numeryczna na zewnątrz dla efektów II rzędu
            diff1 = abs(As1 - target_As1)
            diff2 = abs(As2 - target_As2)
            
            As1 = 0.5 * As1 + 0.5 * target_As1
            As2 = 0.5 * As2 + 0.5 * target_As2
            
            if diff1 < 1e-5 and diff2 < 1e-5:
                break

        As_tot = As1 + As2

        # ----------------------------------------------------------------------
        # PONOWNE WYLICZENIE STANÓW KOŃCOWYCH (DLA MODUŁU "SZCZEGÓŁY OBLICZEŃ")
        # ----------------------------------------------------------------------
        Is_y_fin = As1 * (h/2 - d2)**2 + As2 * (1/3) * (h/2 - d2)**2
        Is_z_fin = As2 * (b/2 - d2)**2 + As1 * (1/3) * (b/2 - d2)**2
        EI_y_fin = Kc_y * Ecd * Ic_y + Es * Is_y_fin
        EI_z_fin = Kc_z * Ecd * Ic_z + Es * Is_z_fin
        NB_y_fin = (math.pi**2 * EI_y_fin) / (l0_y**2) if l0_y > 0 else 1e9
        NB_z_fin = (math.pi**2 * EI_z_fin) / (l0_z**2) if l0_z > 0 else 1e9
        NB_y_fin = max(NB_y_fin, NEd + 0.0001)
        NB_z_fin = max(NB_z_fin, NEd + 0.0001)
        M_Ed_y_fin = M0y / (1 - NEd/NB_y_fin)
        M_Ed_z_fin = M0z / (1 - NEd/NB_z_fin)
        MRd_y_fin = get_MRd(NEd, As1/2, b, h, d_y, d2, fcd, fyd, Es, fck)
        MRd_z_fin = get_MRd(NEd, As2/2, h, b, d_z, d2, fcd, fyd, Es, fck)
        N_Rd_fin = Ac * fcd + (As1 + As2) * fyd
        n_rel_fin = NEd / N_Rd_fin if N_Rd_fin > 0 else 1.0
        
        if n_rel_fin <= 0.1: a_exp_fin = 1.0
        elif n_rel_fin <= 0.7: a_exp_fin = 1.0 + (n_rel_fin - 0.1) * (0.5 / 0.6)
        elif n_rel_fin <= 1.0: a_exp_fin = 1.5 + (n_rel_fin - 0.7) * (0.5 / 0.3)
        else: a_exp_fin = 2.0
        
        eta_fin = (M_Ed_y_fin / MRd_y_fin)**a_exp_fin + (M_Ed_z_fin / MRd_z_fin)**a_exp_fin if MRd_y_fin > 0 and MRd_z_fin > 0 else 999.0
        
        # Obliczenia na cm2 dla prezentacji
        As1_cm2 = As1 * 10000
        As2_cm2 = As2 * 10000
        area_bar_cm2 = area_bar * 10000
        phi_val = int(st.session_state.p_s)
        
        # Przeliczenie na fizyczne pręty dla poszczególnych pasm (min. 2 na krawędź ze względu na narożniki)
        n1 = max(2, math.ceil(As1_cm2 / area_bar_cm2))
        As1_prov_disp = n1 * area_bar_cm2
        
        n2 = max(2, math.ceil(As2_cm2 / area_bar_cm2))
        As2_prov_disp = n2 * area_bar_cm2
        
        # Wyznaczenie ilości prętów całkowitej (min. 4 szt., zawsze parzysta liczba dla symetrii)
        n_total = max(4, math.ceil(As_tot / area_bar))
        n_total = (n_total + 1) // 2 * 2
        
        As_prov_cm2 = n_total * area_bar_cm2
        As_min_cm2 = As_min_tot * 10000
        As_max_cm2 = As_max * 10000

        # ======================================================================
        # WYŚWIETLANIE WYNIKÓW
        # ======================================================================
        
        c_sgn1, c_sgn2 = st.columns(2)
        with c_sgn1:
            st.markdown(f"""
            <div class="metric-box" style="border-left: 3px solid #3b82f6;">
                <div class="res-label" style="display: flex; justify-content: space-between; align-items: center;">
                    <span>WYMAGANE ZBROJENIE A<sub style="text-transform:none;">s1</sub> (WZDŁUŻ BOKU b)</span>
                    <span class="header-help-icon" title="Zbrojenie rozłożone na jednym boku b (wraz z prętami w narożnikach).">?</span>
                </div>
                <div class="res-val">{n1} szt. ⌀{phi_val} &rArr; {As1_prov_disp:.2f} cm²</div>
                <div style="font-size: 0.85rem; color: #6b7280; margin-top: 4px;">Teoretycznie z obliczeń: {As1_cm2:.2f} cm²</div>
            </div>
            """, unsafe_allow_html=True)
        with c_sgn2:
            st.markdown(f"""
            <div class="metric-box" style="border-left: 3px solid #3b82f6;">
                <div class="res-label" style="display: flex; justify-content: space-between; align-items: center;">
                    <span>WYMAGANE ZBROJENIE A<sub style="text-transform:none;">s2</sub> (WZDŁUŻ BOKU h)</span>
                    <span class="header-help-icon" title="Zbrojenie rozłożone na jednym boku h (wraz z prętami w narożnikach).">?</span>
                </div>
                <div class="res-val">{n2} szt. ⌀{phi_val} &rArr; {As2_prov_disp:.2f} cm²</div>
                <div style="font-size: 0.85rem; color: #6b7280; margin-top: 4px;">Teoretycznie z obliczeń: {As2_cm2:.2f} cm²</div>
            </div>
            """, unsafe_allow_html=True)
        
        c_tot1, c_tot2 = st.columns(2)
        color_prov = "#22c55e" if (eta <= eta_limit and As_tot <= As_max) else "#ef4444"
        
        with c_tot1:
            st.markdown(f"""
            <div class="metric-box" style="border-left: 3px solid {color_prov};">
                <div class="res-label">ZBROJENIE ZASTOSOWANE A<sub style="text-transform:none;">s,prov</sub></div>
                <div class="res-val">{n_total} szt. ⌀{phi_val} &rArr; {As_prov_cm2:.2f} cm²</div>
            </div>
            """, unsafe_allow_html=True)
        with c_tot2:
            st.markdown(f"""
            <div class="metric-box" style="border-left: 3px solid {color_prov};">
                <div class="res-label">WARUNEK ZGINANIA DWUKIERUNKOWEGO <span style="text-transform:none;">&eta;</span></div>
                <div class="res-val">{eta:.2f} &le; {eta_limit:.2f}</div>
            </div>
            """, unsafe_allow_html=True)

        if As_min_cm2 <= As_prov_cm2 <= As_max_cm2:
            st.success(f"✅ Zbrojenie mieści się w dopuszczalnych granicach normowych: $A_{{s,min}} ({As_min_cm2:.2f} \\text{{ cm}}^2) \\le A_{{s,prov}} \\le A_{{s,max}} ({As_max_cm2:.2f} \\text{{ cm}}^2)$")
        else:
            st.error(f"❌ Niespełniony warunek zbrojenia min/max: Wymagane przedziały to $A_{{s,min}}({As_min_cm2:.2f} \\text{{ cm}}^2)$ oraz $A_{{s,max}}({As_max_cm2:.2f} \\text{{ cm}}^2)$")

        if As_tot > As_max:
            st.warning("⚠️ Wymagane zbrojenie przekracza dopuszczalny stopień zbrojenia (4%). Należy zwiększyć wymiary przekroju słupa lub zastosować wyższą klasę betonu.")
        elif eta > eta_limit:
            st.warning(f"⚠️ Zginanie dwukierunkowe przekracza wymagany limit nośności ({eta_limit:.2f}). Należy zwiększyć wymiary przekroju słupa.")
        elif eta <= eta_limit and As_tot <= As_max:
            st.success("✅ Warunki nośności na zginanie ze siłą osiową (w tym zginanie dwukierunkowe) są spełnione.")

        # ======================================================================
        # DEBUG / SZCZEGÓŁY OBLICZEŃ
        # ======================================================================
        with st.expander("🔍 Szczegóły obliczeń"):
            st.markdown("#### 1. Podstawowe dane")
            st.latex(rf"b = {b*100:.1f}\,\text{{cm}}, \quad h = {h*100:.1f}\,\text{{cm}}, \quad L = {L_m:.2f}\,\text{{m}}")
            st.latex(rf"N_{{Ed}} = {NEd*1000:.1f}\,\text{{kN}}, \quad M_{{0Ed,y}} = {M0y*1000:.1f}\,\text{{kNm}}, \quad M_{{0Ed,z}} = {M0z*1000:.1f}\,\text{{kNm}}")
            st.latex(rf"\text{{Beton: }} {st.session_state.c_class} \implies f_{{ck}} = {fck:.1f}\,\text{{MPa}}, \quad \text{{Stal: }} {st.session_state.s_class} \implies f_{{yk}} = {fyk:.0f}\,\text{{MPa}}")
            
            st.markdown("#### 2. Parametry materiałowe i geometryczne")
            st.latex(rf"f_{{cd}} = \frac{{f_{{ck}}}}{{\gamma_c}} = \frac{{{fck:.1f}}}{{1.5}} = {fcd:.2f}\,\text{{MPa}}, \quad f_{{yd}} = \frac{{f_{{yk}}}}{{\gamma_s}} = \frac{{{fyk:.0f}}}{{1.15}} = {fyd:.2f}\,\text{{MPa}}")
            st.latex(rf"E_{{cd}} = \frac{{E_{{cm}}}}{{1.2}} = \frac{{{Ecm:.0f}}}{{1.2}} = {Ecd:.0f}\,\text{{MPa}}")
            st.latex(rf"d_2 = c_{{nom}} + \phi_w + \frac{{\phi_s}}{{2}} = {c_nom*1000:.0f} + {phi_w*1000:.0f} + {phi_s*1000/2:.1f} = {d2*1000:.1f}\,\text{{mm}}")
            st.latex(rf"d_y = h - d_2 = {h*1000:.1f} - {d2*1000:.1f} = {d_y*1000:.1f}\,\text{{mm}}, \quad d_z = b - d_2 = {b*1000:.1f} - {d2*1000:.1f} = {d_z*1000:.1f}\,\text{{mm}}")
            
            st.markdown("#### 3. Wpływ pełzania (EC2: 5.8.4)")
            st.latex(rf"h_0 = \frac{{2 A_c}}{{u}} = {h0:.1f}\,\text{{mm}} \implies \varphi(\infty, t_0) = {phi_RH * beta_fcm * beta_t0:.2f}")
            st.latex(rf"\varphi_{{ef}} = \varphi(\infty, t_0) \cdot \frac{{M_{{0Eqp}}}}{{M_{{0Ed}}}} = {(phi_RH * beta_fcm * beta_t0):.2f} \cdot {m_ratio:.2f} = {phi_eff:.3f}")
            
            st.markdown("#### 4. Efekty II rzędu i sztywność - Kierunek Y (EC2: 5.8.7.2)")
            st.latex(rf"l_{{0,y}} = \beta_y L = {beta_y:.2f} \cdot {L_m:.2f} = {l0_y:.2f}\,\text{{m}}, \quad i_y = \frac{{h}}{{\sqrt{{12}}}} = {iy*100:.1f}\,\text{{cm}} \implies \lambda_y = {lambda_y:.1f}")
            st.latex(rf"k_1 = \sqrt{{\frac{{f_{{ck}}}}{{20}}}} = {k1:.3f}, \quad k_{{2,y}} = \min\left(\frac{{n \cdot \lambda_y}}{{170}}, 0.20\right) = {k2_y:.3f}")
            st.latex(rf"K_{{c,y}} = \frac{{k_1 k_{{2,y}}}}{{1 + \varphi_{{ef}}}} = \frac{{{k1:.3f} \cdot {k2_y:.3f}}}{{1 + {phi_eff:.3f}}} = {Kc_y:.4f}")
            st.latex(rf"EI_y = K_{{c,y}} E_{{cd}} I_{{c,y}} + E_s I_{{s,y}} = {EI_y_fin:.2f}\,\text{{MNm}}^2")
            st.latex(rf"N_{{B,y}} = \frac{{\pi^2 EI_y}}{{l_{{0,y}}^2}} = {NB_y_fin*1000:.1f}\,\text{{kN}}")
            st.latex(rf"M_{{Ed,y}}^{{II}} = \frac{{M_{{0Ed,y}}}}{{1 - N_{{Ed}}/N_{{B,y}}}} = \frac{{{M0y*1000:.1f}}}{{1 - {NEd*1000:.1f}/{NB_y_fin*1000:.1f}}} = {M_Ed_y_fin*1000:.2f}\,\text{{kNm}}")
            
            st.markdown("#### 5. Efekty II rzędu i sztywność - Kierunek Z (EC2: 5.8.7.2)")
            st.latex(rf"l_{{0,z}} = \beta_z L = {beta_z:.2f} \cdot {L_m:.2f} = {l0_z:.2f}\,\text{{m}}, \quad i_z = \frac{{b}}{{\sqrt{{12}}}} = {iz*100:.1f}\,\text{{cm}} \implies \lambda_z = {lambda_z:.1f}")
            st.latex(rf"k_1 = {k1:.3f}, \quad k_{{2,z}} = \min\left(\frac{{n \cdot \lambda_z}}{{170}}, 0.20\right) = {k2_z:.3f}")
            st.latex(rf"K_{{c,z}} = \frac{{k_1 k_{{2,z}}}}{{1 + \varphi_{{ef}}}} = \frac{{{k1:.3f} \cdot {k2_z:.3f}}}{{1 + {phi_eff:.3f}}} = {Kc_z:.4f}")
            st.latex(rf"EI_z = K_{{c,z}} E_{{cd}} I_{{c,z}} + E_s I_{{s,z}} = {EI_z_fin:.2f}\,\text{{MNm}}^2")
            st.latex(rf"N_{{B,z}} = \frac{{\pi^2 EI_z}}{{l_{{0,z}}^2}} = {NB_z_fin*1000:.1f}\,\text{{kN}}")
            st.latex(rf"M_{{Ed,z}}^{{II}} = \frac{{M_{{0Ed,z}}}}{{1 - N_{{Ed}}/N_{{B,z}}}} = \frac{{{M0z*1000:.1f}}}{{1 - {NEd*1000:.1f}/{NB_z_fin*1000:.1f}}} = {M_Ed_z_fin*1000:.2f}\,\text{{kNm}}")

            st.markdown("#### 6. Nośność i interakcja zginania dwukierunkowego (EC2: 5.8.9)")
            st.latex(rf"N_{{Rd}} = A_c f_{{cd}} + A_{{s,tot,req}} f_{{yd}} = {N_Rd_fin*1000:.1f}\,\text{{kN}} \implies n_{{rel}} = \frac{{N_{{Ed}}}}{{N_{{Rd}}}} = {n_rel_fin:.3f}")
            st.latex(rf"M_{{Rd,y}} = {MRd_y_fin*1000:.2f}\,\text{{kNm}} \quad \text{{(dla zbrojenia req. }} A_{{s1}} = {As1_cm2:.2f}\,\text{{cm}}^2)")
            st.latex(rf"M_{{Rd,z}} = {MRd_z_fin*1000:.2f}\,\text{{kNm}} \quad \text{{(dla zbrojenia req. }} A_{{s2}} = {As2_cm2:.2f}\,\text{{cm}}^2)")
            st.latex(rf"\text{{Wykładnik interakcji }} a = {a_exp_fin:.2f}")
            st.latex(rf"\eta = \left( \frac{{M_{{Ed,y}}^{{II}}}}{{M_{{Rd,y}}}} \right)^a + \left( \frac{{M_{{Ed,z}}^{{II}}}}{{M_{{Rd,z}}}} \right)^a = \left( \frac{{{M_Ed_y_fin*1000:.2f}}}{{{MRd_y_fin*1000:.2f}}} \right)^{{{a_exp_fin:.2f}}} + \left( \frac{{{M_Ed_z_fin*1000:.2f}}}{{{MRd_z_fin*1000:.2f}}} \right)^{{{a_exp_fin:.2f}}} = {eta_fin:.3f}")

def run():
    render_column_page()

if __name__ == "__main__":
    run()