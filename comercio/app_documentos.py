# comercio/app_documentos.py

import pandas as pd
import streamlit as st

from integraciones.codart import (
    CodartAPIError,
    consultar_dni,
    dni_a_nombre_completo,
)
from comercio.sheets_comercio import (
    append_documento,
    leer_documentos,
)
# 👇 Usamos las opciones de giro tal como en Evaluación
from comercio.app_permisos import GIROS_OPCIONES


def _to_upper(s: str) -> str:
    return (s or "").strip().upper()


def text_input_upper(label: str, key: str, **kwargs) -> str:
    """
    Text input que siempre guarda y devuelve en MAYÚSCULAS.
    No usar para DNI / celulares.
    """
    v = st.text_input(label, key=key, **kwargs)
    v_up = _to_upper(v)
    if v != v_up:
        st.session_state[key] = v_up
    return v_up


def _fmt_fecha_corta(d) -> str:
    try:
        return pd.to_datetime(d).strftime("%d/%m/%Y")
    except Exception:
        return ""


# ===== Autocomplete DNI solo para este módulo DS =====
def _init_dni_state_ds():
    st.session_state.setdefault("dni_ds_msg", "")


def _cb_autocomplete_dni_ds():
    dni_val = (st.session_state.get("dni_ds") or "").strip()
    st.session_state["dni_ds_msg"] = ""

    if not dni_val:
        return

    try:
        res = consultar_dni(dni_val)
        nombre = dni_a_nombre_completo(res)

        if nombre:
            st.session_state["nombre_ds"] = _to_upper(nombre)
            st.session_state[
                "dni_ds_msg"
            ] = "✅ DNI válido: nombre autocompletado."
        else:
            st.session_state["dni_ds_msg"] = (
                "⚠️ DNI OK, pero no se encontró nombre."
            )
    except ValueError as e:
        st.session_state["dni_ds_msg"] = f"⚠️ {e}"
    except CodartAPIError as e:
        st.session_state["dni_ds_msg"] = f"⚠️ {e}"
    except Exception as e:
        st.session_state["dni_ds_msg"] = f"⚠️ Error consultando DNI: {e}"


