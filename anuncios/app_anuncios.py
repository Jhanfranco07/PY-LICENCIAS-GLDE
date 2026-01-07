# anuncios/app_anuncios.py

import os
import pandas as pd
import streamlit as st
from docxtpl import DocxTemplate
from io import BytesIO
from datetime import date
import jinja2

from utils import fecha_larga, safe_filename_pretty  # función común en utils.py

# Ruta del Excel de base de datos de certificados
# Puedes cambiar el nombre si quieres usar el archivo oficial:
# BD_EXCEL_PATH = "BASE DE DATOS - CERTIFICADOS DE ANUNCIO.xlsx"
BD_EXCEL_PATH = "BD_CERTIFICADOS_ANUNCIO.xlsx"


# ============ Helpers para la BD en Excel ============

def split_nombre_apellidos(nombre_raw: str):
    """
    Separa en:
    - apellido paterno
    - apellido materno
    - nombres
    usando una heurística simple basada en espacios.
    """
    if not nombre_raw:
        return "", "", ""

    partes = str(nombre_raw).strip().upper().split()
    if len(partes) == 1:
        return partes[0], "", ""
    elif len(partes) == 2:
        ape_pat = partes[0]
        ape_mat = ""
        nombres = partes[1]
    else:
        ape_pat = partes[0]
        ape_mat = partes[1]
        nombres = " ".join(partes[2:])
    return ape_pat, ape_mat, nombres


