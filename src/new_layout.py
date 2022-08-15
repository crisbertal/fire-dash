from datetime import datetime

import numpy as np
import pandas as pd
import plotly.express as px
from dash import Dash, Input, Output, dcc, html
from sqlalchemy import create_engine

import spquery as spq
import utils

# ----------------------------------------------------------------------------
# DATA
# ----------------------------------------------------------------------------
engine = create_engine("postgresql://postgres:admin@localhost:5432/fire")
comunidad = "Galicia"
ifecha, ffecha = "2013-01-01", "2020-12-31"
data, geojson = spq.get_fire_area_comunidad(engine,
                                            ifecha,
                                            ffecha,
                                            comunidad)
climate_data = spq.get_climate_data(engine,
                                    ifecha,
                                    ffecha,
                                    comunidad)[0]

comunidades = spq.get_comunidades(engine)
incendios = spq.get_incendios(engine)


def process_severity(data):
    seve = data.loc[:, [s for s in data.columns if s.startswith('sev')]]
    labels = list(seve.columns)
    values = seve.loc[0, :].values
    return pd.DataFrame({'labels': labels, 'values': values})


def get_landcover_group1(value):
    if value.startswith('m1'):
        return 'Superficies artificiales'
    if value.startswith('m2'):
        return 'Zonas agrícolas'
    if value.startswith('m3'):
        return 'Zonas forestales o seminaturales'
    if value.startswith('m4'):
        return 'Humedales'
    if value.startswith('m5'):
        return 'Masas de agua'
    return 'No definido'


# TODO terminar los grupos restantes
def get_landcover_group2(value):
    if value.startswith('m21'):
        return 'Tierras de labor'
    if value.startswith('m22'):
        return 'Cultivos permanentes'
    if value.startswith('m23'):
        return 'Praderas'
    if value.startswith('m24'):
        return 'Zonas agrícolas heterogéneas'
    if value.startswith('m31'):
        return 'Bosques'
    if value.startswith('m32'):
        return 'Espacios de vegetación arbustiva y/o herbácea'
    if value.startswith('m33'):
        return 'Espacios abiertos con poca o sin vegetación'
    return 'No definido'


def process_landcover(data):
    # cambiar columnas por filas
    cover = data.loc[:, [c for c in data.columns if c.startswith('m')]]
    labels = list(cover.columns)
    values = cover.loc[0, :].values
    coverdf = pd.DataFrame({'clc': labels, 'area': values})

    coverdf['group1'] = coverdf.loc[:, 'clc'].map(
        lambda x: get_landcover_group1(x))
    coverdf['group2'] = coverdf.loc[:, 'clc'].map(
        lambda x: get_landcover_group2(x))
    coverdf['group3'] = coverdf.loc[:, 'clc'].map(
        lambda x: utils.use_conversion(x))

    return coverdf


def process_bubblemap_data(engine, ifecha, ffecha, comunidad):
    data, geojson = spq.get_bubblemap_data(engine,
                                           ifecha,
                                           ffecha,
                                           comunidad)

    # calcular la severidad media con la severidad moderada en procentaje
    # con respecto al total quemado

    data['sev_perc_moderate'] = pd.Series(data['sev_moderateseverity'] /
                                          data['area_incendio'] * 100).astype(int)

    data['sev_perc_high'] = pd.Series(data['sev_highseverity'] /
                                      data['area_incendio'] * 100).astype(int)

    data["fecha_inicio"] = data["IDate"].map(
        lambda x: datetime.fromtimestamp(x/1000 + 2).strftime("%d/%m/%Y"))

    # transformar los valores a enteros para que sea mas legible
    data["area_incendio"] = data["area_incendio"].astype(int)

    return (data, geojson)


bubbledata, geobubble = process_bubblemap_data(
    engine, ifecha, ffecha, comunidad)

# ----------------------------------------------------------------------------
# LAYOUT
# ----------------------------------------------------------------------------
external_stylesheets = [
    {
        "href": "https://fonts.googleapis.com/css2?"
                "family=Lato:wght@400;700&display=swap",
        "rel": "stylesheet",
    },
]

