FROM ubuntu:latest
RUN apt-get update && apt-get install -y gnupg2
RUN apt update && \
apt-get install -y wget && \
echo "deb http://storage.googleapis.com/tensorflow-serving-apt stable tensorflow-model-server tensorflow-model-server-universal" | tee /etc/apt/sources.list.d/tensorflow-serving.list && \
wget https://storage.googleapis.com/tensorflow-serving-apt/tensorflow-serving.release.pub.gpg && apt-key add tensorflow-serving.release.pub.gpg && \
apt update && \
apt-get install tensorflow-model-server

COPY exporter /models/tf_models


CMD tensorflow_model_server --port=8500 --rest_api_port=${PORT} --model_base_path=/models/tf_models --model_name=avl_from_bytes_with_key