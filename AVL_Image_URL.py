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

SERVER_IP = "http://127.0.0.1:8080"

BASE_URL = f'https://mesonet.agron.iastate.edu/'

AVL_RULE = f"{SERVER_IP}/predict?img_url="

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
    # db_vals = disksave_bulk[img_urls]
    # data = {"img_urls": img_urls}
    # r = requests.post(url, json=data)
    result_dict = {}
    for url in img_urls: result_dict[url] = "None"
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
                'hovertext': "Not labeled yet",
                'LABEL': "Not labeled yet",
                'lon':data['lon'],    
                'lat':data['lat'],
                'PHOTO_URL':data['imgurl'],
                "RSI": getRSI("Not labeled yet"), #BUG
                'label':"AVL-"+"Not labeled yet",
                'customdata':{'url':data['imgurl'],'preds':None},
            }
        else:
            # print("You got this!")
            # print(result_dict)
            res = result_dict[data['imgurl']]
            # print(res)
            # print(data['imgurl'])
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
                'lon':data['lon'],    
                'lat':data['lat'],
                'PHOTO_URL':data['imgurl'],
                'prob_Bare': res[0],
                'prob_Partly Snow Coverage': res[1],
                'prob_Undefined': res[2],
                'prob_Full Snow Coverage': res[3],
                'customdata': {'url':data['imgurl'],'preds':pred},
                'label':"AVL-"+inp,
                "RSI": getRSI(inp) #BUG
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

    dashcams = []
    # TODO: -v uncomment this for caching implementation
    # url = ("http://127.0.0.1:8080/snow_estimate")
    # data = {"img_urls": img_urls}
    # r = requests.post(url, json=data)
    # result_dict = (r.json())['result']

    filtered_data = []
    img_urls = []

    for i, data in tqdm(enumerate(results['data'])):

        rwis_row = rwis_stations[rwis_stations['cid'] == data['cid']].values
        if len(rwis_row) == 0:
            continue
        rwis_row = rwis_row[0]

        if filter:
            point = Point(rwis_row[1],rwis_row[0])  
            distances = (shapely.distance(point,both_highways.geometry) < 0.002)
            if (distances[0] or distances[1]) == False:
                continue
        filtered_data.append(data)
    
        for key in data.keys():
            if key.startswith('imgurl'):
                if data[key] is not None:
                    imgurl = data[key]
                    break
        img_urls.append(imgurl)

    data1 = {"img_urls": img_urls}
    # db_vals = rwis_disksave_bulk[img_urls]
    result_dict = {}
    for img_url in img_urls:
        result_dict[img_url] = None
    # r = requests.post(url, json=data1) 
    # result_dict = (r.json())['result']
    # estimate_ratios = result_dicte['estimate_ratio']
    # img_gen_masks = result_dicte['img_gen_masks']
    # img_src_masks = result_dicte['img_src_masks']
    # print(estimate_ratios)
    image_placeholder = "https://mesonet.agron.iastate.edu/archive/data/2023/05/25/camera/idot_trucks/A34681/A34681_202123305251928.jpg"
    for i, data in tqdm(enumerate(filtered_data)):
        rwis_row = rwis_stations[rwis_stations['cid'] == data['cid']].values
        if len(rwis_row) == 0:
            continue
        rwis_row = rwis_row[0]

        # TODO: conversion of estimate ratio to rsi ranges
        # bare: 0.8-1.0
        # part snow: 0.5-0.8
        # full: 0.2-0.5
        
        if result_dict[img_urls[i]]==None:
            
            category = "Waiting..."
            estimate_ratio = 0
            dashcam = {
                'stid': data['cid'],
                'lon':rwis_row[1],    
                'lat':rwis_row[0],
                'customdata':{'url':img_urls[i], 'preds':[image_placeholder, image_placeholder]}, #img_urls
                'RSC': category, # Predicted category
                "RSI": estimate_ratio, #BUG
                'label':"RWIS-"+category,
                "hovertext": data['cid'] + "<br>" + str(estimate_ratio) 
            }
            dashcams.append(dashcam)
            continue
            
        estimate_ratio = result_dict[img_urls[i]][0]
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
            'customdata':{'url':img_urls[i], 'preds':[result_dict[img_urls[i]][1], result_dict[img_urls[i]][1]]}, #img_urls
            'RSC': category, # Predicted category
            "RSI": estimate_ratio, #BUG
            'label':"RWIS-"+category,
            "hovertext": data['cid'] + "<br>" + str(estimate_ratio) 
        }
        dashcams.append(dashcam)
    return dashcams


def grab_RWIS_data(todo):
    rwis_stations = pd.read_csv('0_RWIS_GPS_data_mod.csv')

    dashcams = []
    # TODO: -v uncomment this for caching implementation
    # url = ("http://127.0.0.1:8080/snow_estimate")
    url = (f"{SERVER_IP}/snow_estimate")
    # data = {"img_urls": img_urls}
    # r = requests.post(url, json=data)
    # result_dict = (r.json())['result']

    filtered_data = []
    img_urls = []
    # url = ("http://127.0.0.1:8080/predictBatchesV2")
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

    data1 = {"img_urls": img_urls}

    r = requests.post(url, json=data1) 
    result_dict = (r.json())['result']
    # print(result_dict)
    # estimate_ratios = result_dicte['estimate_ratio']
    # img_gen_masks = result_dicte['img_gen_masks']
    # img_src_masks = result_dicte['img_src_masks']
    # print(estimate_ratios)
    # image_placeholder = "https://mesonet.agron.iastate.edu/archive/data/2023/05/25/camera/idot_trucks/A34681/A34681_202123305251928.jpg"
    for i, data in tqdm(enumerate(todo)):
        rwis_row = rwis_stations[rwis_stations['cid'] == data['cid']].values
        if len(rwis_row) == 0:
            continue
        rwis_row = rwis_row[0]

        # TODO: conversion of estimate ratio to rsi ranges
        # bare: 0.8-1.0
        # part snow: 0.5-0.8
        # full: 0.2-0.5
        estimate_ratio = result_dict[img_urls[i]][0]
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
            'customdata':{'url':img_urls[i], 'preds':[result_dict[img_urls[i]][1], result_dict[img_urls[i]][1]]}, #img_urls
            'RSC': category, # Predicted category
            'label':"RWIS-"+category,
            "RSI": estimate_ratio, #BUG
            "hovertext": data['cid'] + "<br>" + str(estimate_ratio),
            "old_label":data['cid'] + "<br>" + str(0),
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


    url = (f"{SERVER_IP}/predictBatches")
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
            'lon':data['lon'],    
            'lat':data['lat'],
            'PHOTO_URL':data['imgurl'],
            'prob_Bare': res[0],
            'prob_Partly Snow Coverage': res[1],
            'prob_Undefined': res[2],
            'prob_Full Snow Coverage': res[3],
            'customdata': {'url':data['imgurl'],'preds':pred},
            'label':"AVL-"+inp,
            "RSI": getRSI(inp) #BUG
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
            "RSI": getRSI(inp) #BUG
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