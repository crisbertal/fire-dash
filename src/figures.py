import plotly.express as px
import plotly.graph_objects as go

from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
from sqlalchemy import create_engine

import spquery as spq


@app.callback(
    Output('provincia-map', 'figure'),
    Input('provincia-dropdown', 'value'))
def update_map(provincia):
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
