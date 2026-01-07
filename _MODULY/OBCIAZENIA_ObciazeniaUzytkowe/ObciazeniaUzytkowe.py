import streamlit as st
import pandas as pd
import re

# --------------------------------------------------------------------------------------
# 1. BAZA DANYCH MATERIAŁÓW
# --------------------------------------------------------------------------------------

MATERIALY_SCIANY = {
    "Cegła ceramiczna pełna": 19.0,
    "Cegła dziurawka": 14.0,
    "Pustak ceramiczny 'MAX'": 13.0,
    "Pustak ceramiczny poryzowany (Porotherm)": 8.5,
    "Pustak akustyczny (zalewany)": 22.0,
    "Bloczki silikatowe pełne": 20.0,
    "Bloczki silikatowe drążone": 16.0,
    "Bloczki silikatowe akustyczne": 18.0,
    "Beton komórkowy (odm. 400)": 4.5,
    "Beton komórkowy (odm. 500)": 5.5,
    "Beton komórkowy (odm. 600)": 6.5,
    "Bloczki betonowe": 24.0,
    "Bloczki gipsowe (pełne)": 11.0,
    "Płyty GK (systemowe - rdzeń)": 9.0,
    "Żelbet (monolit)": 25.0,
    "Inny materiał konstrukcyjny...": 0.0
}

MATERIALY_TYNK = {
    "Brak": 0.0,
    "Tynk gipsowy": 12.0,
    "Tynk cementowo-wapienny": 19.0,
    "Tynk cementowy": 21.0,
    "Płyta GK (okładzina)": 9.0,
    "Płytki ceramiczne": 22.0,
    "Kamień (granit/marmur)": 27.0,
    "Inny materiał wykończeniowy...": 0.0
}

# --------------------------------------------------------------------------------------
# 2. DANE REFERENCYJNE EUROKOD (TABELA 6.1 / 6.2)
# --------------------------------------------------------------------------------------

