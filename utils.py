import numpy as np
import pandas as pd
import copy
import math


def load_data(picked_date=''):
    # df = pd.read_csv("1_predicted_I35N_down_2019-01-12_07.csv")
    df = pd.read_csv('https://raw.githubusercontent.com/WMJason/demo-RSI/main/test'+picked_date+'.csv')
    df_rwis = pd.read_csv("https://raw.githubusercontent.com/WMJason/demo-RSI/main/RWIS_locs.csv")
    df_unknown = pd.read_csv('https://raw.githubusercontent.com/WMJason/demo-RSI/main/test_unknown.csv')
    df_rwis_all = pd.read_csv("https://raw.githubusercontent.com/WMJason/demo-RSI/main/2_obtain_rsi_for_imgs.csv")
    return df, df_rwis, df_unknown, df_rwis_all


from pyproj import Proj, transform


def ConvertProjtoDegree(pro_xs=[], pro_ys=[]):
    ###project coordinates into meters
    inProj = Proj(init='epsg:26915')  # NAD83 / UTM zone 15N
    outProj = Proj(init='epsg:4269')  # NAD83

    xs, ys = transform(inProj, outProj, pro_xs, pro_ys)
    return xs, ys


###from dash_bootstrap_mapbox_v3_rsi_semivariogram.py
# import skgstat as skg
# from skgstat import Variogram


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

    return dists[:10]


def ConstructSemi(df={}):
    ###project coordinates into meters
    inProj = Proj(init='epsg:4269')  # NAD83
    outProj = Proj(init='epsg:26915')  # NAD83 / UTM zone 15N

    xs = np.array(df['PHOTO_LONG'])
    ys = np.array(df['PHOTO_LATI'])
    pro_xs, pro_ys = transform(inProj, outProj, xs, ys)
    df['pro_X'] = pro_xs
    df['pro_Y'] = pro_ys
    values = df['RSI']

    xys = []
    for i in range(len(pro_xs)):
        xys.append([pro_xs[i], pro_ys[i]])

    dists = ObtainMaxDistance(xys)
    max_dist = dists[0]

    coordinates = np.array(xys)
    maxlag = max_dist / 2

    # V = Variogram_roadist.Variogram_roadist(coordinates=coordinates,
    #                                     values=values,
    #                                     use_nugget=True,
    #                                     model='spherical',
    #                                     estimator='matheron',
    #                                     bin_func='uniform',
    #                                     maxlag=maxlag)

    # V = Variogram(coordinates=coordinates,
    #               values=values,
    #               use_nugget=True,
    #               model='spherical',
    #               estimator='matheron',
    #               bin_func='uniform',
    #               maxlag=maxlag)

    #semi_infos = V.describe()
    #rnge = round(semi_infos['effective_range'] / 1000, 2)
    rnge = 60.99
    #psill = round(semi_infos['sill'], 2)
    psill = 0.02
    #nugget = round(semi_infos['nugget'], 2)
    nugget = 0.01
    #sill = round(semi_infos['sill'] + semi_infos['nugget'], 2)
    sill = 0.03
    #n_lags = V.n_lags
    n_lags = 10
    #dists = V.bins / 1000
    dists = [4.14540447, 8.21966244, 13.14269996, 18.55741696, 24.02338575, 30.49752274, 
             37.83630649, 45.28761025, 53.05467633, 60.99468264]
    #experiments = V.experimental
    experiments = [0.01293204, 0.01796298, 0.01750724, 0.02161075, 0.03031476, 0.02562167,
                   0.02634403, 0.0252123, 0.02833866, 0.03625549]

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


###calculate the weights
def CalWeights_norm(samples=[], unsampled=[], model='Sph', n=0, r=10, s=1):
    # Calculate G - between measured points
    Gs = []
    for sample in samples:
        G = []
        for sample2 in samples:
            semi = CalSemivariance(point1=sample, point2=sample2, model='Sph', n=n, r=r, s=s)
            cov = s - semi
            G.append(semi)
        G.append(1)
        Gs.append(G)
    Gs_last_row = [1 for sample in samples]
    Gs_last_row.append(0)
    Gs.append(Gs_last_row)

    # Calculate g (covariances) - between measured and unmeasured points
    gs = []
    for ea_unsample in unsampled:
        g = []
        for sample in samples:
            semi = CalSemivariance(point1=sample, point2=ea_unsample, model='Sph', n=n, r=r, s=s)
            cov = s - semi
            g.append(semi)
        g.append(1)
        gs.append(g)
    gs = np.array(gs)

    W = np.dot(np.linalg.inv(Gs), gs.transpose())

    # Calculate the estimation variance
    gs = []
    for ea_unsample in unsampled:
        g = []
        for sample in samples:
            semi = CalSemivariance(point1=sample, point2=ea_unsample, model='Sph', n=n, r=r, s=s)
            g.append(semi)
        g.append(1)
        gs.append(g)
    # print(gs)
    error = np.dot(gs, W)

    errors = []
    for i in range(len(unsampled)):
        errors.append(error[i, i])

    return W, errors


def OK(samples=[], unsampled=[], model='Sph', n=0, r=10, s=1):
    W, errors = CalWeights_norm(samples=samples, unsampled=unsampled, model=model, n=n, r=r, s=s)
    W = W.tolist()
    del W[-1]
    W = np.array(W)

    samples_vals = np.array([[sample[-1] for sample in samples]])

    estimates = np.dot(np.transpose(W), np.transpose(samples_vals))
    estimates = estimates.reshape(len(estimates), )

    return estimates, errors
