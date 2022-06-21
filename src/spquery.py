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
    # Aqui agrega el WGS84 que es el por defecto en GEE
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
