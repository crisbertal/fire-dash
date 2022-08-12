import plotly.express as px
import plotly.graph_objects as go

from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
from sqlalchemy import create_engine

import id


def draw_numero_incendios():
    ''' muestra el texto con el numero de incendios'''
    return html.Div([
        dbc.Card(
            dbc.CardBody([
                html.Div([
                    html.H3("Numero incendios"),
                ], style={'textAlign': 'center', 'height': '3rem'}),
                html.Div([
                ], id=id.NUMERO_INCENDIOS,
                    style={'textAlign': 'center', 'height': '3rem'})
            ])
        ),
    ])


def draw_area_incendios():
    ''' muestra el texto con el area de incendios'''
    return html.Div([
        dbc.Card(
            dbc.CardBody([
                html.Div([
                    html.H3("Area quemada"),
                ], style={'textAlign': 'center', 'height': '3rem'}),
                html.Div([
                ], id=id.AREA_INCENDIOS,
                    style={'textAlign': 'center', 'height': '3rem'})
            ])
        ),
    ])


def draw_mapa_incendios():
    ''' muestra el mapa con los incendios '''
    return html.Div([
        dbc.Card(
            dbc.CardBody([
                dcc.Graph(id=id.MAPA_INCENDIOS)
            ])
        ),
    ])
