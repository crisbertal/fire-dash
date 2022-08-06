import plotly.express as px

from dash import Dash, dcc, html, Input, Output
from sqlalchemy import create_engine

import spquery as spq

# Conexion a la BD
engine = create_engine("postgresql://postgres:admin@localhost:5432/fire")

# Aplicacion dash
app = Dash(__name__)

app.layout = html.Div([
    dcc.Graph(id='graph-with-slider'),
    dcc.Slider(
        2013,
        2020,
        step=None,
        value=2013,
        marks={str(year): str(year) for year in list(range(2013, 2021, 1))},
        id='year-slider'
    )
])


@app.callback(
    Output('graph-with-slider', 'figure'),
    Input('year-slider', 'value'))
def update_figure(selected_year):
    gdf, geojson = spq.get_fire_area_provincia(
        engine, f"{selected_year}-01-01", f"{selected_year}-12-31", "Sevilla")

    fig = px.choropleth_mapbox(gdf,
                               geojson=geojson,
                               locations='ADM2_NAME',
                               featureidkey='properties.ADM2_NAME',
                               color='area_incendios',
                               mapbox_style='carto-positron',
                               color_continuous_scale="Viridis",
                               center={'lat': 37, 'lon': -6},
                               opacity=0.5,
                               zoom=5)
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
