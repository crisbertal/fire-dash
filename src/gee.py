import geemap
import ee
import pandas as pd
import geopandas as gpd
from datetime import datetime
import numpy as np

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
    adm2 = country_df.loc[:, ["ADM1_NAME",
                              "ADM2_NAME", "geometry"]].set_crs(4326)
    # si ya existe solo inserta los valores nuevos
    adm2.to_postgis("provincias", engine, if_exists="append", chunksize=10000)


# ---------------------------------------------------------------------------
# DEPRECADO
def load_final_perimeter_postgis() -> None:
    ''' Carga los perimetros finales de incendios desde 2000 a 2020 '''
    # cargar la capa de españa
    espana = ee.FeatureCollection("FAO/GAUL/2015/level2") \
               .filter(ee.Filter.eq("ADM0_CODE", 229))

    andalucia = espana.filter(
        ee.Filter.stringStartsWith("ADM1_NAME", "Andaluc"))
    huelva = andalucia.filter(ee.Filter.stringStartsWith("ADM2_NAME", "Huelv"))

    # TODO ahora mismo solo huelva para pruebas. Despues se deben cargar todas
    # las provincias

    # recoger datos de incendios solo dentro de españa
    fire = ee.FeatureCollection("JRC/GWIS/GlobFire/v2/FinalPerimeters") \
             .filterBounds(andalucia)

    # CRS WGS84 que es el que carga GEE
    gdf = geemap.ee_to_geopandas(fire).set_crs("4326")

    # sobran 3 ceros desde GEE en el epoch. +2 por el timezone de España
    gdf["start_date"] = gdf["IDate"].map(
        lambda x: datetime.fromtimestamp(x/1000 + 2))
    gdf["end_date"] = gdf["FDate"].map(
        lambda x: datetime.fromtimestamp(x/1000 + 2))

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
   # gdf.to_postgis("perimetrofuego", engine, if_exists="append", chunksize=10000)

    print(gdf)

# ---------------------------------------------------------------------------


