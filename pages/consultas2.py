import time
import json
from datetime import datetime
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import pandas as pd
from datetime import datetime
import streamlit as st


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

serie_time = pd.Series(time_data)
serie_tim=pd.DatetimeIndex(pd.to_datetime(serie_time,unit='s')).tz_convert('America/Bogota')   #tz_convert('America/Bogota')
index_time=serie_tim
index_time_s=index_time.strftime('%Y-%m-%d %H:%M:%S')

df_Orden = pd.DataFrame(data["Orden"], columns=["Orden"])
df_Proceso = pd.DataFrame(data["Proceso"], columns=["Proceso"])
df_Estado = pd.DataFrame(data["Estado"], columns=["Estado"])

time_data = {'time_data': [time.time() + i for i in range(3)]}
df_time_data = pd.DataFrame(time_data, columns=["time_data"])
df_time_data["time_data"] = pd.to_datetime(df_time_data["time_data"], unit="s")

df_consulta = pd.concat([df_Orden, df_Proceso, df_Estado, df_time_data], axis=1)
st.dataframe(df_consulta)


