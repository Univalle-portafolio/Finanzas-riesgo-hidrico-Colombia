"""Observatorio de riesgo hídrico por subzona hidrográfica.

Visualización de trabajo del objetivo específico 1 de la tesis doctoral
"Valoración financiera del riesgo hídrico y diseño de un instrumento de cobertura
para la agricultura bajo riego en Colombia" (Universidad del Valle, GIFINC).
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from scipy import stats

import config
import indices
from fuentes import dhime, eva, oni

st.set_page_config(page_title="Observatorio de riesgo hídrico", page_icon="💧", layout="wide")

AZUL, OCRE, ROJO, GRIS = "#1d5f78", "#c08424", "#a83a2e", "#9fb3bd"
COLOR_FASE = {"El Niño": ROJO, "Neutral": GRIS, "La Niña": AZUL}
SEMANA = 7 * 24 * 3600


def fmt(x, d=1):
    if x is None or (isinstance(x, float) and not np.isfinite(x)) or pd.isna(x):
        return "s. d."
    return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ----------------------------------------------------------------- datos
@st.cache_data
def cargar_subzonas() -> pd.DataFrame:
    ena = pd.read_csv(config.ESTATICO / "ena2022_subzona.csv")
    sirh = pd.read_csv(config.ESTATICO / "sirh_subzona.csv")
    return ena.merge(sirh, on="cod_szh", how="left").set_index("cod_szh", drop=False).rename_axis(None)


@st.cache_data(ttl=SEMANA, show_spinner="Consultando EVA en datos.gov.co…")
def eva_en_linea() -> pd.DataFrame:
    corr = pd.read_csv(config.ESTATICO / "correspondencia_municipio_subzona.csv")
    return eva.agregar_por_subzona(eva.descargar(), corr)


@st.cache_data(ttl=SEMANA, show_spinner="Consultando el ONI en la NOAA…")
def oni_en_linea() -> pd.DataFrame:
    return oni.descargar()


def cargar_eva(en_linea: bool) -> tuple[pd.DataFrame, str]:
    if en_linea:
        try:
            return eva_en_linea(), "datos.gov.co (consulta en vivo)"
        except Exception as e:
            st.sidebar.warning(f"No se pudo consultar la EVA en línea ({e}). Se usa la copia guardada.")
    return pd.read_csv(config.PROCESADO / "eva_subzona.csv"), "copia guardada en el repositorio"


def cargar_oni(en_linea: bool) -> tuple[pd.DataFrame | None, str]:
    ruta = config.PROCESADO / "oni.csv"
    if en_linea or not ruta.exists():
        try:
            return oni_en_linea(), "NOAA CPC (consulta en vivo)"
        except Exception as e:
            if not ruta.exists():
                return None, f"no disponible ({e})"
    d = pd.read_csv(ruta, parse_dates=["fecha"])
    return d, "copia guardada en el repositorio"


def bitacora() -> dict:
    ruta = config.PROCESADO / "actualizacion.json"
    return json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else {}


# ----------------------------------------------------------------- barra lateral
st.sidebar.title("Riesgo hídrico · Colombia")
st.sidebar.caption("Objetivo específico 1 · versión de trabajo")
if st.sidebar.button("Consultar fuentes oficiales ahora", width="stretch",
                     help="Descarga la EVA de datos.gov.co y el ONI de la NOAA. Puede tardar un minuto."):
    eva_en_linea.clear()
    oni_en_linea.clear()
    st.session_state["en_linea"] = True
en_linea = st.session_state.get("en_linea", False)

Z = cargar_subzonas()
EVA, origen_eva = cargar_eva(en_linea)
ONI, origen_oni = cargar_oni(en_linea)
st.sidebar.markdown(f"**EVA:** {origen_eva}  \n**ONI:** {origen_oni}")
reg = bitacora()
if reg:
    st.sidebar.caption("Última actualización automática: " +
                       "; ".join(f"{k.upper()} {v['fecha'][:10]}" for k, v in reg.items()))

st.sidebar.subheader("Pesos del índice sintético")
pesos = {}
for k, (nombre, desc, _) in indices.COMPONENTES.items():
    pesos[k] = st.sidebar.slider(nombre, 0, 5, 1, help=desc, key=f"w_{k}")

P = indices.percentiles(Z)
Z["S"] = indices.sintetico(P, pesos)
Z["puesto"] = Z.S.rank(ascending=False, method="min")
for esc in indices.ESCENARIOS:
    Z[f"I_{esc}"] = indices.deficit_escenario(Z, esc)
Z["etiqueta"] = Z.cod_szh.astype(str) + " · " + Z.subzona
rut = Z.loc[config.SUBZONA_RUT]

# ----------------------------------------------------------------- encabezado
st.title("Observatorio de riesgo hídrico por subzona hidrográfica")
st.markdown("Variables del ENA 2022, la EVA y el SIRH, y un primer cálculo del índice hídrico de la tesis: "
            "**I = max(0, 1 − Q/Q\\*)**. El distrito RUT (subzona 2608) aparece resaltado.")
c = st.columns(5)
c[0].metric("Subzonas", len(Z))
c[1].metric("Con déficit en año seco", int((Z.I_seco > 0).sum()))
c[2].metric("IUA seco > 50 %", int((Z.IUA_seco > 50).sum()))
c[3].metric("RUT · índice sintético", fmt(rut.S, 2), f"puesto {int(rut.puesto)} de {Z.S.notna().sum()}",
            delta_color="off")
c[4].metric("RUT · concesión vigente", f"{fmt(rut.caudal_agricola_vigente_ls, 0)} l/s",
            f"{int(rut.n_concesiones)} concesiones", delta_color="off")

tabs = st.tabs(["Variables", "Índice de déficit", "Índice sintético", "Ficha de subzona", "Caudal y ENSO", "Fuentes"])

VARIABLES = {
    "Índice de uso del agua, año seco (%)": "IUA_seco",
    "Índice de uso del agua, año medio (%)": "IUA_medio",
    "Índice de retención y regulación hídrica (IRH)": "IRH",
    "Coeficiente de variación de la oferta anual (%)": "cv_oferta_anual",
    "Índice de sequía multivariado, 12 meses": "sequia_multiv_12m",
    "Oferta disponible, año seco (Mm³)": "oferta_disp_seco_Mm3",
    "Demanda hídrica total (Mm³/año)": "demanda_hidrica_Mm3",
    "Huella hídrica azul (Mm³/año)": "huella_azul_Mm3",
    "Caudal agrícola concesionado vigente (l/s)": "caudal_agricola_vigente_ls",
    "Número de concesiones agrícolas": "n_concesiones",
}


def barras(d: pd.DataFrame, col: str, titulo: str, alto: int | None = None):
    d = d.sort_values(col)
    colores = [OCRE if i == config.SUBZONA_RUT else AZUL for i in d.cod_szh]
    fig = go.Figure(go.Bar(x=d[col], y=d.etiqueta, orientation="h", marker_color=colores,
                           hovertemplate="%{y}<br>%{x:.3f}<extra></extra>"))
    fig.update_layout(title=titulo, height=alto or max(320, 18 * len(d) + 80),
                      margin=dict(l=10, r=10, t=50, b=10), yaxis=dict(tickfont=dict(size=11)))
    st.plotly_chart(fig, width="stretch")


# ----------------------------------------------------------------- 1. variables
with tabs[0]:
    a, b = st.columns([2, 1])
    nombre = a.selectbox("Variable", list(VARIABLES))
    zona = b.selectbox("Zona hidrográfica", ["Todas"] + sorted(Z.zona_hidrografica.dropna().unique()))
    col = VARIABLES[nombre]
    d = Z if zona == "Todas" else Z[Z.zona_hidrografica == zona]
    d = d[d[col].notna()]
    m = st.columns(4)
    m[0].metric("Subzonas", len(d))
    m[1].metric("Mediana", fmt(d[col].median(), 2))
    m[2].metric("Máximo", fmt(d[col].max(), 2))
    m[3].metric("RUT (2608)", fmt(rut[col], 2))
    n = st.slider("Subzonas que se muestran", 10, max(10, len(d)), min(40, len(d)))
    top = d.nlargest(n, col) if col != "sequia_multiv_12m" else d.nsmallest(n, col)
    if config.SUBZONA_RUT in d.index and config.SUBZONA_RUT not in top.index:
        top = pd.concat([top, d.loc[[config.SUBZONA_RUT]]])
    barras(top, col, nombre)

# ----------------------------------------------------------------- 2. déficit
with tabs[1]:
    st.markdown("Versión transversal del índice de la tesis con los escenarios del ENA 2022: "
                "Q = oferta disponible del escenario y Q\\* = demanda hídrica total. "
                "En la tesis, Q será el caudal diario observado (pestaña **Caudal y ENSO**).")
    esc = st.radio("Escenario hidrológico", list(indices.ESCENARIOS), index=2, horizontal=True,
                   format_func=lambda s: f"Año {s}")
    d = Z[Z[f"I_{esc}"] > 0]
    izq, der = st.columns([3, 2])
    with izq:
        if len(d):
            barras(d, f"I_{esc}", f"{len(d)} subzonas con déficit en año {esc}")
        else:
            st.info("Ninguna subzona tiene déficit en este escenario.")
    with der:
        st.subheader("Distrito RUT")
        t = pd.DataFrame({
            "Escenario": [f"Año {e}" for e in indices.ESCENARIOS],
            "Oferta disponible (Mm³)": [rut[f"oferta_disp_{v}_Mm3"] for v in indices.ESCENARIOS.values()],
            "Demanda (Mm³)": rut.demanda_hidrica_Mm3,
        })
        t["Q/Q*"] = t["Oferta disponible (Mm³)"] / t["Demanda (Mm³)"]
        t["I"] = (1 - 1 / t["Q/Q*"]).clip(lower=0)
        st.dataframe(t.round(2), hide_index=True, width="stretch")
        st.caption(f"Volumen agrícola concesionado (SIRH): {fmt(rut.vol_agricola_vigente_Mm3_anio, 1)} Mm³/año, "
                   f"{fmt(rut.vol_agricola_vigente_Mm3_anio / rut.demanda_hidrica_Mm3, 2)} veces la demanda del ENA.")

# ----------------------------------------------------------------- 3. sintético
with tabs[2]:
    st.markdown("**S = Σ wₖ·Pₖ / Σ wₖ**, donde Pₖ es el percentil del componente k entre las subzonas. "
                "Los pesos se ajustan en la barra lateral. Si falta un componente, los demás se reponderan.")
    tot = sum(pesos.values()) or 1
    st.caption(" · ".join(f"{indices.COMPONENTES[k][0]}: {round(100 * w / tot)} %" for k, w in pesos.items()))
    top = Z.nlargest(25, "S")
    if config.SUBZONA_RUT not in top.index:
        top = pd.concat([top, Z.loc[[config.SUBZONA_RUT]]])
    barras(top, "S", "Las 25 subzonas con mayor índice sintético")
    fig = px.scatter(Z.assign(IUA=Z.IUA_seco.clip(lower=0.1), tipo=np.where(Z.cod_szh == config.SUBZONA_RUT, "RUT", "Subzona")),
                     x="IUA", y="S", color="tipo", log_x=True, hover_name="etiqueta",
                     color_discrete_map={"RUT": OCRE, "Subzona": AZUL},
                     labels={"IUA": "IUA en año seco (%), escala logarítmica", "S": "Índice sintético"})
    fig.add_vline(x=100, line_dash="dash", line_color=ROJO, annotation_text="IUA = 100 %")
    fig.update_layout(height=460, legend_title_text="")
    st.plotly_chart(fig, width="stretch")
    salida = Z[["cod_szh", "subzona", "zona_hidrografica", "S", "puesto", "I_seco"]].join(P.add_prefix("P_"))
    st.download_button("Descargar índice (CSV)", salida.to_csv(index=False).encode("utf-8-sig"),
                       "indice_sintetico_subzonas.csv", "text/csv")

# ----------------------------------------------------------------- 4. ficha
with tabs[3]:
    opciones = Z.sort_values("cod_szh").etiqueta.tolist()
    sel = st.selectbox("Subzona", opciones, index=opciones.index(rut.etiqueta))
    s = Z[Z.etiqueta == sel].iloc[0]
    st.subheader(sel)
    st.caption(f"Zona {s.zona_hidrografica} · Vulnerabilidad hídrica en año seco: {s.IVH_seco_cat} · "
               f"Categoría integrada ENA: {s.categoria_integrada}")
    izq, der = st.columns(2)
    with izq:
        filas = {
            "Área de la subzona (km²)": fmt(s.area_km2, 0),
            "Oferta disponible húmedo / medio / seco (Mm³)":
                " / ".join(fmt(s[f"oferta_disp_{v}_Mm3"], 0) for v in indices.ESCENARIOS.values()),
            "Demanda hídrica total (Mm³)": fmt(s.demanda_hidrica_Mm3, 1),
            "IUA medio / seco (%)": f"{fmt(s.IUA_medio, 1)} / {fmt(s.IUA_seco, 1)}",
            "IRH": fmt(s.IRH, 2),
            "CV de la oferta anual (%)": fmt(s.cv_oferta_anual, 1),
            "Sequía multivariada 12 meses": fmt(s.sequia_multiv_12m, 2),
            "Concesiones agrícolas (SIRH)": "Sin reporte" if pd.isna(s.n_concesiones) else
                f"{int(s.n_concesiones)} · {fmt(s.caudal_agricola_vigente_ls, 0)} l/s",
            "Índice de déficit, año seco": fmt(s.I_seco, 2),
            "Índice sintético": f"{fmt(s.S, 2)} · puesto {int(s.puesto)}" if pd.notna(s.S) else "s. d.",
        }
        st.dataframe(pd.DataFrame(filas.items(), columns=["Variable", "Valor"]), hide_index=True,
                     width="stretch")
    with der:
        comp = P.loc[s.cod_szh].rename(lambda k: indices.COMPONENTES[k][0])
        fig = px.bar(comp[::-1], orientation="h", range_x=[0, 1], labels={"value": "Percentil", "index": ""},
                     title="Componentes del índice sintético")
        fig.update_traces(marker_color=AZUL)
        fig.update_layout(showlegend=False, height=300, margin=dict(t=50, b=10))
        st.plotly_chart(fig, width="stretch")
    e = EVA[EVA.cod_szh == s.cod_szh]
    if len(e):
        medida = st.radio("Variable EVA", ["area_sembrada_ha", "produccion_t", "rendimiento_t_ha"], horizontal=True,
                          format_func={"area_sembrada_ha": "Área sembrada (ha)", "produccion_t": "Producción (t)",
                                       "rendimiento_t_ha": "Rendimiento (t/ha)"}.get)
        agg = "mean" if medida == "rendimiento_t_ha" else "sum"
        g = e.groupby(["cultivo", "anio"], as_index=False)[medida].agg(agg)
        fig = px.line(g, x="anio", y=medida, color="cultivo", markers=True, title="EVA por cultivo",
                      labels={"anio": "Año", medida: ""})
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("Sin registros EVA de arroz, caña, maíz o papa en esta subzona.")

# ----------------------------------------------------------------- 5. caudal y ENSO
with tabs[4]:
    st.markdown("Cargue una serie de **caudal diario** exportada de [DHIME](%s) (IDEAM) para calcular el índice "
                "diario **Iₜ = max(0, 1 − Qₜ/Q\\*)** y compararlo entre fases ENSO (hipótesis 1)." % config.DHIME_URL)
    archivos = st.file_uploader("Archivos CSV de DHIME", type=["csv", "txt"], accept_multiple_files=True)
    locales = sorted((config.CRUDO / "dhime").glob("*.csv"))
    series = []
    for f in archivos or []:
        try:
            series.append(dhime.leer(f.getvalue()))
        except Exception as ex:
            st.error(f"{f.name}: {ex}")
    for f in locales:
        series.append(dhime.leer(f.read_bytes()))
    if not series:
        st.info("Aún no hay series de caudal. Descárguelas de DHIME (parámetro: caudal medio diario) y cárguelas aquí.")
    else:
        Q = pd.concat(series)
        est = st.selectbox("Estación", sorted(Q.estacion.unique()))
        q = Q[Q.estacion == est].set_index("fecha").caudal.asfreq("D")
        st.caption(f"{q.notna().sum():,} días con dato entre {q.index.min():%Y-%m-%d} y {q.index.max():%Y-%m-%d} "
                   f"({100 * q.isna().mean():.1f} % faltante).")
        modo = st.radio("Caudal de referencia Q*", ["Percentil de la serie", "Caudal concesionado (l/s)"],
                        horizontal=True)
        if modo == "Percentil de la serie":
            p = st.slider("Percentil", 10, 90, 50, 5)
            q_ref = float(np.nanpercentile(q, p))
        else:
            q_ref = st.number_input("Caudal (l/s)", min_value=1.0, value=1000.0, step=50.0) / 1000
        st.markdown(f"Q* = **{fmt(q_ref, 3)} m³/s**")
        I = indices.indice_diario(q, q_ref)
        fig = go.Figure()
        fig.add_scatter(x=q.index, y=q, name="Caudal (m³/s)", line=dict(color=AZUL, width=1))
        fig.add_hline(y=q_ref, line_dash="dash", line_color=OCRE, annotation_text="Q*")
        fig.update_layout(height=320, margin=dict(t=30, b=10), title="Caudal diario")
        st.plotly_chart(fig, width="stretch")
        mens = I.resample("MS").mean().rename("I").to_frame()
        if ONI is not None:
            mens = mens.join(ONI.set_index("fecha")[["oni", "fase"]], how="left")
            mens["fase"] = mens.fase.fillna("Sin ONI")
            fig = px.bar(mens.reset_index(), x="fecha", y="I", color="fase", color_discrete_map=COLOR_FASE,
                         title="Índice de déficit mensual por fase ENSO", labels={"fecha": "", "I": "I promedio"})
            fig.update_layout(height=320, legend_title_text="")
            st.plotly_chart(fig, width="stretch")
            ok = mens[mens.fase.isin(COLOR_FASE)].dropna(subset=["I"])
            izq, der = st.columns([3, 2])
            with izq:
                fig = px.box(ok.reset_index(), x="fase", y="I", color="fase", color_discrete_map=COLOR_FASE,
                             category_orders={"fase": list(COLOR_FASE)}, points="all",
                             title="Distribución del índice por fase")
                fig.update_layout(showlegend=False, height=360)
                st.plotly_chart(fig, width="stretch")
            with der:
                resumen = ok.groupby("fase").I.agg(["count", "mean", "median", lambda x: (x > 0).mean()])
                resumen.columns = ["Meses", "Media", "Mediana", "Meses con déficit"]
                st.dataframe(resumen.round(3), width="stretch")
                grupos = [g.I.values for _, g in ok.groupby("fase") if len(g) >= 3]
                if len(grupos) >= 2:
                    h, pv = stats.kruskal(*grupos)
                    st.markdown(f"Prueba de Kruskal-Wallis: H = {fmt(h, 2)}, p = {fmt(pv, 4)}")
                    st.caption("Exploratoria: los meses consecutivos no son independientes. "
                               "La prueba formal de la hipótesis 1 usará el modelo con cambio de régimen.")
        else:
            st.warning("No hay datos del ONI. Use «Consultar fuentes oficiales ahora» en la barra lateral.")
        st.download_button("Descargar índice diario (CSV)",
                           pd.DataFrame({"caudal_m3s": q, "I": I}).to_csv().encode("utf-8-sig"),
                           f"indice_diario_{est}.csv", "text/csv")

# ----------------------------------------------------------------- 6. fuentes
with tabs[5]:
    st.info(config.NOTA_IDEAM)
    st.markdown(f"""
