# import functions_framework
import requests

from functools import partial
# from flask import jsonify

from google.cloud import storage

from google.cloud import firestore
# from firebase_admin import storage
from firebase_admin import initialize_app
import concurrent.futures
import urllib3
import ssl

from multiprocessing.pool import Pool
from dateutil.parser import parse

from google.cloud import aiplatform
from google.protobuf import json_format
from google.protobuf.struct_pb2 import Value

import asyncio
import orjson
import base64
from PIL import Image
import aiohttp

import concurrent.futures

from io import BytesIO

initialize_app()

BUCKET = "demorsi-a1501.appspot.com"

PROJECT = "817015833630"
LOCATION = "us-central1"


API_ENDPOINT =  "us-central1-aiplatform.googleapis.com"
AVL_ENDPOINT_ID = "6332619627989827584"

parameters_dict = {}
parameters = json_format.ParseDict(parameters_dict, Value())

# client_options = {"api_endpoint": API_ENDPOINT}

# client = aiplatform.gapic.PredictionServiceClient(client_options=client_options)
# endpoint = client.endpoint_path(
#         project=PROJECT, location=LOCATION, endpoint=AVL_ENDPOINT_ID
# )


def predict(instances):
    end = aiplatform.Endpoint("6332619627989827584",PROJECT,LOCATION)

    response = end.raw_predict(
        body=orjson.dumps({"instances": instances, "parameters": {}}),
        headers={"Content-Type": "application/json"},
    )
    return orjson.loads(response.content)

def get_buff(res):
    image,img_url = res
    if image is None:
        return None
    image = image.resize((224, 224))
    buff = BytesIO()
    image.save(buff, format="JPEG")
    img_str = base64.b64encode(buff.getvalue())
    return {
            "img_bytes": {"b64": (img_str).decode("utf-8")}, "key": img_url
        }
    # return img_str
async def predictBV2(img_urls):
    MINI_BATCH = 128
    image_height = 224  # Define your image height
    image_width = 224  # Define your image width

    async def fetch_image(session, img_url):
        async with session.get(img_url) as response:
            image_data = await response.read()
        # try:
        image = Image.open(BytesIO(image_data))
        if image.mode != "RGB":
            image = image.convert("RGB")
        
        # except Exception as e:
            
        #     # Handle image processing error here
        #     image = None
        #     img_str = None
        print('fetched')
        return (image,img_url)
        # return None
        # return {img_str}

    async def process_batch(start, end):
        batch_urls = img_urls[start:end]
        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        ctx.options |= 0x4

        conn = aiohttp.TCPConnector(ssl=ctx)
        async with aiohttp.ClientSession(connector=conn) as session:
            tasks = [fetch_image(session, img_url) for img_url in batch_urls]
            batch_images = await asyncio.gather(*tasks)
        print(batch_images)
        with concurrent.futures.ThreadPoolExecutor() as executor:
            resized_images = list(executor.map(get_buff, batch_images))
        print(resized_images)
        response = predict(resized_images)

        results = {}
        for pred in response.get('predictions',[]):
            results[pred['key']] = pred['prediction']

        return results

    final_return = {}

    for start in range(0, len(img_urls), MINI_BATCH):
        end = start + MINI_BATCH
        batch_results = await process_batch(start, end)
        final_return.update(batch_results)

    return final_return



class CustomHttpAdapter (requests.adapters.HTTPAdapter):
    # "Transport adapter" that allows us to use custom ssl_context.

    def __init__(self, ssl_context=None, **kwargs):
        self.ssl_context = ssl_context
        super().__init__(**kwargs)

    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = urllib3.poolmanager.PoolManager(
            num_pools=connections, maxsize=maxsize,
            block=block, ssl_context=self.ssl_context)


def get_legacy_session():
    ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ctx.options |= 0x4  # OP_LEGACY_SERVER_CONNECT
    session = requests.session()
    session.mount('https://', CustomHttpAdapter(ctx))
    return session

# def upload_blob(bytes_io, dest_file_name,bucket):
#     """Uploads a file to the bucket."""
#     destination_blob_name = f"public_images/{dest_file_name}"

