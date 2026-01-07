import streamlit as st
import math
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# --------------------------------------------------------------------------------------
# 1. FUNKCJE RYSUNKOWE
# --------------------------------------------------------------------------------------

def plot_barrier_technical(alpha, s_val, b_val, Fs_val):
    """
    Główny rysunek techniczny:
    - Śnieg dociągnięty do końca lewej połaci
    - Wymiar b NAD dachem (duża czcionka)
    - Siła Fs czerwona, pogrubiona
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    a_rad = math.radians(alpha)
    
    # 1. GEOMETRIA BAZOWA
    # H - wysokość kalenicy
    H = b_val * math.tan(a_rad) + 0.5
    rx, ry = 0, H
    
    # Prawa strona
    bx, by = b_val, H - b_val * math.tan(a_rad)
    ex, ey = bx + 1.2, by - 1.2 * math.tan(a_rad)
    
    # Lewa strona (druga połać)
    lx, ly = -1.5, H - 1.5 * math.tan(a_rad)
    
    # 2. DACH
    ax.plot([rx, ex], [ry, ey], color='black', linewidth=3.5, zorder=5) # Prawa połać
    ax.plot([lx, rx], [ly, ry], color='black', linewidth=3.5, zorder=5) # Lewa połać
    
    # 3. BARIERA
    bar_h = 0.55
    top_x = bx + bar_h * math.sin(a_rad)
    top_y = by + bar_h * math.cos(a_rad)
    ax.plot([bx, top_x], [by, top_y], color='black', linewidth=4.0, zorder=6)
    
    strut_offset = 0.5
    strut_base_x = bx + strut_offset * math.cos(a_rad)
    strut_base_y = by - strut_offset * math.sin(a_rad)
    ax.plot([strut_base_x, top_x], [strut_base_y, top_y], color='black', linewidth=1.5, zorder=5)
    
    # 4. ŚNIEG (Pełny zasięg na obu połaciach)
    snow_d = 0.45 
    snow_peak_y = H + snow_d / math.cos(a_rad)
    
    ls_top_x = lx - snow_d * math.sin(a_rad)
    ls_top_y = ly + snow_d * math.cos(a_rad)
    
    snow_points = [
        (lx, ly),         
        (rx, ry),         
        (bx, by),         
        (bx + snow_d*math.sin(a_rad), by + snow_d*math.cos(a_rad)), 
        (0, snow_peak_y), 
        (ls_top_x, ls_top_y) 
    ]
    
    snow_poly = patches.Polygon(snow_points, closed=True, 
                                facecolor='#e6f2ff', edgecolor='#1f77b4', linewidth=1.0, alpha=0.9, zorder=2)
    ax.add_patch(snow_poly)
    
    # 5. WYMIAROWANIE b (Powiększone)
    dim_y = ry + 0.8  
    ax.plot([rx, rx], [ry, dim_y], 'k--', linewidth=0.8, alpha=0.5) 
    ax.plot([bx, bx], [by, dim_y], 'k--', linewidth=0.8, alpha=0.5) 
    
    ax.annotate('', xy=(rx, dim_y), xytext=(bx, dim_y),
                arrowprops=dict(arrowstyle='<->', color='black', linewidth=1.2))
    
    ax.text((rx + bx)/2, dim_y + 0.1, f"$b = {b_val:.2f} \\; \\mathrm{{m}}$", 
            ha='center', fontsize=16)
    
    # 6. KĄT ALFA
    ax.plot([ex - 2.0, ex], [ey, ey], 'k-', linewidth=0.8, alpha=0.7)
    arc_rad = 1.0
    arc = patches.Arc((ex, ey), arc_rad*2, arc_rad*2, theta1=180-alpha, theta2=180, color='black', linewidth=1.5)
    ax.add_patch(arc)
    ax.text(ex - 1.4, ey - 0.25, f"$\\alpha = {alpha:.1f}^\\circ$", fontsize=16)
    
    # 7. SIŁA Fs
    force_len = 1.0
    fs_x = bx - force_len * math.cos(a_rad)
    fs_y = by + force_len * math.sin(a_rad) + 0.15
    ax.arrow(fs_x, fs_y, 0.7*force_len*math.cos(a_rad), -0.7*force_len*math.sin(a_rad), 
             head_width=0.12, head_length=0.15, fc='red', ec='red', linewidth=2.0, zorder=10)
    ax.text(fs_x, fs_y + 0.3, f"$\\mathbf{{F_s = {Fs_val:.2f} \\; kN/m}}$", color='red', fontsize=17)

    ax.set_aspect('equal')
    ax.axis('off')
    plt.tight_layout()
    return fig

def plot_b_schema_simple():
    """
    Uproszczony schemat do sekcji danych wejściowych (w expanderze).
    """
    fig, ax = plt.subplots(figsize=(5, 3))
    alpha = 30
    b_val = 5.0
    a_rad = math.radians(alpha)
    
    H = b_val * math.tan(a_rad) + 0.5
    rx, ry = 0, H
    bx, by = b_val, H - b_val * math.tan(a_rad)
    ex, ey = bx + 1.0, by - 1.0 * math.tan(a_rad)
    lx, ly = -1.0, H - 1.0 * math.tan(a_rad)
    
    # Dach
    ax.plot([rx, ex], [ry, ey], color='gray', linewidth=2.0)
    ax.plot([lx, rx], [ly, ry], color='gray', linewidth=2.0)
    
    # Bariera
    bar_h = 0.5
    top_x = bx + bar_h * math.sin(a_rad)
    top_y = by + bar_h * math.cos(a_rad)
    ax.plot([bx, top_x], [by, top_y], color='black', linewidth=3.0)
    
    # Wymiar b (czerwony)
    dim_y = ry + 0.4
    ax.plot([rx, rx], [ry, dim_y], 'r--', linewidth=0.8, alpha=0.6)
    ax.plot([bx, bx], [by, dim_y], 'r--', linewidth=0.8, alpha=0.6)
    ax.annotate('', xy=(rx, dim_y), xytext=(bx, dim_y),
                arrowprops=dict(arrowstyle='<->', color='red', linewidth=1.5))
    ax.text((rx + bx)/2, dim_y + 0.1, "$b$", ha='center', color='red', fontsize=14, fontweight='bold')
    
    ax.set_aspect('equal')
    ax.axis('off')
    plt.tight_layout()
    return fig

# --------------------------------------------------------------------------------------
# 2. APLIKACJA STREAMLIT
# --------------------------------------------------------------------------------------

def run():
    st.set_page_config(page_title="PLATFORMA - Bariery Przeciwśnieżne", layout="wide")

    st.markdown("""
        <style>
        button[kind="primary"] { background: #ff4b4b !important; border: none !important; border-radius: 12px !important; height: 52px !important; font-size: 17px !important; font-weight: 900 !important; letter-spacing: 0.5px !important; }
        .streamlit-expanderHeader { font-weight: bold; font-size: 1.0em; }
        .custom-info-box { 
            background-color: #e3f2fd; color: #0d47a1; padding: 15px; border-radius: 8px; border-left: 6px solid #1565c0; margin-top: 5px; margin-bottom: 25px; font-size: 15px;
        }
        div.stButton > button { width: 100%; }
        
        /* Styl dla ręcznej etykiety - idealne odwzorowanie standardowej etykiety Streamlit */
        .manual-label {
            font-size: 14px;
            font-family: "Source Sans Pro", sans-serif;
            color: rgb(49, 51, 63); /* Dokładny kolor etykiet systemowych */
            margin-bottom: 0px;
            height: auto;
            min-height: 1.5rem;
            vertical-align: middle;
            display: flex;
            align-items: center;
            margin-top: 5px; 
        }
        </style>
        """, unsafe_allow_html=True)

    # DANE WEJŚCIOWE
    st.markdown("### DANE WEJŚCIOWE")
    
    st.markdown("""
    <div class="custom-info-box">
        <b>💡 Wskazówka:</b><br>
        Wartość obciążenia śniegiem dachu <b>s</b> należy wyznaczyć w odpowiednim kalkulatorze dla danego typu dachu (jednopołaciowy, dwupołaciowy itp.), a następnie wpisać ją poniżej.
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    
    with col1:
        s_input = st.number_input("Obciążenie śniegiem dachu $s$ [kN/m²]", value=1.20, step=0.1, format="%.2f")
        
    with col2:
        alpha_input = st.number_input("Kąt nachylenia połaci $\\alpha$ [°]", value=30.0, step=1.0, min_value=0.0, max_value=85.0)
        
    with col3:      
        b_input = st.number_input("Rozstaw / Odległość b [m]", value=5.0, step=0.1, min_value=0.1, format="%.1f", key="b_input", help="Wymiar poziomy między barierami lub barierą, a kalenicą")
        st.pyplot(plot_b_schema_simple(), use_container_width=True)
           
   
    # OBLICZENIA
    a_rad = math.radians(alpha_input)
    sin_val = math.sin(a_rad)
    Fs_result = s_input * b_input * sin_val
           
    # PRZYCISK OBLICZ
    _, col_btn, _ = st.columns([1, 2, 1])
    with col_btn:
        calc_btn = st.button("OBLICZ", type="primary", use_container_width=True)

    if calc_btn:
        st.markdown('<div style="text-align: center; font-size: 24px; font-weight: bold; margin-bottom: 20px;">Obciążenie śniegiem bariery</div>', unsafe_allow_html=True)
        
        # WYNIKI - RYSUNEK GŁÓWNY (SZEROKI - 60%)
        # Układ [1, 3, 1] daje środkowi ok. 60%
        r1, r2, r3 = st.columns([1, 3, 1])
        with r2:
            st.pyplot(plot_barrier_technical(alpha_input, s_input, b_input, Fs_result))

        # SZCZEGÓŁY OBLICZEŃ
        with st.expander("Szczegóły obliczeń"):
            st.markdown("#### 1. Podstawowe dane")
            st.write(f"Obciążenie dachu: $s = {s_input:.2f}$ kN/m²")
            st.write(f"Kąt nachylenia połaci: $\\alpha = {alpha_input:.1f}^\\circ$")
            st.write(f"Szerokość zbierania (rzut poziomy): $b = {b_input:.2f}$ m")
            
            st.markdown("#### 2. Szczegółowe obliczenia")
            st.write("Siłę $F_s$ wywieraną przez masę śniegu zsuwającą się po dachu na barierę wyznacza się wg PN-EN 1991-1-3 pkt. 6.4.")
            
            # Rysunek w szczegółach - ZWĘŻONY (40%)
            # Układ [3, 4, 3] daje środkowi ok. 40% (zgodnie z plikiem o nawisach)
            sr1, sr2, sr3 = st.columns([3, 4, 3])
            with sr2:
                st.pyplot(plot_barrier_technical(alpha_input, s_input, b_input, Fs_result))
            
            # Wzór w jednej linii
            st.latex(r"F_s = s \cdot b \cdot \sin(\alpha) = " + 
                     f"{s_input:.2f} \, kN/m^2 \cdot {b_input:.2f} \, m \cdot \sin({alpha_input:.1f}^\circ) = " +
                     f"{s_input:.2f} \, kN/m^2 \cdot {b_input:.2f} \, m \cdot {sin_val:.3f} = " +
                     f"\\mathbf{{{Fs_result:.2f} \, kN/m}}")

if __name__ == "__main__":
    run()