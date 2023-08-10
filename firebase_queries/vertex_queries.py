import requests

res = requests.get("https://us-central1-demorsi-a1501.cloudfunctions.net/avl_api",data={"img_urls":"img1.png"})
print(res.text)