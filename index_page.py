from datetime import datetime as dt
from datetime import date, timedelta
import os
from statistics import mean
from random import randint, shuffle
from datetime import date
import pandas as pd
import plotly.graph_objs as go
import dash
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
import dash_daq as daq

# import dash_datetimepicker

from dash.dependencies import Input, Output

from app import app
import utils
import callbacks
import callbacks_rsi
from utils import load_data

from AVL_Image_URL import get_cameras, grab_avl_data

# from dash import Dash.DiskcacheManager, CeleryManager, Input, Output, html





# rsc_colors = {'Full Snow Coverage': 'blue',
#               'Partly Snow Coverage': '#87CEFA',
#               'Bare': '#808080',
#               'Undefined': '#FDDD0D'}
# # print(df['Predict'])

# df_subs = []
# for rsc_type in list(rsc_colors.keys()):
#     to_append = df[df['Predict'] == rsc_type]
#     if len(to_append) == 0:
#         pass
#     else:
#         df_subs.append(to_append)
# print("GOLO")
# locations = [go.Scattermapbox(
#     lon=df_sub['x'],
#     lat=df_sub['y'],
#     mode='markers',
#     marker={'color': rsc_colors[df_sub['Predict'].iloc[0]], 'size': 10, 'opacity': 0.6},
#     hoverinfo='text',
#     hovertext=df_sub['Predict'],
#     customdata=df_sub['PHOTO_URL'],
#     showlegend=True,
#     name=df_sub['Predict'].iloc[0],
# ) for df_sub in df_subs]
# print("LOGO")

# mapbox_access_token = "pk.eyJ1IjoibWluZ2ppYW53dSIsImEiOiJja2V0Y2lneGQxbzM3MnBuaWltN3RrY2QyIn0.P9tqv8lRlKbVw0_Tz2rPPw"
# map_layout = go.Layout(
#     mapbox=go.layout.Mapbox(
#         accesstoken=mapbox_access_token,
#         center=go.layout.mapbox.Center(lat=mean(df["y"]), lon=mean(df["x"])),
#         style="dark",
#         zoom=8,
#         pitch=0,
#     ),
#     height=740,
#     margin=dict(l=15, r=15, t=15, b=15),
#     paper_bgcolor="#303030",
#     font_color="white"
# )


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
                # dcc.Store(id='df_rwis'),
                dcc.Store(id='df_unknown'),
                # dcc.Store(id='df_rwis_all'),

                dcc.Store(id='picked_df_rwis'),

                dcc.Store(id='avl_points', storage_type="session"),
                dcc.Store(id='rwis_points', storage_type="session"),

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


def make_progress_graph(progress, total):
    progress_graph = (
        go.Figure(data=[go.Bar(x=[progress])])
        .update_xaxes(range=[0, total])
        .update_yaxes(
            showticklabels=False,
        )
        .update_layout(height=100, margin=dict(t=20, b=40))
    )
    return progress_graph

import datetime
from datetime import date, timedelta, timezone
from pytz import timezone
central = timezone('US/Central')
utc = timezone('UTC')
dt = datetime.datetime.now(utc)
time_in_cst = datetime.datetime.now(central)
utc_time = dt.replace(tzinfo=utc).timestamp()

mapbox_access_token = "pk.eyJ1IjoibWluZ2ppYW53dSIsImEiOiJja2V0Y2lneGQxbzM3MnBuaWltN3RrY2QyIn0.P9tqv8lRlKbVw0_Tz2rPPw"

lat =  41.3322983
lon = -93.7797012
locations = [go.Scattermapbox(
    lon=[lon],
    lat=[lat],
    mode='markers',
    marker={'color': "red", 'size': 10, 'opacity': 0.6},
    hoverinfo='text',
    hovertext="Tests",
    customdata=("URL",),
    showlegend=True,
    name="WOW",
)]
map_layout = go.Layout(
    mapbox=go.layout.Mapbox(
        accesstoken=mapbox_access_token,
        center=go.layout.mapbox.Center(lat=lat, lon=lon),
        style="dark",
        zoom=8,
        pitch=0,
    ),
    height=740,
    margin=dict(l=15, r=15, t=15, b=15),
    paper_bgcolor="#303030",
    font_color="white"
)
def HomePage():
    layout = html.Div(
        [
            dcc.Store(id='trigger_on_click'),
            dcc.Store(id='process_in_background'),
            dcc.Store(id='cache'),
            dcc.Store(id='rand'),

            dcc.Interval(id="interval", interval=500),
            dcc.Interval(id="auto_trigger", interval=30000, n_intervals=0),
            dbc.Row(
                [
                    dbc.Col(
                        md=4,
                        children=[
                            dbc.Card(
                                style={'display': 'flex','flex-direction':'row','justify-content': 'center'},
                                children=[
                                    # dcc.DatePickerSingle(
                                    #     id="pick_date_time",
                                    #     min_date_allowed=date(1995, 8, 5),
                                    #     max_date_allowed=date(2023, 12, 6),
                                    #     initial_visible_month=date(2023, 3, 30),
                                    #     date=date(2023, 5, 4),
                                    # ),
                                    
                                    dcc.Input(
                                        id="pick_date_time",
                                        type="datetime-local",
                                        step="1",
                                        value=date.strftime(time_in_cst, "%Y-%m-%dT%H:%M"),
                                        style = {"flex":"3"},
                                    ),
                                    daq.BooleanSwitch(
                                        on=True,
                                        id="live_button",
                                        label="Live",
                                        labelPosition="left",
                                        color="#119dff",
                                        style={"flex":"1","display":"flex","align-items":"center", "justify-content": "center"}
                                    ),
                                ]
                            ),
                            dbc.Card(
                                style={'height': '5vh',
                                       'padding-top': '1vh',
                                       'margin-bottom': '1vh'},
                                children=[
                                    dcc.Slider(0, 720,
                                        step=None,
                                        marks={
                                            30: '1h',
                                            90: '3h',
                                            180: '6h',
                                            360: '12h',
                                            720: '24h'
                                        },
                                        value=30,
                                        id="slider"
                                    ),
                                    html.Div(id='dd-output-container'), # TODO: determine if continuous or discrete slider is better
                                ]
                            ),
                            # dcc.Graph(id="progress_bar_graph", figure=make_progress_graph(0, 10)),
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
                                        style = {'display': 'flex'},
                                        children=[dcc.Loading()])
                            ]
                                
                            ),
                        ],
                    ),
                    html.Br(),
                    dbc.Col(
                        md=8,
                        children=[
                            dbc.Card(
                                id="col-id",
                                children=[
                                    dbc.CardHeader(
                                        "Real-Time AVL Locations"
                                    ),
                                    
                                    dbc.CardBody(
                                        [html.Div(id="result"),
                                         html.Div([
                                            dbc.Spinner(size="me-1", id="spinner_loader"),
                                            dbc.Progress(id="progress_bar", animated=True, striped=True,value=100,color="success"),
                                            html.Button(id="cancel_button_id", disabled=True, children="Cancel Running Job!"),
                                        ], id='while_loading'),
                                        dcc.Loading(dcc.Graph(
                                            id="AVL_map",
                                            # figure=go.Figure(data=locations, layout=map_layout),
                                            config={'displayModeBar': False, 'scrollZoom': True},
                                            # animate=True
                                        )),]
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
    app.run_server(debug=True,host='0.0.0.0',port=8050,dev_tools_props_check=False)

