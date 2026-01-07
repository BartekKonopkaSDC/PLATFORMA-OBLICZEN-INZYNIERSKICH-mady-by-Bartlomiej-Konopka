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

def calculate_mu3(h, b):
    """
    Oblicza współczynnik kształtu dachu mu3 wg PN-EN 1991-1-3 (Wzór 5.5).
    Dla beta <= 60 stopni: mu3 = 0.2 + 10 * (h/b), ale nie więcej niż 2.0.
    """
    if b <= 0: return 0.0
    val = 0.2 + 10.0 * (h / b)
    if val > 2.0: val = 2.0
    return val

def get_tangent_angle(x, b, h):
    """Oblicza kąt stycznej do dachu w punkcie x (stopnie)."""
    if b <= 0: return 0.0
    derivative = (4 * h / (b**2)) * (b - 2 * x)
    angle_rad = math.atan(abs(derivative))
    return math.degrees(angle_rad)

def find_x_for_60_degrees(b, h):
    """Znajduje współrzędną x (od 0 do b/2), gdzie kąt stycznej wynosi 60 stopni."""
    tan60 = math.tan(math.radians(60))
    max_tan = 4 * h / b if b > 0 else 0
    
    if max_tan <= tan60:
        return 0.0, b 
    
    term = (tan60 * (b**2)) / (4 * h)
    x_left = (b - term) / 2.0
    x_right = b - x_left
    
    if x_left < 0: x_left = 0
    if x_right > b: x_right = b
    
    return x_left, x_right

def plot_geometry_schematic(b, h):
    fig, ax = plt.subplots(figsize=(4, 2.5))
    x = np.linspace(0, b, 100)
    y = (4 * h / (b**2)) * (b * x - x**2)
    ax.plot(x, y, color='black', linewidth=1.5)
    ax.plot([0, b], [0, 0], color='gray', linestyle='--', linewidth=1)
    
    ax.annotate('', xy=(0, -h*0.2), xytext=(b, -h*0.2), arrowprops=dict(arrowstyle='<->', color='blue', linewidth=1.5))
    ax.text(b/2, -h*0.35, f"b", ha='center', va='top', color='blue', fontweight='bold', fontsize=12)
    
    ax.annotate('', xy=(b/2, 0), xytext=(b/2, h), arrowprops=dict(arrowstyle='<->', color='red', linewidth=1.5))
    ax.text(b/2 + b*0.02, h/2, f"h", ha='left', va='center', color='red', fontweight='bold', fontsize=12)
    
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_ylim(-h*0.6, h*1.2)
    ax.set_xlim(-b*0.1, b*1.1)
    plt.tight_layout()
    return fig

def plot_mu3_chart():
    hb_ratios = np.linspace(0, 0.5, 200)
    mu_vals = []
    for r in hb_ratios:
        val = 0.2 + 10.0 * r
        if val > 2.0: val = 2.0
        mu_vals.append(val)
    
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(hb_ratios, mu_vals, color='black', linewidth=2)
    ax.set_xlabel(r'Stosunek $h/b$')
    ax.set_ylabel(r'Współczynnik kształtu $\mu_3$')
    ax.set_xticks(np.arange(0, 0.6, 0.1))
    ax.set_yticks(np.arange(0, 2.5, 0.5))
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.set_ylim(0, 2.2)
    ax.set_xlim(0, 0.5)
    ax.plot([0.18, 0.18], [0, 2.0], color='red', linestyle=':', linewidth=1)
    ax.text(0.19, 0.5, r'$h/b=0,18$', color='red', rotation=90, fontsize=10)
    ax.text(0.25, 2.05, r'max $\mu_3 = 2,0$', color='black', fontsize=9)
    plt.tight_layout()
    return fig

