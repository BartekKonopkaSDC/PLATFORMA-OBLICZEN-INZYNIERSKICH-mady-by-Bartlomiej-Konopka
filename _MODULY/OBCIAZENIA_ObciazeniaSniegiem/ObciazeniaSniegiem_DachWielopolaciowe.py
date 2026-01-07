import streamlit as st
import math
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# --------------------------------------------------------------------------------------
# 1. BAZA DANYCH MIAST (STREFY I WYSOKOŚCI)
# --------------------------------------------------------------------------------------
MIASTA_DB = {
    "Białystok":            {"strefa": "4", "A": 150},
    "Bielsko-Biała":        {"strefa": "3", "A": 330},
    "Bydgoszcz":            {"strefa": "2", "A": 60},
    "Bytom":                {"strefa": "2", "A": 280},
    "Chełm":                {"strefa": "3", "A": 190},
    "Chorzów":              {"strefa": "2", "A": 280},
    "Częstochowa":          {"strefa": "2", "A": 260},
    "Dąbrowa Górnicza":     {"strefa": "2", "A": 270},
    "Elbląg":               {"strefa": "3", "A": 10},
    "Gdańsk":               {"strefa": "3", "A": 15},
    "Gdynia":               {"strefa": "3", "A": 30},
    "Gliwice":              {"strefa": "2", "A": 220},
    "Gorzów Wielkopolski":  {"strefa": "1", "A": 20},
    "Grudziądz":            {"strefa": "2", "A": 50},
    "Jelenia Góra":         {"strefa": "3", "A": 350},
    "Kalisz":               {"strefa": "2", "A": 140},
    "Katowice":             {"strefa": "2", "A": 270},
    "Kielce":               {"strefa": "3", "A": 260},
    "Konin":                {"strefa": "2", "A": 100},
    "Koszalin":             {"strefa": "2", "A": 35},
    "Kraków":               {"strefa": "3", "A": 220},
    "Legnica":              {"strefa": "1", "A": 120},
    "Lublin":               {"strefa": "3", "A": 200},
    "Łódź":                 {"strefa": "2", "A": 220},
    "Nowy Sącz":            {"strefa": "3", "A": 300},
    "Olsztyn":              {"strefa": "4", "A": 140},
    "Opole":                {"strefa": "2", "A": 175},
    "Płock":                {"strefa": "2", "A": 100},
    "Poznań":               {"strefa": "2", "A": 85},
    "Radom":                {"strefa": "2", "A": 180},
    "Ruda Śląska":          {"strefa": "2", "A": 270},
    "Rybnik":               {"strefa": "2", "A": 240},
    "Rzeszów":              {"strefa": "3", "A": 220},
    "Siedlce":              {"strefa": "3", "A": 155},
    "Sosnowiec":            {"strefa": "2", "A": 260},
    "Suwałki":              {"strefa": "4", "A": 170},
    "Szczecin":             {"strefa": "1", "A": 25},
    "Tarnów":               {"strefa": "3", "A": 210},
    "Toruń":                {"strefa": "2", "A": 50},
    "Tychy":                {"strefa": "2", "A": 260},
    "Wałbrzych":            {"strefa": "3", "A": 450},
    "Warszawa":             {"strefa": "2", "A": 110},
    "Włocławek":            {"strefa": "2", "A": 65},
    "Wrocław":              {"strefa": "1", "A": 120},
    "Zabrze":               {"strefa": "2", "A": 260},
    "Zakopane":             {"strefa": "5", "A": 850},
    "Zielona Góra":         {"strefa": "1", "A": 150},
}

# --------------------------------------------------------------------------------------
# 2. FUNKCJE OBLICZENIOWE I POMOCNICZE
# --------------------------------------------------------------------------------------

def calculate_ct_iso(U_val, Ti_val):
    """Oblicza Ct wg uproszczonej logiki ISO 4355."""
    if U_val <= 1.0: return 1.0
    delta_T = Ti_val - (-5.0) 
    if delta_T < 0: delta_T = 0
    redukcja = 0.0025 * (U_val - 1.0) * delta_T
    ct = 1.0 - redukcja
    if ct < 0.5: ct = 0.5
    if ct > 1.0: ct = 1.0
    return round(ct, 2)

def calculate_mu1(alpha):
    """Oblicza współczynnik kształtu dachu mu1 wg PN-EN 1991-1-3 Tablica 5.2."""
    if alpha < 0: return 0.8
    if 0 <= alpha <= 30:
        return 0.8
    elif 30 < alpha < 60:
        return 0.8 * (60.0 - alpha) / 30.0
    else: # alpha >= 60
        return 0.0

