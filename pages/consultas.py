import time
import json
from datetime import datetime, timedelta
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import pandas as pd
import streamlit as st

# Título y cabecera
st.title("Sistema de Gestión Avícola")
st.subheader("Consulta de Datos de Producción")

# Configuración de InfluxDB
token = "VmIHuN_GB8AhmOchqnjtgrOL-oD2pHU-2ypKcswWbtM6aY1G2ylRYOJQpsqEANVl9iZ5PdAGqTsOJ30NPCtPUQ=="
org = "cmcorrea4@gmail.com"
bucket = "Elec_var"
url = "https://eu-central-1-1.aws.cloud2.influxdata.com"

# Crear cliente de InfluxDB
client_Inf = InfluxDBClient(url=url, token=token, org=org, verify_ssl=False)

# Opciones de consulta
tiempo_consulta = st.slider('Selecciona el período de consulta (días)', 1, 90, 30)

# Modificamos para adaptarnos a la estructura existente
st.subheader("Consulta de Estación 1.")

# Botón para realizar la consulta
if st.button('Consultar Datos'):
    try:
        # Utilizamos el enfoque del código original, pero adaptado a los campos avícolas
        # Definimos los campos que queremos consultar
        fields = ["Lote", "Consumo_concentrado", "Mortalidad", "Total_huevos"]
        
        # Crear diccionarios para almacenar datos y tiempos
        data = {field: [] for field in fields}
        time_data = {field: [] for field in fields}
        
        # Consultar cada campo
        for field in fields:
            query = f'from(bucket: "{bucket}")|> range(start: -{tiempo_consulta}d)|> filter(fn: (r) => r._field == "{field}" )'
            tables = client_Inf.query_api().query(query, org)
            
            for table in tables:
                for record in table.records:
                    time_data[field].append(record.get_time())
                    data[field].append(record.get_value())
        
        # Verificar si se obtuvieron datos
        if all(len(data[field]) == 0 for field in fields):
            st.warning("No se encontraron datos para el período seleccionado.")
        else:
            # Procesamos los datos para cada campo que tenga información
            dataframes = []
            
            for field in fields:
                if len(data[field]) > 0:
                    # Convertir tiempos a zona horaria local
                    serie_time = pd.Series(time_data[field])
                    serie_tim = pd.DatetimeIndex(pd.to_datetime(serie_time, unit='ns')).tz_convert('America/Bogota')
                    index_time = serie_tim
                    index_time_s = index_time.strftime('%Y-%m-%d %H:%M:%S')
                    
                    # Crear DataFrame para este campo
                    df_field = pd.DataFrame(data[field], columns=[field])
                    df_time = pd.DataFrame(index_time_s, columns=["Time_data"])
                    
                    # Concatenar
                    df_combined = pd.concat([df_field, df_time], axis=1)
                    dataframes.append(df_combined)
            
            # Si tenemos al menos un DataFrame, mostramos los datos
            if dataframes:
                # Si tenemos más de un DataFrame, los juntamos
                if len(dataframes) > 1:
                    # Intentamos combinar los DataFrames que tienen la misma longitud
                    df_result = dataframes[0]
                    for i in range(1, len(dataframes)):
                        if len(dataframes[i]) == len(df_result):
                            df_result = pd.concat([df_result, dataframes[i].drop('Time_data', axis=1, errors='ignore')], axis=1)
                else:
                    df_result = dataframes[0]
                
                # Mostrar el DataFrame resultante
                st.dataframe(df_result)
                
                # Permitir seleccionar un lote (si existe la columna)
                if 'Lote' in df_result.columns and len(df_result['Lote'].dropna().unique()) > 0:
                    lote_seleccionado = st.selectbox('Selecciona un Lote:', df_result['Lote'].dropna().unique())
                    
                    # Filtrar por lote seleccionado
                    filtered_df = df_result[df_result['Lote'] == lote_seleccionado]
                    
                    # Mostrar resultados filtrados
                    if st.button('Filtrar por Lote'):
                        st.write("Datos filtrados por lote:")
                        st.dataframe(filtered_df)
                        
                        # Gráficos para datos numéricos
                        numerical_cols = filtered_df.select_dtypes(include=['number']).columns
                        
                        for col in numerical_cols:
                            if col != 'Lote' and len(filtered_df[col].dropna()) > 0:
                                # Crear DataFrame temporal para gráfico
                                df_chart = pd.DataFrame({
                                    'Fecha': pd.to_datetime(filtered_df['Time_data']),
                                    col: filtered_df[col]
                                })
                                df_chart = df_chart.set_index('Fecha')
                                
                                # Mostrar gráfico
                                st.subheader(f"Gráfico de {col}")
                                st.line_chart(df_chart)
                
                # Exportar a CSV
                csv = df_result.to_csv(index=False)
                st.download_button(
                    label="Descargar datos como CSV",
                    data=csv,
                    file_name=f"datos_avicolas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                )
            else:
                st.warning("No se pudieron procesar los datos obtenidos.")
    
    except Exception as e:
        st.error(f"Error al consultar datos: {str(e)}")
else:
    st.info("Presiona el botón 'Consultar Datos' para ver la información.")

# Añadir información adicional
st.markdown("---")
st.write("Esta aplicación consulta datos de producción avícola desde InfluxDB.")
