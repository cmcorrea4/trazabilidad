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
        fields = ["Lote", "Consumo_concentrado", "Mortalidad", "Total_huevos", 
                "Huevos_yumbo", "Huevos_extra", "Huevos_aa", "Huevos_a", 
                "Huevos_b", "Huevos_c", "Huevos_pipo", "Huevos_sucios", 
                "Huevos_toteados", "Yemas", "Aves_descartadas_seleccion", 
                "Aves_descartadas_venta", "Retiro_aves", "Consumo_por_ave"]
        
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
                        
                        # Crear pestañas para organizar la información
                        tab1, tab2 = st.tabs(["Tabla de datos", "Estadísticas"])
                        
                        with tab1:
                            st.dataframe(filtered_df)
                        
                        with tab2:
                            # Mostrar estadísticas básicas para los datos numéricos
                            numeric_cols = filtered_df.select_dtypes(include=['number']).columns
                            if len(numeric_cols) > 0:
                                st.write("Estadísticas del lote seleccionado:")
                                st.dataframe(filtered_df[numeric_cols].describe())
                        
                        # Gráficos agrupados por categoría
                        st.subheader(f"Gráficos para el lote: {lote_seleccionado}")
                        
                        # 1. Gráfico de producción de huevos
                        huevos_cols = [col for col in ['Huevos_yumbo', 'Huevos_extra', 'Huevos_aa', 
                                                    'Huevos_a', 'Huevos_b', 'Huevos_c', 
                                                    'Huevos_pipo', 'Huevos_sucios', 
                                                    'Huevos_toteados', 'Yemas', 'Total_huevos'] 
                                    if col in filtered_df.columns]
                        
                        if huevos_cols:
                            st.subheader("Producción de Huevos")
                            df_huevos = pd.DataFrame({
                                'Fecha': pd.to_datetime(filtered_df['Time_data'])
                            })
                            
                            for col in huevos_cols:
                                if len(filtered_df[col].dropna()) > 0:
                                    df_huevos[col] = filtered_df[col]
                            
                            if len(df_huevos.columns) > 1:  # Si hay al menos una columna además de 'Fecha'
                                df_huevos = df_huevos.set_index('Fecha')
                                st.line_chart(df_huevos)
                                
                                # Tabla de resumen estadístico
                                st.write("Resumen estadístico de producción de huevos:")
                                st.dataframe(df_huevos.describe())
                        
                        # 2. Gráfico de mortalidad y descarte de aves
                        aves_cols = [col for col in ['Mortalidad', 'Aves_descartadas_seleccion', 
                                                  'Aves_descartadas_venta', 'Retiro_aves'] 
                                  if col in filtered_df.columns]
                        
                        if aves_cols:
                            st.subheader("Mortalidad y Descarte de Aves")
                            df_aves = pd.DataFrame({
                                'Fecha': pd.to_datetime(filtered_df['Time_data'])
                            })
                            
                            for col in aves_cols:
                                if len(filtered_df[col].dropna()) > 0:
                                    df_aves[col] = filtered_df[col]
                            
                            if len(df_aves.columns) > 1:  # Si hay al menos una columna además de 'Fecha'
                                df_aves = df_aves.set_index('Fecha')
                                st.line_chart(df_aves)
                        
                        # 3. Gráfico de consumo
                        consumo_cols = [col for col in ['Consumo_concentrado', 'Consumo_por_ave'] 
                                     if col in filtered_df.columns]
                        
                        if consumo_cols:
                            st.subheader("Consumo de Concentrado")
                            df_consumo = pd.DataFrame({
                                'Fecha': pd.to_datetime(filtered_df['Time_data'])
                            })
                            
                            for col in consumo_cols:
                                if len(filtered_df[col].dropna()) > 0:
                                    df_consumo[col] = filtered_df[col]
                            
                            if len(df_consumo.columns) > 1:  # Si hay al menos una columna además de 'Fecha'
                                df_consumo = df_consumo.set_index('Fecha')
                                st.line_chart(df_consumo)
                        
                        # 4. Gráfico comparativo de producción vs consumo
                        if 'Total_huevos' in filtered_df.columns and 'Consumo_concentrado' in filtered_df.columns:
                            if len(filtered_df['Total_huevos'].dropna()) > 0 and len(filtered_df['Consumo_concentrado'].dropna()) > 0:
                                st.subheader("Relación Producción vs Consumo")
                                df_relacion = pd.DataFrame({
                                    'Fecha': pd.to_datetime(filtered_df['Time_data']),
                                    'Total Huevos': filtered_df['Total_huevos'],
                                    'Consumo (kg)': filtered_df['Consumo_concentrado']
                                })
                                df_relacion = df_relacion.set_index('Fecha')
                                st.line_chart(df_relacion)
                
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

# Sección informativa con métricas clave
st.subheader("Métricas Clave")
try:
    # Consulta para obtener las métricas más recientes
    query_reciente = f'from(bucket: "{bucket}")' \
                    f'|> range(start: -{tiempo_consulta}d)' \
                    f'|> filter(fn: (r) => r._measurement == "Produccion_Avicola")' \
                    f'|> filter(fn: (r) => r._field == "Total_huevos" or r._field == "Mortalidad" or r._field == "Consumo_concentrado")' \
                    f'|> last()'
    
    tables_reciente = client_Inf.query_api().query(query_reciente, org)
    
    # Crear diccionario para almacenar los valores más recientes
    metricas_recientes = {}
    
    for table in tables_reciente:
        for record in table.records:
            campo = record.get_field()
            valor = record.get_value()
            metricas_recientes[campo] = valor
    
    # Mostrar métricas en columnas
    if metricas_recientes:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if "Total_huevos" in metricas_recientes:
                st.metric("Producción Total Reciente", f"{int(metricas_recientes['Total_huevos']):,} huevos")
            else:
                st.metric("Producción Total Reciente", "No disponible")
        
        with col2:
            if "Mortalidad" in metricas_recientes:
                st.metric("Mortalidad Reciente", f"{int(metricas_recientes['Mortalidad']):,} aves")
            else:
                st.metric("Mortalidad Reciente", "No disponible")
        
        with col3:
            if "Consumo_concentrado" in metricas_recientes:
                st.metric("Consumo Reciente", f"{metricas_recientes['Consumo_concentrado']:,.2f} kg")
            else:
                st.metric("Consumo Reciente", "No disponible")
except Exception as e:
    st.warning(f"No se pudieron cargar las métricas recientes: {e}")

st.write("Esta aplicación consulta datos de producción avícola desde InfluxDB.")
st.write("Para registrar nuevos datos, utilice la aplicación de registro correspondiente.")