KATEGORIE_DANE = {
    "A": {
        "opis": "Powierzchnie mieszkalne",
        "psi": (0.7, 0.5, 0.3),
        "podkategorie": {
            "Stropy": {
                "opis_full": "Stropy: pokoje w budynkach mieszkalnych, sypialne i poczekalnie w szpitalach, sypialne w hotelach, kuchnie i toalety",
                "qk_range": "1,5 - 2,0", "Qk_range": "2,0 - 3,0", "def_qk": 2.0, "def_Qk": 2.0
            },
            "Schody": {
                "opis_full": "Schody",
                "qk_range": "2,0 - 4,0", "Qk_range": "2,0 - 4,0", "def_qk": 3.0, "def_Qk": 2.0
            },
            "Balkony": {
                "opis_full": "Balkony",
                "qk_range": "2,5 - 4,0", "Qk_range": "2,0 - 3,0", "def_qk": 4.0, "def_Qk": 2.0
            },
        }
    },
    "B": {
        "opis": "Powierzchnie biurowe",
        "psi": (0.7, 0.5, 0.3),
        "podkategorie": {
            "Biura": {
                "opis_full": "Powierzchnie biurowe",
                "qk_range": "2,0 - 3,0", "Qk_range": "1,5 - 4,5", "def_qk": 3.0, "def_Qk": 3.0
            }
        }
    },
    "C": {
        "opis": "Miejsca zgromadzeń (z wyjątkiem pow. A, B i D)",
        "psi": (0.7, 0.7, 0.6),
        "podkategorie": {
            "C1": {
                "opis_full": "Powierzchnie ze stołami itp. (w szkołach, kawiarniach, restauracjach, stołówkach, czytelniach, recepcjach itp.)",
                "qk_range": "2,0 - 3,0", "Qk_range": "3,0 - 4,0", "def_qk": 3.0, "def_Qk": 4.0
            },
            "C2": {
                "opis_full": "Powierzchnie z zamocowanymi siedzeniami (w kościołach, teatrach, kinach, salach wykładowych, salach zebrań)",
                "qk_range": "3,0 - 4,0", "Qk_range": "2,5 - 7,0", "def_qk": 4.0, "def_Qk": 4.0
            },
            "C3": {
                "opis_full": "Powierzchnie bez przeszkód dla ruchu ludzi (w muzeach, salach wystawowych, korytarze w budynkach publicznych)",
                "qk_range": "3,0 - 5,0", "Qk_range": "4,0 - 7,0", "def_qk": 5.0, "def_Qk": 4.0
            },
            "C4": {
                "opis_full": "Powierzchnie do ćwiczeń fizycznych (sale taneczne, gimnastyczne, sceny)",
                "qk_range": "4,5 - 5,0", "Qk_range": "3,5 - 7,0", "def_qk": 5.0, "def_Qk": 7.0
            },
            "C5": {
                "opis_full": "Powierzchnie dla tłumu (w budynkach z trybunami, tarasy, sale koncertowe, perony)",
                "qk_range": "5,0 - 7,5", "Qk_range": "3,5 - 4,5", "def_qk": 5.0, "def_Qk": 4.5
            },
        }
    },
    "D": {
        "opis": "Powierzchnie handlowe",
        "psi": (0.7, 0.7, 0.6),
        "podkategorie": {
            "D1": {
                "opis_full": "Powierzchnie w sklepach sprzedaży detalicznej",
                "qk_range": "4,0 - 5,0", "Qk_range": "3,5 - 7,0", "def_qk": 5.0, "def_Qk": 4.0
            },
            "D2": {
                "opis_full": "Powierzchnie w domach towarowych",
                "qk_range": "4,0 - 5,0", "Qk_range": "3,5 - 7,0", "def_qk": 5.0, "def_Qk": 4.0
            },
        }
    },
    "E": {
        "opis": "Powierzchnie składowania i przemysłowe",
        "psi": (1.0, 0.9, 0.8),
        "podkategorie": {
            "E1": {
                "opis_full": "Powierzchnie składowania towarów z włączeniem powierzchni dostępu (biblioteki, archiwa, magazyny)",
                "qk_range": "7,5", "Qk_range": "7,0", "def_qk": 7.5, "def_Qk": 7.0
            },
            "E2": {
                "opis_full": "Powierzchnie użytkowane do celów przemysłowych",
                "qk_range": "**", "Qk_range": "**", "def_qk": 0.0, "def_Qk": 0.0
            },
        }
    },
    "F": {
        "opis": "Garaże i parkowanie (lekkie)",
        "psi": (0.7, 0.7, 0.6),
        "podkategorie": {
            "F": {
                "opis_full": "Powierzchnie ruchu i parkowania pojazdów lekkich (≤ 30 kN ciężaru brutto, ≤8 miejsc poza kierowcą)",
                "qk_range": "1,5 - 2,5", "Qk_range": "10 - 20", "def_qk": 2.5, "def_Qk": 20.0
            }
        }
    },
    "G": {
        "opis": "Ruch i parkowanie (średnie)",
        "psi": (0.7, 0.5, 0.3),
        "podkategorie": {
            "G": {
                "opis_full": "Ruch i parkowanie średnich pojazdów (>30 kN, ≤160 kN całkowitego ciężaru)",
                "qk_range": "5,0", "Qk_range": "40 - 90", "def_qk": 5.0, "def_Qk": 90.0
            }
        }
    },
    "H": {
        "opis": "Dachy",
        "psi": (0.0, 0.0, 0.0),
        "podkategorie": {
            "H": {
                "opis_full": "Dachy bez dostępu (z wyjątkiem zwykłego utrzymania i napraw)",
                "qk_range": "0,4", "Qk_range": "1,0", "def_qk": 0.4, "def_Qk": 1.0
            }
        }
    },
    "I": {
        "opis": "Dachy dostępne",
        "psi": (0.7, 0.5, 0.3),
        "podkategorie": {
            "I": {
                "opis_full": "Dachy z dostępem, z warunkami użytkowania wg kategorii A-G",
                "qk_range": "wg A-G**", "Qk_range": "wg A-G**", "def_qk": 2.0, "def_Qk": 2.0
            }
        }
    },
    "K": {
        "opis": "Lądowiska",
        "psi": (0.7, 0.7, 0.6),
        "podkategorie": {
            "HC1": {
                "opis_full": "Lądowiska helikopterów (HC1)",
                "qk_range": "-", "Qk_range": "20,0", "def_qk": 0.0, "def_Qk": 20.0
            },
            "HC2": {
                "opis_full": "Lądowiska helikopterów (HC2)",
                "qk_range": "-", "Qk_range": "60,0", "def_qk": 0.0, "def_Qk": 60.0
            }
        }
    },
}

