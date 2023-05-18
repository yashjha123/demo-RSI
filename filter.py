# will be transferred to utils.py

import fiona
import shapely
import shapely.geometry




with fiona.open("0_merged_I35_I80_pro_buffer20.shp") as fiona_collection:

    # In this case, we'll assume the shapefile only has one record/layer (e.g., the shapefile
    # is just for the borders of a single country, etc.).
    shapefile_record = fiona_collection.next()

    # Use Shapely to create the polygon
    shape = shapely.geometry.asShape( shapefile_record['geometry'] )

    # 41.7396,-93.7757
    point = shapely.geometry.Point(-94.7263, 41.4963) # longitude, latitude

    # Alternative: if point.within(shape)
    if shape.contains(point):
        print("Found shape for point.")

    print(list(shape.coords))