**Cómo se actualiza**

- **EVA y ONI**: un flujo de GitHub Actions ejecuta `actualizar.py` el día 5 de cada mes y guarda los datos nuevos
  en el repositorio. El botón de la barra lateral consulta las fuentes en el momento.
- **ENA 2022**: estudio cuatrienal; se actualiza a mano cuando el IDEAM publique el ENA 2026.
- **SIRH**: base entregada por el IDEAM por solicitud; se reemplaza `data/estatico/sirh_subzona.csv` con cada entrega.
- **Caudal diario**: DHIME no tiene API pública estable; las series se cargan en la pestaña *Caudal y ENSO*.

**Referencias**

Instituto de Hidrología, Meteorología y Estudios Ambientales [IDEAM]. (2023). *Estudio Nacional del Agua 2022*. IDEAM.

Instituto de Hidrología, Meteorología y Estudios Ambientales [IDEAM]. (2026). *Sistema de Información del Recurso
Hídrico (SIRH): registro de usuarios del recurso hídrico* [Base de datos anonimizada, corte de agosto].

Ministerio de Agricultura y Desarrollo Rural [MADR] y Unidad de Planificación Rural Agropecuaria [UPRA]. (2026).
*Evaluaciones Agropecuarias Municipales (EVA) 2019–2025: base agrícola* [Conjunto de datos]. Datos Abiertos Colombia.
{config.EVA_URL_FICHA}

National Oceanic and Atmospheric Administration [NOAA], Climate Prediction Center. (2026). *Oceanic Niño Index (ONI)*
[Conjunto de datos]. {config.ONI_URL}
""")
    if reg:
        st.json(reg)
