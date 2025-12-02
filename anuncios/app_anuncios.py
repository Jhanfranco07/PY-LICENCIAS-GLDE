# anuncios/app_anuncios.py

import streamlit as st
from docxtpl import DocxTemplate
from io import BytesIO
from datetime import date
import jinja2

from utils import fecha_larga  # función común en utils.py


def run_modulo_anuncios():
    st.header("📢 Anuncios Publicitarios – Evaluación")

    # Rutas de plantillas (carpeta en la RAÍZ del proyecto)
    TEMPLATES_EVAL = {
        "PANEL SIMPLE - AZOTEAS": "plantillas_publi/evaluacion_panel_simple_azotea.docx",
        "LETRAS RECORTADAS": "plantillas_publi/evaluacion_letras_recortadas.docx",
        "PANEL SIMPLE - ESTACIONES DE SERVICIO": "plantillas_publi/evaluacion_panel_simple_estacion.docx",
        "TOLDO SENCILLO": "plantillas_publi/evaluacion_toldo_sencillo.docx",
        "PANEL SENCILLO Y LUMINOSO": "plantillas_publi/evaluacion_panel_sencillo_luminoso.docx",
    }

    tipo_anuncio = st.selectbox(
        "Tipo de anuncio publicitario",
        list(TEMPLATES_EVAL.keys())
    )

    st.markdown("---")

    # Lógica de campos adicionales
    usa_grosor = tipo_anuncio in (
        "PANEL SENCILLO Y LUMINOSO",
        "LETRAS RECORTADAS",
    )
    usa_altura_extra = tipo_anuncio == "PANEL SIMPLE - AZOTEAS"

    grosor = 0.0
    altura_extra = 0.0

    # ---------- FORMULARIO ----------
    with st.form("form_evaluacion"):

        # Datos del solicitante
        st.subheader("Datos del solicitante")
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("Solicitante (nombre completo)", max_chars=150)
            direccion = st.text_input("Dirección del solicitante", max_chars=200)
        with col2:
            ruc = st.text_input("RUC", max_chars=15)

        # Datos del anuncio
        st.subheader("Datos del anuncio")

        col3, col4 = st.columns(2)
        with col3:
            largo = st.number_input("Largo (m)", min_value=0.0, step=0.10, format="%.2f")
        with col4:
            alto = st.number_input("Alto (m)", min_value=0.0, step=0.10, format="%.2f")

        if usa_grosor:
            grosor = st.number_input("Grosor (m)", min_value=0.0, step=0.01, format="%.2f")
        elif usa_altura_extra:
            altura_extra = st.number_input("Altura (m)", min_value=0.0, step=0.10, format="%.2f")

        num_cara = st.number_input("N° de caras", min_value=1, step=1)

        leyenda = st.text_area("Leyenda del anuncio", height=80)

        col_colores, col_material = st.columns(2)
        with col_colores:
            colores = st.text_input("Colores principales")
        with col_material:
            material = st.text_input("Material")

        ubicacion = st.text_input("Ubicación del anuncio", max_chars=200)

        # Datos administrativos
        st.subheader("Datos administrativos")
        col6, col7, col8 = st.columns(3)
        with col6:
            n_anuncio = st.text_input("N° de anuncio (ej. 001)")
        with col7:
            num_ds = st.text_input("N° de expediente / DS (ej. 1234)")
        with col8:
            fecha_ingreso = st.date_input("Fecha de ingreso", value=date.today())

        col9, col10 = st.columns(2)
        with col9:
            fecha = st.date_input("Fecha del informe", value=date.today())
        with col10:
            anio = st.number_input(
                "Año (para el encabezado y expediente)",
                min_value=2020,
                max_value=2100,
                value=date.today().year,
                step=1,
            )

        generar = st.form_submit_button("Generar evaluación")

    # ---------- GENERACIÓN DEL WORD ----------
    if generar:
        if not nombre or not n_anuncio or not num_ds:
            st.error("Completa al menos: Solicitante, N° de anuncio y N° de expediente.")
        else:
            template_path = TEMPLATES_EVAL[tipo_anuncio]
            st.info(f"Usando plantilla: {template_path}")

            contexto = {
                "n_anuncio": n_anuncio,
                "nombre": nombre,
                "ruc": ruc,
                "direccion": direccion,
                "largo": f"{largo:.2f}",
                "alto": f"{alto:.2f}",
                "leyenda": leyenda,
                "colores": colores,
                "material": material,
                "ubicacion": ubicacion,          # En Word: {{ubicación}}
                "num_cara": int(num_cara),
                "num_ds": num_ds,
                "fecha_ingreso": fecha_ingreso.strftime("%d/%m/%Y"),
                "fecha": fecha_larga(fecha),     # Fecha larga tipo: 2 de diciembre de 2025
                "anio": anio,
                "tipo_anuncio": tipo_anuncio,
                "grosor": f"{grosor:.2f}" if usa_grosor else "",
                "altura": f"{altura_extra:.2f}" if usa_altura_extra else "",
            }

            try:
                doc = DocxTemplate(template_path)
                doc.render(contexto)

                buffer = BytesIO()
                doc.save(buffer)
                buffer.seek(0)

                nombre_archivo = f"Evaluacion_{tipo_anuncio.replace(' ', '_')}_{n_anuncio}.docx"

                st.success("Evaluación generada correctamente.")
                st.download_button(
                    label="⬇️ Descargar evaluación en Word",
                    data=buffer,
                    file_name=nombre_archivo,
                    mime=(
                        "application/vnd.openxmlformats-"
                        "officedocument.wordprocessingml.document"
                    ),
                )

            except jinja2.TemplateSyntaxError as e:
                st.error("Hay un error de sintaxis en la plantilla Word.")
                st.error(f"Plantilla: {template_path}")
                st.error(f"Mensaje: {e.message}")
                st.error(f"Línea aproximada en el XML: {e.lineno}")
            except Exception as e:
                st.error(f"Ocurrió un error al generar el documento: {e}")


# Permite correr SOLO este módulo si quieres:
if __name__ == "__main__":
    st.set_page_config(page_title="Anuncios Publicitarios", layout="centered")
    run_modulo_anuncios()
