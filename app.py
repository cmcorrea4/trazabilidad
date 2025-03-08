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

# Configuración de la página
st.set_page_config(page_title="Sistema de Gestión Avícola", layout="wide")

# Título y cabecera
st.title('Sistema de Gestión Avícola')
st.subheader('Registro de Datos de Producción')

# Crear columnas para organizar mejor el formulario
col1, col2 = st.columns(2)

# Primera columna - Datos básicos
with col1:
    # Información del lote
    st.subheader("Información del Lote")
    lote = st.text_input('Lote', key='lote')
    fecha = st.date_input('Fecha', value=datetime.now(), key='fecha')
    
    # Datos de consumo y mortalidad
    st.subheader("Datos de Consumo y Población")
    consumo_concentrado = st.number_input('Consumo de concentrado diario (kg)', min_value=0.0, step=0.1, key='consumo_concentrado')
    mortalidad = st.number_input('Mortalidad (en Aves)', min_value=0, step=1, key='mortalidad')
    aves_descartadas_seleccion = st.number_input('Aves descartadas por selección', min_value=0, step=1, key='aves_descartadas_seleccion')
    aves_descartadas_venta = st.number_input('Aves descartadas por venta', min_value=0, step=1, key='aves_descartadas_venta')
    retiro_aves = st.number_input('Retiro aves', min_value=0, step=1, key='retiro_aves')

# Segunda columna - Producción de huevos
with col2:
    st.subheader("Producción de Huevos")
    huevos_yumbo = st.number_input('Huevos Yumbo', min_value=0, step=1, key='huevos_yumbo')
    huevos_extra = st.number_input('Huevos Extra', min_value=0, step=1, key='huevos_extra')
    huevos_aa = st.number_input('Huevos AA', min_value=0, step=1, key='huevos_aa')
    huevos_a = st.number_input('Huevos A', min_value=0, step=1, key='huevos_a')
    huevos_b = st.number_input('Huevos B', min_value=0, step=1, key='huevos_b')
    huevos_c = st.number_input('Huevos C', min_value=0, step=1, key='huevos_c')
    huevos_pipo = st.number_input('Huevos Pipo', min_value=0, step=1, key='huevos_pipo')
    huevos_sucios = st.number_input('Huevos Sucios', min_value=0, step=1, key='huevos_sucios')
    huevos_toteados = st.number_input('Huevos toteados', min_value=0, step=1, key='huevos_toteados')
    yemas = st.number_input('Yemas', min_value=0, step=1, key='yemas')

# Cálculos automáticos (debajo de ambas columnas)
st.subheader("Cálculos Automáticos")
col3, col4 = st.columns(2)

with col3:
    # Cálculo del total de huevos
    total_huevos = (huevos_yumbo + huevos_extra + huevos_aa + huevos_a + 
                   huevos_b + huevos_c + huevos_pipo + huevos_sucios + 
                   huevos_toteados + yemas)
    st.metric("Total Huevos", total_huevos)

with col4:
    # Para el consumo por ave necesitamos el número total de aves
    # Para este ejemplo, asumimos que hay un campo con el total de aves iniciales
    # que debería agregarse al formulario
    total_aves_iniciales = st.number_input('Total de Aves Iniciales', min_value=0, step=1, key='total_aves_iniciales')
    aves_actuales = total_aves_iniciales - mortalidad - aves_descartadas_seleccion - aves_descartadas_venta - retiro_aves
    
    if aves_actuales > 0:
        consumo_por_ave = consumo_concentrado / aves_actuales
        st.metric("Consumo por Ave (kg)", round(consumo_por_ave, 3))
    else:
        st.warning("No hay aves activas para calcular el consumo por ave")

# Campo para observaciones
st.subheader("Observaciones")
observaciones = st.text_area('Observaciones', height=100, key='observaciones')

# Configuración de InfluxDB
bucket = "Elec_var"
org = "cmcorrea4@gmail.com"
token = "VmIHuN_GB8AhmOchqnjtgrOL-oD2pHU-2ypKcswWbtM6aY1G2ylRYOJQpsqEANVl9iZ5PdAGqTsOJ30NPCtPUQ=="
url = "https://eu-central-1-1.aws.cloud2.influxdata.com"

# Botón para registrar datos
if st.button('Registrar Datos'):
    # Crear conexión con InfluxDB
    client = influxdb_client.InfluxDBClient(url=url, token=token, org=org)
    write_api = client.write_api(write_options=SYNCHRONOUS)
    
    # Crear un punto de tiempo para todos los datos
    timestamp = datetime.combine(fecha, datetime.now().time())
    
    # Crear puntos para cada dato
    datos = {
        "Lote": lote,
        "Consumo_concentrado": float(consumo_concentrado),
        "Mortalidad": int(mortalidad),
        "Aves_descartadas_seleccion": int(aves_descartadas_seleccion),
        "Aves_descartadas_venta": int(aves_descartadas_venta),
        "Huevos_yumbo": int(huevos_yumbo),
        "Huevos_extra": int(huevos_extra),
        "Huevos_aa": int(huevos_aa),
        "Huevos_a": int(huevos_a),
        "Huevos_b": int(huevos_b),
        "Huevos_c": int(huevos_c),
        "Huevos_pipo": int(huevos_pipo),
        "Huevos_sucios": int(huevos_sucios),
        "Huevos_toteados": int(huevos_toteados),
        "Yemas": int(yemas),
        "Observaciones": observaciones,
        "Consumo_por_ave": float(consumo_por_ave) if aves_actuales > 0 else 0,
        "Total_huevos": int(total_huevos),
        "Retiro_aves": int(retiro_aves)
    }
    
    # Crear un punto con todos los campos
    punto = influxdb_client.Point("Produccion_Avicola").tag("lote", lote)
    
    # Agregar todos los campos al punto
    for campo, valor in datos.items():
        punto.field(campo, valor)
    
    # Escribir en la base de datos
    write_api.write(bucket=bucket, org=org, record=punto)
    
    st.success(f"Datos del lote {lote} registrados correctamente en la fecha {fecha}")
    
    # Opcional: Mostrar los datos registrados
    st.subheader("Resumen de datos registrados:")
    st.json(datos)
