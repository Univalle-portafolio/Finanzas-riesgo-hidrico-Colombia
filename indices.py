"""Cálculo de los índices del objetivo específico 1."""
from __future__ import annotations

import numpy as np
import pandas as pd

ESCENARIOS = {"húmedo": "humedo", "medio": "medio", "seco": "seco"}

COMPONENTES = {
    # clave: (nombre, descripción, función sobre la tabla de subzonas)
    "presion": ("Presión de uso", "IUA en año seco", lambda d: d.IUA_seco),
    "regulacion": ("Baja regulación", "1 − IRH", lambda d: 1 - d.IRH),
    "variabilidad": ("Variabilidad", "CV de la oferta anual", lambda d: d.cv_oferta_anual),
    "sequia": ("Severidad de sequía", "− índice multivariado 12 meses", lambda d: -d.sequia_multiv_12m),
    "concesiones": ("Presión de concesiones", "Volumen SIRH / oferta disponible seca",
                    lambda d: d.vol_agricola_vigente_Mm3_anio / d.oferta_disp_seco_Mm3),
}


def deficit_escenario(d: pd.DataFrame, escenario: str) -> pd.Series:
    """I = max(0, 1 − Q/Q*), con Q = oferta disponible del escenario ENA y Q* = demanda hídrica."""
    q = d[f"oferta_disp_{ESCENARIOS[escenario]}_Mm3"]
    return (1 - q / d.demanda_hidrica_Mm3).clip(lower=0)


def percentiles(d: pd.DataFrame) -> pd.DataFrame:
    """Lleva cada componente a percentil (0 a 1) entre las subzonas con dato."""
    out = pd.DataFrame(index=d.index)
    for k, (_, _, f) in COMPONENTES.items():
        x = f(d).replace([np.inf, -np.inf], np.nan)
        out[k] = (x.rank(method="average") - 1) / (x.notna().sum() - 1)
    return out


def sintetico(p: pd.DataFrame, pesos: dict[str, float]) -> pd.Series:
    """S = Σ w·P / Σ w, reponderando cuando falta un componente."""
    w = pd.Series(pesos).reindex(p.columns).fillna(0)
    num = (p * w).sum(axis=1, min_count=1)
    den = p.notna().mul(w).sum(axis=1)
    return (num / den).where(den > 0)


def indice_diario(caudal: pd.Series, q_ref: float) -> pd.Series:
    """Índice de déficit diario I_t = max(0, 1 − Q_t / Q*)."""
    return (1 - caudal / q_ref).clip(lower=0)
