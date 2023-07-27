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
from dash import html, Patch, ctx, clientside_callback
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
from AVL_Image_URL import getPredictForOneImage, grab_avl_data_v2, grab_RWIS_data
from dash_extensions.enrich import Input, Output, State, Serverside


mapbox_access_token = "pk.eyJ1IjoibWluZ2ppYW53dSIsImEiOiJja2V0Y2lneGQxbzM3MnBuaWltN3RrY2QyIn0.P9tqv8lRlKbVw0_Tz2rPPw"

# ---------------------------------------------------------------
# from dash_bootstrap_mapbox_v3.py
# ---------------------------------------------------------------
# Menu callback, set and return
# Declare function that connects other pages with content to container

df, df_rwis, df_unknown, df_rwis_all = utils.load_data(date.today(),placeholder=False)

rsc_colors = {'Full Snow Coverage': 'white',
              'Partly Snow Coverage': 'grey',
              'Bare': 'black',
              'Undefined': '#FDDD0D',
              'Not labeled yet':'green',
              'Waiting...':'green',
              'Failed':'red'}
defined_labels = ['Full Snow Coverage',
                  'Partly Snow Coverage',
                  'Bare',
                  'Undefined']
rsc_labels = ['Full Snow Coverage',
              'Partly Snow Coverage',
              'Bare',
              'Undefined',
              'Failed']
# data = [rsc_colors]

# @app.callback([Output('rsc_colors', 'data'),],
#               [Input("url", "pathname")],)
# def init_data(pathname):
#     # data = []

#     if pathname == '/':
#         return data
#     elif pathname == '/rsi':
#         return data
#     elif pathname == '/spatial_mapping':
#         return data
#     else:
#         return data


@app.callback(Output("page-content", "children"),
              [Input("url", "pathname")])
def display_page(pathname):
    print(pathname)
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

@app.callback(Output("pick_date_time","disabled"),Input('live_button', 'on'))
def toggle_live_mode(value):
    return value

# @app.callback(Output("pick_date_time","value"), State("pick_date_time","value"), Input("auto_trigger", "n_intervals"))
# def refresh_data(pick_date_time,auto_trigger_intervals):
#     dt = datetime.datetime.now(CENTRAL)
#     # utc_time = dt.replace(tzinfo=UTC).timestamp()

#     last_time_triggered_central = CENTRAL.localize(parse(pick_date_time)).timestamp()
#     # last_time_triggered_utc = last_time_triggered_central.replace(tzinfo=UTC).timestamp()

#     print(utc_time - last_time_triggered_central)
#     if last_time_triggered_central == None or (dt.timestamp() - last_time_triggered_central)>60:
#         print("New value for last_time_triggered",dt)
#         # print("New value for last_time_triggered",utc_time-utc_time
#         return date.strftime(dt, "%Y-%m-%dT%H:%M")
#     # print("No update")
#     raise dash.exceptions.PreventUpdate
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
    output=Output("experimental", "data"),
    inputs=[Input("process_in_background", "data"),],
    running=[
        (
            Output("spinner_loader", "style"),
            {"display": "block"},
            {"display": "none"},
        ),
    ],
    background=True,
    cancel=[Input("process_in_background", "data")],
    prevent_initial_call=True,
    progress=[Output("cache","data")],
)
def run_calculation(set_progress,todo):
    # print(set_progress)
    # print("TADA5")
    if type(todo) == str and todo == "UsePlaceholder":
        return "We could not find any information for the specified date. Please ensure that you have chosen a date prior to the present. A sample dataset has been generated.."
    if todo == None or len(todo)==0:
        # set_progress(('1','1',prev_fig))
        # raise PreventUpdate
        return "Done"
    avl_todo = []
    rwis_todo = []
    for elem in todo:
        if elem['type'] == "avl":
            avl_todo.append(elem)
        elif elem['type'] ==  "rwis":
            rwis_todo.append(elem)
    BATCH_SIZE = 128
    progress = 0
    for i in range(0,len(rwis_todo),BATCH_SIZE):
        more = rwis_todo[i:i+BATCH_SIZE]
        progress+=len(more)
        new_plots = grab_RWIS_data(more)
        set_progress((new_plots,))
        # print(new_plots)
        time.sleep(3)
    for i in range(0,len(avl_todo),BATCH_SIZE):
        progress += len(avl_todo[i:i+BATCH_SIZE])
        new_plots = grab_avl_data_v2(avl_todo[i:i+BATCH_SIZE])
        
        set_progress((new_plots,))
        time.sleep(3)
        
    
    return "Done"


