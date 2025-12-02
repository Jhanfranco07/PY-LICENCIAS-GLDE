# comercio/app_resolucion.py

import streamlit as st
from docxtpl import DocxTemplate
from datetime import datetime
import io, os

from utils import (
    asegurar_dirs, safe_filename_pretty,
    fmt_fecha_corta, fmt_fecha_larga, fmt_fecha_larga_de,
    build_vigencia, to_upper
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
    with open(os.path.join("salidas", out_name), "wb") as f:
        f.write(buf.getvalue())
    st.success(f"Documento generado: {out_name}")
    st.download_button(
        "⬇️ Descargar .docx",
        buf,
        file_name=out_name,
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
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
        "Variables comunes con Evaluación + específicas de Resolución "
        "(género y vigencia según tus reglas)."
    )

    # Plantilla
    TPL_PATH = "plantillas/resolucion_nuevo.docx"
    with st.expander("📎 Subir/actualizar plantilla .docx (opcional)"):
        up = st.file_uploader("Plantilla de resolución (NUEVO)", type=["docx"])
        if up:
            with open(TPL_PATH, "wb") as f:
                f.write(up.read())
            st.success("Plantilla actualizada.")

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

    # Selecciones exactas de género
    cgen = st.columns(3)
    with cgen[0]:
        genero = st.selectbox(
            "género (texto en 'Visto')*", ["la señora", "el señor"]
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

    c1 = st.columns(2)
    with c1[0]:
        nombre = st.text_input("Nombre completo*", value="")
    with c1[1]:
        dni = st.text_input("DNI* (8 dígitos)", max_chars=8, placeholder="########")
    dni_error = None
    if dni and (not dni.isdigit() or len(dni) != 8):
        dni_error = "El DNI debe tener exactamente 8 dígitos numéricos."
        st.error(f"⚠️ {dni_error}")

    c2 = st.columns(2)
    with c2[0]:
        ds = st.text_input("Documento Simple (DS)*", placeholder="Ej: 123")
    with c2[1]:
        fecha_ingreso = st.date_input(
            "Fecha de ingreso (DS)*", value=None, format="DD/MM/YYYY"
        )

    domicilio = st.text_input(
        "Domicilio fiscal*", placeholder="Calle / Av. ... (sin '-PACHACÁMAC')"
    )
    c3 = st.columns(2)
    with c3[0]:
        ubicacion = st.text_input(
            "Ubicación*", placeholder="Ubicación exacta (sin 'Distrito de Pachacámac')"
        )
    with c3[1]:
        giro = st.text_input(
            "Giro solicitado*", placeholder="p.ej. venta de jugos"
        )

    c4 = st.columns(2)
    with c4[0]:
        horario = st.text_input(
            "Horario*", placeholder="p.ej. 08:00 a 18:00"
        )
    with c4[1]:
        rubro = st.text_input(
            "Rubro*", placeholder="p.ej. Alimentos y bebidas"
        )

    c5 = st.columns(2)
    with c5[0]:
        codigo_rubro = st.text_input(
            "Código de rubro*", placeholder="p.ej. A1-03"
        )
    with c5[1]:
        cod_evaluacion = st.text_input(
            "Código de Evaluación*", value="", placeholder="Ej: 121"
        )

    fecha_evaluacion = st.date_input(
        "Fecha de Evaluación*", value=None, format="DD/MM/YYYY"
    )

    # Vigencia
    st.markdown("**Vigencia de la autorización**")
    cv = st.columns(2)
    with cv[0]:
        vig_ini = st.date_input("Inicio*", value=None, format="DD/MM/YYYY")
    with cv[1]:
        vig_fin = st.date_input("Fin*", value=None, format="DD/MM/YYYY")

    # Certificado
    c6 = st.columns(2)
    with c6[0]:
        cod_certificacion = st.text_input(
            "N° de Certificado*", value="", placeholder="Ej: 789"
        )
    with c6[1]:
        st.write("")  # espaciador

    st.markdown("</div>", unsafe_allow_html=True)

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
        else:
            anio_res = fecha_resolucion.year
            vigencia_texto = build_vigencia(
                vig_ini, vig_fin
            )  # "24 de setiembre de 2025 hasta el 24 de octubre de 2025"

            ctx = {
                # Encabezado
                "cod_resolucion": cod_resolucion.strip(),
                "fecha_resolucion": fmt_fecha_larga(
                    fecha_resolucion
                ),  # Pachacámac, 16 de setiembre del 2025

                # Vistos / Considerandos
                "ds": ds.strip(),
                "fecha_ingreso": fmt_fecha_corta(fecha_ingreso),  # 15/09/2025
                "genero": genero,  # la señora / el señor
                "genero2": genero2,  # la administrada / el administrado
                "genero3": genero3,  # identificada / identificado
                "nombre": to_upper(nombre),
                "dni": dni.strip(),
                "domicilio": to_upper(domicilio) + "-PACHACAMAC",
                "giro": giro.strip(),
                "ubicacion": ubicacion.strip(),  # usar {{ubicacion}} en plantilla
                "horario": horario.strip(),
                "rubro": rubro.strip(),
                "codigo_rubro": codigo_rubro.strip(),

                # Referencia Evaluación
                "cod_evaluacion": cod_evaluacion.strip(),
                "fecha_evaluacion": fmt_fecha_larga(
                    fecha_evaluacion
                ),  # 16 de setiembre del 2025

                # Artículos
                "cod_certificacion": cod_certificacion.strip(),
                "vigencia": vigencia_texto,
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
