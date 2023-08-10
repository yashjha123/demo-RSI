"""
An algorithm to automatically obtain AVL image urls to be used in a html-based webpage.
"""


from shapely.geometry import Polygon, LineString, Point
from google.cloud import firestore 
import datetime
from google.cloud.firestore_v1.base_query import FieldFilter, Or
from google.cloud.firestore_v1.field_path import FieldPath
import geopandas as gpd
import shapely
import time
from multiprocessing import Pool, freeze_support
from tqdm import tqdm


from check_for_archivev2 import isArchived, merge_archive_and_new
firebase_db = firestore.Client(project="demorsi-a1501")


both_highways = gpd.read_file("maps/0_merged_I35_I80_pro_buffer20.shp") # in-built CRS 'epsg:26915'
both_highways = (both_highways.to_crs('EPSG:4326'))

import requests
from datetime import date

import requests
import random

SERVER_IP = "http://162.246.157.104:8080"

BASE_URL = f'https://mesonet.agron.iastate.edu/'
AVL_RULE = f"{SERVER_IP}/predict?img_url="


avl_ref = firebase_db.collection_group("Images")
# TODO: Adjust items to only hold the stid's (should automatically obtain all camera angles)
rwis_items = [(49,0),(30,0),(47,0),(53,0),(72,0),(48,2),(44,0),(14,0),(35,0),(26,0),(0,0)]


def getRSI(lbl):
    ret = 0.0
    if lbl == 'Full Snow Coverage':
        ret = 0.35
    elif lbl == 'Partly Snow Coverage':
        ret = 0.8 - (0.8 - 0.5) * 0.4
        # updated_df.at[i, 'RSI'] = 0.8 - (0.8 - 0.5) * perc_white
        #updated_df.at[i, 'RSI'] = 0.8 - (0.8 - 0.5) * random.random()
    elif lbl == 'Bare':
        ret = 0.9
    return ret

def get_rwis_cameras(windowsize, date):
    """
    Grabs nearest image to date
    """
    print(date)
    def query_me(tup): # TODO: Check all angles and select non-empty
        stid, angle = tup
        query = firebase_db.collection_group(f"IDOT-{stid:03d}-{angle:d}").where(filter=FieldFilter("Date", "<=", date)).order_by("Date",  direction=firestore.Query.DESCENDING).limit(1)
        results = query.get()
        for doc in results:
            return doc
    return list(filter(lambda a:a!=None, list(map(query_me, rwis_items))))

# datee = datetime.datetime(year=2022, month=12, day=29, hour=12, minute=30)
# print(get_rwis_cameras(1,datee))


def get_cameras(windowsize, date):
    """
    Grabs AVL data within windowsize
    """
    print("NEW DATE",date)
    startdate = date - datetime.timedelta(minutes=windowsize)
    enddate = date + datetime.timedelta(minutes=windowsize)

    archived = isArchived(startdate,enddate)
    if archived:
        docs = firebase_db.collection_group("Images").where(filter=FieldFilter("Date", ">=", startdate)).where(filter=FieldFilter("Date", "<=", enddate)).stream()
    else:
        docs = merge_archive_and_new(date,windowsize)
    return docs


def getLabel(result):
    labels =['Bare','Partly Snow Coverage','Undefined','Full Snow Coverage']
    return labels[result.index(max(result))]

def checkcache(results, filter = True):
    global both_highways
    dashcams = []
    print("avl_results",results)
    for doc in results:

        if type(doc) != dict:
            data = doc.to_dict()
        else:
            data = doc
        print(data)
        
        data["imgurl"] = data["IMAGE_URL"]
        long, lat = data["Position"].longitude, data["Position"].latitude
        # if filter:
            # point = Point(long,lat)
            # distances = (shapely.distance(point,both_highways.geometry) < 0.002)
            # if (distances[0] or distances[1]) == False:
            #     continue

        # print("You got this!")
        # print(result_dict)
        if data.get('archive',True):
            res = [data["Bare"], data['Partly'], data['Undefined'], data['Full']]
            inp = getLabel(res)
            pred = {
                'prob_Bare': data['Bare'],
                'prob_Partly Snow Coverage': data['Partly'],
                'prob_Undefined': data['Undefined'],
                'prob_Full Snow Coverage': data['Full']
            }
        else:
            inp = 'Not labeled yet'
            pred = None
        dashcam = {
            # 'name':data['cid'],
            # 'date':data['utc_valid'],
            'hovertext': inp,
            'LABEL': inp,
            'lon':long,    
            'lat':lat,
            'date': data['Date'],
            'PHOTO_URL':data['imgurl'],
            'customdata': {'url':data['imgurl'],'preds':pred},
            'label':"AVL-"+inp,
            "RSI": getRSI(inp)
        }
        dashcams.append(dashcam)
    return dashcams


