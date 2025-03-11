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
st.subheader("Consulta de Estación 1.")
tiempo_consulta = st.slider('Selecciona las Horas de Consulta', 1, 24, 8)

# Campos a consultar
campos = ["Lote", "Consumo_concentrado", "Mortalidad", "Total_huevos"]

# Botón para realizar la consulta
if st.button('Consultar Datos'):
    # Crear diccionarios para almacenar datos y tiempos
    data = {campo: [] for campo in campos}
    time_data = {campo: [] for campo in campos}
    
    try:
        # Consultar cada campo
        for campo in campos:
            query = f'from(bucket: "{bucket}")|> range(start: -{tiempo_consulta}h)|> filter(fn: (r) => r._field == "{campo}" )'
            tables = client_Inf.query_api().query(query, org)
            
            for table in tables:
                for record in table.records:
                    time_data[campo].append(record.get_time())
                    data[campo].append(record.get_value())
        
        # Verificar si hay datos
        if all(len(data[campo]) == 0 for campo in campos):
            st.warning("No se encontraron datos para el período seleccionado.")
        else:
            # Procesar los datos de tiempo (usando el primer campo que tenga datos)
            primer_campo_con_datos = next((campo for campo in campos if len(time_data[campo]) > 0), None)
            
            if primer_campo_con_datos:
                # Convertir tiempos a zona horaria local
                serie_time = pd.Series(time_data[primer_campo_con_datos])
                serie_tim = pd.DatetimeIndex(pd.to_datetime(serie_time, unit='ns')).tz_convert('America/Bogota')
                index_time = serie_tim
                index_time_s = index_time.strftime('%Y-%m-%d %H:%M:%S')
                
                # Crear DataFrames para cada campo
                dataframes = []
                for campo in campos:
                    if len(data[campo]) > 0:
                        # Solo usar los datos hasta la longitud del tiempo
                        longitud_max = min(len(data[campo]), len(index_time_s))
                        df_campo = pd.DataFrame(data[campo][:longitud_max], columns=[campo])
                        dataframes.append(df_campo)
                
                # Crear DataFrame de tiempo
                df_time_data = pd.DataFrame(index_time_s[:longitud_max], columns=["Time_data"])
                dataframes.append(df_time_data)
                
                # Concatenar todos los DataFrames
                df_consulta = pd.concat(dataframes, axis=1)
                
                # Mostrar el DataFrame resultante
                st.subheader("Resultados de la consulta")
                st.dataframe(df_consulta)
                
                # Permitir seleccionar un lote (si hay datos de lote)
                if 'Lote' in df_consulta.columns and not df_consulta['Lote'].empty:
                    # Obtener lotes únicos
                    lotes_unicos = df_consulta['Lote'].dropna().unique()
                    
                    if len(lotes_unicos) > 0:
                        lote_seleccionado = st.selectbox('Selecciona un Lote:', lotes_unicos)
                        
                        # Filtrar por lote seleccionado
                        filtered_df = df_consulta[df_consulta['Lote'] == lote_seleccionado]
                        
                        st.subheader(f"Datos del lote: {lote_seleccionado}")
                        st.dataframe(filtered_df)
                        
                        # Crear gráficos para datos numéricos
                        # 1. Preparar datos para visualización
                        if 'Time_data' in filtered_df.columns:
                            # Convertir a formato datetime
                            filtered_df['Fecha'] = pd.to_datetime(filtered_df['Time_data'])
                            
                            # Gráfico de Consumo
                            if 'Consumo_concentrado' in filtered_df.columns and len(filtered_df['Consumo_concentrado']) > 0:
                                st.subheader("Consumo de Concentrado")
                                chart_data = pd.DataFrame({
                                    'Consumo': filtered_df['Consumo_concentrado'].values
                                }, index=filtered_df['Fecha'])
                                st.line_chart(chart_data)
                            
                            # Gráfico de Mortalidad
                            if 'Mortalidad' in filtered_df.columns and len(filtered_df['Mortalidad']) > 0:
                                st.subheader("Mortalidad")
                                chart_data = pd.DataFrame({
                                    'Mortalidad': filtered_df['Mortalidad'].values
                                }, index=filtered_df['Fecha'])
                                st.line_chart(chart_data)
                            
                            # Gráfico de Total Huevos
                            if 'Total_huevos' in filtered_df.columns and len(filtered_df['Total_huevos']) > 0:
                                st.subheader("Total de Huevos")
                                chart_data = pd.DataFrame({
                                    'Total Huevos': filtered_df['Total_huevos'].values
                                }, index=filtered_df['Fecha'])
                                st.line_chart(chart_data)
                
                # Exportar a CSV
                csv = df_consulta.to_csv(index=False)
                st.download_button(
                    label="Descargar datos como CSV",
                    data=csv,
                    file_name=f"datos_avicolas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                )
            else:
                st.warning("No se pudieron procesar los datos de tiempo.")
    
    except Exception as e:
        st.error(f"Error al consultar datos: {str(e)}")
else:
    st.info("Presiona el botón 'Consultar Datos' para ver la información.")

# Añadir información adicional
st.markdown("---")
st.write("Esta aplicación consulta datos de producción avícola desde InfluxDB.")
