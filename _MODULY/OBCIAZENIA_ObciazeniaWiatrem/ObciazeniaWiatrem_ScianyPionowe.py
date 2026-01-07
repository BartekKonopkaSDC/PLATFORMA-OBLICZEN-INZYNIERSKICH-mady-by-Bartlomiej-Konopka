import streamlit as st
import math
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import pandas as pd

# ======================================================================================
# 1. BAZA DANYCH I PARAMETRY
# ======================================================================================
MIASTA_DB = {
    "Białystok":            {"strefa": "1", "A": 150},
    "Bielsko-Biała":        {"strefa": "1", "A": 330},
    "Bydgoszcz":            {"strefa": "1", "A": 60},
    "Bytom":                {"strefa": "1", "A": 280},
    "Chełm":                {"strefa": "1", "A": 190},
    "Chorzów":              {"strefa": "1", "A": 280},
    "Częstochowa":          {"strefa": "1", "A": 260},
    "Dąbrowa Górnicza":     {"strefa": "1", "A": 270},
    "Elbląg":               {"strefa": "1", "A": 10},
    "Gdańsk":               {"strefa": "2", "A": 15},
    "Gdynia":               {"strefa": "2", "A": 30},
    "Gliwice":              {"strefa": "1", "A": 220},
    "Gorzów Wielkopolski":  {"strefa": "1", "A": 20},
    "Grudziądz":            {"strefa": "1", "A": 50},
    "Jelenia Góra":         {"strefa": "3", "A": 350},
    "Kalisz":               {"strefa": "1", "A": 140},
    "Katowice":             {"strefa": "1", "A": 270},
    "Kielce":               {"strefa": "1", "A": 260},
    "Konin":                {"strefa": "1", "A": 100},
    "Koszalin":             {"strefa": "2", "A": 35},
    "Kraków":               {"strefa": "1", "A": 220},
    "Legnica":              {"strefa": "1", "A": 120},
    "Lublin":               {"strefa": "1", "A": 200},
    "Łódź":                 {"strefa": "1", "A": 220},
    "Nowy Sącz":            {"strefa": "3", "A": 300},
    "Olsztyn":              {"strefa": "1", "A": 140},
    "Opole":                {"strefa": "1", "A": 175},
    "Płock":                {"strefa": "1", "A": 100},
    "Poznań":               {"strefa": "1", "A": 85},
    "Radom":                {"strefa": "1", "A": 180},
    "Ruda Śląska":          {"strefa": "1", "A": 270},
    "Rybnik":               {"strefa": "1", "A": 240},
    "Rzeszów":              {"strefa": "1", "A": 220},
    "Siedlce":              {"strefa": "1", "A": 155},
    "Sosnowiec":            {"strefa": "1", "A": 260},
    "Suwałki":              {"strefa": "1", "A": 170},
    "Szczecin":             {"strefa": "1", "A": 25},
    "Świnoujście":          {"strefa": "2", "A": 5},
    "Tarnów":               {"strefa": "1", "A": 210},
    "Toruń":                {"strefa": "1", "A": 50},
    "Tychy":                {"strefa": "1", "A": 260},
    "Wałbrzych":            {"strefa": "3", "A": 450},
    "Warszawa":             {"strefa": "1", "A": 110},
    "Włocławek":            {"strefa": "1", "A": 65},
    "Wrocław":              {"strefa": "1", "A": 120},
    "Zabrze":               {"strefa": "1", "A": 260},
    "Zakopane":             {"strefa": "3", "A": 850},
    "Zielona Góra":         {"strefa": "1", "A": 150},
}

TERRAIN_PARAMS = {
    "0":   {"z0": 0.003, "zmin": 1.0,  "opis": "Obszary morskie, przybrzeżne wystawione na otwarte morze"},
    "I":   {"z0": 0.01,  "zmin": 1.0,  "opis": "Jeziora, tereny płaskie poziome, zaniedbywalna roślinność, brak przeszkód"},
    "II":  {"z0": 0.05,  "zmin": 2.0,  "opis": "Niska roślinność (trawa), izolowane przeszkody (drzewa, zabudowania) w odległości > 20h"},
    "III": {"z0": 0.30,  "zmin": 5.0,  "opis": "Regularne pokrycie roślinnością/budynkami, izolowane przeszkody w odległości < 20h (wsie, przedmieścia, lasy)"},
    "IV":  {"z0": 1.00,  "zmin": 10.0, "opis": "Obszary, na których min. 15% powierzchni pokrywają budynki o h > 15m"}
}

def update_city_defaults():
    """Funkcja callback aktualizująca strefę i wysokość po wyborze miasta."""
    sel_city = st.session_state.get("ddp_city_w")
    if sel_city in MIASTA_DB:
        st.session_state["ddp_strefa_w"] = MIASTA_DB[sel_city]["strefa"]
        st.session_state["ddp_A_w"] = float(MIASTA_DB[sel_city]["A"])

def get_vb0_value(strefa, A):
    vb0 = 22.0 
    if strefa == "1":
        if A <= 300: vb0 = 22.0
        else: vb0 = 22.0 * (1.0 + 0.0006 * (A - 300.0))
    elif strefa == "2":
        vb0 = 26.0
    elif strefa == "3":
        if A <= 300: vb0 = 22.0
        else: vb0 = 22.0 * (1.0 + 0.0006 * (A - 300.0))
    return vb0

def calc_single_qp(z_val, terrain_cat, vb):
    params = TERRAIN_PARAMS[terrain_cat]
    z0 = params["z0"]
    zmin = params["zmin"]
    z0_II = 0.05
    kr = 0.19 * ((z0 / z0_II) ** 0.07)
    rho = 1.25
    z_calc = max(z_val, zmin)
    cr = kr * math.log(z_calc / z0)
    co = 1.0
    vm = cr * co * vb
    kl = 1.0
    Iv = kl / (co * math.log(z_calc / z0))
    qp_pa = (1.0 + 7.0 * Iv) * 0.5 * rho * (vm ** 2)
    qp_kn = qp_pa / 1000.0
    return qp_kn

def calc_wind_profile(z_max, terrain_cat, vb, num_points=100):
    heights = np.linspace(0.0, z_max, num_points)
    qp_values = []
    for z in heights:
        qp = calc_single_qp(z, terrain_cat, vb)
        qp_values.append(qp)
    return heights, qp_values, TERRAIN_PARAMS[terrain_cat]["zmin"]

