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


def get_incendios_comunidad(engine, idate, fdate, comunidad):
    query = f"""
    select A.*, B.name
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
