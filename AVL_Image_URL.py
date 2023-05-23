"""
An algorithm to automatically obtain AVL image urls to be used in a html-based webpage.
Code: Michael Urbiztondo
"""

from shapely.geometry import Polygon, LineString, Point

import geopandas as gpd
import shapely

both_highways = gpd.read_file("maps/0_merged_I35_I80_pro_buffer20.shp") # in-built CRS 'epsg:26915'
both_highways = (both_highways.to_crs('EPSG:4326'))

import requests
from datetime import date

import requests
import random
BASE_URL = f'https://mesonet.agron.iastate.edu/'

AVL_RULE = f"http://127.0.0.1:8080/predict?img_url="

def get_cameras(window_size, time):
    """
    Grabs latest AVL images based on window size
    """
    # https://mesonet.agron.iastate.edu/api/1/idot_dashcam.json?window=15
    # 2023-02-07T14:31Z",
    URL = BASE_URL + 'api/1/idot_dashcam.json?window=' + window_size + '&valid=' + time
    print(URL)
    response = requests.get(URL)
    data = response.json()
    status = response.status_code
    if status != 200:
        data = None

    return data

def get_rwis_cameras(window_size, time):
    """
    Grabs latest RWIS images based on window size
    """
    # https://mesonet.agron.iastate.edu/api/1/idot_rwiscam.json?window=15
    # 2023-02-07T14:31Z",
    URL = BASE_URL + 'api/1/idot_rwiscam.json?window=' + window_size + '&valid=' + time
    print(URL)
    response = requests.get(URL)
    data = response.json()
    status = response.status_code
    if status != 200:
        data = None

    return data

from tqdm import tqdm
def getLabel(result):
    labels =['Bare','Partly Snow Coverage','Undefined','Full Snow Coverage']
    return labels[result.index(max(result))]

def checkcache(results, filter = True):
    global both_highways
    img_urls = []
    for d in results['data']:
        img_urls.append(d['imgurl'])
    dashcams = []
    url = ("http://127.0.0.1:8080/loadFromCache")

    data = {"img_urls": img_urls}
    r = requests.post(url, json=data)
    result_dict = (r.json())['result']
    for data in results['data']:

        if filter:
            point = Point(data['lon'],data['lat'])
            distances = (shapely.distance(point,both_highways.geometry) < 0.002)
            if (distances[0] or distances[1]) == False:
                continue

        if result_dict[data['imgurl']] == "None":
            # print("What happened?")
            dashcam = {
                # 'name':data['cid'],
                # 'date':data['utc_valid'],
                'Predict': "Not labeled yet",
                'LABEL': "Not labeled yet",
                'x':data['lon'],    
                'y':data['lat'],
                'PHOTO_URL':data['imgurl'],
                "RSI": 0.4 #BUG
            }
        else:
            # print("You got this!")
            # print(result_dict)
            res = result_dict[data['imgurl']]
            # print(res)
            # print(data['imgurl'])
            inp = getLabel(res)
            dashcam = {
                # 'name':data['cid'],
                # 'date':data['utc_valid'],
                'Predict': inp,
                'LABEL': inp,
                'x':data['lon'],    
                'y':data['lat'],
                'PHOTO_URL':data['imgurl'],
                'prob_Bare': res[0],
                'prob_Partly Snow Coverage': res[1],
                'prob_Undefined': res[2],
                'prob_Full Snow Coverage': res[3],
                "RSI": 0.4 #BUG
            }
        dashcams.append(dashcam)
    return dashcams

import pandas as pd

def checkrwiscache(results, filter=True):
    """ 
    Modification of checkcache to work with RWIS API
    # TODO: Modify dashcam keys/columns to the same format seen in callbacks.py: line 222, 228-238
    # IDOT-072: should be undefined case
    """
    rwis_stations = pd.read_csv('0_RWIS_GPS_data_mod.csv')
    img_urls = []
    for d in results['data']:
        for key in d.keys():
            if key.startswith('imgurl'):
                if d[key] is not None:
                    imgurl = d[key]
                    break
        img_urls.append(imgurl)

    dashcams = []
    # TODO: -v uncomment this for caching implementation
    url = ("http://127.0.0.1:8080/snow_estimate")
    # data = {"img_urls": img_urls}
    # r = requests.post(url, json=data)
    # result_dict = (r.json())['result']
    for i, data in tqdm(enumerate(results['data'])):
        # print(data)

        
        # TODO: Convert NWS ID to cid format (or vice versa), using github repo code 
        # - even better: add a column with all the respective cids or whatever into 0_RWIS_GPS_data.csv
        rwis_row = rwis_stations[rwis_stations['cid'] == data['cid']].values
        if len(rwis_row) == 0:
            continue
        rwis_row = rwis_row[0]

        if filter:
            point = Point(rwis_row[1],rwis_row[0])
            distances = (shapely.distance(point,both_highways.geometry) < 0.002)
            # print(point)
            # print(distances)
            if (distances[0] or distances[1]) == False:
                continue
        # if result_dict[data['imgurl']] == "None":
        #     print("What happened?")
        #     dashcam = {
        #         # 'name':data['cid'],
        #         # 'date':data['utc_valid'],
        #         'Predict': "Not labeled yet",
        #         'LABEL': "Not labeled yet",
        #         'x':data['lon'],    
        #         'y':data['lat'],
        #         'PHOTO_URL':data['imgurl'],
        #         "RSI": 0.4 #BUG
        #     }
        #else:

        # TODO: uncomment below -v :(
        # res = result_dict[data['imgurl']]
        # inp = getLabel(res)

        data1 = {"img_url": img_urls[i]}

        r = requests.post(url, json=data1) 
        result_dicte = (r.json())['result']
        estimate_ratio = result_dicte['estimate_ratio']
        print(estimate_ratio)
        # estimate_ratio = 0.6
        # Todo: conversion of estimate ratio to rsi ranges
        # bare: 0.8-1.0
        # part snow: 0.5-0.8
        # full: 0.2-0.5
        if estimate_ratio >= 0.8:
            category = 'Bare'
        elif estimate_ratio >= 0.5:
            category = 'Partly Snow Coverage'
        else:
            category = 'Full Snow Coverage'

        # TODO: add option to see generated mask
        # interpret image from binary data
        # optimize rwis ml function

        dashcam = {
            'stid': data['cid'],
            'lon':rwis_row[1],    
            'lat':rwis_row[0],
            'img_path':img_urls[i],
            'RSC': category, # Predicted category
            "RSI": 0.4 #BUG
        }
        dashcams.append(dashcam)
    return dashcams


