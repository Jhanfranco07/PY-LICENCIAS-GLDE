# licencias/app_compatibilidad.py

import io
import os
from datetime import date

import streamlit as st
from docxtpl import DocxTemplate

from utils import (
    asegurar_dirs,
    fmt_fecha_larga,
    safe_filename_pretty,
    to_upper,
)

# -------------------- Catálogos --------------------

ZONAS = [
    ("RDM",   "Residencial de Densidad Media"),
    ("RDM-1", "Residencial de Densidad Media - 1"),
    ("RDM-e", "Residencial de Densidad Media Especial"),
    ("RDB",   "Residencial de Densidad Baja"),
    ("CZ",    "Comercio Zonal"),
    ("CV",    "Comercio Vecinal"),
    ("E1",    "Educación Básica"),
    ("E2",    "Educación Superior Tecnológica"),
    ("E3",    "Educación Superior Universitaria"),
    ("PTP",   "Protección y Tratamiento Paisajista"),
    ("ZRP",   "Zona de Recreación Pública"),
    ("ZRE",   "Zona de Reglamentación Especial"),
    ("ZTE",   "Zona de Tratamiento Especial"),
    ("ZTE 1", "Zona de Tratamiento Especial 1"),
    ("ZTE 2", "Zona de Tratamiento Especial 2"),
    ("CH",    "Casa Huerta"),
    ("CH-1",  "Casa Huerta 1"),
    ("CH-2",  "Casa Huerta 2"),
    ("CH-3",  "Casa Huerta 3"),
    ("OU",    "Otros Usos"),
    ("OU-C",  "Otros Usos - Cementerio"),
    ("OU-ZA", "Otros Usos - Zona Arqueológica"),
    ("H2",    "Centro de Salud"),
    ("H3",    "Hospital General"),
    ("A",     "Agrícola"),
    ("I2",    "Industria Liviana"),
    ("I4",    "Industria Pesada Básica"),
]
ZONAS_DICT = {c: d for c, d in ZONAS}

ORDENANZAS = [
    "ORD. 1117-MML",
    "ORD. 1146-MML",
    "ORD. 2236-MML",
    "ORD. 933-MML",
    "ORD. 270-2021-PACHACAMAC",
]


# -------------------- Helpers --------------------

def fecha_mes_abrev(d: date) -> str:
    """Ej: 16 DIC 2025 (para el paréntesis del expediente)."""
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
        # Importante para caracteres especiales (&, <, >, etc.)
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


# -------------------- Módulo principal --------------------

