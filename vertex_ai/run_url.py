from typing import Dict, List, Union

from google.cloud import aiplatform
from google.protobuf import json_format
from google.protobuf.struct_pb2 import Value

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
        project=project, location=location, endpoint=endpoint_id
    )
    end = aiplatform.Endpoint(endpoint,PROJECT,location=location)
    parameters_dict = {'signature_name':'from_bytes'}
    parameters = json_format.ParseDict(parameters_dict, Value())
    
    request = {
        'instances':instances,
        'parameters':parameters
    }
    # endpoint.predict()
    response = end.predict(
        instances=instances,
        parameters=parameters_dict,
        use_raw_predict=True
    )
    print("response")
    print(" deployed_model_id:", response.deployed_model_id)
    # The predictions are a google.protobuf.Value representation of the model's predictions.
    predictions = response.predictions
    for prediction in predictions:
        print(" prediction:", dict(prediction))


# instance_dict = {"image_bytes": {"b64": "encoded_content"}, "key": "0"}
# print(instance_dict)
image = ("https://cloud.iowadot.gov/Highway/Photos/Maintenance/MapSnapShots/SnowPlow/2019/1/12/A33304-2019-01-12_07_48_36.jpg")
predict_custom_trained_model_sample(
    project=PROJECT,
    endpoint_id="6332619627989827584",
    location=LOCATION,
    instances=[image]
)