def grab_avl_data(results):
    """
    Processes JSON to grab AVL specific data
    Output: [{Name, Date, Lat, Long, Camera Url},...]
    """
    dashcams = []
    result_dict = {}


    url = ("http://127.0.0.1:8080/predictBatches")
    print(results['data'])
    BATCH_SIZE = 20
    for i in tqdm(range(0,len(results['data']),BATCH_SIZE)):
        img_urls = [x['imgurl'] for x in results['data'][i:i+BATCH_SIZE]]
        # print(img_urls)
        data = {"img_urls": img_urls}
        r = requests.post(url, json=data)
        result = (r.json())['result']
        # print(result)
        result_dict.update(result)

    for data in tqdm(results['data']):
        
        # inp = random.choice(['Full Snow Coverage','Partly Snow Coverage','Bare'])
        # res = requests.get(AVL_RULE+data['imgurl']).json()["result"]
        res = result_dict[data['imgurl']]
        inp = getLabel(res)
        dashcam = {
            # 'name':data['cid'],
            # 'date':data['utc_valid'],
            'Predict': inp,
            'LABEL': inp,
            'x':data['lon'],    
            'y':data['lat'],
            'PHOTO_URL':data['imgurl'],
            'prob_Bare': res[0],
            'prob_Partly Snow Coverage': res[1],
            'prob_Undefined': res[2],
            'prob_Full Snow Coverage': res[3],
            "RSI": 0.4 #BUG
        }
        dashcams.append(dashcam)

    return dashcams


def grab_avl_data_v2(todo):
    """
    Processes JSON to grab AVL specific data
    Output: [{Name, Date, Lat, Long, Camera Url},...]
    """
    dashcams = []
    result_dict = {}


    url = ("http://127.0.0.1:8080/predictBatchesV2")
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
    r = requests.post(url, json=data)
    result = (r.json())['result']
    # return (result)
    # result_dict.update(result)
    i = 0
    for img_url in tqdm(result.keys()):
        
    #     # inp = random.choice(['Full Snow Coverage','Partly Snow Coverage','Bare'])
    #     # res = requests.get(AVL_RULE+data['imgurl']).json()["result"]
        res = result[img_url]
        inp = getLabel(res)
        dashcam = {
            # 'name':data['cid'],
            # 'date':data['utc_valid'],
            'Predict': inp,
            'LABEL': inp,
            'x':todo[i]['lon'],    
            'y':todo[i]['lat'],
            'PHOTO_URL':todo[i]['imgurl'],
            'prob_Bare': res[0],
            'prob_Partly Snow Coverage': res[1],
            'prob_Undefined': res[2],
            'prob_Full Snow Coverage': res[3],
            "RSI": 0.4 #BUG
        }
        dashcams.append(dashcam)
        i+=1

    return dashcams


def getPredictForOneImage(img_url):
    url = ("http://127.0.0.1:8080/predict")
    r = requests.get(url+"?img_url="+img_url)

    res = (r.json())['result']
    inp = getLabel(res)
    dashcam = {
        # 'name':data['cid'],
        # 'date':data['utc_valid'],
        'PHOTO_URL':img_url,
        'Predict': inp,
        'LABEL': inp,
        'prob_Bare': res[0],
        'prob_Partly Snow Coverage': res[1],
        'prob_Undefined': res[2],
        'prob_Full Snow Coverage': res[3],
    }
    # ret = {
    #     'prob_Bare': res[0],
    #     'prob_Partly Snow Coverage': res[1],
    #     'prob_Undefined': res[2],
    #     'prob_Full Snow Coverage': res[3],
    # }
    return dashcam

def convert_UTC():
    pass

def main():
    window_size = '100'
    today = date.today().strftime("%Y/%m/%d/") # TODO: Input user defined UTC Timestamp
    # convert_UTC()
    
    results = get_cameras(window_size)
    print(grab_avl_data(results))


if __name__ == '__main__':
    main()