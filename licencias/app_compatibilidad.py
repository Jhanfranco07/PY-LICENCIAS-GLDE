# licencias/app_compatibilidad.py

import io
from datetime import date

import streamlit as st
from docxtpl import DocxTemplate

from utils import (
    asegurar_dirs,
    fmt_fecha_larga,
    safe_filename_pretty,
    to_upper,
)

# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------
def fecha_mes_abrev(d: date) -> str:
    """
    Devuelve: 16 DIC 2025 (para el paréntesis del EXPEDIENTE).
    """
    if not d:
        return ""
    meses = ["ENE", "FEB", "MAR", "ABR", "MAY", "JUN",
             "JUL", "AGO", "SET", "OCT", "NOV", "DIC"]
    return f"{d.day:02d} {meses[d.month - 1]} {d.year}"


def render_doc(context: dict, filename_stem: str, plantilla_path: str):
    try:
        doc = DocxTemplate(plantilla_path)
    except Exception as e:
        st.error(f"No se pudo abrir la plantilla: {plantilla_path}")
        st.error(str(e))
        return

    try:
        doc.render(context, autoescape=True)
    except Exception as e:
        st.error("Ocurrió un error al rellenar la plantilla.")
        st.error(str(e))
        return

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    out_name = safe_filename_pretty(filename_stem) + ".docx"

    st.success(f"Documento generado: {out_name}")
    st.download_button(
        "⬇️ Descargar compatibilidad en Word",
        data=buffer,
        file_name=out_name,
        mime=(
            "application/vnd.openxmlformats-"
            "officedocument.wordprocessingml.document"
        ),
    )


