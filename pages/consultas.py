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

# Opciones de filtrado
tipo_consulta = st.radio(
    "Tipo de consulta:",
    ["Todos los lotes", "Lote específico"]
)

# Si se selecciona lote específico, mostrar selector de lotes
lote_seleccionado = None
if tipo_consulta == "Lote específico":
    # Primero consultamos los lotes disponibles
    try:
        query_lotes = f'from(bucket: "{bucket}")' \
                      f'|> range(start: -{tiempo_consulta}d)' \
                      f'|> filter(fn: (r) => r._measurement == "Produccion_Avicola")' \
                      f'|> group(columns: ["lote"])' \
                      f'|> distinct(column: "lote")'
        
        tablas_lotes = client_Inf.query_api().query(query_lotes, org)
        lotes_disponibles = []
        
        for tabla in tablas_lotes:
            for record in tabla.records:
                lotes_disponibles.append(record.values.get("lote"))
        
        if lotes_disponibles:
            lote_seleccionado = st.selectbox('Selecciona un lote:', lotes_disponibles)
        else:
            st.warning("No se encontraron lotes en el período seleccionado.")
    except Exception as e:
        st.error(f"Error al consultar lotes: {e}")

# Campos a consultar
campos_avicolas = [
    "Lote", "Consumo_concentrado", "Mortalidad", 
    "Aves_descartadas_seleccion", "Aves_descartadas_venta",
    "Huevos_yumbo", "Huevos_extra", "Huevos_aa", "Huevos_a", 
    "Huevos_b", "Huevos_c", "Huevos_pipo", "Huevos_sucios", 
    "Huevos_toteados", "Yemas", "Observaciones", 
    "Consumo_por_ave", "Total_huevos", "Retiro_aves"
]