def get_avl_and_rwis_locations(df, df_rwis, df_rwis_all):
    df_subs = []
    print(df)
    
    if len(df) > 0:
        for rsc_type in list(rsc_colors.keys()):
            to_append = df[df['hovertext'] == rsc_type] # groups by category (AVL)
            # if len(to_append) == 0:
            #     pass
            # else:
            df_subs.append((rsc_type,to_append))

    # print("DF_SUBS",df_subs)
    avl_locations = [go.Scattermapbox(
        lon=df_sub['lon'],
        lat=df_sub['lat'],
        mode='markers',
        marker={'color': rsc_colors[rsc_type], 'size': 10, 'opacity': 1.0},
        hoverinfo='text',
        hovertext=df_sub['hovertext'],
        customdata=df_sub['customdata'],
        showlegend=True,
        name='AVL-'+rsc_type,
    ) for rsc_type, df_sub in df_subs]

    df_rwis_subs = []
    if(len(df_rwis_all)>0):
        for rsc_type in list(rsc_colors.keys()):
            to_append = df_rwis_all[df_rwis_all['RSC'] == rsc_type]
            df_rwis_subs.append((rsc_type,to_append))

    rwis_locations = [go.Scattermapbox(
        lon=df_sub['lon'],
        lat=df_sub['lat'],
        mode='markers',
        marker={'color': rsc_colors[rsc_type], 'size': 20, 'opacity': 0.8,},
        showlegend=True,
        hoverinfo='text',
        hovertext= df_sub['hovertext'],
        customdata=df_sub['customdata'],
        name='RWIS-'+rsc_type, # iloc grabs element at first index 
    ) for rsc_type,df_sub in df_rwis_subs]

    locations = avl_locations + rwis_locations
    
    # For RSI prediction
    if not df.empty:
        # https://stackoverflow.com/questions/19960077/how-to-filter-pandas-dataframe-using-in-and-not-in-like-in-sql
        criterion = lambda row: row['hovertext'] in defined_labels
        # not_in = df[df.apply(criterion, axis=1)]
        avl_points = df[df.apply(criterion, axis=1)][["RSI","lon",'lat','customdata']]
        pro_X, pro_Y = utils.ConvertDegreetoProj(longs=np.array(avl_points["lon"]),
                             lats=np.array(avl_points["lat"]))
        avl_points["pro_X"] = pro_X
        avl_points["pro_Y"] = pro_Y
    else:
        avl_points = pd.DataFrame(columns=['RSI','lon','lat','pro_X','pro_Y','customdata'])

    return avl_points, locations

