from google.cloud import firestore 
import datetime
from google.cloud.firestore_v1.base_query import FieldFilter, Or, And

db = firestore.Client(project="demorsi-a1501")
records_ref = db.collection_group("records")

def filter(docs,endTime):
    for doc in docs:
        data = doc.to_dict()
        print("WE HAVE SOME DATA",data)
        if data["end"] >= endTime:
            return True
    return False

def strip(datetime):
    return datetime.replace(hour=0, minute=0, second=0, microsecond=0)
import pytz
print(pytz.all_timezones)
window = 10 # minutes
tz = datetime.timezone(datetime.timedelta())
timestamp = datetime.datetime(year=2023, month=8, day=3, hour=4, minute=00,tzinfo=tz)
# pytz



def isArchived(timestamp,window):
    startTime = timestamp - datetime.timedelta(minutes=window)
    endTime = timestamp + datetime.timedelta(minutes=window)
    print(startTime,endTime)
    sig = datetime.timedelta(microseconds=1)
    std = strip(startTime)
    # std = startTime.date()
    etd = strip(endTime)
    print(std,etd)
    # tq = records_ref.where(filter=FieldFilter("Date", u"==", std)).stream()
    # for doc in tq:
    #     print(doc.to_dict())
    # return
    q1 = records_ref.where(filter=FieldFilter("start", "<=", startTime)).where(filter=FieldFilter("Date", "==", std)).stream()
    if etd == std:
        mockTime = endTime
        print(mockTime)
        return filter(q1,mockTime)
    else:
        mockTime = etd - sig
        print("2",mockTime)
        q2 = records_ref.where(filter=FieldFilter("start", "<=", endTime)).where(filter=FieldFilter("Date", "==", etd)).stream()
        return filter(q1,mockTime) and filter(q2,mockTime)
print(isArchived(timestamp,window))
# def avl_query(timestamp,date):

#     filter_1 = FieldFilter("start", "<=", timestamp)
#     filter_2 = FieldFilter("Date", "==", date)

#     # Create the union filter of the two filters (queries)
#     or_filter = And(filters=[filter_1, filter_2])

#     # query = records_ref.where(filter=FieldFilter("start", "<=", timestamp)).where(filter=FieldFilter("end", "<=", timestamp)).limit(1).get()
#     query = records_ref.where(filter=or_filter).get()
#     # col_ref.where(filter=or_filter).stream()
#     return query

# d = avl_query(timestamp,date)
# print(d)