# --------------------------------------------------------------------------------------
# FUNKCJE POMOCNICZE
# --------------------------------------------------------------------------------------

def format_material_label(name: str, db: dict) -> str:
    """Tworzy etykietę: Nazwa (gamma) dla selectboxa."""
    if "Brak" in name or "Inny" in name:
        return name
    density = db.get(name, 0.0)
    return f"{name} (γ={density:.1f})"


def format_cell_text(rng, default_val) -> str:
    """
    Formatowanie tekstu komórki qₖ / Qₖ:
    - zakres,
    - wartość zalecana w nawiasie: (...*).
    """
    d_val_str = str(default_val).replace(".", ",")
    rng_str = str(rng)

    # Wartości specjalne z normy
    if "**" in rng_str:
        return rng_str

    if rng_str == "-" and default_val == 0.0:
        return "-"

    # Zakres = pojedyncza wartość
    if rng_str.replace(" ", "") == d_val_str.replace(" ", ""):
        return f"({d_val_str}*)"

    # Zakres + zalecana wartość w nawiasie
    return f"{rng_str} ({d_val_str}*)"


def opis_two_linie(text: str, max_len: int = 70) -> str:
    """
    Dzieli długi opis na maksymalnie dwie linijki (poprzez znak nowej linii).
    """
    if len(text) <= max_len:
        return text
    split_pos = text.rfind(" ", 0, max_len)
    if split_pos == -1:
        split_pos = max_len
    return text[:split_pos] + "\n" + text[split_pos + 1:]

# --------------------------------------------------------------------------------------
# GENEROWANIE TABEL HTML (Dla połączonych komórek i stylizacji)
# --------------------------------------------------------------------------------------

def generate_custom_html_table(data_dict):
    """
    Generuje kod HTML tabeli kategorii z połączonymi komórkami i czarnym nagłówkiem.
    """
    # Usunięcie wcięć wewnątrz stringa HTML, aby uniknąć interpretacji jako blok kodu przez markdown
    html = """
    <style>
        .custom-table {
            width: 100%;
            border-collapse: collapse;
            font-family: sans-serif;
            font-size: 14px;
            color: #ffffff;
            background-color: #2b2b2b;
        }
        .custom-table th {
            background-color: #000000;
            color: #ffffff;
            border: 1px solid #555;
            padding: 8px;
            text-align: left;
            font-weight: 600;
        }
        .custom-table td {
            border: 1px solid #555;
            padding: 8px;
            vertical-align: middle;
        }
        .center-text {
            text-align: center;
        }
        .red-highlight {
            color: #ff4d4d;
            font-weight: bold;
        }
    </style>
    <table class="custom-table">
        <thead>
            <tr>
                <th style="width: 5%;">Kategoria</th>
                <th style="width: 20%;">Opis kategorii</th>
                <th style="width: 10%;">Podkategoria</th>
                <th style="width: 45%;">Opis szczegółowy</th>
                <th style="width: 10%;">qₖ [kN/m²]</th>
                <th style="width: 10%;">Qₖ [kN]</th>
            </tr>
        </thead>
        <tbody>
    """

    for kat, data_kat in data_dict.items():
        opis_kat = data_kat["opis"]
        podkategorie = data_kat["podkategorie"]
        rowspan = len(podkategorie)
        
        first = True
        for pk_key, pk_vals in podkategorie.items():
            # Konstrukcja wiersza bez wcięć (flush left) aby uniknąć problemów z markdownem
            html += "<tr>"
            
            if first:
                html += f'<td rowspan="{rowspan}" class="center-text"><b>{kat}</b></td>'
                html += f'<td rowspan="{rowspan}">{opis_kat}</td>'
            
            html += f'<td class="center-text">{pk_key}</td>'
            
            opis = opis_two_linie(pk_vals["opis_full"])
            html += f'<td>{opis.replace(chr(10), "<br>")}</td>'
            
            def color_brackets(text):
                return re.sub(r'(\(.*\))', r'<span class="red-highlight">\1</span>', text)

            qk_val = format_cell_text(pk_vals["qk_range"], pk_vals["def_qk"])
            Qk_val = format_cell_text(pk_vals["Qk_range"], pk_vals["def_Qk"])
            
            html += f'<td class="center-text">{color_brackets(qk_val)}</td>'
            html += f'<td class="center-text">{color_brackets(Qk_val)}</td>'
            html += "</tr>"
            
            first = False

    html += """</tbody></table>"""
    return html

