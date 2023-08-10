from google.cloud import aiplatform
from google.protobuf import json_format
from google.protobuf.struct_pb2 import Value

PROJECT = "817015833630"
LOCATION = "us-central1"

AVL_ENDPOINT_ID = "6332619627989827584"
API_ENDPOINT =  "us-central1-aiplatform.googleapis.com"

parameters_dict = {}
parameters = json_format.ParseDict(parameters_dict, Value())

client_options = {"api_endpoint": API_ENDPOINT}

client = aiplatform.gapic.PredictionServiceClient(client_options=client_options)
endpoint = client.endpoint_path(
        project=PROJECT, location=LOCATION, endpoint=AVL_ENDPOINT_ID
)


def predict(instances):
    global endpoint, parameters
    response = client.predict(
        endpoint=endpoint, instances=instances, parameters=parameters
    )
    result = []
    for prediction in response.predictions:
        result.append(dict(prediction))
    return result

# instance_dict = {"image_bytes": {"b64": "encoded_content"}, "key": "0"}
# print(instance_dict)
# gs://demorsi-a1501.appspot.com/public_images/abacus.jpg
# image = "gs://demorsi-a1501.appspot.com/public_images/abacus.jpg"
r = predict(
    instances=['gs://demorsi-a1501.appspot.com/public_images/A34712-2019-01-12_07_58_16.jpg', 'gs://demorsi-a1501.appspot.com/public_images/A32578-2019-01-12_07_24_05.jpg', 'gs://demorsi-a1501.appspot.com/public_images/A34383-2019-01-12_07_55_30.jpg', 'gs://demorsi-a1501.appspot.com/public_images/A34383-2019-01-12_07_55_30.jpg']
)


print(r)