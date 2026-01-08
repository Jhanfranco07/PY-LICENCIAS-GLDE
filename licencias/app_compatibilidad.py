# licencias/app_compatibilidad.py

import io
import os
from datetime import date

import streamlit as st
from docxtpl import DocxTemplate

from integraciones.codart import (
    CodartAPIError,
    consultar_dni,
    consultar_ruc,
    dni_a_nombre_completo,
)

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
    """Renderiza la plantilla Word y muestra botón de descarga."""
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


# -------------------- Callbacks (autocompletar) --------------------

def _set_flash(kind: str, text: str):
    st.session_state["_flash_kind"] = kind
    st.session_state["_flash_text"] = text


def _autocompletar_con_dni():
    st.session_state["_last_action"] = "dni"
    try:
        dni = (st.session_state.get("dni") or "").strip()
        res = consultar_dni(dni)
        nombre = (dni_a_nombre_completo(res) or "").strip()
        if not nombre:
            _set_flash("warning", "RENIEC respondió, pero no llegó el nombre.")
            return
        st.session_state["persona"] = nombre
        _set_flash("success", "Solicitante actualizado con RENIEC (DNI).")
    except (ValueError, CodartAPIError) as e:
        _set_flash("error", str(e))
    except Exception as e:
        _set_flash("error", f"Error inesperado consultando DNI: {e}")


def _autocompletar_con_ruc():
    st.session_state["_last_action"] = "ruc"
    try:
        ruc = (st.session_state.get("ruc") or "").strip()
        res = consultar_ruc(ruc)
        razon = (res.get("razon_social") or "").strip()
        if not razon:
            _set_flash("warning", "SUNAT respondió, pero no llegó la razón social.")
            return
        st.session_state["persona"] = razon
        _set_flash("success", "Solicitante actualizado con SUNAT (RUC).")
    except (ValueError, CodartAPIError) as e:
        _set_flash("error", str(e))
    except Exception as e:
        _set_flash("error", f"Error inesperado consultando RUC: {e}")


# -------------------- Módulo principal --------------------

