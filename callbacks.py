from datetime import datetime as dt
from datetime import date, timedelta
import time
import os
from dash.exceptions import PreventUpdate

# import plotly.graph_objects as go

from statistics import mean
from random import randint, shuffle
from dateutil.parser import parse
import numpy as np
import pandas as pd
import plotly.graph_objs as go
import dash
from dash import dcc
from dash import html
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
from AVL_Image_URL import getPredictForOneImage, grab_avl_data_v2
from dash_extensions.enrich import Input, Output, State, FileSystemCache, Trigger, ServersideOutput


mapbox_access_token = "pk.eyJ1IjoibWluZ2ppYW53dSIsImEiOiJja2V0Y2lneGQxbzM3MnBuaWltN3RrY2QyIn0.P9tqv8lRlKbVw0_Tz2rPPw"

# ---------------------------------------------------------------
# from dash_bootstrap_mapbox_v3.py
# ---------------------------------------------------------------
# Menu callback, set and return
# Declair function  that connects other pages with content to container

class TraceInfo:
    def __init__(self, figure):
        self.fig = figure
        self.traces = self.__traces()
        self.number = self.__len__()
        self.names = self.__trace_names()
        self.colors = self.__trace_colors()

    def __getitem__(self, index):
        return self.traces[index]

    def __len__(self):
        return len(self.traces)

    def __traces(self):
        return self.fig.get('data', [])

    def __trace_colors(self):
        return [trace.get('marker', {}).get('color') for trace in self.traces]

    def __trace_names(self):
        return [trace.get('name') for trace in self.traces]

df, df_rwis, df_unknown, df_rwis_all = utils.load_data(date.today())

rsc_colors = {'Full Snow Coverage': 'white',
              'Partly Snow Coverage': 'grey',
              'Bare': 'black',
              'Undefined': '#FDDD0D',
              'Not labeled yet':'green'}

rsc_labels = ['Full Snow Coverage',
              'Partly Snow Coverage',
              'Bare',
              'Undefined']
data = [df.to_dict(), df_rwis.to_dict(), df_unknown.to_dict(), df_rwis_all.to_dict(),rsc_colors]

@app.callback([Output('df', 'data'),Output('df_rwis', 'data'),
               Output('df_unknown', 'data'),Output('df_rwis_all', 'data'),
               Output('rsc_colors', 'data'),],
              [Input("url", "pathname")],)
def init_data(pathname):
    # data = []

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

# Background process call
# @app.callback() 
# @app.callback(Input("done_points","data"),Input("process_in_background","data"))
# def show_progress_bar()

# @app.callback(Output("result", "children"), Trigger("interval", "n_intervals"))
# def update_progress():
#     value = fsc.get("progress")  # get progress
#     print("FSC",value)
#     if value is None:
#         return "Not started yet!"
#     return "Progress is {:.0f}%".format(float(fsc.get("progress")) * 100)


def tuple_append(tup,elem):
    return tuple(list(tup)+[(elem)])
