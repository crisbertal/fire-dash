from datetime import datetime

import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html
from sqlalchemy import create_engine

import spquery as spq
import utils

# ----------------------------------------------------------------------------
# DATA
# ----------------------------------------------------------------------------
engine = create_engine("postgresql://postgres:admin@localhost:5432/fire")
data, geojson = spq.get_fire_area_comunidad(engine,
                                            "2013-01-01",
                                            "2020-12-31",
                                            "Andalucía")


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


df = px.data.gapminder().query("year==2007")

fig = px.scatter_geo(df, locations="iso_alpha", color="continent",
                     hover_name="country", size="pop",
                     projection="natural earth")


def process_bubblemap_data():
    data, geojson = spq.get_bubblemap_data(engine,
                                           "2013-01-01",
                                           "2020-12-31",
                                           "Andalucía")

    # calcular la severidad media con la severidad moderada en procentaje
    # con respecto al total quemado

    data['sev_perc_moderate'] = pd.Series(data['sev_moderateseverity'] /
                                          data['area_incendio'] * 100).astype(int)

    data['sev_perc_high'] = pd.Series(data['sev_highseverity'] /
                                      data['area_incendio'] * 100).astype(int)

    data["fecha_inicio"] = data["IDate"].map(
        lambda x: datetime.fromtimestamp(x/1000 + 2).strftime("%d/%m/%Y"))

    data["area_incendio"] = data["area_incendio"].astype(int)

    return (data, geojson)


bubbledata, geobubble = process_bubblemap_data()


# ----------------------------------------------------------------------------
# LAYOUT
# ----------------------------------------------------------------------------
app = Dash(__name__)
app.layout = html.Div(
    children=[
        html.H1(children="Analítica de incendios",),
        dcc.Graph(
            figure=px.pie(
                process_severity(data),
                names='labels',
                values='values',
                hole=0.3,
                title="Superficie clasificada por severidad del incendio"
            ),
        ),
        dcc.Graph(
            figure=px.sunburst(
                process_landcover(data),
                path=['group1', 'group2', 'group3'],
                values='area',
                title='Superficie quemada clasificada por CLC'
            )
        ),
        dcc.Graph(
            figure=px.scatter_geo(
                bubbledata,
                geojson=geobubble,
                locations='id',
                featureidkey='properties.id',
                color="sev_perc_high",
                size="area_incendio",
                hover_data=["sev_perc_moderate", "fecha_inicio"],
                labels={
                    "area_incendio": "Area quemada en ha",
                    "sev_perc_high": "Porcentaje de area quemada con alta severidad",
                    "sev_perc_moderate": "Porcentaje de area quemada con severidad media",
                    "fecha_inicio": "Fecha de la primera detección del incendio",
                },
                title="Ubicacion de los incendios",
                fitbounds='geojson',
            )
        )
    ]
)

if __name__ == "__main__":
    app.run_server(debug=True)