# -------------------------------------------------------------------
# Módulo principal
# -------------------------------------------------------------------
def run_modulo_compatibilidad():
    st.header("🏢 Evaluación de Compatibilidad de Uso")

    asegurar_dirs()

    # Rutas de las 2 plantillas
    TPL_COMP_INDETERMINADA = "plantilla_compa/compatibilidad_indeterminada.docx"
    TPL_COMP_TEMPORAL = "plantilla_compa/compatibilidad_temporal.docx"

    st.markdown(
        """
        <style>
        .block-container { padding-top: 1.0rem; max-width: 900px; }
        .stButton>button { border-radius: 10px; padding: .55rem 1rem; font-weight: 600; }
        .card { border: 1px solid #e5e7eb; border-radius: 16px;
                padding: 16px; margin-bottom: 12px; background: #0f172a08; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Subir / actualizar plantillas
    with st.expander("📎 Subir / actualizar plantillas .docx"):
        c1, c2 = st.columns(2)
        with c1:
            up_ind = st.file_uploader(
                "Compatibilidad – INDETERMINADA",
                type=["docx"],
                key="upl_comp_ind",
            )
            if up_ind:
                with open(TPL_COMP_INDETERMINADA, "wb") as f:
                    f.write(up_ind.read())
                st.success("Plantilla INDETERMINADA actualizada.")
        with c2:
            up_temp = st.file_uploader(
                "Compatibilidad – TEMPORAL (01 AÑO)",
                type=["docx"],
                key="upl_comp_temp",
            )
            if up_temp:
                with open(TPL_COMP_TEMPORAL, "wb") as f:
                    f.write(up_temp.read())
                st.success("Plantilla TEMPORAL actualizada.")

    # ------------------------ FORMULARIO ------------------------
    with st.form("form_compatibilidad"):
        st.markdown('<div class="card">', unsafe_allow_html=True)

        # Encabezado: N° {{n_compa}}-2026-MDP-GLDE (el -2026 lo pones tú en la plantilla)
        n_compa = st.text_input(
            "N° de compatibilidad*",
            max_chars=10,
            placeholder="Ej: 1010",
        )

        st.subheader("Datos del solicitante")
        c1, c2 = st.columns(2)
        with c1:
            persona = st.text_input("Solicitante*", max_chars=150)
            dni = st.text_input("DNI (si es persona natural)", max_chars=8)
        with c2:
            ruc = st.text_input("RUC (si es persona jurídica)", max_chars=11)
            nom_comercio = st.text_input("Nombre comercial (opcional)")

        direccion = st.text_input("Dirección*", max_chars=200)

        st.subheader("Datos de la actividad")
        giro = st.text_area("Uso comercial / giro*", height=60)

        # Ordenanza (combo)
        ordenanza = st.selectbox(
            "Ordenanza*",
            [
                "ORDENANZA MUNICIPAL N° 2236-MML, ORD. 933-MML, ORD. 270-2021-PACHACAMAC",
                "ORD. MUNIC. N° 2236-MML, ORD. 933-MML",
                "ORD. MUNIC. N° 2236-MML, ORD. 933-MML, OTRA ORDENANZA",
            ],
        )

        area = st.text_input("Área comercial (m²)*", max_chars=50)

        itse = st.selectbox(
            "ITSE / Nivel de riesgo*",
            [
                "ITSE RIESGO MUY ALTO",
                "ITSE RIESGO ALTO",
                "ITSE RIESGO MEDIO",
            ],
        )

        certificador = st.selectbox(
            "Certificador de riesgo*",
            [
                "AMBROSIO BARRIOS P.",
                "SILVANO BELITO T.",
            ],
        )

        tipo_licencia = st.selectbox(
            "Tipo de licencia*",
            [
                "LICENCIA DE FUNCIONAMIENTO INDETERMINADA",
                "LICENCIA DE FUNCIONAMIENTO TEMPORAL (01 AÑO)",
            ],
        )

        st.markdown("---")
        st.subheader("Actividad específica y zonificación")

        actividad = st.text_input("Actividad general*", max_chars=200)
        codigo = st.text_input("Código de la actividad*", max_chars=50)

        zona = st.selectbox(
            "Zonificación (código)*",
            ["RDM", "CV", "CZ", "CZ1", "CZ2", "CZ3"],
        )

        conformidad = st.selectbox("Conformidad*", ["SI", "NO"])

        st.markdown("---")
        st.subheader("Datos de expediente y fecha")

        ds = st.text_input("N° de expediente / DS*", max_chars=20)
        fecha_ds = st.date_input(
            "Fecha del expediente (para el paréntesis)",
            value=date.today(),
        )
        fecha_doc = st.date_input(
            "Fecha del documento (Pachacamac, ...)",
            value=date.today(),
        )

        st.markdown('</div>', unsafe_allow_html=True)

        generar = st.form_submit_button("🧾 Generar compatibilidad (.docx)")

    # ------------------- PROCESAMIENTO -------------------
    if not generar:
        return

    faltantes = []
    for key, val in {
        "n_compa": n_compa,
        "persona": persona,
        "direccion": direccion,
        "giro": giro,
        "ordenanza": ordenanza,
        "area": area,
        "itse": itse,
        "certificador": certificador,
        "tipo_licencia": tipo_licencia,
        "actividad": actividad,
        "codigo": codigo,
        "zona": zona,
        "ds": ds,
    }.items():
        if isinstance(val, str) and not val.strip():
            faltantes.append(key)

    if not fecha_ds:
        faltantes.append("fecha_ds")
    if not fecha_doc:
        faltantes.append("fecha_doc")

    if faltantes:
        st.error("Faltan campos obligatorios: " + ", ".join(faltantes))
        return

    # DNI / RUC
    dni_val = dni.strip()
    ruc_val = ruc.strip()
    if dni_val and not ruc_val:
        ruc_val = "--------------------"
    elif ruc_val and not dni_val:
        dni_val = "--------------------"
    elif not dni_val and not ruc_val:
        dni_val = "--------------------"
        ruc_val = "--------------------"

    # Nombre comercial vacío -> “--------------------”
    nom_com_val = nom_comercio.strip() or "--------------------"

    # Conformidad -> X en SI / NO
    conf_si = "X" if conformidad == "SI" else ""
    conf_no = "X" if conformidad == "NO" else ""

    ctx = {
        "n_compa": n_compa,                     # <-- solo número, el “-2026” va en la plantilla
        "persona": to_upper(persona),
        "dni": dni_val,
        "ruc": ruc_val,
        "nom_comercio": to_upper(nom_com_val),
        "direccion": to_upper(direccion),
        "giro": to_upper(giro),
        "ordenanza": ordenanza,
        "area": area,
        "itse": itse,
        "certificador": certificador,
        "tipo_licencia": tipo_licencia,
        "actividad": to_upper(actividad),
        "codigo": codigo,
        "zona": zona,
        "ds": ds,
        "fecha_ds": fecha_mes_abrev(fecha_ds),
        "fecha_actual": fmt_fecha_larga(fecha_doc),
        "conf_si": conf_si,
        "conf_no": conf_no,
    }

    # Elegir plantilla según el tipo de licencia
    if "INDETERMINADA" in tipo_licencia:
        tpl_path = TPL_COMP_INDETERMINADA
    else:
        tpl_path = TPL_COMP_TEMPORAL

    # Nombre del archivo: ECU 1010_SAYAS RIVERA...
    base_name = f"ECU {n_compa}_{to_upper(persona)}"
    render_doc(ctx, base_name, tpl_path)


if __name__ == "__main__":
    st.set_page_config(page_title="Compatibilidad de Uso", layout="centered")
    run_modulo_compatibilidad()
