# app_main.py
import streamlit as st

from comercio.app_permisos import run_permisos_comercio
from anuncios.app_anuncios import run_modulo_anuncios
from licencias.app_compatibilidad import run_modulo_compatibilidad
from integraciones.app_consultas import run_modulo_consultas  # ✅ NUEVO


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
            "Consultas DNI / RUC (Pruebas)",  # ✅ NUEVO
        ),
    )

    if modulo == "Permisos de Comercio Ambulatorio":
        run_permisos_comercio()

    elif modulo == "Anuncios Publicitarios":
        run_modulo_anuncios()

    elif modulo == "Compatibilidad de Uso (Licencias)":
        run_modulo_compatibilidad()

    elif modulo == "Consultas DNI / RUC (Pruebas)":  # ✅ NUEVO
        run_modulo_consultas()


if __name__ == "__main__":
    main()