def plot_cylindrical_roof_horizontal_projection(b, h, sk, Ce, Ct, case_type, mu3_val):
    # 1. Geometria dachu
    x = np.linspace(0, b, 200)
    y = (4 * h / (b**2)) * (b * x - x**2)
    
    fig, ax = plt.subplots(figsize=(7, 8.5))
    
    # Zakresy śniegu
    x_start, x_end = find_x_for_60_degrees(b, h)
    ls_len = x_end - x_start
    is_cut = (x_start > 0.05)

    # Grunt i ściany
    wall_depth = 4.0 
    ground_y = -wall_depth
    
    ground_rect = patches.Rectangle((-2, ground_y - 1.0), b + 4, 1.0, facecolor='white', edgecolor='gray', hatch='///', linewidth=0, zorder=0)
    ax.add_patch(ground_rect)
    ax.plot([-2, b + 2], [ground_y, ground_y], color='black', linewidth=1.5)

    ax.plot([0, 0], [ground_y, 0], color='black', linewidth=2.5)
    ax.plot([b, b], [ground_y, 0], color='black', linewidth=2.5)
    ax.plot(x, y, color='black', linewidth=2.5, zorder=10)

    # --- KĄTY ---
    tangent_val = 4 * h / b if b > 0 else 0
    beta_okap = math.degrees(math.atan(tangent_val))
    
    # Zwiększony rozmiar łuków
    arc_base_size = b * 0.15 
    arc_draw_size = arc_base_size * 1.2
    
    if arc_base_size > 0:
        # LEWA BETA
        ax.plot([0, arc_base_size*1.2], [0, 0], color='black', linestyle='--', linewidth=0.8)
        arc_l = patches.Arc((0, 0), arc_draw_size, arc_draw_size, theta1=0, theta2=beta_okap, color='black', linewidth=0.8)
        ax.add_patch(arc_l)
        ax.text(arc_base_size*0.6, -0.2, f"$\\beta={beta_okap:.0f}^\\circ$", color='black', fontsize=11, ha='left', va='top')
        
        # PRAWA BETA (symetria)
        ax.plot([b, b-arc_base_size*1.2], [0, 0], color='black', linestyle='--', linewidth=0.8)
        arc_r = patches.Arc((b, 0), arc_draw_size, arc_draw_size, theta1=180-beta_okap, theta2=180, color='black', linewidth=0.8)
        ax.add_patch(arc_r)
        ax.text(b - arc_base_size*0.6, -0.2, f"$\\beta={beta_okap:.0f}^\\circ$", color='black', fontsize=11, ha='right', va='top')

    # Kąty 60 stopni
    if is_cut:
        y_cut = (4 * h / (b**2)) * (b * x_start - x_start**2)
        tan_len = 1.5 
        
        # LEWE 60
        ax.plot([x_start, x_start+tan_len], [y_cut, y_cut], color='black', linewidth=0.5)
        arc_60_l = patches.Arc((x_start, y_cut), arc_draw_size, arc_draw_size, theta1=0, theta2=60, color='black', linewidth=0.5)
        ax.add_patch(arc_60_l)
        ax.text(x_start + 0.2, y_cut - 0.4, r"$60^\circ$", fontsize=9, va='top', ha='left')
        
        # PRAWE 60
        ax.plot([x_end, x_end-tan_len], [y_cut, y_cut], color='black', linewidth=0.5)
        arc_60_r = patches.Arc((x_end, y_cut), arc_draw_size, arc_draw_size, theta1=120, theta2=180, color='black', linewidth=0.5)
        ax.add_patch(arc_60_r)
        ax.text(x_end - 0.2, y_cut - 0.4, r"$60^\circ$", fontsize=9, ha='right', va='top')
        
        # Linie pionowe odcięcia
        ax.plot([x_start, x_start], [y_cut, h + 3.0], color='red', linestyle=':', linewidth=1)
        ax.plot([x_end, x_end], [y_cut, h + 3.0], color='red', linestyle=':', linewidth=1)

    # --- WYMIAROWANIE ---
    
    # 1. Wymiar b (nad terenem)
    dim_y_b = ground_y + 0.3
    ax.annotate('', xy=(0, dim_y_b), xytext=(b, dim_y_b), arrowprops=dict(arrowstyle='<->', color='black', linewidth=1.2))
    ax.text(b/2, dim_y_b + 0.1, f"$b={b:.1f}$m", ha='center', va='bottom', fontsize=10)
    
    # 2. Wymiar h
    ax.annotate('', xy=(b/2, 0), xytext=(b/2, h), arrowprops=dict(arrowstyle='<->', color='black', linewidth=1.2))
    ax.text(b/2 + 0.2, h/2, f"$h={h:.1f}$m", ha='left', va='center', fontsize=10)

    # 3. Wymiary ls i podział (nad dachem)
    main_dim_y = h + 1.2
    dim_start = x_start if is_cut else 0
    dim_end = x_end if is_cut else b
    dim_label = r"$l_s$" if is_cut else r"$b$"
    
    if is_cut: 
        ax.annotate('', xy=(dim_start, main_dim_y), xytext=(dim_end, main_dim_y), arrowprops=dict(arrowstyle='<->', color='red', linewidth=1.2))
        ax.text((dim_start+dim_end)/2, main_dim_y + 0.1, dim_label, color='red', ha='center', va='bottom')
    
    # Dodatkowa linia podziałowa (4 segmenty) - TYLKO DLA PRZYPADKU (II)
    if case_type == 'ii':
        sub_dim_y = main_dim_y + 0.8
        seg_len = (dim_end - dim_start) / 4.0
        seg_label = r"$l_s/4$" if is_cut else r"$b/4$"
        sub_dim_color = 'red' if is_cut else 'black'
        
        for i in range(4):
            x_s = dim_start + i * seg_len
            x_e = dim_start + (i + 1) * seg_len
            ax.annotate('', xy=(x_s, sub_dim_y), xytext=(x_e, sub_dim_y), arrowprops=dict(arrowstyle='<->', color=sub_dim_color, linewidth=0.8))
            ax.text((x_s + x_e)/2, sub_dim_y + 0.1, seg_label, ha='center', va='bottom', fontsize=8, color=sub_dim_color)

    # --- OBCIĄŻENIE ---
    load_base_y = h + 3.5 
    scale_factor = 2.5
    color = '#1f77b4'
    
    def draw_block(xs, ys, label_val, label_x):
        # Tło
        fill_xs = list(xs) + [xs[-1], xs[0]]
        fill_ys = list(ys) + [load_base_y, load_base_y]
        poly = list(zip(fill_xs, fill_ys))
        rect = patches.Polygon(poly, closed=True, facecolor=color, edgecolor=color, alpha=0.15, linewidth=1.2)
        ax.add_patch(rect)
        
        ax.plot(xs, ys, color=color, linewidth=2)
        ax.plot([min(xs), max(xs)], [load_base_y, load_base_y], color='gray', linewidth=0.5)
        ax.plot([xs[0], xs[0]], [load_base_y, ys[0]], color=color, linewidth=1)
        ax.plot([xs[-1], xs[-1]], [load_base_y, ys[-1]], color=color, linewidth=1)
        
        width = max(xs) - min(xs)
        if width > 0.1:
            n_arrows = max(3, int(width * 1.2))
            for ax_x in np.linspace(min(xs) + width*0.1, max(xs) - width*0.1, n_arrows):
                y_top = np.interp(ax_x, xs, ys)
                h_arrow = y_top - load_base_y
                if h_arrow > 0.2:
                    ax.arrow(ax_x, y_top, 0, -h_arrow + 0.05, head_width=0.15, head_length=0.15, fc=color, ec=color, length_includes_head=True)
        
        if label_val > 0.01:
            ax.text(label_x, max(ys) + 0.2, f"{label_val:.2f} kN/m²", ha='center', va='bottom', fontsize=11, fontweight='bold')

    if case_type == 'i':
        # (i) Prostokąt
        mu = 0.8
        val = mu * Ce * Ct * sk
        if val > 0.01:
            draw_block([dim_start, dim_end], [load_base_y + val * scale_factor, load_base_y + val * scale_factor], val, (dim_start+dim_end)/2)

    else:
        # (ii) Trójkąty
        peak1_x = dim_start + ls_len / 4.0
        peak2_x = dim_end - ls_len / 4.0
        
        val_left = 0.5 * mu3_val * Ce * Ct * sk
        val_right = 1.0 * mu3_val * Ce * Ct * sk
        
        mid_x = dim_start + ls_len / 2.0
        
        # Lewy
        l_xs = [dim_start, peak1_x, mid_x]
        l_ys = [load_base_y, load_base_y + val_left * scale_factor, load_base_y]
        draw_block(l_xs, l_ys, val_left, peak1_x)
        
        # Prawy
        r_xs = [mid_x, peak2_x, dim_end]
        r_ys = [load_base_y, load_base_y + val_right * scale_factor, load_base_y]
        draw_block(r_xs, r_ys, val_right, peak2_x)

    ax.set_aspect('equal')
    ax.axis('off')
    
    max_s = max(0.8, mu3_val) * sk * Ce * Ct
    top_limit = load_base_y + (max_s * scale_factor) + 2.0
    ax.set_ylim(ground_y - 1.5, top_limit)
    ax.set_xlim(-2.5, b + 2.5)
    
    plt.tight_layout()
    return fig

