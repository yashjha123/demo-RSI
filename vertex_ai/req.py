
imgs = ["http://cloud.iowadot.gov/Highway/Photos/Maintenance/MapSnapShots/SnowPlow/2019/1/12/A34712-2019-01-12_07_58_16.jpg",
"http://cloud.iowadot.gov/Highway/Photos/Maintenance/MapSnapShots/SnowPlow/2019/1/12/A32578-2019-01-12_07_24_05.jpg",
"http://cloud.iowadot.gov/Highway/Photos/Maintenance/MapSnapShots/SnowPlow/2019/1/12/A34383-2019-01-12_07_55_30.jpg",
"http://cloud.iowadot.gov/Highway/Photos/Maintenance/MapSnapShots/SnowPlow/2019/1/12/A34383-2019-01-12_07_55_30.jpg"]
import requests
sample = "https://cloud.iowadot.gov/Highway/Photos/Maintenance/MapSnapShots/SnowPlow/2019/1/12/A33304-2019-01-12_07_48_36.jpg"
r = requests.post('https://us-central1-demorsi-a1501.cloudfunctions.net/demo_api', json={"img_urls": imgs,})
print(r.text)

# import ssl