def run_modulo_compatibilidad():
    st.header("🏢 Evaluación de Compatibilidad de Uso")

    asegurar_dirs()
    os.makedirs("plantilla_compa", exist_ok=True)

    # rutas fijas de las plantillas
    TPL_COMP_INDETERMINADA = "plantilla_compa/compatibilidad_indeterminada.docx"
    TPL_COMP_TEMPORAL = "plantilla_compa/compatibilidad_temporal.docx"

    # Defaults
    st.session_state.setdefault("persona", "")
    st.session_state.setdefault("dni", "")
    st.session_state.setdefault("ruc", "")
    st.session_state.setdefault("_flash_kind", "")
    st.session_state.setdefault("_flash_text", "")
    st.session_state.setdefault("_last_action", "")

    # Estilos visuales
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

    # Flash message (si hubo autocompletar)
    if st.session_state.get("_flash_text"):
        kind = st.session_state.get("_flash_kind", "")
        txt = st.session_state.get("_flash_text", "")
        if kind == "success":
            st.success(txt)
        elif kind == "warning":
            st.warning(txt)
        elif kind == "error":
            st.error(txt)
        else:
            st.info(txt)
        # limpiar para que no se repita siempre
        st.session_state["_flash_kind"] = ""
        st.session_state["_flash_text"] = ""

    # ---------- Control de Nº de giros (fuera del form) ----------
    st.markdown('<div class="card">', unsafe_allow_html=True)

    st.markdown(
        '<div class="section-title">Detalle de giros de la tabla</div>',
        unsafe_allow_html=True,
    )
    st.caption("Puedes registrar varios giros en la tabla de compatibilidad.")
    n_giros_tabla = st.number_input(
        "N° de giros en la tabla",
        min_value=1,
        max_value=10,
        step=1,
        key="n_giros_tabla",
    )
    n_giros_tabla = int(n_giros_tabla)

    st.markdown('<hr class="section-divider" />', unsafe_allow_html=True)

    # ---------- Formulario principal ----------
    with st.form("form_compatibilidad"):

        # ---------------- Encabezado ----------------
        st.markdown(
            '<div class="section-title">Encabezado</div>',
            unsafe_allow_html=True,
        )
        n_compa = st.text_input(
            "N° de compatibilidad*",
            max_chars=10,
            placeholder="Ej: 1010",
        )

        st.markdown('<hr class="section-divider" />', unsafe_allow_html=True)

        # ---------------- Datos del solicitante ----------------
        st.markdown(
            '<div class="section-title">Datos del solicitante</div>',
            unsafe_allow_html=True,
        )

        c1, c2 = st.columns(2)
        with c1:
            st.text_input("Solicitante*", max_chars=150, key="persona")
            st.text_input("DNI (si es persona natural)", max_chars=8, key="dni")
        with c2:
            st.text_input("RUC (si es persona jurídica)", max_chars=11, key="ruc")
            nom_comercio = st.text_input("Nombre comercial (opcional)")

        # Botones: usan callback (NO rompe session_state)
        b1, b2 = st.columns(2)
        with b1:
            st.form_submit_button(
                "⚡ Autocompletar solicitante con DNI",
                use_container_width=True,
                on_click=_autocompletar_con_dni,
            )
        with b2:
            st.form_submit_button(
                "⚡ Autocompletar solicitante con RUC",
                use_container_width=True,
                on_click=_autocompletar_con_ruc,
            )

        direccion = st.text_input("Dirección*", max_chars=200)

        st.markdown('<hr class="section-divider" />', unsafe_allow_html=True)

        # ---------------- Datos de la actividad ----------------
        st.markdown(
            '<div class="section-title">Datos de la actividad</div>',
            unsafe_allow_html=True,
        )

        giro = st.text_area(
            "Uso comercial / giro (texto general)*",
            height=80,
            placeholder="Ej: SERVICIO DE CONSULTORIOS ODONTOLÓGICOS",
        )

        col_ord, col_area = st.columns([2, 1])
        with col_ord:
            ordenanzas_sel = st.multiselect(
                "Ordenanzas aplicables*",
                ORDENANZAS,
                default=["ORD. 2236-MML"],
            )
        with col_area:
            area = st.text_input("Área comercial (m²)*", max_chars=50)

        col_itse, col_cert, col_tipo = st.columns(3)
        with col_itse:
            itse = st.selectbox(
                "ITSE / Nivel de riesgo*",
                [
                    "ITSE RIESGO MUY ALTO",
                    "ITSE RIESGO ALTO",
                    "ITSE RIESGO MEDIO",
                ],
            )
        with col_cert:
            certificador = st.selectbox(
                "Certificador de riesgo*",
                [
                    "AMBROSIO BARRIOS P.",
                    "SILVANO BELITO T.",
                ],
            )
        with col_tipo:
            tipo_licencia_simple = st.selectbox(
                "Tipo de licencia*",
                ["INDETERMINADA", "TEMPORAL"],
            )

        st.markdown('<hr class="section-divider" />', unsafe_allow_html=True)

        # ---------------- Actividad general + zonificación ----------------
        st.markdown(
            '<div class="section-title">Actividad general y zonificación</div>',
            unsafe_allow_html=True,
        )

        col_act1, col_act2 = st.columns([3, 1])
        with col_act1:
            actividad = st.text_input("Actividad general*", max_chars=200)
        with col_act2:
            codigo = st.text_input("Código de la actividad*", max_chars=50)

        zona_opciones = [f"{c} – {d}" for c, d in ZONAS]
        zona_sel = st.selectbox("Zonificación (código)*", zona_opciones)
        zona_codigo = zona_sel.split(" – ")[0]
        zona_desc = ZONAS_DICT.get(zona_codigo, "")

        st.markdown('<hr class="section-divider" />', unsafe_allow_html=True)

        # ---------------- Giros de la tabla ----------------
        st.markdown(
            '<div class="section-title">Giros de la tabla de compatibilidad</div>',
            unsafe_allow_html=True,
        )

        actividades_tabla = []
        for i in range(n_giros_tabla):
            st.markdown(f"**Giro {i + 1}**")
            cg1, cg2, cg3 = st.columns([2, 4, 2])
            with cg1:
                cod_giro = st.text_input(
                    f"Código giro {i + 1}",
                    max_chars=50,
                    key=f"codigo_giro_{i + 1}",
                )
            with cg2:
                giro_desc = st.text_input(
                    f"Descripción del giro {i + 1}",
                    max_chars=200,
                    key=f"desc_giro_{i + 1}",
                )
            with cg3:
                conf_giro = st.selectbox(
                    f"Conformidad giro {i + 1}",
                    ["SI", "NO"],
                    key=f"conf_giro_{i + 1}",
                )

            fila_conf_si = "X" if conf_giro == "SI" else ""
            fila_conf_no = "X" if conf_giro == "NO" else ""

            actividades_tabla.append(
                {
                    "codigo": cod_giro,
                    "giro": to_upper(giro_desc),
                    "conf_si": fila_conf_si,
                    "conf_no": fila_conf_no,
                }
            )

        st.markdown('<hr class="section-divider" />', unsafe_allow_html=True)

        # ---------------- Datos de expediente y fecha ----------------
        st.markdown(
            '<div class="section-title">Datos de expediente y fecha</div>',
            unsafe_allow_html=True,
        )

        col_exp1, col_exp2 = st.columns([2, 1])
        with col_exp1:
            ds = st.text_input("N° de expediente / DS*", max_chars=20)
        with col_exp2:
            fecha_ds = st.date_input(
                "Fecha del expediente",
                value=date.today(),
            )

        fecha_doc = st.date_input(
            "Fecha del documento",
            value=date.today(),
        )

        st.markdown("")
        generar = st.form_submit_button("🧾 Generar compatibilidad (.docx)")

    st.markdown("</div>", unsafe_allow_html=True)

    # Si el submit fue por autocompletar, NO generamos (evita consumir lógica y errores)
    if st.session_state.get("_last_action") in ("dni", "ruc"):
        st.session_state["_last_action"] = ""
        st.stop()

    # Si no se presionó generar, salir
    if not generar:
        return

    # Mapear opción corta de licencia al texto completo del documento
    tipo_licencia_map = {
        "INDETERMINADA": "LICENCIA DE FUNCIONAMIENTO INDETERMINADA",
        "TEMPORAL": "LICENCIA DE FUNCIONAMIENTO TEMPORAL (01 AÑO)",
    }
    tipo_licencia = tipo_licencia_map.get(tipo_licencia_simple, "")

    # --------- Validaciones básicas ---------
    persona = (st.session_state.get("persona") or "").strip()
    dni = (st.session_state.get("dni") or "").strip()
    ruc = (st.session_state.get("ruc") or "").strip()

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

    if not ordenanzas_sel:
        faltantes.append("ordenanzas")
    if not fecha_ds:
        faltantes.append("fecha_ds")
    if not fecha_doc:
        faltantes.append("fecha_doc")

    if faltantes:
        st.error("Faltan campos obligatorios: " + ", ".join(faltantes))
        return

    # DNI / RUC con “--------------------” cuando falte
    dni_val = dni
    ruc_val = ruc
    if dni_val and not ruc_val:
        ruc_val = "--------------------"
    elif ruc_val and not dni_val:
        dni_val = "--------------------"
    elif not dni_val and not ruc_val:
        dni_val = "--------------------"
        ruc_val = "--------------------"

    # Nombre comercial vacío
    nom_com_val = (nom_comercio or "").strip() or "--------------------"

    ordenanza_texto = ", ".join(ordenanzas_sel)

    # --------- Contexto para la plantilla ---------
    ctx = {
        "n_compa": n_compa,
        "persona": to_upper(persona),
        "dni": dni_val,
        "ruc": ruc_val,
        "nom_comercio": to_upper(nom_com_val),
        "direccion": to_upper(direccion),
        "giro": to_upper(giro),

        "ordenanza": ordenanza_texto,
        "area": area,
        "itse": itse,
        "certificador": certificador,
        "tipo_licencia": tipo_licencia,

        "actividad": to_upper(actividad),
        "codigo": codigo,

        "zonaona": zona_codigo,  # (si tu plantilla usa {{zona}} mejor usa la clave "zona")
        "zona": zona_codigo,
        "zona_desc": to_upper(zona_desc),

        "ds": ds,
        "fecha_ds": fecha_mes_abrev(fecha_ds),
        "fecha_actual": fmt_fecha_larga(fecha_doc),

        "actividades_tabla": actividades_tabla,
    }

    # Elegir plantilla según tipo de licencia
    if "LICENCIA DE FUNCIONAMIENTO INDETERMINADA" in tipo_licencia:
        tpl_path = TPL_COMP_INDETERMINADA
    else:
        tpl_path = TPL_COMP_TEMPORAL

    base_name = f"{n_compa} - 2026 - {to_upper(persona)}"
    render_doc(ctx, base_name, tpl_path)


if __name__ == "__main__":
    st.set_page_config(page_title="Compatibilidad de Uso", layout="centered")
    run_modulo_compatibilidad()
