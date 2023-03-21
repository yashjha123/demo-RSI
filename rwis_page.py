from datetime import datetime as dt
from datetime import date, timedelta
import os
from statistics import mean
import random
from random import randint, shuffle

import pandas as pd
import plotly.graph_objs as go
import dash
import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc

from dash.dependencies import Input, Output

from app import app
import index_page
import utils
import callbacks

#load RWIS data
df_rwis_all = index_page.df_rwis_all

locations = [go.Scattermapbox(
    lon=df_rwis_all['lon'],
    lat=df_rwis_all['lat'],
    mode='markers',
    marker={'color': df_rwis_all['estimate_ratio'], 'size': 20, 'opacity': 0.6,
            'showscale': True,
            'colorbar': {'len': 0.8, 'title': '0 = no snow; 1 = full snow'},},
    showlegend=True,
    hoverinfo='text',
    hovertext=df_rwis_all['stid'],
    customdata=df_rwis_all['img_path'],
    name='RWIS',
)]

mapbox_access_token = "pk.eyJ1IjoibWluZ2ppYW53dSIsImEiOiJja2V0Y2lneGQxbzM3MnBuaWltN3RrY2QyIn0.P9tqv8lRlKbVw0_Tz2rPPw"
map_layout = go.Layout(
    mapbox=go.layout.Mapbox(
        accesstoken=mapbox_access_token,
        center=go.layout.mapbox.Center(lat=mean(df_rwis_all['lat']), lon=mean(df_rwis_all['lon'])),
        style="dark",
        zoom=7,
        pitch=0,
    ),
    height=740,
    margin=dict(l=15, r=15, t=15, b=15),
    paper_bgcolor="#303030",
    font_color="white"
)


def NamedGroup(children, label, **kwargs):
    return dbc.FormGroup(
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
                                style={'height': '42vh'},
                                children=[
                                    dbc.CardHeader("Real-Time RWIS Image"),
                                    dbc.CardBody(
                                        html.Pre(
                                            id="rwis_img_link",
                                            children=[],
                                        ),
                                    )
                                ]
                            ),
                            html.Br(),
                            dbc.Card(
                                style={'height': '42vh'},
                                children=[
                                    dbc.CardHeader(
                                        "Drivable Areas Prediction"
                                    ),
                                    dbc.CardBody(
                                        html.Pre(
                                            id="drivable_areas",
                                            children=[],
                                        ),
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
                                        "Real-Time RWIS Monitoring"
                                    ),
                                    dbc.CardBody(
                                        dcc.Graph(
                                            id="rwis_map",
                                            figure=go.Figure(data=locations, layout=map_layout),
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
