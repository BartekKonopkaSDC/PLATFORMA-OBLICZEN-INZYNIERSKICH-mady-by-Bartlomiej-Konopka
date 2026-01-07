import streamlit as st
import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.path as mpath
import numpy as np

# ======================================================================================
# 0. KONFIGURACJA I BAZA
# ======================================================================================

def reset_calc():
    """Funkcja resetująca stan obliczeń przy zmianie danych wejściowych."""
    st.session_state["calc_triggered"] = False

BAZA_GRUNTOW_ZRODLO = {
    "Niespoiste": {
        "Piasek drobny (luźny) ID=0.3":       {"gamma": 17.0, "phi": 29.0, "OCR": 1.0},
        "Piasek drobny (śr. zag.) ID=0.5":    {"gamma": 18.0, "phi": 32.0, "OCR": 1.0},
        "Piasek drobny (zagęszcz.) ID=0.7":   {"gamma": 19.0, "phi": 35.0, "OCR": 1.0},
        
        "Piasek średni (luźny) ID=0.3":       {"gamma": 17.5, "phi": 31.0, "OCR": 1.0},
        "Piasek średni (śr. zag.) ID=0.5":    {"gamma": 18.5, "phi": 34.0, "OCR": 1.0},
        "Piasek średni (zagęszcz.) ID=0.7":   {"gamma": 19.5, "phi": 37.0, "OCR": 1.0},
        
        "Piasek gruby (luźny) ID=0.3":        {"gamma": 18.0, "phi": 32.0, "OCR": 1.0},
        "Piasek gruby (śr. zag.) ID=0.5":     {"gamma": 19.0, "phi": 36.0, "OCR": 1.0},
        "Piasek gruby (zagęszcz.) ID=0.7":    {"gamma": 20.0, "phi": 39.0, "OCR": 1.0},
        
        "Pospółka (śr. zag.) ID=0.5":         {"gamma": 19.5, "phi": 38.0, "OCR": 1.0},
        "Pospółka (zagęszcz.) ID=0.7":        {"gamma": 21.0, "phi": 41.0, "OCR": 1.0},
    },
    "Spoiste": {
        "Pył (miękkoplast.) IL=0.4":          {"gamma": 19.0, "phi": 18.0, "OCR": 1.0},
        "Pył (twardoplast.) IL=0.1":          {"gamma": 20.0, "phi": 23.0, "OCR": 1.0},
        
        "Glina piaszczysta (miękkopl.) IL=0.4": {"gamma": 19.5, "phi": 16.0, "OCR": 1.0},
        "Glina piaszczysta (twardopl.) IL=0.1": {"gamma": 21.0, "phi": 24.0, "OCR": 1.0},
        "Glina piaszczysta (półzwarta) IL=0.0": {"gamma": 22.0, "phi": 28.0, "OCR": 1.0},
        
        "Glina pylasta (miękkopl.) IL=0.4":   {"gamma": 19.0, "phi": 15.0, "OCR": 1.0},
        "Glina pylasta (twardopl.) IL=0.1":   {"gamma": 20.5, "phi": 21.0, "OCR": 1.0},
        
        "Ił (miękkoplast.) IL=0.4":           {"gamma": 19.0, "phi": 10.0, "OCR": 1.0},
        "Ił (twardoplast.) IL=0.1":           {"gamma": 20.0, "phi": 16.0, "OCR": 1.0},
        "Ił (półzwarty) IL=0.0":              {"gamma": 21.0, "phi": 20.0, "OCR": 1.0},
    }
}

LISTA_WYBORU = []
FLAT_DB = {}
for k, v in BAZA_GRUNTOW_ZRODLO["Niespoiste"].items():
    LISTA_WYBORU.append(k)
    FLAT_DB[k] = v
for k, v in BAZA_GRUNTOW_ZRODLO["Spoiste"].items():
    LISTA_WYBORU.append(k)
    FLAT_DB[k] = v

# --------------------------------------------------------------------------------------
# 1. FUNKCJE OBLICZENIOWE
# --------------------------------------------------------------------------------------

def calculate_k0(phi_deg, ocr):
    phi_rad = math.radians(phi_deg)
    k0 = (1.0 - math.sin(phi_rad)) * math.sqrt(ocr)
    return k0

