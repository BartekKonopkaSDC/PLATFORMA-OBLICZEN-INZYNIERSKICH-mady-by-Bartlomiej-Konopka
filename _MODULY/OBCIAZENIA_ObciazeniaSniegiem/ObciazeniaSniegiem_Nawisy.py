import streamlit as st
import math
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.path as mpath
import numpy as np

# --------------------------------------------------------------------------------------
# 1. FUNKCJE RYSOWANIA
# --------------------------------------------------------------------------------------

def plot_overhang_schematic(alpha_val, se_val, d_val):
    """
    Rysuje schematyczny przekrój przez krawędź dachu z nawisem śnieżnym.
    Jednostki są POGRUBIONE.
    """
    fig, ax = plt.subplots(figsize=(7, 6))
    
    # Parametry geometryczne rysunku
    draw_angle_deg = 25
    a_rad = math.radians(draw_angle_deg)
    
    # Stała wysokość wizualna warstwy śniegu
    h_draw = 1.0 
    
    # Geometria
    eaves_overhang = 1.0 
    roof_len_back = 3.5 
    
    def get_roof_y(x):
        return -x * math.tan(a_rad)

    x_roof_start = -roof_len_back
    y_roof_start = get_roof_y(x_roof_start)
    x_eaves = eaves_overhang
    y_eaves = get_roof_y(x_eaves)
    
    # --- 1. KONSTRUKCJA (zorder=5) ---
    ax.plot([0, 0], [0, -3.5], color='black', linewidth=4.0, zorder=5)
    ax.plot([x_roof_start, x_eaves], [y_roof_start, y_eaves], color='black', linewidth=4.0, zorder=5)

    # --- 2. ŚNIEG (zorder=1 - TŁO) ---
    Path = mpath.Path
    
    p_top_left = (x_roof_start, y_roof_start + h_draw)
    p_btm_left = (x_roof_start, y_roof_start)
    p_eaves_edge = (x_eaves, y_eaves)
    p_snow_start_curve = (x_eaves, y_eaves + h_draw)
    
    path_data = [
        (Path.MOVETO, p_top_left),
        (Path.LINETO, p_snow_start_curve),
    ]
    
    # Nawis
    c1 = (x_eaves + 0.6, y_eaves + h_draw - 0.1)
    c2 = (x_eaves + 0.9, y_eaves - 0.6)
    p_tip = (x_eaves + 0.3, y_eaves - 1.5)
    
    path_data.append((Path.CURVE4, c1))
    path_data.append((Path.CURVE4, c2))
    path_data.append((Path.CURVE4, p_tip))
    
    c3 = (x_eaves + 0.1, y_eaves - 1.2)
    c4 = (x_eaves - 0.2, y_eaves - 0.2)
    
    path_data.append((Path.CURVE4, c3))
    path_data.append((Path.CURVE4, c4))
    path_data.append((Path.LINETO, p_eaves_edge))
    
    path_data.append((Path.LINETO, p_btm_left))
    path_data.append((Path.CLOSEPOLY, p_btm_left))
    
    codes, verts = zip(*path_data)
    path = Path(verts, codes)
    patch = patches.PathPatch(path, facecolor='#e6f2ff', edgecolor='#1f77b4', lw=1.5, alpha=0.9, zorder=1)
    ax.add_patch(patch)

    # --- 3. OZNACZENIA (zorder > 10) ---
    
    # A. Wektor siły Se
    arrow_x = x_eaves + 0.3
    arrow_y_start = y_eaves - 1.6
    arrow_len = 1.0
    
    ax.arrow(arrow_x, arrow_y_start, 0, -arrow_len, head_width=0.15, head_length=0.2, 
             fc='red', ec='red', linewidth=2.0, zorder=20)
    
    # Tekst s_e: CAŁOŚĆ pogrubiona (włącznie z jednostką)
    ax.text(arrow_x, arrow_y_start - arrow_len - 0.2, f"$\\mathbf{{s_e = {se_val:.2f} \\; kN/m}}$", 
            color='red', fontsize=14, ha='center', va='top', zorder=20)
    
    # B. Wymiar d (Pionowy)
    dim_x = x_eaves
    dim_y_roof = y_eaves
    dim_y_snow = y_eaves + h_draw
    
    ax.plot([dim_x, dim_x + 0.4], [dim_y_roof, dim_y_roof], 'k:', linewidth=0.5, zorder=10)
    ax.plot([dim_x, dim_x + 0.4], [dim_y_snow, dim_y_snow], 'k:', linewidth=0.5, zorder=10)
    
    dim_line_x = dim_x + 0.2
    ax.annotate('', xy=(dim_line_x, dim_y_roof), xytext=(dim_line_x, dim_y_snow), 
                arrowprops=dict(arrowstyle='<->', color='blue', linewidth=1.2), zorder=20)
    
    # Tekst d: CAŁOŚĆ pogrubiona (włącznie z jednostką)
    ax.text(dim_line_x + 0.1, (dim_y_roof + dim_y_snow)/2, f"$\\mathbf{{d={d_val:.2f} \\; m}}$", 
            color='blue', ha='left', va='center', fontsize=12,
            zorder=30, bbox=dict(facecolor='white', alpha=1.0, edgecolor='none', pad=1))

    # Ustawienia widoku
    ax.set_aspect('equal')
    ax.axis('off')
    
    ax.set_xlim(-4.0, 2.5)
    ax.set_ylim(-3.5, 3.0)
    
    plt.tight_layout()
    return fig

