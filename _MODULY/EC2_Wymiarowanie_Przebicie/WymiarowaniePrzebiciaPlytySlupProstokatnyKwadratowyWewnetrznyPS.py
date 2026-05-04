# ==============================================================================
# WymiarowaniePrzebiciaPlytySlupProstokatnyKwadratowyWewnetrznyPS.py
# FINAL PREMIUM VERSION v8
# - Profesjonalny, monochromatyczny rysunek (styl CAD)
# - Poprawione nazewnictwo dla dokładania pasm pośrednich
# ==============================================================================

import streamlit as st
import math

# ==============================================================================
# IMPORT TABLIC
# ==============================================================================
try:
    from TABLICE.ParametryBetonu import (
        list_concrete_classes,
        get_concrete_params,
    )

    from TABLICE.ParametryStali import (
        list_steel_grades,
        get_steel_params,
    )

except Exception as e:
    st.error(f"Błąd importu tablic materiałowych: {e}")
    st.stop()


# ==============================================================================
# FUNKCJE
# ==============================================================================
def bar_area_cm2(phi_mm):
    return math.pi * phi_mm**2 / 4 / 100.0

def area_per_meter_cm2(phi_mm, spacing_cm):
    if spacing_cm <= 0:
        return 0.0
    return bar_area_cm2(phi_mm) * (100 / spacing_cm)

def beta_from_moments(Ved_kN, b_cm, h_cm, Mx_kNm, My_kNm):
    if Ved_kN <= 0:
        return 1.15
    b_m = b_cm / 100
    h_m = h_cm / 100
    beta = (
        1.0
        + abs(Mx_kNm) / (Ved_kN * b_m)
        + abs(My_kNm) / (Ved_kN * h_m)
    )
    return max(beta, 1.15)


def normalize_angle_near(angle_rad, reference_rad):
    while angle_rad - reference_rad <= -math.pi:
        angle_rad += 2 * math.pi
    while angle_rad - reference_rad > math.pi:
        angle_rad -= 2 * math.pi
    return angle_rad


def opening_center_from_side(
    side,
    edge_gap_cm,
    offset_cm,
    hole_b_cm,
    hole_h_cm,
    col_b_cm,
    col_h_cm,
):
    if side == "Lewa":
        return (
            -(col_b_cm / 2 + edge_gap_cm + hole_b_cm / 2),
            offset_cm,
        )
    if side == "Prawa":
        return (
            col_b_cm / 2 + edge_gap_cm + hole_b_cm / 2,
            offset_cm,
        )
    if side == "Góra":
        return (
            offset_cm,
            col_h_cm / 2 + edge_gap_cm + hole_h_cm / 2,
        )
    return (
        offset_cm,
        -(col_h_cm / 2 + edge_gap_cm + hole_h_cm / 2),
    )


def rect_gap_distance_cm(rect1_w, rect1_h, rect2_cx, rect2_cy, rect2_w, rect2_h):
    dx = max(abs(rect2_cx) - (rect1_w + rect2_w) / 2.0, 0.0)
    dy = max(abs(rect2_cy) - (rect1_h + rect2_h) / 2.0, 0.0)
    return math.hypot(dx, dy)


def opening_sector_angles(x_cm, y_cm, hole_b_cm, hole_h_cm):
    ref_angle = math.atan2(y_cm, x_cm) if abs(x_cm) > 1e-9 or abs(y_cm) > 1e-9 else 0.0
    corners = [
        (x_cm - hole_b_cm / 2, y_cm - hole_h_cm / 2),
        (x_cm + hole_b_cm / 2, y_cm - hole_h_cm / 2),
        (x_cm + hole_b_cm / 2, y_cm + hole_h_cm / 2),
        (x_cm - hole_b_cm / 2, y_cm + hole_h_cm / 2),
    ]
    unwrapped = [
        normalize_angle_near(math.atan2(cy, cx), ref_angle)
        for cx, cy in corners
    ]
    return min(unwrapped), max(unwrapped), ref_angle


def sample_segment(p0, p1, target_step_cm):
    length = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    steps = max(1, int(math.ceil(length / target_step_cm)))
    return [
        (
            p0[0] + (p1[0] - p0[0]) * i / steps,
            p0[1] + (p1[1] - p0[1]) * i / steps,
        )
        for i in range(steps + 1)
    ]


def sample_arc(center, radius_cm, angle_start, angle_end, target_step_cm):
    arc_len = abs(angle_end - angle_start) * radius_cm
    steps = max(6, int(math.ceil(arc_len / target_step_cm)))
    return [
        (
            center[0] + radius_cm * math.cos(angle_start + (angle_end - angle_start) * i / steps),
            center[1] + radius_cm * math.sin(angle_start + (angle_end - angle_start) * i / steps),
        )
        for i in range(steps + 1)
    ]


def merge_point_sequences(sequences):
    merged = []
    for seq in sequences:
        for pt in seq:
            if not merged or math.hypot(pt[0] - merged[-1][0], pt[1] - merged[-1][1]) > 1e-9:
                merged.append(pt)
    return merged


def rounded_rectangle_points(width_cm, height_cm, radius_cm, target_step_cm=0.75):
    half_w = width_cm / 2.0
    half_h = height_cm / 2.0
    sequences = [
        sample_segment((-half_w, -half_h - radius_cm), (half_w, -half_h - radius_cm), target_step_cm),
        sample_arc((half_w, -half_h), radius_cm, -math.pi / 2, 0.0, target_step_cm),
        sample_segment((half_w + radius_cm, -half_h), (half_w + radius_cm, half_h), target_step_cm),
        sample_arc((half_w, half_h), radius_cm, 0.0, math.pi / 2, target_step_cm),
        sample_segment((half_w, half_h + radius_cm), (-half_w, half_h + radius_cm), target_step_cm),
        sample_arc((-half_w, half_h), radius_cm, math.pi / 2, math.pi, target_step_cm),
        sample_segment((-half_w - radius_cm, half_h), (-half_w - radius_cm, -half_h), target_step_cm),
        sample_arc((-half_w, -half_h), radius_cm, math.pi, 3 * math.pi / 2, target_step_cm),
    ]
    return merge_point_sequences(sequences)


def rectangle_perimeter_points(width_cm, height_cm, target_step_cm=0.75):
    half_w = width_cm / 2.0
    half_h = height_cm / 2.0
    sequences = [
        sample_segment((-half_w, -half_h), (half_w, -half_h), target_step_cm),
        sample_segment((half_w, -half_h), (half_w, half_h), target_step_cm),
        sample_segment((half_w, half_h), (-half_w, half_h), target_step_cm),
        sample_segment((-half_w, half_h), (-half_w, -half_h), target_step_cm),
    ]
    return merge_point_sequences(sequences)