def run_documentos_comercio():
    _init_dni_state_ds()

    st.markdown(
        """
    <style>
    .block-container { padding-top: 1.0rem; max-width: 980px; }
    .card { border: 1px solid #e5e7eb; border-radius: 16px; padding: 16px; margin-bottom: 12px; background: #0f172a08; }
    .stButton>button { border-radius: 10px; padding: .55rem 1rem; font-weight: 600; }
    </style>
    """,
        unsafe_allow_html=True,
    )

    st.title("📥 Registro de Documentos Simples – Comercio Ambulatorio")
    st.caption(
        "Registra los Documentos Simples (D.S.) que luego se usarán en la "
        "Evaluación y Autorización de comercio ambulatorio."
    )

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Nuevo Documento Simple")

    # ------------------------------------------------------------------
    # Tipo de solicitud / Asunto
    # ------------------------------------------------------------------
    tipo_asunto = st.selectbox(
        "Tipo de solicitud*",
        [
            "RENOVACION",
            "SOLICITUD DE COMERCIO AMBULATORIO",
            "OTROS (especificar)",
        ],
        key="tipo_asunto_ds",
    )

    asunto_otro = ""
    if tipo_asunto == "OTROS (especificar)":
        asunto_otro = text_input_upper(
            "Asunto (texto libre)*",
            key="asunto_otro",
            placeholder="Ej.: Solicitud de constancia, queja, etc.",
        )

    # ------------------------------------------------------------------
    # Datos básicos
    # ------------------------------------------------------------------
    c1, c2 = st.columns(2)
    with c1:
        fecha_ingreso = st.date_input(
            "Fecha de ingreso*",
            key="fecha_ingreso_ds",
            value=None,
            format="DD/MM/YYYY",
        )
    with c2:
        num_ds = st.text_input(
            "N° de Documento Simple*",
            key="num_ds",
            placeholder="Ej.: 17168-2025",
        )

    # DNI + nombre con autocomplete
    c3, c4 = st.columns([2, 3])
    with c3:
        dni = st.text_input(
            "DNI (8 dígitos)*",
            key="dni_ds",
            max_chars=8,
            placeholder="########",
            on_change=_cb_autocomplete_dni_ds,
        )
    with c4:
        nombre = text_input_upper(
            "Nombre y apellido*",
            key="nombre_ds",
            value=st.session_state.get("nombre_ds", ""),
        )

    msg_dni = (st.session_state.get("dni_ds_msg") or "").strip()
    if msg_dni:
        if msg_dni.startswith("✅"):
            st.success(msg_dni)
        else:
            st.warning(msg_dni)

    domicilio = text_input_upper("Domicilio fiscal*", key="domicilio_ds")

    # ------------------------------------------------------------------
    # Giro / motivo de la solicitud (condicional)
    # ------------------------------------------------------------------
    if tipo_asunto in ("RENOVACION", "SOLICITUD DE COMERCIO AMBULATORIO"):
        giro_label = st.selectbox(
            "Giro (según Ordenanza)*",
            GIROS_OPCIONES,
            key="giro_motivo_ds_select",
        )
        # Lo que se guarda en la hoja: GIRO O MOTIVO DE LA SOLICITUD
        giro_motivo = _to_upper(giro_label)
    else:
        giro_motivo = text_input_upper(
            "Giro o motivo de la solicitud*",
            key="giro_motivo_ds",
            placeholder="Describe el motivo de la solicitud",
        )

    ubicacion = text_input_upper(
        "Ubicación a solicitar*",
        key="ubicacion_ds",
        placeholder="Av./Jr./Parque ...",
    )

    celular = st.text_input(
        "N° de celular",
        key="celular_ds",
        placeholder="Ej.: 987654321",
    )

    procedencia = st.selectbox(
        "Procedente / Improcedente*",
        ["PROCEDENTE", "IMPROCEDENTE"],
        key="procedencia_ds",
    )

    c5, c6, c7 = st.columns(3)
    with c5:
        num_carta = text_input_upper("N° de carta", key="num_carta_ds")
    with c6:
        fecha_carta = st.date_input(
            "Fecha de la carta",
            key="fecha_carta_ds",
            value=None,
            format="DD/MM/YYYY",
        )
    with c7:
        fecha_notif = st.date_input(
            "Fecha de notificación",
            key="fecha_notif_ds",
            value=None,
            format="DD/MM/YYYY",
        )

    folios = text_input_upper("Folios", key="folios_ds")

    st.markdown("</div>", unsafe_allow_html=True)

    # ----------------- Botón GUARDAR D.S. -----------------
    if st.button("💾 Registrar Documento Simple"):
        falt = []

        # Asunto que se guarda en la columna ASUNTO
        asunto_final = (
            asunto_otro.strip()
            if tipo_asunto == "OTROS (especificar)"
            else tipo_asunto
        )

        if not fecha_ingreso:
            falt.append("fecha_ingreso")
        if not num_ds.strip():
            falt.append("num_ds")
        if not asunto_final:
            falt.append("asunto")
        if not nombre.strip():
            falt.append("nombre")
        if not dni.strip():
            falt.append("dni")
        if not domicilio.strip():
            falt.append("domicilio")
        if not giro_motivo.strip():
            falt.append("giro_motivo")
        if not ubicacion.strip():
            falt.append("ubicacion")

        if dni and (not dni.isdigit() or len(dni) != 8):
            st.error("DNI inválido: debe tener exactamente 8 dígitos.")
        elif falt:
            st.error("Faltan campos obligatorios: " + ", ".join(falt))
        else:
            try:
                append_documento(
                    fecha_ingreso=_fmt_fecha_corta(fecha_ingreso),
                    num_documento_simple=_to_upper(num_ds),
                    asunto=_to_upper(asunto_final),
                    nombre=_to_upper(nombre),
                    dni=dni.strip(),
                    domicilio_fiscal=_to_upper(domicilio),
                    giro_motivo=_to_upper(giro_motivo),
                    ubicacion_solicitar=_to_upper(ubicacion),
                    celular=celular.strip(),
                    procedencia=_to_upper(procedencia),
                    num_carta=_to_upper(num_carta),
                    fecha_carta=_fmt_fecha_corta(fecha_carta)
                    if fecha_carta
                    else "",
                    fecha_notificacion=_fmt_fecha_corta(fecha_notif)
                    if fecha_notif
                    else "",
                    folios=_to_upper(folios),
                    estado="PENDIENTE",
                )
                st.success("Documento Simple registrado correctamente.")
            except Exception as e:
                st.error(f"No se pudo registrar el Documento Simple: {e}")

    # ----------------- Vista rápida de la BD -----------------
    st.markdown("---")
    with st.expander("📊 Ver últimos Documentos registrados"):
        try:
            df = leer_documentos()
            if df.empty:
                st.info("Aún no hay documentos registrados.")
            else:
                st.dataframe(df.tail(50), use_container_width=True)
        except Exception as e:
            st.error(f"No se pudo leer la base de datos: {e}")


# Para usar este archivo solo (sin app_main.py)
if __name__ == "__main__":
    st.set_page_config(
        page_title="Documentos Simples – Comercio Ambulatorio",
        page_icon="📥",
        layout="centered",
    )
    run_documentos_comercio()
