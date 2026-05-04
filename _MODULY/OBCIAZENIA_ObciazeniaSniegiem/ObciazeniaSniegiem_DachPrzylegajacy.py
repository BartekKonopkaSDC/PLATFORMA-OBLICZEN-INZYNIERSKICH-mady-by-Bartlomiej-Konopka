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

def plot_geometry_schema(alpha_deg):
    """
    Rysuje mały schemat pomocniczy w panelu bocznym (Input).
    Budynek wyższy (b1) jest dwuspadowy.
    Kąt dachu wyższego ustawiony na sztywno na 35 stopni dla celów poglądowych.
    """
    fig, ax = plt.subplots(figsize=(4, 2.5))
    
    # Parametry rysunkowe
    b1_draw = 2.5
    b2_draw = 2.0
    h_draw = 1.2
    ground_y = 0.0
    roof_low_y = 1.5
    roof_high_eave_y = roof_low_y + h_draw
    
    # Kąt do rysowania - NA STAŁE 35 STOPNI
    draw_alpha = 35.0
    rad = math.radians(draw_alpha)
    
    # Kalenica wyższego
    half_width = b1_draw / 2.0
    ridge_h = half_width * math.tan(rad)
    roof_high_ridge_y = roof_high_eave_y + ridge_h
    ridge_x = -half_width
    
    # --- RYSOWANIE ---
    
    # 1. Grunt
    ax.plot([-b1_draw - 0.5, b2_draw + 0.5], [ground_y, ground_y], 'k-', lw=1)
    
    # 2. Budynek WYŻSZY
    ax.plot([-b1_draw, -b1_draw], [ground_y, roof_high_eave_y], 'k-', lw=1.5)
    ax.plot([0, 0], [ground_y, roof_high_eave_y], 'k-', lw=1.5)
    ax.plot([-b1_draw, ridge_x], [roof_high_eave_y, roof_high_ridge_y], 'k-', lw=1.5)
    ax.plot([ridge_x, 0], [roof_high_ridge_y, roof_high_eave_y], 'k-', lw=1.5)
    
    # 3. Budynek NIŻSZY
    ax.plot([0, b2_draw], [roof_low_y, roof_low_y], 'k-', lw=1.5)
    ax.plot([b2_draw, b2_draw], [roof_low_y, ground_y], 'k-', lw=1.5)
    
    # --- OZNACZENIA ---
    # h
    ax.annotate("", xy=(-0.15, roof_low_y), xytext=(-0.15, roof_high_eave_y), arrowprops=dict(arrowstyle="<->", lw=0.8, color='blue'))
    ax.text(-0.3, (roof_low_y + roof_high_eave_y)/2, "$h$", ha='right', va='center', fontsize=11, color='blue')
    
    # b1
    ax.annotate("", xy=(-b1_draw, ground_y - 0.2), xytext=(0, ground_y - 0.2), arrowprops=dict(arrowstyle="<->", lw=0.8, color='blue'))
    ax.text(-b1_draw/2, ground_y - 0.5, "$b_1$", ha='center', va='top', fontsize=11, color='blue')
    
    # b2
    ax.annotate("", xy=(0, ground_y - 0.2), xytext=(b2_draw, ground_y - 0.2), arrowprops=dict(arrowstyle="<->", lw=0.8, color='blue'))
    ax.text(b2_draw/2, ground_y - 0.5, "$b_2$", ha='center', va='top', fontsize=11, color='blue')
    
    # Alpha1 (niebieski)
    ax.plot([0, -1.0], [roof_high_eave_y, roof_high_eave_y], color='blue', linestyle='--', lw=0.8)
    arc = patches.Arc((0, roof_high_eave_y), 1.5, 1.5, theta1=180-draw_alpha, theta2=180, color='blue', lw=1.5)
    ax.add_patch(arc)
    ax.text(-1.1, roof_high_eave_y + 0.2, "$\\alpha_1$", ha='right', va='bottom', fontsize=11, color='blue', fontweight='bold')

    ax.set_ylim(-0.8, roof_high_ridge_y + 0.5)
    ax.set_xlim(-b1_draw - 0.5, b2_draw + 0.5)
    ax.axis('off')
    plt.tight_layout()
    return fig