def split_perimeter_lengths(points, angle_min, angle_max, angle_ref):
    total_len = 0.0
    excluded_len = 0.0
    if len(points) < 2:
        return total_len, excluded_len

    for i, p1 in enumerate(points):
        p2 = points[(i + 1) % len(points)]
        seg_len = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
        if seg_len <= 1e-9:
            continue
        total_len += seg_len
        mid_x = 0.5 * (p1[0] + p2[0])
        mid_y = 0.5 * (p1[1] + p2[1])
        mid_angle = normalize_angle_near(math.atan2(mid_y, mid_x), angle_ref)
        if angle_min <= mid_angle <= angle_max:
            excluded_len += seg_len

    return total_len, excluded_len


def points_on_effective_rectangle(width_cm, height_cm, count, angle_min=None, angle_max=None, angle_ref=0.0):
    perimeter_points = rectangle_perimeter_points(width_cm, height_cm, target_step_cm=0.35)
    kept = []
    for pt in perimeter_points:
        if angle_min is not None and angle_max is not None:
            angle = normalize_angle_near(math.atan2(pt[1], pt[0]), angle_ref)
            if angle_min <= angle <= angle_max:
                continue
        kept.append(pt)

    if not kept:
        return []

    if count <= 1:
        return [kept[0]]

    if len(kept) <= count:
        return kept

    last_index = len(kept) - 1
    return [
        kept[int(round(i * last_index / (count - 1)))]
        for i in range(count)
    ]


