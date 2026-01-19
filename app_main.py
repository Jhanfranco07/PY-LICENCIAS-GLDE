# app_main.py
import streamlit as st

from comercio.app_documentos import run_documentos_comercio
from comercio.app_permisos import run_permisos_comercio
from anuncios.app_anuncios import run_modulo_anuncios
from licencias.app_compatibilidad import run_modulo_compatibilidad
from integraciones.app_consultas import run_modulo_consultas


def main():
    # Configuración general de la app
    st.set_page_config(
        page_title="Generador de Documentos – GLDE",
        page_icon="🧾",
        layout="centered",
    )

    st.title("Generador de Documentos – GLDE")

    # Sidebar de navegación
    st.sidebar.title("Módulos")
    modulo = st.sidebar.radio(
        "Selecciona el módulo:",
        (
            "📥 Documentos Simples (Comercio Ambulatorio)",
            "🧾 Permisos de Comercio Ambulatorio",
            "📢 Anuncios Publicitarios",
            "🏢 Compatibilidad de Uso (Licencias)",
            "🔎 Consultas DNI / RUC (Pruebas)",
        ),
    )

    # Ruteo según módulo seleccionado
    if modulo == "📥 Documentos Simples (Comercio Ambulatorio)":
        # Módulo para registrar y ver Documentos Simples (D.S.)
        run_documentos_comercio()

    elif modulo == "🧾 Permisos de Comercio Ambulatorio":
        # Módulo de Evaluación, Resolución, Certificado y BD de comercio ambulatorio
        run_permisos_comercio()

    elif modulo == "📢 Anuncios Publicitarios":
        run_modulo_anuncios()

    elif modulo == "🏢 Compatibilidad de Uso (Licencias)":
        run_modulo_compatibilidad()

    elif modulo == "🔎 Consultas DNI / RUC (Pruebas)":
        run_modulo_consultas()


if __name__ == "__main__":
    main()