def solve_layer_pressures(layers_data, q_surcharge, H_total, water_present, h_w_val):
    results = []
    z_water = H_total - h_w_val if water_present else 99999.0
    current_depth = 0.0
    sigma_v_accumulated = q_surcharge 

    for i, layer in enumerate(layers_data):
        h = layer['h']
        gamma = layer['gamma']
        phi = layer['phi']
        ocr = layer['ocr']
        name = layer['name']

        k0 = calculate_k0(phi, ocr)
        z_top = current_depth
        z_bot = current_depth + h
        
        def get_water_pressure(z):
            if z <= z_water: return 0.0
            return (z - z_water) * 10.0
        
        # A: Nad wodą
        if z_bot <= z_water:
            sigma_v_top = sigma_v_accumulated
            sigma_v_bot = sigma_v_accumulated + (gamma * h)
            
            e_tot_top = sigma_v_top * k0
            e_tot_bot = sigma_v_bot * k0
            
            results.append({
                "id": i + 1, "name": name, "gamma": gamma, "phi": phi, "ocr": ocr, "k0": k0,
                "z_top": z_top, "z_bot": z_bot,
                "sigma_v_top": sigma_v_top, "sigma_v_bot": sigma_v_bot,
                "u_top": 0.0, "u_bot": 0.0,
                "e0_top": e_tot_top, "e0_bot": e_tot_bot,
                "is_submerged": False
            })
            sigma_v_accumulated = sigma_v_bot
            
        # B: Pod wodą
        elif z_top >= z_water:
            gamma_eff = gamma - 10.0
            if gamma_eff < 0: gamma_eff = 0
            
            sigma_v_top = sigma_v_accumulated
            sigma_v_bot = sigma_v_accumulated + (gamma_eff * h)
            
            u_top = get_water_pressure(z_top)
            u_bot = get_water_pressure(z_bot)
            
            e_tot_top = (sigma_v_top * k0) + u_top
            e_tot_bot = (sigma_v_bot * k0) + u_bot
            
            results.append({
                "id": i + 1, "name": name, "gamma": gamma, "phi": phi, "ocr": ocr, "k0": k0,
                "z_top": z_top, "z_bot": z_bot,
                "sigma_v_top": sigma_v_top, "sigma_v_bot": sigma_v_bot,
                "u_top": u_top, "u_bot": u_bot,
                "e0_top": e_tot_top, "e0_bot": e_tot_bot,
                "is_submerged": True
            })
            sigma_v_accumulated = sigma_v_bot
            
        # C: Przecinana
        else:
            # 1. Sucha
            h1 = z_water - z_top
            sigma_v_mid = sigma_v_accumulated + (gamma * h1)
            
            results.append({
                "id": i + 1, "name": name + " (nad wodą)", "gamma": gamma, "phi": phi, "ocr": ocr, "k0": k0,
                "z_top": z_top, "z_bot": z_water,
                "sigma_v_top": sigma_v_accumulated, "sigma_v_bot": sigma_v_mid,
                "u_top": 0.0, "u_bot": 0.0,
                "e0_top": sigma_v_accumulated * k0, "e0_bot": sigma_v_mid * k0,
                "is_submerged": False
            })
            
            # 2. Mokra
            h2 = z_bot - z_water
            gamma_eff = gamma - 10.0
            if gamma_eff < 0: gamma_eff = 0
            sigma_v_bot = sigma_v_mid + (gamma_eff * h2)
            
            u_bot_end = get_water_pressure(z_bot)
            e_tot_mid = sigma_v_mid * k0
            e_tot_bot = (sigma_v_bot * k0) + u_bot_end
            
            results.append({
                "id": i + 1, "name": name + " (pod wodą)", "gamma": gamma, "phi": phi, "ocr": ocr, "k0": k0,
                "z_top": z_water, "z_bot": z_bot,
                "sigma_v_top": sigma_v_mid, "sigma_v_bot": sigma_v_bot,
                "u_top": 0.0, "u_bot": u_bot_end,
                "e0_top": e_tot_mid, "e0_bot": e_tot_bot,
                "is_submerged": True
            })
            sigma_v_accumulated = sigma_v_bot

        current_depth += h

    return results

# --------------------------------------------------------------------------------------
# 2. RYSUNEK
# --------------------------------------------------------------------------------------