def calculate_mu2(alpha):
    """
    Oblicza współczynnik kształtu mu2 wg PN-EN 1991-1-3 Tablica 5.2.
    """
    if alpha <= 30:
        return 0.8 + 0.8 * (alpha / 30.0)
    else:
        return 1.6

def plot_mu_coefficients():
    """Generuje wykres mu1 i mu2 w funkcji kąta alfa (0-60 stopni)."""
    alphas = np.linspace(0, 60, 100)
    mu1_vals = [calculate_mu1(a) for a in alphas]
    mu2_vals = [calculate_mu2(a) for a in alphas]

    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(alphas, mu1_vals, label=r'$\mu_1$', color='blue', linewidth=2)
    ax.plot(alphas, mu2_vals, label=r'$\mu_2$', color='green', linewidth=2)
    
    ax.set_xlabel(r'Kąt nachylenia połaci $\alpha$ [°]')
    ax.set_ylabel(r'Współczynnik kształtu $\mu$')
    
    ax.set_title('Współczynniki kształtu dachu')
    
    ax.set_yticks(np.arange(0, 1.9, 0.2))
    
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.legend()
    ax.set_xlim(0, 60)
    ax.set_ylim(0, 1.8)
    plt.tight_layout()
    
    return fig

def plot_multi_roof(angles, loads_tuples, label_positions=None, max_load_ref=None):
    """
    Generuje wykres Matplotlib dla dachu wielopołaciowego.
    """
    if label_positions is None:
        label_positions = ['auto', 'auto', 'auto', 'auto']

    a1_L, a2_L, a1_P, a2_P = angles
    (s1_L_s, s1_L_e), (s1_P_s, s1_P_e), (s2_L_s, s2_L_e), (s2_P_s, s2_P_e) = loads_tuples
    
    # --- GEOMETRIA ---
    W_bldg = 10.0 # Szerokość umowna jednego budynku
    
    # Konwersja na radiany
    r1_L = math.radians(max(a1_L, 2))
    r1_P = math.radians(max(a2_L, 2))
    r2_L = math.radians(max(a1_P, 2))
    r2_P = math.radians(max(a2_P, 2))
    
    # Budynek Lewy
    denom1 = (1.0/math.tan(r1_L) + 1.0/math.tan(r1_P))
    h1 = W_bldg / denom1
    x_peak1 = h1 / math.tan(r1_L)
    
    # Budynek Prawy
    denom2 = (1.0/math.tan(r2_L) + 1.0/math.tan(r2_P))
    h2 = W_bldg / denom2
    x_peak2_local = h2 / math.tan(r2_L)
    x_peak2 = W_bldg + x_peak2_local
    
    # Poziomy odniesienia
    wall_depth = 2.5
    ground_y = -wall_depth
    total_W = 2 * W_bldg
    
    fig, ax = plt.subplots(figsize=(8, 7.0))
    
    # 1. RYSUNEK KONSTRUKCJI
    # Grunt
    ground_rect = patches.Rectangle(
        (-2, ground_y - 1.0), total_W + 4, 1.0, 
        facecolor='white', edgecolor='gray', hatch='///', linewidth=0, zorder=0
    )
    ax.add_patch(ground_rect)
    ax.plot([-2, total_W + 2], [ground_y, ground_y], color='black', linewidth=1.5)

    # Ściany
    ax.plot([0, 0], [ground_y, 0], color='black', linewidth=2.5)
    ax.plot([W_bldg, W_bldg], [ground_y, 0], color='black', linewidth=2.5)
    ax.plot([total_W, total_W], [ground_y, 0], color='black', linewidth=2.5)

    # Dach
    ax.plot([0, x_peak1, W_bldg], [0, h1, 0], color='black', linewidth=2.5, zorder=10)
    ax.plot([W_bldg, x_peak2, total_W], [0, h2, 0], color='black', linewidth=2.5, zorder=10)
    
    # 2. OZNACZENIA KĄTÓW
    def draw_angle_annotation(x_base, y_base, angle_val, label, is_left_oriented):
        draw_ang = max(min(angle_val, 80), 2)
        marker_len = 2.0
        if is_left_oriented:
            ax.plot([x_base, x_base + marker_len], [y_base, y_base], color='black', linestyle='--', linewidth=1.0)
            arc = patches.Arc((x_base, y_base), marker_len*0.8, marker_len*0.8, theta1=0, theta2=draw_ang, color='black')
            ax.add_patch(arc)
            ax.text(x_base + marker_len*0.5, y_base - 0.4, f"${label}={angle_val:.0f}^\\circ$", fontsize=10, ha='left', va='top')
        else:
            ax.plot([x_base, x_base - marker_len], [y_base, y_base], color='black', linestyle='--', linewidth=1.0)
            arc = patches.Arc((x_base, y_base), marker_len*0.8, marker_len*0.8, theta1=180-draw_ang, theta2=180, color='black')
            ax.add_patch(arc)
            ax.text(x_base - marker_len*0.5, y_base - 0.4, f"${label}={angle_val:.0f}^\\circ$", fontsize=10, ha='right', va='top')

    draw_angle_annotation(0, 0, a1_L, "\\alpha_{1.L}", True)
    draw_angle_annotation(W_bldg, 0, a2_L, "\\alpha_{2.L}", False)
    draw_angle_annotation(W_bldg, 0, a1_P, "\\alpha_{1.P}", True)
    draw_angle_annotation(total_W, 0, a2_P, "\\alpha_{2.P}", False)

    # 3. RYSOWANIE OBCIĄŻENIA (Trapezowe)
    max_h = max(h1, h2)
    load_base_y = max_h + 1.0
    scale_factor = 2.0
    color = '#1f77b4'
    
    def draw_trapezoid_load(sx, ex, v_start, v_end, label_pos='auto'):
        """
        Rysuje obciążenie i etykiety.
        """
        if max(v_start, v_end) <= 0.01: return
        
        h_start = v_start * scale_factor
        h_end = v_end * scale_factor
        
        # Wierzchołki trapezu
        verts = [
            (sx, load_base_y),
            (ex, load_base_y),
            (ex, load_base_y + h_end),
            (sx, load_base_y + h_start)
        ]
        
        poly = patches.Polygon(verts, closed=True, linewidth=1.2, edgecolor=color, facecolor=color, alpha=0.15)
        ax.add_patch(poly)
        
        # Linie obrysu
        ax.plot([sx, ex], [load_base_y, load_base_y], color='gray', linewidth=0.5) # Baza
        ax.plot([sx, ex], [load_base_y + h_start, load_base_y + h_end], color=color, linewidth=2) # Góra
        ax.plot([sx, sx], [load_base_y, load_base_y + h_start], color=color, linewidth=1) # Bok lewy
        ax.plot([ex, ex], [load_base_y, load_base_y + h_end], color=color, linewidth=1)   # Bok prawy
        
        # Strzałki (interpolacja liniowa)
        width = ex - sx
        n_arrows = max(2, int(width * 0.8))
        arrow_x = np.linspace(sx, ex, n_arrows+2)[1:-1]
        for ax_x in arrow_x:
            rel_pos = (ax_x - sx) / width
            curr_h = h_start + (h_end - h_start) * rel_pos
            ax.arrow(ax_x, load_base_y + curr_h, 0, -curr_h + 0.1, 
                     head_width=0.15, head_length=0.15, 
                     fc=color, ec=color, length_includes_head=True)
        
        # --- ETYKIETY ---
        unit_str = " kN/m²"
        
        # Helper do rysowania tekstu
        def plot_text(x, y_h, val):
            ax.text(x, load_base_y + y_h + 0.2, f"{val:.2f}{unit_str}", 
                    ha='center', va='bottom', fontsize=9, fontweight='bold')

        if label_pos == 'none':
            return
        
        if label_pos == 'auto':
            # Jeśli wartości zbliżone (prostokąt) -> jedna etykieta na środku
            if abs(v_start - v_end) < 0.05:
                plot_text(sx + width/2, h_start, v_start)
            else:
                # Domyślnie dwie
                plot_text(sx, h_start, v_start)
                plot_text(ex, h_end, v_end)
        elif label_pos == 'start':
            # Tylko na początku (sx)
            plot_text(sx, h_start, v_start)
        elif label_pos == 'end':
            # Tylko na końcu (ex)
            plot_text(ex, h_end, v_end)

    # Wywołania dla 4 odcinków (z użyciem przekazanych ustawień etykiet)
    # 1. B1 Lewa
    draw_trapezoid_load(0, x_peak1, s1_L_s, s1_L_e, label_pos=label_positions[0])
    # 2. B1 Prawa
    draw_trapezoid_load(x_peak1, W_bldg, s1_P_s, s1_P_e, label_pos=label_positions[1])
    # 3. B2 Lewa
    draw_trapezoid_load(W_bldg, x_peak2, s2_L_s, s2_L_e, label_pos=label_positions[2])
    # 4. B2 Prawa
    draw_trapezoid_load(x_peak2, total_W, s2_P_s, s2_P_e, label_pos=label_positions[3])

    ax.set_aspect('equal')
    ax.axis('off')
    
    # Skalowanie wykresu - SZTYWNY LIMIT Y, ABY WYKRESY MIAŁY TĄ SAMĄ WYSOKOŚĆ
    if max_load_ref is None:
        all_vals = [s1_L_s, s1_L_e, s1_P_s, s1_P_e, s2_L_s, s2_L_e, s2_P_s, s2_P_e]
        max_s_val = max(all_vals) if all_vals else 1.0
    else:
        max_s_val = max_load_ref
        
    top_limit = load_base_y + (max_s_val * scale_factor) + 2.0
    ax.set_ylim(ground_y - 0.5, top_limit)
    ax.set_xlim(-2.5, total_W + 2.5)
    
    plt.tight_layout()
    return fig

