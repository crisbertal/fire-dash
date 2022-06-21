# %%
from sqlalchemy import create_engine
import geopandas as gpd

import geemap
import ee

# %%
# Inicializar el modulo de GEE
ee.Initialize()

# Descargar datos de incendios entre las fechas indicadas para todo el mundo
# dataset = ee.ImageCollection('FIRMS').filter(
#     ee.Filter.date('2018-08-01', '2018-08-10'))

# print(dataset)
# print(type(dataset))

# %%
# Datos de fronteras de primer orden (comunidades)
data = ee.FeatureCollection("FAO/GAUL/2015/level2").filter(ee.Filter.eq(
    'ADM0_CODE', 229)).filter(ee.Filter.stringStartsWith('ADM1_NAME', 'Andalu'))

gdf = geemap.ee_to_geopandas(data)

# %%
states = ee.FeatureCollection("TIGER/2018/States")
gdf = geemap.ee_to_geopandas(states)
gdf.head(5)

# %%
gdf = gpd.GeoDataFrame.from_file('data/fire_andalucia2020.geojson')
gdf.head()

# %%
# motor para insertar valores en la BD
# llama al tipo de BD, usuario@contrasena/direccionBD/nombreBD
engine = create_engine("postgresql://postgres:admin@localhost:5432/fire")
print("conectado a BD")

# %%
# insertar las provincias en postgis
gdf.to_postgis("incendios", engine, if_exists="append", chunksize=10000)
print("Tabla agregada")


'''
select A."IDate", A."Id",
       ST_Area(ST_Transform(A.geometry, utmzone(ST_Centroid(A.geometry)))) / 10000 as area_incendio, 
       A.geometry
    from pronvincias B, incendios A
    where B."ADM2_NAME" = 'Huelva' and
          ST_Intersects(A.geometry, B.geometry) and
          ST_Area(ST_Transform(A.geometry, utmzone(ST_Centroid(A.geometry)))) / 10000 > 20
'''

'''
Area quemada por incendio en Huelva
select A."Id",
       ST_Area(ST_Transform(ST_Union(A.geometry), utmzone(ST_Centroid(ST_Union(A.geometry))))) / 10000 as area_quemada,
       ST_Union(A.geometry)
from incendios A, pronvincias B
where B."ADM2_NAME" = 'Huelva' and
      ST_Intersects(A.geometry, B.geometry)
group by A."Id"
'''

'''
Area quemada por provincias en 2020
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
# %%
query = "SELECT id, geometry FROM incendios, provincias WHERE ST_INTERSECTS(incendios.geometry, provincias.geometry) AND provincias.name = 'Huelva'"

# %%
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

gdf = gpd.GeoDataFrame.from_postgis(query, engine, geom_col="geometry")
gdf.explore()

# %%
gdf.plot(column='area_incendio', cmap='Blues', linewidth=1, edgecolor='0.9', legend = True)
# %%
import json 

with open("data/incendios.geojson", "r") as file:
    capa = json.load(file)

capa

# %%
gdf = gdf.drop(columns=['geometry'])
gdf.head()

# %%
geojson = gdf.to_json()
geojson = geojson.set_crs('EPSG:4326')
print(geojson)

# %%
# Este sale bien cargando desde un GeoJSON, que es el mismo gdf pero exportado
import plotly.express as px

fig = px.choropleth_mapbox(gdf, geojson=capa, 
                    locations='ADM2_NAME',
                    featureidkey='properties.provincia',
                    color='area_incendio',
                    mapbox_style='carto-positron',
                    color_continuous_scale="Viridis",
                    center={'lat': 37, 'lon': -6},
                    zoom=5)
                    
fig.show()

# %%
gdf = gdf.replace(['C�diz'],'Cadiz')
gdf = gdf.replace(['C�rdoba'],'Cordoba')
gdf = gdf.replace(['M�laga'],'Malaga')
gdf

# %%
gdf.to_file('data/incendio.geojson', driver='GeoJSON')

# %%
with open("data/incendio.geojson", "r") as file:
    capa = json.load(file)

capa
# %%
import json

gjson = json.loads(gdf.to_json())
type(gjson)

gjson.update({"crs": {
        "type": "name",
        "properties": {
            "name": "urn:ogc:def:crs:OGC:1.3:CRS84"
        }
    },})

print(gjson)


# %%
with open('data/prueba.geojson', 'w') as file:
    file.write(gdf.to_json())

# %%
import plotly.express as px

with open('data/prueba.geojson', 'r') as file:
    capa = json.load(file)

fig = px.choropleth_mapbox(gdf, geojson=gjson, 
                    locations='ADM2_NAME',
                    featureidkey='properties.ADM2_NAME',
                    color='area_incendio',
                    mapbox_style='carto-positron',
                    color_continuous_scale="Viridis",
                    center={'lat': 37, 'lon': -6},
                    opacity=0.5,
                    zoom=5)
                    
fig.show()

# %%
import dash
from dash import dcc
from dash import html
import plotly.express as px

app = dash.Dash(__name__)

app.layout = html.Div(
    children=[
        html.H1(children="Datos de incendios de Andalucía",),
        dcc.Graph(
            figure=px.choropleth_mapbox(gdf, geojson=gjson, 
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

app.run_server(debug=True)
