# integraciones/codart.py

from __future__ import annotations

import os
from typing import Any, Dict

import requests
import streamlit as st

BASE_URL = "https://api.codart.cgrt.net/api/v1/consultas"


class CodartAPIError(Exception):
    """Errores al consumir CODART (token, límites, caídas, etc.)."""


def _get_token() -> str:
    """
    Busca el token en:
    1) st.secrets["CODART_TOKEN"]
    2) variable de entorno CODART_TOKEN
    """
    token = None
    try:
        token = st.secrets.get("CODART_TOKEN")
    except Exception:
        token = None

    if not token:
        token = os.getenv("CODART_TOKEN")

    if not token:
        raise CodartAPIError(
            "Falta CODART_TOKEN. Configúralo en .streamlit/secrets.toml o como variable de entorno."
        )
    return token


def _get_json(url: str) -> Dict[str, Any]:
    token = _get_token()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }

    try:
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        raise CodartAPIError(f"Error HTTP/red consultando CODART: {e}") from e
    except ValueError as e:
        raise CodartAPIError("La respuesta de CODART no fue JSON válido.") from e

    if not isinstance(data, dict):
        raise CodartAPIError("Respuesta inesperada de CODART (no es dict).")

    if data.get("success") is not True:
        msg = data.get("message") or data.get("error") or "success=false"
        raise CodartAPIError(f"CODART respondió error: {msg}")

    return data


def validar_dni(dni: str) -> str:
    dni = (dni or "").strip()
    if not (dni.isdigit() and len(dni) == 8):
        raise ValueError("DNI inválido. Debe tener 8 dígitos.")
    return dni


def validar_ruc(ruc: str) -> str:
    ruc = (ruc or "").strip()
    if not (ruc.isdigit() and len(ruc) == 11):
        raise ValueError("RUC inválido. Debe tener 11 dígitos.")
    return ruc


@st.cache_data(ttl=60 * 60 * 24)  # 24h
def consultar_dni(dni: str) -> Dict[str, Any]:
    """
    RENIEC DNI:
    GET https://api.codart.cgrt.net/api/v1/consultas/reniec/dni/{dni}
    Devuelve result (dict).
    """
    dni_ok = validar_dni(dni)
    url = f"{BASE_URL}/reniec/dni/{dni_ok}"
    data = _get_json(url)
    return data.get("result", {}) or {}


@st.cache_data(ttl=60 * 60 * 24)
def consultar_ruc(ruc: str) -> Dict[str, Any]:
    """
    SUNAT RUC:
    GET https://api.codart.cgrt.net/api/v1/consultas/sunat/ruc/{ruc}
    Devuelve result (dict).
    """
    ruc_ok = validar_ruc(ruc)
    url = f"{BASE_URL}/sunat/ruc/{ruc_ok}"
    data = _get_json(url)
    return data.get("result", {}) or {}


def dni_a_nombre_completo(res: Dict[str, Any]) -> str:
    """
    Arma nombre completo a partir del resultado RENIEC.
    Prioriza full_name.
    """
    full = (res.get("full_name") or "").strip()
    if full:
        return full

    parts = [
        (res.get("first_last_name") or "").strip(),
        (res.get("second_last_name") or "").strip(),
        (res.get("first_name") or "").strip(),
    ]
    return " ".join([p for p in parts if p]).strip()