#     blob = bucket.blob(destination_blob_name)
#     # print(blob.path)
#     blob.upload_from_string(bytes_io,content_type='image/jpeg')
#     # blob.upload_from_filename(source_file_name, if_generation_match=generation_match_precondition)
#     blob.make_public()
#     # print(
#     #     f"File uploaded to {destination_blob_name}."
#     # )
#     return f'gs://{BUCKET}/{destination_blob_name}'

# def download_img(doc,bucket):
    # img_url = doc["image_url"]
    # response = get_legacy_session().get(img_url)
    # bytes_io = (response.content)
    # id = img_url.split('/')[-1]

    # blob_url = upload_blob(bytes_io,id,bucket)
    # # 'blob_url': blob_url,
    # #     'position': doc["position"],
    # #     'image_url': doc["image_url"]
    
    # return {
    #     'blob_url':blob_url,
    #     'position':doc["position"],
    #     'image_url':doc["image_url"],
    #     'date':doc['date']
    # }

# def predict(instances):
#     global endpoint, parameters
#     response = client.predict(
#         endpoint=endpoint, instances=instances, parameters=parameters
#     )
#     result = []
#     for prediction in response.predictions:
#         result.append(dict(prediction))
#     return result

def post_to_firebase(doc,avl_ref):
    preds = doc["pred"]
    bare = preds[0]
    partly = preds[1]
    undefined = preds[2]
    full = preds[3]

    date = parse(doc["date"])

    img_url = doc["image_url"]
    id = img_url.split('/')[-1]

    location = firestore.GeoPoint(doc["position"][0], doc["position"][1])
    collection_ref = avl_ref.document(date.strftime("%Y-%m-%d")).collection("Images")
    collection_ref.document(id).set({"IMAGE_URL": doc["image_url"], "Position": location,
                              "Bare": bare, "Partly": partly, 
                              "Undefined": undefined, "Full": full, "Date": date})
    return None

async def process(request):
    """HTTP Cloud Function.
    Args:
        request (flask.Request): The request object.
        <https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data>
    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`
        <https://flask.palletsprojects.com/en/1.1.x/api/#flask.make_response>.
    """
    request_json = request.get_json(silent=True)


    db = firestore.Client(project="demorsi-a1501")
    avl_ref = db.collection("avl")
    docs = request_json["input"]

    # bucket_client = storage.Client()
    # bucket = bucket_client.bucket(BUCKET)
    # map(img_urls,)
    preds = await predictBV2([doc['image_url'] for doc in docs])
    print(preds)
    # with Pool() as pool:
    #     blob_dicts = list(pool.map(partial(download_img,bucket=bucket),img_urls,chunksize=20))

    
    # bucket_imgs = [doc["blob_url"] for doc in blob_dicts]
    # bucket_imgs = list(pred_dict.keys())

    # preds = predict(bucket_imgs,bucket=bucket)
    pred_dict = {}

    for doc in docs:
        pred_dict[doc["image_url"]] = {
            "position":doc["position"],
            "image_url":doc["image_url"],
            'date':doc['date'],
            'pred':preds[doc["image_url"]]
        }
    # for pred in preds:
        # pred_dict[pred["filename"]]["pred"] = pred['prediction']
        # pred_dict[pred["filename"]]['prediction'] = pred['prediction']
        
    # with Pool() as pool:
    # blob_dicts = list(pool.map(post_to_firebase,list(pred_dict.values())))
    list(map(partial(post_to_firebase,avl_ref=avl_ref),list(pred_dict.values())))
    # print('Hello {}!'.format(pred_dict))
    return str(pred_dict), 200, {'Content-Type': 'application/json'}
    # return jsonify({"data":list(pred_dict.values())})
    # return 'Hello {}!'.format(pred_dict)

# @functions_framework.http
# def hello_http(request):
#     from asyncio import run
#     return run(process(request))
TEMPLATE ="https://cloud.iowadot.gov/Highway/Photos/Maintenance/MapSnapShots/SnowPlow/2019/1/12/A33304-2019-01-12_07_48_36.jpg"
res = asyncio.run(predictBV2([TEMPLATE]*500))
print(res)
# await 