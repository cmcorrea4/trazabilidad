import streamlit as st
from PIL import Image
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS
import time
import json
from datetime import datetime
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import pandas as pd
from datetime import datetime
import pytz
def consulta_(option):
   
   time_c=1
   token = "VmIHuN_GB8AhmOchqnjtgrOL-oD2pHU-2ypKcswWbtM6aY1G2ylRYOJQpsqEANVl9iZ5PdAGqTsOJ30NPCtPUQ=="
   org = "cmcorrea4@gmail.com"
   bucket = "Elec_var"
   client_Inf = InfluxDBClient(url="https://eu-central-1-1.aws.cloud2.influxdata.com", token=token,org=org,verify_ssl=False)
   query = 'from(bucket: "Elec_var")|> range(start: -'+str(time_c)+'h)|> filter(fn: (r) => r._field =="'+var1+'")'


   table = client_Inf.query_api().query(query, org)

   var_s =[]
   time_s_ =[]
   for table_ in table:
      for record in table_.records:
          time_s_.append(record.get_time())
          var_s.append(record.get_value())

   serie_time = pd.Series(time_s_)
   #serie_tim=pd.DatetimeIndex(pd.to_datetime(serie_time,unit='s')).pytz.timezone('America/Bogota')   #tz_convert('America/Bogota')
   #index_time=serie_tim
                  #cr_date = datetime.datetime.strptime(cr_date, '%Y-%m-%d %H:%M:%S')
   st.write(serie_time)
   st.write(var_s)
   
   #index_time_s=index_time.strptime('%Y-%m-%d %H:%M:%S')        
 
   #var_serie = pd.Series(var_s,index_time)
                                               #var_serie=var_serie.to_period('S')
   #var_serie.describe()
   #var=var_serie.reset_index(level=0)
                                             #var.rename(columns = {'index':'Date', '0':prod}, inplace = True)
   #var.columns=['Fecha','Orden']
   #st.write(var)
   

st.subheader ('Consulta de Productos')   

var1 = st.radio(
    "Selecciona orden",
    ('1234', '4567','8910','Orden'))


if st.button('Consulta'):
    consulta_(var1)
else:
    st.write('')



