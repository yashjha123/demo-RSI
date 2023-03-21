from datetime import datetime as dt
from datetime import date, timedelta
import time
import os
from statistics import mean
from random import randint, shuffle

import numpy as np
import pandas as pd
import plotly.graph_objs as go
import dash
import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc

from dash.dependencies import Input, Output, State
from utils import *
import utils
from app import app
import index_page
from index_page import *
import rsi_page
from rsi_page import *
import crop_cal_perc_white_black
from crop_cal_perc_white_black import *


mapbox_access_token = "pk.eyJ1IjoibWluZ2ppYW53dSIsImEiOiJja2V0Y2lneGQxbzM3MnBuaWltN3RrY2QyIn0.P9tqv8lRlKbVw0_Tz2rPPw"

# ---------------------------------------------------------------
# from dash_bootstrap_mapbox_v3.py
# ---------------------------------------------------------------
# Menu callback, set and return
# Declair function  that connects other pages with content to container

df, df_rwis, df_unknown, df_rwis_all = utils.load_data()

rsc_colors = {'Full Snow Coverage': 'white',
              'Partly Snow Coverage': 'grey',
              'Bare': 'black',
              'Undefined': '#FDDD0D'}
data = [df.to_dict(), df_rwis.to_dict(), df_unknown.to_dict(), df_rwis_all.to_dict(),rsc_colors]

@app.callback([Output('df', 'data'),Output('df_rwis', 'data'),
               Output('df_unknown', 'data'),Output('df_rwis_all', 'data'),
               Output('rsc_colors', 'data'),],
              [Input("url", "pathname")],)
def init_data(pathname):
    

    if pathname == '/':
        return data
    elif pathname == '/rsi':
        return data
    elif pathname == '/spatial_mapping':
        return data
    else:
        return data


@app.callback(Output("page-content", "children"),
              [Input("url", "pathname")])
def display_page(pathname):
    if pathname == '/':
        return index_page.HomePage()
    elif pathname == '/rsi':
        return rsi_page.HomePage()
    elif pathname == '/spatial_mapping':
        return html.Div(children=[html.Iframe(src="assets/2018-11-25_I35S_10 a.m..html",
                style={"height": "800px", "width": "90%",
                       'display': 'block', 'margin-left': 'auto',
                       'margin-right': 'auto',})])
    else:
        return html.H5('You are looking at path = ' + pathname)

#callback for the AVL points map
#to determine the file
@app.callback(
    #Output('dd-output-container', 'children'),
    [Output('picked_df', 'data'),Output('picked_df_rwis', 'data'),Output('picked_df_unknown', 'data'),
     Output('picked_df_rwis_all', 'data'),Output('AVL_map', 'figure'),],
    [Input('pick_date', 'value'),Input('rsc_colors', 'data'),],
)
def load_map(pick_date, rsc_colors):

    rsc_colors = rsc_colors
    
    if pick_date != 'Nighttime':
        picked_date = '2'
    else:
        picked_date = ''


    df, df_rwis, df_unknown, df_rwis_all = utils.load_data(picked_date)

    df_subs = []
    for rsc_type in list(rsc_colors.keys()):
        to_append = df[df['Predict'] == rsc_type]
        if len(to_append) == 0:
            pass
        else:
            df_subs.append(to_append)


    avl_locations = [go.Scattermapbox(
        lon=df_sub['x'],
        lat=df_sub['y'],
        mode='markers',
        marker={'color': rsc_colors[df_sub['Predict'].iloc[0]], 'size': 10, 'opacity': 1.0},
        hoverinfo='text',
        hovertext=df_sub['Predict'],
        customdata=df_sub['PHOTO_URL'],
        showlegend=True,
        name='AVL-'+df_sub['Predict'].iloc[0],
    ) for df_sub in df_subs]

    df_rwis_subs = []
    for rsc_type in list(rsc_colors.keys()):
        to_append = df_rwis_all[df_rwis_all['RSC'] == rsc_type]
        if len(to_append) == 0:
            pass
        else:
            df_rwis_subs.append(to_append)

    rwis_locations = [go.Scattermapbox(
        lon=df_sub['lon'],
        lat=df_sub['lat'],
        mode='markers',
        marker={'color': rsc_colors[df_sub['RSC'].iloc[0]], 'size': 20, 'opacity': 0.8,},
        showlegend=True,
        hoverinfo='text',
        hovertext=df_sub['stid'],
        customdata=df_sub['img_path'],
        name='RWIS-'+df_sub['RSC'].iloc[0],
    ) for df_sub in df_rwis_subs]

    locations = avl_locations + rwis_locations

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
    figure = go.Figure(data=locations, layout=map_layout)
    return [df.to_dict(), df_rwis.to_dict(), df_unknown.to_dict(), df_rwis_all.to_dict(),figure]

