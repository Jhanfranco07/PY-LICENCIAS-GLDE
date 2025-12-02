# comercio/app_permisos.py

import streamlit as st
from docxtpl import DocxTemplate
import pandas as pd
import io, os

# ========= Utils locales =========
def asegurar_dirs():
    os.makedirs("salidas", exist_ok=True)
    os.makedirs("plantillas", exist_ok=True)

def safe_filename_pretty(texto: str) -> str:
    prohibidos = '<>:"/\\|?*'
    limpio = ''.join('_' if c in prohibidos else c for c in str(texto))
    return limpio.replace('\n',' ').replace('\r',' ').strip()

def to_upper(s: str) -> str:
    return (s or "").strip().upper()

def fmt_fecha_corta(d) -> str:
    try:
        return pd.to_datetime(d).strftime("%d/%m/%Y")
    except Exception:
        return ""

def fmt_fecha_larga(d) -> str:
    meses = [
        "enero","febrero","marzo","abril","mayo","junio",
        "julio","agosto","setiembre","octubre","noviembre","diciembre"
    ]
    try:
        dt = pd.to_datetime(d)
        return f"{dt.day} de {meses[dt.month-1]} del {dt.year}"
    except Exception:
        return ""

def fmt_fecha_larga_de(d) -> str:
    t = fmt_fecha_larga(d)
    return t.replace(" del ", " de ") if t else t

def build_vigencia(fi, ff) -> str:
    ini = fmt_fecha_larga_de(fi)
    fin = fmt_fecha_larga_de(ff)
    return f"{ini} hasta el {fin}" if ini and fin else ""

def build_vigencia2(fi, ff) -> str:
    i = fmt_fecha_corta(fi)
    f = fmt_fecha_corta(ff)
    return f"{i} - {f}" if i and f else ""

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

def genero_labels(sexo: str):
    return (
        ("la señora", "la administrada", "identificada", "Sra")
        if sexo == "Femenino"
        else ("el señor", "el administrado", "identificado", "Sr")
    )

