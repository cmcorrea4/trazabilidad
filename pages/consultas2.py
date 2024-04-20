import time
import json
from datetime import datetime
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import pandas as pd
from datetime import datetime


time_c=1
token = "VmIHuN_GB8AhmOchqnjtgrOL-oD2pHU-2ypKcswWbtM6aY1G2ylRYOJQpsqEANVl9iZ5PdAGqTsOJ30NPCtPUQ=="
org = "cmcorrea4@gmail.com"
bucket = "Elec_var"
client_Inf = InfluxDBClient(url="https://eu-central-1-1.aws.cloud2.influxdata.com", token=token,org=org,verify_ssl=False)

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

df_Orden = pd.DataFrame(data["Orden"], columns=["Orden"])
df_Proceso = pd.DataFrame(data["Proceso"], columns=["Proceso"])
df_Estado = pd.DataFrame(data["Estado"], columns=["Estado"])

df_consulta = pd.concat([df_Orden, df_Proceso, df_Estado], axis=1)
st.dataframe(df_consulta)