def plot_abutting_roof(b1, b2, h, alpha_high, s_s, s_w, s_base, ls, case_label):
    """
    Rysunek wynikowy z zaspą.
    Wyświetla wartości obciążeń w kN/m2.
    Kąt dachu wyższego jest DYNAMICZNY (zależy od alpha_high).
    """
    
    # Wartości całkowite
    s_total_peak = s_s + s_w
    s_peak_vis = max(s_total_peak, s_base)
    
    # SKALOWANIE WIZUALNE
    h_ref_visual = max(h, 2.0)
    target_load_height = 0.7 * h_ref_visual
    
    if s_peak_vis > 0.001:
        load_scale = target_load_height / s_peak_vis
    else:
        load_scale = 1.0

    # GEOMETRIA
    draw_b1 = min(b1, 10.0)
    draw_ls_full = ls
    draw_b2 = b2
    
    half_width = draw_b1 / 2.0
    high_roof_eave_y = h
    high_roof_ridge_x = -half_width
    
    # Dynamiczna wysokość kalenicy (zgodnie z obliczeniami)
    high_roof_ridge_y = h + half_width * math.tan(math.radians(alpha_high))
    
    low_roof_y = 0.0
    ground_y = -3.0
    max_draw_width = max(draw_ls_full, draw_b2) + 2.0
    
    fig, ax = plt.subplots(figsize=(8, 5))
    
    # 1. BUDYNKI
    ax.plot([-draw_b1-1, max_draw_width], [ground_y, ground_y], 'k-', lw=1) # Grunt
    
    # Budynek WYŻSZY
    ax.plot([0, 0], [ground_y, high_roof_eave_y], 'k-', lw=2.5) # Ściana
    ax.plot([-draw_b1, -draw_b1], [ground_y, high_roof_eave_y], 'k-', lw=2.5)
    ax.plot([-draw_b1, high_roof_ridge_x], [high_roof_eave_y, high_roof_ridge_y], 'k-', lw=2.5)
    ax.plot([high_roof_ridge_x, 0], [high_roof_ridge_y, high_roof_eave_y], 'k-', lw=2.5)
    
    # Budynek NIŻSZY
    ax.plot([0, draw_b2], [low_roof_y, low_roof_y], 'k-', lw=2.5)
    ax.plot([draw_b2, draw_b2], [low_roof_y, ground_y], 'k-', lw=2.5)
    
    # 2. OBCIĄŻENIE
    h_peak = s_peak_vis * load_scale
    h_base = s_base * load_scale
    
    # Kolor bazowy (nie szary) - Jasnozielony
    base_color = 'lightgreen'
    base_edge = 'green'
    
    def draw_arrows_in_rect(start_x, end_x, y_bottom, height, color):
        """Rysuje strzałki wewnątrz prostokątnego obszaru"""
        width = end_x - start_x
        if width <= 0: return
        n_arrows = max(2, int(width / 1.5))
        for i in range(n_arrows + 1):
            ax_x = start_x + (i / n_arrows) * width
            if abs(ax_x) < 0.1: continue
            
            ax.arrow(ax_x, y_bottom + height - 0.1, 0, -(height - 0.2), 
                     head_width=0.15, head_length=0.15, fc=color, ec=color, alpha=0.6)

    if "równomierne" in case_label:
        rect = patches.Rectangle((0, low_roof_y), draw_b2, h_base, 
                                 facecolor=base_color, edgecolor=base_edge, alpha=0.5)
        ax.add_patch(rect)
        
        # Strzałki dla równomiernego
        draw_arrows_in_rect(0, draw_b2, low_roof_y, h_base, base_edge)
        
        ax.text(draw_b2/2, low_roof_y + h_base + 0.2, f"{s_base:.2f} kN/m²", ha='center', fontweight='bold', color=base_edge)
        
    else:
        # ZASPA
        cutoff_x = min(draw_ls_full, draw_b2)
        
        if draw_ls_full > 0:
            h_at_cutoff = h_peak - (h_peak - h_base) * (cutoff_x / draw_ls_full)
            s_val_at_cutoff = s_peak_vis - (s_peak_vis - s_base) * (cutoff_x / draw_ls_full)
        else:
            h_at_cutoff = h_base
            s_val_at_cutoff = s_base
            
        # Główny wielokąt zaspy (niebieski)
        poly_real_coords = [
            [0, low_roof_y], 
            [cutoff_x, low_roof_y], 
            [cutoff_x, low_roof_y + h_at_cutoff], 
            [0, low_roof_y + h_peak]
        ]
        poly_real = patches.Polygon(poly_real_coords, facecolor='skyblue', edgecolor='blue', alpha=0.6)
        ax.add_patch(poly_real)
        
        # Reszta dachu (jeśli b2 > ls) - obciążenie bazowe
        if draw_b2 > draw_ls_full:
            poly_rest = patches.Rectangle((draw_ls_full, low_roof_y), draw_b2 - draw_ls_full, h_base,
                                          facecolor=base_color, edgecolor=base_edge, alpha=0.5)
            ax.add_patch(poly_rest)
            # Strzałki na reszcie
            draw_arrows_in_rect(draw_ls_full, draw_b2, low_roof_y, h_base, base_edge)
            
        # Fantom zaspy (jeśli ls > b2)
        if draw_ls_full > draw_b2:
            poly_phantom_coords = [
                [cutoff_x, low_roof_y],
                [draw_ls_full, low_roof_y],
                [draw_ls_full, low_roof_y + h_base],
                [cutoff_x, low_roof_y + h_at_cutoff]
            ]
            poly_phantom = patches.Polygon(poly_phantom_coords, facecolor='none', edgecolor='gray', linestyle='--', alpha=0.5)
            ax.add_patch(poly_phantom)
            
            # Linia pomocnicza odcięcia (szara) - schodzi w dół pod wykres
            ax.plot([cutoff_x, cutoff_x], [low_roof_y + h_at_cutoff, low_roof_y], color='gray', linestyle=':', linewidth=1.5)
            
            # Etykieta na krawędzi (NIEBIESKA - bo to realna wartość na dachu)
            # U GÓRY
            ax.text(cutoff_x + 0.3, low_roof_y + h_at_cutoff, f"{s_val_at_cutoff:.2f} kN/m²", 
                    ha='left', va='center', color='blue', fontweight='bold')
            
            # Linia pomocnicza do wartości teoretycznej s_base (na końcu fantomu)
            # Schodzi pod wykres
            ax.plot([draw_ls_full, draw_ls_full], [low_roof_y + h_base, low_roof_y - 0.2], color='gray', linestyle=':', linewidth=1.0)
            
        # STRZAŁKI W ZASPIE
        num_arrows = max(3, int(cutoff_x / 1.5))
        for i in range(num_arrows + 1):
            ax_x = (i / num_arrows) * cutoff_x
            if ax_x > 0.1: 
                # h śniegu w tym punkcie
                if draw_ls_full > 0:
                    h_curr = h_peak - (h_peak - h_base) * (ax_x / draw_ls_full)
                else:
                    h_curr = h_base
                
                ax.arrow(ax_x, low_roof_y + h_curr - 0.1, 0, -(h_curr - 0.2), 
                         head_width=0.15, head_length=0.15, fc='blue', ec='blue', alpha=0.5)

        # ETYKIETY GŁÓWNE
        # Peak
        ax.text(0.2, low_roof_y + h_peak + 0.2, f"{s_peak_vis:.2f} kN/m²", ha='left', va='bottom', color='blue', fontweight='bold')
        
        # Base (koniec zaspy)
        if draw_b2 > draw_ls_full:
            # Etykieta s_base w środku reszty
            ax.text(draw_ls_full + (draw_b2 - draw_ls_full)/2, low_roof_y + h_base + 0.2, f"{s_base:.2f} kN/m²", 
                    ha='center', va='bottom', color=base_edge)
        else:
            # Etykieta s_base na końcu fantomu (szara), pod wykresem, po PRAWEJ stronie linii
            # Zbliżona do spodu (-0.2), wyrównana do lewej strony linii (ha='left'), lekko przesunięta w prawo (+0.1)
            ax.text(draw_ls_full + 0.1, low_roof_y - 0.2, f"{s_base:.2f} kN/m²", 
                    ha='left', va='top', color='gray')
        
    # 3. WYMIAROWANIE
    def draw_dim_line(x1, x2, y, label):
        ax.annotate("", xy=(x1, y), xytext=(x2, y), arrowprops=dict(arrowstyle="<->", lw=0.8))
        ax.text((x1+x2)/2, y - 0.1, label, ha='center', va='top')
    
    # h
    ax.annotate("", xy=(-0.5, 0), xytext=(-0.5, h), arrowprops=dict(arrowstyle="<->", lw=0.8))
    ax.text(-0.6, h/2, f"h={h}m", ha='right', va='center', rotation=90)
    
    # b1
    draw_dim_line(-draw_b1, 0, ground_y - 0.5, f"$b_1={b1}m$")
    
    # b2
    draw_dim_line(0, draw_b2, ground_y - 0.5, f"$b_2={b2}m$")
    
    # ls
    if "zaspa" in case_label:
        dim_y = low_roof_y - 1.2
        ax.plot([0, 0], [low_roof_y, dim_y], 'k:', lw=0.5)
        ax.plot([draw_ls_full, draw_ls_full], [low_roof_y, dim_y], 'k:', lw=0.5)
        ax.annotate("", xy=(0, dim_y), xytext=(draw_ls_full, dim_y), arrowprops=dict(arrowstyle="<->", lw=0.8, color='red'))
        ax.text(draw_ls_full/2, dim_y - 0.1, f"$l_s={ls:.2f}m$", ha='center', va='top', color='red')

    ax.set_aspect('equal')
    ax.axis('off')
    top_y = max(high_roof_ridge_y, low_roof_y + h_peak + 1.0)
    ax.set_ylim(ground_y - 1.5, top_y)
    ax.set_xlim(-draw_b1 - 1, max_draw_width + 1)
    
    plt.tight_layout()
    return fig