def draw_geometry_and_pressure(H_input, q_input, water_present=False, h_w_input=0.0, results=None):
    x_build_left = -2.5
    x_wall_right = 0.0
    x_soil_right = 6.5  
    
    wall_thick = 0.4
    slab_foundation_h = 0.5
    slab_ceiling_h = 0.3
    wall_1st_h = 1.0 
    subsoil_depth_vis = 2.0 * slab_foundation_h 

    if results is None:
        # --- TRYB SCHEMATYCZNY ---
        H_viz = 2.0  
        q_viz_height = 0.5
        wall_thick_viz = 0.25
        slab_found_viz = 0.30
        slab_ceil_viz = 0.20
        wall_1st_viz = 0.8
        sub_viz = 2.0 * slab_found_viz
        base_h_fig = 5.0
        # SKALOWANIE 85%
        final_figsize = (6, base_h_fig * 0.85)
    else:
        # --- TRYB WYNIKOWY ---
        H_viz = H_input
        q_viz_height = 0.6
        wall_thick_viz = 0.4
        slab_found_viz = 0.5
        slab_ceil_viz = 0.3
        wall_1st_viz = 1.0
        sub_viz = subsoil_depth_vis
        base_h_fig = min(5 + (H_viz / 4.0), 8)
        final_figsize = (6, base_h_fig * 0.7)
    
    fig, ax = plt.subplots(figsize=final_figsize)
    
    lev_0 = 0.0              
    lev_slab_top = lev_0 - (0.5 * slab_ceil_viz)
    lev_slab_bot = lev_slab_top - slab_ceil_viz
    lev_found_bot = lev_0 - H_viz
    lev_found_top = lev_found_bot + slab_found_viz
    lev_wall_1st_top = lev_slab_top + wall_1st_viz
    lev_bottom_view = lev_found_bot - sub_viz
    concrete_color = '#e0e0e0'
    
    # Konstrukcja
    ax.add_patch(patches.Rectangle((x_build_left, lev_found_bot), abs(x_build_left), slab_found_viz, facecolor=concrete_color, edgecolor='none', zorder=10))
    ax.add_patch(patches.Rectangle((-wall_thick_viz, lev_found_top), wall_thick_viz, lev_wall_1st_top - lev_found_top, facecolor=concrete_color, edgecolor='none', zorder=10))
    ax.add_patch(patches.Rectangle((x_build_left, lev_slab_bot), abs(x_build_left) - wall_thick_viz + 0.02, slab_ceil_viz, facecolor=concrete_color, edgecolor='none', zorder=10))

    lw_concrete = 1.5
    ax.plot([0, 0], [lev_found_bot, lev_wall_1st_top], color='black', linewidth=lw_concrete, zorder=11)
    ax.plot([x_build_left, 0], [lev_found_bot, lev_found_bot], color='black', linewidth=lw_concrete, zorder=11)
    ax.plot([x_build_left, -wall_thick_viz], [lev_found_top, lev_found_top], color='black', linewidth=lw_concrete, zorder=11)
    ax.plot([x_build_left, x_build_left], [lev_found_bot, lev_found_top], color='black', linewidth=0.5, zorder=11) 
    
    ax.plot([-wall_thick_viz, -wall_thick_viz], [lev_found_top, lev_slab_bot], color='black', linewidth=lw_concrete, zorder=11)
    ax.plot([x_build_left, -wall_thick_viz], [lev_slab_bot, lev_slab_bot], color='black', linewidth=lw_concrete, zorder=11)
    ax.plot([x_build_left, -wall_thick_viz], [lev_slab_top, lev_slab_top], color='black', linewidth=lw_concrete, zorder=11)
    ax.plot([x_build_left, x_build_left], [lev_slab_bot, lev_slab_top], color='black', linewidth=0.5, zorder=11) 
    ax.plot([-wall_thick_viz, -wall_thick_viz], [lev_slab_top, lev_wall_1st_top], color='black', linewidth=lw_concrete, zorder=11)
    ax.plot([-wall_thick_viz, 0], [lev_wall_1st_top, lev_wall_1st_top], color='black', linewidth=0.5, zorder=11) 

    # Grunt
    soil_color_n = '#e8e8e8' 
    
    if results is None:
        h_part = H_viz / 3.0
        ax.add_patch(patches.Rectangle((0, lev_0 - h_part), x_soil_right, h_part, facecolor='#ffffff', edgecolor='none', zorder=0))
        ax.plot([0, x_soil_right], [lev_0 - h_part, lev_0 - h_part], color='#cccccc', linestyle='--', linewidth=0.8)
        ax.text(x_soil_right/2, lev_0 - h_part/2, "Warstwa 1", ha='center', va='center', color='#666', style='italic')

        ax.add_patch(patches.Rectangle((0, lev_0 - 2*h_part), x_soil_right, h_part, facecolor='#f4f4f4', edgecolor='none', zorder=0))
        ax.plot([0, x_soil_right], [lev_0 - 2*h_part, lev_0 - 2*h_part], color='#cccccc', linestyle='--', linewidth=0.8)
        ax.text(x_soil_right/2, lev_0 - 1.5*h_part, "Warstwa i", ha='center', va='center', color='#666', style='italic')

        y_start_n = lev_0 - 2*h_part
        h_n_visual = abs(lev_bottom_view - y_start_n)
        ax.add_patch(patches.Rectangle((0, lev_bottom_view), x_soil_right, h_n_visual, facecolor=soil_color_n, edgecolor='none', zorder=0))
        ax.add_patch(patches.Rectangle((x_build_left, lev_bottom_view), (0 - x_build_left), abs(lev_found_bot - lev_bottom_view), facecolor=soil_color_n, edgecolor='none', zorder=0))
        ax.text(x_soil_right/2, lev_found_bot + h_part/2, "Warstwa n", ha='center', va='center', color='#666', style='italic')

        if water_present:
            y_layer_i_bot = lev_0 - 2*h_part
            lev_water_viz = y_layer_i_bot + (h_part / 6.0)
            
            ax.plot([0, x_soil_right], [lev_water_viz, lev_water_viz], color='blue', linestyle='-.', linewidth=1.2, zorder=20)
            ax.text(x_soil_right - 0.2, lev_water_viz + 0.05, "Poziom zwierciadła wody", ha='right', va='bottom', fontsize=9, color='blue', style='italic')
            
            dim_x_w = 5.5
            ax.annotate('', xy=(dim_x_w, lev_water_viz), xytext=(dim_x_w, lev_found_bot), arrowprops=dict(arrowstyle='<->', color='blue', linewidth=1.2), zorder=25)
            ax.text(dim_x_w + 0.15, lev_found_bot + (lev_water_viz - lev_found_bot)/2, "$h_w$", rotation=90, ha='left', va='center', fontsize=11, fontweight='bold', color='blue', zorder=26)
            ax.plot([dim_x_w - 0.2, dim_x_w + 0.2], [lev_water_viz, lev_water_viz], color='blue', lw=0.5, zorder=20)
            ax.plot([dim_x_w - 0.2, dim_x_w + 0.2], [lev_found_bot, lev_found_bot], color='blue', lw=0.5, zorder=20)
            ax.plot([dim_x_w, 0], [lev_found_bot, lev_found_bot], color='blue', linewidth=0.8, linestyle=':', zorder=19)

    else:
        colors = ['#ffffff', '#fcfcfc']
        num_res = len(results)
        for i, res in enumerate(results):
            z_t = lev_0 - res['z_top']
            z_b = lev_0 - res['z_bot']
            is_last = (i == num_res - 1)
            
            if is_last:
                h_layer = abs(lev_bottom_view - z_t)
            else:
                h_layer = res['z_bot'] - res['z_top']
            
            ax.add_patch(patches.Rectangle((0, z_t - h_layer), x_soil_right, h_layer, facecolor=colors[i % 2], edgecolor='none', zorder=0))
            if not is_last:
                ax.plot([0, x_soil_right], [z_b, z_b], color='#cccccc', linestyle='-', linewidth=0.5)
            
            if is_last:
                 label_y = z_t - (abs(lev_found_bot - z_t))/2 
            else:
                 label_y = z_t - (res['z_bot'] - res['z_top'])/2
                 
            label_text = f"{res['name']}\n$\\gamma={res['gamma']}, \\phi={res['phi']}^\\circ$"
            ax.text(x_soil_right - 0.1, label_y, label_text, ha='right', va='center', fontsize=7, color='#555555', style='italic')
        
        ax.add_patch(patches.Rectangle((x_build_left, lev_bottom_view), (0 - x_build_left), abs(lev_found_bot - lev_bottom_view), facecolor='white', edgecolor='none', zorder=0))

        if water_present:
            lev_water_res = lev_found_bot + h_w_input
            ax.plot([0, x_soil_right], [lev_water_res, lev_water_res], color='blue', linestyle='-.', linewidth=1.2, zorder=20)

    ax.plot([0, x_soil_right], [lev_0, lev_0], color='black', linewidth=1.2, zorder=15)
    
    if results is None:
        dim_x = -3.0 
        custom_dash = (0, (1, 5)) 
        ax.plot([dim_x, 0], [lev_0, lev_0], color='black', linewidth=0.8, linestyle=custom_dash, zorder=50)
        ax.plot([dim_x, 0], [lev_found_bot, lev_found_bot], color='black', linewidth=0.8, linestyle=custom_dash, zorder=50)
        ax.annotate('', xy=(dim_x, lev_found_bot), xytext=(dim_x, lev_0), arrowprops=dict(arrowstyle='<->', color='black', linewidth=1.2), zorder=51)
        ax.text(dim_x - 0.15, lev_found_bot + H_viz/2, "H", rotation=90, ha='right', va='center', fontsize=12, fontweight='bold', zorder=52)

        q_width = x_soil_right 
        ax.add_patch(patches.Rectangle((0, lev_0), q_width, q_viz_height, facecolor='#1f77b4', alpha=0.15, edgecolor='#1f77b4', linestyle='--'))
        arr_top = lev_0 + q_viz_height * 0.8
        arr_bot = lev_0 + q_viz_height * 0.2
        arr_len = arr_top - arr_bot
        num_arrows = 6
        for x_ar in np.linspace(0.3, q_width - 0.3, num_arrows):
            ax.arrow(x_ar, arr_top, 0, -arr_len, head_width=0.12, head_length=0.12, color='#1f77b4', length_includes_head=True, zorder=20)
        ax.text(q_width/2, lev_0 + q_viz_height + 0.1, "q", ha='center', va='bottom', color='#1f77b4', fontweight='bold', fontsize=12)

    if results is not None:
        pressure_color = '#d62728' 
        max_e = max(r['e0_bot'] for r in results)
        fixed_plot_width = 2.5
        scale_x = fixed_plot_width / max_e if max_e > 0 else 1.0
        
        for res in results:
            z_t = lev_0 - res['z_top']
            z_b = lev_0 - res['z_bot']
            x_t = res['e0_top'] * scale_x
            x_b = res['e0_bot'] * scale_x
            
            ax.plot([x_t, x_b], [z_t, z_b], color=pressure_color, linewidth=2.5, zorder=25)
            ax.annotate('', xy=(0, z_t), xytext=(x_t, z_t), arrowprops=dict(arrowstyle='->', color=pressure_color, lw=1.0))
            ax.annotate('', xy=(0, z_b), xytext=(x_b, z_b), arrowprops=dict(arrowstyle='->', color=pressure_color, lw=1.0))
            
            if res['e0_top'] > 0.1:
                y_pos = z_t
                va_align = 'center'
                if abs(z_t - lev_0) < 0.1: va_align = 'center' 
                bbox_props = dict(boxstyle="square,pad=0.1", fc="white", ec="none", alpha=1.0)
                ax.text(x_t + 0.1, y_pos, f"{res['e0_top']:.2f} kPa", ha='left', va=va_align, fontsize=9, fontweight='bold', color=pressure_color, zorder=60, bbox=bbox_props)
            
            if res['e0_bot'] > 0.1:
                bbox_props = dict(boxstyle="square,pad=0.1", fc="white", ec="none", alpha=0.8)
                ax.text(x_b + 0.1, z_b, f"{res['e0_bot']:.2f} kPa", ha='left', va='center', fontsize=9, fontweight='bold', color=pressure_color, zorder=60, bbox=bbox_props)
            
            ax.plot([x_t, x_t], [z_t, z_b], color=pressure_color, linewidth=0)

        poly_points = [(0, lev_0)]
        for res in results:
            x_t = res['e0_top'] * scale_x
            x_b = res['e0_bot'] * scale_x
            z_t = lev_0 - res['z_top']
            z_b = lev_0 - res['z_bot']
            poly_points.append((x_t, z_t))
            poly_points.append((x_b, z_b))
        poly_points.append((0, lev_found_bot))
        ax.add_patch(patches.Polygon(poly_points, closed=True, facecolor=pressure_color, alpha=0.15, zorder=5))

    ax.set_xlim(-3.8, x_soil_right + 0.2)
    ax.set_ylim(lev_bottom_view, lev_wall_1st_top + 0.2)
    ax.axis('off')
    plt.tight_layout()
    return fig