def guardar_certificado_en_excel(
    eval_ctx,
    vigencia_txt,
    n_certificado,
    fecha_cert,
    fisico,
    tecnico,
    doc_tipo,
    doc_num,
    num_recibo,
):
    """
    Construye una fila con el formato oficial y la agrega (o crea) el Excel.
    """

    # Nombre base para separar apellidos y nombres:
    # - Si es RUC 20 usamos el REPRESENTANTE
    # - Si es RUC 10 usamos el solicitante (nombre completo)
    tipo_ruc = eval_ctx.get("tipo_ruc", "")
    if tipo_ruc == "20" and eval_ctx.get("representante"):
        nombre_persona = eval_ctx.get("representante", "")
    else:
        nombre_persona = eval_ctx.get("nombre", "")

    ape_pat, ape_mat, nombres = split_nombre_apellidos(nombre_persona)

    # Razón social = campo {{nombre}} (para RUC 20 será la empresa)
    razon_social = str(eval_ctx.get("nombre", "")).strip().upper()

    # Fechas en formato corto para Excel
    fecha_emision_str = fecha_cert.strftime("%d/%m/%Y") if fecha_cert else ""

    # FECHA DE EXPIRACIÓN = texto de {{vigencia}}
    # -> "INDETERMINADA" o "TEMPORAL (X) MESES"
    fecha_expiracion_str = vigencia_txt

    # Campos comunes desde la evaluación
    num_ds_val = str(eval_ctx.get("num_ds", "")).strip()
    ruc_empresa = str(eval_ctx.get("ruc", "")).strip()
    direccion = str(eval_ctx.get("direccion", "")).strip().upper()
    ubicacion = str(eval_ctx.get("ubicacion", "")).strip().upper()
    leyenda = str(eval_ctx.get("leyenda", "")).strip().upper()
    tipo_anuncio = str(eval_ctx.get("tipo_anuncio", "")).strip().upper()
    largo = eval_ctx.get("largo", "")
    alto = eval_ctx.get("alto", "")
    grosor = eval_ctx.get("grosor", "")
    altura_soporte = eval_ctx.get("altura", "")
    color = eval_ctx.get("colores", "")
    material = eval_ctx.get("material", "")
    num_caras = eval_ctx.get("num_cara", "")

    # Columnas exactamente como en el formato oficial
    columnas = [
        "EXP",
        "N° RECIBO",
        "RUC DE LA EMPRESA",
        "NÚMERO DE AUTORIZACION ",
        "FECHA DE EMISIÓN DE LA AUTORIZACION",
        "FECHA DE EXPIRACIÓN DE LA AUTORIZACION",
        "TIPO DE DOCUMENTO DE IDENTIDAD DEL SOLICITANTE",
        "NÚMERO DE DOCUMENTO DE IDENTIDAD DEL SOLICITANTE",
        "APELLIDO PATERNO DEL SOLICITANTE",
        "APELLIDO MATERNO DEL SOLICITANTE",
        "NOMBRE DEL SOLICITANTE",
        "RAZÓN SOCIAL DEL SOLICITANTE",
        "CARACTERISTICA FISICA DEL PANEL",
        "CARACTERISTICA TECNICA DEL PANEL",
        "TIPO DE ANUNCIPO PUBLICITARIO (Móvil, paneles, banderolas, etc.)",
        "DIRECCION",
        "UBICACIÓN",
        "LEYENDA",
        "LARGO",
        "ALTO",
        "ANCHO",
        "GROSOR",
        "LONGUITUD DE SOPORTES",
        "COLOR",
        "MATERIAL",
        "N° CARAS",
    ]

    nueva_fila = {
        "EXP": num_ds_val,
        "N° RECIBO": num_recibo,
        "RUC DE LA EMPRESA": ruc_empresa,
        "NÚMERO DE AUTORIZACION ": n_certificado,
        "FECHA DE EMISIÓN DE LA AUTORIZACION": fecha_emision_str,
        "FECHA DE EXPIRACIÓN DE LA AUTORIZACION": fecha_expiracion_str,
        "TIPO DE DOCUMENTO DE IDENTIDAD DEL SOLICITANTE": doc_tipo,
        "NÚMERO DE DOCUMENTO DE IDENTIDAD DEL SOLICITANTE": doc_num,
        "APELLIDO PATERNO DEL SOLICITANTE": ape_pat,
        "APELLIDO MATERNO DEL SOLICITANTE": ape_mat,
        "NOMBRE DEL SOLICITANTE": nombres,
        "RAZÓN SOCIAL DEL SOLICITANTE": razon_social,
        "CARACTERISTICA FISICA DEL PANEL": fisico,
        "CARACTERISTICA TECNICA DEL PANEL": tecnico,
        "TIPO DE ANUNCIPO PUBLICITARIO (Móvil, paneles, banderolas, etc.)": tipo_anuncio,
        "DIRECCION": direccion,
        "UBICACIÓN": ubicacion,
        "LEYENDA": leyenda,
        "LARGO": largo,
        "ALTO": alto,
        "ANCHO": "",   # por ahora no lo capturamos en el formulario
        "GROSOR": grosor,
        "LONGUITUD DE SOPORTES": altura_soporte,
        "COLOR": color,
        "MATERIAL": material,
        "N° CARAS": num_caras,
    }

    # Leemos o creamos el Excel
    if os.path.exists(BD_EXCEL_PATH):
        try:
            df = pd.read_excel(BD_EXCEL_PATH)
        except Exception:
            df = pd.DataFrame(columns=columnas)
    else:
        df = pd.DataFrame(columns=columnas)

    # Aseguramos que todas las columnas existan
    for col in columnas:
        if col not in df.columns:
            df[col] = ""

    # Agregamos la nueva fila
    df = pd.concat([df, pd.DataFrame([nueva_fila])], ignore_index=True)

    # Reordenamos columnas por si acaso
    df = df[columnas]

    df.to_excel(BD_EXCEL_PATH, index=False)


# ============ Módulo principal ============