# ========= MÓDULO COMPLETO: evaluación + resolución + certificado =========
def run_permisos_comercio():
    asegurar_dirs()

    st.markdown(
        """
    <style>
    .block-container { padding-top: 1.0rem; max-width: 980px; }
    .stButton>button { border-radius: 10px; padding: .55rem 1rem; font-weight: 600; }
    .card { border: 1px solid #e5e7eb; border-radius: 16px; padding: 16px; margin-bottom: 12px; background: #0f172a08; }
    .hint { color:#64748b; font-size:.9rem; }
    </style>
    """,
        unsafe_allow_html=True,
    )

    st.title("🧾 Permisos Ambulatorios")
    st.caption(
        "Completa **una sola vez** (Evaluación). "
        "Resolución y Certificado reutilizan automáticamente esos datos."
    )

    # Rutas plantillas
    TPL_EVAL = "plantillas/evaluacion_ambulante.docx"
    TPL_RES_NUEVO = "plantillas/resolucion_nuevo.docx"
    TPL_RES_DENTRO = "plantillas/resolucion_dentro_tiempo.docx"
    TPL_RES_FUERA = "plantillas/resolucion_fuera_tiempo.docx"
    TPL_CERT = "plantillas/certificado.docx"

    # Carga de plantillas
    with st.expander("📎 Subir/actualizar plantillas .docx"):
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            f = st.file_uploader("Evaluación", type=["docx"], key="upl_eval")
            if f:
                open(TPL_EVAL, "wb").write(f.read())
                st.success("OK Evaluación")
        with c2:
            f = st.file_uploader("Res. NUEVO", type=["docx"], key="upl_res_n")
            if f:
                open(TPL_RES_NUEVO, "wb").write(f.read())
                st.success("OK Res. NUEVO")
        with c3:
            f = st.file_uploader("Res. DENTRO", type=["docx"], key="upl_res_d")
            if f:
                open(TPL_RES_DENTRO, "wb").write(f.read())
                st.success("OK Res. DENTRO")
        with c4:
            f = st.file_uploader("Res. FUERA", type=["docx"], key="upl_res_f")
            if f:
                open(TPL_RES_FUERA, "wb").write(f.read())
                st.success("OK Res. FUERA")
        with c5:
            f = st.file_uploader("Certificado", type=["docx"], key="upl_cert")
            if f:
                open(TPL_CERT, "wb").write(f.read())
                st.success("OK Certificado")

    # ---------- Módulo 1: EVALUACIÓN ----------
    st.header("Módulo 1 · Evaluación")
    st.markdown('<div class="card">', unsafe_allow_html=True)

    sexo = st.selectbox("Género de la persona*", ["Femenino", "Masculino"], key="sexo")

    cod_evaluacion = st.text_input(
        "Código de evaluación*",
        key="cod_evaluacion",
        value=st.session_state.get("cod_evaluacion", ""),
        placeholder="Ej: 121, 132, 142...",
    )
    nombre = st.text_input(
        "Solicitante (Nombre completo)*",
        key="nombre",
        value=st.session_state.get("nombre", ""),
    )
    dni = st.text_input(
        "DNI* (8 dígitos)",
        key="dni",
        value=st.session_state.get("dni", ""),
        max_chars=8,
        placeholder="########",
    )
    if dni and (not dni.isdigit() or len(dni) != 8):
        st.error("⚠️ DNI debe tener exactamente 8 dígitos numéricos")

    ds = st.text_input(
        "Documento Simple (DS)",
        key="ds",
        value=st.session_state.get("ds", ""),
        placeholder="Ej.: 123 (opcional)",
    )
    domicilio = st.text_input(
        "Domicilio fiscal*",
        key="domicilio",
        value=st.session_state.get("domicilio", ""),
    )

    c1, c2 = st.columns(2)
    with c1:
        fecha_ingreso = st.date_input(
            "Fecha de ingreso*",
            key="fecha_ingreso",
            value=st.session_state.get("fecha_ingreso", None),
            format="DD/MM/YYYY",
        )
    with c2:
        fecha_evaluacion = st.date_input(
            "Fecha de evaluación*",
            key="fecha_evaluacion",
            value=st.session_state.get("fecha_evaluacion", None),
            format="DD/MM/YYYY",
        )

    giro = st.text_input(
        "Giro solicitado*",
        key="giro",
        value=st.session_state.get("giro", ""),
    )
    ubicacion = st.text_input(
        "Ubicación*",
        key="ubicacion",
        value=st.session_state.get("ubicacion", ""),
        placeholder="Av./Jr./Parque..., sin 'Distrito de Pachacámac'",
    )
    referencia = st.text_input(
        "Referencia (opcional)",
        key="referencia",
        value=st.session_state.get("referencia", ""),
    )
    horario_eval = st.text_input(
        "Horario (opcional)",
        key="horario",
        value=st.session_state.get("horario", ""),
        placeholder="Ej.: 16:00 A 21:00 HORAS",
    )

    c3, c4 = st.columns(2)
    with c3:
        tiempo_num = st.number_input(
            "Tiempo*",
            key="tiempo",
            value=st.session_state.get("tiempo", 1),
            min_value=1,
            step=1,
        )
    with c4:
        plazo_unidad = st.selectbox(
            "Plazo*",
            ["meses", "años"],
            key="plazo",
            index=(
                ["meses", "años"].index(st.session_state.get("plazo", "meses"))
                if st.session_state.get("plazo", "meses") in ["meses", "años"]
                else 0
            ),
        )
    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("🧾 Generar Evaluación (.docx)"):
        falt = []
        req = {
            "cod_evaluacion": cod_evaluacion,
            "nombre": nombre,
            "dni": dni,
            "domicilio": domicilio,
            "giro": giro,
            "ubicacion": ubicacion,
        }
        for k, v in req.items():
            if not isinstance(v, str) or not v.strip():
                falt.append(k)
        if not fecha_ingreso:
            falt.append("fecha_ingreso")
        if not fecha_evaluacion:
            falt.append("fecha_evaluacion")
        if dni and (not dni.isdigit() or len(dni) != 8):
            st.error("DNI inválido")
        elif falt:
            st.error("Faltan campos: " + ", ".join(falt))
        else:
            ctx_eval = {
                "sexo": sexo,
                "cod_evaluacion": cod_evaluacion.strip(),
                "nombre": to_upper(nombre),
                "dni": dni.strip(),
                "ds": (ds or "").strip(),
                "domicilio": to_upper(domicilio),
                "fecha_ingreso": fmt_fecha_corta(fecha_ingreso),
                "fecha_evaluacion": fmt_fecha_larga(fecha_evaluacion),
                "giro": giro.strip(),
                "ubicacion": ubicacion.strip(),
                "referencia": to_upper(referencia),
                "horario": horario_eval.strip(),
                "tiempo": int(tiempo_num),
                "plazo": plazo_unidad,
                "fecha_ingreso_raw": str(fecha_ingreso) if fecha_ingreso else "",
                "fecha_evaluacion_raw": str(fecha_evaluacion) if fecha_evaluacion else "",
            }
            st.session_state["eval_ctx"] = ctx_eval
            anio_eval = pd.to_datetime(fecha_evaluacion).year
            render_doc(
                ctx_eval,
                f"EV. N° {cod_evaluacion}-{anio_eval}_{to_upper(nombre)}",
                TPL_EVAL,
            )

    st.markdown("---")

    # ---------- Módulo 2: RESOLUCIÓN ----------
    st.header("Módulo 2 · Resolución")
    st.markdown('<div class="card">', unsafe_allow_html=True)

    eva = st.session_state.get("eval_ctx", {})
    if not eva:
        st.warning(
            "Primero completa y guarda la **Evaluación**. "
            "Aquí solo pedimos lo propio de la Resolución."
        )
    else:
        res_tipo = st.selectbox(
            "Tipo de resolución / plantilla",
            ["NUEVO", "DENTRO_DE_TIEMPO", "FUERA_DE_TIEMPO"],
            index=0,
        )
        c0 = st.columns(2)
        with c0[0]:
            cod_resolucion = st.text_input(
                "N° de resolución*",
                key="cod_resolucion",
                value=st.session_state.get("cod_resolucion", ""),
                placeholder="Ej: 456",
            )
        with c0[1]:
            fecha_resolucion = st.date_input(
                "Fecha de resolución*",
                key="fecha_resolucion",
                value=st.session_state.get("fecha_resolucion", None),
                format="DD/MM/YYYY",
            )

        st.markdown("**Vigencia de la autorización**")
        cv = st.columns(2)
        with cv[0]:
            res_vig_ini = st.date_input(
                "Inicio*",
                key="res_vig_ini",
                value=st.session_state.get("res_vig_ini", None),
                format="DD/MM/YYYY",
            )
        with cv[1]:
            res_vig_fin = st.date_input(
                "Fin*",
                key="res_vig_fin",
                value=st.session_state.get("res_vig_fin", None),
                format="DD/MM/YYYY",
            )

        c6 = st.columns(2)
        with c6[0]:
            cod_certificacion = st.text_input(
                "N° de Certificado*",
                key="cod_certificacion",
                value=st.session_state.get("cod_certificacion", ""),
                placeholder="Ej: 789",
            )
        with c6[1]:
            antiguo_certificado = st.text_input(
                "N° de Certificado anterior (opcional)",
                key="antiguo_certificado",
                value=st.session_state.get("antiguo_certificado", ""),
                placeholder="Ej: 121",
            )
            if antiguo_certificado and not str(antiguo_certificado).isdigit():
                st.error("El certificado anterior debe ser solo números (ej.: 121)")

        genero, genero2, genero3, sr = genero_labels(eva.get("sexo", "Femenino"))
        st.markdown("**Datos importados desde Evaluación (solo lectura):**")
        st.write(
            {
                "DS": eva.get("ds", ""),
                "Nombre": eva.get("nombre", ""),
                "DNI": eva.get("dni", ""),
                "Domicilio": eva.get("domicilio", "") + "-PACHACAMAC",
                "Ubicación": eva.get("ubicacion", ""),
                "Giro": eva.get("giro", ""),
                "Horario": eva.get("horario", ""),
                "Código de Evaluación": eva.get("cod_evaluacion", ""),
                "Fecha de Evaluación": eva.get("fecha_evaluacion", ""),
                "Género -> (genero, genero2, genero3, sr)": (
                    genero,
                    genero2,
                    genero3,
                    sr,
                ),
            }
        )

        with st.expander("✏️ Ediciones rápidas (opcional)"):
            st.info("Por defecto NO necesitas tocar nada aquí.")
            eva["ds"] = st.text_input("DS (override opcional)", value=eva.get("ds", ""))
            eva["nombre"] = to_upper(
                st.text_input("Nombre (override opcional)", value=eva.get("nombre", ""))
            )
            eva["dni"] = st.text_input(
                "DNI (override opcional)", value=eva.get("dni", ""), max_chars=8
            )
            eva["domicilio"] = to_upper(
                st.text_input(
                    "Domicilio (override opcional)", value=eva.get("domicilio", "")
                )
            )
            eva["ubicacion"] = st.text_input(
                "Ubicación (override opcional)", value=eva.get("ubicacion", "")
            )
            eva["giro"] = st.text_input(
                "Giro (override opcional)", value=eva.get("giro", "")
            )
            eva["horario"] = st.text_input(
                "Horario (override opcional)", value=eva.get("horario", "")
            )

        def plantilla_por_tipo(t):
            return (
                TPL_RES_NUEVO
                if t == "NUEVO"
                else (TPL_RES_DENTRO if t == "DENTRO_DE_TIEMPO" else TPL_RES_FUERA)
            )

        if st.button("📄 Generar Resolución"):
            falt = []
            for k, v in {
                "cod_resolucion": cod_resolucion,
                "fecha_resolucion": fecha_resolucion,
                "vig_ini": res_vig_ini,
                "vig_fin": res_vig_fin,
                "cod_certificacion": cod_certificacion,
            }.items():
                if v in [None, ""]:
                    falt.append(k)

            if eva.get("dni") and (
                not str(eva["dni"]).isdigit() or len(str(eva["dni"])) != 8
            ):
                st.error("DNI inválido (8 dígitos)")
            elif not eva.get("horario"):
                st.error("Falta **Horario** en Evaluación (o en Ediciones rápidas).")
            elif falt:
                st.error("Faltan campos de Resolución: " + ", ".join(falt))
            else:
                anio_res = pd.to_datetime(fecha_resolucion).year
                vigencia_texto = build_vigencia(res_vig_ini, res_vig_fin)

                ctx_res = {
                    "cod_resolucion": str(cod_resolucion).strip(),
                    "fecha_resolucion": fmt_fecha_larga(fecha_resolucion),
                    "ds": str(eva.get("ds", "")).strip(),
                    "fecha_ingreso": fmt_fecha_corta(eva.get("fecha_ingreso_raw")),
                    "genero": genero,
                    "genero2": genero2,
                    "genero3": genero3,
                    "nombre": to_upper(eva.get("nombre", "")),
                    "dni": str(eva.get("dni", "")).strip(),
                    "domicilio": to_upper(eva.get("domicilio", ""))
                    + "-PACHACAMAC",
                    "giro": str(eva.get("giro", "")).strip(),
                    "ubicacion": str(eva.get("ubicacion", "")).strip(),
                    "horario": str(eva.get("horario", "")).strip(),
                    "cod_evaluacion": str(eva.get("cod_evaluacion", "")).strip(),
                    "fecha_evaluacion": eva.get("fecha_evaluacion", ""),
                    "cod_certificacion": str(cod_certificacion).strip(),
                    "vigencia": vigencia_texto,
                    "antiguo_certificado": str(antiguo_certificado or "").strip(),
                }

                tpl = plantilla_por_tipo(res_tipo)
                render_doc(
                    ctx_res,
                    f"RS. N° {ctx_res['cod_resolucion']}-{anio_res}_{to_upper(eva.get('nombre',''))}",
                    tpl,
                )

    st.markdown("---")

    # ---------- Módulo 3: CERTIFICADO ----------
    st.header("Módulo 3 · Certificado")
    st.markdown('<div class="card">', unsafe_allow_html=True)

    fecha_certificado = st.date_input(
        "Fecha del certificado*",
        key="fecha_certificado",
        value=st.session_state.get("fecha_certificado", None),
        format="DD/MM/YYYY",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("🪪 Generar Certificado"):
        eva = st.session_state.get("eval_ctx", {})
        if not eva:
            st.error(
                "Primero completa y guarda la **Evaluación** y la "
                "**Resolución** (vigencias)."
            )
        else:
            v_cod_cert = st.session_state.get("cod_certificacion", "")
            v_vig_ini = st.session_state.get("res_vig_ini", None)
            v_vig_fin = st.session_state.get("res_vig_fin", None)
            _, _, _, sr = genero_labels(eva.get("sexo", "Femenino"))

            falt = []
            if not v_cod_cert:
                falt.append("cod_certificacion")
            if not fecha_certificado:
                falt.append("fecha_certificado")
            if not eva.get("horario"):
                falt.append("horario (en Evaluación)")
            if not v_vig_ini or not v_vig_fin:
                falt.append("vigencia Inicio/Fin (en Resolución)")
            if falt:
                st.error("Faltan campos: " + ", ".join(falt))
            else:
                anio_cert = pd.to_datetime(fecha_certificado).year
                ctx_cert = {
                    "codigo_certificado": str(v_cod_cert).strip(),
                    "ds": str(eva.get("ds", "")).strip(),
                    "sr": sr,
                    "nombre": to_upper(eva.get("nombre", "")),
                    "dni": str(eva.get("dni", "")).strip(),
                    "ubicacion": str(eva.get("ubicacion", "")).strip(),
                    "referencia": to_upper(eva.get("referencia", "")),
                    "giro": str(eva.get("giro", "")).strip(),
                    "horario": str(eva.get("horario", "")).strip(),
                    "tiempo": eva.get("tiempo", ""),
                    "plazo": eva.get("plazo", ""),
                    "vigencia2": build_vigencia2(v_vig_ini, v_vig_fin),
                    "fecha_certificado": fmt_fecha_larga(fecha_certificado),
                }
                render_doc(
                    ctx_cert,
                    f"AU. {ctx_cert['codigo_certificado']}-{anio_cert}_{to_upper(eva.get('nombre',''))}",
                    TPL_CERT,
                )

    # ---------- Ayuda ----------
    with st.expander("ℹ️ Llaves por plantilla (qué se llena)"):
        st.markdown(
            """
**Evaluación (`evaluacion_ambulante.docx`):**  
{{cod_evaluacion}}, {{nombre}}, {{dni}}, {{ds}}, {{domicilio}},  
{{fecha_ingreso}}, {{fecha_evaluacion}}, {{giro}}, {{ubicacion}},  
{{referencia}}, {{horario}}, {{tiempo}}, {{plazo}}

**Resolución (NUEVO / DENTRO / FUERA):**  
{{cod_resolucion}}, {{fecha_resolucion}},  
{{ds}}, {{fecha_ingreso}},  
{{genero}}, {{genero2}}, {{genero3}},  
{{nombre}}, {{dni}}, {{domicilio}},  
{{giro}}, {{ubicacion}}, {{horario}},  
{{cod_evaluacion}}, {{fecha_evaluacion}},  
{{cod_certificacion}}, {{vigencia}}, {{antiguo_certificado}}

**Certificado (`certificado.docx`):**  
{{codigo_certificado}}, {{ds}},  
{{sr}}, {{nombre}}, {{dni}},  
{{ubicacion}}, {{referencia}}, {{giro}},  
{{horario}},  
{{tiempo}}, {{plazo}},  
{{vigencia2}},  
{{fecha_certificado}}
"""
        )


# Para usar este archivo solo (sin app_main.py)
if __name__ == "__main__":
    st.set_page_config(
        page_title="Permisos (Evaluación, Resolución, Certificado)",
        page_icon="🧾",
        layout="centered",
    )
    run_permisos_comercio()
