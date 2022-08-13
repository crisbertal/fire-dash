import geopandas as gpd
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
        )
    ]
)

if __name__ == "__main__":
    app.run_server(debug=True)
