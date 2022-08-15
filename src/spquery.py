import json

import geopandas as gpd


def get_query(engine, query):
    ''' 
    Envia la query a postgis a traves del engine pasado por parametro. 
    Devuelve el geojson obtenido con el WGS84 con sistema de referencia
    '''
    # Recoge el resultado de la consulta de postgis
    gdf = gpd.GeoDataFrame.from_postgis(query,
                                        engine,
                                        geom_col="geometry")

    # Agregar el CRS al geojson porque pandas no lo hace todavia
    # Aqui agrega el WGS84 que es el usado por los frameworks para mostrar
    # mapas
    gjson = json.loads(gdf.to_json())
    gjson.update({"crs": {
        "type": "name",
        "properties": {
                "name": "urn:ogc:def:crs:OGC:1.3:CRS84"
        }
    }, })

    return (gdf, gjson)


def get_fire_area_bounds(engine):
    ''' Devuelve el total de area quemada por provincia '''

    query = f"""
        select 
            B."ADM2_NAME",
            SUM(ST_Area(ST_Transform(A.geometry, utmzone(ST_Centroid(A.geometry)))) / 10000) as area_incendio,
            B.geometry
        from 
            pronvincias B,
            incendios A
        where
            ST_Intersects(A.geometry, B.geometry)
        group by 
            B."ADM2_NAME",
            B.geometry 
    """

    return get_query(engine, query)


def get_fire_area_provincia(engine, idate, fdate, provincia):
    ''' Devuelve los datos espaciales del incendio agregados por
    provincia para el rango de fechas indicadas'''

    query = f"""
    select 
        B."ADM2_NAME",
        SUM(A.perim_area) as area_incendios,
        COUNT(A.id) as numero_incendios,
        SUM(A.sev_highseverity) as sev_highseverity,
        SUM(A.sev_lowseverity) as sev_lowseverity,
        SUM(A.sev_moderateseverity) as sev_moderateseverity,
        SUM(A.sev_regrowth) as sev_regrowth,
        SUM(A.sev_unburned) as sev_unburned,
        SUM(A.topo_este) as topo_este,
        SUM(A.topo_noreste) as topo_noreste,
        SUM(A.topo_noroeste) as topo_noroeste,
        SUM(A.topo_norte) as topo_norte,
        SUM(A.topo_oeste) as topo_oeste,
        SUM(A.topo_slopei) as topo_slopei,
        SUM(A.topo_slopeii) as topo_slopeii,
        SUM(A.topo_slopeiii) as topo_slopeiii,
        SUM(A.topo_slopeiv) as topo_slopeiv,
        SUM(A.topo_slopev) as topo_slopev,
        SUM(A.topo_slopevi) as topo_slopevi,
        SUM(A.topo_sur) as topo_sur,
        SUM(A.topo_sureste) as topo_sureste,
        SUM(A.topo_suroeste) as topo_suroeste,
        SUM(A.m111) as m111,
        SUM(A.m112) as m112,
        SUM(A.m121) as m121,
        SUM(A.m122) as m122,
        SUM(A.m123) as m123,
        SUM(A.m124) as m124,
        SUM(A.m131) as m131,
        SUM(A.m132) as m132,
        SUM(A.m133) as m133,
        SUM(A.m141) as m141,
        SUM(A.m142) as m142,
        SUM(A.m211) as m211,
        SUM(A.m212) as m212,
        SUM(A.m213) as m213,
        SUM(A.m221) as m221,
        SUM(A.m222) as m222,
        SUM(A.m223) as m223,
        SUM(A.m231) as m231,
        SUM(A.m241) as m241,
        SUM(A.m242) as m242,
        SUM(A.m243) as m243,
        SUM(A.m244) as m244,
        SUM(A.m311) as m311,
        SUM(A.m312) as m312,
        SUM(A.m313) as m313,
        SUM(A.m321) as m321,
        SUM(A.m322) as m322,
        SUM(A.m323) as m323,
        SUM(A.m324) as m324,
        SUM(A.m331) as m331,
        SUM(A.m332) as m332,
        SUM(A.m333) as m333,
        SUM(A.m334) as m334,
        SUM(A.m335) as m335,
        SUM(A.m411) as m411,
        SUM(A.m412) as m412,
        SUM(A.m421) as m421,
        SUM(A.m422) as m422,
        SUM(A.m423) as m423,
        SUM(A.m511) as m511,
        SUM(A.m512) as m512,
        SUM(A.m521) as m521,
        SUM(A.m522) as m522,
        SUM(A.m523) as m523,
        B.geometry
    from 
        provincias B,
        incendios A
    where
        ST_Intersects(A.geometry, B.geometry) and
        A.idate_string between '{idate}' and '{fdate}' and
        B."ADM2_NAME" like '{provincia}'
    group by 
        B."ADM2_NAME",
        B.geometry 
    """

    return get_query(engine, query)


def get_fire_geometry(engine, idate, fdate, provincia):
    query = f"""
    select A.geometry,
        A.perim_area as area_incendio,
        A.id
    from 
        provincias B,
        incendios A

    where
        ST_Intersects(A.geometry, B.geometry) and
        A.idate_string between '{idate}' and '{fdate}' and
        B."ADM2_NAME" like '{provincia}'
    """

    return get_query(engine, query)


