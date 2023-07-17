import datetime
from pytz import timezone
from dateutil.parser import parse
pick_date_time = "2023-07-15T09:23"
CENTRAL = timezone('US/Central')
UTC = timezone('UTC')
dt = datetime.datetime.now(CENTRAL)
last_time_triggered_central = CENTRAL.localize(parse(pick_date_time)).timestamp()
print(dt)
print(last_time_triggered_central)
# out = parse(pick_date_time).replace(tzinfo=CENTRAL)
# print(out)
# print(CENTRAL.localize(parse(pick_date_time)))
# print(CENTRAL.localize(parse(pick_date_time)).astimezone(UTC))
# # print(UTC.localize(out))
# out = out.astimezone(UTC)
# print(out)