def load_fire_file() -> None:
    # gdf = gpd.read_file(
    #     "../data/database_incendios_espana.geojson").dropna().to_crs("EPSG:3035")

    # por el motivo que sea en algunos casos mete una columna "mean" que no he conseguido detectar
    gdf = gpd.read_file(
        "../data/database_incendios.geojson").drop(columns=["mean"]).dropna().to_crs("EPSG:3035")

    # calcular el area directamente aqui
    gdf["perim_area"] = gdf["geometry"].area / 10000

    gdf["sev_area"] = sum([gdf["sev_highseverity"],
                           gdf["sev_lowseverity"],
                           gdf["sev_moderateseverity"],
                           gdf["sev_regrowth"],
                           gdf["sev_unburned"]])

    # comprobar que incendios entran en una sola foto de landsat
    gdf["sev_check"] = np.floor(
        gdf["perim_area"]) - np.floor(gdf["sev_area"])

    # incendios validos para subir a postgis
    gdf = gdf.loc[gdf["sev_check"] <= 1, :]

    # transformar temperatura a celsius
    gdf["clima_temp_max"] = gdf["clima_temp_max"] - 273.15
    gdf["clima_temp_min"] = gdf["clima_temp_min"] - 273.15
    gdf["clima_temp_media"] = gdf["clima_temp_media"] - 273.15

    # velocidad del viento a partir de componentes
    # -- comparar luego con la obtenida en la capa de clima2
    gdf["viento_velocidad"] = np.sqrt(
        np.power(gdf["viento_u_comp"], 2) + np.power(gdf["viento_v_comp"], 2))

    # calcular direccion del viento
    # https://www.silviaalonsoperez.com/2014/06/direccion-y-velocidad-del-viento-con-componentes-meridional-y-zonal/
    gdf["viento_direccion_bruta"] = np.arctan2(
        gdf["viento_u_comp"], gdf["viento_v_comp"]) * 180 / np.pi
    gdf["viento_direccion"] = (
        gdf["viento_direccion_bruta"] + 360) % 360

    # pasar las fechas a string (conservando los epoch tambien)
    gdf["fdate_string"] = gdf["FDate"].map(
        lambda x: datetime.fromtimestamp(x/1000 + 2))
    gdf["idate_string"] = gdf["IDate"].map(
        lambda x: datetime.fromtimestamp(x/1000 + 2))
    gdf["sev_postfiredate_string"] = gdf["sev_postfiredate"].map(
        lambda x: datetime.fromtimestamp(x/1000 + 2))
    gdf["sev_prefiredate_string"] = gdf["sev_prefiredate"].map(
        lambda x: datetime.fromtimestamp(x/1000 + 2))

    # subir a postgis
    # -- eliminar columnas que no van a postgis
    # -- cambiar a wgs84 antes de subirlas
    gdf = gdf.drop(columns=["sev_area", "sev_check",
                   "viento_direccion_bruta"]).to_crs("EPSG:4326")
    print(gdf.info())

    # gdf.to_postgis("incendios", engine, if_exists="append", chunksize=10000)

    def check_areas(gdf):
        '''comprobar que las areas son correctas'''

        gdf["sev_area"] = sum([gdf["sev_highseverity"],
                               gdf["sev_lowseverity"],
                               gdf["sev_moderateseverity"],
                               gdf["sev_regrowth"],
                               gdf["sev_unburned"]])

        gdf["slope_area"] = sum([gdf["topo_slopei"],
                                 gdf["topo_slopeii"],
                                 gdf["topo_slopeiii"],
                                 gdf["topo_slopeiv"],
                                 gdf["topo_slopev"],
                                 gdf["topo_slopevi"]])

        gdf["orientacion_area"] = sum([gdf["topo_este"],
                                       gdf["topo_noreste"],
                                       gdf["topo_noroeste"],
                                       gdf["topo_norte"],
                                       gdf["topo_oeste"],
                                       gdf["topo_sur"],
                                       gdf["topo_sureste"],
                                       gdf["topo_suroeste"]])

        gdf["usos_suelo_area"] = sum([gdf["m111"], gdf["m112"], gdf["m121"], gdf["m122"],
                                      gdf["m123"], gdf["m124"], gdf["m131"], gdf["m132"],
                                      gdf["m133"], gdf["m141"], gdf["m142"], gdf["m211"],
                                      gdf["m212"], gdf["m213"], gdf["m221"], gdf["m222"],
                                      gdf["m223"], gdf["m231"], gdf["m241"], gdf["m242"],
                                      gdf["m243"], gdf["m244"], gdf["m311"], gdf["m312"],
                                      gdf["m313"], gdf["m321"], gdf["m322"], gdf["m323"],
                                      gdf["m324"], gdf["m331"], gdf["m332"], gdf["m333"],
                                      gdf["m334"], gdf["m335"], gdf["m411"], gdf["m412"],
                                      gdf["m421"], gdf["m422"], gdf["m423"], gdf["m511"],
                                      gdf["m512"], gdf["m521"], gdf["m522"], gdf["m523"]])

        print(gdf.loc[:, ["perim_area", "sev_area",
                          "slope_area", "orientacion_area", "usos_suelo_area"]])

        # comprobar que sev entra en perimetro y que el incendio entra en una imagen
        gdf["sev_check"] = np.floor(
            gdf["perim_area"]) - np.floor(gdf["sev_area"])
        print("comprobacion: \n", gdf.loc[gdf["sev_check"] > 1, [
            "sev_check", "perim_area", "sev_area", "usos_suelo_area"]])


# ---------------------------------------------------------------------------
# EJECUCION
# load_counties_postgis()
# load_fired_postgis()
# insert_firecci_potgis()
# load_final_perimeter_postgis()
load_fire_file()
