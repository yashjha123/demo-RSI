import datetime
import requests
from dateutil.parser import parse
from tqdm import tqdm

from shapely.geometry import Polygon, LineString, Point
import shapely
import ast
# import shapely.distance


# TODO: Check if data exists in database already before writing (saves on daily entity read/write quota)

# IMAGE_URL = "https://mesonet.agron.iastate.edu/archive/data/2023/06/07/camera/IDOT-047-00/IDOT-047-00_202306071929.jpg"
IMAGE_URL = "http://cloud.iowadot.gov/Highway/Photos/Maintenance/MapSnapShots/SnowPlow/2019/1/12/A34363-2019-01-12_07_11_17.jpg"
id = IMAGE_URL.split('/')[-1]
BASE_URL = f'https://mesonet.agron.iastate.edu/'


def get_avl_cameras(window_size, time):
    """
    Grabs latest AVL images based on window size
    """
    # https://mesonet.agron.iastate.edu/api/1/idot_dashcam.json?window=15
    # 2023-02-07T14:31Z",
    URL = BASE_URL + 'api/1/idot_dashcam.json?window=' + window_size + '&valid=' + time
    # print(URL)
    response = requests.get(URL)
    data = response.json()
    status = response.status_code
    if status != 200:
        data = None

    return data
import geopandas as gpd
both_highways = gpd.read_file("../maps/0_merged_I35_I80_pro_buffer20.shp") # in-built CRS 'epsg:26915'
both_highways = (both_highways.to_crs('EPSG:4326'))

# january 2023 8th to 15th and 19th
# january 2020 19th 
import pandas as pd

# 10th January 2023
one_day = datetime.timedelta(days=1)
scrape_date = datetime.datetime.now() -  datetime.timedelta(days=91) -  datetime.timedelta(days=15)
avl_data = get_avl_cameras('400', scrape_date.strftime("%Y-%m-%dT%H:%M"))
import geopandas
df = pd.DataFrame(avl_data['data'])
print(df)

gdf = geopandas.GeoDataFrame(
    df, geometry=geopandas.points_from_xy(df.lon, df.lat), crs="EPSG:4326"
)
gdf = gdf.to_crs("EPSG:4326")
distance = gdf.geometry.distance(both_highways.geometry)
# print(gdf[0])
# print(shapely.distance(gdf.geometry,both_highways.geometry.shift()))

i80 = (both_highways.geometry[0])
i20 = (both_highways.geometry[1])
# quit()
one_year_ago = scrape_date - datetime.timedelta(days=365)
pbar = tqdm(total=365-91-15)
SERVER_URL = 'https://us-central1-demorsi-a1501.cloudfunctions.net/demo_api'

while scrape_date > one_year_ago:
    avl_data = get_avl_cameras('1440', scrape_date.strftime("%Y-%m-%dT%H:%M"))
    pbar.update(1)
    outputs = []
    i = 0
    df = pd.DataFrame(avl_data['data'])

    gdf = geopandas.GeoDataFrame(
    df, geometry=geopandas.points_from_xy(df.lon, df.lat), crs="EPSG:4326"
    )
    gdf = gdf.to_crs("EPSG:4326")
    distance = gdf.distance(i80) < 0.002
    distance2 = gdf.distance(i20) < 0.002
    # point = avl_data['data'][1]67
    # pnt = Point(point["lon"],point["lat"])
    # distances = (shapely.distance(pnt,both_highways.geometry[0]))
    # print(gdf[0])
    new_gdf = gdf[(distance | distance2)]
    # print(new_gdf)
    new_gdf['position'] = new_gdf[['lat','lon']].values.tolist()
    new_gdf = new_gdf[['imgurl','position','utc_valid']]
    new_gdf.columns = ['image_url','position','date']
    outputs = new_gdf.to_dict('records')
        # if i%256 == 255:
        #     r = requests.post(SERVER_URL, json={"input": outputs})
        #     outputs = []
        #     print(r.text)
        # break
    # print(outputs)
    for i in range(0,len(outputs),128*3):
        r = requests.post(SERVER_URL, json={"input": outputs[i*128*3:(i+1)*128*3]})
        print(r.text)
    # return_json = ast.literal_eval(r.text)
    # print(return_json)

    outputs = []
    # break
    # print(avl_data)

    # january 2022 8th to 15th
pbar.close()
