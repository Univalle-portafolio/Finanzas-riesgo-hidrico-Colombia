"""Actualiza los datos procesados desde las fuentes oficiales.

Uso:
    python actualizar.py                 # descarga EVA y ONI
    python actualizar.py --eva-local ruta.csv   # usa un CSV de EVA descargado a mano
    python actualizar.py --solo oni
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

import config
from fuentes import eva, oni

BITACORA = config.PROCESADO / "actualizacion.json"


def _bitacora(fuente: str, **datos) -> None:
    reg = json.loads(BITACORA.read_text(encoding="utf-8")) if BITACORA.exists() else {}
    reg[fuente] = {"fecha": datetime.now(timezone.utc).isoformat(timespec="seconds"), **datos}
    BITACORA.write_text(json.dumps(reg, ensure_ascii=False, indent=2), encoding="utf-8")


def actualizar_eva(local: Path | None = None) -> None:
    corr = pd.read_csv(config.ESTATICO / "correspondencia_municipio_subzona.csv")
    base = eva.leer_local(local) if local else eva.descargar()
    g = eva.agregar_por_subzona(base, corr)
    g.to_csv(config.PROCESADO / "eva_subzona.csv", index=False)
    _bitacora("eva", origen=f"archivo local {local.name}" if local else config.EVA_URL_CSV, registros=len(base),
              anios=f"{int(g.anio.min())}-{int(g.anio.max())}", filas=len(g))
    print(f"EVA: {len(base):,} registros leídos, {len(g):,} filas por subzona.")


def actualizar_oni() -> None:
    d = oni.descargar()
    d.to_csv(config.PROCESADO / "oni.csv", index=False)
    _bitacora("oni", origen=config.ONI_URL, ultimo=d.fecha.max().strftime("%Y-%m"))
    print(f"ONI: {len(d)} meses, último {d.fecha.max():%Y-%m}.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--solo", choices=["eva", "oni"])
    ap.add_argument("--eva-local", type=Path)
    a = ap.parse_args()
    config.PROCESADO.mkdir(parents=True, exist_ok=True)
    errores = []
    for nombre, f in [("eva", lambda: actualizar_eva(a.eva_local)), ("oni", actualizar_oni)]:
        if a.solo and a.solo != nombre:
            continue
        try:
            f()
        except Exception as e:  # una fuente caída no detiene a las demás
            errores.append(f"{nombre}: {e}")
            print(f"Error al actualizar {nombre}: {e}")
    if errores and len(errores) == (1 if a.solo else 2):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
