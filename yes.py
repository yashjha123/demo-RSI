import pandas as pd
from AVL_Image_URL import get_cameras, grab_avl_data
from datetime import date



time = date.today().strftime("%Y-%m-%dT%H:%M")
d = grab_avl_data(get_cameras("50",time))
print(d)
p = pd.DataFrame(d)

print(p)

