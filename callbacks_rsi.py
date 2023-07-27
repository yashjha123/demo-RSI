import datetime
from datetime import date, timedelta, timezone
import time
import os
from dash.exceptions import PreventUpdate

# import plotly.graph_objects as go
from pytz import timezone
CENTRAL = timezone('US/Central')
UTC = timezone('UTC')

from statistics import mean
from random import randint, shuffle
from dateutil.parser import parse
import numpy as np
import pandas as pd
import plotly.graph_objs as go
import dash
from dash import dcc
from dash import html, Patch, ctx
from dash import clientside_callback, ClientsideFunction

import dash_bootstrap_components as dbc
# from dash.exceptions import PreventDefault
# from dash.dependencies import Input, Output, State
from utils import *
import utils
from app import app
import index_page
from index_page import *
import rsi_page
from rsi_page import *
import crop_cal_perc_white_black
from crop_cal_perc_white_black import *
from dash_extensions.enrich import Input, Output, State, Serverside


mapbox_access_token = "pk.eyJ1IjoibWluZ2ppYW53dSIsImEiOiJja2V0Y2lneGQxbzM3MnBuaWltN3RrY2QyIn0.P9tqv8lRlKbVw0_Tz2rPPw"

@app.callback(
    [Output('semi-model', 'value'),
     Output('semi-nugget', 'value'),
     Output('semi-range', 'value'),
     Output('semi-sill', 'value'),
     Output('maxlag', 'data'),
     Output('n_lags', 'data'),
     Output('dists', 'data'),
     Output('experiments', 'data')],
    [Input('avl_points', 'data'),],)
def initial_semi(avl_points): # NOTE: This reconstructs semi whenever new data is loaded
    avl_df = pd.DataFrame.from_dict(avl_points)
    print("AVL_DF",avl_df)
    # updated_df = crop_cal_perc_white_black.ObtainAdjustedRSI(df=df)
    nugget, rnge, sill, maxlag, n_lags, dists, experiments = utils.ConstructSemi(df=avl_df)
    return ('Spherical',nugget,rnge,sill,maxlag,n_lags,dists,experiments)

#recommended semi parameters
@app.callback(
    Output("semi_fig", "figure"),
    [Input('semi-model', 'value'),
     Input('semi-nugget', 'value'),
     Input('semi-range', 'value'),
     Input('semi-sill', 'value'),
     Input('maxlag', 'data'),
     Input('n_lags', 'data'),
     Input('dists', 'data'),
     Input('experiments', 'data'),],
)
def plot_semi_fig(semi_model, semi_nugget, semi_range, semi_sill,maxlag,n_lags,dists,experiments):
    # print('Selected model type: ', semi_model)
    # print('Input nugget: ', semi_nugget)
    # print('Input range: ', semi_range)
    # print('Input sill: ', semi_sill)
    dists_semis = [[0, semi_nugget]] + [[(n_lag + 1) * (maxlag / n_lags),
                                         utils.CalSemivariance(h=(n_lag + 1) * (maxlag / n_lags), n=semi_nugget,
                                                               r=semi_range,
                                                               s=semi_sill,
                                                               model=semi_model[:3])]
                                        for n_lag in range(n_lags)]
    # print(dists_semis)
    to_plot = {}
    to_plot['dist'] = [dist_semi[0] for dist_semi in dists_semis]
    to_plot['semi'] = [dist_semi[1] for dist_semi in dists_semis]
    to_scatter = {}
    to_scatter['dist'] = dists
    # print(dists)
    to_scatter['semi'] = experiments
    # print(experiments)
    fig = go.Figure()
    # fig = px.line(to_plot, x="dist", y="semi", labels={'dist': 'Separation Distance (km)', 'semi': 'Semivariance'})
    fig.add_trace(go.Scatter(x=to_plot['dist'], y=to_plot['semi'], mode='lines', name='Fitted Line'))
    fig.add_trace(go.Scatter(x=to_scatter['dist'], y=to_scatter['semi'], mode='markers', name='Experimental'))
    fig.update_layout(
        paper_bgcolor="#303030",
        plot_bgcolor="#303030",
        font_color="white",
        xaxis=dict(
            showline=True,
            showgrid=False,
            showticklabels=True,
            range=[0, max(to_plot['dist'])],
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=False,
            showticklabels=True,
            # range=[0, max(to_plot['semi'])*1.2],
        ),
    )
    return fig