# --------------------------------------------------------------------------------------
# 3. GŁÓWNA APLIKACJA
# --------------------------------------------------------------------------------------

def run():
    if "calc_triggered" not in st.session_state: st.session_state["calc_triggered"] = False

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
        div.row-widget.stRadio > div { flex-direction: row; gap: 10px; }
        .stCaption { margin-top: -5px; margin-bottom: 5px; font-size: 0.8em; }
        .streamlit-expanderHeader { font-weight: bold; font-size: 1.1em; }
        div[data-testid="column"] { padding: 0px 5px; }
        .block-container { padding-top: 1.5rem; padding-bottom: 1.5rem; }
        h3 { margin-top: 1rem !important; margin-bottom: 0.5rem !important; font-size: 1.2rem; }
        div[data-testid="stForm"] > div { margin-bottom: 0 !important; }
        div[data-testid="column"] > div > div > div > div > div { display: flex; align-items: center; height: 100%; }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div style="text-align:center; margin-top:0.4rem; margin-bottom:0rem;">
            <span style="font-size:36px; font-weight:800; letter-spacing:1px; color:#dddddd;">
                PARCIE SPOCZYNKOWE GRUNTU ŚCIANY BUDYNKU
            </span>
        </div>
        <div style="text-align:center; font-size:14px; color:#aaaaaa; margin-top:-12px; margin-bottom:1.5rem;">
            wg PN-EN 1997-1
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### DANE WEJŚCIOWE")
    col_inp1, col_inp2 = st.columns([1, 1])

    with col_inp2:
        H_total = st.number_input("Wysokość ściany $H$ [m]", value=3.0, step=0.1, min_value=0.5, format="%.2f", help="Wysokość od poziomu gruntu do spodu fundamentu.", on_change=reset_calc)
        q_surcharge = st.number_input("Obciążenie naziomu $q$ [kPa]", value=5.0, step=1.0, min_value=0.0, on_change=reset_calc)
        num_layers = st.number_input("Liczba warstw gruntu n [-]", value=1, min_value=1, max_value=5, step=1, on_change=reset_calc)
        
        water_option = st.radio("Czy poziom wody gruntowej znajduje się powyżej poziomu posadowienia?", ["Nie", "Tak"], index=0, horizontal=True, on_change=reset_calc)
        
        water_present = False
        h_w_val = 0.0
        
        if water_option == "Tak":
            water_present = True
            h_w_val = st.number_input("Wysokość słupa wody $h_w$ [m]", value=1.0, min_value=0.0, max_value=H_total, step=0.1, help="Wysokość zwierciadła wody mierzona od spodu fundamentu w górę.", on_change=reset_calc)
    
    with col_inp1:
        fig_schema = draw_geometry_and_pressure(H_total, q_surcharge, water_present=water_present, h_w_input=h_w_val, results=None)
        st.pyplot(fig_schema, use_container_width=False)

    st.markdown("### PARAMETRY GRUNTU")
    st.info("⚠️ Ważne: Parametry gruntów wybierane z 'Bazy' są wartościami orientacyjnymi (szacunkowymi) opartymi na literaturze technicznej.\nDo wyznaczenia dokładnych wartości parcia gruntu należy przyjąć parametry określone na podstawie badań geotechnicznych dla danej lokalizacji.")
    
    h0, h1, h2, h3, h4, h5, h6 = st.columns([0.6, 1.0, 2.5, 0.8, 0.8, 0.8, 0.8])
    h2.markdown("Nazwa Warstwy")
    h3.markdown("Grub. $h$ [m]", help="Miąższość (grubość) danej warstwy gruntu.")
    h4.markdown("$\\gamma$ [kN/m³]", help="Ciężar objętościowy gruntu.")
    h5.markdown("OCR [-]", help="Stopień przekonsolidowania gruntu (Overconsolidation Ratio). Dla gruntów normalnie skonsolidowanych OCR=1.")
    h6.markdown("$\\phi'$ [°]", help="Efektywny kąt tarcia wewnętrznego gruntu.")

    layers_data_input = []
    sum_h_prev = 0.0
    input_valid = True
    error_msg = ""
    error_type = "ok"

    for i in range(int(num_layers)):
        c0, c1, c2, c3, c4, c5, c6 = st.columns([0.6, 1.0, 2.5, 0.8, 0.8, 0.8, 0.8])
        c0.markdown(f"<div style='height: 40px; display: flex; align-items: center; justify-content: center;'><b>Warstwa {i+1}</b></div>", unsafe_allow_html=True)
        mode = c1.radio(f"src_{i}", ["Własne", "Z bazy"], key=f"mode_{i}", label_visibility="collapsed", horizontal=True, on_change=reset_calc)

        def_gamma, def_phi, def_ocr = 18.0, 30.0, 1.0
        final_name = f"Warstwa {i+1}"
        
        key_g = f"g_in_{i}"
        key_o = f"o_in_{i}"
        key_p = f"p_in_{i}"

        if mode == "Z bazy":
            sel_grunt = c2.selectbox(f"g_sel_{i}", LISTA_WYBORU, key=f"sel_{i}", label_visibility="collapsed", on_change=reset_calc)
            if sel_grunt:
                final_name = sel_grunt.split(" ID=")[0].split(" IL=")[0]
                params = FLAT_DB[sel_grunt]
                def_gamma = params["gamma"]
                def_phi = params["phi"]
                def_ocr = params["OCR"]
                st.session_state[key_g] = def_gamma
                st.session_state[key_o] = def_ocr
                st.session_state[key_p] = def_phi
        else:
            final_name = c2.text_input(f"name_{i}", value=f"Warstwa {i+1}", key=f"txt_{i}", label_visibility="collapsed", on_change=reset_calc)

        is_disabled = (mode == "Z bazy")
        is_last_layer = (i == int(num_layers) - 1)
        
        if not is_last_layer:
            h_def = 1.0
            h_val = c3.number_input(f"h_{i}", value=h_def, step=0.1, key=f"h_in_{i}", label_visibility="collapsed", on_change=reset_calc)
            sum_h_prev += h_val
        else:
            h_remaining = H_total - sum_h_prev
            key_h_last = f"h_in_{i}"
            st.session_state[key_h_last] = float(h_remaining)
            h_val = c3.number_input(f"h_{i}", value=float(h_remaining), disabled=True, key=key_h_last, label_visibility="collapsed", min_value=None, max_value=None)
            
            if h_remaining < -0.001:
                input_valid = False
                error_msg = f"Suma grubości warstw nadkładu ({sum_h_prev:.2f} m) przekracza wysokość ściany H ({H_total:.2f} m). Zmniejsz ilość warstw lub ich miąższość."
                error_type = "error"
            elif abs(h_remaining) <= 0.001:
                input_valid = False
                error_msg = "Suma miąższości warstw równa się wysokości ściany H. Ostatnia warstwa ma 0 m grubości. Zmniejsz ilość warstw lub ich miąższość."
                error_type = "warning"

        gam_val = c4.number_input(f"gam_{i}", value=def_gamma, step=0.5, disabled=is_disabled, key=key_g, label_visibility="collapsed", on_change=reset_calc)
        ocr_val = c5.number_input(f"ocr_{i}", value=def_ocr, step=0.1, disabled=is_disabled, key=key_o, label_visibility="collapsed", on_change=reset_calc)
        phi_val = c6.number_input(f"phi_{i}", value=def_phi, step=1.0, disabled=is_disabled, key=key_p, label_visibility="collapsed", on_change=reset_calc)

        layers_data_input.append({
            "h": h_val, "gamma": gam_val, "phi": phi_val, "ocr": ocr_val, "name": final_name
        })

    if not input_valid:
        if error_type == "error":
            st.error(f"⚠️ BŁĄD DANYCH: {error_msg}")
        else:
            st.warning(f"OSTRZEŻENIE: {error_msg}")

    b1, b2, b3 = st.columns([1, 2, 1])
    if b2.button("OBLICZ", type="primary", use_container_width=True, key="calc_btn"):
        st.session_state["calc_triggered"] = True

    if st.session_state["calc_triggered"]:
        if not input_valid: st.stop()
        
        st.markdown("### WYNIKI")
        
        results = solve_layer_pressures(layers_data_input, q_surcharge, H_total, water_present, h_w_val)
        
        c_left, c_mid, c_right = st.columns([1, 3, 1])
        with c_mid:
            fig_res = draw_geometry_and_pressure(H_total, q_surcharge, water_present=water_present, h_w_input=h_w_val, results=results)
            st.pyplot(fig_res, use_container_width=True)
            
        E0_sum = 0.0
        Moment_sum = 0.0
        for r in results:
            h_lay = r['z_bot'] - r['z_top']
            area = 0.5 * (r['e0_top'] + r['e0_bot']) * h_lay
            E0_sum += area
            y_cg = (h_lay/3) * ((2*r['e0_top'] + r['e0_bot']) / (r['e0_top'] + r['e0_bot'])) if (r['e0_top'] + r['e0_bot']) > 0 else 0
            arm = (H_total - r['z_bot']) + y_cg
            Moment_sum += area * arm
        
        st.info(f"**📊 WYNIKI ZBIORCZE (SIŁY WYPADKOWE):**\n\nCałkowita siła parcia $E_0 = {E0_sum:.2f}$ kN/mb &nbsp;&nbsp;|&nbsp;&nbsp; Moment wywracający $M_O = {Moment_sum:.2f}$ kNm/mb")

        st.markdown("<br>", unsafe_allow_html=True) 

        with st.expander("Szczegóły obliczeń", expanded=False):
            st.markdown("#### 1. PODSTAWOWE DANE")
            st.write(f"Wysokość ściany $H = {H_total:.2f}$ m")
            st.write(f"Obciążenie naziomu $q = {q_surcharge:.2f}$ kPa")
            st.write(f"Liczba warstw: {num_layers}")
            if water_present: st.write(f"Poziom wody gruntowej: $h_w = {h_w_val:.2f}$ m (od spodu fundamentu)")
            else: st.write("Woda gruntowa: brak")
            
            st.markdown("#### 2. SZCZEGÓŁOWE OBLICZENIA")
            
            c_r1, c_r2, c_r3 = st.columns([1, 2, 1])
            with c_r2: st.pyplot(fig_res, use_container_width=True)

            st.write("Dla każdej warstwy obliczono współczynnik parcia spoczynkowego $K_0$, naprężenia pionowe $\\sigma'_v$ oraz parcie $e_0$.")
            
            if water_present:
                st.write("W przypadku występowania wody gruntowej, uwzględniono wypór hydrostatyczny (zmniejszenie ciężaru obj. gruntu o ok. $10 \\, kN/m^3$) oraz dodano parcie wody $u$.")
                st.write("Parcie całkowite: dla warstwy nienawodnionej $e_{0} = \\sigma'_v \\cdot K_0$, dla warstwy nawodnionej $e_{tot} = (\\sigma'_v \\cdot K_0) + u$")
            else:
                st.write("Parcie spoczynkowe: $e_{0} = \\sigma'_v \\cdot K_0$")
            
            for r in results:
                st.markdown(f"**Warstwa {r['id']} – {r['name']}**")
                st.write(f"Głębokość: $z = {r['z_top']:.2f} \\div {r['z_bot']:.2f}$ m (miąższość $h = {r['z_bot']-r['z_top']:.2f}$ m)")
                st.latex(r"K_0 = (1 - \sin \phi') \cdot \sqrt{OCR} = (1 - \sin %.0f^\circ) \cdot \sqrt{%.1f} = %.3f" % (r['phi'], r['ocr'], r['k0']))
                
                st.write("**Naprężenia pionowe efektywne:**")
                if r['id'] == 1 and not "(pod wodą)" in r['name']:
                     st.latex(r"\sigma'_{v,top} = q = %.2f \, \text{kPa}" % (r['sigma_v_top']))
                else:
                     st.latex(r"\sigma'_{v,top} = \sigma'_{v,prev} = %.2f \, \text{kPa}" % (r['sigma_v_top']))
                
                h_layer_val = r['z_bot'] - r['z_top']
                
                if r['is_submerged']:
                    st.latex(r"\sigma'_{v,bot} = \sigma'_{v,top} + (\gamma - 10) \cdot h = %.2f + (%.1f - 10) \cdot %.2f = %.2f \, \text{kPa}" 
                             % (r['sigma_v_top'], r['gamma'], h_layer_val, r['sigma_v_bot']))
                else:
                    st.latex(r"\sigma'_{v,bot} = \sigma'_{v,top} + \gamma \cdot h = %.2f + %.1f \cdot %.2f = %.2f \, \text{kPa}" 
                             % (r['sigma_v_top'], r['gamma'], h_layer_val, r['sigma_v_bot']))
                
                if r['u_top'] > 0.001 or r['u_bot'] > 0.001:
                    st.write("**Parcie wody:**")
                    st.latex(r"u_{top} = %.2f \, \text{kPa}, \quad u_{bot} = %.2f \, \text{kPa}" % (r['u_top'], r['u_bot']))

                st.write("**Parcie spoczynkowe całkowite:**")
                
                e_earth_top = r['sigma_v_top'] * r['k0']
                e_earth_bot = r['sigma_v_bot'] * r['k0']
                
                if r['u_top'] > 0.001:
                    st.latex(r"e_{0,top} = (%.2f \, \text{kPa} \cdot %.3f) + %.2f \, \text{kPa} = %.2f \, \text{kPa} + %.2f \, \text{kPa} = %.2f \, \text{kPa}" 
                             % (r['sigma_v_top'], r['k0'], r['u_top'], e_earth_top, r['u_top'], r['e0_top']))
                else:
                    st.latex(r"e_{0,top} = %.2f \, \text{kPa} \cdot %.3f = %.2f \, \text{kPa}" 
                             % (r['sigma_v_top'], r['k0'], r['e0_top']))
                
                if r['u_bot'] > 0.001:
                    st.latex(r"e_{0,bot} = (%.2f \, \text{kPa} \cdot %.3f) + %.2f \, \text{kPa} = %.2f \, \text{kPa} + %.2f \, \text{kPa} = %.2f \, \text{kPa}" 
                             % (r['sigma_v_bot'], r['k0'], r['u_bot'], e_earth_bot, r['u_bot'], r['e0_bot']))
                else:
                    st.latex(r"e_{0,bot} = %.2f \, \text{kPa} \cdot %.3f = %.2f \, \text{kPa}" 
                             % (r['sigma_v_bot'], r['k0'], r['e0_bot']))
                st.divider()

if __name__ == "__main__":
    run()