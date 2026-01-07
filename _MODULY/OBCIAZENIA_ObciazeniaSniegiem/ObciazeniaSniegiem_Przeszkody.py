import streamlit as st
import math
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# --------------------------------------------------------------------------------------
# 1. BAZA DANYCH MIAST (STREFY I WYSOKOŚCI)
# --------------------------------------------------------------------------------------
# Zweryfikowano wg PN-EN 1991-1-3:2005/NA:2010
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

def calculate_drift_params(h_obstacle, sk, gamma=2.0):
    """
    Oblicza parametry zaspy przy przeszkodzie wg PN-EN 1991-1-3 p. 6.2.
    """
    # Wzór 6.1: mu1 = 0.8
    mu1 = 0.8
    if sk <= 0.001:
        return mu1, mu1, 5.0
    
    # Wzór 6.2: mu2 = gamma * h / sk
    mu2_calc = (gamma * h_obstacle) / sk
    # Ograniczenia: 0.8 <= mu2 <= 2.0
    mu2 = max(0.8, min(mu2_calc, 2.0))
    
    # Wzór 6.3: ls = 2 * h
    ls_calc = 2.0 * h_obstacle
    # Ograniczenia: 5 <= ls <= 15
    ls = max(5.0, min(ls_calc, 15.0))
    
    return mu1, mu2, ls

def update_city_defaults():
    """Callback do aktualizacji strefy i wysokości po zmianie miasta."""
    miasto = st.session_state["zwp_city"]
    if miasto in MIASTA_DB:
        dane = MIASTA_DB[miasto]
        st.session_state["zwp_strefa"] = dane["strefa"]
        st.session_state["zwp_A"] = float(dane["A"])

def plot_schematic_fig62():
    """
    Rysuje schemat poglądowy przeszkody na dachu (styl techniczny).
    Dach płaski + pionowa przegroda (szary blok) + wymiar h.
    """
    fig, ax = plt.subplots(figsize=(5, 2.5))
    
    # Geometria
    ax.plot([-3, 3], [0, 0], color='black', linewidth=1.5) # Dach
    # Kreskowanie pod dachem
    rect_roof = patches.Rectangle((-3, -0.4), 6, 0.4, facecolor='white', edgecolor='gray', hatch='///', linewidth=0)
    ax.add_patch(rect_roof)
    
    # Przeszkoda (Prostokąt) - pełny szary blok
    h_demo = 1.5
    wall_w = 0.3
    rect_wall = patches.Rectangle(
        (-wall_w/2, 0), wall_w, h_demo,
        facecolor='#e0e0e0', edgecolor='black', linewidth=1.5, zorder=10
    )
    ax.add_patch(rect_wall)
    
    # Wymiar h
    ax.annotate(
        '', xy=(-0.5, 0), xytext=(-0.5, h_demo),
        arrowprops=dict(arrowstyle='<->', lw=1.0)
    )
    ax.text(-0.6, h_demo/2, 'h', va='center', ha='right', fontsize=12, fontstyle='italic')
    
    # Linia pomocnicza
    ax.plot([-0.5, 0], [h_demo, h_demo], color='gray', linestyle='--', linewidth=0.5)

    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_ylim(-0.5, h_demo + 0.5)
    plt.tight_layout()
    return fig

