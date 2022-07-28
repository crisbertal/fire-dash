import geemap 
import ee
import geetools
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
                .filter(ee.Filter.eq("ADM0_CODE", 229))

    country_df = geemap.ee_to_geopandas(country)
    # se asigna el crs por defecto WGS84
    adm2 = country_df.loc[:, ["ADM1_NAME", "ADM2_NAME", "geometry"]].set_crs(4326)
    # si ya existe solo inserta los valores nuevos
    adm2.to_postgis("provincias", engine, if_exists="append", chunksize=10000)


# ---------------------------------------------------------------------------
def load_final_perimeter_postgis() -> None: 
    ''' Carga los perimetros finales de incendios desde 2000 a 2020 '''
    # cargar la capa de españa
    espana = ee.FeatureCollection("FAO/GAUL/2015/level2") \
               .filter(ee.Filter.eq("ADM0_CODE", 229)) 

    andalucia = espana.filter(ee.Filter.stringStartsWith("ADM1_NAME", "Andaluc"))
    huelva = andalucia.filter(ee.Filter.stringStartsWith("ADM2_NAME", "Huelv"))

    # TODO ahora mismo solo huelva para pruebas. Despues se deben cargar todas 
    # las provincias 

    # recoger datos de incendios solo dentro de españa
    fire = ee.FeatureCollection("JRC/GWIS/GlobFire/v2/FinalPerimeters") \
             .filterBounds(andalucia)

    # CRS WGS84 que es el que carga GEE
    gdf = geemap.ee_to_geopandas(fire).set_crs("4326")

    # sobran 3 ceros desde GEE en el epoch. +2 por el timezone de España
    gdf["start_date"] = gdf["IDate"].map(lambda x: datetime.fromtimestamp(x/1000 + 2))
    gdf["end_date"] = gdf["FDate"].map(lambda x: datetime.fromtimestamp(x/1000 + 2))

    # TODO si lo quieres hacer para espania recuerda que tienes que filtrar los
    # incendios raros que ocupan todo el mundo

    # TODO refactoriza esto, porque es solo valido para Huelva
    # filtrar las entradas anomalas. En este caso 43 entradas
    gdf["area"] = gdf["geometry"].area
    gdf = gdf[gdf.area < 60000]

    # eliminar columnas que no son necesarias
    # el area la cojo desde PostGIS en las querys
    gdf = gdf.drop(columns=['IDate', 'FDate', 'area'])
    
    # si ya existe la tabla solo agrega los valores nuevos
    gdf.to_postgis("perimetrofuego", engine, if_exists="append", chunksize=10000)

# ---------------------------------------------------------------------------
# EJECUCION
# load_counties_postgis()
# load_fired_postgis()
# insert_firecci_potgis()
load_final_perimeter_postgis()