app = Dash(__name__, external_stylesheets=external_stylesheets)
app.layout = html.Div(
    children=[
        html.Div(
            children=[
                html.H1(children="Analítica de incendios",
                        className="header-title"),
            ],
            className="header",
        ),
        html.Div(
            children=[
                html.Div(
                    children=[
                        html.Div(children="Comunidad", className="menu-title"),
                        dcc.Dropdown(
                            id="comunidad-filter",
                            options=[
                                {"label": comunidad, "value": comunidad}
                                for comunidad in np.sort(comunidades.name)
                            ],
                            value="Andalucía",
                            clearable=False,
                            className="dropdown",
                        ),
                    ]
                ),
                html.Div(
                    children=[
                        html.Div(
                            children="Rango de fechas",
                            className="menu-title"
                        ),
                        dcc.DatePickerRange(
                            id="date-range",
                            min_date_allowed=datetime.fromtimestamp(
                                incendios.IDate.min()/1000),
                            max_date_allowed=datetime.fromtimestamp(
                                incendios.FDate.max()/1000),
                            start_date=datetime.fromtimestamp(
                                incendios.IDate.min()/1000),
                            end_date=datetime.fromtimestamp(
                                incendios.FDate.max()/1000),
                        ),
                    ]
                ),
            ],
            className="menu",
        ),
        html.Div(
            children=[
                html.Div(
                    children=dcc.Graph(
                        id="pie-severity",
                    ),
                    className="card",
                ),
                html.Div(
                    children=[
                        dcc.Graph(
                            id="sunburst-landcover",
                        ),
                    ],
                    className="card",
                ),
                html.Div(
                    children=[

                        dcc.Graph(
                            id="bubblemap-incendios",
                        ),
                    ], className="card",
                ),
                html.Div(
                    children=[
                        dcc.Graph(
                            id="scatter-clima"
                        )
                    ], className="card",
                )
            ],
            className="wrapper",
        ),
    ],
)


@app.callback(
    [
        Output('pie-severity', 'figure'),
        Output('sunburst-landcover', 'figure'),
        Output('bubblemap-incendios', 'figure'),
        Output('scatter-clima', 'figure')
    ],
    [
        Input('comunidad-filter', 'value'),
        Input('date-range', 'start_date'),
        Input('date-range', 'end_date')
    ]
)
def update_landcover(comunidad, idate, fdate):
    comunidad = comunidad
    ifecha, ffecha = idate, fdate

    print(comunidad)
    print(ifecha, ffecha)

    # queries
    data, geojson = spq.get_fire_area_comunidad(engine,
                                                ifecha,
                                                ffecha,
                                                comunidad)

    print(data)

    climate_data = spq.get_climate_data(engine,
                                        ifecha,
                                        ffecha,
                                        comunidad)[0]

    bubbledata, geobubble = process_bubblemap_data(
        engine, ifecha, ffecha, comunidad)

    # figures
    pie_chart = px.pie(process_severity(data),
                       names='labels',
                       values='values',
                       hole=0.3,
                       title="Superficie clasificada por severidad del incendio",
                       )

    sunburst_chart = px.sunburst(
        process_landcover(data),
        path=[
            'group1', 'group2', 'group3'],
        values='area',
        title='Superficie quemada clasificada por CLC'
    )

    bubblemap_chart = px.scatter_geo(
        bubbledata,
        geojson=geobubble,
        locations='id',
        featureidkey='properties.id',
        color="sev_perc_high",
        size="area_incendio",
        hover_data={
            "id": False,
            "area_incendio": True,
            "sev_perc_high": True,
            "sev_perc_moderate": True,
            "fecha_inicio": True,
        },
        labels={
            "area_incendio": "Area quemada en ha",
            "sev_perc_high": "Porcentaje de area quemada con alta severidad",
            "sev_perc_moderate": "Porcentaje de area quemada con severidad media",
            "fecha_inicio": "Fecha de la primera detección del incendio",
        },
        title="Ubicacion de los incendios",
        fitbounds='geojson',
    )

    clima_scatter = px.scatter_matrix(
        climate_data,
        dimensions=[
            "clima_temp_media",
            "clima_temp_max",
            "clima_temp_min",
            "area_incendio",
            "viento_velocidad"
        ],
        title="Correlación de variables",
        # ocupa todo el ancho por defecto
        height=800,
    )

    return pie_chart, sunburst_chart, bubblemap_chart, clima_scatter


if __name__ == "__main__":
    app.run_server(debug=True)
