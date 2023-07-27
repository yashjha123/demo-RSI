import numpy as np
import pandas as pd
import copy
import math

import pandas as pd
from AVL_Image_URL import get_cameras, grab_avl_data, checkcache, get_rwis_cameras, checkrwiscache

from datetime import date
import datetime
from datetime import timedelta

def load_data(picked_date_time, window=360, placeholder = False):
    # df = pd.read_csv("1_predicted_I35N_down_2019  -01-12_07.csv")
    # df = pd.read_csv('https://raw.githubusercontent.com/WMJason/demo-RSI/main/test'+picked_date+'.csv')
    if placeholder:
        df = pd.read_csv('placeholder.csv')
        df_rwis_all = pd.read_csv("placeholder2.csv") # prediction mask url + estimate ratio + classification
        
    else:
        time = (picked_date_time).strftime("%Y-%m-%dT%H:%M")
        avl_data = checkcache(get_cameras(str(window),time))
        all = checkrwiscache(get_rwis_cameras(str(window),time))
        # print(d)
        # print(avl_data)
        df = pd.DataFrame(avl_data)
        df_rwis_all = pd.DataFrame(all)
        # df.to_csv("placeholder.csv")
        # df_rwis_all.to_csv("placeholder2.csv")
        # template/preset data for initial demorsi - remove/replace when RWIS is automated
    df_rwis = pd.read_csv("https://raw.githubusercontent.com/WMJason/demo-RSI/main/RWIS_locs.csv") # ask whats going on here...
    df_unknown = pd.read_csv('https://raw.githubusercontent.com/WMJason/demo-RSI/main/test_unknown.csv') # unknown RWIS data (location, time, for interpolation)
    # df_rwis_all = pd.read_csv("https://raw.githubusercontent.com/WMJason/demo-RSI/main/2_obtain_rsi_for_imgs.csv") # prediction mask url + estimate ratio + classification
    return df, df_rwis, df_unknown, df_rwis_all



from pyproj import Proj, transform
from pyproj import Transformer


def ConvertProjtoDegree(pro_xs=[], pro_ys=[]):
    ###project coordinates into meters
    print(pro_xs)
    print(pro_ys)
    inProj = Proj(init='epsg:26915')  # NAD83 / UTM zone 15N
    outProj = Proj(init='epsg:4269')  # NAD83

    
    xs, ys = transform(inProj, outProj, pro_xs, pro_ys )
    print(xs,ys)
    return xs, ys

def ConvertDegreetoProj(lats=[], longs=[]):
    ###project coordinates into meters
    print("VALUESSS ARE NICE",lats,longs)
    # outProj = Proj(init='epsg:26915')  # NAD83 / UTM zone 15N
    # inProj = Proj(init='epsg:4269')  # NAD83

    xs,ys = Transformer.from_crs("EPSG:4269","EPSG:26915").transform(lats,longs)
    # xs, ys = transform(inProj, outProj, lats, longs )
    print(xs,ys)
    return xs, ys


###from dash_bootstrap_mapbox_v3_rsi_semivariogram.py
import skgstat as skg
from skgstat import Variogram


###Semivariogram####
def Eudist(xy1, xy2):
    diff = 0
    for i in range(len(xy1)):
        diff += ((xy1[i] - xy2[i]) ** 2)

    dist = diff ** 0.5
    return dist


def ObtainMaxDistance(xys):
    dists = []
    cxys = copy.deepcopy(xys)
    for xy in xys:
        cxys.remove(xy)
        for cxy in cxys:
            dist = Eudist(xy, cxy)
            dists.append(dist)
    dists.sort(reverse=True)
    print("DESTINATIONS",dists[:10])
    return dists[:10]


