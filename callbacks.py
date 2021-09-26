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


# ---------------------------------------------------------------
# from dash_bootstrap_mapbox_v3.py
# ---------------------------------------------------------------
# Menu callback, set and return
# Declair function  that connects other pages with content to container
@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def display_page(pathname):
    if pathname == '/':
        return index_page.HomePage()
    elif pathname == '/rsi':
        return rsi_page.HomePage()
    else:
        return html.H5('You are looking at path = ' + pathname)


# callback for Web_link
@app.callback(
    Output("web_link", "children"),
    [Input('map', 'clickData')],
)
def display_click_data(clickData):
    if clickData is None:
        return 'Click on any dot'
    else:
        # print (clickData)
        the_link = clickData['points'][0]['customdata']
        if the_link is None:
            return 'No Photo Available'
        else:
            return html.Img(
                src=the_link,
                style={'max-height': '100%', 'max-width': '100%', })


# callback for pie_chart
@app.callback(
    Output('pie_chart', 'figure'),
    [Input('map', 'clickData')])
def display_pie_chart(clickData):
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
        return fig
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
            return fig
        else:
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
                showlegend=True,
                margin=dict(t=10, b=0, l=10, r=0),
                paper_bgcolor="#303030",
                plot_bgcolor="#303030",
                font_color="white",
            )
            return fig


# from dash_bootstrap_mapbox_v3_rsi.py
# callback for Semivariogram Figure
@app.callback(
    Output("semi_fig", "figure"),
    [Input('semi-model', 'value'),
     Input('semi-nugget', 'value'),
     Input('semi-range', 'value'),
     Input('semi-sill', 'value')],
)
def plot_semi_fig(semi_model, semi_nugget, semi_range, semi_sill):
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
# df = crop_cal_perc_white_black.ObtainAdjustedRSI(df=df)
knowns = [[df['pro_X'][i], df['pro_Y'][i], df['RSI'][i]] for i in range(len(df))]

df_unknown = pd.read_csv("3_2018-11-25_7_STATEOFIOWAI35N.csv")
unknowns = [[df_unknown['pro_X'][i], df_unknown['pro_Y'][i]] for i in range(len(df_unknown))]


@app.callback(
    Output('map', 'figure'),
    [Input('rsi_interpolate', 'n_clicks')],
    [State('semi-model', 'value'),
     State('semi-nugget', 'value'),
     State('semi-range', 'value'),
     State('semi-sill', 'value')], )
def update_rsi_map(n_clicks, semi_model, semi_nugget, semi_range, semi_sill):
    rsi_locations = [go.Scattermapbox(
        lon=updated_df['x'],
        lat=updated_df['y'],
        mode='markers',
        marker={'size': 10, 'opacity': 0.6, 'color': updated_df['RSI'], 'showscale': True,
                'colorbar': {'len': 0.8}, },
        hoverinfo='text',
        hovertext=updated_df['RSI'],
        customdata=updated_df['PHOTO_URL'],
        showlegend=True,
        name="Observed RSI",
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
            marker={'size': 8, 'opacity': 0.4, 'color': np.concatenate([estimates, np.array(updated_df['RSI'])]),
                    'showscale': True,
                    'colorbar': {'len': 0.8}, },
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