def generate_scianki_html_table(rows_data):
    """
    Generuje kod HTML tabeli ścianek działowych w tym samym stylu co tabela kategorii.
    Ważne: Usunięcie wcięć (indentation) w generowanym stringu, aby uniknąć traktowania jako kod.
    """
    
    html = """
    <style>
        .custom-table {
            width: 100%;
            border-collapse: collapse;
            font-family: sans-serif;
            font-size: 14px;
            color: #ffffff;
            background-color: #2b2b2b;
        }
        .custom-table th {
            background-color: #000000;
            color: #ffffff;
            border: 1px solid #555;
            padding: 8px;
            text-align: left;
            font-weight: 600;
        }
        .custom-table td {
            border: 1px solid #555;
            padding: 8px;
            vertical-align: middle;
        }
        .center-text {
            text-align: center;
        }
    </style>
    <table class="custom-table">
        <thead>
            <tr>
                <th style="width: 40%;">Ciężar własny ścianki g [kN/m]</th>
                <th style="width: 60%;">Obciążenie zastępcze od ścianek działowych qₖ [kN/m²]</th>
            </tr>
        </thead>
        <tbody>
    """
    
    for row in rows_data:
        g_val = row["Ciężar własny ścianki g [kN/m]"]
        qk_val = row["Obciążenie zastępcze od ścianek działowych qₖ [kN/m²]"]
        
        # Brak wcięć dla tagów tr/td
        html += "<tr>"
        html += f'<td class="center-text">{g_val}</td>'
        html += f'<td class="center-text">{qk_val}</td>'
        html += "</tr>"
        
    html += "</tbody></table>"
    return html

# --------------------------------------------------------------------------------------
# GŁÓWNA APLIKACJA STREAMLIT
# --------------------------------------------------------------------------------------

