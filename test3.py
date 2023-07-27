# import pandas as pd

# df = pd.read_csv("2_obtain_rsi_for_imgs.csv")

# d = df.to_dict('records')
# print(d)
# for x in d:
#     x['stid+RSI'] = x['img_path'][20:28]

# 1_rwis_imgs_masks\\IDOT-000
from pyproj import Proj
from pyproj import Transformer
lats = [41.516057]
longs = [-93.78049]

# outProj = Proj(init='epsg:26915')  # NAD83 / UTM zone 15N
# inProj = Proj(init='epsg:4269')  # NAD83

transformer = Transformer.from_crs("EPSG:4269","EPSG:26915")
xs,ys = transformer.transform([42,43],[-93,-92])
# xs, ys = transform(inProj, outProj, lats, longs )

print(xs,ys)
