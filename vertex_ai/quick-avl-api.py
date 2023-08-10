import urllib3
import ssl

import requests
from multiprocessing import Pool

from functools import partial
BUCKET = "demorsi-a1501.appspot.com"
def upload_blob(bytes_io, dest_file_name,bucket):
    """Uploads a file to the bucket."""
    destination_blob_name = f"public_images/{dest_file_name}"

    blob = bucket.blob(destination_blob_name)
    # print(blob.path)
    blob.upload_from_string(bytes_io,content_type='image/jpeg')
    # blob.upload_from_filename(source_file_name, if_generation_match=generation_match_precondition)
    # blob.make_public()
    # print(
    #     f"File uploaded to {destination_blob_name}."
    # )
    return f'gs://{BUCKET}/{destination_blob_name}'
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

from google.cloud import storage
bucket_client = storage.Client()


def download_img(doc):
    img_url = doc["image_url"]
    id = img_url.split('/')[-1]
    response = get_legacy_session().get(img_url)
    bytes_io = (response.content)
    

    return [doc,bytes_io]

def upload(bytes_and_docs,bucket):
    doc,bytes_io = bytes_and_docs
    img_url = doc["image_url"]
    id = img_url.split('/')[-1]
    blob_url = upload_blob(bytes_io,id,bucket)

    return {
        'blob_url':blob_url,
        'position':doc["position"],
        'image_url':doc["image_url"],
        'date':doc['date']
    }


img_urls= [{'image_url':'https://cloud.iowadot.gov/Highway/Photos/Maintenance/MapSnapShots/SnowPlow/2019/1/12/A33304-2019-01-12_07_48_36.jpg','date':'1','position':'123','blob_url':'1232'}]
with Pool() as pool:
    bytes_and_docs = list(map(partial(download_img),img_urls))


with bucket_client.batch():
    bucket = bucket_client.bucket(BUCKET)
    # for x in bytes_and_docs:
    #     upload(bucket=bucket,)
    list(map(partial(upload, bucket=bucket),bytes_and_docs))
