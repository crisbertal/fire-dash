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

comunidades = spq.get_comunidades(engine)
incendios = spq.get_incendios(engine)


def process_severity(data):
    # la suma total de ha esta 5 o 6 ha por debajo
    vars = [
        'Alta',
        'Baja',
        'Moderada',
        'Rebrote',
        'No quemada'
    ]

    names = {
        'sev_highseverity': 'Alta',
        'sev_lowseverity': 'Baja',
        'sev_moderateseverity': 'Moderada',
        'sev_regrowth': 'Rebrote',
        'sev_unburned': 'No quemada'
    }

    seve = data.rename(columns=names).loc[:, [s for s in vars]].sum()
    return pd.DataFrame({'labels': seve.index, 'values': seve.values})


def process_slope(data):
    vars = [
        "< 5 grados",
        ">= 5 y < 15 grados",
        ">= 15 y < 25 grados",
        ">= 25 y < 35 grados",
        ">= 35 y < 45 grados",
        "> 45 grados",
    ]

    names = {
        "topo_slopei": "< 5 grados",
        "topo_slopeii": ">= 5 y < 15 grados",
        "topo_slopeiii": ">= 15 y < 25 grados",
        "topo_slopeiv": ">= 25 y < 35 grados",
        "topo_slopev": ">= 35 y < 45 grados",
        "topo_slopevi": "> 45 grados",
    }

    slope = data.rename(columns=names).loc[:, [s for s in vars]].sum()
    return pd.DataFrame({'labels': slope.index, 'values': slope.values})


def process_direction(data):
    names = {
        "topo_este": "Este",
        "topo_noreste": "Noreste",
        "topo_noroeste": "Noroeste",
        "topo_norte": "Norte",
        "topo_oeste": "Oeste",
        "topo_sur": "Sur",
        "topo_sureste": "Sureste",
        "topo_suroeste": "Suroeste"
    }

    vars = [
        "Este",
        "Noreste",
        "Noroeste",
        "Norte",
        "Oeste",
        "Sur",
        "Sureste",
        "Suroeste"
    ]

    direction = data.rename(columns=names).loc[:, [s for s in vars]].sum()
    return pd.DataFrame({'labels': direction.index, 'values': direction.values})


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
    # APUNTE la suma de las areas no coinciden con el area total en algunas
    # comunidades
    cover = data.loc[:, [c for c in data.columns if c.startswith('m')]].sum()
    coverdf = pd.DataFrame({'clc': cover.index, 'area': cover.values})

    coverdf['group1'] = coverdf.loc[:, 'clc'].map(
        lambda x: get_landcover_group1(x))
    coverdf['group2'] = coverdf.loc[:, 'clc'].map(
        lambda x: get_landcover_group2(x))
    coverdf['group3'] = coverdf.loc[:, 'clc'].map(
        lambda x: utils.use_conversion(x))

    return coverdf


def process_bubblemap_data(data):

    # calcular la severidad media con la severidad moderada en procentaje
    # con respecto al total quemado

    data['sev_perc_moderate'] = pd.Series(data['sev_moderateseverity'] /
                                          data['perim_area'] * 100).astype(int)

    data['sev_perc_high'] = pd.Series(data['sev_highseverity'] /
                                      data['perim_area'] * 100).astype(int)

    data["fecha_inicio"] = data["IDate"].map(
        lambda x: datetime.fromtimestamp(x/1000 + 2).strftime("%d/%m/%Y"))

    # transformar los valores a enteros para que sea mas legible
    data["perim_area"] = data["perim_area"].astype(int)

    return data


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
                    children=[
                        html.H3("Número de incendios"),
                        html.P(id="numero-incendios")
                    ],
                    className="card",
                ),
                html.Div(
                    children=[
                        html.H3("Superficice total quemada"),
                        html.P(id="superficie-incendios")
                    ],
                    className="card",
                ),
                html.Div(
                    children=dcc.Graph(
                        id="pie-severity",
                    ),
                    className="card",
                ),
                html.Div(
                    children=dcc.Graph(
                        id="pie-slope",
                    ),
                    className="card",
                ),
                html.Div(
                    children=dcc.Graph(
                        id="pie-direction",
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
        Output('numero-incendios', 'children'),
        Output('superficie-incendios', 'children'),
        Output('pie-severity', 'figure'),
        Output('pie-slope', 'figure'),
        Output('pie-direction', 'figure'),
        Output('sunburst-landcover', 'figure'),
        Output('bubblemap-incendios', 'figure'),
        Output('scatter-clima', 'figure'),
    ],
    [
        Input('comunidad-filter', 'value'),
        Input('date-range', 'start_date'),
        Input('date-range', 'end_date'),
    ]
)
def update_landcover(comunidad, idate, fdate):
    comunidad = comunidad
    ifecha, ffecha = idate, fdate

    # datos totales obtenidos de la bd
    data, geojson = spq.get_incendios_comunidad(
        engine,
        ifecha,
        ffecha,
        comunidad
    )

    # figures
    num_incendios = data.loc[:, ['perim_area']].count()
    superficie_incendios = f"{int(data.loc[:, ['perim_area']].sum().values)} hectáreas"

    pie_chart = px.pie(
        process_severity(data),
        names='labels',
        values='values',
        hole=0.3,
        title="Superficie clasificada por severidad del incendio",
    )

    pie_slope = px.pie(
        process_slope(data),
        names='labels',
        values='values',
        hole=0.3,
        title="Superficie clasificada por la pendiente de la zona quemada",
    )

    pie_direction = px.pie(
        process_direction(data),
        names='labels',
        values='values',
        hole=0.3,
        title="Superficie clasificada la orientación de la zona quemada",
    )

    sunburst_chart = px.sunburst(
        process_landcover(data),
        path=[
            'group1', 'group2', 'group3'],
        values='area',
        title='Superficie quemada clasificada por CLC'
    )

    # if clima_selected:
    #     points = [punto['pointIndex'] for punto in clima_selected['points']]
    #     bubbledata = bubbledata.loc[points, :]

    # if bubble_selected:
    #     points = [punto['pointIndex'] for punto in bubble_selected['points']]
    #     print(points)
    #     climate_data = climate_data.loc[points, :]

    # for selected_data in [bubble_selected, clima_selected]:
    #     if selected_data and selected_data['points']:

    bubblemap_chart = px.scatter_geo(
        process_bubblemap_data(data),
        geojson=geojson,
        locations='id',
        featureidkey='properties.id',
        color="sev_perc_high",
        size="perim_area",
        hover_data={
            "id": False,
            "perim_area": True,
            "sev_perc_high": True,
            "sev_perc_moderate": True,
            "fecha_inicio": True,
        },
        labels={
            "perim_area": "Area quemada en ha",
            "sev_perc_high": "Porcentaje de area quemada con alta severidad",
            "sev_perc_moderate": "Porcentaje de area quemada con severidad media",
            "fecha_inicio": "Fecha de la primera detección del incendio",
        },
        title="Ubicacion de los incendios",
        fitbounds='geojson',
    )

    clima_scatter = px.scatter_matrix(
        data,
        dimensions=[
            "clima_temp_media",
            "clima_temp_max",
            "clima_temp_min",
            "perim_area",
            "viento_velocidad"
        ],
        title="Correlación de variables",
        # ocupa todo el ancho por defecto
        height=800,
    )

    return num_incendios, superficie_incendios, pie_chart, pie_slope, pie_direction, sunburst_chart, bubblemap_chart, clima_scatter


if __name__ == "__main__":
    app.run_server(debug=True)
