# anuncios/app_anuncios.py

import streamlit as st
from docxtpl import DocxTemplate
from io import BytesIO
from datetime import date
import jinja2

from utils import fecha_larga, safe_filename_pretty  # función común en utils.py


def run_modulo_anuncios():
    st.header("📢 Anuncios Publicitarios – Evaluación y Certificado")

    # ========= Rutas de plantillas (carpeta en la RAÍZ del proyecto) =========
    TEMPLATES_EVAL = {
        "PANEL SIMPLE - AZOTEAS": "plantillas_publicidad/evaluacion_panel_simple_azotea.docx",
        "LETRAS RECORTADAS": "plantillas_publicidad/evaluacion_letras_recortadas.docx",
        "PANEL SIMPLE - ESTACIONES DE SERVICIO": "plantillas_publicidad/evaluacion_panel_simple_estacion.docx",
        "TOLDO SENCILLO": "plantillas_publicidad/evaluacion_toldo_sencillo.docx",
        "PANEL SENCILLO Y LUMINOSO": "plantillas_publicidad/evaluacion_panel_sencillo_luminoso.docx",
    }

    TEMPLATES_CERT = {
        "PANEL SIMPLE - AZOTEAS": "plantillas_publicidad/certificado_panel_simple_azotea.docx",
        "LETRAS RECORTADAS": "plantillas_publicidad/certificado_letras_recortadas.docx",
        "PANEL SIMPLE - ESTACIONES DE SERVICIO": "plantillas_publicidad/certificado_panel_simple_estacion.docx",
        "TOLDO SENCILLO": "plantillas_publicidad/certificado_toldo_sencillo.docx",
        "PANEL SENCILLO Y LUMINOSO": "plantillas_publicidad/certificado_panel_sencillo_luminoso.docx",
    }

    tipo_anuncio = st.selectbox(
        "Tipo de anuncio publicitario",
        list(TEMPLATES_EVAL.keys())
    )

    st.markdown("---")

    # -------------------------------------------------------------------------
    #                    MÓDULO 1 · EVALUACIÓN
    # -------------------------------------------------------------------------

    # Estos tipos usan GROSOR en las dimensiones
    usa_grosor = tipo_anuncio in (
        "PANEL SENCILLO Y LUMINOSO",
        "LETRAS RECORTADAS",
        "TOLDO SENCILLO",
    )
    # Este tipo usa ALTURA (soporte) extra
    usa_altura_extra = tipo_anuncio == "PANEL SIMPLE - AZOTEAS"

    grosor = 0.0
    altura_extra = 0.0

    with st.form("form_evaluacion"):

        # ---------------- Datos del solicitante ----------------
        st.subheader("Datos del solicitante")

        # Tipo de contribuyente / RUC 10 vs RUC 20
        tipo_ruc_label = st.radio(
            "Tipo de contribuyente",
            ["RUC 10 – Persona natural", "RUC 20 – Persona jurídica"],
            index=0,
            horizontal=True,
        )
        tipo_ruc = "10" if tipo_ruc_label.startswith("RUC 10") else "20"

        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("Solicitante (nombre completo)", max_chars=150)
            # Si es RUC 20, pedimos también el representante legal (solo para Excel luego)
            if tipo_ruc == "20":
                representante = st.text_input(
                    "Representante legal (solo RUC 20)",
                    max_chars=150,
                    placeholder="Nombre completo del representante"
                )
            else:
                representante = ""
            direccion = st.text_input("Dirección del solicitante", max_chars=200)

        with col2:
            ruc = st.text_input("RUC", max_chars=15)

        # ---------------- Datos del anuncio ----------------
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

        # ---------------- Datos administrativos ----------------
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

        generar_eval = st.form_submit_button("Generar evaluación")

    # ---------- GENERACIÓN DEL WORD (EVALUACIÓN) ----------
    if generar_eval:
        if not nombre or not n_anuncio or not num_ds:
            st.error("Completa al menos: Solicitante, N° de anuncio y N° de expediente.")
        else:
            template_path = TEMPLATES_EVAL[tipo_anuncio]
            st.info(f"Usando plantilla: {template_path}")

            contexto_eval = {
                "n_anuncio": n_anuncio,
                "nombre": nombre,
                "ruc": ruc,
                "direccion": direccion,
                "largo": f"{largo:.2f}",
                "alto": f"{alto:.2f}",
                "leyenda": leyenda,
                "colores": colores,
                "material": material,
                "ubicacion": ubicacion,          # En Word: {{ubicacion}}
                "num_cara": int(num_cara),
                "num_ds": num_ds,
                "fecha_ingreso": fecha_ingreso.strftime("%d/%m/%Y"),
                "fecha": fecha_larga(fecha),     # Fecha larga tipo: 2 de diciembre de 2025
                "anio": anio,
                "tipo_anuncio": tipo_anuncio,
                "grosor": f"{grosor:.2f}" if usa_grosor else "",
                "altura": f"{altura_extra:.2f}" if usa_altura_extra else "",
                # Campos extra solo para registro / Excel (no usados en Word)
                "tipo_ruc": tipo_ruc,                 # "10" o "20"
                "tipo_ruc_label": tipo_ruc_label,     # texto completo del radio
                "representante": representante,       # solo si RUC 20
            }

            # guardamos datos para el certificado y, luego, para Excel
            st.session_state["anuncio_eval_ctx"] = contexto_eval

            try:
                doc = DocxTemplate(template_path)
                doc.render(contexto_eval, autoescape=True)

                buffer = BytesIO()
                doc.save(buffer)
                buffer.seek(0)

                base_name = f"EA {n_anuncio}_exp{num_ds}_{nombre.lower()}"
                nombre_archivo = safe_filename_pretty(base_name) + ".docx"

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
                st.error("Hay un error de sintaxis en la plantilla de EVALUACIÓN.")
                st.error(f"Plantilla: {template_path}")
                st.error(f"Mensaje: {e.message}")
                st.error(f"Línea aproximada en el XML: {e.lineno}")
            except Exception as e:
                st.error(f"Ocurrió un error al generar el documento de evaluación: {e}")

    # -------------------------------------------------------------------------
    #                    MÓDULO 2 · CERTIFICADO
    # -------------------------------------------------------------------------
    st.markdown("---")
    st.subheader("📜 Certificado de Anuncio Publicitario")

    eval_ctx = st.session_state.get("anuncio_eval_ctx")

    if not eval_ctx:
        st.info("Primero genera la **Evaluación** para reutilizar sus datos en el Certificado.")
        return

    # Mostramos un pequeño resumen de datos reutilizados
    with st.expander("Ver datos reutilizados de la Evaluación"):
        st.write(
            {
                "N° anuncio": eval_ctx.get("n_anuncio"),
                "Expediente / DS": eval_ctx.get("num_ds"),
                "Nombre / Razón social": eval_ctx.get("nombre"),
                "Tipo de RUC": eval_ctx.get("tipo_ruc_label"),
                "Representante (si RUC 20)": eval_ctx.get("representante"),
                "Dirección": eval_ctx.get("direccion"),
                "Ubicación": eval_ctx.get("ubicacion"),
                "Leyenda": eval_ctx.get("leyenda"),
                "Dimensiones": f"{eval_ctx.get('largo')} x {eval_ctx.get('alto')}",
                "Grosor": eval_ctx.get("grosor"),
                "Altura (soporte)": eval_ctx.get("altura"),
                "Caras": eval_ctx.get("num_cara"),
                "Colores": eval_ctx.get("colores"),
                "Material": eval_ctx.get("material"),
            }
        )

    with st.form("form_certificado"):
        colc1, colc2 = st.columns(2)
        with colc1:
            n_certificado = st.text_input("N° de certificado", max_chars=20)
        with colc2:
            # la fecha del certificado (parte baja de la hoja)
            fecha_cert = st.date_input("Fecha del certificado", value=date.today())

        # Vigencia
        vigencia_tipo = st.selectbox(
            "Tipo de vigencia",
            ["INDETERMINADA", "TEMPORAL"]
        )

        meses_vigencia = 0
        if vigencia_tipo == "TEMPORAL":
            meses_vigencia = st.number_input(
                "Meses de vigencia",
                min_value=1,
                max_value=60,
                step=1,
                value=1,
            )

        # Ordenanza
        ordenanza = st.selectbox(
            "Ordenanza aplicable",
            ["2682-MML", "107-MDP/C"]
        )

        # Características físicas / técnicas
        colf, colt = st.columns(2)
        with colf:
            fisico = st.selectbox(
                "Características FÍSICAS",
                ["TOLDO", "PANEL SIMPLE", "LETRAS RECORTADAS", "BANDEROLA"]
            )
        with colt:
            tecnico = st.selectbox(
                "Características TÉCNICAS",
                ["SENCILLO", "LUMINOSO", "ILUMINADO"]
            )

        generar_cert = st.form_submit_button("Generar certificado")

    # ---------- GENERACIÓN DEL WORD (CERTIFICADO) ----------
    if generar_cert:
        if not n_certificado:
            st.error("Completa el N° de certificado.")
            return

        if vigencia_tipo == "TEMPORAL":
            vigencia_txt = f"TEMPORAL ({int(meses_vigencia)}) MESES"
        else:
            vigencia_txt = "INDETERMINADA"

        cert_template_path = TEMPLATES_CERT.get(tipo_anuncio)
        if not cert_template_path:
            st.error("No se encontró plantilla de certificado para este tipo de anuncio.")
            return

        contexto_cert = {
            "n_certificado": n_certificado,
            "num_ds": eval_ctx.get("num_ds", ""),
            "vigencia": vigencia_txt,
            "ordenanza": ordenanza,

            "nombre": eval_ctx.get("nombre", ""),
            "direccion": eval_ctx.get("direccion", ""),
            "ubicacion": eval_ctx.get("ubicacion", ""),
            "leyenda": eval_ctx.get("leyenda", ""),

            "largo": eval_ctx.get("largo", ""),
            "alto": eval_ctx.get("alto", ""),
            "grosor": eval_ctx.get("grosor", ""),   # usado por letras/panel luminoso/toldo
            "altura": eval_ctx.get("altura", ""),   # usado por panel azotea (SOPORTE)
            "color": eval_ctx.get("colores", ""),
            "material": eval_ctx.get("material", ""),
            "num_cara": eval_ctx.get("num_cara", ""),

            "fisico": fisico,
            "tecnico": tecnico,
            "fecha": fecha_larga(fecha_cert),       # PACHACÁMAC, {{fecha}}
        }

        try:
            doc = DocxTemplate(cert_template_path)
            doc.render(contexto_cert, autoescape=True)

            buffer = BytesIO()
            doc.save(buffer)
            buffer.seek(0)

            # Nombre del archivo: CERT 183_EXP 6127_MANCO JARA
            num_ds_val = str(eval_ctx.get("num_ds", "")).strip()
            nombre_val = str(eval_ctx.get("nombre", "")).strip().upper()

            base_name_cert = f"CERT {n_certificado}_EXP {num_ds_val}_{nombre_val}"
            nombre_archivo_cert = safe_filename_pretty(base_name_cert) + ".docx"

            st.success("Certificado generado correctamente.")
            st.download_button(
                label="⬇️ Descargar certificado en Word",
                data=buffer,
                file_name=nombre_archivo_cert,
                mime=(
                    "application/vnd.openxmlformats-"
                    "officedocument.wordprocessingml.document"
                ),
            )

        except jinja2.TemplateSyntaxError as e:
            st.error("Hay un error de sintaxis en la plantilla de CERTIFICADO.")
            st.error(f"Plantilla: {cert_template_path}")
            st.error(f"Mensaje: {e.message}")
            st.error(f"Línea aproximada en el XML: {e.lineno}")
        except Exception as e:
            st.error(f"Ocurrió un error al generar el certificado: {e}")


# Permite correr SOLO este módulo si quieres:
if __name__ == "__main__":
    st.set_page_config(page_title="Anuncios Publicitarios", layout="centered")
    run_modulo_anuncios()