# Botón para realizar la consulta
if st.button('Consultar Datos'):
    try:
        # Modificamos el enfoque para consultar primero todos los tiempos disponibles
        # y luego rellenar los datos para cada campo en esos tiempos
        
        # Crear el filtro de lote si es necesario
        filtro_lote = f'|> filter(fn: (r) => r.lote == "{lote_seleccionado}")' if tipo_consulta == "Lote específico" and lote_seleccionado else ""
        
        # Primero, obtener todos los tiempos únicos para crear un DataFrame base
        query_tiempo = f'from(bucket: "{bucket}")' \
                       f'|> range(start: -{tiempo_consulta}d)' \
                       f'|> filter(fn: (r) => r._measurement == "Produccion_Avicola")' \
                       f'{filtro_lote}' \
                       f'|> group()' \
                       f'|> distinct(column: "_time")' \
                       f'|> sort(columns: ["_time"], desc: false)'
        
        tables_tiempo = client_Inf.query_api().query(query_tiempo, org)
        tiempos = []
        
        for table in tables_tiempo:
            for record in table.records:
                tiempos.append(record.get_time())
        
        # Si no hay tiempos disponibles, mostrar un mensaje y salir
        if not tiempos:
            st.warning("No se encontraron datos para los criterios seleccionados.")
        else:
            # Crear un DataFrame vacío con todos los tiempos
            df_resultado = pd.DataFrame({'Timestamp': tiempos})
            
            # Para cada campo, obtener los valores correspondientes a cada tiempo
            for campo in campos_avicolas:
                query_campo = f'from(bucket: "{bucket}")' \
                              f'|> range(start: -{tiempo_consulta}d)' \
                              f'|> filter(fn: (r) => r._measurement == "Produccion_Avicola")' \
                              f'|> filter(fn: (r) => r._field == "{campo}")' \
                              f'{filtro_lote}' \
                              f'|> sort(columns: ["_time"], desc: false)'
                
                tables_campo = client_Inf.query_api().query(query_campo, org)
                
                # Crear un diccionario que mapee tiempo a valor para este campo
                valores_por_tiempo = {}
                for table in tables_campo:
                    for record in table.records:
                        valores_por_tiempo[record.get_time()] = record.get_value()
                
                # Rellenar el DataFrame con los valores para este campo
                # Si no hay valor para un tiempo específico, se rellena con None
                df_resultado[campo] = df_resultado['Timestamp'].map(
                    lambda t: valores_por_tiempo.get(t, None)
                )
            
            # Formatear el DataFrame para mostrar
            df_display = df_resultado.copy()
            
            # Convertir timestamp a formato legible
            df_display["Fecha"] = df_display["Timestamp"].dt.strftime('%Y-%m-%d %H:%M:%S')
            df_display = df_display.drop("Timestamp", axis=1)
            
            # Título de resultados
            if tipo_consulta == "Lote específico" and lote_seleccionado:
                st.subheader(f"Datos del lote: {lote_seleccionado}")
            else:
                st.subheader("Datos de todos los lotes")
            
            # Mostrar tabla de datos
            st.dataframe(df_display)
            
            # Exportar a CSV
            csv = df_display.to_csv(index=False)
            st.download_button(
                label="Descargar datos como CSV",
                data=csv,
                file_name=f"datos_avicolas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )
            
            # Visualizaciones básicas usando Streamlit
            st.subheader("Visualizaciones")
            
            # Preparar datos para gráficos (eliminando campos no numéricos y estableciendo el índice de tiempo)
            df_grafico = df_resultado.copy()
            
            # Filtrar solo columnas numéricas para gráficos
            columnas_numericas = df_grafico.select_dtypes(include=['number']).columns.tolist()
            
            # Gráfico de producción de huevos (si hay datos disponibles)
            categorias_huevos = [col for col in ["Huevos_yumbo", "Huevos_extra", "Huevos_aa", 
                                              "Huevos_a", "Huevos_b", "Huevos_c", 
                                              "Huevos_pipo", "Huevos_sucios", 
                                              "Huevos_toteados", "Yemas"]
                              if col in columnas_numericas]
            
            if categorias_huevos:
                df_huevos = df_grafico[["Timestamp"] + categorias_huevos].copy()
                df_huevos = df_huevos.set_index("Timestamp")
                
                st.line_chart(df_huevos)
                st.caption("Producción de Huevos por Categoría")
            
            # Gráfico de mortalidad y descarte (si hay datos disponibles)
            categorias_mortalidad = [col for col in ["Mortalidad", "Aves_descartadas_seleccion", 
                                                 "Aves_descartadas_venta", "Retiro_aves"]
                                  if col in columnas_numericas]
            
            if categorias_mortalidad:
                df_mortalidad = df_grafico[["Timestamp"] + categorias_mortalidad].copy()
                df_mortalidad = df_mortalidad.set_index("Timestamp")
                
                st.line_chart(df_mortalidad)
                st.caption("Mortalidad y Descarte de Aves")
            
            # Gráfico de consumo (si hay datos disponibles)
            if "Consumo_concentrado" in columnas_numericas:
                df_consumo = df_grafico[["Timestamp", "Consumo_concentrado"]].copy()
                df_consumo = df_consumo.set_index("Timestamp")
                
                st.line_chart(df_consumo)
                st.caption("Consumo de Concentrado (kg)")
            
            # Consumo por ave (si hay datos disponibles)
            if "Consumo_por_ave" in columnas_numericas:
                df_consumo_ave = df_grafico[["Timestamp", "Consumo_por_ave"]].copy()
                df_consumo_ave = df_consumo_ave.set_index("Timestamp")
                
                st.line_chart(df_consumo_ave)
                st.caption("Consumo por Ave (kg)")
    
    except Exception as e:
        st.error(f"Error al consultar datos: {str(e)}")
else:
    st.info("Presiona el botón 'Consultar Datos' para ver la información.")

# Añadir información adicional
st.markdown("---")
st.write("Esta aplicación consulta datos de producción avícola desde InfluxDB.")
st.write("Para registrar nuevos datos, utilice la aplicación de registro correspondiente.")
