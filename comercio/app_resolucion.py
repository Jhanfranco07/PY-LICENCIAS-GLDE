# comercio/app_resolucion.py

import io
import os
from datetime import datetime

import streamlit as st
from docxtpl import DocxTemplate

from utils import (
    asegurar_dirs,
    safe_filename_pretty,
    fmt_fecha_corta,
    fmt_fecha_larga,
    build_vigencia,
    to_upper,
)

# Nombre de la key donde Evaluación guarda su contexto
EVAL_CTX_KEY = "comercio_eval_ctx"


# ========= helper para guardar DOCX =========
def render_doc(context: dict, filename_stem: str, plantilla_path: str):
    if not os.path.exists(plantilla_path):
        st.error(f"No se encontró la plantilla: {plantilla_path}")
        return

    doc = DocxTemplate(plantilla_path)
    doc.render(context)

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)

    out_name = f"{safe_filename_pretty(filename_stem)}.docx"

    # Guardar también en carpeta local "salidas"
    os.makedirs("salidas", exist_ok=True)
    with open(os.path.join("salidas", out_name), "wb") as f:
        f.write(buf.getvalue())

    st.success(f"Documento generado: {out_name}")
    st.download_button(
        "⬇️ Descargar .docx",
        buf,
        file_name=out_name,
        mime=(
            "application/vnd.openxmlformats-"
            "officedocument.wordprocessingml.document"
        ),
    )