def run_modulo_anuncios():
    st.header("📢 Anuncios Publicitarios – Evaluación y Certificado")

    # Estilos visuales tipo “card”
    st.markdown(
        """
        <style>
        .block-container { padding-top: 1.0rem; max-width: 900px; }
        .stButton>button {
            border-radius: 10px;
            padding: .55rem 1rem;
            font-weight: 600;
        }
        .card {
            border: 1px solid rgba(148, 163, 184, 0.35);
            border-radius: 16px;
            padding: 18px 20px;
            margin-bottom: 18px;
            background: rgba(15, 23, 42, 0.35);
        }
        .section-title {
            font-size: 0.95rem;
            text-transform: uppercase;
            letter-spacing: .08em;
            color: #9ca3af;
            margin-bottom: 0.35rem;
            font-weight: 600;
        }
        .section-divider {
            margin: 0.4rem 0 0.9rem 0;
            border-top: 1px solid rgba(148, 163, 184, 0.35);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="card">', unsafe_allow_html=True)

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

    # -------------------- Selección de tipo de anuncio --------------------
    st.markdown(
        '<div class="section-title">Tipo de anuncio publicitario</div>',
        unsafe_allow_html=True,
    )
    tipo_anuncio = st.selectbox(
        "Selecciona el tipo de anuncio",
        list(TEMPLATES_EVAL.keys()),
    )

    st.markdown('<hr class="section-divider" />', unsafe_allow_html=True)

    # ------------------------ MÓDULO 1 · EVALUACIÓN --------------------------
    with st.form("form_evaluacion"):

        st.markdown(
            '<div class="section-title">Evaluación del anuncio</div>',
            unsafe_allow_html=True,
        )

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

        # ---------------- Datos del solicitante ----------------
        st.markdown(
            '<div class="section-title">Datos del solicitante</div>',
            unsafe_allow_html=True,
        )

        tipo_ruc_label = st.radio(
            "Tipo de contribuyente",
            ["RUC 10 – Persona natural", "RUC 20 – Persona jurídica"],
            index=0,
            horizontal=True,
            key="tipo_ruc_radio",
        )
        es_ruc20 = tipo_ruc_label.startswith("RUC 20")
        tipo_ruc = "20" if es_ruc20 else "10"

        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input(
                "Solicitante (nombre completo o razón social)",
                max_chars=150,
                key="nombre_sol",
            )

            if es_ruc20:
                representante = st.text_input(
                    "Representante legal (solo RUC 20)",
                    max_chars=150,
                    key="representante_sol",
                    placeholder="Nombre completo del representante",
                )
            else:
                representante = ""

            direccion = st.text_input(
                "Dirección del solicitante",
                max_chars=200,
                key="direccion_sol",
            )

        with col2:
            ruc = st.text_input("RUC", max_chars=15, key="ruc_sol")

        st.markdown('<hr class="section-divider" />', unsafe_allow_html=True)

        # ---------------- Datos del anuncio ----------------
        st.markdown(
            '<div class="section-title">Datos del anuncio</div>',
            unsafe_allow_html=True,
        )

        col3, col4 = st.columns(2)
        with col3:
            largo = st.number_input(
                "Largo (m)", min_value=0.0, step=0.10, format="%.2f", key="largo_an"
            )
        with col4:
            alto = st.number_input(
                "Alto (m)", min_value=0.0, step=0.10, format="%.2f", key="alto_an"
            )

        if usa_grosor:
            grosor = st.number_input(
                "Grosor (m)", min_value=0.0, step=0.01, format="%.2f", key="grosor_an"
            )
        elif usa_altura_extra:
            altura_extra = st.number_input(
                "Altura (m)", min_value=0.0, step=0.10, format="%.2f", key="altura_an"
            )

        num_cara = st.number_input("N° de caras", min_value=1, step=1, key="caras_an")

        leyenda = st.text_area("Leyenda del anuncio", height=80, key="leyenda_an")

        col_colores, col_material = st.columns(2)
        with col_colores:
            colores = st.text_input("Colores principales", key="colores_an")
        with col_material:
            material = st.text_input("Material", key="material_an")

        ubicacion = st.text_input(
            "Ubicación del anuncio", max_chars=200, key="ubicacion_an"
        )

        st.markdown('<hr class="section-divider" />', unsafe_allow_html=True)

        # ---------------- Datos administrativos ----------------
        st.markdown(
            '<div class="section-title">Datos administrativos</div>',
            unsafe_allow_html=True,
        )
        col6, col7, col8 = st.columns(3)
        with col6:
            n_anuncio = st.text_input("N° de anuncio (ej. 001)", key="n_anuncio")
        with col7:
            num_ds = st.text_input("N° de expediente / DS (ej. 1234)", key="num_ds")
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
                key="anio_an",
            )

        st.markdown("")
        generar_eval = st.form_submit_button("📝 Generar evaluación (.docx)")

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
                # Extra solo para registro / Excel
                "tipo_ruc": tipo_ruc,               # "10" o "20"
                "tipo_ruc_label": tipo_ruc_label,   # texto del radio
                "representante": representante,     # solo si RUC 20
            }

            # guardamos datos para el certificado y luego para Excel
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
    st.markdown('<hr class="section-divider" />', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-title">Certificado de anuncio publicitario</div>',
        unsafe_allow_html=True,
    )

    eval_ctx = st.session_state.get("anuncio_eval_ctx")

    if eval_ctx:
        # Resumen
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

            st.markdown("### Datos para BD Excel (opcional)")
            col_doc1, col_doc2, col_rec = st.columns(3)
            with col_doc1:
                doc_tipo = st.selectbox(
                    "Tipo de documento del solicitante",
                    ["DNI", "CARNET DE EXTRANJERIA"],
                    key="doc_tipo",
                )
            with col_doc2:
                doc_num = st.text_input(
                    "N° documento del solicitante",
                    max_chars=20,
                    key="doc_num",
                )
            with col_rec:
                num_recibo = st.text_input(
                    "N° de recibo (solo BD, opcional)",
                    max_chars=30,
                    key="num_recibo",
                )

            generar_cert = st.form_submit_button("📜 Generar certificado (.docx)")
    else:
        st.info("Primero genera la **Evaluación** para poder armar el certificado.")
        generar_cert = False
        n_certificado = ""
        fecha_cert = None
        vigencia_tipo = "INDETERMINADA"
        meses_vigencia = 0
        ordenanza = ""
        fisico = ""
        tecnico = ""
        doc_tipo = "DNI"
        doc_num = ""
        num_recibo = ""

    # ---------- GENERACIÓN DEL WORD (CERTIFICADO) ----------
    if generar_cert and eval_ctx:
        if not n_certificado:
            st.error("Completa el N° de certificado.")
        else:
            if vigencia_tipo == "TEMPORAL":
                vigencia_txt = f"TEMPORAL ({int(meses_vigencia)}) MESES"
            else:
                vigencia_txt = "INDETERMINADA"

            cert_template_path = TEMPLATES_CERT.get(tipo_anuncio)
            if not cert_template_path:
                st.error("No se encontró plantilla de certificado para este tipo de anuncio.")
            else:
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
                    "grosor": eval_ctx.get("grosor", ""),
                    "altura": eval_ctx.get("altura", ""),
                    "color": eval_ctx.get("colores", ""),
                    "material": eval_ctx.get("material", ""),
                    "num_cara": eval_ctx.get("num_cara", ""),

                    "fisico": fisico,
                    "tecnico": tecnico,
                    "fecha": fecha_larga(fecha_cert) if fecha_cert else "",
                }

                try:
                    doc = DocxTemplate(cert_template_path)
                    doc.render(contexto_cert, autoescape=True)

                    buffer = BytesIO()
                    doc.save(buffer)
                    buffer.seek(0)

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

                    # Guardamos en sesión los datos necesarios para BD (pero NO lo escribimos aún)
                    st.session_state["anuncio_ultimo_cert_eval"] = eval_ctx
                    st.session_state["anuncio_ultimo_cert_meta"] = {
                        "vigencia_txt": vigencia_txt,
                        "n_certificado": n_certificado,
                        "fecha_cert": fecha_cert,
                        "fisico": fisico,
                        "tecnico": tecnico,
                        "doc_tipo": doc_tipo,
                        "doc_num": doc_num,
                        "num_recibo": num_recibo,
                    }

                except jinja2.TemplateSyntaxError as e:
                    st.error("Hay un error de sintaxis en la plantilla de CERTIFICADO.")
                    st.error(f"Plantilla: {cert_template_path}")
                    st.error(f"Mensaje: {e.message}")
                    st.error(f"Línea aproximada en el XML: {e.lineno}")
                except Exception as e:
                    st.error(f"Ocurrió un error al generar el certificado: {e}")

    # -------------------------------------------------------------------------
    #      OPCIÓN PARA GUARDAR EL ÚLTIMO CERTIFICADO EN LA BD
    # -------------------------------------------------------------------------
    st.markdown('<hr class="section-divider" />', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-title">Registrar último certificado en BD Excel</div>',
        unsafe_allow_html=True,
    )

    ult_eval = st.session_state.get("anuncio_ultimo_cert_eval")
    ult_meta = st.session_state.get("anuncio_ultimo_cert_meta")

    if not ult_eval or not ult_meta:
        st.info(
            "Todavía no hay un certificado reciente para registrar en la BD. "
            "Genera un certificado y luego podrás guardarlo aquí."
        )
    else:
        if st.button("💾 Guardar último certificado en BD Excel"):
            try:
                guardar_certificado_en_excel(
                    ult_eval,
                    ult_meta["vigencia_txt"],
                    ult_meta["n_certificado"],
                    ult_meta["fecha_cert"],
                    ult_meta["fisico"],
                    ult_meta["tecnico"],
                    ult_meta["doc_tipo"],
                    ult_meta["doc_num"],
                    ult_meta["num_recibo"],
                )
                st.success("Certificado registrado en la base de datos Excel.")
            except Exception as e:
                st.error(f"Ocurrió un error al guardar en Excel: {e}")

    # -------------------------------------------------------------------------
    #     VER / EDITAR / DESCARGAR BD (SI EXISTE EL EXCEL)
    # -------------------------------------------------------------------------
    st.markdown('<hr class="section-divider" />', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-title">Base de datos de certificados</div>',
        unsafe_allow_html=True,
    )

    if os.path.exists(BD_EXCEL_PATH):
        try:
            df_bd = pd.read_excel(BD_EXCEL_PATH)

            with st.expander("Ver / editar base de datos"):
                edited_df = st.data_editor(
                    df_bd,
                    num_rows="dynamic",
                    use_container_width=True,
                    key="editor_bd_certificados",
                )
                st.caption(
                    "Puedes editar celdas o agregar / eliminar filas. "
                    "Luego guarda los cambios en el archivo Excel."
                )

                if st.button("💾 Guardar cambios en Excel"):
                    try:
                        edited_df.to_excel(BD_EXCEL_PATH, index=False)
                        st.success("Cambios guardados correctamente en el Excel.")
                    except Exception as e:
                        st.error(f"No se pudo guardar el Excel: {e}")

            # Botón de descarga del archivo actual
            with open(BD_EXCEL_PATH, "rb") as f:
                st.download_button(
                    "⬇️ Descargar Excel de certificados",
                    data=f,
                    file_name=os.path.basename(BD_EXCEL_PATH),
                    mime=(
                        "application/vnd.openxmlformats-"
                        "officedocument.spreadsheetml.sheet"
                    ),
                )
        except Exception as e:
            st.error(f"No se pudo leer el Excel de BD: {e}")
    else:
        st.info(
            "Aún no existe el archivo de base de datos. "
            "Cuando guardes un certificado, se creará automáticamente."
        )

    st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    st.set_page_config(page_title="Anuncios Publicitarios", layout="centered")
    run_modulo_anuncios()
