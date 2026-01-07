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

def calculate_mu1(alpha):
    """Oblicza współczynnik kształtu dachu mu1 wg PN-EN 1991-1-3 Tablica 5.2."""
    if alpha < 0: return 0.8
    if 0 <= alpha <= 30:
        return 0.8
    elif 30 < alpha < 60:
        return 0.8 * (60.0 - alpha) / 30.0
    else: # alpha >= 60
        return 0.0

def plot_mu_coefficients():
    """Generuje wykres mu1 w funkcji kąta alfa (0-60 stopni)."""
    alphas = np.linspace(0, 60, 100)
    mu1_vals = [calculate_mu1(a) for a in alphas]

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(alphas, mu1_vals, label=r'$\mu_1$', color='blue', linewidth=2)
     
    ax.set_xlabel(r'Kąt nachylenia połaci $\alpha$ [°]')
    ax.set_ylabel(r'Współczynnik kształtu dachu $\mu$')
    ax.set_title('Współczynnik kształtu dachu')
    
    ax.set_yticks(np.arange(0, 1.9, 0.2))
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.legend()
    ax.set_xlim(0, 60)
    ax.set_ylim(0, 1.0)
    plt.tight_layout()
    
    return fig

def plot_roof_mono(alpha, s_val):
    """
    Generuje techniczny wykres Matplotlib dla dachu jednopołaciowego.
    """
    W = 10.0  
    draw_alpha = max(min(alpha, 80), 2)
    a_rad = math.radians(draw_alpha)
    h = W * math.tan(a_rad)
    wall_depth = 2.5
    ground_y = -wall_depth
    
    fig, ax = plt.subplots(figsize=(6, 7.5))
    
    # Grunt
    ground_rect = patches.Rectangle((-2, ground_y - 1.0), width=W + 4, height=1.0, facecolor='white', edgecolor='gray', hatch='///', linewidth=0, zorder=0)
    ax.add_patch(ground_rect)
    ax.plot([-2, W + 2], [ground_y, ground_y], color='black', linewidth=1.5)

    # Budynek
    ax.plot([0, 0], [ground_y, 0], color='black', linewidth=2.5)
    ax.plot([W, W], [ground_y, h], color='black', linewidth=2.5)
    ax.plot([0, W], [0, h], color='black', linewidth=2.5, zorder=10)
    
    # Oznaczenie kąta
    marker_len = 3.0 if W > 3 else W
    ax.plot([0, marker_len], [0, 0], color='black', linestyle='--', linewidth=1.0)
    arc_size = marker_len * 0.8
    if h > W and marker_len > W/2: arc_size = W * 0.3
    arc = patches.Arc((0, 0), arc_size, arc_size, theta1=0, theta2=draw_alpha, color='black', linewidth=0.8)
    ax.add_patch(arc)
    ax.text(marker_len * 0.6, -0.3, f"$\\alpha={alpha:.0f}^\\circ$", fontsize=11, color='black', ha='left', va='top')

    # Obciążenie
    load_base_y = h + 0.5 
    scale_factor = 2.5
    h_load = s_val * scale_factor
    color = '#1f77b4' 
    
    if s_val > 0.01:
        rect = patches.Rectangle((0, load_base_y), width=W, height=h_load, linewidth=1.2, edgecolor=color, facecolor=color, alpha=0.15)
        ax.add_patch(rect)
        ax.plot([0, W], [load_base_y + h_load, load_base_y + h_load], color=color, linewidth=2)
        ax.plot([0, W], [load_base_y, load_base_y], color='gray', linewidth=0.5)
        ax.plot([0, 0], [load_base_y, load_base_y + h_load], color=color, linewidth=1)
        ax.plot([W, W], [load_base_y, load_base_y + h_load], color=color, linewidth=1)

        n_arrows = 9
        arrow_steps = np.linspace(0, W, n_arrows + 2)[1:-1]
        for ax_x in arrow_steps:
            ax.arrow(ax_x, load_base_y + h_load, 0, -h_load + 0.05, head_width=0.15, head_length=0.15, fc=color, ec=color, length_includes_head=True)
        
        mid_x = W / 2.0
        ax.text(mid_x, load_base_y + h_load + 0.2, f"{s_val:.2f} kN/m²", ha='center', va='bottom', fontsize=12, fontweight='bold')

    ax.set_aspect('equal')
    ax.axis('off')
    top_limit = load_base_y + h_load + 1.5
    ax.set_ylim(ground_y - 0.5, top_limit)
    ax.set_xlim(-2.5, W + 2.5)
    plt.tight_layout()
    return fig

def update_city_defaults():
    """Callback do aktualizacji strefy i wysokości po zmianie miasta."""
    miasto = st.session_state["dj_city"]
    if miasto in MIASTA_DB:
        dane = MIASTA_DB[miasto]
        st.session_state["dj_strefa"] = dane["strefa"]
        st.session_state["dj_A"] = float(dane["A"])

