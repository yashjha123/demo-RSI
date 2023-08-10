from google.cloud import firestore 
import datetime
from google.cloud.firestore_v1.base_query import FieldFilter, Or, And
from dateutil.parser import parse

import shapely
from shapely.geometry import Polygon, LineString, Point

import requests

import geopandas as gpd

from multiprocessing.pool import Pool
from functools import partial
firebase_db = firestore.Client(project="demorsi-a1501")

# doc_ref = firebase_db.collection("avl")
# sub_avl_ref = doc_ref.document(date.strftime("%Y-%m-%d")).collection("Images")
# docs = sub_avl_ref.document(id).get()
avl_ref = firebase_db.collection_group("Images")
# id = "A33994_202308090209.jpg"
# date = parse("2023-08-09T06:40Z")
# sub_avl_ref = doc_ref.document(date.strftime("%Y-%m-%d")).collection("Images")
# docs = sub_avl_ref.document(id).get()
# docs = avl_ref.where(filter=FieldFilter(firestore.FieldPath.documentId(), "==", id)).get()
# print(docs.to_dict())
# quit()
both_highways = gpd.read_file("maps/0_merged_I35_I80_pro_buffer20.shp") # in-built CRS 'epsg:26915'
both_highways = (both_highways.to_crs('EPSG:4326'))

records_ref = firebase_db.collection_group("records")

BASE_URL = f'https://mesonet.agron.iastate.edu/'

def get_avl_from_iowa(window_size, time):
    """
    Grabs latest AVL images based on window size
    """
    # https://mesonet.agron.iastate.edu/api/1/idot_dashcam.json?window=15
    # 2023-02-07T14:31Z",
    URL = BASE_URL + 'api/1/idot_dashcam.json?window=' + str(window_size) + '&valid=' + time.strftime("%Y-%m-%dT%H:%M")
    # print(URL)
    response = requests.get(URL)
    data = response.json()
    status = response.status_code
    if status != 200:
        data = None

    return data['data']
main_avl_ref = firebase_db.collection("avl")
def check_points_in_firebase(point,in_firebase):
    # print("Checking",point)
    img_url = point["imgurl"]
    id = img_url.split('/')[-1]
    # print(point)
    date = parse(point['utc_valid'])

    pnt = Point(point["lon"],point["lat"])
    distances = (shapely.distance(pnt,both_highways.geometry) < 0.002)
    if (distances[0] or distances[1]) == False:
        # print("Ignored")
        # point outside both research area
        return None
    
    # docs = avl_ref.where_equals('id',id).get()
    # print(id)
    
    # sub_avl_ref = main_avl_ref.document(date.strftime("%Y-%m-%d")).collection("Images")
    # doc = sub_avl_ref.document(id).get()
    # docs = avl_ref.where(filter=FieldFilter("id", "==", id)).get()
    if id in in_firebase.keys():
        # points found in the db
        # print(doc.to_dict())
        # quit()
        # print("in firebase")
        return in_firebase[id]
    # points not found
    # print("Not in archive")
    return {
        "Position":firestore.GeoPoint(point["lat"],point["lon"]),
        "IMAGE_URL":img_url,
        "Date":parse(point["utc_valid"]),
        "archive": False
    }

def get_dates_from_firebase(maybe_unarchived_data):
    print(maybe_unarchived_data[0])
    startDate = parse(maybe_unarchived_data[0]['utc_valid'])
    endDate = parse(maybe_unarchived_data[-1]['utc_valid'])
    responses = {}
    while startDate < endDate:
        day_string = startDate.strftime("%Y-%m-%d")
        startDate += datetime.timedelta(days=1)
        docs = main_avl_ref.document(day_string).collection("Images").stream()
        ids = []
        for doc in docs:
            responses[(doc.id)] = doc.to_dict()
        # responses[day_string] = ids
    return responses
def merge_archive_and_new(date,window_size):
    maybe_unarchived_data = get_avl_from_iowa(window_size,date)
    in_firebase = get_dates_from_firebase(maybe_unarchived_data)
    with Pool(10) as pool:
        ret = list(filter(lambda x:x is not None, pool.map(partial(check_points_in_firebase,in_firebase=in_firebase),maybe_unarchived_data)))
    return ret

def isArchived(startTime,endTime):
    records = records_ref.where(filter=FieldFilter("start", "<=", startTime)).stream()
    for record in records:
        data = record.to_dict()
        if data['end'] >= endTime:
            return True
    return False

if __name__ == '__main__':

    date = parse("2023-08-09T06:40Z")
    windowsize = 1440
    startdate = date - datetime.timedelta(minutes=windowsize)
    enddate = date + datetime.timedelta(minutes=windowsize)
    ret = merge_archive_and_new(date,windowsize)
    print(ret)
    print(isArchived(startdate,enddate))
# def avl_query(timestamp,date):

#     filter_1 = FieldFilter("start", "<=", timestamp)
#     filter_2 = FieldFilter("Date", "==", date)

#     # Create the union filter of the two filters (queries)
#     or_filter = And(filters=[filter_1, filter_2])

#     # query = records_ref.where(filter=FieldFilter("start", "<=", timestamp)).where(filter=FieldFilter("end", "<=", timestamp)).limit(1).get()
#     query = records_ref.where(filter=or_filter).get()
#     # col_ref.where(filter=or_filter).stream()
#     return query

# d = avl_query(timestamp,date)
# print(d)