def plot_obstacle_case(h_obstacle, ls, s_base, s_max):
    """
    Generuje wykres Matplotlib dla zaspy przy przeszkodzie w stylu technicznym.
    """
    # Ustalenie zakresu rysowania
    margin_left = 2.0
    # Ustawiamy szerokość "bazy" tak, by była wystarczająca na opis, ale nie za duża.
    margin_right = ls + 3.5 
    W_plot = margin_right
    
    fig, ax = plt.subplots(figsize=(8, 5)) 
    
    # Poziomy
    ground_y = -0.5
    roof_y = 0.0
    
    # Poziom linii wymiarowej ls (nieco nad przeszkodą, ale nie za wysoko)
    dim_ls_y = h_obstacle + 0.4
    
    # Poziom odniesienia dla obciążenia
    load_base_y = dim_ls_y + 1.2
    
    # --- 1. BUDYNEK ---
    
    # Linia dachu
    ax.plot([-margin_left, margin_right], [roof_y, roof_y], color='black', linewidth=2.5, zorder=5)
    
    # Kreskowanie pod dachem
    rect_roof = patches.Rectangle(
        (-margin_left, ground_y), margin_left + margin_right, roof_y - ground_y,
        facecolor='white', edgecolor='gray', hatch='///', linewidth=0, zorder=0
    )
    ax.add_patch(rect_roof)
    
    # Przeszkoda (Prostokąt) - pełny szary blok
    wall_thick = 0.4
    rect_obs = patches.Rectangle(
        (-wall_thick, roof_y), wall_thick, h_obstacle,
        facecolor='#e0e0e0', edgecolor='black', linewidth=1.5, zorder=10
    )
    ax.add_patch(rect_obs)
    
    # --- 2. WYMIARY ---
    
    # Wymiar h (z lewej)
    dim_x = -wall_thick - 0.4
    ax.annotate(
        '', xy=(dim_x, 0), xytext=(dim_x, h_obstacle),
        arrowprops=dict(arrowstyle='<->', lw=1.0)
    )
    ax.text(dim_x - 0.1, h_obstacle / 2, f"$h={h_obstacle:.2f}$m", 
            rotation=90, va='center', ha='right', fontsize=10)
    # Linia pomocnicza do h
    ax.plot([dim_x, -wall_thick], [h_obstacle, h_obstacle], color='gray', linestyle='--', linewidth=0.5)

    # --- 3. OBCIĄŻENIE (Blok nad budynkiem) ---
    scale_factor = 2.5 # Skala wizualna
    color_load = '#1f77b4'
    
    val_max_draw = s_max * scale_factor
    val_base_draw = s_base * scale_factor
    
    if val_max_draw < 0.1: val_max_draw = 0.1
    if val_base_draw < 0.1: val_base_draw = 0.1

    # Wielokąt obciążenia
    poly_x = [0, 0, ls, W_plot, W_plot, 0]
    poly_y = [
        load_base_y,
        load_base_y + val_max_draw,
        load_base_y + val_base_draw,
        load_base_y + val_base_draw,
        load_base_y,
        load_base_y
    ]
    
    # Tło
    drift_poly = patches.Polygon(
        list(zip(poly_x, poly_y)), 
        closed=True, 
        facecolor=color_load, edgecolor=color_load, 
        alpha=0.15, linewidth=1.2, zorder=10
    )
    ax.add_patch(drift_poly)
    
    # Grube linie konturowe
    ax.plot([0, ls], [load_base_y + val_max_draw, load_base_y + val_base_draw], color=color_load, linewidth=2.0, zorder=11)
    ax.plot([ls, W_plot], [load_base_y + val_base_draw, load_base_y + val_base_draw], color=color_load, linewidth=2.0, zorder=11)
    ax.plot([0, W_plot], [load_base_y, load_base_y], color='gray', linewidth=0.8, zorder=10)
    ax.plot([0, 0], [load_base_y, load_base_y + val_max_draw], color=color_load, linewidth=1.0, zorder=11)

    # Strzałki (zagęszczone)
    # 1. Strzałka MAX
    ax.arrow(0.1, load_base_y + val_max_draw, 0, -val_max_draw + 0.05, 
             head_width=0.15, head_length=0.15, fc=color_load, ec=color_load, length_includes_head=True, zorder=12)
    ax.text(0.2, load_base_y + val_max_draw + 0.2, f"{s_max:.2f} kN/m²", 
            ha='left', va='bottom', fontweight='bold', fontsize=10)
            
    # 2. Strzałki w strefie zaspy
    n_arrows_drift = max(3, int(ls * 1.5))
    x_drift = np.linspace(0.1, ls, n_arrows_drift + 2)[1:-1]
    for x in x_drift:
        ratio = x / ls
        y_curr = val_max_draw - (val_max_draw - val_base_draw) * ratio
        ax.arrow(x, load_base_y + y_curr, 0, -y_curr + 0.05, 
                 head_width=0.12, head_length=0.12, fc=color_load, ec=color_load, length_includes_head=True, zorder=12, alpha=0.7)

    # 3. Strzałki w strefie bazowej
    n_arrows_base = max(3, int((W_plot - ls) * 1.5))
    if W_plot > ls:
        x_base = np.linspace(ls, W_plot, n_arrows_base + 2)[1:-1]
        for x in x_base:
            ax.arrow(x, load_base_y + val_base_draw, 0, -val_base_draw + 0.05, 
                     head_width=0.12, head_length=0.12, fc=color_load, ec=color_load, length_includes_head=True, zorder=12, alpha=0.7)
            
    # Tekst przy wartości bazowej - NA ŚRODKU pola obciążenia stałego
    center_base_x = ls + (W_plot - ls) / 2
    ax.text(center_base_x, load_base_y + val_base_draw + 0.2, f"{s_base:.2f} kN/m²", 
            ha='center', va='bottom', fontweight='bold', fontsize=10)

    # Wymiar ls (linia wymiarowa)
    ax.plot([0, 0], [load_base_y, dim_ls_y], color='gray', lw=0.5, linestyle=':')
    ax.plot([ls, ls], [load_base_y, dim_ls_y], color='gray', lw=0.5, linestyle=':')
    ax.annotate(
        '', xy=(0, dim_ls_y), xytext=(ls, dim_ls_y),
        arrowprops=dict(arrowstyle='<->', lw=1.0)
    )
    ax.text(ls / 2, dim_ls_y + 0.1, f"$l_s={ls:.2f}$m", ha='center', va='bottom', fontsize=10)

    # Ustawienia osi
    ax.set_aspect('equal')
    ax.axis('off')
    
    # Limity
    top_limit = load_base_y + val_max_draw + 1.0
    ax.set_ylim(-1.0, top_limit)
    ax.set_xlim(-margin_left - 0.5, W_plot + 0.5)
    
    plt.tight_layout()
    return fig