def run():
    if "nav_s" not in st.session_state: st.session_state["nav_s"] = 0.0

    st.markdown("""
        <style>
        button[kind="primary"] { background: #ff4b4b !important; border: none !important; border-radius: 12px !important; height: 52px !important; font-size: 17px !important; font-weight: 900 !important; letter-spacing: 0.5px !important; }
        button[kind="primary"]:hover { filter: brightness(0.95); }
        div.row-widget.stRadio > div { flex-direction: row; gap: 20px; }
        .stCaption { margin-top: -10px; margin-bottom: 10px; }
        .streamlit-expanderHeader { font-weight: bold; font-size: 1.1em; }
        
        .custom-info-box { 
            background-color: #e3f2fd; 
            color: #0d47a1; 
            padding: 15px; 
            border-radius: 8px; 
            border-left: 6px solid #1565c0; 
            margin-bottom: 20px;
            font-size: 16px;
        }
        
        .result-title {
            text-align: center;
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 20px;
            color: #31333F;
        }
        .result-value {
            text-align: center;
            font-size: 20px;
            color: #ff4b4b;
            font-weight: bold;
            margin-bottom: 20px;
        }
        </style>
        """, unsafe_allow_html=True)

    st.markdown("### DANE WEJŚCIOWE")
    
    st.markdown("""
    <div class="custom-info-box">
        <b>💡 Wskazówka:</b><br>
        Wartość obciążenia śniegiem dachu <b>s</b> należy wyznaczyć w odpowiednim kalkulatorze dla danego typu dachu (jednopołaciowy, dwupołaciowy itp.), a następnie wpisać ją poniżej.
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        s_input = st.number_input("Obciążenie śniegiem dachu $s$ [kN/m²]", value=1.60, step=0.1, min_value=0.0, format="%.2f", key="nav_s_input")
    
    with col2:
        alpha = st.number_input("Kąt nachylenia połaci przy okapie $\\alpha$ [°]", value=30.0, step=1.0, min_value=0.0, max_value=89.0, key="nav_alpha")
        
    with col3:
        gamma_input = st.number_input("Ciężar objętościowy śniegu $\\gamma$ [kN/m³]", value=3.0, step=0.1, min_value=0.1, format="%.1f", key="nav_gamma", help="Zalecane: 3.0 wg PN-EN 1991-1-3 p. 6.3(2)")

     
    # Przycisk wyśrodkowany
    b1, b2, b3 = st.columns([1, 2, 1])
    with b2:
        calc_btn = st.button("OBLICZ", type="primary", use_container_width=True, key="nav_btn")

    if calc_btn:
        # 2. Obliczenia
        gamma = gamma_input
        
        if s_input > 0:
            d = s_input / gamma 
            
            # Współczynnik k (norma p. 6.3 UWAGA)
            # k = 3/d, lecz k <= d
            if d > 0:
                k_calc = 3.0 / d
            else:
                k_calc = 0
            
            k_limit = d
            k_final = min(k_calc, k_limit)
            
            # Wzór 6.4
            se = (k_final * (s_input**2)) / gamma
        else:
            d = 0.0
            k_final = 0.0
            se = 0.0

        # --- SEKCJA WYNIKÓW ---
        st.markdown("### WYNIKI")
        st.markdown("**Obciążenie nawisu śnieżnego**")
               
        # Wyśrodkowany wykres (szerokość 40% -> układ 3-4-3)
        c1, c2, c3 = st.columns([3, 4, 3])
        with c2:
            st.pyplot(plot_overhang_schematic(alpha, se, d))

        with st.expander("Szczegóły obliczeń"):
            # 1. Podstawowe dane
            st.markdown("#### 1. Podstawowe dane")
            st.write(f"Ciężar objętościowy śniegu: $\\gamma = {gamma:.1f}$ kN/m³")
            st.write(f"Obciążenie dachu: $s = {s_input:.2f}$ kN/m²")
            st.write(f"Kąt nachylenia połaci: $\\alpha = {alpha:.1f}^\\circ$")

            # 2. Szczegółowe obliczenia
            st.markdown("#### 2. Szczegółowe obliczenia")
            
            st.markdown("**Grubość warstwy śniegu:**")
            st.latex(r"d = \frac{s}{\gamma} = \frac{" + f"{s_input:.2f} \\, \\text{{kN/m}}^2" + r"}{" + f"{gamma:.1f} \\, \\text{{kN/m}}^3" + r"} = " + f"{d:.3f} \\, \\text{{m}}")
            
            st.markdown("**Współczynnik kształtu nawisu $k$:**")
            st.markdown("Zgodnie z uwagą do p. 6.3 (wzór przybliżony):")
            st.latex(r"k = \min\left(\frac{3}{d}; \, d\right) = \min\left(\frac{3}{" + f"{d:.3f}" + r"}; \, " + f"{d:.3f}" + r"\right) = \min(" + f"{3/d if d>0 else 0:.3f}; {d:.3f}) = " + f"{k_final:.3f}")
            
            st.markdown("**Obciążenie liniowe krawędzi $s_e$:**")
            
            # Rysunek w szczegółach (40% szerokości) [3, 4, 3]
            sc1, sc2, sc3 = st.columns([3, 4, 3])
            with sc2:
                st.pyplot(plot_overhang_schematic(alpha, se, d))
                
            st.latex(r"s_e = \frac{k \cdot s^2}{\gamma} = \frac{" + f"{k_final:.3f} \\cdot ({s_input:.2f} \\, \\text{{kN/m}}^2)^2" + r"}{" + f"{gamma:.1f} \\, \\text{{kN/m}}^3" + r"} = \mathbf{" + f"{se:.2f}" + r"} \, \text{kN/m}")

if __name__ == "__main__":
    run()