from typing import Dict, List, Union

from google.cloud import aiplatform
from google.protobuf import json_format
from google.protobuf.struct_pb2 import Value
import orjson
PROJECT = "817015833630"
LOCATION = "us-central1"

# aiplatform.init(
#     # your Google Cloud Project ID or number
#     # environment default used is not set
#     project='my-project',

#     # the Vertex AI region you will use
#     # defaults to us-central1
#     location='us-central1',

#     # Google Cloud Storage bucket in same region as location
#     # used to stage artifacts
#     # staging_bucket='gs://my_staging_bucket',
# )


def predict_custom_trained_model_sample(
    project: str,
    endpoint_id: str,
    instances: Union[Dict, List[Dict]],
    location: str = "us-central1",
    api_endpoint: str = "us-central1-aiplatform.googleapis.com",
):
    """
    `instances` can be either single instance of type dict or a list
    of instances.
    """
    # The AI Platform services require regional API endpoints.
    client_options = {"api_endpoint": api_endpoint}
    # Initialize client that will be used to create and send requests.
    # This client only needs to be created once, and can be reused for multiple requests.
    client = aiplatform.gapic.PredictionServiceClient(client_options=client_options)
    # The format of each instance should conform to the deployed model's prediction input schema.
    # instances = instances if isinstance(instances, list) else [instances]
    # instances = [
    #     json_format.ParseDict(instance_dict, Value()) for instance_dict in instances
    # ]
    endpoint = client.endpoint_path(
        project=PROJECT, location=LOCATION, endpoint='6332619627989827584'
    )
    end = aiplatform.Endpoint("6332619627989827584",PROJECT,LOCATION)
    parameters_dict = {}

    response = end.raw_predict(
        body=orjson.dumps({"instances": instances, "parameters": parameters_dict}),
        headers={"Content-Type": "application/json"},
    )
    print(response.content)
    # res = orjson.loads(response.content)['predictions']
    # parameters_dict = {}
    # parameters = json_format.ParseDict(parameters_dict, Value())
    # endpoint = client.endpoint_path(
    #     project=project, location=location, endpoint=endpoint_id
    # )
    # response = client.predict(
    #     endpoint=endpoint, instances=instances, parameters=parameters
    # )
    # print("response")
    # print(" deployed_model_id:", response.deployed_model_id)
    # The predictions are a google.protobuf.Value representation of the model's predictions.
    # predictions = response['predictions']
    # for prediction in predictions:
    #     print(" prediction:", (prediction))
    return res

# print(instance_dict)
# gs://demorsi-a1501.appspot.com/public_images/abacus.jpg
image = "gs://demorsi-a1501.appspot.com/public_images/A33304-2019-01-12_07_48_36.jpg"
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
# print(res.text)
predict_custom_trained_model_sample(
    project=PROJECT,    
    endpoint_id="6332619627989827584",
    location=LOCATION,
    instances=[instance_dict]*10
)