import pandas as pd

rwis_stations = pd.read_csv('0_RWIS_GPS_data_mod.csv')
d = rwis_stations.to_dict('records')
stations = {}
for x in d:
    stations[x['cid']] = [x['Latitude'],x['Longitude (-W)']]

def checkrwiscache(results, filter=True):
    """ 
    Modification of checkcache to work with RWIS API
    """
    rwiscams = []
    img_urls = []
    print(list(results))
    for doc in tqdm(results):
        # TODO: conversion of estimate ratio to rsi ranges
        # bare: 0.8-1.0
        # part snow: 0.5-0.8
        # full: 0.2-0.5
        data = doc.to_dict()
        estimate_ratio = data['Snow_estimate_Ratio']
        if estimate_ratio >= 0.8:
            category = 'Bare'
        elif estimate_ratio >= 0.5:
            category = 'Partly Snow Coverage'
        else:
            category = 'Full Snow Coverage'

        rwiscam = {
            'stid': data['Station_ID'],
            'lon':stations[data['Station_ID']][1],    
            'lat':stations[data['Station_ID']][0],
            'customdata':{'url':data['image_url'], 'preds':[data['SRC_MASK'], data['SRC_MASK']]}, # preds = output masks (2)
            'RSC': category, # Predicted category
            "RSI": estimate_ratio, #BUG
            'label':"RWIS-"+category,
            "hovertext": data['Station_ID'] + "<br>" + str(estimate_ratio) 
        }
        rwiscams.append(rwiscam)
    return rwiscams

import ast

API_URL = 'https://us-central1-demorsi-a1501.cloudfunctions.net/demo_api'
def make_avl_predictions(todo):
    """
    Processes JSON to grab AVL specific data
    Output: [{Name, Date, Lat, Long, Camera Url},...]
    """
    dashcams = []

    outputs = []
    for point in todo:
        print(point)
        img_url = point["imgurl"]
        location = [point["lat"], point["lon"]]

        outputs.append({
            "position":location,
            "image_url":img_url,
            "date":point["date"].strftime("%Y-%m-%dT%H:%M")
        })
        
    res = requests.post(API_URL, json={"input": outputs})
    return_json = ast.literal_eval(res.text)

    for point in tqdm(return_json.values()):

        res = point['pred']
        
        inp = getLabel(res)
        pred = {
            'prob_Bare': res[0],
            'prob_Partly Snow Coverage': res[1],
            'prob_Undefined': res[2],
            'prob_Full Snow Coverage': res[3]
        }
        dashcam = {
            # 'name':data['cid'],
            # 'date':data['utc_valid'],
            'hovertext': inp,
            'LABEL': inp,
            'lon':point['position'][1],
            'lat':point['position'][0],
            'PHOTO_URL':point['image_url'],
            'customdata': {'url':img_url,'preds':pred,"type":"AVL"},
            'label':"AVL-"+inp,
            "RSI": getRSI(inp) #BUG
        }
        dashcams.append(dashcam)

    return dashcams


def getPredictForOneImage(img_url):
    url = (f"{SERVER_IP}/predict")
    r = requests.get(url+"?img_url="+img_url)

    res = (r.json())['result']
    inp = getLabel(res)
    pred = {
            'prob_Bare': res[0],
            'prob_Partly Snow Coverage': res[1],
            'prob_Undefined': res[2],
            'prob_Full Snow Coverage': res[3]
        }
    dashcam = {
        # 'name':data['cid'],
        # 'date':data['utc_valid'],
        'PHOTO_URL':img_url,
        'hovertext': inp,
        'LABEL': inp,
        'prob_Bare': res[0],
        'prob_Partly Snow Coverage': res[1],
        'prob_Undefined': res[2],
        'prob_Full Snow Coverage': res[3],
        'label':"AVL-"+inp,
        'customdata': {'url':img_url,'preds':pred,"type":"AVL"},
    }
    # ret = {
    #     'prob_Bare': res[0],
    #     'prob_Partly Snow Coverage': res[1],
    #     'prob_Undefined': res[2],
    #     'prob_Full Snow Coverage': res[3],
    # }
    return dashcam