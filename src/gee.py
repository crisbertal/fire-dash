import geemap 
import ee
import pandas as pd
import geopandas as gpd
from datetime import datetime

from sqlalchemy import create_engine

# Inicio de la api de gee
ee.Initialize()

# Inicio del objeto para llamar a la BD
# llama al tipo de BD, usuario@contrasena/direccionBD/nombreBD
engine = create_engine("postgresql://postgres:admin@localhost:5432/fire")

# ---------------------------------------------------------------------------
# Limitar la zona de extraccion de datos. Para españa en principio
def load_counties_postgis() -> None:
    country = ee.FeatureCollection("FAO/GAUL/2015/level2") \
                .filter(ee.Filter.eq('ADM0_CODE', 229))

    country_df = geemap.ee_to_geopandas(country)
    # se asigna el crs por defecto WGS84
    adm2 = country_df.loc[:, ['ADM1_NAME', 'ADM2_NAME', 'geometry']].set_crs(4326)
    # si ya existe solo inserta los valores nuevos
    adm2.to_postgis("provincias", engine, if_exists="append", chunksize=10000)

# ---------------------------------------------------------------------------
# Recoger datos de perimetro de incendio en España
def load_fired_postgis() -> None: 
    # que cargue desde 2010 a 2020
    year_list = list(range(10, 22, 1))

    # cargar la capa de españa
    country = ee.FeatureCollection("FAO/GAUL/2015/level0") \
                .filter(ee.Filter.eq('ADM0_CODE', 229))

    frames = []
    for year in year_list:
        # recoger datos de incendios solo dentro de españa
        fire = ee.FeatureCollection(f"JRC/GWIS/GlobFire/v2/DailyPerimeters/20{year}") \
                 .filterBounds(country)
        frames.append(geemap.ee_to_geopandas(fire))

    # CRS WGS84 que es el que carga GEE
    gdf = gpd.GeoDataFrame(pd.concat(frames)).set_crs(4326)
    # sobran 3 ceros desde GEE en el epoch. +2 por el timezone de España
    gdf['Date'] = gdf['IDate'].map(lambda x: datetime.fromtimestamp(x/1000 + 2))
    # si ya existe la tabla solo agrega los valores nuevos
    gdf.to_postgis("perimetrofuego", engine, if_exists="append", chunksize=10000)

# ---------------------------------------------------------------------------
# EJECUCION
# load_counties_postgis()
load_fired_postgis()














