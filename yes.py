import pandas as pd
from AVL_Image_URL import get_cameras, grab_avl_data
from datetime import date
from random import sample



# time = date.today().strftime("%Y-%m-%dT%H:%M")
# d = (get_cameras("  ",time))
# data_list = list(d['data'])
# real_data = (sample(data_list,2000))
# f = pd.DataFrame(real_data)
# f.to_csv("data.csv")
# print((real_data))
# # p = pd.DataFrame(d)

# # print(len(p))

rsc_colors = {'Full Snow Coverage': 'white',
              'Partly Snow Coverage': 'grey',
              'Bare': 'black',
              'Undefined': '#FDDD0D',
              'Not labeled yet':'green'}

rsc_labels = ['Full Snow Coverage',
              'Partly Snow Coverage',
              'Bare',
              'Undefined']

df_rwis_all = pd.read_csv("https://raw.githubusercontent.com/WMJason/demo-RSI/main/2_obtain_rsi_for_imgs.csv") # prediction mask url + estimate ratio + classification
print(df_rwis_all['RSC'])

df_rwis_subs = []
for rsc_type in list(rsc_colors.keys()):
    to_append = df_rwis_all[df_rwis_all['RSC'] == rsc_type]
    if len(to_append) == 0:
        pass
    else:
        df_rwis_subs.append(to_append)

# print(df_rwis_subs)