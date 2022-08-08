import plotly.express as px
import plotly.graph_objects as go

from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
from sqlalchemy import create_engine

# Aplicacion dash
app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
# Text field

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
    # el layout de la pantalla se divide en 12 columnas.
    # width indica cuales de ellas ocupan el componente
    html.Div(
        [
            dbc.Row([
                dbc.Col([
                    dbc.Row([
                        dbc.Col([draw_text()]),
                        dbc.Col([draw_text()])
                    ]),
                    html.Br(),
                    dbc.Row([draw_figure(500)])
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

# TODO borrar esto despues de terminar las pruebas
if __name__ == "__main__":
    app.run_server(debug=True)
