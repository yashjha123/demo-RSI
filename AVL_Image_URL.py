"""
An algorithm to automatically obtain AVL image urls to be used in a html-based webpage.
Code: Michael Urbiztondo
"""

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

def checkcache(results):
    img_urls = []
    for d in results['data']:
        img_urls.append(d['imgurl'])
    dashcams = []
    url = ("http://127.0.0.1:8080/loadFromCache")

    data = {"img_urls": img_urls}
    r = requests.post(url, json=data)
    result_dict = (r.json())['result']
    for data in results['data']:
        if result_dict[data['imgurl']] == "None":
            print("What happened?")
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

def checkrwiscache(results):
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
        # TODO: deal with completely null case (all imgurls null)
        # Not sure if we null data should be stored
    dashcams = []
    # TODO: -v uncomment this for caching implementation
    # url = ("http://127.0.0.1:8080/loadFromRWISCache")
    # data = {"img_urls": img_urls}
    # r = requests.post(url, json=data)
    # result_dict = (r.json())['result']
    for i, data in enumerate(results['data']):
        print(data)
        # TODO: Convert NWS ID to cid format (or vice versa), using github repo code 
        # - even better: add a column with all the respective cids or whatever into 0_RWIS_GPS_data.csv
        rwis_row = rwis_stations[rwis_stations['cid'] == data['cid']].values
        if len(rwis_row) == 0:
            continue
        rwis_row = rwis_row[0]
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
        dashcam = {
            'stid': data['cid'],
            'lon':rwis_row[1],    
            'lat':rwis_row[0],
            'img_path':img_urls[i],
            'RSC': 'Bare', # Predicted category
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
        print(result)
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


def grab_avl_data_v2(img_urls):
    """
    Processes JSON to grab AVL specific data
    Output: [{Name, Date, Lat, Long, Camera Url},...]
    """
    dashcams = []
    result_dict = {}


    url = ("http://127.0.0.1:8080/predictBatchesV2")
    # print(results['data'])
    print(img_urls)
    # BATCH_SIZE = 20
    # for i in tqdm(range(0,len(results))):
    #     img_urls = [x['imgurl'] for x in results['data'][i:i+BATCH_SIZE]]
    #     # print(img_urls)
    data = {"img_urls": img_urls}
    r = requests.post(url, json=data)
    result = (r.json())['result']
    print(result)
    # result_dict.update(result)

    # for data in tqdm(img_urls):
        
    #     # inp = random.choice(['Full Snow Coverage','Partly Snow Coverage','Bare'])
    #     # res = requests.get(AVL_RULE+data['imgurl']).json()["result"]
    #     res = result_dict[data['imgurl']]
    #     inp = getLabel(res)
    #     dashcam = {
    #         # 'name':data['cid'],
    #         # 'date':data['utc_valid'],
    #         'Predict': inp,
    #         'LABEL': inp,
    #         'x':data['lon'],    
    #         'y':data['lat'],
    #         'PHOTO_URL':data['imgurl'],
    #         'prob_Bare': res[0],
    #         'prob_Partly Snow Coverage': res[1],
    #         'prob_Undefined': res[2],
    #         'prob_Full Snow Coverage': res[3],
    #         "RSI": 0.4 #BUG
    #     }
    #     dashcams.append(dashcam)

    # return dashcams


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