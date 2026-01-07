# integraciones/app_consultas.py

import json
import streamlit as st

from integraciones.codart import (
    CodartAPIError,
    consultar_dni,
    consultar_ruc,
    dni_a_nombre_completo,
)

def run_modulo_consultas():
    st.header("📄 Consultas (DNI / RUC) – Pruebas")
    st.caption("Módulo interno para verificar consultas a RENIEC (DNI) y SUNAT (RUC).")

    tab_dni, tab_ruc = st.tabs(["DNI (RENIEC)", "RUC (SUNAT)"])

    # ---------------- DNI ----------------
    with tab_dni:
        st.subheader("Consulta por DNI")
        dni = st.text_input("DNI (8 dígitos)", max_chars=8, placeholder="Ej: 70238666")

        if st.button("🔎 Consultar DNI", use_container_width=True, key="btn_consulta_dni"):
            try:
                res = consultar_dni(dni)
                st.success("Consulta DNI OK")
                st.write("**Nombre completo:**", dni_a_nombre_completo(res) or "-")
                st.code(json.dumps(res, indent=2, ensure_ascii=False), language="json")
            except ValueError as e:
                st.error(str(e))
            except CodartAPIError as e:
                st.error(str(e))
            except Exception as e:
                st.error("Error inesperado")
                st.exception(e)

    # ---------------- RUC ----------------
    with tab_ruc:
        st.subheader("Consulta por RUC")
        ruc = st.text_input("RUC (11 dígitos)", max_chars=11, placeholder="Ej: 20538856674")

        if st.button("🔎 Consultar RUC", use_container_width=True, key="btn_consulta_ruc"):
            try:
                res = consultar_ruc(ruc)
                st.success("Consulta RUC OK")

                st.write("**Razón social:**", res.get("razon_social", "-"))
                st.write("**Dirección:**", res.get("direccion", "-"))
                st.write(
                    "**Estado / condición:**",
                    f"{res.get('estado','-')} / {res.get('condicion','-')}",
                )

                st.code(json.dumps(res, indent=2, ensure_ascii=False), language="json")
            except ValueError as e:
                st.error(str(e))
            except CodartAPIError as e:
                st.error(str(e))
            except Exception as e:
                st.error("Error inesperado")
                st.exception(e)
