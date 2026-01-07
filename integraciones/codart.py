# integraciones/codart.py

from __future__ import annotations

import os
from typing import Any, Dict, Optional

import requests
import streamlit as st

BASE_URL = "https://api.codart.cgrt.net/api/v1/consultas"


class CodartAPIError(Exception):
    """Errores al consumir CODART (token, límites, caídas, WAF, etc.)."""


def _get_token() -> str:
    """
    Streamlit Cloud: usa st.secrets["CODART_TOKEN"].
    Fallback: variable de entorno CODART_TOKEN.
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
            "Falta CODART_TOKEN. Configúralo en Streamlit Cloud: Settings → Secrets."
        )
    return str(token).strip()


@st.cache_resource
def _get_session(token: str) -> requests.Session:
    """
    Session cacheada (mejor performance) + headers anti-406/WAF.
    Queda cacheada por token: si cambias el secret, se crea otra sesión.
    """
    s = requests.Session()
    s.headers.update(
        {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            # clave para evitar bloqueos típicos en Cloud/WAF:
            "User-Agent": "Mozilla/5.0 (Streamlit; CODART client)",
        }
    )
    return s

def _get_json(url: str, params: Optional[dict] = None) -> Dict[str, Any]:
    token = _get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",  # 👈 FIX para el 415
    }

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except requests.HTTPError as e:
        body = ""
        try:
            body = (resp.text or "")[:300]
        except Exception:
            body = ""
        raise CodartAPIError(f"HTTP {resp.status_code}: {body}") from e
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
    RENIEC DNI.
    Soporta /reniec/dni/{dni} y /reniec/dni/dni?dni=...
    """
    dni_ok = validar_dni(dni)

    url_a = f"{BASE_URL}/reniec/dni/{dni_ok}"
    url_b = f"{BASE_URL}/reniec/dni/dni"
    params_b = {"dni": dni_ok}

    try:
        data = _get_json(url_a)
        return data.get("result", {}) or {}
    except CodartAPIError as e:
        msg = str(e)
        if "HTTP 404" in msg or "HTTP 406" in msg:
            data = _get_json(url_b, params=params_b)
            return data.get("result", {}) or {}
        raise


@st.cache_data(ttl=60 * 60 * 24)  # 24h
def consultar_ruc(ruc: str) -> Dict[str, Any]:
    """
    SUNAT RUC.
    Soporta /sunat/ruc/{ruc} y /sunat/ruc/ruc?ruc=...
    """
    ruc_ok = validar_ruc(ruc)

    url_a = f"{BASE_URL}/sunat/ruc/{ruc_ok}"
    url_b = f"{BASE_URL}/sunat/ruc/ruc"
    params_b = {"ruc": ruc_ok}

    try:
        data = _get_json(url_a)
        return data.get("result", {}) or {}
    except CodartAPIError as e:
        msg = str(e)
        if "HTTP 404" in msg or "HTTP 406" in msg:
            data = _get_json(url_b, params=params_b)
            return data.get("result", {}) or {}
        raise


def dni_a_nombre_completo(res: Dict[str, Any]) -> str:
    """Arma nombre completo a partir del resultado RENIEC. Prioriza full_name."""
    full = (res.get("full_name") or "").strip()
    if full:
        return full

    parts = [
        (res.get("first_last_name") or "").strip(),
        (res.get("second_last_name") or "").strip(),
        (res.get("first_name") or "").strip(),
    ]
    return " ".join([p for p in parts if p]).strip()