# callback for Web_link
@app.callback(
    Output("web_link", "children"),
    [Input('AVL_map', 'clickData')],
)
def display_click_data(clickData):
    if clickData is None:
        return 'Click on any dot'
    else:
        the_link = clickData['points'][0]['customdata']
        if the_link is None:
            return 'No Photo Available'
        else:
            if 'SnowPlow' in the_link:
                return html.Img(
                    src=the_link,
                    style={'max-height': '90%', 'max-width': '90%',
                           'display': 'block', 'margin-left': 'auto',
                           'margin-right': 'auto',})
            else:
                the_link = 'https://raw.githubusercontent.com/WMJason/demo-RSI/main/'+the_link.replace('\\','/')
                return html.Img(
                    src=the_link,
                    style={'max-height': '70%', 'max-width': '70%',
                           'display': 'block', 'margin-left': 'auto',
                           'margin-right': 'auto',},)


# callback for pie_chart
@app.callback(
    Output('dl_prediction', 'children'),
    [Input('AVL_map', 'clickData'), Input('picked_df', 'data')])
def display_dl_prediction(clickData, df):
    if clickData is None:
        labels = ['Please click a dot.']
        values = [1.0]
        colors = ['grey']
        fig = go.Figure(data=[go.Pie(labels=labels, values=values, marker={'colors': colors}, textinfo='label', )])
        fig.update_layout(
            height=300,
            showlegend=False,
            margin=dict(t=10, b=0, l=10, r=0),
            uniformtext={
                "mode": "hide",
                "minsize": 25,
            },
            paper_bgcolor="#303030",
            plot_bgcolor="#303030",
            font_color="white"
        )
    
        to_return = [
            dbc.CardBody(
                dcc.Graph(
                    id="pie_chart",
                    figure=fig,
                    config={'displayModeBar': False},
                ),
            )
        ]
        return to_return
    else:
        # print (clickData)
        the_link = clickData['points'][0]['customdata']
        if the_link is None:
            labels = ['There is no prediction for this photo.']
            values = [1.0]
            colors = ['grey']
            fig = go.Figure(data=[go.Pie(labels=labels, values=values, marker={'colors': colors}, textinfo='label', )])
            fig.update_layout(
                height=300,
                showlegend=False,
                margin=dict(t=10, b=0, l=10, r=0),
                uniformtext={
                    "mode": "hide",
                    "minsize": 25,
                },
                paper_bgcolor="#303030",
                plot_bgcolor="#303030",
                font_color="white"
            )
            
            to_return = [
                dbc.CardBody(
                    dcc.Graph(
                        id="pie_chart",
                        figure=fig,
                        config={'displayModeBar': False},
                    ),
                )
            ]
            return to_return
        else:
            if 'SnowPlow' in the_link:
                try:
                    df = pd.DataFrame.from_dict(df)
                    labels = list(rsc_colors.keys())
                    values = []
                    for label in labels:
                        values.append(
                            round(df[df['PHOTO_URL'] == the_link]['prob_' + label].values[0], 3))
                    colors = list(rsc_colors.values())
                    fig = go.Figure(data=[
                        go.Pie(labels=labels, values=values, hole=.4, marker={'colors': colors}, )])
                    # fig.update_layout(legend=dict(
                    #     orientation="h",
                    # ))
                    fig.update_layout(
                        height=300,
                        showlegend=True,
                        margin=dict(t=10, b=0, l=10, r=0),
                        paper_bgcolor="#303030",
                        plot_bgcolor="#303030",
                        font_color="white",
                    )
                    
                    to_return = [
                        dbc.CardBody(
                            dcc.Graph(
                                id="pie_chart",
                                figure=fig,
                                config={'displayModeBar': False},
                            ),
                        )
                    ]
                except:
                    labels = ['Please click a dot.']
                    values = [1.0]
                    colors = ['grey']
                    fig = go.Figure(data=[go.Pie(labels=labels, values=values, marker={'colors': colors}, textinfo='label', )])
                    fig.update_layout(
                        height=300,
                        showlegend=False,
                        margin=dict(t=10, b=0, l=10, r=0),
                        uniformtext={
                            "mode": "hide",
                            "minsize": 25,
                        },
                        paper_bgcolor="#303030",
                        plot_bgcolor="#303030",
                        font_color="white"
                    )
                
                    to_return = [
                        dbc.CardBody(
                            dcc.Graph(
                                id="pie_chart",
                                figure=fig,
                                config={'displayModeBar': False},
                            ),
                        )
                    ]
                return to_return
            else:
                # print (clickData)
                the_link = 'https://raw.githubusercontent.com/WMJason/demo-RSI/main/'+clickData['points'][0]['customdata'].replace('\\','/').replace('img.jpg','mask.jpg')
                if the_link is None:
                    return 'No Mask Available'
                else:
                    to_return = [
                        html.Img(
                        src=the_link,
                        style={'max-height': '70%', 'max-width': '70%',
                               'display': 'block', 'margin': 'auto',}
                        )
                    ]
                    return to_return



