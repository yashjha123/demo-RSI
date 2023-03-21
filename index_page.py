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
from utils import *
import callbacks


from AVL_Image_URL import get_cameras, grab_avl_data

df = load_data()




rsc_colors = {'Full Snow Coverage': 'blue',
              'Partly Snow Coverage': '#87CEFA',
              'Bare': '#808080',
              'Undefined': '#FDDD0D'}
print(df['Predict'])

df_subs = []
for rsc_type in list(rsc_colors.keys()):
    to_append = df[df['Predict'] == rsc_type]
    if len(to_append) == 0:
        pass
    else:
        df_subs.append(to_append)
print("GOLO")
locations = [go.Scattermapbox(
    lon=df_sub['x'],
    lat=df_sub['y'],
    mode='markers',
    marker={'color': rsc_colors[df_sub['Predict'].iloc[0]], 'size': 10, 'opacity': 0.6},
    hoverinfo='text',
    hovertext=df_sub['Predict'],
    customdata=df_sub['PHOTO_URL'],
    showlegend=True,
    name=df_sub['Predict'].iloc[0],
) for df_sub in df_subs]
print("LOGO")

mapbox_access_token = "pk.eyJ1IjoibWluZ2ppYW53dSIsImEiOiJja2V0Y2lneGQxbzM3MnBuaWltN3RrY2QyIn0.P9tqv8lRlKbVw0_Tz2rPPw"
map_layout = go.Layout(
    mapbox=go.layout.Mapbox(
        accesstoken=mapbox_access_token,
        center=go.layout.mapbox.Center(lat=mean(df["y"]), lon=mean(df["x"])),
        style="dark",
        zoom=8,
        pitch=0,
    ),
    height=740,
    margin=dict(l=15, r=15, t=15, b=15),
    paper_bgcolor="#303030",
    font_color="white"
)

banner = html.Div(
    id="banner",
    className="banner",
    children=[
        html.Div(
            id="banner-text",
            children=[
                html.H1("AI-based RSC Monitoring", style={'font-family': 'Arial, Helvetica, sans-serif', }),
                # html.H6("Developed by Mingjian Wu", style={'font-family': 'Arial, Helvetica, sans-serif',}),
            ],
        ),
        html.Div(
            id="banner-logo",
            children=[
                dcc.Link("Home", href='/', className='button',
                         style={'text-decoration': 'None'}),
                dcc.Link("Geostatistics Interpolation (RSI)", href='rsi', className='button',
                         style={'margin-left': '10px', 'text-decoration': 'None'}),
                html.A("LEARN MORE", href='https://sites.google.com/ualberta.ca/drtaejkwon/home', className='button',
                         style={'margin-left': '10px', 'text-decoration': 'None'}),
                html.A(
                    # html.Img(id="logo", src=app.get_asset_url("dash-logo-new.png")),
                    html.Img(id="logo", src='https://www.ualberta.ca/_assets/images/ua-logo-green.svg'),
                    href="https://plotly.com/dash/",
                ),
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
                                    style={'height': '44vh'},
                                    children=[
                                        dbc.CardHeader("Real-Time AVL Image"),
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
                                    children=[
                                        dbc.CardHeader(
                                            "Deep Learning (CNN) Prediction"
                                        ),
                                        dbc.CardBody(
                                            dcc.Graph(
                                                id="pie_chart",
                                                config={'displayModeBar': False},
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
                                            "Real-Time AVL Locations"
                                        ),
                                        dbc.CardBody(
                                            dcc.Graph(
                                                id="map",
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


# Set layout to index function
app.layout = PageLayout()

##----------------------------------------------------------
if __name__ == "__main__":
    app.run_server(debug=False,host='0.0.0.0',port=6000)