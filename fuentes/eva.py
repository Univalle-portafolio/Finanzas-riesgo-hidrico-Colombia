"""Evaluaciones Agropecuarias Municipales (EVA) desde Datos Abiertos Colombia.

Descarga la base agrícola completa, filtra los cultivos de la tesis y la agrega
por subzona hidrográfica con la correspondencia municipio-subzona.
"""
from __future__ import annotations

import io
from pathlib import Path

import pandas as pd
import requests

import config

COLUMNAS = {
    "Código Dane municipio": "cod_mpio",
    "Cultivo": "cultivo",
    "Desagregación cultivo": "desagregacion",
    "Año": "anio",
    "Periodo": "periodo",
    "Área sembrada": "area_sembrada_ha",
    "Área cosechada": "area_cosechada_ha",
    "Producción": "produccion_t",
}


def _numero(serie: pd.Series) -> pd.Series:
    """Convierte '1.234,50' o '1234.5' a número."""
    s = serie.astype(str).str.strip()
    con_coma = s.str.contains(",", regex=False)
    s = s.where(~con_coma, s.str.replace(".", "", regex=False).str.replace(",", ".", regex=False))
    return pd.to_numeric(s, errors="coerce")


def descargar(destino: Path | None = None) -> pd.DataFrame:
    """Descarga la base EVA desde datos.gov.co (formato CSV)."""
    r = requests.get(config.EVA_URL_CSV, timeout=config.TIEMPO_ESPERA)
    r.raise_for_status()
    if destino:
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(r.content)
    return pd.read_csv(io.BytesIO(r.content), dtype=str)


def leer_local(ruta: Path) -> pd.DataFrame:
    return pd.read_csv(ruta, dtype=str)


def agregar_por_subzona(eva: pd.DataFrame, correspondencia: pd.DataFrame) -> pd.DataFrame:
    """Filtra los cultivos de la tesis y suma área y producción por subzona, desagregación y año."""
    faltan = [c for c in COLUMNAS if c not in eva.columns]
    if faltan:
        raise ValueError(f"La base EVA cambió de estructura; faltan columnas: {faltan}")
    d = eva[list(COLUMNAS)].rename(columns=COLUMNAS)
    validas = {(c, x) for c, xs in config.EVA_DESAGREGACIONES.items() for x in xs}
    d = d[[(c, x) in validas for c, x in zip(d.cultivo, d.desagregacion)]].copy()
    d["cod_mpio"] = pd.to_numeric(d.cod_mpio, errors="coerce")
    d["anio"] = pd.to_numeric(d.anio, errors="coerce")
    for c in ["area_sembrada_ha", "area_cosechada_ha", "produccion_t"]:
        d[c] = _numero(d[c])
    d = d.merge(correspondencia[["cod_mpio", "cod_szh"]], on="cod_mpio", how="left")
    sin = d.cod_szh.isna().sum()
    if sin:
        print(f"Aviso: {sin} registros EVA sin subzona asignada (municipios nuevos o códigos distintos).")
    g = (d.dropna(subset=["cod_szh"])
           .groupby(["cod_szh", "cultivo", "desagregacion", "anio"], as_index=False)
           .agg(area_sembrada_ha=("area_sembrada_ha", "sum"),
                area_cosechada_ha=("area_cosechada_ha", "sum"),
                produccion_t=("produccion_t", "sum"),
                n_municipios=("cod_mpio", "nunique")))
    g["rendimiento_t_ha"] = (g.produccion_t / g.area_cosechada_ha).round(3)
    g["cod_szh"] = g.cod_szh.astype(int)
    return g
