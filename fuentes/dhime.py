"""Lectura de series de caudal diario exportadas desde DHIME (IDEAM).

DHIME no tiene una API pública estable: las series se descargan desde el portal
y se guardan en data/crudo/dhime/ o se cargan en la aplicación.
"""
from __future__ import annotations

import io
import unicodedata

import pandas as pd


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return "".join(ch for ch in s.lower() if ch.isalnum())


def leer(contenido: bytes | str) -> pd.DataFrame:
    """Devuelve columnas estacion, fecha y caudal (m³/s) a partir de un CSV de DHIME."""
    texto = contenido.decode("utf-8-sig", errors="replace") if isinstance(contenido, bytes) else contenido
    sep = ";" if texto.splitlines()[0].count(";") > texto.splitlines()[0].count(",") else ","
    d = pd.read_csv(io.StringIO(texto), sep=sep, dtype=str)
    cols = {_norm(c): c for c in d.columns}
    fecha = next((cols[k] for k in cols if k in ("fecha", "date", "fechahora")), None)
    valor = next((cols[k] for k in cols if k in ("valor", "value", "caudal")), None)
    est = next((cols[k] for k in cols if k in ("codigoestacion", "estacion", "nombreestacion")), None)
    if not fecha or not valor:
        raise ValueError("No se encontraron las columnas de fecha y valor en el archivo de DHIME.")
    out = pd.DataFrame({
        "estacion": d[est] if est else "estación",
        "fecha": pd.to_datetime(d[fecha], errors="coerce", dayfirst=False),
        "caudal": pd.to_numeric(d[valor].str.replace(",", ".", regex=False), errors="coerce"),
    }).dropna(subset=["fecha", "caudal"])
    out["fecha"] = out.fecha.dt.normalize()
    return out.groupby(["estacion", "fecha"], as_index=False).caudal.mean().sort_values("fecha")