# ==============================================================================
# MAIN
# ==============================================================================
def run():

    st.markdown("""
    <style>
    div[role="radiogroup"] > label{
        display:inline-flex !important;
        margin-right:0.9rem;
    }
    </style>
    """, unsafe_allow_html=True)

    # ==========================================================================
    # DANE WEJŚCIOWE
    # ==========================================================================
    st.markdown("### DANE WEJŚCIOWE")

    # --------------------------------------------------------------------------
    # ROW 1
    # --------------------------------------------------------------------------
    c1, c2, c3 = st.columns(3)

    with c1:
        Ved = st.number_input(
            "Siła przebijająca $V_{Ed}$ [kN]",
            value=400,
            step=50,
            key="ved_ps_wew"
        )

    with c2:
        b = st.number_input(
            "Wymiar słupa $b$ [cm]",
            value=40,
            step=1,
            key="b_ps_wew"
        )

    with c3:
        h_col = st.number_input(
            "Wymiar słupa $h$ [cm]",
            value=40,
            step=1,
            key="h_col_ps_wew"
        )

    # --------------------------------------------------------------------------
    # ROW 2
    # --------------------------------------------------------------------------
    c1, c2, c3 = st.columns(3)

    with c1:
        h_p = st.number_input(
            "Grubość płyty $h_p$ [cm]",
            value=22,
            step=1,
            key="hp_ps_wew"
        )

    with c2:
        concrete = st.selectbox(
            "Klasa betonu",
            list_concrete_classes(),
            index=4,
            key="conc_ps_wew"
        )

    with c3:
        steel = st.selectbox(
            "Klasa stali",
            list_steel_grades(),
            index=1,
            key="steel_ps_wew"
        )

    # --------------------------------------------------------------------------
    # ROW 3
    # --------------------------------------------------------------------------
    phi_list =[8,10,12,14,16,18,20,22,25,28,32]

    c1, c2, c3 = st.columns(3)

    with c1:
        phi_x = st.selectbox(
            "Średnica zbrojenia głównego $\\phi_x$ [mm]",
            phi_list,
            index=4,
            key="phix_ps_wew"
        )

    with c2:
        phi_y = st.selectbox(
            "Średnica zbrojenia drugorzędnego $\\phi_y$ [mm]",
            phi_list,
            index=4,
            key="phiy_ps_wew"
        )

    with c3:
        cnom = st.number_input(
            "Otulina $c_{nom}$ [mm]",
            value=30,
            step=5,
            key="cnom_ps_wew"
        )

    # --------------------------------------------------------------------------
    # ROW 4
    # --------------------------------------------------------------------------
    c1, c2, c3 = st.columns(3)

    with c1:
        beta_mode = st.radio(
            "Współczynnik $\\beta$ uwzględniający mimośród obciążenia",["Auto", "Wylicz", "Ręcznie"],
            horizontal=True,
            key="beta_mode_ps_wew"
        )

    if beta_mode == "Auto":
        beta = 1.15
        with c2:
            st.text_input(
                "Wartość współczynnika $\\beta$",
                value=f"{beta:.2f}",
                disabled=True,
                key="beta_auto_ps_wew"
            )

    elif beta_mode == "Wylicz":
        
        help_m = """
        **Zasada działania momentów:**
        
        Program interpretuje momenty zgodnie ze wzorem normowym: 
        $\\beta = 1 + \\frac{|M_x|}{V_{Ed} \\cdot b} + \\frac{|M_y|}{V_{Ed} \\cdot h_{col}}$

        * **$M_x$** - działa wokół osi Y i wywołuje mimośród wzdłuż wymiaru **b** słupa. Im większy jest wymiar $b$, tym większe ramię dla pary sił wewnętrznych, co zmniejsza negatywny wpływ tego momentu na naprężenia.
        * **$M_y$** - działa wokół osi X i wywołuje mimośród wzdłuż wymiaru **h** słupa. Podobnie, większy wymiar $h$ skuteczniej redukuje wpływ momentu $M_y$.
        """

        with c2:
            Mx = st.number_input(
                "$M_x$[kNm]",
                value=10,
                step=10,
                help=help_m,
                key="mx_ps_wew"
            )
        with c3:
            My = st.number_input(
                "$M_y$ [kNm]",
                value=10,
                step=10,
                help=help_m,
                key="my_ps_wew"
            )
        beta = beta_from_moments(Ved, b, h_col, Mx, My)

    else:
        with c2:
            beta = st.number_input(
                "Wartość współczynnika $\\beta$",
                value=1.15,
                step=0.01,
                format="%.2f",
                key="beta_manual_ps_wew"
            )

    # --------------------------------------------------------------------------
    # ROW 5
    # --------------------------------------------------------------------------
    c1, c2, c3 = st.columns(3)

    with c1:
        mode = st.radio(
            "Sposób podania zbrojenia płyty",
            ["Rozstaw prętów", "Pole powierzchni"],
            horizontal=True,
            key="mode_ps_wew"
        )

    if mode == "Rozstaw prętów":
        with c2:
            sx = st.number_input("Rozstaw $s_x$ [cm]", value=20, key="sx_ps_wew")
            Asx = area_per_meter_cm2(phi_x, sx)
        with c3:
            sy = st.number_input("Rozstaw $s_y$ [cm]", value=20, key="sy_ps_wew")
            Asy = area_per_meter_cm2(phi_y, sy)
    else:
        with c2:
            Asx = st.number_input("$A_{sx}$ [cm²/m]", value=10.0, key="asx_ps_wew")
        with c3:
            Asy = st.number_input("$A_{sy}$[cm²/m]", value=10.0, key="asy_ps_wew")

    # --------------------------------------------------------------------------
    # ROW 6
    # --------------------------------------------------------------------------
    c1, c2, c3 = st.columns(3)

    with c1:
        opening_enabled = st.checkbox(
            "Uwzględnij otwór prostokątny",
            value=False,
            key="opening_enabled_ps_wew"
        )

    opening_mode = "Prosty"
    hole_b = 0.0
    hole_h = 0.0
    opening_side = "Prawa"
    opening_edge_gap = 0.0
    opening_offset = 0.0
    hole_x = 0.0
    hole_y = 0.0

    if opening_enabled:
        with c2:
            hole_b = st.number_input(
                "Szerokość otworu $b_{otw}$ [cm]",
                min_value=1.0,
                value=30.0,
                step=1.0,
                key="hole_b_ps_wew"
            )
        with c3:
            hole_h = st.number_input(
                "Wysokość otworu $h_{otw}$ [cm]",
                min_value=1.0,
                value=20.0,
                step=1.0,
                key="hole_h_ps_wew"
            )

        c1, c2, c3 = st.columns(3)
        with c1:
            opening_mode = st.radio(
                "Lokalizacja otworu",
                ["Prosty", "Współrzędne"],
                horizontal=True,
                key="opening_mode_ps_wew"
            )

        if opening_mode == "Prosty":
            with c2:
                opening_side = st.selectbox(
                    "Położenie względem słupa",
                    ["Lewa", "Prawa", "Góra", "Dół"],
                    index=1,
                    key="opening_side_ps_wew"
                )
            with c3:
                opening_edge_gap = st.number_input(
                    "Odległość od lica słupa [cm]",
                    min_value=0.0,
                    value=20.0,
                    step=1.0,
                    key="opening_gap_ps_wew"
                )

            c1, c2, c3 = st.columns(3)
            with c1:
                opening_offset = st.number_input(
                    "Przesunięcie wzdłuż boku [cm]",
                    value=0.0,
                    step=1.0,
                    key="opening_offset_ps_wew"
                )
            hole_x, hole_y = opening_center_from_side(
                opening_side,
                opening_edge_gap,
                opening_offset,
                hole_b,
                hole_h,
                b,
                h_col,
            )
            with c2:
                st.number_input(
                    "x środka otworu [cm]",
                    value=float(f"{hole_x:.1f}"),
                    disabled=True,
                    key="hole_x_preview_ps_wew"
                )
            with c3:
                st.number_input(
                    "y środka otworu [cm]",
                    value=float(f"{hole_y:.1f}"),
                    disabled=True,
                    key="hole_y_preview_ps_wew"
                )
        else:
            with c2:
                hole_x = st.number_input(
                    "$x_{otw}$ środka [cm]",
                    value=50.0,
                    step=1.0,
                    key="hole_x_ps_wew"
                )
            with c3:
                hole_y = st.number_input(
                    "$y_{otw}$ środka [cm]",
                    value=0.0,
                    step=1.0,
                    key="hole_y_ps_wew"
                )

    # --------------------------------------------------------------------------
    # ROW 7
    # --------------------------------------------------------------------------
    c1, c2, c3 = st.columns(3)

    with c1:
        punch_type = st.radio(
            "Typ zbrojenia na przebicie",["Pręty zbrojeniowe", "Dyble trzpieniowe"],
            horizontal=True,
            key="punch_type_ps_wew"
        )

    with c2:
        sc2_1, sc2_2 = st.columns(2)
        with sc2_1:
            phi_sw = st.selectbox(
                "Średnica $\\phi$ [mm]",[8,10,12,14,16,20,25,28,32],
                index=2,
                key="phisw_ps_wew"
            )
        with sc2_2:
            if punch_type == "Pręty zbrojeniowe":
                punch_steel = st.selectbox(
                    "Klasa stali",
                    list_steel_grades(),
                    index=1,
                    key="punch_steel_ps_wew"
                )
                fywk = get_steel_params(punch_steel).fyk
            else:
                fywk = st.number_input(
                    "$f_{ywk}$ [MPa]",
                    value=500,
                    step=10,
                    help="Charakterystyczna granica plastyczności stali dybli trzpieniowych na przebicie.",
                    key="fywk_ps_wew"
                )

    with c3:
        rozmieszczenie_typ = st.radio(
            "Układ elementów na obwodach",["Stała ilość / obwód", "Minimalna ilość / obwód"],
            horizontal=True,
            help="Zgodnie z PN-EN 1992-1-1 rozstaw elementów na obwodzie (St) nie może przekraczać 1.5d oraz 2d. Ponieważ obwody rosną, konieczne staje się wkładanie dodatkowych 'krótszych' pasm promieniowych na dalszych obwodach. Opcja pierwsza stosuje rygor z obwodu zewnętrznego do samych okolic słupa (zużywa więcej stali).",
            key="rozm_typ_ps_wew"
        )

    # --------------------------------------------------------------------------
    # BUTTON
    # --------------------------------------------------------------------------
    _, cbtn, _ = st.columns([1,2,1])

    calc = cbtn.button(
        "OBLICZ",
        type="primary",
        use_container_width=True,
        key="btn_calc_ps_wew"
    )

    # ==========================================================================
    # OBLICZENIA
    # ==========================================================================
    if calc:

        fck = get_concrete_params(concrete).fck

        dx = h_p - cnom/10 - phi_x/20
        dy = h_p - cnom/10 - phi_y/20
        d = (dx + dy) / 2

        rho_x = Asx / (100 * dx)
        rho_y = Asy / (100 * dy)
        rho_l = min(math.sqrt(rho_x * rho_y), 0.02)

        k = min(1 + math.sqrt(200 / (d * 10)), 2.0)
        CRdc = 0.18 / 1.5

        u0 = 2 * (b + h_col)
        u1 = 2 * (b + h_col) + 4 * math.pi * d
        u1_eff = u1
        u1_excluded = 0.0
        opening_distance = 0.0
        opening_affects = False
        opening_reason = "Brak otworu."
        opening_angle_min = 0.0
        opening_angle_max = 0.0
        opening_angle_ref = 0.0
        opening_reduction_pct = 0.0

        if opening_enabled:
            opening_distance = rect_gap_distance_cm(b, h_col, hole_x, hole_y, hole_b, hole_h)
            opening_reason = f"Otwór w odległości {opening_distance:.1f} cm od lica słupa."
            if opening_distance < 6.0 * d:
                opening_angle_min, opening_angle_max, opening_angle_ref = opening_sector_angles(
                    hole_x, hole_y, hole_b, hole_h
                )
                u1_points = rounded_rectangle_points(b, h_col, 2.0 * d, target_step_cm=0.40)
                u1_total_geom, u1_excluded = split_perimeter_lengths(
                    u1_points,
                    opening_angle_min,
                    opening_angle_max,
                    opening_angle_ref,
                )
                if u1_total_geom > 1e-9 and u1_excluded > 1e-9:
                    opening_affects = True
                    u1_eff = max(u1 * (1.0 - u1_excluded / u1_total_geom), 0.15 * u1)
                    opening_reduction_pct = 100.0 * (u1 - u1_eff) / u1
                    opening_reason = (
                        f"Otwór leży w strefie 6d i redukuje obwód kontrolny u1 o {u1 - u1_eff:.2f} cm."
                    )
                else:
                    opening_reason = "Otwór jest blisko słupa, ale nie przecina sektora obwodu kontrolnego."
            else:
                opening_reason = f"Otwór jest poza strefą wpływu 6d ({opening_distance:.1f} cm >= {6.0 * d:.1f} cm)."

        vEd_u0 = beta * Ved * 1000 / (u0 * d * 100)
        vEd = beta * Ved * 1000 / (u1_eff * d * 100)

        vRdc = CRdc * k * ((100 * rho_l * fck) ** (1/3))

        nu = 0.6 * (1 - fck / 250)
        fcd = fck / 1.5
        vRdmax = 0.5 * nu * fcd

        need_reinf = vEd > vRdc

        fywd = fywk / 1.15
        one_bar = bar_area_cm2(phi_sw)

        # ======================================================================
        # WYNIKI
        # ======================================================================
        st.markdown(
            """
            <style>
            .results-title {
                display: flex;
                align-items: baseline;
                justify-content: space-between;
                gap: 12px;
                margin: 6px 0 16px 0;
                padding-bottom: 10px;
                border-bottom: 1px solid #2f3440;
            }
            .results-title h3 {
                margin: 0;
                color: #f8fafc;
                font-size: 1.35rem;
                font-weight: 750;
            }
            .results-title span {
                color: #94a3b8;
                font-size: 0.9rem;
            }
            .result-section-header {
                font-size: 1.0rem;
                font-weight: 700;
                color: #e5e7eb;
                margin-top: 22px;
                margin-bottom: 10px;
                letter-spacing: 0.03em;
                text-transform: uppercase;
            }
            .check-card, .metric-box {
                background-color: #1f242d;
                padding: 14px;
                border-radius: 8px;
                border: 1px solid #3f4653;
                min-height: 126px;
            }
            .check-top {
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 10px;
                margin-bottom: 10px;
            }
            .check-symbol {
                font-size: 1.15rem;
                font-weight: 800;
            }
            .check-title {
                font-size: 0.82rem;
                color: #cbd5e1;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.04em;
            }
            .status-pill {
                border-radius: 999px;
                padding: 4px 9px;
                font-size: 0.74rem;
                font-weight: 750;
                white-space: nowrap;
            }
            .status-ok { color: #dcfce7; background: rgba(34,197,94,0.16); border: 1px solid rgba(34,197,94,0.45); }
            .status-warn { color: #fef3c7; background: rgba(245,158,11,0.16); border: 1px solid rgba(245,158,11,0.45); }
            .status-fail { color: #fee2e2; background: rgba(239,68,68,0.16); border: 1px solid rgba(239,68,68,0.45); }
            .formula-line {
                color: #f8fafc;
                font-size: 1.22rem;
                font-weight: 760;
                line-height: 1.45;
            }
            .formula-line small {
                color: #94a3b8;
                font-size: 0.82rem;
                font-weight: 500;
            }
            .decision-band {
                margin-top: 12px;
                padding: 12px 14px;
                border-radius: 8px;
                font-weight: 700;
            }
            .decision-ok { background: rgba(34,197,94,0.14); border-left: 4px solid #22c55e; color: #dcfce7; }
            .decision-warn { background: rgba(245,158,11,0.14); border-left: 4px solid #f59e0b; color: #fef3c7; }
            .decision-fail { background: rgba(239,68,68,0.14); border-left: 4px solid #ef4444; color: #fee2e2; }
            .res-label {
                font-size: 0.78rem;
                color: #9ca3af;
                text-transform: uppercase;
                margin-bottom: 4px;
                letter-spacing: 0.02em;
                font-weight: 700;
            }
            .res-val {
                font-size: 1.15rem;
                font-weight: 760;
                color: #ffffff;
                line-height: 1.35;
            }
            .res-unit {
                font-size: 0.9rem;
                color: #9ca3af;
                font-weight: 400;
            }
            .layout-note {
                color: #9ca3af;
                font-size: 0.9rem;
                margin-top: 6px;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="results-title">
                <h3>WYNIKI OBLICZEŃ</h3>
                <span>PN-EN 1992-1-1 / przebicie płyty przy słupie wewnętrznym</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        basic_ok = vEd <= vRdc
        max_ok = vEd_u0 <= vRdmax

        # ----------------------------------------------------------------------
        # KONTROLE NORMOWE
        # ----------------------------------------------------------------------
        st.markdown(
            '<div class="result-section-header">KONTROLE NOŚNOŚCI WG PN-EN 1992-1-1</div>',
            unsafe_allow_html=True,
        )

        c_res1, c_res2 = st.columns(2)

        basic_color = "#22c55e" if basic_ok else "#f59e0b"
        basic_symbol = "✓" if basic_ok else "!"
        basic_status = "SPEŁNIONY" if basic_ok else "ZBROJENIE WYMAGANE"
        basic_status_class = "status-ok" if basic_ok else "status-warn"
        max_color = "#22c55e" if max_ok else "#ef4444"
        max_symbol = "✓" if max_ok else "×"
        max_status = "SPEŁNIONY" if max_ok else "NIESPEŁNIONY"
        max_status_class = "status-ok" if max_ok else "status-fail"

        with c_res1:
            st.markdown(
                f"""
                <div class="check-card" style="border-left: 4px solid {basic_color};">
                    <div class="check-top">
                        <div>
                            <div class="check-symbol" style="color:{basic_color};">{basic_symbol}</div>
                            <div class="check-title">Nośność betonu na obwodzie u<sub>1</sub></div>
                        </div>
                        <div class="status-pill {basic_status_class}">{basic_status}</div>
                    </div>
                    <div class="formula-line">
                        v<sub>Ed,u1</sub> = {vEd:.3f} <small>MPa</small><br>
                        v<sub>Rd,c</sub> = {vRdc:.3f} <small>MPa</small>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with c_res2:
            st.markdown(
                f"""
                <div class="check-card" style="border-left: 4px solid {max_color};">
                    <div class="check-top">
                        <div>
                            <div class="check-symbol" style="color:{max_color};">{max_symbol}</div>
                            <div class="check-title">Maksymalna nośność przy słupie u<sub>0</sub></div>
                        </div>
                        <div class="status-pill {max_status_class}">{max_status}</div>
                    </div>
                    <div class="formula-line">
                        v<sub>Ed,0</sub> = {vEd_u0:.3f} <small>MPa</small><br>
                        v<sub>Rd,max</sub> = {vRdmax:.3f} <small>MPa</small>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if basic_ok and max_ok:
            st.markdown('<div class="decision-band decision-ok">Wniosek: Zbrojenie na przebicie nie jest wymagane.</div>', unsafe_allow_html=True)
        elif not max_ok:
            st.markdown(
                '<div class="decision-band decision-fail">Wniosek: Przekroczono maksymalną nośność przy słupie. Zmień geometrię, beton lub obciążenie przed doborem zbrojenia.</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown('<div class="decision-band decision-warn">Wniosek: Wymagane jest zbrojenie na przebicie.</div>', unsafe_allow_html=True)

        if opening_enabled:
            opening_color = "#f59e0b" if opening_affects else "#22c55e"
            opening_status = "WPŁYWA" if opening_affects else "BEZ WPŁYWU"
            st.markdown(
                f"""
                <div class="metric-box" style="border-left: 3px solid {opening_color}; margin-top: 14px;">
                    <div class="res-label">OTWÓR PROSTOKĄTNY</div>
                    <div class="res-val">
                        {opening_status}: {hole_b:.1f} × {hole_h:.1f} cm
                    </div>
                    <div class="layout-note">
                        Środek otworu: x = {hole_x:.1f} cm, y = {hole_y:.1f} cm. {opening_reason}
                    </div>
                    <div class="layout-note">
                        u<sub>1,eff</sub> = {u1_eff:.2f} cm
                        {"(" + f"-{opening_reduction_pct:.1f}% względem u1" + ")" if opening_affects else ""}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # ----------------------------------------------------------------------
        # ROZMIESZCZENIE ZBROJENIA NA PRZEBICIE
        # ----------------------------------------------------------------------
        # Deklaracja zmiennych zbrojenia dla scope "Szczegółów Obliczeń"
        n_layers = 0
        x_out = 0.0
        uout = 0.0
        radial_spacing = 0.0
        fywd_eff = 0.0
        Asw_req_perimeter = 0.0
        Asw_prov_perimeter_min = 0.0
        Asw_prov_perimeter_max = 0.0
        n_total_layout = 0
        Asw_prov_total = 0.0
        layer_counts = []
        layer_offsets = []

        if need_reinf and max_ok:
            st.markdown(
                '<div class="result-section-header">DOBÓR I ROZMIESZCZENIE ZBROJENIA NA PRZEBICIE</div>',
                unsafe_allow_html=True,
            )

            k_out = 1.50
            first_layer_a = 0.50 * d
            radial_spacing_max = 0.75 * d
            tangential_spacing_inner_max = 1.50 * d
            tangential_spacing_outer_max = 2.00 * d
            uout = beta * Ved * 1000 / (vRdc * d * 100)
            x_out = max((uout - 2 * (b + h_col)) / (2 * math.pi), 2 * d)

            if x_out < 3 * d:
                first_layer_a = 0.30 * d
                last_required_a = 1.50 * d
            else:
                last_required_a = max(first_layer_a + radial_spacing_max, x_out - k_out * d)

            def round_up_to_multiple(value, multiple):
                return int(math.ceil(value / multiple) * multiple)

            radial_spacing = radial_spacing_max
            n_layers_from_zone = math.ceil((last_required_a - first_layer_a) / radial_spacing) + 1
            n_layers = max(2, n_layers_from_zone)
            layer_offsets =[
                first_layer_a + i * radial_spacing
                for i in range(n_layers)
            ]

            d_mm = d * 10
            u1_mm = u1 * 10
            sr_design_mm = radial_spacing * 10
            fywd_eff = min(250 + 0.25 * d_mm, fywd)

            Asw_req_perimeter = max(
                (vEd - 0.75 * vRdc)
                * (u1_eff * 10.0)
                * d_mm
                / (1.5 * (d_mm / sr_design_mm) * fywd_eff),
                0,
            ) / 100

            required_counts =[]
            layer_effective_lengths = []
            layer_reduction_ratios = []
            for a_i in layer_offsets:
                u_i = 2 * (b + h_col) + 2 * math.pi * a_i
                reduction_ratio = 1.0
                if opening_affects:
                    ring_points = rectangle_perimeter_points(b + 2 * a_i, h_col + 2 * a_i, target_step_cm=0.40)
                    ring_total_geom, ring_excluded = split_perimeter_lengths(
                        ring_points,
                        opening_angle_min,
                        opening_angle_max,
                        opening_angle_ref,
                    )
                    if ring_total_geom > 1e-9:
                        reduction_ratio = max(1.0 - ring_excluded / ring_total_geom, 0.15)
                u_i_eff = u_i * reduction_ratio
                layer_effective_lengths.append(u_i_eff)
                layer_reduction_ratios.append(reduction_ratio)
                st_limit = (
                    tangential_spacing_inner_max
                    if a_i <= 2 * d
                    else tangential_spacing_outer_max
                )
                n_i_spacing = max(4, math.ceil(u_i_eff / st_limit))
                n_i_strength = max(4, math.ceil(Asw_req_perimeter / one_bar))
                required_counts.append(max(n_i_spacing, n_i_strength))

            # --- DECYZJA O SPOSOBIE ALOKACJI PRĘTÓW ---
            if rozmieszczenie_typ == "Stała ilość / obwód":
                n_per_layer = round_up_to_multiple(max(required_counts), 4)
                layer_counts =[n_per_layer for _ in layer_offsets]
            else:
                layer_counts =[round_up_to_multiple(req, 4) for req in required_counts]
            
            n_total_layout = sum(layer_counts)
            Asw_prov_perimeter_min = min(layer_counts) * one_bar
            Asw_prov_perimeter_max = max(layer_counts) * one_bar
            
            Asw_prov_total = n_total_layout * one_bar
            Asw_req = Asw_req_perimeter

            c_asw1, c_asw2, c_asw3 = st.columns(3)

            with c_asw1:
                st.markdown(
                    f"""
                    <div class="metric-box" style="border-left: 3px solid #f59e0b;">
                        <div class="res-label">A<sub>sw,req</sub> NA OBWÓD</div>
                        <div class="res-val">
                            A<sub>sw,req</sub> = {Asw_req:.2f} <span class="res-unit">cm²</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with c_asw2:
                prov_str = f"{Asw_prov_perimeter_min:.2f}" if Asw_prov_perimeter_min == Asw_prov_perimeter_max else f"{Asw_prov_perimeter_min:.2f} - {Asw_prov_perimeter_max:.2f}"
                st.markdown(
                    f"""
                    <div class="metric-box" style="border-left: 3px solid #22c55e;">
                        <div class="res-label">A<sub>sw,prov</sub> NA OBWÓD</div>
                        <div class="res-val">
                            A<sub>sw,prov</sub> = {prov_str} <span class="res-unit">cm²</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with c_asw3:
                element_label = "dybli trzpieniowych" if punch_type == "Dyble trzpieniowe" else "prętów"
                
                if punch_type == "Dyble trzpieniowe":
                    if min(layer_counts) == max(layer_counts):
                        rozm_str = f"{layer_counts[0]} szt. × {n_layers} obw. Ø{phi_sw}"
                    else:
                        rozm_str = f"od {min(layer_counts)} do {max(layer_counts)} szt. × {n_layers} obw. Ø{phi_sw}"
                else:
                    if min(layer_counts) == max(layer_counts):
                        rozm_str = f"{n_layers} obw. × {layer_counts[0]} szt. Ø{phi_sw}"
                    else:
                        rozm_str = f"{n_layers} obw. (od {min(layer_counts)} do {max(layer_counts)} szt.) Ø{phi_sw}"

                st.markdown(
                    f"""
                    <div class="metric-box">
                        <div class="res-label">ROZMIESZCZENIE</div>
                        <div class="res-val">
                            {rozm_str}
                        </div>
                        <div class="layout-note">Razem: {n_total_layout} szt. {element_label}, A<sub>sw,total</sub> = {Asw_prov_total:.2f} cm²</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            st.markdown(
                '<div class="result-section-header">ROZMIESZCZENIE PRĘTÓW NA PRZEBICIE</div>',
                unsafe_allow_html=True,
            )

            layout_rows =[]
            min_area_warnings =[]
            for i, (a_i, n_i, u_i_eff, reduction_ratio_i) in enumerate(
                zip(layer_offsets, layer_counts, layer_effective_lengths, layer_reduction_ratios),
                start=1
            ):
                st_i = u_i_eff / n_i
                st_limit = (
                    tangential_spacing_inner_max
                    if a_i <= 2 * d
                    else tangential_spacing_outer_max
                )
                sr_i_mm = sr_design_mm
                st_i_mm = st_i * 10
                one_bar_min_cm2 = (
                    0.08 * math.sqrt(fck) * sr_i_mm * st_i_mm / (1.5 * fywk)
                ) / 100
                if one_bar < one_bar_min_cm2:
                    min_area_warnings.append((i, one_bar_min_cm2))
                
                layout_rows.append({
                    "Obwód": f"{i}",
                    "a od lica słupa [cm]": round(a_i, 1),
                    "a/d [-]": round(a_i / d, 2),
                    "Liczba elementów[szt.]": n_i,
                    "Asw,prov [cm²]": round(n_i * one_bar, 2),
                    "u_eff [cm]": round(u_i_eff, 1),
                    "sₜ po obwodzie [cm]": round(st_i, 1),
                    "Limit sₜ [cm]": round(st_limit, 1),
                    "Redukcja obwodu [%]": round((1.0 - reduction_ratio_i) * 100, 1),
                })

            st.dataframe(layout_rows, use_container_width=True, hide_index=True)

            # Schemat poglądowy: inżynierski rysunek obwodów kontrolnych i zbrojenia (CAD Style)
            if not max_ok:
                st.info("Schemat rozmieszczenia niedostępny — najpierw spełnij warunek maksymalnej nośności przy słupie (v_Ed,0 ≤ v_Rd,max).")
            else:
                try:
                    import matplotlib.pyplot as plt
                    from matplotlib.patches import Rectangle, FancyBboxPatch

                    fig, ax = plt.subplots(figsize=(8.0, 6.5))
                    ax.axis('off') 

                    # Rysowanie słupa (szare kreskowanie)
                    ax.add_patch(Rectangle((-b/2, -h_col/2), b, h_col, facecolor="#e2e8f0", edgecolor="#0f172a", linewidth=1.5, hatch="///", zorder=4))
                    col_label = f"SŁUP\n{b:.0f}×{h_col:.0f} cm"
                    label_fontsize = max(5, min(8, int(min(b, h_col) / 6)))
                    ax.text(0, 0, col_label, color="#0f172a", ha="center", va="center", fontsize=label_fontsize, fontweight="bold", zorder=5, clip_on=True)

                    # Obwód kontrolny u1 
                    u1_patch = FancyBboxPatch((-b/2, -h_col/2), b, h_col, boxstyle=f"round,pad={2*d},rounding_size={2*d}", fill=False, edgecolor="#3b82f6", linewidth=1.2, linestyle="--", zorder=2)
                    ax.add_patch(u1_patch)
                    ax.text(b/2 + 2*d + 3, 0, "u₁", color="#1d4ed8", fontsize=11, fontweight="bold", va="center")

                    # Obwód zewnętrzny u_out
                    uout_patch = FancyBboxPatch((-b/2, -h_col/2), b, h_col, boxstyle=f"round,pad={x_out},rounding_size={x_out}", fill=False, edgecolor="#10b981", linewidth=1.2, linestyle=":", zorder=1)
                    ax.add_patch(uout_patch)
                    ax.text(b/2 + x_out + 3, 0, "uₒᵤₜ", color="#047857", fontsize=11, fontweight="bold", va="center")

                    if opening_enabled:
                        ax.add_patch(
                            Rectangle(
                                (hole_x - hole_b / 2, hole_y - hole_h / 2),
                                hole_b,
                                hole_h,
                                facecolor="#ffffff",
                                edgecolor="#dc2626",
                                linewidth=1.4,
                                linestyle="-",
                                zorder=4,
                            )
                        )
                        ax.text(
                            hole_x,
                            hole_y,
                            "OTWÓR",
                            color="#991b1b",
                            ha="center",
                            va="center",
                            fontsize=8,
                            fontweight="bold",
                            zorder=5,
                        )
                        if opening_affects:
                            ray_len = max(
                                x_out,
                                layer_offsets[-1] if layer_offsets else 0.0,
                                math.hypot(hole_x, hole_y),
                                2 * d,
                            ) + max(b, h_col, hole_b, hole_h)
                            for ang in (opening_angle_min, opening_angle_max):
                                ax.plot(
                                    [0.0, ray_len * math.cos(ang)],
                                    [0.0, ray_len * math.sin(ang)],
                                    color="#dc2626",
                                    linewidth=1.0,
                                    linestyle="-.",
                                    zorder=1,
                                )

                    def draw_dim(x1, y1, x2, y2, text, color="#334155", offset_text=2.5, text_rot=0):
                        ax.annotate('', xy=(x1, y1), xytext=(x2, y2), arrowprops=dict(arrowstyle='<->', color=color, lw=1.0))
                        cx, cy = (x1+x2)/2, (y1+y2)/2
                        if x1 == x2: # Pionowy
                            ax.text(cx - offset_text, cy, text, ha='right', va='center', fontsize=9, color=color, rotation=90)
                        else:        # Poziomy
                            ax.text(cx, cy + offset_text, text, ha='center', va='bottom', fontsize=9, color=color, rotation=text_rot)

                    draw_dim(b/2, -h_col/4 - 3, b/2 + 2*d, -h_col/4 - 3, f"2d = {2*d:.1f} cm", color="#1d4ed8", offset_text=2)
                    draw_dim(b/2, h_col/4 + 3, b/2 + x_out, h_col/4 + 3, f"xₒᵤₜ = {x_out:.1f} cm", color="#047857", offset_text=2)

                    # Punkty zbrojenia (wszystkie czarne/ciemne na jasnoszarych obwodach)
                    for idx, (a_i, n_i) in enumerate(zip(layer_offsets, layer_counts), start=1):
                        ring_w = b + 2 * a_i
                        ring_h = h_col + 2 * a_i
                    
                        # Linia obwodu zbrojenia (cienka, jasnoszara)
                        ax.add_patch(Rectangle((-ring_w / 2, -ring_h / 2), ring_w, ring_h, fill=False, edgecolor="#94a3b8", linewidth=0.8, linestyle="-", zorder=2))
                    
                        # Punkty prętów/dybli (jednolite, ciemne CAD)
                        pts = points_on_effective_rectangle(
                            ring_w,
                            ring_h,
                            n_i,
                            opening_angle_min if opening_affects else None,
                            opening_angle_max if opening_affects else None,
                            opening_angle_ref,
                        )
                        ax.scatter([p[0] for p in pts], [p[1] for p in pts], s=25, color="#1e293b", edgecolor="#ffffff", linewidth=0.5, zorder=3)

                    # Opisy skrajnych obwodów
                    ax.text(b/2 + layer_offsets[0], -h_col/2 - 4, "1. obw.", color="#475569", fontsize=8, fontweight="bold", ha="center")
                    ax.text(b/2 + layer_offsets[-1], -h_col/2 - 4, f"{n_layers}. obw.", color="#475569", fontsize=8, fontweight="bold", ha="center")

                    max_a = max(
                        x_out,
                        layer_offsets[-1],
                        2 * d,
                        abs(hole_x) + hole_b / 2 if opening_enabled else 0.0,
                        abs(hole_y) + hole_h / 2 if opening_enabled else 0.0,
                    )
                    lim_x = b / 2 + max_a + 25
                    lim_y = h_col / 2 + max_a + 25
                    ax.set_xlim(-lim_x, lim_x)
                    ax.set_ylim(-lim_y, lim_y)
                    ax.set_aspect("equal", adjustable="box")
                    fig.tight_layout()
                    st.pyplot(fig, use_container_width=True)
                except Exception as e:
                    st.info(f"Nie udało się wyświetlić schematu rozmieszczenia: {e}")
    
            if min_area_warnings:
                failed = ", ".join(str(row[0]) for row in min_area_warnings)
                st.warning(
                    f"Średnica Ø{phi_sw} może nie spełniać minimalnego pola pojedynczego "
                    f"elementu wg 9.4.3 / równania 9.11 dla obwodów: {failed}. "
                    "Zwiększ średnicę albo zagęść elementy."
                )

        elif basic_ok and max_ok:
            st.info("Zbrojenie na przebicie nie jest wymagane.")

        # ----------------------------------------------------------------------
        # SZCZEGÓŁY OBLICZEŃ
        # ----------------------------------------------------------------------
        with st.expander("🔍 Szczegóły obliczeń"):
            st.markdown("#### 2.1 Wysokość użyteczna przekroju")
            st.latex(rf"d_x = h_p - c_{{nom}} - \frac{{\phi_x}}{{2}} = {h_p:.1f} \, \text{{cm}} - {cnom/10:.1f} \, \text{{cm}} - \frac{{{phi_x/10:.1f}}}{{2}} \, \text{{cm}} = {dx:.2f} \, \text{{cm}}")
            st.latex(rf"d_y = h_p - c_{{nom}} - \frac{{\phi_y}}{{2}} = {h_p:.1f} \, \text{{cm}} - {cnom/10:.1f} \, \text{{cm}} - \frac{{{phi_y/10:.1f}}}{{2}} \, \text{{cm}} = {dy:.2f} \, \text{{cm}}")
            st.latex(rf"d = \frac{{d_x + d_y}}{{2}} = \frac{{{dx:.2f} \, \text{{cm}} + {dy:.2f} \, \text{{cm}}}}{{2}} = {d:.2f} \, \text{{cm}}")

            st.markdown("#### 2.2 Wytrzymałość obliczeniowa materiałów")
            st.latex(rf"f_{{cd}} = \frac{{f_{{ck}}}}{{\gamma_c}} = \frac{{{fck:.1f} \, \text{{MPa}}}}{{1.50}} = {fcd:.2f} \, \text{{MPa}}")
            if need_reinf:
                st.latex(rf"f_{{ywd}} = \frac{{f_{{ywk}}}}{{\gamma_s}} = \frac{{{fywk:.0f} \, \text{{MPa}}}}{{1.15}} = {fywd:.2f} \, \text{{MPa}}")
                if max_ok:
                    st.latex(rf"f_{{ywd,ef}} = \min(250 + 0.25d, f_{{ywd}}) = \min(250 + 0.25 \cdot {d*10:.0f}, {fywd:.2f}) = {fywd_eff:.2f} \, \text{{MPa}}")

            st.markdown("#### 2.3 Współczynniki i stopień zbrojenia")
            st.latex(rf"\rho_x = \frac{{A_{{sx}}}}{{1 \text{{m}} \cdot d_x}} = \frac{{{Asx:.2f} \, \text{{cm}}^2}}{{100 \, \text{{cm}} \cdot {dx:.2f} \, \text{{cm}}}} = {rho_x:.5f}")
            st.latex(rf"\rho_y = \frac{{A_{{sy}}}}{{1 \text{{m}} \cdot d_y}} = \frac{{{Asy:.2f} \, \text{{cm}}^2}}{{100 \, \text{{cm}} \cdot {dy:.2f} \, \text{{cm}}}} = {rho_y:.5f}")
            st.latex(rf"\rho_l = \min\left(\sqrt{{\rho_x \cdot \rho_y}}, 0.02\right) = \min\left(\sqrt{{{rho_x:.5f} \cdot {rho_y:.5f}}}, 0.02\right) = {rho_l:.5f}")
            st.latex(rf"k = \min\left(1 + \sqrt{{\frac{{200}}{{d}}}}, 2.0\right) = \min\left(1 + \sqrt{{\frac{{200}}{{{d*10:.0f} \, \text{{mm}}}}}}, 2.0\right) = {k:.3f}")
            st.latex(rf"\nu = 0.6 \cdot \left(1 - \frac{{f_{{ck}}}}{{250}}\right) = 0.6 \cdot \left(1 - \frac{{{fck:.1f}}}{{250}}\right) = {nu:.3f}")

            st.markdown("#### 2.4 Geometria obwodów kontrolnych")
            st.latex(rf"u_0 = 2 \cdot (b + h_{{col}}) = 2 \cdot ({b:.1f} \, \text{{cm}} + {h_col:.1f} \, \text{{cm}}) = {u0:.2f} \, \text{{cm}}")
            st.latex(rf"u_1 = 2 \cdot (b + h_{{col}}) + 4\pi d = 2 \cdot ({b:.1f} \, \text{{cm}} + {h_col:.1f} \, \text{{cm}}) + 4\pi \cdot {d:.2f} \, \text{{cm}} = {u1:.2f} \, \text{{cm}}")
            if opening_enabled:
                st.markdown("#### 2.4a Otwór prostokątny")
                st.latex(rf"b_{{otw}} = {hole_b:.1f} \, \text{{cm}}, \quad h_{{otw}} = {hole_h:.1f} \, \text{{cm}}")
                st.latex(rf"x_{{otw}} = {hole_x:.1f} \, \text{{cm}}, \quad y_{{otw}} = {hole_y:.1f} \, \text{{cm}}")
                st.latex(rf"a_{{otw}} = {opening_distance:.2f} \, \text{{cm}}")
                if opening_affects:
                    st.latex(rf"u_{{1,eff}} = u_1 - \Delta u_{{otw}} = {u1:.2f} - {u1 - u1_eff:.2f} = {u1_eff:.2f} \, \text{{cm}}")
                else:
                    st.latex(rf"u_{{1,eff}} = u_1 = {u1_eff:.2f} \, \text{{cm}}")

            st.markdown("#### 2.5 Naprężenia i weryfikacja nośności betonu")
            if beta_mode == "Wylicz":
                st.latex(rf"\beta = 1.0 + \frac{{|M_x|}}{{V_{{Ed}} \cdot b}} + \frac{{|M_y|}}{{V_{{Ed}} \cdot h_{{col}}}} = 1.0 + \frac{{{Mx:.1f}}}{{{Ved:.1f} \cdot {b/100:.2f}}} + \frac{{{My:.1f}}}{{{Ved:.1f} \cdot {h_col/100:.2f}}} = {beta:.3f}")
            
            st.latex(rf"v_{{Rd,max}} = 0.5 \cdot \nu \cdot f_{{cd}} = 0.5 \cdot {nu:.3f} \cdot {fcd:.2f} \, \text{{MPa}} = {vRdmax:.3f} \, \text{{MPa}}")
            st.latex(rf"v_{{Ed,0}} = \frac{{\beta \cdot V_{{Ed}}}}{{u_0 \cdot d}} = \frac{{{beta:.3f} \cdot {Ved:.1f} \, \text{{kN}} \cdot 10^3}}{{{u0:.2f} \, \text{{cm}} \cdot {d:.2f} \, \text{{cm}} \cdot 10^2}} = {vEd_u0:.3f} \, \text{{MPa}} \le v_{{Rd,max}} \implies \text{{{'OK' if max_ok else 'Przekroczono!'}}}")

            st.latex(rf"v_{{Rd,c}} = C_{{Rd,c}} \cdot k \cdot (100 \cdot \rho_l \cdot f_{{ck}})^{{1/3}} = {CRdc:.3f} \cdot {k:.3f} \cdot (100 \cdot {rho_l:.5f} \cdot {fck:.1f})^{{1/3}} = {vRdc:.3f} \, \text{{MPa}}")
            st.latex(rf"v_{{Ed,u1}} = \frac{{\beta \cdot V_{{Ed}}}}{{u_{{1,eff}} \cdot d}} = \frac{{{beta:.3f} \cdot {Ved:.1f} \, \text{{kN}} \cdot 10^3}}{{{u1_eff:.2f} \, \text{{cm}} \cdot {d:.2f} \, \text{{cm}} \cdot 10^2}} = {vEd:.3f} \, \text{{MPa}}")

            if need_reinf and max_ok:
                st.markdown("#### 2.6 Wymiarowanie zbrojenia na przebicie")
                st.latex(rf"u_{{out}} = \frac{{\beta \cdot V_{{Ed}}}}{{v_{{Rd,c}} \cdot d}} = \frac{{{beta:.3f} \cdot {Ved:.1f} \cdot 10^3}}{{{vRdc:.3f} \cdot {d:.2f} \cdot 10^2}} = {uout:.2f} \, \text{{cm}}")
                st.latex(rf"x_{{out}} = \frac{{u_{{out}} - 2(b + h_{{col}})}}{{2\pi}} = \frac{{{uout:.2f} - 2({b:.1f} + {h_col:.1f})}}{{2\pi}} = {x_out:.2f} \, \text{{cm}}")
                
                st.latex(rf"A_{{sw,req,1\text{{. obw.}}}} = \frac{{(v_{{Ed,u1}} - 0.75 \cdot v_{{Rd,c}}) \cdot u_{{1,eff}} \cdot s_r}}{{1.5 \cdot f_{{ywd,ef}}}} = \frac{{({vEd:.3f} - 0.75 \cdot {vRdc:.3f}) \cdot {u1_eff:.2f} \cdot {radial_spacing:.2f}}}{{1.5 \cdot {fywd_eff:.2f}}} = {Asw_req_perimeter:.2f} \, \text{{cm}}^2")
                
                st.latex(rf"n_{{req}} = \frac{{A_{{sw,req,1\text{{. obw.}}}}}}{{A_{{1\phi}}}} = \frac{{{Asw_req_perimeter:.2f}}}{{{one_bar:.2f}}} = {Asw_req_perimeter/one_bar:.1f} \implies {layer_counts[0]} \text{{ szt. na 1. obwodzie}}")
                st.latex(rf"A_{{sw,prov,1\text{{. obw.}}}} = n_1 \cdot A_{{1\phi}} = {layer_counts[0]} \cdot {one_bar:.2f} = {layer_counts[0]*one_bar:.2f} \, \text{{cm}}^2 \ge A_{{sw,req,1\text{{. obw.}}}}")
