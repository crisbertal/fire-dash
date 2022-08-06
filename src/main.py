import plotly.express as px
import plotly.graph_objects as go

from dash import Dash, dcc, html, Input, Output
from sqlalchemy import create_engine

import spquery as spq

# Conexion a la BD
engine = create_engine("postgresql://postgres:admin@localhost:5432/fire")

# Aplicacion dash
app = Dash(__name__)

app.layout = html.Div([
    # TODO poner para que sea con las comunidades y despues provincias
    dcc.Dropdown(['Murcia', 'Huelva', 'Sevilla', 'Lugo',
                 'La Rioja', 'Badajoz'], 'Huelva', id="provincia-dropdown"),
    dcc.Graph(id='provincia-map'),
    dcc.Graph(id='usos-donut'),
])


@app.callback(
    Output('provincia-map', 'figure'),
    Input('provincia-dropdown', 'value'))
def update_map(provincia):
    gdf, geojson = spq.get_fire_area_provincia(
        engine, "2013-01-01", "2018-01-01", provincia)

    fig = px.choropleth_mapbox(gdf,
                               geojson=geojson,
                               locations='ADM2_NAME',
                               featureidkey='properties.ADM2_NAME',
                               color='area_incendios',
                               mapbox_style='carto-positron',
                               color_continuous_scale="Viridis",
                               center={'lat': 40, 'lon': -3},
                               opacity=0.5,
                               zoom=4)

    fig.update_layout(transition_duration=500)

    return fig


def use_conversion(use):
    dict_usos = {
        "m111": "Continuous urban fabric",
        "m112": "Discontinuous urban fabric",
        "m121": "Industrial or commercial units",
        "m122": "Road and rail networks and associated land",
        "m123": "Port areas",
        "m124": "Airports",
        "m131": "Mineral extraction sites",
        "m132": "Dump sites",
        "m133": "Construction sites",
        "m141": "Green urban areas",
        "m142": "Sport and leisure facilities",
        "m211": "Non-irrigated arable land",
        "m212": "Permanently irrigated land",
        "m213": "Rice fields",
        "m221": "Vineyards",
        "m222": "Fruit trees and berry plantations",
        "m223": "Olive groves",
        "m231": "Pastures",
        "m241": "Annual crops associated with permanent crops",
        "m242": "Complex cultivation patterns",
        "m243": "Land principally occupied by agriculture, with significant areas of natural vegetation",
        "m244": "Agro-forestry areas",
        "m311": "Broad-leaved forest",
        "m312": "Coniferous forest",
        "m313": "Mixed forest",
        "m321": "Natural grasslands",
        "m322": "Moors and heathland",
        "m323": "Sclerophyllous vegetation",
        "m324": "Transitional woodland-shrub",
        "m331": "Beaches, dunes, sands",
        "m332": "Bare rocks",
        "m333": "Sparsely vegetated areas",
        "m334": "Burnt areas",
        "m335": "Glaciers and perpetual snow",
        "m411": "Inland marshes",
        "m412": "Peat bogs",
        "m421": "Salt marshes",
        "m422": "Salines",
        "m423": "Intertidal flats",
        "m511": "Water courses",
        "m512": "Water bodies",
        "m521": "Coastal lagoons",
        "m522": "Estuaries",
        "m523": "Sea and ocean"
    }
    return dict_usos[use]


@app.callback(
    Output('usos-donut', 'figure'),
    Input('provincia-dropdown', 'value'))
def update_usos_suelo_chart(provincia):
    gdf, geojson = spq.get_fire_area_provincia(
        engine, "2013-01-01", "2018-01-01", provincia)

    # elimina las columnas con valor 0
    gdf = gdf.loc[:, (gdf != 0).any(axis=0)]

    # selecciona solo las columnas de uso de suelo
    usos = gdf.loc[:, [m for m in gdf.columns if m.startswith('m')]]

    labels = [use_conversion(m) for m in usos.columns]
    values = usos.loc[0, :].values

    # Use `hole` to create a donut-like pie chart
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.3)])
    fig.update_layout(transition_duration=500)

    return fig


if __name__ == "__main__":
    app.run_server(debug=True)


# %%
# Ejecuta la consulta desde el repositorio de queries
'''
gdf, geojson = spq.get_fire_area_provincia(engine)

app.layout = html.Div(
    children=[
        html.H1(children="Datos de incendios de Andalucía",),
        dcc.Graph(
            figure=px.choropleth_mapbox(gdf,
                                        geojson=geojson,
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
'''

# %%


# Conexion a la BD
engine = create_engine("postgresql://postgres:admin@localhost:5432/fire")
