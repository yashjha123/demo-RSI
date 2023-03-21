#import numpy as np
#import pandas as pd
import random

# from PIL import Image, ImageOps
# from skimage.morphology import convex_hull_image
# from skimage import data, img_as_float
# from skimage.util import invert
# from skimage.color import rgb2gray
# from skimage.filters import threshold_sauvola
# import cv2
# import requests
# from io import BytesIO


# from tensorflow.keras.preprocessing.image import img_to_array, load_img


def ObtainAdjustedRSI(df={}):
    updated_df = df.drop(df[df.Predict == 'Undefined'].index)
    updated_df = updated_df.reset_index(drop=True)
    img_urls = updated_df['PHOTO_URL']
    predicts = updated_df['Predict']

    for i in range(len(img_urls)):
        if predicts[i] == 'Undefined':
            updated_df.at[i, 'RSI'] = None
        else:
            # ###load img from url
            # img_url = img_urls[i]
            # response = requests.get(img_url)
            # img = Image.open(BytesIO(response.content))
            #
            # ###crop img
            # box = (0.3 * img.width, 0.5 * img.height, 0.6 * img.width, 0.6 * img.height)  # (left, upper, right, lower)
            # area = img.crop(box)
            #
            # ###convert to BW
            # # read grayscale image
            # gray_image = ImageOps.grayscale(area)
            # gray_image = np.array(gray_image)
            # # convert to binary
            # (thresh, im_bw) = cv2.threshold(gray_image, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
            #
            # ###calculate binary proportion
            # tot_cells = len(np.where(im_bw == 255)[0]) + len(np.where(im_bw == 0)[0])
            # perc_white = len(np.where(im_bw == 255)[0]) / tot_cells
            # perc_black = len(np.where(im_bw == 0)[0]) / tot_cells

            if predicts[i] == 'Full Snow Coverage':
                updated_df.at[i, 'RSI'] = 0.35
            elif predicts[i] == 'Partly Snow Coverage':
                # updated_df.at[i, 'RSI'] = 0.8 - (0.8 - 0.5) * perc_white
                updated_df.at[i, 'RSI'] = 0.8 - (0.8 - 0.5) * random.random()
            elif predicts[i] == 'Bare':
                updated_df.at[i, 'RSI'] = 0.9

    return updated_df

##df = pd.read_csv('test.csv')
##df = ObtainAdjustedRSI(df=df)











