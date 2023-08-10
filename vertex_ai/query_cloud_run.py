import requests
import orjson

headers = {
    'Content-Type': 'application/json',
}



# with open(image, "rb") as image_file:idot-047-00_202306071929.jpg (800×450)
#     encoded_string = base64.b64encode(image_file.read())
img = "https://cloud.iowadot.gov/Highway/Photos/Maintenance/MapSnapShots/SnowPlow/2019/1/12/A33304-2019-01-12_07_48_36.jpg"
import requests
import base64
# import tensorflow as tf
# img_bytes = tf.map_fn(
#     tf.io.read_file,
#     [image]
# )
res = requests.get(img)
from PIL import Image
from io import BytesIO
image = Image.open(BytesIO(res.content))
if image.mode != "RGB":
    image = image.convert("RGB")
image_height = 224
image_width = 224
channels = 3
# resize the input image and preprocess it
image = image.resize((image_height, image_width))
encoded_string = base64.b64encode(res.content)

buff = BytesIO()
image.save(buff, format="JPEG")
img_str = base64.b64encode(buff.getvalue())
# print(encoded_string)
# instance_dict = {"image_bytes": {"b64": encoded_string}, "key": "0"}
instance_dict = {
            "img_bytes": {"b64": (img_str).decode("utf-8")},"key": "0"
        }

instances = {
    "instances":[instance_dict],
    "parameters":{}
}

data = orjson.dumps(instances)
response = requests.post(
    'https://cloud-run-docker-xmctotgaqq-uc.a.run.app/v1/models/avl_from_bytes_with_key:predict',
    headers=headers,
    data=data,
)
print(response.content)