import pandas as pd

df = pd.read_csv("2_obtain_rsi_for_imgs.csv")

d = df.to_dict('records')
print(d)
for x in d:
    x['stid+RSI'] = x['img_path'][20:28]

1_rwis_imgs_masks\\IDOT-000