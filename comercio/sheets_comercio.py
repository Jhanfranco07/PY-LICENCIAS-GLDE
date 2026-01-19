# sheets_comercio.py
"""
Manejo de Google Sheets para Comercio Ambulatorio (Evaluación + Autorización).

- Usa st.secrets["gcp_service_account"] como en ANUNCIOS.
- En UN solo Google Sheets se crean / usan dos hojas:
    • Evaluaciones_CA
    • Autorizaciones_CA
"""

from __future__ import annotations

from typing import List, Dict

import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials

# ---------------------------------------------------------------------------
# CONFIG BÁSICA
# ---------------------------------------------------------------------------

# 👉 PON AQUÍ el ID del Google Sheets de COMERCIO AMBULATORIO
SPREADSHEET_ID_COMERCIO = "1Sd9f0PTfGvFsOPQhA32hUp2idcdkX_LVYQ-bAX2nYU8"

EVAL_SHEET_NAME = "Evaluaciones_CA"
AUTO_SHEET_NAME = "Autorizaciones_CA"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# ---------------------------------------------------------------------------
# COLUMNAS
# ---------------------------------------------------------------------------

COLUMNAS_EVALUACION: List[str] = [
    "N°",
    "NUMERO DE DOCUMENTO SIMPLE",
    "NOMBRES Y APELLIDOS",
    "N° DE EVALUACIÓN",
    "FECHA",
    "N° DE RESOLUCIÓN",
    "FECHA DE RESOLUCIÓN",
    "N° DE AUTORIZACIÓN",
    "FECHA DE AUTORIZACION",
]

COLUMNAS_AUTORIZACION: List[str] = [
    "FECHA DE INGRESO",
    "D.S",
    "NOMBRE Y APELLIDO",
    "DNI",
    "GENERO",
    "DOMICILIO FISCAL",
    "CERTIFICADO ANTERIOR",
    "FECHA EMITIDA CERTIFICADO ANTERIOR",
    "FECHA DE CADUCIDAD CERTIFICADO ANTERIOR",
    "N° DE EVALUACION",
    "FECHA DE EVALUACION",
    "N° DE RESOLUCIÓN",
    "FECHA RESOLUCIÓN",
    "N° DE CERTIFICADO",
    "FECHA EMITIDA CERTIFICADO",
    "VIGENCIA DE AUTORIZACIÓN",
    "LUGAR DE VENTA",
    "REFERENCIA",
    "GIRO",
    "HORARIO",
    "N° TELEFONO",
]

# ---------------------------------------------------------------------------
# CLIENTE GSPREAD
# ---------------------------------------------------------------------------


@st.cache_resource
def _get_client() -> gspread.Client:
    """
    Crea el cliente de Google Sheets usando st.secrets["gcp_service_account"].
    """
    creds_info = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client


def _get_spreadsheet():
    client = _get_client()
    return client.open_by_key(SPREADSHEET_ID_COMERCIO)