@app.callback(
    output=Output("result", "children"),
    inputs=[Input("process_in_background", "data"),State('AVL_map', 'figure'),State('pick_date', 'value')],
    running=[
        (
            Output("result", "style"),
            {"display": "none"},
            {"display": "block"},
        ),
        (
            Output("progress_bar", "style"),
            {"display": "block"},
            {"display": "none"},
        ),
        (
            Output("spinner_loader", "style"),
            {"display": "block"},
            {"display": "none"},
        ),    
        (
            Output("cancel_button_id", "style"),
            {"display": "block"},
            {"display": "none"},
        ),
        (Output("cancel_button_id", "disabled"), False, True),
    ],
    background=True,
    cancel=[Input("cancel_button_id", "n_clicks"),Input('pick_date_time', 'date')],
    prevent_initial_call=True,
    progress=[Output("progress_bar", "value") ,Output('AVL_map', 'figure')],
)
def run_calculation(set_progress,todo,prev_fig,selected_date):
    # print(set_progress)
    print("TADA5")
    if todo == None or len(todo)==0:
        # set_progress(('1','1',prev_fig))
        # raise PreventUpdate
        return "Done"

    # print(todo)
    print(" ")

    BATCH_SIZE = 32*4
    # for i in range(100):
    #     time.sleep(0.5)
    #     set_progress((str(i + 1), str(100)))
    # return [f"Clicked {100} times"]
    # print(prev_fig)
    not_labelled_index = 0
    # for x in range(len(prev_fig['data'])):
    #     d[prev_fig['data'][x]['hovertext'][0]] = x
    #     print(prev_fig['data'][x]['hovertext'][0],x)
        # if(prev_fig['data'][x]['hovertext'][0]=='Not labeled yet'):
        #     not_labelled_index = x
        #     break
    
    for i in range(0,len(todo),BATCH_SIZE):
        d = {}
        new_d = {}
        for color in rsc_labels:
            new_d[color] = []
        for x in range(len(prev_fig['data'])):
            # print(d['da'])
            d[prev_fig['data'][x]['hovertext'][0]] = x
            print(prev_fig['data'][x]['hovertext'][0],x)
        new_plots = grab_avl_data_v2(todo[i:i+BATCH_SIZE])
        not_labelled_index = d['Not labeled yet']
        # getPredictForOneImage(url)
        # print(i)
        for new_plot in new_plots:
            img_url = new_plot['PHOTO_URL']
            ind = prev_fig['data'][not_labelled_index]['customdata'].index(img_url)
            
            prev_fig['data'][not_labelled_index]['customdata'].pop(ind)
            prev_fig['data'][not_labelled_index]['hovertext'].pop(ind)
            prev_fig['data'][not_labelled_index]['lat'].pop(ind)
            prev_fig['data'][not_labelled_index]['lon'].pop(ind)
            # ans_indx = d[(new_plot['Predict'])]
            # print(new_plot)

            if new_plot['Predict'] in d.keys():
                cri = d[new_plot['Predict']]
                # print(prev_fig['data'][cri]['customdata'])
                # print(prev_fig['data'][cri]['hovertext'])
                # print(prev_fig['data'][cri]['lon'])
                # print(prev_fig['data'][cri]['lat'])
                prev_fig['data'][cri]['customdata'] = tuple_append(prev_fig['data'][cri]['customdata'],new_plot['PHOTO_URL'])
                prev_fig['data'][cri]['hovertext'] = tuple_append(prev_fig['data'][cri]['hovertext'],new_plot['Predict'])
                prev_fig['data'][cri]['lon'] = tuple_append(prev_fig['data'][cri]['lon'],new_plot['x'])
                prev_fig['data'][cri]['lat'] = tuple_append(prev_fig['data'][cri]['lat'],new_plot['y'])
            else:
                new_d[new_plot['Predict']].append(new_plot)
        avl_locations = []
        for color in rsc_labels:
            lons = [x['x'] for x in new_d[color]]
            lats = [x['y'] for x in new_d[color]]
            labels = [x['Predict'] for x in new_d[color]]
            imgs = [x['PHOTO_URL'] for x in new_d[color]]
            if len(labels) > 0:
                avl_locations.append(go.Scattermapbox(
                    lon=lons,
                    lat=lats,
                    mode='markers',
                    marker={'color': rsc_colors[color], 'size': 10, 'opacity': 1.0},
                    hoverinfo='text',
                    hovertext=labels,
                    customdata=imgs,
                    showlegend=True,
                    name='AVL-'+labels[0],
                ))
        map_layout = go.Layout(
            mapbox=go.layout.Mapbox(
                accesstoken=mapbox_access_token,
                style="dark",
                zoom=7,
                pitch=0,
            ),
            height=740,
            margin=dict(l=15, r=15, t=15, b=15),
            paper_bgcolor="#303030",
            font_color="white",
            uirevision=True
        )
        new_fig = go.Figure(data=avl_locations, layout=map_layout)
        prev_fig['data'].extend(new_fig['data'])
          
        print(str(i), str(len(todo)))
        set_progress((str(i*100/len(todo)),prev_fig))
    
    #     # fsc.set("progress",str(i))
    # set_progress(('1','1'))
    return "Done"