# --------------------------------------------------------------------------------------
# 3. GŁÓWNA LOGIKA APLIKACJI
# --------------------------------------------------------------------------------------
def run():
    # Inicjalizacja Session State
    if "dw_sk" not in st.session_state: st.session_state["dw_sk"] = 0.0

    # Style CSS
    st.markdown(
        """
        <style>
        button[kind="primary"] {
            background: #ff4b4b !important;
            border: none !important;
            border-radius: 12px !important;
            height: 52px !important;
            font-size: 17px !important;
            font-weight: 900 !important;
            letter-spacing: 0.5px !important;
        }
        button[kind="primary"]:hover { filter: brightness(0.95); }
        div.row-widget.stRadio > div { flex-direction: row; gap: 20px; }
        .stCaption { margin-top: -10px; margin-bottom: 10px; }
        
        .streamlit-expanderHeader {
            font-weight: bold;
            font-size: 1.1em;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    current_dir = os.path.dirname(os.path.abspath(__file__))
    mapa_path = os.path.join(current_dir, "mapa_stref.png")

    # --- MAPA STREF ---
    with st.expander("🗺️ Mapa stref śniegowych wg PN-EN 1991-1-3"):
        if os.path.exists(mapa_path):
            m1, m2, m3 = st.columns([1, 2, 1])
            with m2: st.image(mapa_path) 
        else:
            st.warning("Brak pliku 'mapa_stref.png'.")

    # ==================================================================================
    # 1. DANE WEJŚCIOWE
    # ==================================================================================
    st.markdown("### DANE WEJŚCIOWE")

    # -------------------------------------------------------------------------
    # KOLUMNA 1: Miasto, Strefa, Wysokość
    # -------------------------------------------------------------------------
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("Czy chcesz wybrać miejscowość z listy?")
        city_mode = st.radio(
            "city_mode_label",
            ["Nie", "Tak"],
            index=0,
            label_visibility="collapsed",
            key="dw_city_mode",
            horizontal=True
        )
    
        use_city = (city_mode == "Tak")
        sel_strefa_index = 1
        default_A = 200.0
        disable_strefa = False

        if use_city:
            lista_miast = sorted(list(MIASTA_DB.keys()))
            idx_krakow = lista_miast.index("Kraków") if "Kraków" in lista_miast else 0
            
            wybrane_miasto = st.selectbox(
                "Wybierz miasto:", 
                lista_miast, 
                index=idx_krakow, 
                key="dw_city",
                on_change=update_city_defaults
            )
            
            dane_miasta = MIASTA_DB[wybrane_miasto]
            strefy_options = ["1", "2", "3", "4", "5"]
            try:
                sel_strefa_index = strefy_options.index(dane_miasta["strefa"])
            except ValueError:
                sel_strefa_index = 1
            default_A = float(dane_miasta["A"])
            disable_strefa = True

        strefa = st.selectbox(
            "Strefa obciążenia śniegiem",
            options=["1", "2", "3", "4", "5"],
            index=sel_strefa_index,
            disabled=disable_strefa,
            help="Numer strefy zgodnie z Załącznikiem Krajowym NA do PN-EN 1991-1-3.",
            key="dw_strefa"
        )
        if disable_strefa:
            st.caption(f"🔒 Strefa przypisana dla: {wybrane_miasto}")

        A = st.number_input(
            "Wysokość nad poziomem morza $A$ [m]",
            value=default_A,
            step=10.0,
            format="%.1f",
            key="dw_A"
        )
        if use_city: st.caption("⚠️ Podano średnią wysokość dla miejscowości.")

    # -------------------------------------------------------------------------
    # KOLUMNA 2: Ce, Ct
    # -------------------------------------------------------------------------
    with col2:
        teren_dict = {
            "Normalny": 1.0,
            "Wystawiony na wiatr": 0.8,
            "Osłonięty": 1.2
        }
        typ_terenu = st.selectbox(
            "Typ terenu",
            options=list(teren_dict.keys()),
            index=0,
            help="Decyduje o współczynniku ekspozycji Ce.",
            key="dw_teren"
        )
        
        with st.expander("ℹ️ Tablica 5.1 – Współczynnik ekspozycji Cₑ"):
            st.markdown(
                """
                | Typ terenu | $C_e$ | Opis |
                | :--- | :---: | :--- |
                | **Wystawiony** | 0,8 | Teren płaski, bez przeszkód, wystawiony na działanie wiatru z każdej strony, bez osłon lub z niewielkimi osłonami utworzonymi przez teren, inne budowle lub drzewa. |
                | **Normalny** | 1,0 | Teren, na którym nie występuje znaczne przenoszenie śniegu przez wiatr na budowle z powodu ukształtowania terenu, innych budowli lub drzew. |
                | **Osłonięty** | 1,2 | Teren, w którym rozpatrywana budowla jest znacznie niższa niż otaczający teren albo jest otoczona wysokimi drzewami lub/i wyższymi budowlami. |
                """
            )
        
        current_Ce = teren_dict[typ_terenu]
        st.text_input("Współczynnik ekspozycji $C_e$", value=str(current_Ce), disabled=True, key="dw_Ce_disp")

        st.markdown(r"Czy dach ma przenikalność ciepła $U > 1 \, \small \frac{W}{m^2 \cdot K}$?")
        ct_mode = st.radio("ct_mode_label", ["Nie", "Tak"], index=0, label_visibility="collapsed", key="dw_ct_mode", horizontal=True)
        
        Ct_val = 1.0
        if ct_mode == "Tak":
            c_u, c_ti = st.columns(2)
            with c_u: U_input = st.number_input("Wsp. $U$", value=2.0, step=0.1, min_value=1.0, key="dw_U")
            with c_ti: Ti_input = st.number_input("Temp. wew. $T_i$", value=18.0, step=1.0, key="dw_Ti")
            Ct_val = calculate_ct_iso(U_input, Ti_input)
            st.text_input("Współczynnik termiczny $C_t$", value=str(Ct_val), disabled=True, key="dw_ct_disp_yes")
        else:
            st.text_input("Współczynnik termiczny $C_t$", value="1.0", disabled=True, key="dw_ct_disp_no")

    # -------------------------------------------------------------------------
    # KOLUMNA 3: Bariery + Geometria
    # -------------------------------------------------------------------------
    with col3:
        st.markdown("**Czy na dachu znajdują się bariery przeciwśnieżne?**")
        snow_guards = st.radio(
            "snow_guards_label",
            ["Nie", "Tak"],
            index=0,
            label_visibility="collapsed",
            key="dw_snow_guards",
            horizontal=True
        )

        st.write("Czy nachylenie połaci jest jednakowe?")
        diff_slopes = st.radio("diff_slopes", ["Tak", "Nie"], index=0, label_visibility="collapsed", key="dw_diff_slopes", horizontal=True)
        
        alpha_L1, alpha_P1 = 30.0, 30.0
        alpha_L2, alpha_P2 = 30.0, 30.0
        
        if diff_slopes == "Tak": 
            # Jedno pod drugim
            a1 = st.number_input(r"Kąt nachylenia połaci budynku pierszego $\alpha_{1,2.L}$ [°]", value=30.0, step=1.0, key="dw_a1")
            alpha_L1 = a1
            alpha_P1 = a1
            
            a2 = st.number_input(r"Kąt nachylenia połaci budynku drugiego $\alpha_{1,2.P}$ [°]", value=30.0, step=1.0, key="dw_a2")
            alpha_L2 = a2
            alpha_P2 = a2
        else: 
            st.write("Kąt nachylenia połaci budynku pierwszego:")
            c3c, c3d = st.columns(2)
            with c3c: alpha_L1 = st.number_input("Połać Lewa $\\alpha_{1.L}$", value=30.0, step=1.0, key="dw_aL1")
            with c3d: alpha_P1 = st.number_input("Połać Prawa $\\alpha_{2.L}$", value=30.0, step=1.0, key="dw_aP1")
            
            st.write("Kąt nachylenia połaci budynku drugiego:")
            c3e, c3f = st.columns(2)
            with c3e: alpha_L2 = st.number_input("Połać Lewa $\\alpha_{1.P}$", value=45.0, step=1.0, key="dw_aL2")
            with c3f: alpha_P2 = st.number_input("Połać Prawa $\\alpha_{2.P}$", value=45.0, step=1.0, key="dw_aP2")

        with st.expander("ℹ️ Tablica 5.2 – Współcz. kształtu dachu $\mu_1$, $\mu_2$"):
            if snow_guards == "Tak":
                st.info("⚠️ **Wybrano bariery przeciwśnieżne.**")
                st.markdown(
                    """
                    Zgodnie z **PN-EN 1991-1-3 p. 5.2(7)**:
                    > *W przypadku gdy śnieg nie może zsuwać się z dachu na skutek zakończenia go attyką lub występowania innych przeszkód (np. płotki przeciwśnieżne) współczynnik kształtu dachu powinien wynosić co najmniej **0,8**.*
                    
                    Przyjęto: $\mu_1 = 0,8$ (niezależnie od kąta nachylenia).
                    """
                )
            else:
                # Zmieniono wielkość czcionki w tabeli używając HTML
                st.markdown(
                    """
                    <div style="font-size: small;">

                    | Kąt nachylenia $\\alpha$ | $\\mu_1$ | $\\mu_2$ |
                    | :--- | :--- | :--- |
                    | $0^\\circ \\le \\alpha \\le 30^\\circ$ | $0,8$ | $0,8 + 0,8 \\cdot \\frac{\\alpha}{30}$ |
                    | $30^\\circ < \\alpha < 60^\\circ$ | $0,8 \\cdot \\frac{60 - \\alpha}{30}$ | $1,6$ |
                    | $\\alpha \\ge 60^\\circ$ | $0,0$ | $1,6$ |
                    
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                st.pyplot(plot_mu_coefficients(), use_container_width=True)

    
    b1, b2, b3 = st.columns([1, 2, 1])
    oblicz_clicked = False
    with b2:
        if st.button("OBLICZ", type="primary", use_container_width=True, key="dw_btn"):
            oblicz_clicked = True

    if oblicz_clicked:
        # 1. Sk
        Ce = current_Ce
        Ct = Ct_val
        
        sk_calc = 0.0
        if strefa == "1":
            formula_val = 0.007 * A - 1.4
            sk_calc = max(formula_val, 0.7) if A <= 300 else formula_val
        elif strefa == "2":
            sk_calc = 0.9 if A <= 300 else 0.007 * A - 1.4
        elif strefa == "3":
            formula_val = 0.006 * A - 0.6
            sk_calc = max(formula_val, 1.2) if A <= 300 else formula_val
        elif strefa == "4":
            sk_calc = 1.6 if A <= 300 else 0.006 * A - 0.6
        elif strefa == "5":
            formula_val = 0.93 * math.exp(0.00134 * A)
            sk_calc = max(formula_val, 2.0)
        
        sk = round(sk_calc, 3)
        st.session_state["dw_sk"] = sk

        # 2. Obliczenia współczynników
        if snow_guards == "Tak":
            mu1_L1 = 0.8
            mu1_P1 = 0.8
            mu1_L2 = 0.8
            mu1_P2 = 0.8
        else:
            mu1_L1 = calculate_mu1(alpha_L1)
            mu1_P1 = calculate_mu1(alpha_P1)
            mu1_L2 = calculate_mu1(alpha_L2)
            mu1_P2 = calculate_mu1(alpha_P2)
        
        # Mu2 dla kosza (średnia)
        alpha_mean = (alpha_P1 + alpha_L2) / 2.0
        mu2_val = calculate_mu2(alpha_mean)

        # 3. Przypadki obciążenia
        
        # (i) Jednorodne
        loads_i = [
            (mu1_L1*Ce*Ct*sk, mu1_L1*Ce*Ct*sk),
            (mu1_P1*Ce*Ct*sk, mu1_P1*Ce*Ct*sk),
            (mu1_L2*Ce*Ct*sk, mu1_L2*Ce*Ct*sk),
            (mu1_P2*Ce*Ct*sk, mu1_P2*Ce*Ct*sk)
        ]
        s_i_L1 = mu1_L1 * Ce * Ct * sk
        s_i_P1 = mu1_P1 * Ce * Ct * sk
        s_i_L2 = mu1_L2 * Ce * Ct * sk
        s_i_P2 = mu1_P2 * Ce * Ct * sk

        # (ii) Zaspa w koszu
        s_valley = mu2_val * Ce * Ct * sk
        
        # B1 Lewa
        s_ii_L1 = s_i_L1
        # B1 Prawa (do kosza) - rośnie od s_i_P1 do s_valley
        s_P1_ridge = s_i_P1
        # B2 Lewa (z kosza) - maleje od s_valley do s_i_L2
        s_L2_ridge = s_i_L2
        # B2 Prawa
        s_ii_P2 = s_i_P2
        
        loads_ii = [
            (s_ii_L1, s_ii_L1),
            (s_P1_ridge, s_valley),
            (s_valley, s_L2_ridge),
            (s_ii_P2, s_ii_P2)
        ]
        
        # OBLICZENIE MAX DO SKALOWANIA WSPÓLNEGO
        all_vals_combined = [
            s_i_L1, s_i_P1, s_i_L2, s_i_P2,
            s_ii_L1, s_P1_ridge, s_valley, s_L2_ridge, s_ii_P2
        ]
        max_load_common = max(all_vals_combined) if all_vals_combined else 1.0

        # ==============================================================================
        # 3. WYNIKI - DWIE KOLUMNY OBOK SIEBIE
        # ==============================================================================
        st.markdown("### WYNIKI")

        col_res1, col_res2 = st.columns(2)

        # LEWA KOLUMNA: Przypadek (i)
        with col_res1:
            st.markdown("**Przypadek (i) – Obciążenie równomierne**")
            fig_i = plot_multi_roof(
                [alpha_L1, alpha_P1, alpha_L2, alpha_P2],
                loads_i,
                label_positions=['auto', 'auto', 'auto', 'auto'],
                max_load_ref=max_load_common
            )
            st.pyplot(fig_i, use_container_width=True)

        # PRAWA KOLUMNA: Przypadek (ii)
        with col_res2:
            st.markdown("**Przypadek (ii) – Obciążenie zaspą w koszu**")
            fig_ii = plot_multi_roof(
                [alpha_L1, alpha_P1, alpha_L2, alpha_P2],
                loads_ii,
                label_positions=['auto', 'end', 'none', 'auto'],
                max_load_ref=max_load_common
            )
            st.pyplot(fig_ii, use_container_width=True)

        # ==============================================================================
        # 4. SZCZEGÓŁY OBLICZEŃ
        # ==============================================================================
        with st.expander("Szczegóły obliczeń"):
            # 1. DANE
            st.markdown("#### 1. Podstawowe dane")
            st.write(f"Strefa śniegowa: **{strefa}**")
            st.write(f"Wysokość nad poziomem morza: $A = {A:.2f} \\text{{ m n.p.m.}}$")
            st.write(f"Współczynnik ekspozycji: $C_e = {Ce}$")
            st.write(f"Współczynnik termiczny: $C_t = {Ct}$")
            
            if snow_guards == "Tak":
                st.write("Bariery przeciwśnieżne: **TAK** (wymusza $\\mu_1 \\ge 0,8$)")
            else:
                st.write("Bariery przeciwśnieżne: **NIE** (standardowy ześlizg śniegu)")

            st.write(f"Obciążenie śniegiem gruntu: **$s_k = {sk:.2f} \\text{{ kN/m}}^2$**")
            
            st.write("Kąty nachylenia i współczynniki kształtu:")
            st.write(f"- Kąt nachylenia połaci budynku pierwszego: $\\alpha_{{1.L}}={alpha_L1}^\\circ (\\mu_1={mu1_L1:.3f}), \\quad \\alpha_{{2.L}}={alpha_P1}^\\circ (\\mu_1={mu1_P1:.3f})$")
            st.write(f"- Kąt nachylenia połaci budynku drugiego: $\\alpha_{{1.P}}={alpha_L2}^\\circ (\\mu_1={mu1_L2:.3f}), \\quad \\alpha_{{2.P}}={alpha_P2}^\\circ (\\mu_1={mu1_P2:.3f})$")
            
            st.markdown(r"Średni kąt w koszu: $\bar{\alpha} = \frac{" + f"{alpha_P1:.1f} + {alpha_L2:.1f}" + r"}{2} = " + f"{alpha_mean:.1f}^\\circ$")
            st.markdown(f"Współczynnik kształtu w koszu: **$\\mu_2(\\bar{{\\alpha}}) = {mu2_val:.3f}$**")
            
            if alpha_mean >= 60:
                st.warning("⚠️ Uwaga: Jedna lub obie połacie są nachylone do środka zagłębienia pod kątem > 60°. Należy zwrócić szczególną uwagę na wartości współczynnika kształtu (PN-EN 1991-1-3 p. 5.3.4 (4)). Wg kalkulatora przyjęto 1.6.")

            # 2. OBLICZENIA
            st.markdown("#### 2. Wyniki szczegółowe")
            
            # (i)
            st.markdown("**Przypadek (i) – Obciążenie równomierne**")
            
            # Przywrócono wyświetlanie wykresu (i) w sekcji szczegółowej
            c1_i_d, c2_i_d, c3_i_d = st.columns([1, 2, 1])
            with c2_i_d:
                st.pyplot(fig_i, use_container_width=True)

            st.latex(r"s_{1.L} = \mu_1(\alpha_{1.L}) \cdot C_e \cdot C_t \cdot s_k = " + f"{mu1_L1:.3f} \\cdot {Ce} \\cdot {Ct} \\cdot {sk:.2f} \\, \\text{{kN/m}}^2 = \\mathbf{{{s_i_L1:.2f}}} \\, \\text{{kN/m}}^2")
            st.latex(r"s_{2.L} = \mu_1(\alpha_{2.L}) \cdot C_e \cdot C_t \cdot s_k = " + f"{mu1_P1:.3f} \\cdot {Ce} \\cdot {Ct} \\cdot {sk:.2f} \\, \\text{{kN/m}}^2 = \\mathbf{{{s_i_P1:.2f}}} \\, \\text{{kN/m}}^2")
            st.latex(r"s_{1.P} = \mu_1(\alpha_{1.P}) \cdot C_e \cdot C_t \cdot s_k = " + f"{mu1_L2:.3f} \\cdot {Ce} \\cdot {Ct} \\cdot {sk:.2f} \\, \\text{{kN/m}}^2 = \\mathbf{{{s_i_L2:.2f}}} \\, \\text{{kN/m}}^2")
            st.latex(r"s_{2.P} = \mu_1(\alpha_{2.P}) \cdot C_e \cdot C_t \cdot s_k = " + f"{mu1_P2:.3f} \\cdot {Ce} \\cdot {Ct} \\cdot {sk:.2f} \\, \\text{{kN/m}}^2 = \\mathbf{{{s_i_P2:.2f}}} \\, \\text{{kN/m}}^2")

            st.divider()

            # (ii)
            st.markdown("**Przypadek (ii) – Obciążenie zaspą w koszu**")
            
            # Przywrócono wyświetlanie wykresu (ii) w sekcji szczegółowej
            c1_ii, c2_ii, c3_ii = st.columns([1, 2, 1])
            with c2_ii: 
                st.pyplot(fig_ii, use_container_width=True)
            
            st.markdown("Połacie zewnętrzne:")
            st.latex(r"s_{1.L} = \mu_1(\alpha_{1.L}) \cdot C_e \cdot C_t \cdot s_k = " + f"{mu1_L1:.3f} \\cdot {Ce} \\cdot {Ct} \\cdot {sk:.2f} \\, \\text{{kN/m}}^2 = \\mathbf{{{s_ii_L1:.2f}}} \\, \\text{{kN/m}}^2")
            st.latex(r"s_{2.P} = \mu_1(\alpha_{2.P}) \cdot C_e \cdot C_t \cdot s_k = " + f"{mu1_P2:.3f} \\cdot {Ce} \\cdot {Ct} \\cdot {sk:.2f} \\, \\text{{kN/m}}^2 = \\mathbf{{{s_ii_P2:.2f}}} \\, \\text{{kN/m}}^2")

            st.markdown("Połacie wewnętrzne (w koszu):")
            
            st.latex(r"s_{kosz} = \mu_2(\bar{\alpha}) \cdot C_e \cdot C_t \cdot s_k = " + f"{mu2_val:.3f} \\cdot {Ce} \\cdot {Ct} \\cdot {sk:.2f} \\, \\text{{kN/m}}^2 = \\mathbf{{{s_valley:.2f}}} \\, \\text{{kN/m}}^2")

            st.markdown("Zmienność obciążenia (interpolacja):")
            st.latex(r"s_{2.L} (\text{od kalenicy}) = \mathbf{" + f"{s_P1_ridge:.2f}" + r"} \, \text{kN/m}^2 \longrightarrow s_{kosz} = \mathbf{" + f"{s_valley:.2f}" + r"} \, \text{kN/m}^2")
            st.latex(r"s_{kosz} = \mathbf{" + f"{s_valley:.2f}" + r"} \, \text{kN/m}^2 \longrightarrow s_{1.P} (\text{do kalenicy}) = \mathbf{" + f"{s_L2_ridge:.2f}" + r"} \, \text{kN/m}^2")

if __name__ == "__main__":
    run()