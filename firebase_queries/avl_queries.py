from google.cloud import firestore 
import datetime
from google.cloud.firestore_v1.base_query import FieldFilter, Or
from google.cloud.firestore_v1.field_path import FieldPath

db = firestore.Client(project="demorsi-a1501")
avl_ref = db.collection_group("Images")


windowsize = 1
date = datetime.datetime(year=2022, month=12, day=24, hour=12, minute=30)

def avl_query(date):
    startdate = date - datetime.timedelta(hours=windowsize)
    enddate = date + datetime.timedelta(hours=windowsize)
    query = db.collection_group("Images").where(filter=FieldFilter("Date", ">=", startdate)).where(filter=FieldFilter("Date", "<=", enddate)).stream()
    return query
# museums = db.collection_group("landmarks").where(
#     filter=FieldFilter("type", "==", "museum")
# )


for doc in avl_query(date):
   # print((f"{doc.id} => {doc.to_dict()}"))
    data = doc.to_dict()
    print(data["Position"].longitude)