def update_city_defaults():
    """Callback do aktualizacji strefy i wysokości po zmianie miasta."""
    miasto = st.session_state["dp_city"]
    if miasto in MIASTA_DB:
        dane = MIASTA_DB[miasto]
        st.session_state["dp_strefa"] = dane["strefa"]
        st.session_state["dp_A"] = float(dane["A"])

def run():
    if "dp_sk" not in st.session_state: st.session_state["dp_sk"] = 0.0

    # --------------------------------------------------------------------------
    # STYLE CSS
    # --------------------------------------------------------------------------
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
        .streamlit-expanderHeader { font-weight: bold; font-size: 1.1em; }
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
            with m2:
                st.image(mapa_path) 
        else:
            st.warning("Brak pliku 'mapa_stref.png'.")

    # ==================================================================================
    # 1. DANE WEJŚCIOWE
    # ==================================================================================
    st.markdown("### DANE WEJŚCIOWE")

    col1, col2, col3 = st.columns(3)

    # --- KOLUMNA 1: LOKALIZACJA ---
    with col1:
        st.write("Czy chcesz wybrać miejscowość z listy?")
        
        city_mode = st.radio(
            "city_mode_label",
            ["Nie", "Tak"],
            index=0,
            label_visibility="collapsed",
            key="dp_city_mode",
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
                key="dp_city",
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

        strefa = st.selectbox("Strefa obciążenia śniegiem", options=["1", "2", "3", "4", "5"], index=sel_strefa_index, disabled=disable_strefa, key="dp_strefa")
        if disable_strefa:
            st.caption(f"🔒 Strefa dla: {wybrane_miasto}")

        A = st.number_input("Wysokość nad poziomem morza $A$ [m]", value=default_A, step=10.0, format="%.1f", key="dp_A")
        if use_city:
            st.caption("⚠️ Podano średnią wysokość dla miejscowości.")

    # --- KOLUMNA 2: TEREN I TERMIKA ---
    with col2:
        teren_dict = {"Normalny": 1.0, "Wystawiony na wiatr": 0.8, "Osłonięty": 1.2}
        typ_terenu = st.selectbox("Typ terenu", options=list(teren_dict.keys()), index=0, key="dp_teren")
        current_Ce = teren_dict[typ_terenu]
        
        with st.expander("ℹ️ Tablica 5.1 – Współczynnik Cₑ"):
            st.markdown(
                """
                | Typ terenu | $C_e$ | Opis |
                | :--- | :---: | :--- |
                | **Wystawiony** | 0,8 | Teren płaski, bez przeszkód, wystawiony na działanie wiatru z każdej strony, bez osłon lub z niewielkimi osłonami utworzonymi przez teren, inne budowle lub drzewa. |
                | **Normalny** | 1,0 | Teren, na którym nie występuje znaczne przenoszenie śniegu przez wiatr na budowle z powodu ukształtowania terenu, innych budowli lub drzew. |
                | **Osłonięty** | 1,2 | Teren, w którym rozpatrywana budowla jest znacznie niższa niż otaczający teren albo jest otoczona wysokimi drzewami lub/i wyższymi budowlami. |
                """
            )
        st.text_input("Współczynnik ekspozycji $C_e$", value=str(current_Ce), disabled=True, key="dp_Ce_disp")

        st.markdown(r"Czy dach ma przenikalność ciepła $U > 1 \, \frac{W}{m^2 \cdot K}$?", unsafe_allow_html=False)
        ct_mode = st.radio("ct_mode_dp", ["Nie", "Tak"], index=0, label_visibility="collapsed", key="dp_ct_mode", horizontal=True)
        
        Ct_val = 1.0
        if ct_mode == "Tak":
            c_u, c_ti = st.columns(2)
            with c_u: U_input = st.number_input("Współczynnik $U$", value=2.0, step=0.1, min_value=1.0, key="dp_U")
            with c_ti: Ti_input = st.number_input("Temp. wew. $T_i$", value=18.0, step=1.0, key="dp_Ti")
            Ct_val = calculate_ct_iso(U_input, Ti_input)
            st.text_input("Współczynnik termiczny $C_t$", value=str(Ct_val), disabled=True, key="dp_ct_disp_yes")
        else:
            st.text_input("Współczynnik termiczny $C_t$", value="1.0", disabled=True, key="dp_ct_disp_no")

    # --- KOLUMNA 3: S1 i GEOMETRIA ---
    with col3:
        # S1 na szczycie
        s_high = st.number_input("Obciążenie śniegiem dachu wyższego $s_1$ [kN/m²]", value=1.60, step=0.01, min_value=0.0, key="dp_s_high", help="Maksymalne obciążenie śniegiem na połaci dachu wyższego, z której śnieg może się zsunąć.")
        
        # Info pod S1
        st.info("ℹ️ Wartość obciążenia na dachu wyższym ($s_1$) należy wyznaczyć w innym module (np. Dach dwupołaciowy) i wprowadzić poniżej ręcznie.")

        # Geometria poniżej (bez linii podziału)
        # Wiersz 1: b1, b2
        c_g1, c_g2 = st.columns(2)
        with c_g1:
            b1 = st.number_input("$b_1$ [m]", value=10.0, step=0.5, min_value=0.1, key="dp_b1", help="Szerokość budynku wyższego")
        with c_g2:
            b2 = st.number_input("$b_2$ [m]", value=8.0, step=0.5, min_value=0.1, key="dp_b2", help="Szerokość dachu niższego (przylegającego)")
            
        # Wiersz 2: alpha1, h
        c_g3, c_g4 = st.columns(2)
        with c_g3:
            alpha_high = st.number_input("Kąt $\\alpha_1$ [°]", value=35.0, step=1.0, min_value=0.0, max_value=85.0, key="dp_alpha_high", help="Kąt dachu wyższego (wpływa na ześlizg)")
        with c_g4:
            h = st.number_input("Różnica wysokości $h$ [m]", value=3.0, step=0.1, min_value=0.1, key="dp_h")
        
        # Rysunek pomocniczy geometrii na spodzie
        st.pyplot(plot_geometry_schema(alpha_high), use_container_width=True)


    # ==================================================================================
    # 2. PRZYCISK OBLICZEŃ (WYNIKI)
    # ==================================================================================
    b1_col, b2_col, b3_col = st.columns([1, 2, 1])
    with b2_col:
        oblicz = st.button("OBLICZ", type="primary", use_container_width=True, key="dp_btn")

    if oblicz:
        # --- 1. Sk ---
        sk_calc = 0.0
        if strefa == "1": sk_calc = max(0.007*A - 1.4, 0.7) if A<=300 else 0.007*A - 1.4
        elif strefa == "2": sk_calc = 0.9 if A<=300 else 0.007*A - 1.4
        elif strefa == "3": sk_calc = max(0.006*A - 0.6, 1.2) if A<=300 else 0.006*A - 0.6
        elif strefa == "4": sk_calc = 1.6 if A<=300 else 0.006*A - 0.6
        elif strefa == "5": sk_calc = max(0.93*math.exp(0.00134*A), 2.0)
        sk = round(sk_calc, 3)
        st.session_state["dp_sk"] = sk

        # --- 2. OBLICZENIA ---
        mu_1_low = 0.8
        s_case1 = mu_1_low * current_Ce * Ct_val * sk
        
        val_slide = 0.0
        if alpha_high > 15:
            val_slide = 0.5 * s_high
        
        mu_s = 0.0
        s_ref_low = sk * current_Ce * Ct_val
        if s_ref_low > 0.0001:
            mu_s = val_slide / s_ref_low
            
        gamma = 2.0
        if sk > 0.0001:
            limit_mu_w = (gamma * h) / sk
        else:
            limit_mu_w = 999.0 
            
        calc_mu_w = (b1 + b2) / (2.0 * h)
        mu_w = min(calc_mu_w, limit_mu_w)
        if mu_w < 0.8: mu_w = 0.8
        if mu_w > 4.0: mu_w = 4.0
        
        s_w = mu_w * current_Ce * Ct_val * sk
        mu_2 = mu_s + mu_w
        
        ls = 2 * h
        if ls < 5.0: ls = 5.0
        if ls > 15.0: ls = 15.0
        
        s_case2_peak = val_slide + s_w

        # ==============================================================================
        # 3. WYNIKI
        # ==============================================================================
        st.markdown("### WYNIKI")
        
        c_res1, c_res2 = st.columns(2)
        
        with c_res1:
            st.markdown("**Przypadek (i) - Obciążenie równomierne**")
            fig1 = plot_abutting_roof(b1, b2, h, alpha_high, 0, 0, s_case1, ls, "równomierne")
            st.pyplot(fig1, use_container_width=True)
            
        with c_res2:
            st.markdown("**Przypadek (ii) - Obciążenie z zaspą**")
            fig2 = plot_abutting_roof(b1, b2, h, alpha_high, val_slide, s_w, s_case1, ls, "zaspa")
            st.pyplot(fig2, use_container_width=True)
            
        # SZCZEGÓŁY
        with st.expander("🔍 Szczegóły obliczeń"):
            
            st.markdown("#### 1. Podstawowe dane i współczynniki")
            st.write(f"Wartość charakterystyczna obciążenia śniegiem: $s_k = {sk:.2f}$ kN/m²")
            st.write(f"Współczynnik ekspozycji: $C_e = {current_Ce}$")
            st.write(f"Współczynnik termiczny: $C_t = {Ct_val}$")
            st.write(f"Obciążenie dachu wyższego: $s_1 = {s_high:.2f}$ kN/m²")
            st.write("Przyjęto dach niższy płaski ($\\alpha_2 = 0^\\circ \\rightarrow \\mu_1 = 0,8$).")
            
            st.markdown("**Współczynniki kształtu:**")
            st.latex(r"\mu_1 = 0,80 \quad (\text{dla } \alpha_2 = 0^\circ)")
            
            if alpha_high > 15:
                st.latex(r"\mu_s = \frac{0,5 \cdot s_1}{s_k \cdot C_e \cdot C_t} = \frac{0,5 \cdot %.2f \, \text{kN/m}^2}{%.2f \, \text{kN/m}^2 \cdot %.1f \cdot %.1f} = \mathbf{%.2f}" 
                         % (s_high, sk, current_Ce, Ct_val, mu_s))
            else:
                st.latex(r"\mu_s = 0 \quad (\text{bo } \alpha_1 \le 15^\circ)")
                
            st.latex(r"\mu_w = \frac{b_1 + b_2}{2h} = \frac{%.2f \, \text{m} + %.2f \, \text{m}}{2 \cdot %.2f \, \text{m}} = \mathbf{%.2f}" 
                     % (b1, b2, h, mu_w))
            
            st.latex(r"\mu_2 = \mu_s + \mu_w = %.2f + %.2f = \mathbf{%.2f}" 
                     % (mu_s, mu_w, mu_2))

            st.markdown("#### 2. Obliczenia szczegółowe")
            
            # WYKRES RÓWNOMIERNY
            st.markdown("**Przypadek (i) - Obciążenie równomierne**")
            c_det1, c_det2, c_det3 = st.columns([1, 2, 1])
            with c_det2:
                st.pyplot(fig1, use_container_width=True)
                
            st.markdown("Obciążenie równomierne (na płaskiej części):")
            st.latex(r"s_{base} = \mu_1 \cdot C_e \cdot C_t \cdot s_k = 0,80 \cdot %.1f \cdot %.1f \cdot %.2f \, \text{kN/m}^2 = \mathbf{%.2f} \, \text{kN/m}^2" 
                     % (current_Ce, Ct_val, sk, s_case1))

            # WYKRES ZASPA
            st.markdown("**Przypadek (ii) - Obciążenie z zaspą**")
            c_det1, c_det2, c_det3 = st.columns([1, 2, 1])
            with c_det2:
                st.pyplot(fig2, use_container_width=True)
            
            st.markdown("Składowe obciążenia przy uskoku:")
            
            if alpha_high > 15:
                st.latex(r"s_s = 0,5 \cdot s_1 = 0,5 \cdot %.2f \, \text{kN/m}^2 = \mathbf{%.2f} \, \text{kN/m}^2" % (s_high, val_slide))
            else:
                st.latex(r"s_s = 0 \quad (\text{bo } \alpha_1 \le 15^\circ)")

            st.markdown("Składowa od wiatru (wyznaczona przez $\\mu_w$):")
            st.latex(r"s_w = \mu_w \cdot C_e \cdot C_t \cdot s_k = %.2f \cdot %.1f \cdot %.1f \cdot %.2f \, \text{kN/m}^2 = %.2f \, \text{kN/m}^2" 
                     % (mu_w, current_Ce, Ct_val, sk, s_w))
            
            st.latex(r"l_s = 2 \cdot h = 2 \cdot %.2f \, \text{m} = \mathbf{%.2f} \, \text{m}" % (h, ls))
            
            if ls > b2:
                st.markdown("Obciążenie na krawędzi dachu (w punkcie odcięcia zaspy $x=b_2$):")
                s_edge_val = s_case2_peak - (s_case2_peak - s_case1) * (b2 / ls)
                st.latex(r"s_{edge} = s_{max} - (s_{max} - s_{base}) \cdot \frac{b_2}{l_s} = %.2f - (%.2f - %.2f) \cdot \frac{%.2f}{%.2f} = \mathbf{%.2f} \, \text{kN/m}^2" 
                         % (s_case2_peak, s_case2_peak, s_case1, b2, ls, s_edge_val))

            st.markdown("Maksymalne obciążenie przy ścianie (szczyt zaspy):")
            st.latex(r"s_{max} = s_s + s_w = %.2f \, \text{kN/m}^2 + %.2f \, \text{kN/m}^2 = \mathbf{%.2f} \, \text{kN/m}^2" 
                     % (val_slide, s_w, s_case2_peak))

if __name__ == "__main__":
    run()