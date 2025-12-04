# app_main.py
import streamlit as st

from comercio.app_permisos import run_permisos_comercio
from anuncios.app_anuncios import run_modulo_anuncios
from licencias.app_compatibilidad import run_modulo_compatibilidad


def main():
    
    st.set_page_config(
        page_title="Generador de Documentos – GLDE",
        page_icon="🧾",
        layout="centered",
    )

    st.title("Generador de Documentos – GLDE")

    st.sidebar.title("Módulos")
    modulo = st.sidebar.radio(
        "Selecciona el tipo de documento:",
        (
            "Permisos de Comercio Ambulatorio",
            "Anuncios Publicitarios",
            "Compatibilidad de Uso (Licencias)",
        ),
    )

    if modulo == "Permisos de Comercio Ambulatorio":
        # flujo completo: Evaluación + Resolución + Certificado
        run_permisos_comercio()

        # Si luego quieres, aquí podrías meter otro radio interno
        # para elegir entre:
        #   - flujo completo
        #   - solo evaluación (run_evaluacion_comercio)
        #   - solo resolución (run_resolucion_nuevo)

    elif modulo == "Anuncios Publicitarios":
        run_modulo_anuncios()

    elif modulo == "Compatibilidad de Uso (Licencias)":
        run_modulo_compatibilidad()


if __name__ == "__main__":
    main()
