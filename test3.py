import pandas as pd

df = pd.read_csv('0_RWIS_GPS_data_mod.csv')
d = df.to_dict('records')
station_id = 'IDOT-000'

stations = {}

for x in d:
    stations[x['cid']] = [x['Latitude'],x['Longitude (-W)']]

print(stations[station_id])
    # { 'cid': ['lat','lon']}