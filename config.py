"""Parámetros del observatorio: fuentes oficiales, rutas y constantes."""
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
ESTATICO = RAIZ / "data" / "estatico"
PROCESADO = RAIZ / "data" / "procesado"
CRUDO = RAIZ / "data" / "crudo"

# Subzona hidrográfica del distrito de riego RUT (Roldanillo, La Unión, Toro)
SUBZONA_RUT = 2608

# --- Evaluaciones Agropecuarias Municipales (EVA), MADR-UPRA, Datos Abiertos Colombia ---
EVA_ID = "uejq-wxrr"  # EVA 2019-2025, base agrícola
EVA_URL_CSV = f"https://www.datos.gov.co/api/views/{EVA_ID}/rows.csv?accessType=DOWNLOAD"
EVA_URL_FICHA = f"https://www.datos.gov.co/d/{EVA_ID}"
# Cultivos y desagregaciones de la base de la tesis
EVA_DESAGREGACIONES = {
    "Arroz": ["Arroz riego", "Arroz secano manual", "Arroz secano mecanizado"],
    "Caña": ["Caña de azúcar", "Caña miel", "Caña panelera"],
    "Maíz": ["Maíz amarillo tecnificado", "Maíz amarillo tradicional", "Maíz blanco tecnificado",
             "Maíz blanco tradicional", "Maíz tecnificado", "Maíz tradicional"],
    "Papa": ["Papa criolla", "Papa todas las variedades"],
}

# --- Índice Oceánico de El Niño (ONI), NOAA Climate Prediction Center ---
ONI_URL = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"
ONI_UMBRAL = 0.5          # °C
ONI_TEMPORADAS_MIN = 5    # temporadas trimestrales consecutivas para declarar un episodio

# --- Caudal diario: DHIME del IDEAM (descarga manual) ---
DHIME_URL = "http://dhime.ideam.gov.co/atencionciudadano/"

# Nota obligatoria por las condiciones de uso del SIRH
NOTA_IDEAM = ("Los datos de concesiones provienen del Sistema de Información del Recurso Hídrico (SIRH) "
              "del IDEAM. Los resultados son elaboración propia y no constituyen cifras oficiales del IDEAM.")

TIEMPO_ESPERA = 120  # segundos para las descargas
