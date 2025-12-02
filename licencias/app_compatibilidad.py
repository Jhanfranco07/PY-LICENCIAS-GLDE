# licencias/app_compatibilidad.py
import streamlit as st
from utils import (
    asegurar_dirs,
    fmt_fecha_corta, fmt_fecha_larga, to_upper,
)

def run_modulo_compatibilidad():
    asegurar_dirs()

    st.header("Compatibilidad de Uso – Licencias de Funcionamiento")
    st.caption("Genera el informe / resolución de compatibilidad de uso desde una plantilla .docx")

    # Aquí puedes luego conectar tus plantillas:
    #   TPL_COMPAT = "plantilla_compa/compatibilidad_uso.docx"  (por ejemplo)

    st.markdown("---")

    # ====== FORMULARIO EJEMPLO (ajústalo a tus campos reales) ======
    col1, col2 = st.columns(2)
    with col1:
        solicitante = st.text_input("Solicitante (nombre completo)*")
        doc_identidad = st.text_input("DNI / RUC*")
        domicilio = st.text_input("Domicilio fiscal*")
    with col2:
        expediente = st.text_input("N° de expediente / trámite*")
        fecha_solicitud = st.date_input("Fecha de solicitud*", format="DD/MM/YYYY")
        zona = st.text_input("Zona / Sector urbano*")

    giro = st.text_area("Giro de negocio solicitado*", height=80)
    ubicacion = st.text_input("Ubicación del establecimiento*", max_chars=200)
    zonificacion = st.text_input("Zonificación urbanística propuesta*", max_chars=100)
    observaciones = st.text_area("Observaciones (opcional)", height=80)

    if st.button("💾 Generar documento de compatibilidad"):
        faltan = []
        for k, v in {
            "solicitante": solicitante,
            "doc_identidad": doc_identidad,
            "domicilio": domicilio,
            "expediente": expediente,
            "fecha_solicitud": fecha_solicitud,
            "giro": giro,
            "ubicacion": ubicacion,
            "zonificacion": zonificacion,
        }.items():
            if v in [None, ""]:
                faltan.append(k)

        if faltan:
            st.error("Faltan campos obligatorios: " + ", ".join(faltan))
        else:
            st.success("Aquí luego conectamos con docxtpl para generar el .docx 😄")
            # Más adelante armamos:
            #   contexto = {...}
            #   DocxTemplate(...).render(contexto)
            #   st.download_button(...)


# Solo si quieres probar este módulo por separado:
if __name__ == "__main__":
    st.set_page_config(page_title="Compatibilidad de Uso", layout="centered")
    run_modulo_compatibilidad()