def get_cdir_value_from_table(strefa, angle):
    val = 1.0
    if strefa == "1":
        if angle in [210, 240, 270]: val = 1.0
        elif angle in [180, 300]: val = 0.9
        elif angle in [120, 150]: val = 0.7
        else: val = 0.8
    elif strefa == "2":
        if angle in [240, 270, 300, 330, 0, 30]: val = 1.0
        elif angle in [210]: val = 0.9
        elif angle in [60, 90, 180]: val = 0.8
        elif angle in [120, 150]: val = 0.7
        else: val = 1.0 
    elif strefa == "3":
        if angle in [180, 210, 240, 270]: val = 1.0
        elif angle in [150, 300]: val = 0.9
        elif angle in [120]: val = 0.7
        else: val = 0.8
    return val

# --------------------------------------------------------------------------------------
# 5. RYSUNEK SCHEMATYCZNY (GEOMETRIA 3D)
# --------------------------------------------------------------------------------------

def draw_geometry_schematic(b, d, z, show_user_z=False):
    """Rysunek 3D w panelu wejściowym"""
    fig, ax = plt.subplots(figsize=(4, 3)) 
    ax.set_aspect('equal')
    ax.axis('off')
    
    max_dim = max(b, d, z)
    if max_dim == 0: max_dim = 10
    scale = 10.0 / max_dim
    bb, dd, zz = b * scale, d * scale, z * scale
    
    angle = np.radians(30)
    cos_a = np.cos(angle)
    sin_a = np.sin(angle)
    
    vec_d = (dd * cos_a, dd * sin_a)
    vec_b = (-bb * cos_a, bb * sin_a)
    origin = (0, 0)
    
    p_center = origin
    p_right = (origin[0] + vec_d[0], origin[1] + vec_d[1])
    p_left  = (origin[0] + vec_b[0], origin[1] + vec_b[1])
    p_back  = (p_left[0] + vec_d[0], p_left[1] + vec_d[1])
    
    def add_z(p, z_val): return (p[0], p[1] + z_val)
    p_center_top = add_z(p_center, zz)
    p_right_top  = add_z(p_right, zz)
    p_left_top   = add_z(p_left, zz)
    p_back_top   = add_z(p_back, zz)

    ax.plot([p_left[0], p_center[0]], [p_left[1], p_center[1]], 'k-', lw=1.2)
    ax.plot([p_center[0], p_center_top[0]], [p_center[1], p_center_top[1]], 'k-', lw=1.2)
    ax.plot([p_center_top[0], p_left_top[0]], [p_center_top[1], p_left_top[1]], 'k-', lw=1.2)
    ax.plot([p_left_top[0], p_left[0]], [p_left_top[1], p_left[1]], 'k-', lw=1.2)
    
    ax.plot([p_center[0], p_right[0]], [p_center[1], p_right[1]], 'k-', lw=1.2)
    ax.plot([p_right[0], p_right_top[0]], [p_right[1], p_right_top[1]], 'k-', lw=1.2)
    ax.plot([p_right_top[0], p_center_top[0]], [p_right_top[1], p_center_top[1]], 'k-', lw=1.2)
    
    ax.plot([p_left_top[0], p_back_top[0]], [p_left_top[1], p_back_top[1]], 'k-', lw=1.2)
    ax.plot([p_back_top[0], p_right_top[0]], [p_back_top[1], p_right_top[1]], 'k-', lw=1.2)
    
    ax.plot([p_left[0], p_back[0]], [p_left[1], p_back[1]], 'grey', ls=':', lw=0.8)
    ax.plot([p_back[0], p_right[0]], [p_back[1], p_right[1]], 'grey', ls=':', lw=0.8)
    ax.plot([p_back[0], p_back_top[0]], [p_back[1], p_back_top[1]], 'grey', ls=':', lw=0.8)

    mid_left_x = (p_left[0] + p_center[0]) / 2
    mid_left_y = (p_left[1] + p_center_top[1]) / 2
    
    # Strzałka - krótsza o połowę (0.3)
    arrow_len_sch = bb * 0.4 
    if arrow_len_sch < 1.0: arrow_len_sch = 1.0
    
    # Odsunięta
    dist_mult = 2.0
    start_x = mid_left_x - dist_mult*cos_a - arrow_len_sch*cos_a
    start_y = mid_left_y - dist_mult*sin_a - arrow_len_sch*sin_a
    end_x = mid_left_x - dist_mult*cos_a
    end_y = mid_left_y - dist_mult*sin_a
    
    # "Tłusta" strzałka
    ax.arrow(start_x, start_y, end_x - start_x, end_y - start_y, 
             head_width=max(zz*0.15, 0.75), width=max(zz*0.04, 0.1), 
             color='#1f77b4', length_includes_head=True)
    
    # W blisko strzałki
    ax.text(start_x + 1, start_y + 1.75, "W", color='#1f77b4', fontsize=12, ha='right', va='top', fontweight='bold', rotation=30)

    def draw_dim_line(x1, y1, x2, y2, text, offset_x=0, offset_y=0):
        ax.plot([x1, x1+offset_x], [y1, y1+offset_y], 'k-', lw=0.4, alpha=0.5)
        ax.plot([x2, x2+offset_x], [y2, y2+offset_y], 'k-', lw=0.4, alpha=0.5)
        ax.annotate("", xy=(x1+offset_x, y1+offset_y), xytext=(x2+offset_x, y2+offset_y), arrowprops=dict(arrowstyle='<->', lw=0.6, color='black'))
        mid_x = (x1+x2)/2 + offset_x
        mid_y = (y1+y2)/2 + offset_y
        ax.text(mid_x, mid_y, text, ha='center', va='center', fontsize=9, bbox=dict(facecolor='white', edgecolor='none', pad=0.5, alpha=0.8))

    draw_dim_line(p_right[0], p_right[1], p_right_top[0], p_right_top[1], "z", offset_x=0.5, offset_y=0)
    off_b_dist = 0.5
    draw_dim_line(p_left[0], p_left[1], p_center[0], p_center[1], "b", offset_x=-off_b_dist*sin_a - 0.2, offset_y=-off_b_dist*cos_a)
    off_d_dist = 0.5
    draw_dim_line(p_center[0], p_center[1], p_right[0], p_right[1], "d", offset_x=off_d_dist*sin_a + 0.2, offset_y=-off_d_dist*cos_a)

    if show_user_z:
        uzz = zz * 0.66
        p_l_u = (p_left[0], p_left[1] + uzz)
        p_c_u = (p_center[0], p_center[1] + uzz)
        p_r_u = (p_right[0], p_right[1] + uzz)
        
        ax.plot([p_l_u[0], p_c_u[0]], [p_l_u[1], p_c_u[1]], color='#d62728', linestyle='--', lw=1.0)
        ax.plot([p_c_u[0], p_r_u[0]], [p_c_u[1], p_r_u[1]], color='#d62728', linestyle='--', lw=1.0)
        
        mid_d_x = (p_center[0] + p_right[0]) / 2
        mid_d_y = (p_center[1] + p_right[1]) / 2
        mid_d_u_x = mid_d_x
        mid_d_u_y = mid_d_y + uzz
        
        ax.annotate("", xy=(mid_d_x, mid_d_y), xytext=(mid_d_u_x, mid_d_u_y),
                    arrowprops=dict(arrowstyle='<->', lw=1.0, color='#d62728'))
        
        ax.text(mid_d_u_x + 0.2, (mid_d_y + mid_d_u_y)/2, r"$z_{user}$", color='#d62728', fontsize=8, ha='left', va='center')

    plt.tight_layout()
    return fig

