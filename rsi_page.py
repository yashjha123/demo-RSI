from datetime import datetime as dt
from datetime import date, timedelta
import os
from statistics import mean
import random
from random import randint, shuffle

import pandas as pd
import plotly.graph_objs as go
import dash
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc

from dash.dependencies import Input, Output

from app import app
import utils
import callbacks

import index_page
from index_page import *
import crop_cal_perc_white_black
from crop_cal_perc_white_black import *



def NamedGroup(children, label, **kwargs):
    return html.Div(
        [
            dbc.Label(label),
            children
        ],
        **kwargs
    )



def HomePage():
    layout = html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        md=4,
                        children=[
                            dbc.Card(
                                style={'height': '44vh'},
                                children=[
                                    dcc.Store(id='maxlag'),
                                    dcc.Store(id='n_lags'),
                                    dcc.Store(id='dists'),
                                    dcc.Store(id='experiments'),
                                    dcc.Store(id='updated_df'),
                                    dbc.CardHeader("Semivariogram Parameters"),
                                    dbc.CardBody(
                                        [
                                            NamedGroup(
                                                dcc.Dropdown(
                                                    id="semi-model",
                                                    options=[
                                                        {"label": 'Spherical', "value": 'Spherical'},
                                                        {"label": 'Gaussian', "value": 'Gaussian'},
                                                        {"label": 'Exponential', "value": 'Exponential'},

                                                    ],
                                                    value='Spherical',
                                                    multi=False,
                                                    style={'width': '200px', },
                                                ),
                                                label="Semivarigram Model Type",
                                            ),
                                            html.Br(),
                                            NamedGroup(
                                                dcc.Input(
                                                    id="semi-nugget",
                                                    type="number",
                                                    min=0,
                                                    max=1,
                                                    step=0.01,
                                                    value=0,
                                                    style={'background-color': '#242633', 'color': 'white', 'width': '200px',}
                                                ),
                                                label="Semivariogram Nugget",
                                            ),
                                            html.Br(),
                                            NamedGroup(
                                                dcc.Input(
                                                    id="semi-sill",
                                                    type="number",
                                                    min=0,
                                                    step=0.01,
                                                    value=1,
                                                    style={'background-color': '#242633', 'color': 'white', 'width': '200px',}
                                                ),
                                                label="Semivariogram Sill",
                                            ),
                                            html.Br(),
                                            NamedGroup(
                                                dcc.Input(
                                                    id="semi-range",
                                                    type="number",
                                                    min=1,
                                                    max=200,
                                                    value=100,
                                                    style={'background-color': '#242633', 'color': 'white',  'width': '200px',}
                                                    # marks={i: str(i) for i in range(0, 200, 20)},
                                                ),
                                                label="Semivariogram Range (km)",
                                            ),
                                        ]
                                    )
                                ]
                            ),
                            html.Br(),
                            dbc.Card(
                                children=[
                                    dbc.CardHeader(
                                        "Semivariogram Figure",
                                    ),
                                    dbc.CardBody(
                                        dcc.Graph(
                                            id="semi_fig",
                                            config={'displayModeBar': False},
                                            style={'height': '280px', },
                                        ),
                                    ),
                                    html.Button('Update Interpolated Results in Map',
                                                id='rsi_interpolate',
                                                n_clicks=0,
                                                style={'color':'white','background-color':'#242633'}),
                                ]
                            ),
                        ],
                    ),
                    html.Br(),
                    dbc.Col(
                        md=8,
                        children=[
                            dbc.Card(
                                children=[
                                    dbc.CardHeader(
                                        "Map (RSI Interpolation Map)"
                                    ),
                                    dcc.Loading(
                                        dbc.Spinner(
                                            children=[dcc.Graph(
                                            id="RSI_map",
                                            #figure=go.Figure(data=locations, layout=map_layout),
                                            config={'displayModeBar': False, 'scrollZoom': True},
                                        )],
                                            color="primary",
                                            type='default',
                                            fullscreen=False,
                                        ),
                                    ),
                                ]
                            ),
                            html.Br(),
                        ],
                    ),
                ]
            ),
        ],
    )
    return layout
