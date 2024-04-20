import streamlit as st
from PIL import Image
from datetime import datetime

import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS

import time
import json
from datetime import datetime
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import pandas as pd
from datetime import datetime



st.title('Sierras Y Equipos')
st.subheader('Registro de Proceso, Estación 1.')

orden_t = st.selectbox(
    'Selecciona la Orden',
    ('1234', '4567', '8910'),key=1)


proceso = st.selectbox(
    'Selecciona el proceso',
    ('Proceso 1', 'Proceso 2', 'Proceso 3'),key=2)

estado=st.selectbox(
    'Selecciona el Estado',
    ('Recibido', 'En Proceso', 'Terminado'),key=3)



bucket = "Elec_var"
org = "cmcorrea4@gmail.com"
token = "VmIHuN_GB8AhmOchqnjtgrOL-oD2pHU-2ypKcswWbtM6aY1G2ylRYOJQpsqEANVl9iZ5PdAGqTsOJ30NPCtPUQ=="
# Store the URL of your InfluxDB instance
url="https://eu-central-1-1.aws.cloud2.influxdata.com"

if st.button('Registrar'):
   client = influxdb_client.InfluxDBClient(url=url,token=token,org=org)
   write_api = client.write_api(write_options=SYNCHRONOUS)
   p = influxdb_client.Point("Trazabilidad").tag("location", "Estación 1").field("Orden", orden_t)
   write_api.write(bucket=bucket, org=org, record=p)
   p = influxdb_client.Point("Trazabilidad").tag("location", "Estación 1").field("Proceso", proceso)
   write_api.write(bucket=bucket, org=org, record=p)
   p = influxdb_client.Point("Trazabilidad").tag("location", "Estación 1").field("Estado", estado)
   write_api.write(bucket=bucket, org=org, record=p)
  