####callback for updating RSI Interpolated Map via button
# TODO: We might need to use Inputs instead of States
@app.callback(
    Output('RSI_map', 'figure'),
    [Input('rsi_interpolate', 'n_clicks'),Input('avl_points', 'data')],
    [State('semi-model', 'value'),
     State('semi-nugget', 'value'),
     State('semi-range', 'value'),
     State('semi-sill', 'value'),
     State('picked_df_rwis', 'data')],)
def update_rsi_map(n_clicks, avl_points, semi_model, semi_nugget, semi_range, semi_sill, df_rwis):
    df_unknown = pd.read_csv('https://raw.githubusercontent.com/WMJason/demo-RSI/main/test_unknown.csv') # unknown RWIS data (location, time, for interpolation)
    avl_points = pd.DataFrame.from_dict(avl_points)
    print(avl_points)
    if df_rwis is not None:
        df_rwis = pd.DataFrame.from_dict(df_rwis) # 
        print("WOAH",df_rwis)
    else:
        df_rwis = pd.DataFrame(columns=['lon','lat'])
    rsi_locations = [go.Scattermapbox(
        lon=avl_points['lon'],
        lat=avl_points['lat'],
        mode='markers',
        marker={'size': 10, 'opacity': 1.0,
                'color': avl_points['RSI'],
                'colorscale': [[0, 'white'], [1, 'black']],
                'cmin': 0,
                'cmax': 1,
                'showscale': True,
                'colorbar': {'len': 0.8, 'title': '0 = icy/snowy; 1 = dry'}, },
        hoverinfo='text',
        hovertext=avl_points['RSI'],
        customdata=avl_points['RSI'],
        showlegend=True,
        name="Observed RSI", # Mobile locations
    )] + [go.Scattermapbox(
        lon=df_rwis['lon'],
        lat=df_rwis['lat'],
        mode='markers',
        marker={'color': 'red', 'size': 20, 'opacity': 0.6},
        showlegend=True,
        name='RWIS',
    )]
    if avl_points.empty:
        mean_lon, mean_lat = 41.0,-94.0
    else:
        mean_lon, mean_lat = mean(avl_points['lon']), mean(avl_points['lat'])
    rsi_map_layout = go.Layout(
        mapbox=go.layout.Mapbox(
            accesstoken=mapbox_access_token,
            center=go.layout.mapbox.Center(lon=mean_lon,lat=mean_lat), 
            style="dark",
            zoom=8,
            pitch=0,
        ),
        height=740,
        margin=dict(l=15, r=15, t=15, b=15),
        paper_bgcolor="#303030",
        font_color="white",
    )

    if n_clicks and not avl_points.empty:
        #time.sleep(2)
        knowns = [[avl_points['pro_X'][i], avl_points['pro_Y'][i], avl_points['RSI'][i]] for i in range(len(avl_points))] # TODO: Update this command to use python's pandas dataframe
        unknowns = [[df_unknown['pro_X'][i], df_unknown['pro_Y'][i]] for i in range(len(df_unknown))]
        estimates, errors = utils.OK(samples=knowns,
                                     unsampled=unknowns,
                                     model=semi_model[:3], n=semi_nugget, r=semi_range * 1000, s=semi_sill)

        estimates_xs, estimates_ys = utils.ConvertProjtoDegree(pro_xs=np.array(df_unknown['pro_X']),
                                                               pro_ys=np.array(df_unknown['pro_Y']))
        rsi_locations[0].marker['showscale'] = False
        updated_locations = [go.Scattermapbox(
            lon=np.concatenate([estimates_xs, np.array(avl_points['lon'])]),
            lat=np.concatenate([estimates_ys, np.array(avl_points['lat'])]),
            mode='markers',
            marker={'size': 10, 'opacity': 0.9,
                    'color': np.concatenate([estimates, np.array(avl_points['RSI'])]),
                    'colorscale': [[0, 'white'],[1, 'black']],
                    'cmin': 0,
                    'cmax': 1,
                    'showscale': True,
                    'colorbar': {'len': 0.8, 'title': '0 = icy/snowy; 1 = dry'},},
            hoverinfo='text',
            hovertext=np.concatenate([estimates, np.array(avl_points['RSI'])]),
            showlegend=True,
            name="Estimated RSI",
        )] + rsi_locations
    else:
        updated_locations = rsi_locations

    fig = go.Figure(data=updated_locations, layout=rsi_map_layout)

    # Return figure
    return fig