def run():
    if "dj_sk" not in st.session_state: st.session_state["dj_sk"] = 0.0
    
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

    # KOLUMNA 1: Strefa i Teren
    with col1:
        st.write("Czy chcesz wybrać miejscowość z listy?")
        city_mode = st.radio(
            "city_mode_label",
            ["Nie", "Tak"],
            index=0,
            label_visibility="collapsed",
            key="dj_city_mode",
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
                key="dj_city",
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
            key="dj_strefa"
        )
        if disable_strefa:
            st.caption(f"🔒 Strefa przypisana dla: {wybrane_miasto}")

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
            key="dj_teren"
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
        st.text_input("Współczynnik ekspozycji $C_e$", value=str(current_Ce), disabled=True, key="dj_Ce_disp")

    # KOLUMNA 2: Wysokość i Ct
    with col2:
        A = st.number_input(
            "Wysokość nad poziomem morza $A$ [m]",
            value=default_A,
            step=10.0,
            format="%.1f",
            key="dj_A"
        )
        if use_city:
            st.caption("⚠️ Podano średnią wysokość dla miejscowości.")

        st.markdown(r"Czy dach ma przenikalność ciepła $U > 1 \, \small \frac{W}{m^2 \cdot K}$?")
        ct_mode = st.radio("ct_mode_label", ["Nie", "Tak"], index=0, label_visibility="collapsed", key="dj_ct_mode", horizontal=True)
        Ct_val = 1.0

        if ct_mode == "Tak":
            c_u, c_ti = st.columns(2)
            with c_u:
                U_input = st.number_input("Wsp. $U$", value=2.0, step=0.1, min_value=1.0, key="dj_U")
            with c_ti:
                Ti_input = st.number_input("Temp. $T_i$", value=18.0, step=1.0, key="dj_Ti")
            Ct_val = calculate_ct_iso(U_input, Ti_input)
            st.text_input("Współczynnik termiczny $C_t$", value=str(Ct_val), disabled=True, key="dj_ct_disp_yes")
        else:
            Ct_val = 1.0
            st.text_input("Współczynnik termiczny $C_t$", value="1.0", disabled=True, key="dj_ct_disp_no")

    # KOLUMNA 3: Geometria i Tabela
    with col3:
        st.markdown("**Czy na dachu znajdują się bariery przeciwśnieżne?**")
        snow_guards = st.radio(
            "snow_guards_label",
            ["Nie", "Tak"],
            index=0,
            label_visibility="collapsed",
            key="dj_snow_guards",
            horizontal=True
        )
        
        alpha = st.number_input(
            "Kąt nachylenia połaci $\\alpha$ [°]",
            value=10.0, step=1.0, format="%.1f",
            min_value=0.0, max_value=90.0,
            key="dj_alpha"
        )
        
        with st.expander("ℹ️ Tablica 5.2 – Współczynnik kształtu dachu μ₁"):
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

                    | Kąt nachylenia $\\alpha$ | Współczynnik $\\mu_1$ |
                    | :--- | :--- |
                    | $0^\\circ \\le \\alpha \\le 30^\\circ$ | $\\mu_1 = 0,8$ |
                    | $30^\\circ < \\alpha < 60^\\circ$ | $\\mu_1 = 0,8 \\cdot \\frac{60 - \\alpha}{30}$ |
                    | $\\alpha \\ge 60^\\circ$ | $\\mu_1 = 0,0$ |
                    
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                st.pyplot(plot_mu_coefficients(), use_container_width=True)


    # ==================================================================================
    # 2. PRZYCISK OBLICZEŃ
    # ==================================================================================
    b1, b2, b3 = st.columns([1, 2, 1])
    oblicz_clicked = False
    with b2:
        if st.button("OBLICZ", type="primary", use_container_width=True, key="dj_btn"):
            oblicz_clicked = True

    if oblicz_clicked:
        # --- 1. OBLICZENIE Sk ---
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

        # --- 2. OBLICZENIE Mu1 ---
        if snow_guards == "Tak":
            mu1 = 0.8
        else:
            mu1 = calculate_mu1(alpha)
        
        # --- 3. WYNIK KOŃCOWY ---
        s_val = mu1 * Ce * Ct * sk
        
        st.session_state["dj_sk"] = sk

        # ==============================================================================
        # 3. WYNIKI
        # ==============================================================================
        st.markdown("### WYNIKI")
        st.markdown("**Obciążenie dachu jednopołaciowego**")

        # Wykres wycentrowany, 50% szerokości
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            fig1 = plot_roof_mono(alpha, s_val)
            st.pyplot(fig1, use_container_width=True)

        # ==============================================================================
        # 4. SZCZEGÓŁY OBLICZEŃ
        # ==============================================================================
        with st.expander("Szczegóły obliczeń"):
            # 1. PODSTAWOWE DANE
            st.markdown("#### 1. Podstawowe dane")
            st.write(f"Strefa śniegowa: **{strefa}**")
            st.write(f"Wysokość nad poziomem morza: $A = {A:.2f} \\text{{ m n.p.m.}}$")
            st.write(f"Kąt nachylenia: $\\alpha = {alpha:.1f}^\\circ$")
            st.write(f"Współczynnik ekspozycji: $C_e = {Ce}$")
            st.write(f"Współczynnik termiczny: $C_t = {Ct}$")
            
            if snow_guards == "Tak":
                st.write("Bariery przeciwśnieżne: **TAK** (wymusza $\\mu_1 \\ge 0,8$)")
            else:
                st.write("Bariery przeciwśnieżne: **NIE** (standardowy ześlizg śniegu)")

            st.write(f"Obciążenie śniegiem gruntu: **$s_k = {sk:.2f} \\text{{ kN/m}}^2$**")
            st.write(f"Współczynnik kształtu dachu: **$\\mu_1 = {mu1:.3f}$**")
            
            # 2. OBLICZENIA
            st.markdown("#### 2. Wyniki szczegółowe")
            
            c1, c2, c3 = st.columns([1, 2, 1])
            with c2:
                st.pyplot(fig1, use_container_width=True)
            
            st.latex(
                r"s = \mu_1 \cdot C_e \cdot C_t \cdot s_k = "
                r"{:.3f} \cdot {} \cdot {} \cdot {:.2f} \, \text{{kN/m}}^2 = \mathbf{{{:.2f}}} \, \text{{kN/m}}^2"
                .format(mu1, Ce, Ct, sk, s_val)
            )

if __name__ == "__main__":
    run()