def StronaObciazeniaUzytkowe() -> None:
    
    # 0. STYLE I KONFIGURACJA STRONY (Identyczne jak w KombinacjeObciazen.py)
    st.markdown(
        """
        <style>
        .block-container { padding-top: 1.5rem; padding-bottom: 1.5rem; }
        h3 { margin-top: 1rem !important; margin-bottom: 0.5rem !important; font-size: 1.2rem; }
        div[data-testid="stForm"] > div { margin-bottom: 0 !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # 1. TYTUŁ GŁÓWNY (NA GÓRZE STRONY)
    st.markdown(
        """
        <div style="text-align:center; margin-top:0.4rem; margin-bottom:0rem;">
            <span style="font-size:42px; font-weight:800; letter-spacing:1px; color:#dddddd;">
                OBCIĄŻENIA UŻYTKOWE
            </span>
        </div>
        <div style="text-align:center; font-size:14px; color:#aaaaaa; margin-top:-12px; margin-bottom:1.5rem;">
            wg PN-EN 1991-1-1
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # 2. ZAKŁADKI POD TYTUŁEM
    tab1, tab2 = st.tabs(["OBCIĄŻENIA UŻYTKOWE", "ŚCIANY DZIAŁOWE"])

    # ==================================================================================
    # ZAKŁADKA 1: OBCIĄŻENIE UŻYTKOWE
    # ==================================================================================
    with tab1:
        # TYTUŁ W ZAKŁADCE USUNIĘTY (JEST TERAZ NA GÓRZE)

        # 1. CZĘŚĆ TEORETYCZNA
        st.markdown(
            """
            **Obciążenia użytkowe** (zmienne) zależą od przeznaczenia budowli. 
            Klasyfikuje się je w kategorie (od A do K) zgodnie z tablicą 6.1 normy PN-EN 1991-1-1.
            Wartości te obejmują:
            - **równomiernie rozłożone $q_k$** [kN/m²] – do sprawdzania efektów ogólnych,
            - **skupione $Q_k$** [kN] – do sprawdzania efektów lokalnych (np. przebicie).
            """
        )

        # 2. TABELA ZBIORCZA - WYGENEROWANA W HTML
        st.markdown(generate_custom_html_table(KATEGORIE_DANE), unsafe_allow_html=True)
        
        # LEGENDA
        st.caption(
            """
            **Legenda:**
            * `*` Wartość zalecana przez ogólną normę europejską (EN). **Uwaga:** W Polsce należy zweryfikować tę wartość z **Załącznikiem Krajowym (NA)**, który może narzucać inne parametry.
            * `**` Wartość należy przyjąć wg specyfikacji technologicznej lub uzgodnień z inwestorem.
            """
        )
        
        # 3. KALKULATOR
        st.markdown("")
        st.markdown("#### 🧮 Kalkulator wartości zalecanych")
        
        c_kat, c_podkat = st.columns([1, 2])
        with c_kat:
            wybrana_kat = st.selectbox("Wybierz kategorię:", list(KATEGORIE_DANE.keys()))
        
        with c_podkat:
            dane_kat = KATEGORIE_DANE[wybrana_kat]
            podkategorie = dane_kat["podkategorie"]
            
            # Lista opcji do selectboxa
            opcje = list(podkategorie.keys())
            
            wybrana_podkat_klucz = st.selectbox(
                f"Podkategoria ({dane_kat['opis']}):", 
                opcje,
                format_func=lambda x: f"{x} – {podkategorie[x]['opis_full'][:60]}..." 
            )
            vals = podkategorie[wybrana_podkat_klucz]
            psi_vals = dane_kat["psi"]

        # Wyniki w kolumnach
        st.markdown("")
        col_res1, col_res2, col_psi = st.columns([1.2, 1.2, 2.0])
        
        with col_res1:
            st.metric("Obc. równomierne qₖ", f"{vals['def_qk']} kN/m²")
        
        with col_res2:
            st.metric("Obc. skupione Qₖ", f"{vals['def_Qk']} kN")
            
        with col_psi:
            st.markdown("**Współczynniki jednoczesności $\psi$:**")
            st.markdown(f"""
            - $\psi_0 = {psi_vals[0]}$ (kombinacyjna)
            - $\psi_1 = {psi_vals[1]}$ (częsta)
            - $\psi_2 = {psi_vals[2]}$ (prawie stała)
            """)

    # ==================================================================================
    # ZAKŁADKA 2: ŚCIANY DZIAŁOWE
    # ==================================================================================
    with tab2:
        # TYTUŁ W ZAKŁADCE ZAMIENIONY NA MNIEJSZY NAGŁÓWEK
        st.markdown("### Obciążenie ścianami działowymi")
        
        st.markdown(
            """
            Jeśli konstrukcja stropu pozwala na poprzeczny rozkład obciążeń, zaleca się aby ciężar własny przestawnych ścian działowych, 
            który może być uwzględniany jako obciążenie równomiernie rozłożone $q_k$, był dodawany do obciążeń użytkowych.
            
            Wartości charakterystyczne oddziaływań zależą od ciężaru własnego ścian i wynoszą:
            """
        )
        
        # Tabela reguł – ZMIENIONO NA HTML (naprawiono wcięcia, aby uniknąć problemu raw code)
        scianki_rows = [
            {
                "Ciężar własny ścianki g [kN/m]": "g ≤ 1,0 kN/m",
                "Obciążenie zastępcze od ścianek działowych qₖ [kN/m²]": "0,5",
            },
            {
                "Ciężar własny ścianki g [kN/m]": "1,0 < g ≤ 2,0 kN/m",
                "Obciążenie zastępcze od ścianek działowych qₖ [kN/m²]": "0,8",
            },
            {
                "Ciężar własny ścianki g [kN/m]": "2,0 < g ≤ 3,0 kN/m",
                "Obciążenie zastępcze od ścianek działowych qₖ [kN/m²]": "1,2",
            },
            {
                "Ciężar własny ścianki g [kN/m]": "g > 3,0 kN/m",
                "Obciążenie zastępcze od ścianek działowych qₖ [kN/m²]": "Projekt indywidualny (obc. liniowe)",
            },
        ]

        # Wywołanie generatora HTML dla tabeli
        st.markdown(generate_scianki_html_table(scianki_rows), unsafe_allow_html=True)

        # KOMUNIKAT O CIĘŻSZYCH ŚCIANACH
        st.error(
            "⚠️ **UWAGA:** Cięższe ściany należy projektować z uwzględnieniem położenia i kierunku usytuowania oraz rodzaju konstrukcji stropu."
        )
        
        # Kalkulator
        st.markdown("")
        st.markdown("#### 🧮 Kalkulator obciążenia zastępczego")
        
        col_h, col_empty = st.columns([1, 3])
        h_sciany = col_h.number_input("Wysokość ściany [m]", value=2.70, step=0.05, format="%.2f")

        st.markdown("###### Warstwy ściany")
        
        def row_layer(label, materials_db, default_idx, key_suffix):
            c_mat, c_thick, c_density_custom = st.columns([3, 1, 1])
            
            mat = c_mat.selectbox(
                label, 
                options=list(materials_db.keys()), 
                index=default_idx, 
                format_func=lambda x: format_material_label(x, materials_db),
                key=f"mat_{key_suffix}",
                label_visibility="collapsed"
            )
            
            def_th = 0.0
            if "Tynk" in mat or "Płyta" in mat:
                def_th = 1.5
            elif "Pustak" in mat or "Cegła" in mat:
                def_th = 12.0
            
            gr = c_thick.number_input(
                "Grubość [cm]", 
                value=def_th, 
                step=0.5, 
                key=f"gr_{key_suffix}",
                help="Grubość warstwy w cm",
                label_visibility="collapsed"
            )
            
            dens = materials_db.get(mat, 0.0)
            if "Inny" in mat:
                dens = c_density_custom.number_input(
                    "γ [kN/m³]", value=10.0, step=1.0, key=f"dens_custom_{key_suffix}", label_visibility="collapsed"
                )
            
            return gr / 100.0, dens

        ch1, ch2, ch3 = st.columns([3, 1, 1])
        ch1.caption("Materiał")
        ch2.caption("Grubość [cm]")
        
        d1, rho1 = row_layer("Warstwa 1", MATERIALY_TYNK, 1, "L1") 
        d2, rho2 = row_layer("Warstwa 2", MATERIALY_SCIANY, 3, "L2") 
        d3, rho3 = row_layer("Warstwa 3", MATERIALY_TYNK, 1, "L3") 

        g_lin = h_sciany * (d1 * rho1 + d2 * rho2 + d3 * rho3)
        
        qk_part = 0.0
        msg = ""
        is_heavy_warning = False

        if g_lin <= 1.0:
            qk_part, msg = 0.5, "Norma (g ≤ 1.0 kN/m)"
        elif g_lin <= 2.0:
            qk_part, msg = 0.8, "Norma (1.0 < g ≤ 2.0 kN/m)"
        elif g_lin <= 3.0:
            qk_part, msg = 1.2, "Norma (2.0 < g ≤ 3.0 kN/m)"
        else:
            qk_part = g_lin * 0.4  
            msg = "Aproksymacja inżynierska (>3.0 kN/m)"
            is_heavy_warning = True

   
        res_c1, res_c2 = st.columns(2)
        res_c1.metric("Ciężar liniowy ściany", f"{g_lin:.2f} kN/m")
        res_c2.metric("Obciążenie równomierne", f"{qk_part:.2f} kN/m²", delta="! Inżynierski" if is_heavy_warning else None, delta_color="off")
        
        if is_heavy_warning:
            st.error(
                f"⚠️ **UWAGA:** Ciężar ściany ({g_lin:.2f} kN/m) > 3,0 kN/m. Wynik to **szacunek inżynierski**. Zaleca się przyjąć obciążenie liniowe w miejscu ustawienia ściany."
            )
        else:
            st.success(f"✅ {msg}")


if __name__ == "__main__":
    StronaObciazeniaUzytkowe()