#callback for the AVL points map
#to determine the file
# TODO: update for toggleable filter button
@app.callback(
    #Output('dd-output-container', 'children'),
    [Output('picked_df_rwis', 'data'),Output('avl_points','data'),
     Output('AVL_map', 'figure'),Output('process_in_background','data')],
    [Input('slider', 'value'),Input('pick_date_time', 'value')],
)
def load_map(window, pick_date_time):
    global rsc_colors
    triggered_id = ctx.triggered_id
    # if ctx.t
    print("TRIGGER ID",triggered_id)
    # if triggered_id!="rsc_colors":
    #     if cache!=None:
    #         print(cache)
    #         return [dash.no_update,dash.no_update,dash.no_update,dash.no_update,cache,dash.no_update]
    #     # quit()
    # print(prev_fig)
    todo = []

    print(pick_date_time)
    # print(parse(pick_date_time).replace(tzinfo=CENTRAL).astimezone(UTC))
    # print(parse(pick_date_time))
    # print(triggered)
    rsc_colors = rsc_colors

    df, df_rwis, df_unknown, df_rwis_all = utils.load_data(CENTRAL.localize(parse(pick_date_time)).astimezone(UTC),window=window) # TODO:
    # print(df)
    # df, df_rwis, df_unknown, df_rwis_all = utils.load_data(picked_date)

    
    # print(mean(df_rwis_all['lat'])) # 41.841316666666664
    # print(mean(df_rwis_all['lon'])) # -93.10251666666667
    map_layout = go.Layout(
        mapbox=go.layout.Mapbox(
            accesstoken=mapbox_access_token,
            center=go.layout.mapbox.Center(lat=41.841, lon=-93.102),
            style="dark",
            zoom=7,
            pitch=0,
        ),
        height=740,
        margin=dict(l=15, r=15, t=15, b=15),
        paper_bgcolor="#303030",
        font_color="white",
        # uirevision=True
    )
    avl_points, locations = get_avl_and_rwis_locations(df, df_rwis, df_rwis_all)
    # todo: implement a template_locations variables to remove redundance data packets
    # print(locations)
    # if len(locations):
    figure = go.Figure(data=locations, layout=map_layout)
    # else:
    #     df, df_rwis, df_unknown, df_rwis_all = utils.load_data(parse(pick_date_time), placeholder=False) # TODO:
    #     locations = get_avl_and_rwis_locations(df, df_rwis, df_rwis_all)
    #     figure = go.Figure(data=locations, layout=map_layout)
    #     todo = "UsePlaceholder"
    # figure.add
    # ptr = {'curveNumber': 1, 'pointNumber': 0, 'pointIndex': 0, 'lon': -93.8417, 'lat': 40.73867, 'customdata': '1_rwis_imgs_masks\\IDOT-026-00_202001191426img.jpg', 'hovertext': 'RLEI4', 'bbox': {'x0': 451.9141511111087, 'x1': 453.9141511111087, 'y0': 675.3332477751857, 'y1': 677.3332477751857}}
    # print(prev_fig)
    # if prev_fig != None:
    #     ret = {"data":[],"layout":prev_fig["layout"]}
    #     for x in range(len(figure.data)):
    #         ret['data'].append(figure.data[x])
    #     figure = ret
    # for plt in df:
    #     avl_points.append({'type':'avl','lon':plt['lon'],'lat':plt['lat'],'imgurl':plt})
    if len(df) > 0:
        for plt in (df[df['hovertext'] == "Not labeled yet"]).to_dict('records'):
            todo.append({'type':"avl",'lon':plt['lon'],'lat':plt['lat'],'imgurl':plt['PHOTO_URL']})
            
    if len(df_rwis_all) >0:
        for plt in (df_rwis_all[df_rwis_all['RSC'] == "Waiting..."]).to_dict('records'):
            todo.append({'type':'rwis','cid':plt['stid'],'lon':plt['lon'],'lat':plt['lat'],'imgurl':plt['customdata']['url']})
    # print("Figure looks like",figure)
    return [df_rwis.to_dict(),avl_points.to_dict(),figure,Serverside(todo)]