#callback for the AVL points map
#to determine the file
@app.callback(
    #Output('dd-output-container', 'children'),
    [Output('picked_df', 'data'),Output('picked_df_rwis', 'data'),Output('picked_df_unknown', 'data'),
     Output('picked_df_rwis_all', 'data'),Output('AVL_map', 'figure'),ServersideOutput('process_in_background','data')],
    [Input('pick_date', 'value'),Input('pick_date_time', 'date'),Input('rsc_colors', 'data')],
    [State('AVL_map', 'figure')] 
)
def load_map(pick_date, pick_date_time, rsc_colors, prev_fig):
    # print(prev_fig)

    # print(parse(pick_date_time))
    # print(triggered)
    rsc_colors = rsc_colors
    
    if pick_date != 'Nighttime':
        picked_date = '2'
    else:
        picked_date = ''

    df, df_rwis, df_unknown, df_rwis_all = utils.load_data(parse(pick_date_time)) # TODO:

    # df, df_rwis, df_unknown, df_rwis_all = utils.load_data(picked_date)

    df_subs = []
    # print
    
    if len(df) > 0:
        for rsc_type in list(rsc_colors.keys()):
            to_append = df[df['Predict'] == rsc_type] # groups by category (AVL)
            if len(to_append) == 0:
                pass
            else:
                df_subs.append(to_append)

    # print("DF_SUBS",df_subs)
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
        name='RWIS-'+df_sub['RSC'].iloc[0], # iloc grabs element at first index 
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
        font_color="white",
        uirevision=True
    )
    figure = go.Figure(data=locations, layout=map_layout)
    # figure.add
    # ptr = {'curveNumber': 1, 'pointNumber': 0, 'pointIndex': 0, 'lon': -93.8417, 'lat': 40.73867, 'customdata': '1_rwis_imgs_masks\\IDOT-026-00_202001191426img.jpg', 'hovertext': 'RLEI4', 'bbox': {'x0': 451.9141511111087, 'x1': 453.9141511111087, 'y0': 675.3332477751857, 'y1': 677.3332477751857}}
    # print(prev_fig)
    if prev_fig != None:
        ret = {"data":[],"layout":prev_fig["layout"]}
        for x in range(len(figure.data)):
            ret['data'].append(figure.data[x])
            # prev_fig['data'][x]['hoverinfo']=figure.data[x].hoverinfo
            # prev_fig['data'][x]['hovertext']=figure.data[x].hovertext
            # prev_fig['data'][x]['lat']=figure.data[x].lat
            # prev_fig['data'][x]['lon']=figure.data[x].lon
            # prev_fig['data'][x]['marker']=figure.data[x].marker
            # prev_fig['data'][x]['mode']=figure.data[x].mode
            # prev_fig['data'][x]['name']=figure.data[x].name
            # prev_fig['data'][x]['showlegend']=figure.data[x].showlegend
            # prev_fig['data'][x]['type']=figure.data[x].type
        figure = ret
    # print(figure.data[0].customdata)
    # figure.add_trace(go.Scattermapbox(
    #             lon=(-93.8417,),
    #     lat=(40.73867,),
    #     mode='markers',
    #     marker={'color': rsc_colors["Full Snow Coverage"], 'size': 10, 'opacity': 1.0},
    #     hoverinfo='text',
    #     hovertext="AVL-DATA",
    #     customdata=("http://cloud.iowadot.gov/Highway/Photos/Maintenance/MapSnapShots/SnowPlow/2019/1/12/A33976-2019-01-12_07_15_26.jpg",),
    #     showlegend=True,
    #     name="AVL-DATA"
    # ))

    todo = []
    # print(df[df['Predict'] == "Not labeled yet"])
    if len(df) > 0:
        # print(df)
        for plt in (df[df['Predict'] == "Not labeled yet"]).to_dict('records'):
            # print(plt)
            todo.append({'lon':plt['x'],'lat':plt['y'],'imgurl':plt['PHOTO_URL']})
    # ['PHOTO_URL'].values)
    print("TADA")
    return [df.to_dict(), df_rwis.to_dict(), df_unknown.to_dict(), df_rwis_all.to_dict(),figure,todo]


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
                # print('check')
                if the_link.startswith("https"):
                    the_link = the_link.replace('\\','/') #'https://raw.githubusercontent.com/WMJason/demo-RSI/main/'+the_link.replace('\\','/')
                else:
                    the_link = 'https://raw.githubusercontent.com/WMJason/demo-RSI/main/'+the_link.replace('\\','/')
                    
                return html.Img(
                    src=the_link,
                    style={'max-height': '70%', 'max-width': '70%',
                           'display': 'block', 'margin-left': 'auto',
                           'margin-right': 'auto',},)


