from tensorflow.keras.preprocessing.image import img_to_array, load_img
from tensorflow.keras.models import Sequential
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Dropout, Flatten, Dense, Conv2D, MaxPooling2D
from PIL import Image
import tensorflow as tf
import numpy as np
import requests
import os
import datetime
import pickle
import time
import csv
from os import walk
from io import BytesIO


model = None
image_height = 224
image_width = 224
channels = 3

def load_model():
    # load the pre-trained Keras model (here we are using a model
    # pre-trained on ImageNet and provided by Keras, but you can
    # substitute in your own networks just as easily)
    global model
    #####Define the CNN architecture
    # Create structure of Convolutional Neural Network
    model = Sequential()

    model.add(Conv2D(16, kernel_size=(3, 3),
                     activation='relu',
                     input_shape=(image_height, image_width, channels)))
    #model.add(BatchNormalization())#
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Conv2D(32, (3, 3), activation='relu'))
    #model.add(BatchNormalization())#
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Conv2D(64, (3, 3), activation='relu'))
    #model.add(BatchNormalization())#
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Conv2D(128, (3, 3), activation='relu'))
    #model.add(BatchNormalization())#
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Conv2D(256, (3, 3), activation='relu'))
    #model.add(BatchNormalization())#
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Dropout(0.5))
    model.add(Flatten())
    model.add(Dense(1000, activation='relu'))
    #model.add(BatchNormalization())#
    model.add(Dropout(0.5))
    model.add(Dense(1000, activation='relu'))
    #model.add(BatchNormalization())#
    model.add(Dropout(0.5))
    model.add(Dense(4, activation='softmax'))

    model.load_weights('4_retrain_baseline_update_train9.h5')
    # model = tf.keras.models.load_model('./keras_model.h5')


def prepare_image(img_url):
    response = requests.get(img_url)
    image = Image.open(BytesIO(response.content))
    # if the image mode is not RGB, convert it
    if image.mode != "RGB":
        image = image.convert("RGB")

    # resize the input image and preprocess it
    image = image.resize((image_height, image_width))
    image = img_to_array(image) / 255
    image = np.expand_dims(image, axis=0)
    # return the processed image
    return image


def predict(img_urls):

    rsc_predicts = []
    for img_url in img_urls:
        re_image = prepare_image(img_url)
        preds = model.predict(re_image).tolist()[0]
        rsc_predicts.append(preds)
    return rsc_predicts
        

img_urls = ['http://cloud.iowadot.gov/Highway/Photos/Maintenance/MapSnapShots/SnowPlow/2019/1/12/A33976-2019-01-12_07_15_26.jpg',
            'http://cloud.iowadot.gov/Highway/Photos/Maintenance/MapSnapShots/SnowPlow/2019/1/12/A34003-2019-01-12_07_51_41.jpg',]

def main(img_urls=img_urls):
    load_model()
    rsc_predicts = predict(img_urls)
    return rsc_predicts