clientside_callback(
    """
    async function(new_points,prev_fig,avl_points) {
        console.log("AVL",avl_points)
        console.log(prev_fig)
        console.log(new_points)
        var indices = new Object();
        prev_fig['data'].forEach((element,i)=>{
            indices[element["name"]] = i
        })
        console.log(indices)
        const index_of_blank_RWIS = indices[ 'RWIS-Waiting...'];
        const index_of_blank_AVL = indices[ 'AVL-Not labeled yet'];
        new_points.forEach((new_point)=>{
            let ind = 0;
            let index_of_blank_data = 0;
            if(new_point["label"].startsWith("AVL")){
                index_of_blank_data = index_of_blank_AVL;
                const img_url = new_point['PHOTO_URL']
                ind = prev_fig['data'][index_of_blank_data]['customdata'].map((e)=>e.url).indexOf(img_url)


                /* Updating the AVL
                console.log(avl_points['customdata'])
                console.log(Object.keys(avl_points['customdata']).filter((key)=>avl_points['customdata'][key].url==img_url))
                
                const index_inside_avlp = Object.keys(avl_points['customdata']).filter((key)=>avl_points['customdata'][key].url==img_url)[0]
                */
                const new_index = Object.keys(avl_points["RSI"]).length;
                avl_points['RSI'][new_index] = new_point['RSI'];
                avl_points['lon'][new_index] = new_point['lon'];
                avl_points['lat'][new_index] = new_point['lat'];
                avl_points['customdata'][new_index] = new_point['customdata'];

            } else {
                console.log(new_point["label"])
                index_of_blank_data = index_of_blank_RWIS;

                const identifier = new_point['old_label'];
                ind = prev_fig['data'][index_of_blank_data]['hovertext'].indexOf(identifier)
                /*console.log(ind)
                console.log(index_of_blank_data)*/
            }
            
            prev_fig['data'][index_of_blank_data]['hovertext'].splice(ind, 1)
            prev_fig['data'][index_of_blank_data]['customdata'].splice(ind, 1)
            prev_fig['data'][index_of_blank_data]['lat'].splice(ind, 1)
            prev_fig['data'][index_of_blank_data]['lon'].splice(ind, 1)

            if(new_point["label"] in indices){
                const cri = indices[new_point['label']];
                prev_fig["data"][cri]['customdata'].push(new_point['customdata'])
                prev_fig["data"][cri]['hovertext'].push(new_point['hovertext'])
                prev_fig["data"][cri]['lon'].push(new_point['lon'])
                prev_fig["data"][cri]['lat'].push(new_point['lat'])
                console.log(new_point)
            }
        })
        console.log("changed prev_fig",prev_fig)
        console.log("avl_points",avl_points)
        return (Object.assign({}, prev_fig),avl_points);
    }
    """,
    [Output("AVL_map","figure",allow_duplicate=True),Output('avl_points','data',allow_duplicate=True)],
    Input('cache', 'data'),
    [State("AVL_map","figure"),State('avl_points','data')],
    prevent_initial_call=True
)
# @app.callback([Output("AVL_map","figure",allow_duplicate=True)],[Input("cache","data")],prevent_initial_call=True,)
# def function2(data):
#     print("Updating",data)
#     return (data,)

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
            if type(the_link) == str:
                return html.Img(
                    src=the_link['url'],
                    style={'max-height': '90%', 'max-width': '90%',
                           'display': 'block', 'margin-left': 'auto',
                           'margin-right': 'auto',})
            else:
                # print('check')
                    
                return html.Img(
                    src=the_link['url'],
                    style={'max-height': '70%', 'max-width': '70%',
                           'display': 'block', 'margin-left': 'auto',
                           'margin-right': 'auto',},)


# callback for pie_chart
@app.callback(
    [Output('dl_prediction', 'children'),Output('trigger_on_click','data')],
    [Input('AVL_map', 'clickData')],)
def display_dl_prediction(clickData):
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
            # print(the_link)

            img_url = the_link['url']
            if 'SnowPlow' in img_url or 'idot_trucks' in img_url:
                print("EE")

                try:
                    # try:
                    if the_link['preds'] == None:
                        print("WE AREN'T LABELLED YET")
                        values = []
                        labels = rsc_labels
                        classes = getPredictForOneImage(img_url)
                        # print(classes)
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
                        
                        # print(classes)
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
                            round(the_link['preds']['prob_' + label], 3))
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
                preds = clickData['points'][0]['customdata']['preds']
                # https://raw.githubusercontent.com/WMJason/demo-RSI/main/https:/mesonet.agron.iastate.edu/archive/data/2023/05/02/camera/IDOT-030-00/IDOT-030-00_202305022358.jpg
                if clickData['points'][0]['customdata'] is None:
                    return 'No Mask Available'
                else:
                    to_return = [
                        html.Img(
                        src=preds[0],
                        style={'max-height': '70%', 'max-width': '70%',
                               'display': 'inline-block', 'margin': 'auto',}
                        )
                    ]
                    return to_return, False
