# comercio/app_evaluacion.py

import streamlit as st
from docxtpl import DocxTemplate
from datetime import datetime
import io, os

from utils import (
    asegurar_dirs,
    fmt_fecha_corta, fmt_fecha_larga
)

# ===========================
# Helpers para guardar DOCX
# ===========================
def safe_filename_pretty(texto: str) -> str:
    """Permite un nombre legible: deja espacios y 'N°'; elimina caracteres prohibidos del SO."""
    prohibidos = '<>:"/\\|?*'
    limpio = ''.join('_' if c in prohibidos else c for c in str(texto))
    return limpio.replace('\n',' ').replace('\r',' ').strip()


def render_doc(context: dict, filename_stem: str, plantilla_path: str):
    if not os.path.exists(plantilla_path):
        st.error(f"No se encontró la plantilla: {plantilla_path}")
        return

    doc = DocxTemplate(plantilla_path)
    doc.render(context)

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    out_name = f"{safe_filename_pretty(filename_stem)}.docx"
    out_path = os.path.join("salidas", out_name)
    with open(out_path, "wb") as f:
        f.write(buffer.getvalue())

    st.success(f"Documento generado: {out_name}")
    st.download_button(
        "⬇️ Descargar .docx",
        data=buffer,
        file_name=out_name,
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )


# ===========================
# MÓDULO: Evaluación Comercio
# ===========================
def run_evaluacion_comercio():
    asegurar_dirs()

    st.markdown("""
    <style>
    .block-container { padding-top: 1.2rem; max-width: 900px; }
    .stButton>button { border-radius: 10px; padding: .6rem 1rem; font-weight: 600; }
    .card { border: 1px solid #e5e7eb; border-radius: 16px; padding: 16px; margin-bottom: 12px; background: #0f172a08; }
    </style>
    """, unsafe_allow_html=True)

    st.title("🧾 Evaluación de Comercio Ambulatorio")
    st.caption("Genera la Evaluación desde una plantilla .docx (docxtpl).")

    # --- Plantilla
    TPL_PATH = "plantillas/evaluacion_ambulante.docx"
    st.markdown("**Plantilla activa:** `plantillas/evaluacion_ambulante.docx`")
    if not os.path.exists(TPL_PATH):
        st.warning("Sube tu plantilla `.docx` con las llaves Jinja indicadas abajo.")

    tpl_upl = st.file_uploader("Subir/actualizar plantilla .docx", type=["docx"])
    if tpl_upl:
        with open(TPL_PATH, "wb") as f:
            f.write(tpl_upl.read())
        st.success("Plantilla actualizada.")

    # --- Formulario (manual)
    st.markdown('<div class="card">', unsafe_allow_html=True)

    # Código de evaluación (manual, sin autogenerado)
    cod_evaluacion = st.text_input(
        "Código de evaluación*",
        value="",
        placeholder="Ej: 121, 132, 142..."
    )

    nombre = st.text_input("Solicitante (Nombre completo)*")

    # DNI con validación estricta: 8 dígitos
    dni = st.text_input("DNI* (8 dígitos)", max_chars=8, placeholder="########")
    dni_error = None
    if dni and (not dni.isdigit() or len(dni) != 8):
        dni_error = "El DNI debe tener exactamente 8 dígitos numéricos."
        st.error(f"⚠️ {dni_error}")

    # Documento simple (DS) libre
    ds = st.text_input("Documento Simple (DS)", placeholder="Ej.: 123, 045, etc. (opcional)")

    domicilio = st.text_input("Domicilio fiscal*")

    c1, c2 = st.columns(2)
    with c1:
        fecha_ingreso = st.date_input("Fecha de ingreso*", value=None, format="DD/MM/YYYY")
    with c2:
        fecha_evaluacion = st.date_input("Fecha de evaluación*", value=None, format="DD/MM/YYYY")

    giro = st.text_area("Giro solicitado*", placeholder="Descripción del giro/actividad")
    ubicacion = st.text_input("Ubicación*", placeholder="Av. / Jr. / Parque ...")
    referencia = st.text_input("Referencia", placeholder="Opcional")

    c3, c4 = st.columns(2)
    with c3:
        tiempo_num = st.number_input(
            "Tiempo*", min_value=1, step=1,
            help="Solo número (1,2,3,...)"
        )
    with c4:
        plazo_unidad = st.selectbox(
            "Plazo*", ["meses", "años"],
            help="Unidad del tiempo autorizado"
        )

    st.markdown('</div>', unsafe_allow_html=True)

    # Botón generar
    if st.button("🧾 Generar Evaluación (.docx)"):
        # Validaciones mínimas
        faltantes = []
        for k, v in {
            "cod_evaluacion": cod_evaluacion,
            "nombre": nombre,
            "dni": dni,
            "domicilio": domicilio,
            "giro": giro,
            "ubicacion": ubicacion,
        }.items():
            if not isinstance(v, str) or not v.strip():
                faltantes.append(k)

        # Fechas requeridas
        if not fecha_ingreso:
            faltantes.append("fecha_ingreso")
        if not fecha_evaluacion:
            faltantes.append("fecha_evaluacion")

        # Reglas extra
        reglas_error = []
        if dni_error:
            reglas_error.append(dni_error)

        if faltantes or reglas_error:
            if faltantes:
                st.error("Faltan campos obligatorios: " + ", ".join(faltantes))
            for err in reglas_error:
                st.error(f"Regla: {err}")
        else:
            # Año desde la fecha de evaluación
            anio_eval = fecha_evaluacion.year if fecha_evaluacion else datetime.now().year

            # Contexto para docxtpl
            ctx = {
                "cod_evaluacion": cod_evaluacion.strip(),
                "nombre": nombre.strip().upper(),
                "dni": dni.strip(),
                "ds": (ds or "").strip(),
                "domicilio": domicilio.strip().upper(),
                "fecha_ingreso": fmt_fecha_corta(fecha_ingreso),
                "fecha_evaluacion": fmt_fecha_larga(fecha_evaluacion),
                "giro": giro.strip(),
                "ubicacion": ubicacion.strip(),
                "referencia": (referencia or "").strip().upper(),
                "tiempo": int(tiempo_num),
                "plazo": plazo_unidad,
            }

            # 🔹 Guardar contexto para reutilizar en Resolución
            st.session_state["comercio_eval_ctx"] = ctx

            nombre_archivo_pretty = (
                f"EV. N° {cod_evaluacion}-{anio_eval}_{nombre.strip().upper()}"
            )

            render_doc(ctx, nombre_archivo_pretty, TPL_PATH)



# Permite correr SOLO este módulo si quieres:
if __name__ == "__main__":
    st.set_page_config(
        page_title="Evaluación de Comercio Ambulatorio",
        page_icon="🧾",
        layout="centered"
    )
    run_evaluacion_comercio()
