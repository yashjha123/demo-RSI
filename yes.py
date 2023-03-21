import pandas as pd
from AVL_Image_URL import get_cameras, grab_avl_data
from datetime import date
from random import sample



time = date.today().strftime("%Y-%m-%dT%H:%M")
d = (get_cameras("  ",time))
data_list = list(d['data'])
real_data = (sample(data_list,2000))
f = pd.DataFrame(real_data)
f.to_csv("data.csv")
print((real_data))
# p = pd.DataFrame(d)

# print(len(p))