# ======================================================================================
# FUNKCJE RYSOWANIA WYNIKÓW
# ======================================================================================

def plot_wind_pressure_profile(heights, qp_values, z_max, qp_max, z_min, user_z=None, user_qp=None):
    fig, ax = plt.subplots(figsize=(5, 3.8))
    FONT_S, FONT_M = 7, 8
    ax.plot(qp_values, heights, color='#1f77b4', linewidth=2.0, label=r'$q_p(z)$')
    ax.fill_betweenx(heights, 0, qp_values, color='#1f77b4', alpha=0.15)
    n_arrows = 8
    step = max(1, len(heights) // n_arrows)
    for i in range(step, len(heights), step):
        h_val = heights[i]
        q_val = qp_values[i]
        if h_val > 0.2:
            ax.arrow(0, h_val, q_val, 0, head_width=0.2, head_length=max(qp_values)*0.04, fc='#1f77b4', ec='#1f77b4', length_includes_head=True, alpha=0.8, lw=0.6)
    qp_zmin = qp_values[0]
    if z_min < z_max:
        ax.plot([0, qp_zmin], [z_min, z_min], color='gray', linestyle=':', linewidth=1.0)
        ax.text(qp_zmin + 0.02, z_min, f"$z_{{min}}={z_min}$m\n$q_p={qp_zmin:.2f}$", fontsize=FONT_S, va='center', color='black', fontfamily='serif')
    ax.plot([0, qp_max], [z_max, z_max], color='black', linestyle='--', linewidth=1.0)
    ax.text(qp_max + 0.02, z_max, f"$z={z_max}$m\n$q_p={qp_max:.2f}$", fontsize=FONT_M, va='center', color='black', fontfamily='serif')
    if user_z is not None and user_qp is not None:
        if abs(user_z - z_max) > 0.1 and abs(user_z - z_min) > 0.1:
            ax.plot([0, user_qp], [user_z, user_z], color='#d62728', linestyle='--', linewidth=1.5)
            ax.scatter([user_qp], [user_z], color='#d62728', s=25, zorder=6)
            ax.text(user_qp + 0.02, user_z, f"$z={user_z}$m\n$q_p={user_qp:.2f}$", fontsize=FONT_M, va='center', color='#d62728', fontfamily='serif')
    ax.set_ylabel('Wysokość $z$ [m]', fontsize=FONT_M, fontfamily='serif')
    ax.set_xlabel('Wartość szczytowa ciśnienia prędkości $q_p$ [kN/m²]', fontsize=FONT_M, fontfamily='serif')
    ax.tick_params(axis='both', which='major', labelsize=FONT_S)
    ax.set_ylim(0, z_max * 1.15); ax.set_xlim(0, max(qp_values) * 1.6)
    ax.grid(True, linestyle='--', alpha=0.6)
    ground_line = patches.Rectangle((-1, -2), width=10, height=2, facecolor='white', hatch='///', edgecolor='gray')
    ax.add_patch(ground_line); ax.axhline(0, color='black', linewidth=1.5)
    plt.tight_layout()
    return fig

# --- Rysunek 1: Geometria i Strefy (Jedna strzałka) ---
def draw_wall_zones_geometry(b, d, h):
    e = min(b, 2 * h)
    fig, ax = plt.subplots(figsize=(6, 4.5))
    FONT_DIM = 8
    FONT_W = 11
    FONT_ZONE = 10
    
    margin_x = max(d, b) * 0.45
    margin_y = max(d, b) * 0.45
    ax.set_xlim(-margin_x, d + margin_x)
    ax.set_ylim(-margin_y, b + margin_y)
    ax.set_aspect('equal')
    ax.axis('off')
    
    # 1. Jedna Strzałka wiatru
    arrow_len = d * 0.25
    gap_w = d * 0.35
    arrow_end_x = -gap_w
    arrow_start_x = arrow_end_x - arrow_len
    
    ax.arrow(arrow_start_x, b/2, arrow_len, 0, head_width=b*0.06, head_length=b*0.06, 
             fc='#1f77b4', ec='#1f77b4', width=b*0.008, length_includes_head=True)
    
    # W nad strzałką, wyśrodkowane
    ax.text((arrow_start_x + arrow_end_x)/1.75, b/2 + b*0.02, "W", ha='center', va='bottom', 
            color='#1f77b4', fontsize=FONT_W, fontweight='bold', fontfamily='serif')
    
    # 2. Obrys
    rect = patches.Rectangle((0, 0), d, b, linewidth=1.5, edgecolor='black', facecolor='white', zorder=1)
    ax.add_patch(rect)
    
    # 3. Linie stref (krawędziowe)
    dist_A = e / 5.0
    tick_len = b * 0.05
    # Góra (wychodzi na zewnątrz)
    ax.plot([dist_A, dist_A], [b, b+tick_len], 'k-', lw=0.8)
    if e < d: ax.plot([e, e], [b, b+tick_len], 'k-', lw=0.8)
    # Dół (wychodzi na zewnątrz)
    ax.plot([dist_A, dist_A], [0, -tick_len], 'k-', lw=0.8)
    if e < d: ax.plot([e, e], [0, -tick_len], 'k-', lw=0.8)

    # 4. Opisy stref
    offset_lbl = b * 0.05
    # D, E
    ax.text(-d*0.03, b/2, "D", ha='right', va='center', fontsize=FONT_ZONE, fontweight='bold', color='red', fontfamily='serif')
    ax.text(d + d*0.03, b/2, "E", ha='left', va='center', fontsize=FONT_ZONE, fontweight='bold', color='red', fontfamily='serif')
    
    # A, B, C (Góra i Dół)
    center_A = dist_A / 2
    ax.text(center_A, b + 0.5*offset_lbl, "A", ha='center', va='bottom', fontsize=FONT_ZONE, fontweight='bold', color='red', fontfamily='serif')
    ax.text(center_A, -0.5*offset_lbl, "A", ha='center', va='top', fontsize=FONT_ZONE, fontweight='bold', color='red', fontfamily='serif')
    
    if d > dist_A:
        end_B = min(e, d)
        center_B = (dist_A + end_B) / 2
        ax.text(center_B, b + 0.5*offset_lbl, "B", ha='center', va='bottom', fontsize=FONT_ZONE, fontweight='bold', color='red', fontfamily='serif')
        ax.text(center_B, -0.5*offset_lbl, "B", ha='center', va='top', fontsize=FONT_ZONE, fontweight='bold', color='red', fontfamily='serif')
        
    if d > e:
        center_C = (e + d) / 2
        ax.text(center_C, b + 0.5*offset_lbl, "C", ha='center', va='bottom', fontsize=FONT_ZONE, fontweight='bold', color='red', fontfamily='serif')
        ax.text(center_C, -0.5*offset_lbl, "C", ha='center', va='top', fontsize=FONT_ZONE, fontweight='bold', color='red', fontfamily='serif')

    # 5. Wymiarowanie (Zewnątrz)
    def draw_dim(x1, y1, x2, y2, text, offset=0, rot=0, text_offset_y=0):
        dx, dy = x2-x1, y2-y1
        length = math.hypot(dx, dy)
        if length == 0: return
        nx, ny = -dy/length, dx/length
        
        # 1. Obliczamy punkty linii wymiarowej
        px1, py1 = x1 + nx*offset, y1 + ny*offset
        px2, py2 = x2 + nx*offset, y2 + ny*offset
        
        # Rysowanie linii i strzałek
        ax.plot([x1, px1], [y1, py1], 'k-', lw=0.5, alpha=0.5)
        ax.plot([x2, px2], [y2, py2], 'k-', lw=0.5, alpha=0.5)
        ax.annotate("", xy=(px1, py1), xytext=(px2, py2), arrowprops=dict(arrowstyle='<->', lw=0.6))
        
        # 2. Obliczamy środek linii wymiarowej
        mid_x = (px1 + px2) / 2
        mid_y = (py1 + py2) / 2
        
        # 3. Przesuwamy tekst względem środka linii o zadany text_offset_y
        tx = mid_x + nx * text_offset_y
        ty = mid_y + ny * text_offset_y
        
        ax.text(tx, ty, text, ha='center', va='center', rotation=rot, fontsize=8, 
                bbox=dict(facecolor='white', edgecolor='none', pad=0.2, alpha=0.7), fontfamily='serif')

    dim_offset_bot = -b * 0.4
    dim_offset_top = b * 0.4
    
    draw_dim(0, 0, d, 0, f"d = {d} m", offset=dim_offset_bot, text_offset_y=b*0.05)
    draw_dim(d, 0, d, b, f"b = {b} m", offset=dim_offset_bot, rot=90, text_offset_y=b*0.05)


     # Wymiar e/5 - WEWNĄTRZ STREFY A, przybliżony o połowę
    offset_inner = b * 0.25 # Głębiej w środku
        
    # e/5 i e - GÓRA
    draw_dim(0, b, dist_A, b, f"e/5={dist_A:.2f} m", offset=offset_inner, text_offset_y=-b*0.05)
          
    # e/5 - DÓŁ (Symetria)
    draw_dim(0, 0, dist_A, 0, f"e/5={dist_A:.2f} m", offset=-offset_inner, text_offset_y=b*0.05)

    plt.tight_layout()
    return fig

# --- Rysunek 2: Wartości ciśnień (Wyniki - ZEWNĘTRZNE) ---
def draw_wall_pressures_only(b, d, h, cpe_dict, qp_val):
    e = min(b, 2 * h)
    fig, ax = plt.subplots(figsize=(6, 4.5))
    FONT_VAL = 9
    FONT_W = 11
    
    margin_x = max(d, b) * 0.65
    margin_y = max(d, b) * 0.65
    ax.set_xlim(-margin_x, d + margin_x)
    ax.set_ylim(-margin_y, b + margin_y)
    ax.set_aspect('equal')
    ax.axis('off')
    
    # 1. Jedna Strzałka wiatru (centralnie)
    arrow_len = d * 0.25
    gap_w = d * 0.6
    arrow_end_x = -gap_w
    arrow_start_x = arrow_end_x - arrow_len
    
    ax.arrow(arrow_start_x, b/2, arrow_len, 0, head_width=b*0.06, head_length=b*0.06, 
             fc='#1f77b4', ec='#1f77b4', width=b*0.008, length_includes_head=True)
    # W nad strzałką
    ax.text((arrow_start_x + arrow_end_x)/1.85, b/2 + b*0.02, "W", ha='center', va='bottom', 
            color='#1f77b4', fontsize=FONT_W, fontweight='bold', fontfamily='serif')
    
    dist_A = min(e/5, d)
    dist_B = min(e, d)
    
    # Skalowanie wykresów
    vals = [abs(qp_val * v[0]) for v in cpe_dict.values()]
    max_val = max(vals) if vals else 1.0
    if max_val == 0: max_val = 1.0
    scale_factor = (min(b, d) * 0.25) / max_val

    def get_color(val):
        if val < 0: return '#cceeff' # Ssanie tło
        return '#ffcccc' # Parcie tło
    
    def get_arrow_color(val):
        if val < 0: return '#004c99' # Ssanie strzałka (mocny niebieski)
        return '#990000' # Parcie strzałka (mocny czerwony)
    
    def draw_pressure_block(x_start, y_start, w, h, val, orient):
        size = abs(val) * scale_factor
        color = get_color(val)
        arr_color = get_arrow_color(val)
        is_suction = (val < 0)
        
        if orient == 'left': # Ściana D
            rx, ry = x_start - size, y_start
            rw, rh = size, h
            arr_dx = 1 if not is_suction else -1
        elif orient == 'right': # Ściana E
            rx, ry = x_start, y_start
            rw, rh = size, h
            arr_dx = -1 if not is_suction else 1
        elif orient == 'top': # Ściany A, B, C (góra)
            rx, ry = x_start, y_start
            rw, rh = w, size
            arr_dy = -1 if not is_suction else 1
        elif orient == 'bottom': # Ściany A, B, C (dół)
            rx, ry = x_start, y_start - size
            rw, rh = w, size
            arr_dy = 1 if not is_suction else -1

        rect = patches.Rectangle((rx, ry), rw, rh, fc=color, ec='black', lw=0.5)
        ax.add_patch(rect)
        
        # Strzałki (Mocne kolory)
        arr_len_viz = size * 0.6
        if size > 0.1:
            if orient in ['left', 'right']:
                n_arr = max(1, int(h / (min(b,d)*0.3)))
                step = h / (n_arr + 1)
                for i in range(n_arr):
                    y_arr = ry + (i+1)*step
                    x_arr = rx + size/2 - (arr_len_viz/2)*arr_dx
                    ax.arrow(x_arr, y_arr, arr_len_viz*arr_dx, 0, head_width=size*0.15, fc=arr_color, ec=arr_color, length_includes_head=True)
            else:
                n_arr = max(1, int(w / (min(b,d)*0.3)))
                step = w / (n_arr + 1)
                for i in range(n_arr):
                    x_arr = rx + (i+1)*step
                    y_arr = ry + size/2 - (arr_len_viz/2)*arr_dy
                    ax.arrow(x_arr, y_arr, 0, arr_len_viz*arr_dy, head_width=size*0.15, fc=arr_color, ec=arr_color, length_includes_head=True)

        # Etykieta
        label = f"{val:.2f}\nkN/m²"
        if orient == 'left':
            ax.text(rx - size*0.1, ry + h/2, label, ha='right', va='center', fontsize=FONT_VAL, fontfamily='serif')
        elif orient == 'right':
            ax.text(rx + rw + size*0.1, ry + h/2, label, ha='left', va='center', fontsize=FONT_VAL, fontfamily='serif')
        elif orient == 'top':
            ax.text(rx + w/2, ry + rh + size*0.1, label, ha='center', va='bottom', fontsize=FONT_VAL, fontfamily='serif')
        elif orient == 'bottom':
            ax.text(rx + w/2, ry - size*0.1, label, ha='center', va='top', fontsize=FONT_VAL, fontfamily='serif')

    draw_pressure_block(0, 0, 0, b, qp_val * cpe_dict["D"][0], 'left')
    draw_pressure_block(d, 0, 0, b, qp_val * cpe_dict["E"][0], 'right')
    draw_pressure_block(0, b, dist_A, 0, qp_val * cpe_dict["A"][0], 'top')
    draw_pressure_block(0, 0, dist_A, 0, qp_val * cpe_dict["A"][0], 'bottom')
    
    if d > dist_A:
        len_B = min(e, d) - dist_A
        draw_pressure_block(dist_A, b, len_B, 0, qp_val * cpe_dict["B"][0], 'top')
        draw_pressure_block(dist_A, 0, len_B, 0, qp_val * cpe_dict["B"][0], 'bottom')
        
    if d > e:
        len_C = d - e
        draw_pressure_block(e, b, len_C, 0, qp_val * cpe_dict["C"][0], 'top')
        draw_pressure_block(e, 0, len_C, 0, qp_val * cpe_dict["C"][0], 'bottom')
        
    rect_main = patches.Rectangle((0, 0), d, b, fill=False, ec='black', lw=1.5, zorder=2)
    ax.add_patch(rect_main)
    
    # Wymiarowanie 
    def draw_dim(x1, y1, x2, y2, text, offset=0, rot=0, text_offset_y=0):
        dx, dy = x2-x1, y2-y1
        length = math.hypot(dx, dy)
        if length == 0: return
        nx, ny = -dy/length, dx/length
        
        # 1. Obliczamy punkty linii wymiarowej
        px1, py1 = x1 + nx*offset, y1 + ny*offset
        px2, py2 = x2 + nx*offset, y2 + ny*offset
        
        # Rysowanie linii i strzałek
        ax.plot([x1, px1], [y1, py1], 'k-', lw=0.5, alpha=0.5)
        ax.plot([x2, px2], [y2, py2], 'k-', lw=0.5, alpha=0.5)
        ax.annotate("", xy=(px1, py1), xytext=(px2, py2), arrowprops=dict(arrowstyle='<->', lw=0.6))
        
        # 2. Obliczamy środek linii wymiarowej
        mid_x = (px1 + px2) / 2
        mid_y = (py1 + py2) / 2
        
        # 3. POPRAWKA: Przesuwamy tekst względem środka linii o zadany text_offset_y
        tx = mid_x + nx * text_offset_y
        ty = mid_y + ny * text_offset_y
        
        ax.text(tx, ty, text, ha='center', va='center', rotation=rot, fontsize=8, 
                bbox=dict(facecolor='white', edgecolor='none', pad=0.2, alpha=0.7), fontfamily='serif')

    dim_offset_bot = -b * 0.6
    dim_offset_top = b * 0.6
    
    draw_dim(0, 0, d, 0, f"d = {d} m", offset=dim_offset_bot, text_offset_y=b*0.05)
    draw_dim(d, 0, d, b, f"b = {b} m", offset=-d*0.7, rot=90, text_offset_y=b*0.05)


     # Wymiar e/5 - WEWNĄTRZ STREFY A, przybliżony o połowę
    offset_inner = b * 0.1 # Głębiej w środku
        
    # e/5 i e - GÓRA
    draw_dim(0, b, dist_A, b, f"{dist_A:.2f} m", offset=-offset_inner, text_offset_y=-b*0.06)
          
    # e/5 - DÓŁ (Symetria)
    draw_dim(0, 0, dist_A, 0, f"{dist_A:.2f} m", offset=offset_inner, text_offset_y=b*0.06)
   

    plt.tight_layout()
    return fig

def get_cpe_full(h, d):
    ratio = h / d
    cpe10_A, cpe1_A = -1.2, -1.4
    cpe10_B, cpe1_B = -0.8, -1.1
    cpe10_C, cpe1_C = -0.5, -0.5
    
    if ratio <= 0.25: cpe_D = 0.7
    elif ratio >= 1.0: cpe_D = 0.8
    else: cpe_D = 0.7 + (0.8 - 0.7) * (ratio - 0.25) / 0.75
    cpe10_D = cpe1_D = round(cpe_D, 2)
        
    if ratio <= 0.25: cpe_E = -0.3
    elif ratio >= 5.0: cpe_E = -0.7
    elif ratio <= 1.0: cpe_E = -0.3 + (-0.5 - (-0.3)) * (ratio - 0.25) / 0.75
    else: cpe_E = -0.5 + (-0.7 - (-0.5)) * (ratio - 1.0) / 4.0
    cpe10_E = cpe1_E = round(cpe_E, 2)
    
    return {"A": (cpe10_A, cpe1_A), "B": (cpe10_B, cpe1_B), "C": (cpe10_C, cpe1_C), "D": (cpe10_D, cpe1_D), "E": (cpe10_E, cpe1_E)}

def run():
    if "ddp_qp_max" not in st.session_state: st.session_state["ddp_qp_max"] = 0.0

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
        </style>
        """,
        unsafe_allow_html=True
    )

    current_dir = os.path.dirname(os.path.abspath(__file__))
    mapa_path = os.path.join(current_dir, "mapa_stref_wiatr.png")

    with st.expander("🗺️ Mapa stref wiatrowych wg PN-EN 1991-1-4"):
        if os.path.exists(mapa_path):
            m1, m2, m3 = st.columns([1, 2, 1])
            with m2:
                st.image(mapa_path) 
        else:
            st.info(f"Brak pliku mapy: {os.path.basename(mapa_path)}.")

    st.markdown("### DANE WEJŚCIOWE")
    col1, col2, col3 = st.columns([0.3, 0.35, 0.35])

    with col1:
        st.write("Czy chcesz wybrać miejscowość z listy?")
        city_mode = st.radio("city_mode_w", ["Nie", "Tak"], index=0, label_visibility="collapsed", key="ddp_city_mode_w", horizontal=True)
    
        use_city = (city_mode == "Tak")
        sel_strefa_index = 0
        default_A = 200.0
        disable_strefa = False

        if use_city:
            lista_miast = sorted(list(MIASTA_DB.keys()))
            idx_krakow = lista_miast.index("Kraków") if "Kraków" in lista_miast else 0
            wybrane_miasto = st.selectbox("Wybierz miasto:", lista_miast, index=idx_krakow, key="ddp_city_w", on_change=update_city_defaults)
            dane_miasta = MIASTA_DB[wybrane_miasto]
            try:
                sel_strefa_index = ["1", "2", "3"].index(dane_miasta["strefa"])
            except ValueError:
                sel_strefa_index = 0
            default_A = float(dane_miasta["A"])
            disable_strefa = True

        strefa = st.selectbox("Strefa obciążenia wiatrem", options=["1", "2", "3"], index=sel_strefa_index, disabled=disable_strefa, key="ddp_strefa_w")
        if disable_strefa:
            st.caption(f"🔒 Strefa przypisana dla: {wybrane_miasto}")

        A = st.number_input("Wysokość nad poziomem morza $A$ [m]", value=default_A, step=10.0, format="%.1f", key="ddp_A_w")
        if use_city:
            st.caption("⚠️ Podano średnią wysokość dla miejscowości. Zweryfikuj dla konkretnej lokalizacji.")

        disp_vb0 = get_vb0_value(strefa, A)
        disp_qb0 = 0.5 * 1.25 * (disp_vb0**2) / 1000.0
        
        st.number_input("Wartość podstawowa $v_{b,0}$ [m/s]", value=disp_vb0, disabled=True, format="%.2f", key="disp_vb0")
        st.number_input("Wartość podstawowa $q_{b,0}$ [kN/m²]", value=disp_qb0, disabled=True, format="%.3f", key="disp_qb0")

    with col2:
        keys_terenu = list(TERRAIN_PARAMS.keys())
        kat_terenu = st.selectbox("Kategoria terenu", options=keys_terenu, index=2, key="ddp_kat_terenu")
        with st.expander("ℹ️ Pomoc - Kategoria terenu"):
            for k, v in TERRAIN_PARAMS.items():
                st.markdown(f"**Kat. {k}**: {v['opis']}")
        
        st.write("Czy uwzględnić inny współczynnik sezonowy niż zalecany?")
        use_cseason = st.radio("use_cseason_label", ["Nie", "Tak"], index=0, label_visibility="collapsed", horizontal=True, key="radio_c_season")
        dis_season = (use_cseason == "Nie")
        c_season_val = st.number_input("Współczynnik sezonowy $c_{season}$", value=1.0, step=0.01, format="%.2f", disabled=dis_season, key="num_c_season")

        st.write("Czy uwzględnić inny współczynnik kierunkowy niż zalecany?")
        use_cdir = st.radio("use_cdir_label", ["Nie", "Tak"], index=0, label_visibility="collapsed", horizontal=True, key="radio_c_dir")
        
        c_dir_val = 1.0
        if use_cdir == "Tak":
            st.write("Wybierz kierunek wiatru:")
            angle = st.selectbox("Kierunek [°]", options=[0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330], key="sel_angle")
            c_dir_calc = get_cdir_value_from_table(strefa, angle)
            st.number_input("Współczynnik kierunkowy $c_{dir}$", value=c_dir_calc, disabled=True, format="%.2f", key=f"cdir_val_{angle}_{strefa}")
            c_dir_val = c_dir_calc
        else:
            st.number_input("Współczynnik kierunkowy $c_{dir}$", value=1.0, disabled=True, format="%.2f", key="num_c_dir_dis")

    with col3:
        curr_b = st.session_state.get("ddp_b_bud", 20.0)
        curr_d = st.session_state.get("ddp_d_bud", 15.0)
        curr_z = st.session_state.get("ddp_z_bud", 10.0)
        
        show_user_line = False
        user_z_prev = None
        if st.session_state.get("ddp_inter_check", "Nie") == "Tak":
            show_user_line = True
            user_z_prev = st.session_state.get("ddp_z_user", curr_z/2)

        fig_geo = draw_geometry_schematic(curr_b, curr_d, curr_z, user_z_prev if show_user_line else None)
        st.pyplot(fig_geo, use_container_width=True)
        
        c3_1, c3_2, c3_3 = st.columns(3)
        with c3_1:
            b_bud = st.number_input("Szerokość $b$ [m]", value=20.0, step=1.0, key="ddp_b_bud", help="Wymiar ściany prostopadłej do kierunku wiatru (nawietrznej).")
        with c3_2:
            d_bud = st.number_input("Głębokość $d$ [m]", value=15.0, step=1.0, key="ddp_d_bud", help="Wymiar ściany równoległej do kierunku wiatru (bocznej).")
        with c3_3:
            z_bud = st.number_input("Wysokość $z$ [m]", value=10.0, step=0.5, key="ddp_z_bud", help="Całkowita wysokość budynku.")
            
        # Dodajemy pytanie o parcie wewnętrzne (ZGODNIE Z ŻYCZENIEM W KOLUMNIE 3 - WYŻEJ)
        # Przenosimy pytanie do label, aby tooltip działał poprawnie
        st.markdown("**Czy uwzględniać parcie wewnętrzne?**", help="Dla typowych budynków nie zaleca się rezygnowania z parcia wewnętrznego. Wyłącznie w przypadku hermetycznie szczelnych obiektów możliwe jest nie uwzględnianie parcia wewnętrznego.")
        include_cpi = st.radio(
            "include_cpi_label",
            ["Tak", "Nie"], 
            index=0, 
            horizontal=True,
            label_visibility="collapsed"
        )

        if include_cpi == "Tak":
            cp1, cp2 = st.columns(2)
            with cp1:
                st.number_input(r"$C_{pi}$ - nadciśnienie", value=0.2, disabled=True, key="disp_cpi_p")
            with cp2:
                st.number_input(r"$C_{pi}$ - podciśnienie", value=-0.3, disabled=True, key="disp_cpi_m")

        # Pytanie o wysokość NA SAMYM DOLE
        st.write("**Czy wyznaczyć ciśnienie wiatru na innej wysokości niż z?**")
        calc_inter = st.radio("calc_inter_label", ["Nie", "Tak"], index=0, label_visibility="collapsed", horizontal=True, key="ddp_inter_check")
        
        user_z_val = None
        if calc_inter == "Tak":
            user_z_val = st.number_input("Podaj wysokość $z_{user}$ [m]", value=min(5.0, z_bud), min_value=0.0, max_value=z_bud, step=0.5, key="ddp_z_user")

    b1, b2, b3 = st.columns([1, 2, 1])
    oblicz_clicked = False
    with b2:
        if st.button("OBLICZ", type="primary", use_container_width=True, key="ddp_btn_w"):
            oblicz_clicked = True

    if oblicz_clicked:
        vb0 = get_vb0_value(strefa, A)
        c_season = c_season_val if not dis_season else 1.0
        c_dir = c_dir_val
        vb = c_dir * c_season * vb0 
        
        heights, qp_vals, zmin_val = calc_wind_profile(z_bud, kat_terenu, vb)
        qp_top = qp_vals[-1]
        st.session_state["ddp_qp_max"] = qp_top
        
        qp_user_val = None
        if user_z_val is not None:
            qp_user_val = calc_single_qp(user_z_val, kat_terenu, vb)

        calc_qp = qp_user_val if qp_user_val is not None else qp_top
        calc_z = user_z_val if user_z_val is not None else z_bud
        
        # Pobieramy bazowe współczynniki Cpe
        cpe_data_base = get_cpe_full(z_bud, d_bud)
        
        # Modyfikacja Cpe o parcie wewnętrzne (najgorszy przypadek)
        final_cpe_data = {}
        
        for zone, (cpe10, cpe1) in cpe_data_base.items():
            if include_cpi == "Tak":
                # Logika: sumujemy wartości bezwzględne (najgorszy scenariusz)
                if cpe10 > 0: 
                    # Parcie zewn (>0) + ssanie wewn (-0.3) -> 0.8 - (-0.3) = 1.1
                    val_10 = cpe10 + 0.3
                    val_1 = cpe1 + 0.3
                else: 
                    # Ssanie zewn (<0) + parcie wewn (+0.2) -> -1.2 - 0.2 = -1.4
                    val_10 = cpe10 - 0.2
                    val_1 = cpe1 - 0.2
            else:
                val_10 = cpe10
                val_1 = cpe1
            
            final_cpe_data[zone] = (val_10, val_1)
        
        st.markdown("### WYNIKI")
        
        r1, r2 = st.columns(2)
        with r1:
            st.markdown("**Strefy i wymiary**")
            fig_geo = draw_wall_zones_geometry(b_bud, d_bud, z_bud)
            st.pyplot(fig_geo, use_container_width=True)
        with r2:
            st.markdown(f"**Wartości ciśnienia $w_e$ [kN/m²]** (dla $z={calc_z:.2f}$ m)")
            # Przekazujemy zmodyfikowane dane final_cpe_data
            fig_pres = draw_wall_pressures_only(b_bud, d_bud, z_bud, final_cpe_data, calc_qp)
            st.pyplot(fig_pres, use_container_width=True)
        
        res_col1, res_col2 = st.columns([0.5, 0.5])
        
        with res_col1:
            with st.expander("🧮 Profil pionowy wartości szczytowej ciśnienia prędkości $q_p(z)$"):
                fig_prof = plot_wind_pressure_profile(heights, qp_vals, z_bud, qp_top, zmin_val, user_z_val, qp_user_val)
                st.pyplot(fig_prof, use_container_width=True)
        
        with res_col2:
            with st.expander("🧮 Współczynniki $C_{pe}$ dla ścian"):
                
                st.markdown("#### Tablica 7.1 - Wartości $C_{pe,10}$")
                data_10 = {
                    "A": ["-1.2", "-1.2", "-1.2"],
                    "B": ["-0.8", "-0.8", "-0.8"],
                    "C": ["-0.5", "-0.5", "-0.5"],
                    "D": ["+0.8", "+0.8", "+0.7"],
                    "E": ["-0.7", "-0.5", "-0.3"]
                }
                df_10 = pd.DataFrame(data_10, index=["5", "1", "≤ 0.25"])
                df_10.index.name = "h/d"
                st.table(df_10)

                st.markdown("#### Tablica 7.1 - Wartości $C_{pe,1}$")
                data_1 = {
                    "A": ["-1.4", "-1.4", "-1.4"],
                    "B": ["-1.1", "-1.1", "-1.1"],
                    "C": ["-0.5", "-0.5", "-0.5"],
                    "D": ["+1.0", "+1.0", "+1.0"],
                    "E": ["-0.7", "-0.5", "-0.3"]
                }
                df_1 = pd.DataFrame(data_1, index=["5", "1", "≤ 0.25"])
                df_1.index.name = "h/d"
                st.table(df_1)
                
                # Dodana tabela z Cpi bez indeksu
                st.markdown("#### Wartości $C_{pi}$ (ciśnienie wewnętrzne)")
                st.caption("Dla budynków bez ściany dominującej (wg 7.2.9)")
                data_pi = {
                    "Wariant": ["Nadciśnienie", "Podciśnienie"],
                    "Wartość": ["+0.2", "-0.3"]
                }
                df_pi = pd.DataFrame(data_pi)
                # Ustawiamy 'Wariant' jako indeks, aby ukryć numerację 0,1
                df_pi.set_index("Wariant", inplace=True)
                st.table(df_pi)

        # -------------------------------------------------------------------------
        # SZCZEGÓŁOWY RAPORT OBLICZEŃ
        # -------------------------------------------------------------------------
        with st.expander("Szczegóły obliczeń"):
            
            # --- 1. GEOMETRIA ---
            st.markdown("#### 1. Geometria budynku")
            st.write(f"Wymiary: $b={b_bud}$ m, $d={d_bud}$ m, $h={z_bud}$ m")
            if user_z_val is not None:
                 st.write(f"Wysokość obliczeniowa $z_{{user}} = {user_z_val}$ m")
            st.write(f"Stosunek wymiarów $h/d = {z_bud/d_bud:.2f}$")
            e_val = min(b_bud, 2*z_bud)
            st.write(f"Wymiar odniesienia $e = \\min(b, 2h) = {e_val:.2f}$ m")

            # --- 2. DANE PODSTAWOWE ---
            st.markdown("#### 2. Prędkość podstawowa wiatru")
            st.latex(r"v_b = c_{dir} \cdot c_{season} \cdot v_{b,0}")
            st.write(f"Dla wybranej strefy **{strefa}** i wysokości n.p.m. **$A={A}$ m**:")
            st.write(f"- Wartość bazowa: $v_{{b,0}} = {vb0:.2f}$ m/s")
            st.write(f"- Współczynnik kierunkowy: $c_{{dir}} = {c_dir:.2f}$")
            st.write(f"- Współczynnik sezonowy: $c_{{season}} = {c_season:.2f}$")
            st.markdown(f"**Wynik:** $v_b = {c_dir:.2f} \cdot {c_season:.2f} \cdot {vb0:.2f} \\text{{ m/s}} = {vb:.2f}$ m/s")

            # --- 3. PARAMETRY TERENU ---
            st.markdown("#### 3. Parametry terenu i ekspozycji")
            params = TERRAIN_PARAMS[kat_terenu]
            z0 = params["z0"]
            zmin_t = params["zmin"]
            z0_II = 0.05
            kr = 0.19 * ((z0 / z0_II) ** 0.07)
            
            st.write(f"Kategoria terenu: **{kat_terenu}**")
            st.write(f"- $z_0 = {z0}$ m")
            st.write(f"- $z_{{min}} = {zmin_t}$ m")
            
            st.write("Współczynnik terenu $k_r$:")
            st.latex(r"k_r = 0.19 \cdot \left(\frac{z_0}{z_{0,II}}\right)^{0.07}")
            st.write(f"$k_r = 0.19 \cdot ({z0} \\text{{ m}}/{z0_II} \\text{{ m}})^{{0.07}} = {kr:.4f}$")

            # --- 4. CIŚNIENIE PRĘDKOŚCI ---
            st.markdown(f"#### 4. Wartość szczytowa ciśnienia prędkości $q_p(z)$")
            st.write(f"Obliczenia dla wysokości $z_e = {calc_z:.2f}$ m.")
            
            # Obliczenia pośrednie dla raportu
            z_calc = max(calc_z, zmin_t)
            cr = kr * math.log(z_calc / z0)
            co = 1.0 # Standardowo
            vm = cr * co * vb
            Iv = 1.0 / (co * math.log(z_calc / z0))
            rho = 1.25
            
            # Wyświetlanie kroków
            st.write("**a) Współczynnik chropowatości $c_r(z)$**")
            st.latex(r"c_r(z) = k_r \cdot \ln\left(\frac{z}{z_0}\right)")
            st.write(f"$c_r({calc_z}) = {kr:.4f} \cdot \ln({z_calc} \\text{{ m}}/{z0} \\text{{ m}}) = {cr:.4f}$")
            
            st.write("**b) Średnia prędkość wiatru $v_m(z)$**")
            st.latex(r"v_m(z) = c_r(z) \cdot c_o(z) \cdot v_b")
            st.write(f"$v_m({calc_z}) = {cr:.4f} \cdot {co} \cdot {vb:.2f} \\text{{ m/s}} = {vm:.2f}$ m/s")
            
            st.write("**c) Intensywność turbulencji $I_v(z)$**")
            st.latex(r"I_v(z) = \frac{k_I}{c_o(z) \cdot \ln(z/z_0)} \quad (k_I=1.0)")
            st.write(f"$I_v({calc_z}) = 1.0 / ({co} \cdot \ln({z_calc} \\text{{ m}}/{z0} \\text{{ m}})) = {Iv:.4f}$")
            
            st.write("**d) Wartość szczytowa ciśnienia $q_p(z)$**")
            st.latex(r"q_p(z) = \left[1 + 7 \cdot I_v(z)\right] \cdot \frac{1}{2} \cdot \rho \cdot v_m^2(z)")
            st.write(f"$q_p({calc_z}) = [1 + 7 \cdot {Iv:.4f}] \cdot 0.5 \cdot {rho} \\text{{ kg/m}}^3 \cdot ({vm:.2f} \\text{{ m/s}})^2$")
            st.markdown(f"**Wynik:** $q_p({calc_z}) = {calc_qp:.2f}$ kN/m²")

            # --- 5. CIŚNIENIE NETTO ---
            st.markdown("#### 5. Obciążenie wiatrem na powierzchnie")
            st.latex(r"w_{netto} = q_p(z) \cdot (C_{pe} - C_{pi})")
            st.write("Znak (+) oznacza parcie na ścianę, znak (-) oznacza ssanie (odrywanie).")
            st.write("Wartości $C_{pe}$ odczytano z Tablicy 7.1 normy PN-EN 1991-1-4.")
            
            if include_cpi == "Tak":
                st.write("Przyjęto wartości dla budynków bez ściany dominującej:")
                st.write(r"$C_{pi} = +0.2$ (nadciśnienie); $C_{pi} = -0.3$ (podciśnienie)")

                st.info("""
                **Zasada kombinacji:**
                Dla każdej strefy sprawdzono dwa warianty $C_{pi}$ i wybrano ten, który daje **większą co do modułu** wartość obciążenia (najbardziej niekorzystny).
                
                - Jeśli wiatr zewnętrzne prze ścianę ($C_{pe} > 0$), najgorzej jest, gdy wiatr wewnętrzne ją zasysa ($C_{pi} = -0.3$).
                - Jeśli wiatr zewnętrzne odrywa ścianę ($C_{pe} < 0$), najgorzej jest, gdy wiatr wewnętrzne ją wypycha ($C_{pi} = +0.2$).
                """)
            else:
                st.write("Pominięto parcie wewnętrzne ($C_{pi} = 0$) zgodnie z wyborem użytkownika.")
            
            # Wstawienie rysunku 40% (układ 3-4-3 daje ok. 40% w środku)
            c_left, c_center, c_right = st.columns([3, 4, 3])
            with c_center:
                st.pyplot(fig_pres, use_container_width=True)

            # Pętla po strefach do wyświetlenia obliczeń
            for zone in ["D", "E", "A", "B", "C"]:
                if zone not in cpe_data_base: continue
                
                cpe_val = cpe_data_base[zone][0]
                
                # Ustalenie użytego Cpi
                if include_cpi == "Tak":
                    if cpe_val > 0:
                        cpi_used = -0.3
                    else:
                        cpi_used = 0.2
                    c_netto = cpe_val - cpi_used
                else:
                    cpi_used = 0.0
                    c_netto = cpe_val
                
                w_final = calc_qp * c_netto
                
                st.markdown(f"**Strefa {zone}** ($C_{{pe,10}} = {cpe_val}$)")
                st.write(f"$$w_{{netto,{zone}}} = {calc_qp:.2f} \\text{{ kN/m}}^2 \cdot ({cpe_val} - ({cpi_used})) = {w_final:.2f} \\text{{ kN/m}}^2$$")

if __name__ == "__main__":
    run()