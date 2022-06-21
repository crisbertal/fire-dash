import json

import dash
import ee
import geemap
import geopandas as gpd
import plotly.express as px

from dash import dcc, html
from sqlalchemy import create_engine

# Conexion a la BD
engine = create_engine("postgresql://postgres:admin@localhost:5432/fire")

# Query a la BD
query = f'''
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
'''

# Cargar el resultado de la query en un dataframe
gdf = gpd.GeoDataFrame.from_postgis(query, engine, geom_col="geometry")

# Agregar el CRS al geojson porque pandas no lo hace todavia
# Aqui agrega el WGS84 que es el por defecto en GEE
gjson = json.loads(gdf.to_json())
gjson.update({"crs": {
        "type": "name",
        "properties": {
            "name": "urn:ogc:def:crs:OGC:1.3:CRS84"
        }
    }, })

# Aplicacion dash
app = dash.Dash(__name__)

app.layout = html.Div(
    children=[
        html.H1(children="Datos de incendios de Andalucía",),
        dcc.Graph(
            figure=px.choropleth_mapbox(gdf,
                                        geojson=gjson,
                                        locations='ADM2_NAME',
                                        featureidkey='properties.ADM2_NAME',
                                        color='area_incendio',
                                        mapbox_style='carto-positron',
                                        color_continuous_scale="Viridis",
                                        center={'lat': 37, 'lon': -6},
                                        opacity=0.5,
                                        zoom=5)
        ),
    ]
)

if __name__ == "__main__":
    app.run_server(debug=True)
