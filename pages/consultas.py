import time
import json
from datetime import datetime
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import pandas as pd
from datetime import datetime
import streamlit as st

st.title(" Consulta de Estación 1.")

time_c = st.slider('Seleccciona las Horas de Consulta', 1, 24, 8)

#time_c=24
token = "VmIHuN_GB8AhmOchqnjtgrOL-oD2pHU-2ypKcswWbtM6aY1G2ylRYOJQpsqEANVl9iZ5PdAGqTsOJ30NPCtPUQ=="
org = "cmcorrea4@gmail.com"
bucket = "Elec_var"
client_Inf = InfluxDBClient(url="https://eu-central-1-1.aws.cloud2.influxdata.com", token=token,org=org,verify_ssl=False)

fields = ["Orden", "Proceso", "Estado"]
data = {field: [] for field in fields}
time_data = {field: [] for field in fields}

try:

 for field in fields:
    query = f'from(bucket: "{bucket}")|> range(start: -{time_c}h)|> filter(fn: (r) => r._field == "{field}" )'
    tables = client_Inf.query_api().query(query, org)
    for table in tables:
        for record in table.records:
            time_data[field].append(record.get_time())
            data[field].append(record.get_value())

 serie_time = pd.Series(time_data[field])
 serie_tim=pd.DatetimeIndex(pd.to_datetime(serie_time,unit='s')).tz_convert('America/Bogota')   #tz_convert('America/Bogota')
 index_time=serie_tim
 index_time_s=index_time.strftime('%Y-%m-%d %H:%M:%S')

 df_Orden = pd.DataFrame(data["Orden"], columns=["Orden"])
 df_Proceso = pd.DataFrame(data["Proceso"], columns=["Proceso"])
 df_Estado = pd.DataFrame(data["Estado"], columns=["Estado"])
 df_time_data = pd.DataFrame(index_time_s, columns=["Time_data"])


 df_consulta = pd.concat([df_Orden, df_Proceso, df_Estado, df_time_data], axis=1)
 st.dataframe(df_consulta)

 orden_seleccionado = st.selectbox('Selecciona una Orden:', df_consulta['Orden'].unique())

# Filtrar el DataFrame por el estado seleccionado
 filtered_df = df_consulta[df_consulta['Orden'] == orden_seleccionado]

 # Mostrar el DataFrame resultante cuando se presiona el botón
 if st.button('Consultar'):
     st.write("DataFrame filtrado:")
     st.write(filtered_df)
except:
 st.write(" No hay registros dentro del tiempo definido.")



