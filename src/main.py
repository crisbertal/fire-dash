import plotly.express as px
import dash

from dash import dcc, html
from sqlalchemy import create_engine

import spquery as spq

# Conexion a la BD
engine = create_engine("postgresql://postgres:admin@localhost:5432/fire")

# Aplicacion dash
app = dash.Dash(__name__)

# Ejecuta la consulta desde el repositorio de queries
gdf, geojson = spq.get_fire_area_bounds(engine)

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

if __name__ == "__main__":
    app.run_server(debug=True)