def run():
    if "zwp_sk" not in st.session_state: st.session_state["zwp_sk"] = 0.0

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

    col1, col2, col3 = st.columns(3)

    # --- KOLUMNA 1: LOKALIZACJA ---
    with col1:
        st.write("Czy chcesz wybrać miejscowość z listy?")
        
        city_mode = st.radio(
            "city_mode_label",
            ["Nie", "Tak"],
            index=0,
            label_visibility="collapsed",
            key="zwp_city_mode",
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
                key="zwp_city",
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

        strefa = st.selectbox("Strefa obciążenia śniegiem", options=["1", "2", "3", "4", "5"], index=sel_strefa_index, disabled=disable_strefa, help="Numer strefy zgodnie z Załącznikiem Krajowym NA do PN-EN 1991-1-3.", key="zwp_strefa")
        if disable_strefa:
            st.caption(f"🔒 Strefa dla: {wybrane_miasto}")

        A = st.number_input("Wysokość nad poziomem morza $A$ [m]", value=default_A, step=10.0, format="%.1f", key="zwp_A")
        if use_city:
            st.caption("⚠️ Podano średnią wysokość dla miejscowości.")

    # --- KOLUMNA 2: TEREN I TERMIKA ---
    with col2:
        teren_dict = {
            "Normalny": 1.0,
            "Wystawiony na wiatr": 0.8,
            "Osłonięty": 1.2
        }
        typ_terenu = st.selectbox("Typ terenu", options=list(teren_dict.keys()), index=0, help="Decyduje o współczynniku ekspozycji Ce.", key="zwp_teren")
        
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
        st.text_input("Współczynnik ekspozycji $C_e$", value=str(current_Ce), disabled=True, key="zwp_Ce_disp")

        st.markdown(r"Czy dach ma przenikalność ciepła $U > 1 \, \frac{W}{m^2 \cdot K}$?", unsafe_allow_html=False)
        ct_mode = st.radio("ct_mode_label", ["Nie", "Tak"], index=0, label_visibility="collapsed", key="zwp_ct_mode", horizontal=True)
        Ct_val = 1.0
        if ct_mode == "Tak":
            c_u, c_ti = st.columns(2)
            with c_u: U_input = st.number_input("Wsp. $U$ [W/m²K]", value=2.0, step=0.1, min_value=1.0, key="zwp_U")
            with c_ti: Ti_input = st.number_input("Temp. wew. $T_i$ [°C]", value=18.0, step=1.0, key="zwp_Ti")
            Ct_val = calculate_ct_iso(U_input, Ti_input)
            st.text_input("Współczynnik termiczny $C_t$", value=str(Ct_val), disabled=True, key="zwp_ct_disp_yes")
        else:
            Ct_val = 1.0
            st.text_input("Współczynnik termiczny $C_t$", value="1.0", disabled=True, key="zwp_ct_disp_no")

    # --- KOLUMNA 3: PRZESZKODA ---
    with col3:
        h_obstacle = st.number_input("Wysokość przeszkody $h$ [m]", value=1.5, step=0.1, min_value=0.0, format="%.2f", key="zwp_h")
        fig_sch = plot_schematic_fig62()
        st.pyplot(fig_sch, use_container_width=True)

        gamma_snow = st.number_input("Ciężar objętościowy śniegu $\\gamma$ [kN/m³]", value=2.0, step=0.1, min_value=1.0, format="%.1f", help="Zalecana wartość wg PN-EN 1991-1-3 to 2.0 kN/m³.", key="zwp_gamma")
        
        with st.expander("ℹ️ Współczynnik kształtu dachu μ₁ oraz μ₂"):
            st.markdown(
                r"""
                | Współczynnik | Wartość / Wzór |
                | :--- | :--- |
                | $\mu_1$ | $0,8$ |
                | $\mu_2$ | $\begin{matrix} \gamma \cdot h / s_k \\ (0,8 \le \mu_2 \le 2,0) \end{matrix}$ |
                """
            )

    
    b1, b2, b3 = st.columns([1, 2, 1])
    oblicz_clicked = False
    with b2:
        if st.button("OBLICZ", type="primary", use_container_width=True, key="zwp_btn"):
            oblicz_clicked = True

    if oblicz_clicked:
        # Obliczenia
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

        mu1, mu2, ls = calculate_drift_params(h_obstacle, sk, gamma_snow)
        s_base = mu1 * Ce * Ct * sk
        s_max = mu2 * Ce * Ct * sk

        st.session_state["zwp_sk"] = sk

        st.markdown("### WYNIKI")
        st.markdown("**Obciążenie zaspą przy występie/przeszkodzie**")

        # Główny wykres wycentrowany (50% szerokości)
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            fig = plot_obstacle_case(h_obstacle, ls, s_base, s_max)
            st.pyplot(fig, use_container_width=True)

        with st.expander("Szczegóły obliczeń"):
            # 1. DANE I PARAMETRY
            st.markdown("#### 1. Dane i parametry")
            
            strefa_desc = ""
            if strefa == "1": strefa_desc = "≥ 0,70 lub 0,007A - 1,4"
            elif strefa == "2": strefa_desc = "0,9 kN/m²"
            elif strefa == "3": strefa_desc = "≥ 1,2 lub 0,006A - 0,6"
            elif strefa == "4": strefa_desc = "1,6 kN/m²"
            elif strefa == "5": strefa_desc = "≥ 2,0 lub 0,93exp(0,00134A)"
            
            st.write(f"Strefa śniegowa: **{strefa}** ({strefa_desc})")
            st.write(f"Wysokość nad poziomem morza: $A = {A:.2f} \\text{{ m n.p.m.}}$")
            st.write(f"Współczynnik ekspozycji: $C_e = {Ce}$")
            st.write(f"Współczynnik termiczny: $C_t = {Ct}$")
            st.write(f"Obciążenie śniegiem gruntu: **$s_k = {sk:.2f} \\text{{ kN/m}}^2$**")
            st.write(f"Ciężar objętościowy śniegu: $\\gamma = {gamma_snow:.1f} \\text{{ kN/m}}^3$")
            st.write(f"Wysokość przeszkody: $h = {h_obstacle:.2f} \\text{{ m}}$")
            
            st.markdown(r"**Współczynniki kształtu i długość zaspy:**")
            st.latex(r"\mu_1 = 0,8")
            
            mu2_raw = (gamma_snow * h_obstacle) / sk if sk > 0 else 0
            st.latex(r"\mu_2 = \frac{\gamma \cdot h}{s_k} = \frac{" + "{:.1f} \\cdot {:.2f}".format(gamma_snow, h_obstacle) + r"}{" + "{:.2f}".format(sk) + r"} = " + "{:.3f}".format(mu2_raw))
            st.latex(r"\text{{Przyjęto: }} \mu_2 = \mathbf{{{:.3f}}} \quad (0,8 \le \mu_2 \le 2,0)".format(mu2))

            st.latex(r"l_s = 2 \cdot h = 2 \cdot {:.2f} = {:.2f} \, \text{{m}}".format(h_obstacle, 2*h_obstacle))
            st.latex(r"\text{{Przyjęto: }} l_s = \mathbf{{{:.2f}}} \, \text{{m}} \quad (5 \, \text{{m}} \le l_s \le 15 \, \text{{m}})".format(ls))

            # 2. WYNIKI SZCZEGÓŁOWE
            st.markdown("#### 2. Wyniki szczegółowe")
            
            # Wykres wycentrowany (50% szerokości)
            c1_d, c2_d, c3_d = st.columns([1, 2, 1])
            with c2_d:
                st.pyplot(fig, use_container_width=True)
            
            st.markdown("Obciążenie podstawowe (poza zaspą):")
            # Poprawiona metoda formatowania - bezpieczna i sprawdzona
            st.latex(
                r"s_{{base}} = \mu_1 \cdot C_e \cdot C_t \cdot s_k = "
                r"0,8 \cdot {} \cdot {} \cdot {:.2f} \, \text{{kN/m}}^2 = \mathbf{{{:.2f}}} \, \text{{kN/m}}^2"
                .format(Ce, Ct, sk, s_base)
            )
            
            st.markdown("Maksymalne obciążenie (przy przeszkodzie):")
            st.latex(
                r"s_{{max}} = \mu_2 \cdot C_e \cdot C_t \cdot s_k = "
                r"{:.3f} \cdot {} \cdot {} \cdot {:.2f} \, \text{{kN/m}}^2 = \mathbf{{{:.2f}}} \, \text{{kN/m}}^2"
                .format(mu2, Ce, Ct, sk, s_max)
            )

if __name__ == "__main__":
    run()