def run_modulo_compatibilidad():
    st.header("🏢 Evaluación de Compatibilidad de Uso")

    asegurar_dirs()
    os.makedirs("plantilla_compa", exist_ok=True)

    # rutas de plantillas
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

    with st.form("form_compatibilidad"):
        st.markdown('<div class="card">', unsafe_allow_html=True)

        # Encabezado: en Word será N° {{n_compa}}-2026-MDP-GLDE
        n_compa = st.text_input(
            "N° de compatibilidad*",
            max_chars=10,
            placeholder="Ej: 1010",
        )

        # ---------------- Datos del solicitante ----------------
        st.subheader("Datos del solicitante")
        c1, c2 = st.columns(2)
        with c1:
            persona = st.text_input("Solicitante*", max_chars=150)
            dni = st.text_input("DNI (si es persona natural)", max_chars=8)
        with c2:
            ruc = st.text_input("RUC (si es persona jurídica)", max_chars=11)
            nom_comercio = st.text_input("Nombre comercial (opcional)")

        direccion = st.text_input("Dirección*", max_chars=200)

        # ---------------- Datos de la actividad ----------------
        st.subheader("Datos de la actividad")
        giro = st.text_area("Uso comercial / giro*", height=60)

        # Ordenanzas (múltiple selección)
        ordenanzas_sel = st.multiselect(
            "Ordenanzas aplicables*",
            ORDENANZAS,
            default=["ORD. 2236-MML"],
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

        # Actividad general (cabecera de la tabla)
        actividad = st.text_input("Actividad general*", max_chars=200)
        codigo = st.text_input("Código de la actividad*", max_chars=50)

        # ----- Detalle de giros (filas de la tabla) -----
        st.markdown("**Detalle de giros de la tabla (pueden ser varios)**")
        num_giros = st.number_input(
            "N° de giros en la tabla",
            min_value=1,
            max_value=7,
            value=1,
            step=1,
            key="num_giros_tabla",
        )

        actividades_tabla = []
        for i in range(int(num_giros)):
            st.markdown(f"**Giro {i + 1}**")
            cg1, cg2, cg3 = st.columns([1.1, 2.8, 1.1])
            with cg1:
                codigo_i = st.text_input(
                    f"Código {i + 1}",
                    max_chars=50,
                    key=f"codigo_tabla_{i+1}",
                )
            with cg2:
                giro_i = st.text_input(
                    f"Giro {i + 1}",
                    max_chars=200,
                    key=f"giro_tabla_{i+1}",
                )
            with cg3:
                conf_i = st.selectbox(
                    f"Conformidad {i + 1}",
                    ["SI", "NO"],
                    key=f"conf_tabla_{i+1}",
                )

            actividades_tabla.append(
                {
                    "codigo": codigo_i,
                    "giro": giro_i,
                    "conf_si": "X" if conf_i == "SI" else "",
                    "conf_no": "X" if conf_i == "NO" else "",
                }
            )

        # Zonificación (única para todos los giros)
        zona_opciones = [f"{c} – {d}" for c, d in ZONAS]
        zona_sel = st.selectbox("Zonificación (código)*", zona_opciones)
        zona_codigo = zona_sel.split(" – ")[0]
        zona_desc = ZONAS_DICT.get(zona_codigo, "")

        st.markdown("---")
        st.subheader("Datos de expediente y fecha")

        ds = st.text_input("N° de expediente / DS*", max_chars=20)
        fecha_ds = st.date_input(
            "Fecha del expediente",
            value=date.today(),
        )
        fecha_doc = st.date_input(
            "Fecha del documento",
            value=date.today(),
        )

        st.markdown('</div>', unsafe_allow_html=True)

        generar = st.form_submit_button("🧾 Generar compatibilidad (.docx)")

    # Si aún no se envía el formulario, no hago nada más
    if not generar:
        return

    # --------- Validaciones básicas ---------
    faltantes = []
    for key, val in {
        "n_compa": n_compa,
        "persona": persona,
        "direccion": direccion,
        "giro": giro,
        "area": area,
        "itse": itse,
        "certificador": certificador,
        "tipo_licencia": tipo_licencia,
        "actividad": actividad,
        "codigo": codigo,
        "zona": zona_codigo,
        "ds": ds,
    }.items():
        if isinstance(val, str) and not val.strip():
            faltantes.append(key)

    # Ordenanzas y fechas
    if not ordenanzas_sel:
        faltantes.append("ordenanzas")
    if not fecha_ds:
        faltantes.append("fecha_ds")
    if not fecha_doc:
        faltantes.append("fecha_doc")

    # Validar cada giro de la tabla
    for idx, fila in enumerate(actividades_tabla, start=1):
        if not str(fila.get("codigo", "")).strip():
            faltantes.append(f"codigo_giro_{idx}")
        if not str(fila.get("giro", "")).strip():
            faltantes.append(f"giro_{idx}")

    if faltantes:
        st.error("Faltan campos obligatorios: " + ", ".join(faltantes))
        return

    # DNI / RUC con “--------------------” cuando falte
    dni_val = dni.strip()
    ruc_val = ruc.strip()
    if dni_val and not ruc_val:
        ruc_val = "--------------------"
    elif ruc_val and not dni_val:
        dni_val = "--------------------"
    elif not dni_val and not ruc_val:
        dni_val = "--------------------"
        ruc_val = "--------------------"

    # Nombre comercial vacío
    nom_com_val = nom_comercio.strip() or "--------------------"

    # Ordenanzas unidas por coma
    ordenanza_texto = ", ".join(ordenanzas_sel)

    # Preparamos la lista para la tabla (en mayúsculas donde corresponde)
    actividades_tabla_ctx = []
    for fila in actividades_tabla:
        actividades_tabla_ctx.append(
            {
                "codigo": fila["codigo"].strip(),
                "giro": to_upper(fila["giro"]),
                "conf_si": fila["conf_si"],
                "conf_no": fila["conf_no"],
            }
        )

    # Contexto para la plantilla
    ctx = {
        # Encabezado
        "n_compa": n_compa,                     # N° {{n_compa}}-2026-MDP-GLDE

        # Datos del solicitante
        "persona": to_upper(persona),
        "dni": dni_val,
        "ruc": ruc_val,
        "nom_comercio": to_upper(nom_com_val),
        "direccion": to_upper(direccion),

        # Datos de la actividad
        "giro": to_upper(giro),
        "ordenanza": ordenanza_texto,
        "area": area,
        "itse": itse,
        "certificador": certificador,
        "tipo_licencia": tipo_licencia,

        # Cabecera de la tabla
        "actividad": to_upper(actividad),
        "codigo": codigo,

        # Zona (única para todos los giros)
        "zona": zona_codigo,
        "zona_desc": zona_desc,

        # Expediente y fechas
        "ds": ds,
        "fecha_ds": fecha_mes_abrev(fecha_ds),
        "fecha_actual": fmt_fecha_larga(fecha_doc),

        # Detalle de giros para la tabla
        # En Word usarás:
        # {% for fila in actividades_tabla %}
        #   {{ fila.codigo }} / {{ fila.giro }} / {{ zona }} / {{ fila.conf_si }} ...
        # {% endfor %}
        "actividades_tabla": actividades_tabla_ctx,
    }

    # Elegir plantilla según tipo de licencia
    if "INDETERMINADA" in tipo_licencia:
        tpl_path = TPL_COMP_INDETERMINADA
    else:
        tpl_path = TPL_COMP_TEMPORAL

    # Nombre del archivo: {{n_compa}} - 2026 - {{persona}}
    base_name = f"{n_compa} - 2026 - {to_upper(persona)}"
    render_doc(ctx, base_name, tpl_path)


if __name__ == "__main__":
    st.set_page_config(page_title="Compatibilidad de Uso", layout="centered")
    run_modulo_compatibilidad()
