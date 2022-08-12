import plotly.express as px
import plotly.graph_objects as go

from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
from datetime import date
from sqlalchemy import create_engine

import spquery as spq
import layout
import utils
import id
import components as cp

# ---------------------------------------------------------------------------------
# ESTILOS
# ---------------------------------------------------------------------------------
# estilo para Sidebar fija
# https://dash-bootstrap-components.opensource.faculty.ai/examples/simple-sidebar/
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "padding": "2rem 1rem",
    "background-color": "coral",
}

# estilo para el panel de graficas
CONTENT_STYLE = {
    "margin-left": "16rem",
    "padding": "2rem 1rem",
    "background-color": "#F2F2F2",
}

# ---------------------------------------------------------------------------------
# COMPONENTES
# ---------------------------------------------------------------------------------

df = px.data.iris()


def draw_text():
    return html.Div([
        dbc.Card(
            dbc.CardBody([
                html.Div([
                    html.H2("Text"),
                ], style={'textAlign': 'center', 'height': '3rem'})
            ])
        ),
    ])

# Iris bar figure


def draw_figure(altura):
    return html.Div([
        dbc.Card(
            dbc.CardBody([
                dcc.Graph(
                    figure=px.bar(
                        df, x="sepal_width", y="sepal_length", color="species", height=altura
                    ).update_layout(
                        template='plotly_dark',
                        plot_bgcolor='rgba(0, 0, 0, 0)',
                        paper_bgcolor='rgba(0, 0, 0, 0)',
                    ),
                    config={
                        'displayModeBar': False
                    }
                )
            ])
        ),
    ])


# ---------------------------------------------------------------------------------
# APLICACION DASH
# ---------------------------------------------------------------------------------
# Aplicacion dash
app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = html.Div([
    html.Div(
        [
            html.H2("Fueguito 🔥", className="display-8"),
            html.Hr(),
            dcc.DatePickerRange(
                id=id.DATE_PICKER,
                min_date_allowed=date(2013, 1, 1),
                max_date_allowed=date(2020, 12, 31),
                # initial_visible_month=date(2017, 8, 5),
                # end_date=date(2017, 8, 25)
            ),
            html.Hr(),
            # TODO poner para que sea con las comunidades y despues provincias
            dcc.Dropdown(['Murcia', 'Huelva', 'Sevilla', 'Lugo',
                          'La Rioja', 'Badajoz'], 'Huelva', id=id.PROVINCIA_MENU),
        ],
        style=SIDEBAR_STYLE,
    ),
    # el layout de la pantalla se divide en 12 columnas.
    # width indica cuales de ellas ocupan el componente
    html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Row([
                    dbc.Col([cp.draw_numero_incendios()]),
                    dbc.Col([cp.draw_area_incendios()])
                ]),
                html.Br(),
                # dbc.Row([cp.draw_mapa_incendios()])
            ], width=6),
            dbc.Col([
                dbc.Row([draw_figure(270)]),
                html.Br(),
                dbc.Row([draw_figure(270)])
            ], width=6),
        ], align='center'),
        html.Br(),
        dbc.Row([
            dbc.Col([draw_figure(400)], width=6),
            dbc.Col([draw_figure(400)], width=6)
        ]),
        html.Br(),
        dbc.Row([
            draw_figure(500)
        ])
    ], style=CONTENT_STYLE)
])
'''
app.layout = html.Div([
    html.Div(
        [
            html.H2("Fueguito 🔥", className="display-8"),
            html.Hr(),
            # TODO poner para que sea con las comunidades y despues provincias
            dcc.Dropdown(['Murcia', 'Huelva', 'Sevilla', 'Lugo',
                          'La Rioja', 'Badajoz'], 'Huelva', id="provincia-dropdown"),
        ],
        style=SIDEBAR_STYLE,
    ),
    html.Div([
        dbc.Row([
                dbc.Col([
                    dbc.Row([
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H4("Número de incendios",
                                                    className="card-title"),
                                            html.P(
                                                className="card-text", id="card-num-incendios"
                                            ),
                                        ]
                                    ),
                                ],
                                style={"width": "18rem"},
                            ),
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.H4("Superficie quemada",
                                                    className="card-title"),
                                            html.P(
                                                className="card-text", id="card-num-area"
                                            ),
                                        ]
                                    ),
                                ],
                                style={"width": "18rem"},
                            ),
                            ]),

                    dbc.Card(
                        [
                            dbc.CardBody(
                                [
                                    dcc.Graph(id='provincia-map'),
                                ]
                            ),
                        ],
                    ),
                ]),
                dbc.Col(dcc.Graph(id='usos-donut')),
                ]
                ),
    ], style=CONTENT_STYLE)
])
'''

# ---------------------------------------------------------------------------------
# CALLBACKS
# ---------------------------------------------------------------------------------
# Conexion a la BD
engine = create_engine("postgresql://postgres:admin@localhost:5432/fire")


@app.callback(
    Output(id.NUMERO_INCENDIOS, 'children'),
    Input(id.PROVINCIA_MENU, 'value'),
    Input(id.DATE_PICKER, 'start_date'),
    Input(id.DATE_PICKER, 'end_date'))
def update_numero_incendios(provincia, idate, fdate):
    gdf, geojson = spq.get_fire_area_provincia(
        engine, idate, fdate, provincia)

    # elimina las columnas con valor 0
    gdf = gdf.loc[:, (gdf != 0).any(axis=0)]

    # Coge el valor de numero de incendios
    num = gdf.loc[:, ["numero_incendios"]].values[0][0]

    return html.P(f"{num}")


@app.callback(
    Output(id.AREA_INCENDIOS, 'children'),
    Input(id.PROVINCIA_MENU, 'value'),
    Input(id.DATE_PICKER, 'start_date'),
    Input(id.DATE_PICKER, 'end_date'))
def update_area_quemada(provincia, idate, fdate):
    gdf, geojson = spq.get_fire_area_provincia(
        engine, idate, fdate, provincia)

    # elimina las columnas con valor 0
    gdf = gdf.loc[:, (gdf != 0).any(axis=0)]

    # Coge el valor de numero de incendios
    num = gdf.loc[:, ["area_incendios"]].values[0][0]

    return f"{round(num)} ha"


@app.callback(
    Output(id.MAPA_INCENDIOS, 'figure'),
    Input('provincia-dropdown', 'value'))
def update_bubble_map_incendios(provincia):
    gdf, geojson = spq.get_fire_geometry(
        engine, "2013-01-01", "2018-01-01", provincia)

    fig = px.choropleth_mapbox(gdf,
                               geojson=geojson,
                               locations='id',
                               featureidkey='properties.id',
                               color='area_incendio',
                               mapbox_style='carto-positron',
                               color_continuous_scale="Viridis",
                               center={'lat': 40, 'lon': -3},
                               opacity=0.5,
                               zoom=4)

    fig.update_layout(transition_duration=500,
                      margin=dict(t=0, b=0, l=0, r=0))

    return fig


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
    # TODO no usar un pie chart porque hay muchos valores
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
