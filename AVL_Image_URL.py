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
    Grabs latest RWIS images based on window size
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
from tqdm import tqdm
def getLabel(result):
    labels =['Bare','Partly Snow Coverage','Undefined','Full Snow Coverage']
    return labels[result.index(max(result))]
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