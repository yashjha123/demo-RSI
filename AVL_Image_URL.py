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



firebase_db = firestore.Client(project="demorsi-a1501")


both_highways = gpd.read_file("maps/0_merged_I35_I80_pro_buffer20.shp") # in-built CRS 'epsg:26915'
both_highways = (both_highways.to_crs('EPSG:4326'))

import requests
from datetime import date
from db_handler.nicedb import NiceDB, NiceTable, BulkTable

db = NiceDB()
db.start()
db.test()

import requests
import random

SERVER_IP = "http://162.246.157.104:8080"
BASE_URL = f'https://mesonet.agron.iastate.edu/'
AVL_RULE = f"{SERVER_IP}/predict?img_url="

avl_ref = firebase_db.collection_group("Images")
# TODO: Adjust items to only hold the stid's (should automatically obtain all camera angles)
rwis_items = [(49,0),(30,0),(47,0),(53,0),(72,0),(48,2),(44,0),(14,0),(35,0),(26,0),(0,0)]

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
    startdate = date - datetime.timedelta(minutes=windowsize)
    enddate = date + datetime.timedelta(minutes=windowsize)
    query = firebase_db.collection_group("Images").where(filter=FieldFilter("Date", ">=", startdate)).where(filter=FieldFilter("Date", "<=", enddate)).stream()
    return query


def getLabel(result):
    labels =['Bare','Partly Snow Coverage','Undefined','Full Snow Coverage']
    return labels[result.index(max(result))]


disksave_bulk = BulkTable(db,"AVL_PRED",key="IMAGE_URL",value=["Bare","PartlySnowCoverage","Undefined","FullSnowCoverage"],high_load=True)
def checkcache(results, filter = True):
    global both_highways
    dashcams = []

    for doc in results:
        print((f"{doc.id} => {doc.to_dict()}"))
        data = doc.to_dict()
        data["imgurl"] = data["IMAGE_URL"]
        long, lat = data["Position"].longitude, data["Position"].latitude
        if filter:
            point = Point(long,lat)
            distances = (shapely.distance(point,both_highways.geometry) < 0.002)
            if (distances[0] or distances[1]) == False:
                continue

        # print("You got this!")
        # print(result_dict)
        res = [data["Bare"], data['Partly'], data['Undefined'], data['Full']]
        inp = getLabel(res)
        pred = {
            'prob_Bare': data['Bare'],
            'prob_Partly Snow Coverage': data['Partly'],
            'prob_Undefined': data['Undefined'],
            'prob_Full Snow Coverage': data['Full']
        }
        dashcam = {
            # 'name':data['cid'],
            # 'date':data['utc_valid'],
            'hovertext': inp,
            'LABEL': inp,
            'lon':long,    
            'lat':lat,
            'PHOTO_URL':data['imgurl'],
            'prob_Bare': res[0],
            'prob_Partly Snow Coverage': res[1],
            'prob_Undefined': res[2],
            'prob_Full Snow Coverage': res[3],
            'customdata': {'url':data['imgurl'],'preds':pred},
            'label':"AVL-"+inp,
            "RSI": 0.4 #BUG
        }
        dashcams.append(dashcam)
    return dashcams


import pandas as pd
rwis_disksave_bulk = BulkTable(db,"RWIS_PRED",key="IMAGE_URL",value=["Snow_Estimate_Ratio","SRC_MASK"],high_load=True)

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

def grab_avl_data_v2(todo):
    """
    Processes JSON to grab AVL specific data
    Output: [{Name, Date, Lat, Long, Camera Url},...]
    """
    dashcams = []
    result_dict = {}


    url = (f"{SERVER_IP}/predictBatchesV2")
    # print(results['data'])
    # print("IMG URLS",img_urls)
    # BATCH_SIZE = 20
    # for i in tqdm(range(0,len(results))):
    #     img_urls = [x['imgurl'] for x in results['data'][i:i+BATCH_SIZE]]
    #     # print(img_urls)
    img_urls = []
    for x in todo:
        # print(x)
        img_urls.append(x['imgurl'])
    data = {"img_urls": img_urls}
    print(len(img_urls))
    r = requests.post(url, json=data)
    result = (r.json())['result']
    # return (result)
    print(len(result.keys()))
    # result_dict.update(result)
    i = 0
    for img_url in tqdm(result.keys()):
        
    #     # inp = random.choice(['Full Snow Coverage','Partly Snow Coverage','Bare'])
    #     # res = requests.get(AVL_RULE+data['imgurl']).json()["result"]
        res = result[img_url]
        if type(res) == str:
            res = [0,0,0,0]
            inp = "Failed"
        else:
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
            'lon':todo[i]['lon'],    
            'lat':todo[i]['lat'],
            'PHOTO_URL':todo[i]['imgurl'],
            'prob_Bare': res[0],
            'prob_Partly Snow Coverage': res[1],
            'prob_Undefined': res[2],
            'prob_Full Snow Coverage': res[3],
            'customdata': {'url':img_url,'preds':pred,"type":"AVL"},
            'label':"AVL-"+inp,
            "RSI": 0.4 #BUG
        }
        dashcams.append(dashcam)
        i+=1

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