# ========= MÓDULO: Resolución NUEVO =========
def run_resolucion_nuevo():
    asegurar_dirs()

    st.markdown(
        """
    <style>
    .block-container { padding-top: 1.2rem; max-width: 980px; }
    .stButton>button { border-radius: 10px; padding: .6rem 1rem; font-weight: 600; }
    .card { border: 1px solid #e5e7eb; border-radius: 16px; padding: 16px; margin-bottom: 12px; background: #0f172a08; }
    .subtle { color:#64748b; font-size:.9rem; }
    </style>
    """,
        unsafe_allow_html=True,
    )

    st.title("📄 Resolución Gerencial – Tipo NUEVO")
    st.caption(
        "Reutiliza datos de la Evaluación y añade la información propia de la Resolución."
    )

    # ----------------- contexto reutilizado de Evaluación -----------------
    eval_ctx = st.session_state.get(EVAL_CTX_KEY, {}) or {}

    def ev(key, default=""):
        """Conveniencia: trae de Evaluación como str si existe."""
        if key not in eval_ctx or eval_ctx[key] is None:
            return default
        return eval_ctx[key]

    with st.expander("👁 Datos importados desde Evaluación (solo lectura)"):
        if eval_ctx:
            st.json(eval_ctx)
        else:
            st.info("Aún no hay contexto de Evaluación en session_state.")

    # ----------------- plantilla -----------------
    TPL_PATH = "plantillas/resolucion_nuevo.docx"
    with st.expander("📎 Subir/actualizar plantilla .docx (opcional)"):
        up = st.file_uploader("Plantilla de resolución (NUEVO)", type=["docx"])
        if up:
            with open(TPL_PATH, "wb") as f:
                f.write(up.read())
            st.success("Plantilla actualizada.")

    # =================== BLOQUE: DATOS RESOLUCIÓN ===================
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Datos de la Resolución")

    c0 = st.columns(2)
    with c0[0]:
        cod_resolucion = st.text_input(
            "N° de resolución*", value="", placeholder="Ej: 456"
        )
    with c0[1]:
        fecha_resolucion = st.date_input(
            "Fecha de resolución*", value=None, format="DD/MM/YYYY"
        )

    st.markdown("---")
    st.subheader("Datos del administrado (reusados de Evaluación)")

    # Género (no viene de evaluación, pero podrías mapearlo si quisieras)
    cgen = st.columns(3)
    with cgen[0]:
        genero = st.selectbox(
            "género (texto en 'Visto')*",
            ["la señora", "el señor"],
        )
    with cgen[1]:
        genero2 = st.selectbox(
            "género2 (la/el administrad@)*",
            ["la administrada", "el administrado"],
        )
    with cgen[2]:
        genero3 = st.selectbox(
            "género3 (identificad@)*",
            ["identificada", "identificado"],
        )

    # Nombre / DNI / DS / Domicilio
    c1 = st.columns(2)
    with c1[0]:
        nombre = st.text_input(
            "Nombre completo*",
            value=str(ev("nombre", "")),
        )
    with c1[1]:
        dni = st.text_input(
            "DNI* (8 dígitos)",
            max_chars=8,
            placeholder="########",
            value=str(ev("dni", "")),
        )

    dni_error = None
    if dni and (not dni.isdigit() or len(dni) != 8):
        dni_error = "El DNI debe tener exactamente 8 dígitos numéricos."
        st.error(f"⚠️ {dni_error}")

    c2 = st.columns(2)
    with c2[0]:
        ds = st.text_input(
            "Documento Simple (DS)*",
            placeholder="Ej: 123",
            value=str(ev("ds", "")),
        )
    with c2[1]:
        fecha_ingreso = st.date_input(
            "Fecha de ingreso (DS)*", value=None, format="DD/MM/YYYY"
        )

    domicilio_val = str(ev("domicilio", ""))
    # si viene con "-PACHACAMAC" lo quitamos para editarlo limpio
    if domicilio_val.endswith("-PACHACAMAC"):
        domicilio_val = domicilio_val.replace("-PACHACAMAC", "")

    domicilio = st.text_input(
        "Domicilio fiscal*",
        placeholder="Calle / Av. ... (sin '-PACHACÁMAC')",
        value=domicilio_val,
    )

    # Giro / Ubicación
    c3 = st.columns(2)
    with c3[0]:
        ubicacion = st.text_input(
            "Ubicación*",
            placeholder="Ubicación exacta (sin 'Distrito de Pachacámac')",
            value=str(ev("ubicacion", "")),
        )
    with c3[1]:
        giro = st.text_input(
            "Giro solicitado*",
            placeholder="p.ej. VENTA DE BEBIDAS SALUDABLES Y SANDWICHES",
            value=str(ev("giro", "")),
        )

    # Horario, Rubro y Código de rubro (estos son propios de la Resolución)
    c4 = st.columns(2)
    with c4[0]:
        horario = st.text_input(
            "Horario*", placeholder="p.ej. 06:00 a 11:00"
        )
    with c4[1]:
        rubro = st.text_input(
            "Rubro*",
            placeholder="p.ej. Alimentos y bebidas",
        )

    c5 = st.columns(2)
    with c5[0]:
        codigo_rubro = st.text_input(
            "Código de rubro*",
            placeholder="p.ej. 005",
        )
    with c5[1]:
        cod_evaluacion = st.text_input(
            "Código de Evaluación*",
            value=str(ev("cod_evaluacion", "")),
            placeholder="Ej: 121",
        )

    fecha_evaluacion = st.date_input(
        "Fecha de Evaluación*", value=None, format="DD/MM/YYYY"
    )

    # =================== BLOQUE: VIGENCIA ===================
    st.markdown("**Vigencia de la autorización**")
    cv1 = st.columns(2)
    with cv1[0]:
        vig_ini = st.date_input("Inicio*", value=None, format="DD/MM/YYYY")
    with cv1[1]:
        vig_fin = st.date_input("Fin*", value=None, format="DD/MM/YYYY")

    # Tiempo y plazo reutilizados de Evaluación
    tiempo_default = ev("tiempo", 1)
    try:
        tiempo_default_int = int(tiempo_default) if tiempo_default else 1
    except Exception:
        tiempo_default_int = 1

    plazo_opciones = ["meses", "años"]
    plazo_default = str(ev("plazo", "meses"))
    plazo_index = (
        plazo_opciones.index(plazo_default)
        if plazo_default in plazo_opciones
        else 0
    )

    cv2 = st.columns(2)
    with cv2[0]:
        tiempo_num = st.number_input(
            "Tiempo* (dentro del paréntesis)",
            min_value=1,
            step=1,
            value=tiempo_default_int,
        )
    with cv2[1]:
        plazo_unidad = st.selectbox(
            "Plazo* (unidad de tiempo)",
            plazo_opciones,
            index=plazo_index,
        )

    # =================== BLOQUE: CERTIFICADO ===================
    c6 = st.columns(2)
    with c6[0]:
        cod_certificacion = st.text_input(
            "N° de Certificado*", value="", placeholder="Ej: 789"
        )
    with c6[1]:
        st.write("")  # espaciador

    st.markdown("</div>", unsafe_allow_html=True)

    # =================== BOTÓN GENERAR ===================
    if st.button("📄 Generar Resolución (NUEVO)"):
        faltantes = []
        for k, v in {
            "cod_resolucion": cod_resolucion,
            "fecha_resolucion": fecha_resolucion,
            "genero": genero,
            "genero2": genero2,
            "genero3": genero3,
            "ds": ds,
            "fecha_ingreso": fecha_ingreso,
            "nombre": nombre,
            "dni": dni,
            "domicilio": domicilio,
            "ubicacion": ubicacion,
            "giro": giro,
            "horario": horario,
            "rubro": rubro,
            "codigo_rubro": codigo_rubro,
            "cod_evaluacion": cod_evaluacion,
            "fecha_evaluacion": fecha_evaluacion,
            "vig_ini": vig_ini,
            "vig_fin": vig_fin,
            "tiempo": tiempo_num,
            "plazo": plazo_unidad,
            "cod_certificacion": cod_certificacion,
        }.items():
            if v is None or (isinstance(v, str) and not v.strip()):
                faltantes.append(k)

        reglas = []
        if dni_error:
            reglas.append(dni_error)

        if faltantes or reglas:
            if faltantes:
                st.error("Faltan campos obligatorios: " + ", ".join(faltantes))
            for r in reglas:
                st.error(f"Regla: {r}")
            return

        # =================== CONTEXTO PARA LA PLANTILLA ===================
        anio_res = fecha_resolucion.year
        vigencia_texto = build_vigencia(vig_ini, vig_fin)

        ctx = {
            # Encabezado
            "cod_resolucion": cod_resolucion.strip(),
            "fecha_resolucion": fmt_fecha_larga(fecha_resolucion),

            # Vistos / Considerandos
            "ds": ds.strip(),
            "fecha_ingreso": fmt_fecha_corta(fecha_ingreso),
            "genero": genero,
            "genero2": genero2,
            "genero3": genero3,
            "nombre": to_upper(nombre),
            "dni": dni.strip(),
            "domicilio": to_upper(domicilio) + "-PACHACAMAC",
            "giro": giro.strip(),
            "ubicacion": ubicacion.strip(),
            "horario": horario.strip(),
            "rubro": rubro.strip(),
            "codigo_rubro": codigo_rubro.strip(),

            # Referencia Evaluación
            "cod_evaluacion": cod_evaluacion.strip(),
            "fecha_evaluacion": fmt_fecha_larga(fecha_evaluacion),

            # Artículos
            "cod_certificacion": cod_certificacion.strip(),
            "vigencia": vigencia_texto,

            # Para el texto: "AUTORIZAR por el plazo de ({{tiempo}}) {{plazo}}"
            "tiempo": int(tiempo_num),
            "plazo": plazo_unidad,
        }

        nombre_arch = f"RES. N° {cod_resolucion}-{anio_res}_{to_upper(nombre)}"
        render_doc(ctx, nombre_arch, TPL_PATH)


# Para correr este módulo solo
if __name__ == "__main__":
    st.set_page_config(
        page_title="Resolución (NUEVO) - Comercio Ambulatorio",
        page_icon="📄",
        layout="centered",
    )
    run_resolucion_nuevo()