def run():
    if "dwl_sk" not in st.session_state: st.session_state["dwl_sk"] = 0.0

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

    with st.expander("🗺️ Mapa stref śniegowych wg PN-EN 1991-1-3"):
        if os.path.exists(mapa_path):
            m1, m2, m3 = st.columns([1, 2, 1])
            with m2:
                st.image(mapa_path) 
        else:
            st.warning("Brak pliku 'mapa_stref.png'.")

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
            key="dwl_city_mode",
            horizontal=True
        )
    
        use_city = (city_mode == "Tak")
        sel_strefa_index = 1
        default_A = 200.0
        disable_strefa = False

        if use_city:
            lista_miast = sorted(list(MIASTA_DB.keys()))
            idx_default = lista_miast.index("Warszawa") if "Warszawa" in lista_miast else 0
            wybrane_miasto = st.selectbox("Wybierz miasto:", lista_miast, index=idx_default, key="dwl_city")
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
            key="dwl_strefa"
        )
        if disable_strefa:
            st.caption(f"🔒 Strefa przypisana dla: {wybrane_miasto}")

        A = st.number_input("Wysokość nad poziomem morza $A$ [m]", value=default_A, step=10.0, format="%.1f", key="dwl_A")
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
            key="dwl_teren"
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
        st.text_input("Współczynnik ekspozycji $C_e$", value=str(current_Ce), disabled=True, key="dwl_Ce_disp")

        st.markdown(r"Czy dach ma przenikalność ciepła $U > 1 \, \small \frac{W}{m^2 \cdot K}$?")
        ct_mode = st.radio("ct_mode_label", ["Nie", "Tak"], index=0, label_visibility="collapsed", key="dwl_ct_mode", horizontal=True)
        
        Ct_val = 1.0
        if ct_mode == "Tak":
            c_u, c_ti = st.columns(2)
            with c_u:
                U_input = st.number_input("Wsp. $U$", value=2.0, step=0.1, min_value=1.0, key="dwl_U")
            with c_ti:
                Ti_input = st.number_input("Temp. $T_i$", value=18.0, step=1.0, key="dwl_Ti")
            Ct_val = calculate_ct_iso(U_input, Ti_input)
            st.text_input("Współczynnik termiczny $C_t$", value=str(Ct_val), disabled=True, key="dwl_ct_disp")
        else:
            st.text_input("Współczynnik termiczny $C_t$", value="1.0", disabled=True, key="dwl_ct_disp_no")

    # -------------------------------------------------------------------------
    # KOLUMNA 3: Geometria (Dla dachu walcowego - bez barier, mu1 zawsze 0.8)
    # -------------------------------------------------------------------------
    with col3:
        curr_b = st.session_state.get("dwl_b", 12.0)
        curr_h = st.session_state.get("dwl_h", 2.0)
        st.pyplot(plot_geometry_schematic(curr_b, curr_h), use_container_width=False)
        
        b_dim = st.number_input("Szerokość (rozpiętość) $b$ [m]", value=12.0, step=0.5, min_value=0.1, key="dwl_b")
        h_dim = st.number_input("Wyniosłość (strzałka) $h$ [m]", value=2.0, step=0.1, min_value=0.0, key="dwl_h")
        
        tangent_val = 4 * h_dim / b_dim if b_dim > 0 else 0
        beta_okap = math.degrees(math.atan(tangent_val))
        
        st.caption(f"Kąt stycznej przy okapie $\\beta \\approx {beta_okap:.1f}^\\circ$")
        
        mu3_calc = calculate_mu3(h_dim, b_dim)
        
        with st.expander("ℹ️ Współczynnik kształtu dachu $\mu_3$"):
            st.markdown(r"""
            | Kąt nachylenia stycznej $\beta$ | Współczynnik $\mu_3$ |
            | :--- | :--- |
            | $\beta \leq 60^\circ$ | $\mu_3 = 0,2 + 10 \frac{h}{b} \leq 2,0$ |
            | $\beta > 60^\circ$ | $\mu_3 = 0$ |
            """)
            st.pyplot(plot_mu3_chart(), use_container_width=True)


    b1, b2, b3 = st.columns([1, 2, 1])
    oblicz_clicked = False
    with b2:
        if st.button("OBLICZ", type="primary", use_container_width=True, key="dwl_btn"):
            oblicz_clicked = True

    if oblicz_clicked:
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
        st.session_state["dwl_sk"] = sk

        s_uni_val = 0.8 * current_Ce * Ct_val * sk
        s_drift_max = mu3_calc * current_Ce * Ct_val * sk
        s_drift_min = 0.5 * s_drift_max

        st.markdown("### WYNIKI")

        fig1 = plot_cylindrical_roof_horizontal_projection(b_dim, h_dim, sk, current_Ce, Ct_val, 'i', mu3_calc)
        fig2 = plot_cylindrical_roof_horizontal_projection(b_dim, h_dim, sk, current_Ce, Ct_val, 'ii', mu3_calc)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Przypadek (i) – Obciążenie równomierne**")
            st.pyplot(fig1, use_container_width=True)

        with c2:
            st.markdown("**Przypadek (ii) – Obciążenie nierównomierne**")
            st.pyplot(fig2, use_container_width=True)

        with st.expander("Szczegóły obliczeń"):
            st.markdown("#### 1. Podstawowe dane")
            st.write(f"Strefa: **{strefa}**, Wysokość $A = {A}$ m n.p.m.")
            st.write(f"Współczynnik ekspozycji $C_e = {current_Ce}$, termiczny $C_t = {Ct_val}$")
            st.write(f"Obciążenie gruntu $s_k = {sk:.3f}$ kN/m²")
            
            hb_ratio = h_dim / b_dim
            st.write(f"Stosunek wysokości dachu do szerokości: $h/b = {hb_ratio:.3f}$")
            st.write(f"Współczynnik kształtu dachu: $\mu_3 = {mu3_calc:.3f}$")
            
            st.write(f"Kąt stycznej przy okapie: $\\beta = {beta_okap:.1f}^\\circ$")
            if beta_okap > 60:
                st.warning(r"Uwaga: Część dachu ma nachylenie $> 60^\circ$, w tych miejscach obciążenie $\mu = 0$.")

            st.markdown("#### 2. Wyniki szczegółowe")
            
            st.markdown("**Przypadek (i) – Obciążenie równomierne**")
            c1_d, c2_d, c3_d = st.columns([1, 2, 1])
            with c2_d:
                st.pyplot(fig1, use_container_width=True)
            st.latex(r"s = 0,8 \cdot C_e \cdot C_t \cdot s_k = " + f"0,8 \\cdot {current_Ce} \\cdot {Ct_val} \\cdot {sk:.2f} \, \\text{{kN/m}}^2 = \\mathbf{{{s_uni_val:.2f}}} \\, \\text{{kN/m}}^2")
            
            st.divider()

            st.markdown("**Przypadek (ii) – Obciążenie nierównomierne**")
            c1_d, c2_d, c3_d = st.columns([1, 2, 1])
            with c2_d:
                st.pyplot(fig2, use_container_width=True)

            st.markdown("**Obciążenie na połaci 'nawietrznej' (szczyt 1):**")
            st.latex(r"s_{t,1} = \mu_3 \cdot C_e \cdot C_t \cdot s_k = " + f"{mu3_calc:.2f} \\cdot {current_Ce} \\cdot {Ct_val} \\cdot {sk:.2f} \, \\text{{kN/m}}^2 = \\mathbf{{{s_drift_max:.2f}}} \\, \\text{{kN/m}}^2")
            
            st.markdown("**Obciążenie na połaci 'zawietrznej' (szczyt 2):**")
            st.latex(r"s_{t,2} = 0,5 \cdot s_{t,1} = \mathbf{" + f"{s_drift_min:.2f}" + r"} \, \text{kN/m}^2")

if __name__ == "__main__":
    run()