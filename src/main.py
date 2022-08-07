import plotly.express as px
import plotly.graph_objects as go

from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
from sqlalchemy import create_engine

import spquery as spq

# Conexion a la BD
engine = create_engine("postgresql://postgres:admin@localhost:5432/fire")

# Aplicacion dash
app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

# estilo para Sidebar fija
# https://dash-bootstrap-components.opensource.faculty.ai/examples/simple-sidebar/
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
}

# estilo para el panel de graficas
CONTENT_STYLE = {
    "margin-left": "18rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
}

app.layout = html.Div([
    html.Div(
        [
            html.H2("Fueguito 🔥", className="display-8"),
            html.Hr(),
            html.P(
                "A simple sidebar layout with navigation links", className="lead"
            ),
            # TODO poner para que sea con las comunidades y despues provincias
            dcc.Dropdown(['Murcia', 'Huelva', 'Sevilla', 'Lugo',
                          'La Rioja', 'Badajoz'], 'Huelva', id="provincia-dropdown"),
        ],
        style=SIDEBAR_STYLE,
    ),
    html.Div([
        dbc.Row(
            [
                dbc.Col(dcc.Graph(id='provincia-map')),
                dbc.Col(dcc.Graph(id='usos-donut')),
            ]
        ),
    ], style=CONTENT_STYLE)
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
    fig = go.Figure(
        data=[go.Pie(labels=labels, values=values, hole=.3)])
    # hace que la info se muestre dentro del sector
    fig.update_traces(textposition='inside')
    # pone un tamanio minimo. Si no cabe, no lo muestra
    fig.update_layout(uniformtext_minsize=12,
                      uniformtext_mode='hide',
                      transition_duration=500,
                      margin=dict(t=0, b=0, l=0, r=0))

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