# callback for pie_chart
@app.callback(
    [Output('dl_prediction', 'children'),Output('trigger_on_click','data')],
    [Input('AVL_map', 'clickData'), Input('picked_df', 'data')],)
def display_dl_prediction(clickData, df):
    print(clickData)
    # avl_fig = (go.Figure(avl_fig))
    if clickData is None:
        print("AAA")
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
        return to_return, False
    else:
        print("BBB")

        # print (clickData)
        the_link = clickData['points'][0]['customdata']
        # print("B",the_link)

        if the_link is None:
            print("CCC")

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
            return to_return, False
        else:
            print("DDD")

            if 'SnowPlow' in the_link or 'idot_trucks' in the_link:
                print("EEE")
                try:
                    df = pd.DataFrame.from_dict(df)
                    # try:
                    if df[df['PHOTO_URL'] == the_link]["LABEL"].values[0] == "Not labeled yet":
                        print("WE AREN'T LABELLED YET")
                        values = []
                        labels = rsc_labels
                        classes = getPredictForOneImage(the_link)
                        print(classes)
                        for label in labels:
                            values.append(
                                round(classes['prob_' + label], 3))
                        colors = list(rsc_colors.values())

                        fig = go.Figure(data=[
                            go.Pie(labels=labels, values=values, hole=.4, marker={'colors': colors}, )])
                        # to_return = [
                        #     dbc.CardBody(
                        #         html.Center(
                        #             dbc.Spinner(spinner_style={"width": "5rem", "height": "5rem"},color="light")
                        #         )
                        #     )
                        # ]
                        fig.update_layout(
                            height=300,
                            showlegend=True,
                            margin=dict(t=10, b=0, l=10, r=0),
                            paper_bgcolor="#303030",
                            plot_bgcolor="#303030",
                            font_color="white",
                        )
                        
                        print(classes)
                        to_return = [
                            dbc.CardBody(
                                dcc.Graph(
                                    id="pie_chart",
                                    figure=fig,
                                    config={'displayModeBar': False},
                                ),
                            )
                        ]
                        return to_return, classes        
                    labels = rsc_labels
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
                except Exception as e:
                    print("EXCEPTION CALLED!!")
                    print(e)
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
                return to_return, False
            else:
                print("WHY ARE WE HERE?")
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
                    return to_return, False



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
     State('semi-sill', 'value'),
     State('picked_df_rwis', 'data')], )
def update_rsi_map(n_clicks, updated_df, df_unknowns, semi_model, semi_nugget, semi_range, semi_sill, df_rwis):
    updated_df = pd.DataFrame.from_dict(updated_df)
    df_rwis = pd.DataFrame.from_dict(df_rwis) # 
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