def _get_worksheet(sheet_name: str, columnas: List[str]) -> gspread.Worksheet:
    """
    Devuelve la worksheet indicada. Si no existe, la crea.
    Si está vacía, escribe la fila de encabezados.
    """
    sh = _get_spreadsheet()
    try:
        ws = sh.worksheet(sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        ws = sh.add_worksheet(title=sheet_name, rows=1000, cols=len(columnas) + 2)

    values = ws.get_all_values()
    if not values:
        ws.update("A1", [columnas])

    return ws


# ---------------------------------------------------------------------------
# HELPERS GENÉRICOS
# ---------------------------------------------------------------------------


def _leer_df(sheet_name: str, columnas: List[str]) -> pd.DataFrame:
    ws = _get_worksheet(sheet_name, columnas)
    values = ws.get_all_values()

    if not values:
        return pd.DataFrame(columns=columnas)

    header = values[0]
    filas = values[1:]

    df = pd.DataFrame(filas, columns=header)

    for col in columnas:
        if col not in df.columns:
            df[col] = ""

    df = df[columnas]
    return df


def _escribir_df(sheet_name: str, columnas: List[str], df: pd.DataFrame) -> None:
    ws = _get_worksheet(sheet_name, columnas)

    df = df.copy()
    for col in columnas:
        if col not in df.columns:
            df[col] = ""
    df = df[columnas].fillna("")

    values = [df.columns.tolist()] + df.astype(str).values.tolist()

    ws.clear()
    ws.update("A1", values)


def _append_fila(
    sheet_name: str,
    columnas: List[str],
    fila: Dict[str, str],
    auto_numero_col: str | None = None,
) -> None:
    """
    Agrega una nueva fila:
    - 'fila' es un dict {columna: valor}
    - si auto_numero_col no es None, se rellena con correlativo (1,2,3,...)
    """
    df = _leer_df(sheet_name, columnas)

    nueva = {col: "" for col in columnas}
    for col, val in fila.items():
        if col in nueva:
            nueva[col] = val

    if auto_numero_col and auto_numero_col in nueva:
        nueva[auto_numero_col] = len(df) + 1

    df = pd.concat([df, pd.DataFrame([nueva])], ignore_index=True)
    _escribir_df(sheet_name, columnas, df)


# ---------------------------------------------------------------------------
# API PÚBLICA – EVALUACIONES
# ---------------------------------------------------------------------------


def leer_evaluaciones() -> pd.DataFrame:
    return _leer_df(EVAL_SHEET_NAME, COLUMNAS_EVALUACION)


def escribir_evaluaciones(df: pd.DataFrame) -> None:
    _escribir_df(EVAL_SHEET_NAME, COLUMNAS_EVALUACION, df)


def append_evaluacion(
    *,
    num_ds: str,
    nombre_completo: str,
    cod_evaluacion: str,
    fecha_eval: str,
    cod_resolucion: str = "",
    fecha_resolucion: str = "",
    num_autorizacion: str = "",
    fecha_autorizacion: str = "",
) -> None:
    """
    Agrega una fila a Evaluaciones_CA.
    Todas las fechas deben venir ya como string (ej. '16/01/2026').
    """
    fila = {
        "NUMERO DE DOCUMENTO SIMPLE": num_ds or "",
        "NOMBRES Y APELLIDOS": nombre_completo or "",
        "N° DE EVALUACIÓN": cod_evaluacion or "",
        "FECHA": fecha_eval or "",
        "N° DE RESOLUCIÓN": cod_resolucion or "",
        "FECHA DE RESOLUCIÓN": fecha_resolucion or "",
        "N° DE AUTORIZACIÓN": num_autorizacion or "",
        "FECHA DE AUTORIZACION": fecha_autorizacion or "",
    }

    _append_fila(
        EVAL_SHEET_NAME,
        COLUMNAS_EVALUACION,
        fila,
        auto_numero_col="N°",
    )


# ---------------------------------------------------------------------------
# API PÚBLICA – AUTORIZACIONES
# ---------------------------------------------------------------------------


def leer_autorizaciones() -> pd.DataFrame:
    return _leer_df(AUTO_SHEET_NAME, COLUMNAS_AUTORIZACION)


def escribir_autorizaciones(df: pd.DataFrame) -> None:
    _escribir_df(AUTO_SHEET_NAME, COLUMNAS_AUTORIZACION, df)


def append_autorizacion(
    *,
    fecha_ingreso: str,
    ds: str,
    nombre_completo: str,
    dni: str,
    genero: str,
    domicilio_fiscal: str,
    certificado_anterior: str,
    fecha_emision_cert_ant: str,
    fecha_caducidad_cert_ant: str,
    cod_evaluacion: str,
    fecha_evaluacion: str,
    cod_resolucion: str,
    fecha_resolucion: str,
    cod_certificacion: str,
    fecha_emision_cert: str,
    vigencia_autorizacion: str,
    lugar_venta: str,
    referencia: str,
    giro: str,
    horario: str,
    telefono: str = "",
) -> None:
    """
    Agrega una fila a Autorizaciones_CA.

    Todos los campos se mandan ya como string formateado
    (fechas tipo '16/01/2026', etc.).
    """
    fila = {
        "FECHA DE INGRESO": fecha_ingreso or "",
        "D.S": ds or "",
        "NOMBRE Y APELLIDO": nombre_completo or "",
        "DNI": dni or "",
        "GENERO": genero or "",
        "DOMICILIO FISCAL": domicilio_fiscal or "",
        "CERTIFICADO ANTERIOR": certificado_anterior or "",
        "FECHA EMITIDA CERTIFICADO ANTERIOR": fecha_emision_cert_ant or "",
        "FECHA DE CADUCIDAD CERTIFICADO ANTERIOR": fecha_caducidad_cert_ant or "",
        "N° DE EVALUACION": cod_evaluacion or "",
        "FECHA DE EVALUACION": fecha_evaluacion or "",
        "N° DE RESOLUCIÓN": cod_resolucion or "",
        "FECHA RESOLUCIÓN": fecha_resolucion or "",
        "N° DE CERTIFICADO": cod_certificacion or "",
        "FECHA EMITIDA CERTIFICADO": fecha_emision_cert or "",
        "VIGENCIA DE AUTORIZACIÓN": vigencia_autorizacion or "",
        "LUGAR DE VENTA": lugar_venta or "",
        "REFERENCIA": referencia or "",
        "GIRO": giro or "",
        "HORARIO": horario or "",
        "N° TELEFONO": telefono or "",
    }

    _append_fila(
        AUTO_SHEET_NAME,
        COLUMNAS_AUTORIZACION,
        fila,
        auto_numero_col=None,  # aquí no hay columna "N°"
    )
