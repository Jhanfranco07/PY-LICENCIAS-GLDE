# comercio/app_resolucion.py

import io
import os

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

    st.title("📄 Resolución Gerencial – Comercio Ambulatorio (Nuevo)")
    st.caption(
        "Reutiliza automáticamente datos de la Evaluación "
        "(giro, rubro, código, tiempo y plazo)."
    )

    # Plantilla
    TPL_PATH = "plantillas/resolucion_nuevo.docx"
    with st.expander("📎 Subir/actualizar plantilla .docx (opcional)"):
        up = st.file_uploader("Plantilla de resolución (NUEVO)", type=["docx"])
        if up:
            with open(TPL_PATH, "wb") as f:
                f.write(up.read())
            st.success("Plantilla actualizada.")

    # =================== DATOS IMPORTADOS DESDE EVALUACIÓN ===================
    eval_ctx = st.session_state.get("comercio_eval_ctx")

    if eval_ctx:
        with st.expander("🧾 Datos importados desde Evaluación (solo lectura):"):
            resumen = {
                "DS": eval_ctx.get("ds", ""),
                "Nombre": eval_ctx.get("nombre", ""),
                "DNI": eval_ctx.get("dni", ""),
                "Domicilio": eval_ctx.get("domicilio", ""),
                "Ubicación": eval_ctx.get("ubicacion", ""),
                "Giro": eval_ctx.get("giro", ""),
                "Horario": eval_ctx.get("horario", ""),
                "Código de Evaluación": eval_ctx.get("cod_evaluacion", ""),
                "Fecha de Evaluación": fmt_fecha_larga(
                    eval_ctx["fecha_evaluacion"]
                )
                if eval_ctx.get("fecha_evaluacion")
                else "",
                "Tiempo": eval_ctx.get("tiempo", ""),
                "Plazo": eval_ctx.get("plazo", ""),
                "Rubro": eval_ctx.get("rubro", ""),
                "Código de rubro": eval_ctx.get("codigo_rubro", ""),
            }
            st.json(resumen)
    else:
        st.info(
            "Todavía no hay datos cargados desde la Evaluación. "
            "Primero genera la Evaluación (con tiempo/plazo y rubro)."
        )

    # =================== FORMULARIO RESOLUCIÓN ===================
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
    st.subheader("Datos del administrado")

    # Género (se define aquí)
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

    # Datos básicos (prefill con evaluación si existe)
    c1 = st.columns(2)
    with c1[0]:
        nombre = st.text_input(
            "Nombre completo*",
            value=eval_ctx.get("nombre", "") if eval_ctx else "",
        )
    with c1[1]:
        dni = st.text_input(
            "DNI* (8 dígitos)",
            max_chars=8,
            placeholder="########",
            value=eval_ctx.get("dni", "") if eval_ctx else "",
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
            value=eval_ctx.get("ds", "") if eval_ctx else "",
        )
    with c2[1]:
        fecha_ingreso = st.date_input(
            "Fecha de ingreso (DS)*",
            value=eval_ctx.get("fecha_ingreso") if eval_ctx else None,
            format="DD/MM/YYYY",
        )

    domicilio = st.text_input(
        "Domicilio fiscal*",
        placeholder="Calle / Av. ... (sin '-PACHACÁMAC')",
        value=eval_ctx.get("domicilio", "").replace("-PACHACAMAC", "")
        if eval_ctx
        else "",
    )

    c3 = st.columns(2)
    with c3[0]:
        ubicacion = st.text_input(
            "Ubicación*",
            placeholder="Ubicación exacta (sin 'Distrito de Pachacámac')",
            value=eval_ctx.get("ubicacion", "") if eval_ctx else "",
        )
    with c3[1]:
        giro = st.text_input(
            "Giro solicitado*",
            placeholder="Texto de giro (ya viene de Evaluación)",
            value=eval_ctx.get("giro", "") if eval_ctx else "",
        )

    c4 = st.columns(2)
    with c4[0]:
        horario = st.text_input(
            "Horario*",
            placeholder="p.ej. 06:00 a 11:00",
            value=eval_ctx.get("horario", "") if eval_ctx else "",
        )
    with c4[1]:
        # Solo mostramos rubro y código que ya vienen de Evaluación
        rubro = str(eval_ctx.get("rubro", "")) if eval_ctx else ""
        codigo_rubro = str(eval_ctx.get("codigo_rubro", "")) if eval_ctx else ""
        st.text_input(
            "Rubro (solo lectura)",
            value=rubro,
            disabled=True,
        )
        st.text_input(
            "Código de rubro (solo lectura)",
            value=codigo_rubro,
            disabled=True,
        )

    c5 = st.columns(2)
    with c5[0]:
        cod_evaluacion = st.text_input(
            "Código de Evaluación*",
            value=eval_ctx.get("cod_evaluacion", "") if eval_ctx else "",
            placeholder="Ej: 121",
        )
    with c5[1]:
        fecha_evaluacion = st.date_input(
            "Fecha de Evaluación*",
            value=eval_ctx.get("fecha_evaluacion") if eval_ctx else None,
            format="DD/MM/YYYY",
        )

    # Vigencia de la autorización
    st.markdown("**Vigencia de la autorización**")
    cv1 = st.columns(2)
    with cv1[0]:
        vig_ini = st.date_input("Inicio*", value=None, format="DD/MM/YYYY")
    with cv1[1]:
        vig_fin = st.date_input("Fin*", value=None, format="DD/MM/YYYY")

    # Certificado
    c6 = st.columns(2)
    with c6[0]:
        cod_certificacion = st.text_input(
            "N° de Certificado*",
            value="",
            placeholder="Ej: 789",
        )
    with c6[1]:
        st.write("")  # espaciador

    st.markdown("</div>", unsafe_allow_html=True)

    # =================== BOTÓN GENERAR ===================
    if st.button("📄 Generar Resolución"):
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
            "cod_evaluacion": cod_evaluacion,
            "fecha_evaluacion": fecha_evaluacion,
            "vig_ini": vig_ini,
            "vig_fin": vig_fin,
            "cod_certificacion": cod_certificacion,
        }.items():
            if v is None or (isinstance(v, str) and not v.strip()):
                faltantes.append(k)

        reglas = []
        if dni_error:
            reglas.append(dni_error)

        if not eval_ctx:
            reglas.append(
                "No se encontraron datos de Evaluación en memoria. "
                "Primero genera la Evaluación (tiempo, plazo, rubro, etc.)."
            )
        else:
            tiempo = eval_ctx.get("tiempo")
            plazo = eval_ctx.get("plazo")
            rubro = eval_ctx.get("rubro")
            codigo_rubro = eval_ctx.get("codigo_rubro")
            if tiempo in (None, "") or not plazo:
                reglas.append(
                    "La Evaluación no tiene 'tiempo' y/o 'plazo'. "
                    "Vuelve a generar la Evaluación y luego la Resolución."
                )
            if not rubro or not codigo_rubro:
                reglas.append(
                    "La Evaluación no tiene 'rubro' y/o 'código de rubro'. "
                    "Vuelve a generar la Evaluación seleccionando un rubro."
                )

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
            "rubro": str(eval_ctx.get("rubro", "")),
            "codigo_rubro": str(eval_ctx.get("codigo_rubro", "")),

            # Referencia Evaluación
            "cod_evaluacion": cod_evaluacion.strip(),
            "fecha_evaluacion": fmt_fecha_larga(fecha_evaluacion),

            # Artículos
            "cod_certificacion": cod_certificacion.strip(),
            "vigencia": vigencia_texto,

            # Plazo: AUTORIZAR por el plazo de ({{tiempo}}) {{plazo}}, ...
            "tiempo": eval_ctx.get("tiempo"),
            "plazo": eval_ctx.get("plazo"),
        }

        nombre_arch = (
            f"RES. N° {cod_resolucion}-{anio_res}_{to_upper(nombre)}"
        )
        render_doc(ctx, nombre_arch, TPL_PATH)


# Para correr este módulo solo
if __name__ == "__main__":
    st.set_page_config(
        page_title="Resolución (NUEVO) - Comercio Ambulatorio",
        page_icon="📄",
        layout="centered",
    )
    run_resolucion_nuevo()
