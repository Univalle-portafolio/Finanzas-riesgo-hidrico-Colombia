"""Índice Oceánico de El Niño (ONI) de la NOAA y clasificación de fases ENSO."""
from __future__ import annotations

import io

import pandas as pd
import requests

import config

# Mes central de cada temporada trimestral
MES_CENTRAL = {"DJF": 1, "JFM": 2, "FMA": 3, "MAM": 4, "AMJ": 5, "MJJ": 6,
               "JJA": 7, "JAS": 8, "ASO": 9, "SON": 10, "OND": 11, "NDJ": 12}


def descargar() -> pd.DataFrame:
    r = requests.get(config.ONI_URL, timeout=config.TIEMPO_ESPERA)
    r.raise_for_status()
    return leer_texto(r.text)


def leer_texto(texto: str) -> pd.DataFrame:
    d = pd.read_csv(io.StringIO(texto), sep=r"\s+")
    d.columns = [c.upper() for c in d.columns]
    d = d.rename(columns={"SEAS": "temporada", "YR": "anio", "TOTAL": "sst", "ANOM": "oni"})
    d["mes"] = d.temporada.map(MES_CENTRAL)
    d["fecha"] = pd.to_datetime(dict(year=d.anio, month=d.mes, day=1))
    return clasificar(d[["fecha", "temporada", "anio", "mes", "oni"]].sort_values("fecha").reset_index(drop=True))


def clasificar(d: pd.DataFrame, umbral: float = config.ONI_UMBRAL,
               minimo: int = config.ONI_TEMPORADAS_MIN) -> pd.DataFrame:
    """Fase ENSO según la regla de la NOAA: |ONI| >= 0,5 °C durante al menos cinco temporadas seguidas."""
    d = d.copy()
    signo = d.oni.ge(umbral).astype(int) - d.oni.le(-umbral).astype(int)
    racha = (signo != signo.shift()).cumsum()
    largo = signo.groupby(racha).transform("size")
    d["fase"] = "Neutral"
    d.loc[(signo == 1) & (largo >= minimo), "fase"] = "El Niño"
    d.loc[(signo == -1) & (largo >= minimo), "fase"] = "La Niña"
    return d
