from google.cloud import storage
from firebase_admin import storage
from firebase_admin import initialize_app

initialize_app()
import requests
BUCKET = "demorsi-a1501.appspot.com"

SAMPLE = "https://cloud.iowadot.gov/Highway/Photos/Maintenance/MapSnapShots/SnowPlow/2019/1/12/A33304-2019-01-12_07_48_36.jpg"
# storage_client = storage.Client()
bucket = storage.bucket(BUCKET)

# bucket = storage_client.bucket(BUCKET)

def upload_blob(bytes_io, dest_file_name):
    """Uploads a file to the bucket."""
    destination_blob_name = f"public_images/{dest_file_name}"

    blob = bucket.blob(destination_blob_name)
    print(blob.path)
    blob.upload_from_string(bytes_io,content_type='image/jpeg')
    # blob.upload_from_filename(source_file_name, if_generation_match=generation_match_precondition)
    blob.make_public()
    print(
        f"File uploaded to {destination_blob_name}."
    )
    return f'gs://{BUCKET}/{destination_blob_name}'

def download_img(img_url):
    response = requests.get(img_url)
    bytes_io = (response.content)
    id = img_url.split('/')[-1]
    return upload_blob(bytes_io,id)


gs = list(map(download_img,[SAMPLE]))
print(gs)
# with Pool as pool:
#     pool.map()

# upload_blob(BUCKET,"abacuss.jpg","public_images/cheese.jpg")