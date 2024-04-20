import time
import json
from datetime import datetime
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import pandas as pd
from datetime import datetime



fields = ["Orden", "Proceso", "Estado"]
data = {field: [] for field in fields}
time_data = {field: [] for field in fields}

for field in fields:
    query = f'from(bucket: "{bucket}")|> range(start: -{time_c}h)|> filter(fn: (r) => r._field == "{field}" )'
    tables = client_Inf.query_api().query(query, org)
    for table in tables:
        for record in table.records:
            time_data[field].append(record.get_time())
            data[field].append(record.get_value())

df_temp = pd.DataFrame(data["Orden"], columns=["Orden"])
df_hum = pd.DataFrame(data["Proceso"], columns=["Proceso"])
df_senst = pd.DataFrame(data["Estado"], columns=["Estado"])