def get_numero_incendios(engine, idate, fdate, provincia):
    ''' Devuelve el numero de incendios en el rango y geometria indicada '''

    query = f"""
    select 
        COUNT(A.id) as numero_incendios,
    from 
        provincias B,
        incendios A
    where
        ST_Intersects(A.geometry, B.geometry) and
        A.idate_string between '{idate}' and '{fdate}' and
        B."ADM2_NAME" like '{provincia}'
    """

    return get_query(engine, query)


def get_fire_area_comunidad(engine, idate, fdate, comunidad):
    ''' Devuelve los datos espaciales del incendio agregados por
    comunidad autonoma para el rango de fechas indicadas'''

    query = f"""
    select 
        B.name,
        SUM(A.perim_area) as area_incendios,
        COUNT(A.id) as numero_incendios,
        SUM(A.sev_highseverity) as sev_highseverity,
        SUM(A.sev_lowseverity) as sev_lowseverity,
        SUM(A.sev_moderateseverity) as sev_moderateseverity,
        SUM(A.sev_regrowth) as sev_regrowth,
        SUM(A.sev_unburned) as sev_unburned,
        SUM(A.topo_este) as topo_este,
        SUM(A.topo_noreste) as topo_noreste,
        SUM(A.topo_noroeste) as topo_noroeste,
        SUM(A.topo_norte) as topo_norte,
        SUM(A.topo_oeste) as topo_oeste,
        SUM(A.topo_slopei) as topo_slopei,
        SUM(A.topo_slopeii) as topo_slopeii,
        SUM(A.topo_slopeiii) as topo_slopeiii,
        SUM(A.topo_slopeiv) as topo_slopeiv,
        SUM(A.topo_slopev) as topo_slopev,
        SUM(A.topo_slopevi) as topo_slopevi,
        SUM(A.topo_sur) as topo_sur,
        SUM(A.topo_sureste) as topo_sureste,
        SUM(A.topo_suroeste) as topo_suroeste,
        SUM(A.m111) as m111,
        SUM(A.m112) as m112,
        SUM(A.m121) as m121,
        SUM(A.m122) as m122,
        SUM(A.m123) as m123,
        SUM(A.m124) as m124,
        SUM(A.m131) as m131,
        SUM(A.m132) as m132,
        SUM(A.m133) as m133,
        SUM(A.m141) as m141,
        SUM(A.m142) as m142,
        SUM(A.m211) as m211,
        SUM(A.m212) as m212,
        SUM(A.m213) as m213,
        SUM(A.m221) as m221,
        SUM(A.m222) as m222,
        SUM(A.m223) as m223,
        SUM(A.m231) as m231,
        SUM(A.m241) as m241,
        SUM(A.m242) as m242,
        SUM(A.m243) as m243,
        SUM(A.m244) as m244,
        SUM(A.m311) as m311,
        SUM(A.m312) as m312,
        SUM(A.m313) as m313,
        SUM(A.m321) as m321,
        SUM(A.m322) as m322,
        SUM(A.m323) as m323,
        SUM(A.m324) as m324,
        SUM(A.m331) as m331,
        SUM(A.m332) as m332,
        SUM(A.m333) as m333,
        SUM(A.m334) as m334,
        SUM(A.m335) as m335,
        SUM(A.m411) as m411,
        SUM(A.m412) as m412,
        SUM(A.m421) as m421,
        SUM(A.m422) as m422,
        SUM(A.m423) as m423,
        SUM(A.m511) as m511,
        SUM(A.m512) as m512,
        SUM(A.m521) as m521,
        SUM(A.m522) as m522,
        SUM(A.m523) as m523,
        B.geometry
    from 
        comunidades B,
        incendios A
    where
        ST_Intersects(A.geometry, B.geometry) and
        A.idate_string between '{idate}' and '{fdate}' and
        B.name like '{comunidad}'
    group by 
        B.name,
        B.geometry 
    """

    return get_query(engine, query)


def get_bubblemap_data(engine, idate, fdate, comunidad):
    # ST_Centroid(A.geometry) as geometry,
    query = f"""
    select 
        A.id,
        A."IDate",
        A.geometry,
        A.perim_area as area_incendio,
        A.sev_highseverity,
        A.sev_lowseverity,
        A.sev_moderateseverity,
        A.sev_regrowth,
        A.sev_unburned
    from 
        comunidades B,
        incendios A
    where
        ST_Intersects(A.geometry, B.geometry) and
        A.idate_string between '{idate}' and '{fdate}' and
        B.name like '{comunidad}'
    """

    return get_query(engine, query)


def get_climate_data(engine, idate, fdate, comunidad):
    query = f"""
    select 
        A.id,
        A.perim_area as area_incendio,
        A.geometry,
        A.viento_velocidad,
        A.viento_direccion,
        A.clima_hum_suelo,
        clima_temp_max,
        clima_temp_media,
        clima_temp_min
    from 
        comunidades B,
        incendios A
    where
        ST_Intersects(A.geometry, B.geometry) and
        A.idate_string between '{idate}' and '{fdate}' and
        B.name like '{comunidad}'
    """

    return get_query(engine, query)


def get_comunidades(engine):
    query = "select * from comunidades"
    return gpd.GeoDataFrame.from_postgis(query, engine, geom_col="geometry")


def get_incendios(engine):
    query = "select * from incendios"
    return gpd.GeoDataFrame.from_postgis(query, engine, geom_col="geometry")
