from datetime import datetime as dt
from datetime import date, timedelta
import os
from statistics import mean
from random import randint, shuffle

import pandas as pd
import plotly.graph_objs as go
import dash
import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc

from dash.dependencies import Input, Output

from app import app
import utils
import callbacks


banner = html.Div(
    id="banner",
    className="banner",
    children=[
        html.Div(
            id="banner-text",
            children=[
                # html.H1("AI-based RSC Monitoring", style={'font-family': 'Arial, Helvetica, sans-serif', }),
                # html.H6("Developed by Mingjian Wu", style={'font-family': 'Arial, Helvetica, sans-serif',}),
                html.A(
                    html.Img(id="logo_left", src=app.get_asset_url("Picture2.png"),
                             style={'width': '30%', 'height': '30%'}),
                    href='/', )
            ],
        ),
        html.Div(
            id="banner-logo",
            children=[
                dcc.Link("Home", href='/', className='button',
                         style={'text-decoration': 'None'}),
                dcc.Link("Geostatistics Interpolation (RSI)", href='rsi', className='button',
                         style={'margin-left': '10px', 'text-decoration': 'None'}),
                dcc.Link("Demo (Spatial Mapping)", href='spatial_mapping', className='button',
                         style={'margin-left': '10px', 'text-decoration': 'None'}),
                html.A("LEARN MORE", href='https://sites.google.com/ualberta.ca/drtaejkwon/home', className='button',
                       style={'margin-left': '10px', 'text-decoration': 'None'}),
                html.A(
                    # html.Img(id="logo", src=app.get_asset_url("dash-logo-new.png")),
                    html.Img(id="logo", src='https://www.ualberta.ca/_assets/images/ua-logo-green.svg'),
                    href="https://plotly.com/dash/",
                ),
                # dcc.Store stores the intermediate value
                dcc.Store(id='df'),
                dcc.Store(id='df_rwis'),
                dcc.Store(id='df_unknown'),
                dcc.Store(id='df_rwis_all'),
                dcc.Store(id='rsc_colors'),

                dcc.Store(id='picked_df'),
                dcc.Store(id='picked_df_rwis'),
                dcc.Store(id='picked_df_unknown'),
                dcc.Store(id='picked_df_rwis_all'),
            ],
        ),
    ],
)

content = html.Div([dcc.Location(id="url"), banner, html.Div(id="page-content")])

container = dbc.Container([content], fluid=True, )


# Main index function that will call and return all layout variables
def PageLayout():
    layout = html.Div([container])
    return layout


def HomePage():
    layout = html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        md=4,
                        children=[
                            dbc.Card(
                                style={'height': '5vh'},
                                children=[
                                    dcc.Dropdown(
                                        id="pick_date",
                                        options=[
                                            {"label": 'Nighttime AVL', "value": 'Nighttime'},
                                            {"label": 'Daytime AVL', "value": 'Daytime'},
                                        ],
                                        value='Nighttime',
                                    ),
                                    html.Div(id='dd-output-container'),
                                ]
                            ),
                            dbc.Card(
                                style={'height': '39vh'},
                                children=[
                                    dbc.CardHeader("Real-Time RSC Image"),
                                    dbc.CardBody(
                                        html.Pre(
                                            id="web_link",
                                            children=[],
                                        ),
                                    )
                                ]
                            ),
                            html.Br(),
                            dbc.Card(
                                style={'height': '40vh'},
                                children=[
                                    dbc.CardHeader(
                                        "Deep Learning Prediction"
                                    ),
                                    dbc.CardBody(
                                        id = "dl_prediction",
                                        children=[dcc.Graph(
                                            id="pie_chart",
                                            config={'displayModeBar': False},
                                        ),],
                                    )
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
                                        "Real-Time AVL Locations"
                                    ),
                                    dbc.CardBody(
                                        dcc.Graph(
                                            id="AVL_map",
                                            #figure=go.Figure(data=locations, layout=map_layout),
                                            config={'displayModeBar': False, 'scrollZoom': True},
                                        ),
                                    )
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


# Set layout to index function
app.layout = PageLayout()

##----------------------------------------------------------
if __name__ == "__main__":
    app.run_server(debug=True)