def ConstructSemi(df={}):
    if df.empty:
        return [0.01,60.99,0.03, 279498.4527227931/1000,10,[],[]]
    ###project coordinates into meters
    a = datetime.datetime.now()

    inProj = Proj(init='epsg:4269')  # NAD83
    outProj = Proj(init='epsg:26915')  # NAD83 / UTM zone 15N

    xs = np.array(df['lon'])
    ys = np.array(df['lat'])
    b = datetime.datetime.now()
    print("FIRST",b-a)
    pro_xs, pro_ys = transform(inProj, outProj, xs, ys)
    c = datetime.datetime.now()
    print("SECOND",c-b)

    # print(pro_xs,pro_ys)
    df['pro_X'] = pro_xs
    df['pro_Y'] = pro_ys
    values = df['RSI']
    values[-1] -= 0.001
    xys = []
    print("FORO")
    xys = list(zip(pro_xs,pro_ys))
    print(xys)
    # for i in range(len(pro_xs)):
        # xys.append([pro_xs[i], pro_ys[i]])
    # d = print("THIRD",)

    dists = ObtainMaxDistance(xys)
    max_dist = dists[0]

    coordinates = np.array(xys)
    maxlag = max_dist / 2

    e = datetime.datetime.now()
    V = Variogram(coordinates=coordinates,
                  values=values,
                  use_nugget=True,
                  model='spherical',
                  estimator='matheron',
                  bin_func='uniform',
                  maxlag=maxlag)

    semi_infos = V.describe()
    print(semi_infos)
    rnge = round(semi_infos['effective_range'] / 1000, 2)
    # rnge = 60.99
    psill = round(semi_infos['sill'], 2)
    # psill = 0.02
    nugget = round(semi_infos['nugget'], 2)
    # nugget = 0.01
    sill = round(semi_infos['sill'] + semi_infos['nugget'], 2)
    # sill = 0.03
    n_lags = V.n_lags
    # n_lags = 10
    dists = V.bins / 1000
    # placeholder_dists = []
    experiments = V.experimental
    # placeholder_experiments = []

    
    return nugget, rnge, sill, maxlag / 1000, n_lags, dists, experiments


###from dash_bootstrap_mapbox_v3_rsi_interpolation.py
def isNum(h=''):
    try:
        h = h + 1
    except TypeError:
        return False
    else:
        return True


def CalSemivariance(point1=[], point2=[], h='', n=0, r=10, s=1,
                    model='Sph'):  # h - distance ; n - nugget; r - range; ps - partial sill
    #print(point1)
    #print(point2)
    if isNum(h=h):
        pass
    else:
        h = EuDistance(point1[0], point1[1], point2[0], point2[1])

    if model == 'Sph':

        if h == 0:
            semivariance = 0
        elif h > r:
            semivariance = n + s - n
        elif 0 < h <= r:
            semivariance = n + (s - n) * (1.5 * (h / r) - 0.5 * (h ** 3 / r ** 3))

        return semivariance

    elif model == 'Gau':

        if h > 0:
            semivariance = n + (s - n) * (1 - math.exp(-(h ** 2 / r ** 2)))

        elif h == 0:
            semivariance = 0

        return semivariance


    elif model == 'Exp':

        if h > 0:
            semivariance = n + (s - n) * (1 - math.exp(-h / r))

        elif h == 0:
            semivariance = 0

        return semivariance


def EuDistance(x1, y1, x2, y2):
    dist = ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5
    return dist


import pykrige.kriging_tools as kt
from pykrige.ok import OrdinaryKriging

def OK(samples=[], unsampled=[], model='Sph', n=0, r=10, s=1):
    embed = {
        "Sph":"spherical",
        "Gau":"gaussian",
        "Exp":"exponential"
    }
    samples = np.array(samples)
    unsampled = np.array(unsampled)
    myKriging = OrdinaryKriging(
        samples[:, 0],
        samples[:, 1],
        samples[:, 2],
        variogram_model=embed[model],
        verbose=True,
        variogram_parameters={'sill': s, 'range': r, 'nugget': n},
        enable_plotting=False,
    )
    estimates, ss  = myKriging.execute(style="points",xpoints=unsampled[:,0],ypoints=unsampled[:,1])
    # W, errors = CalWeights_norm(samples=samples, unsampled=unsampled, model=model, n=n, r=r, s=s)
    # W = W.tolist()
    # del W[-1]
    # W = np.array(W)

    # samples_vals = np.array([[sample[-1] for sample in samples]])

    # estimates = np.dot(np.transpose(W), np.transpose(samples_vals))
    # estimates = estimates.reshape(len(estimates), )
    errors = None
    return estimates, errors
