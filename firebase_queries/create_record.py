from google.cloud import firestore 
import datetime
from google.cloud.firestore_v1.base_query import FieldFilter, Or, And

db = firestore.Client(project="demorsi-a1501")
records_ref = db.collection_group("records")

window = 9 # minutes
dt = datetime.timedelta(hours=window)
def strip(datetime):
    return datetime.replace(hour=0, minute=0, second=0, microsecond=0)

tz = datetime.timezone(datetime.timedelta())
timestamp = datetime.datetime(year=2023, month=8, day=3, hour=12, minute=00,tzinfo=tz)
# pytz

data = {"Date": strip(timestamp), "start": timestamp-dt, "end": timestamp+dt}

# Add a new doc in collection 'cities' with ID 'LA'
db.collection("records").document("LA").set(data)