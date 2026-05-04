import streamlit as st


def run():
    st.markdown(
        """
        <div style="
            margin: 1.2rem 0;
            padding: 1rem 1.1rem;
            border: 1px solid #f3d38a;
            border-radius: 12px;
            background: linear-gradient(180deg, #fffdf5 0%, #fff8e7 100%);
            color: #5b4a1f;
        ">
            <div style="font-size: 1.05rem; font-weight: 700; margin-bottom: 0.35rem;">
                Kalkulator w fazie opracowania
            </div>
            <div style="font-size: 0.95rem; line-height: 1.5;">
                Ten modul jest obecnie przygotowywany i zostanie udostepniony w jednej z kolejnych aktualizacji.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
