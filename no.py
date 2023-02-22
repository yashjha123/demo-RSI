import requests

url = ("http://127.0.0.1:8080/predictBatches")
data = {"img_urls": ["https://cloud.iowadot.gov/Highway/Photos/Maintenance/MapSnapShots/SnowPlow/2019/1/12/A34363-2019-01-12_07_01_17.jpg"]*30}

r = requests.post(url, json=data)

print(r.json())