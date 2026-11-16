# Observatorio de riesgo hídrico por subzona hidrográfica

Aplicación en Streamlit del objetivo específico 1 de la tesis doctoral *Valoración financiera del riesgo hídrico y diseño de un instrumento de cobertura para la agricultura bajo riego en Colombia* (Doctorado en Ingeniería, Universidad del Valle, grupo GIFINC).

Muestra las variables hídricas de las 198 subzonas hidrográficas, calcula el índice de déficit **I = max(0, 1 − Q/Q\*)** y un índice hídrico sintético con pesos ajustables, y compara el índice diario de caudal entre fases de El Niño, La Niña y neutral. El distrito RUT (subzona 2608) aparece resaltado.

## Estructura

```
app.py                     Aplicación Streamlit
actualizar.py              Descarga y procesa las fuentes oficiales
config.py                  URL de las fuentes, rutas y constantes
indices.py                 Índice de déficit, índice sintético e índice diario
fuentes/
  eva.py                   EVA (MADR-UPRA) desde datos.gov.co
  oni.py                   Índice Oceánico de El Niño (NOAA) y fases ENSO
  dhime.py                 Lectura de series de caudal exportadas de DHIME (IDEAM)
data/
  estatico/                ENA 2022, resumen del SIRH y correspondencia municipio-subzona
  procesado/               EVA por subzona, ONI y bitácora de actualización
  crudo/dhime/             Series de caudal propias (no se suben a GitHub)
.github/workflows/         Actualización automática mensual
```

## Fuentes y actualización

| Fuente | Entidad | Cómo se actualiza |
|---|---|---|
| Evaluaciones Agropecuarias Municipales (EVA) 2019–2025, conjunto `uejq-wxrr` | MADR y UPRA, Datos Abiertos Colombia | Automática, cada mes, con GitHub Actions; o en vivo con el botón de la aplicación |
| Índice Oceánico de El Niño (ONI) | NOAA, Climate Prediction Center | Automática, cada mes; o en vivo |
| Estudio Nacional del Agua (ENA) 2022 | IDEAM | Manual, cuando se publique un nuevo ENA |
| Sistema de Información del Recurso Hídrico (SIRH) | IDEAM, por solicitud | Manual: reemplazar `data/estatico/sirh_subzona.csv` |
| Caudal medio diario | IDEAM, portal DHIME | Carga de archivos CSV en la pestaña *Caudal y ENSO* |

La fase ENSO sigue la regla de la NOAA: El Niño o La Niña cuando el ONI supera ±0,5 °C durante al menos cinco temporadas trimestrales seguidas.

## Ejecutar en el computador

```bash
python -m venv .venv
source .venv/bin/activate        # en Windows: .venv\Scripts\activate
pip install -r requirements.txt
python actualizar.py             # descarga EVA y ONI
streamlit run app.py
```

Si ya tiene la base EVA descargada: `python actualizar.py --eva-local ruta/al/archivo.csv`.

## Publicar en GitHub

1. En GitHub, cree un repositorio nuevo (por ejemplo, `riesgo-hidrico-colombia`). Puede ser público o privado.
2. Suba el contenido de esta carpeta, con *Add file → Upload files* o con git:
   ```bash
   git init
   git add .
   git commit -m "Primera versión del observatorio"
   git branch -M main
   git remote add origin https://github.com/USUARIO/riesgo-hidrico-colombia.git
   git push -u origin main
   ```
   La carpeta `.github` empieza con punto y algunos sistemas la ocultan; verifique que quede en el repositorio.
3. Dé permiso de escritura a la actualización automática: *Settings → Actions → General → Workflow permissions → Read and write permissions → Save*.
4. Ejecute la primera actualización: *Actions → Actualizar datos oficiales → Run workflow*. Así se crea `data/procesado/oni.csv`. Después se repite sola el día 5 de cada mes.

## Publicar en Streamlit Community Cloud

1. Entre a [share.streamlit.io](https://share.streamlit.io) con su cuenta de GitHub.
2. *Create app → Deploy a public app from GitHub*.
3. Elija el repositorio, la rama `main` y el archivo principal `app.py`.
4. En *Advanced settings*, elija Python 3.11 y pulse *Deploy*.

Cada vez que GitHub Actions guarde datos nuevos, Streamlit vuelve a cargar la aplicación con ellos.

## Condiciones de uso de los datos

Los datos de concesiones provienen del Sistema de Información del Recurso Hídrico (SIRH) del IDEAM. Los resultados son elaboración propia y no constituyen cifras oficiales del IDEAM. El repositorio solo contiene el resumen por subzona del SIRH, sin datos de usuarios. Las bases de ASORUT no deben subirse al repositorio (Ley 1581 de 2012).

## Referencias

Instituto de Hidrología, Meteorología y Estudios Ambientales [IDEAM]. (2023). *Estudio Nacional del Agua 2022*. IDEAM.

Instituto de Hidrología, Meteorología y Estudios Ambientales [IDEAM]. (2026). *Sistema de Información del Recurso Hídrico (SIRH): registro de usuarios del recurso hídrico* [Base de datos anonimizada, corte de agosto].

Ministerio de Agricultura y Desarrollo Rural [MADR] y Unidad de Planificación Rural Agropecuaria [UPRA]. (2026). *Evaluaciones Agropecuarias Municipales (EVA) 2019–2025: base agrícola* [Conjunto de datos]. Datos Abiertos Colombia. https://www.datos.gov.co/d/uejq-wxrr

National Oceanic and Atmospheric Administration [NOAA], Climate Prediction Center. (2026). *Oceanic Niño Index (ONI)* [Conjunto de datos]. https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt

---
Sandra Milena Barona Ramírez · Universidad del Valle · GIFINC