# from dash_bootstrap_mapbox_v3_rsi.py
# callback for Semivariogram Figure
#initialize semi parameters
@app.callback(
    [Output('semi-model', 'value'),
     Output('semi-nugget', 'value'),
     Output('semi-range', 'value'),
     Output('semi-sill', 'value'),
     Output('maxlag', 'data'),
     Output('n_lags', 'data'),
     Output('dists', 'data'),
     Output('experiments', 'data'),
     Output('updated_df', 'data'),],
    [Input('df', 'data'),],)
def initial_semi(df):
    df = pd.DataFrame.from_dict(df)
    updated_df = crop_cal_perc_white_black.ObtainAdjustedRSI(df=df)
    nugget, rnge, sill, maxlag, n_lags, dists, experiments = utils.ConstructSemi(df=updated_df)
    return ('Spherical',nugget,rnge,sill,maxlag,n_lags,dists,experiments,updated_df.to_dict())

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

@app.callback(
    Output('RSI_map', 'figure'),
    [Input('rsi_interpolate', 'n_clicks'),Input('updated_df', 'data'),Input('df_unknown', 'data')],
    [State('semi-model', 'value'),
     State('semi-nugget', 'value'),
     State('semi-range', 'value'),
     State('semi-sill', 'value')], )
def update_rsi_map(n_clicks, updated_df, df_unknowns, semi_model, semi_nugget, semi_range, semi_sill):
    updated_df = pd.DataFrame.from_dict(updated_df)
    rsi_locations = [go.Scattermapbox(
        lon=updated_df['x'],
        lat=updated_df['y'],
        mode='markers',
        marker={'size': 10, 'opacity': 1.0,
                'color': updated_df['RSI'],
                'colorscale': [[0, 'white'], [1, 'black']],
                'cmin': 0,
                'cmax': 1,
                'showscale': True,
                'colorbar': {'len': 0.8, 'title': '0 = icy/snowy; 1 = dry'}, },
        hoverinfo='text',
        hovertext=updated_df['RSI'],
        customdata=updated_df['PHOTO_URL'],
        showlegend=True,
        name="Observed RSI",
    )] + [go.Scattermapbox(
        lon=df_rwis['lon'],
        lat=df_rwis['lat'],
        mode='markers',
        marker={'color': 'red', 'size': 20, 'opacity': 0.6},
        showlegend=True,
        name='RWIS',
    )]

    rsi_map_layout = go.Layout(
        mapbox=go.layout.Mapbox(
            accesstoken=mapbox_access_token,
            center=go.layout.mapbox.Center(lat=mean(updated_df["y"]), lon=mean(updated_df["x"])),
            style="dark",
            zoom=8,
            pitch=0,
        ),
        height=740,
        margin=dict(l=15, r=15, t=15, b=15),
        paper_bgcolor="#303030",
        font_color="white",
    )

    if n_clicks:
        #time.sleep(2)
        knowns = [[updated_df['pro_X'][i], updated_df['pro_Y'][i], updated_df['RSI'][i]] for i in range(len(updated_df))]
        unknowns = [[df_unknown['pro_X'][i], df_unknown['pro_Y'][i]] for i in range(len(df_unknown))]
        estimates, errors = utils.OK(samples=knowns,
                                     unsampled=unknowns,
                                     model=semi_model[:3], n=semi_nugget, r=semi_range * 1000, s=semi_sill)

        estimates_xs, estimates_ys = utils.ConvertProjtoDegree(pro_xs=np.array(df_unknown['pro_X']),
                                                               pro_ys=np.array(df_unknown['pro_Y']))
        rsi_locations[0].marker['showscale'] = False
        updated_locations = [go.Scattermapbox(
            lon=np.concatenate([estimates_xs, np.array(updated_df['x'])]),
            lat=np.concatenate([estimates_ys, np.array(updated_df['y'])]),
            mode='markers',
            marker={'size': 10, 'opacity': 0.9,
                    'color': np.concatenate([estimates, np.array(updated_df['RSI'])]),
                    'colorscale': [[0, 'white'],[1, 'black']],
                    'cmin': 0,
                    'cmax': 1,
                    'showscale': True,
                    'colorbar': {'len': 0.8, 'title': '0 = icy/snowy; 1 = dry'},},
            hoverinfo='text',
            hovertext=np.concatenate([estimates, np.array(updated_df['RSI'])]),
            showlegend=True,
            name="Estimated RSI",
        )] + rsi_locations
    else:
        updated_locations = rsi_locations

    fig = go.Figure(data=updated_locations, layout=rsi_map_layout)

    # Return figure
    return fig



