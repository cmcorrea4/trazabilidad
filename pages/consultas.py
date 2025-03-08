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
            lote_seleccionado = None
    except Exception as e:
        st.error(f"Error al consultar lotes: {e}")
        lote_seleccionado = None

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
    datos = {campo: [] for campo in campos_avicolas}
    datos["Timestamp"] = []  # Para almacenar los timestamps
    
    try:
        # Crear el filtro de lote si es necesario
        filtro_lote = f'|> filter(fn: (r) => r.lote == "{lote_seleccionado}")' if tipo_consulta == "Lote específico" and lote_seleccionado else ""
        
        # Consultar cada campo
        for campo in campos_avicolas:
            query = f'from(bucket: "{bucket}")' \
                    f'|> range(start: -{tiempo_consulta}d)' \
                    f'|> filter(fn: (r) => r._measurement == "Produccion_Avicola")' \
                    f'|> filter(fn: (r) => r._field == "{campo}")' \
                    f'{filtro_lote}' \
                    f'|> sort(columns: ["_time"], desc: false)'
            
            tables = client_Inf.query_api().query(query, org)
            
            for table in tables:
                for record in table.records:
                    # Almacenar el valor
                    datos[campo].append(record.get_value())
                    
                    # Almacenar el timestamp (solo para el primer campo)
                    if campo == campos_avicolas[0]:
                        # Convertir a zona horaria local
                        tiempo = record.get_time().astimezone()
                        datos["Timestamp"].append(tiempo)
        
        # Crear DataFrame
        df_resultado = pd.DataFrame(datos)
        
        # Si no hay datos, mostrar mensaje
        if df_resultado.empty:
            st.warning("No se encontraron datos para los criterios seleccionados.")
        else:
            # Formatear el DataFrame para mostrar
            df_display = df_resultado.copy()
            
            # Convertir timestamp a formato legible
            if "Timestamp" in df_display.columns:
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
            
            # Gráfico de producción de huevos
            categorias_huevos = ["Huevos_yumbo", "Huevos_extra", "Huevos_aa", "Huevos_a", 
                               "Huevos_b", "Huevos_c", "Huevos_pipo", "Huevos_sucios", 
                               "Huevos_toteados", "Yemas"]
            
            df_huevos = df_resultado[["Timestamp"] + [col for col in categorias_huevos if col in df_resultado.columns]]
            df_huevos = df_huevos.set_index("Timestamp")
            
            st.line_chart(df_huevos)
            st.caption("Producción de Huevos por Categoría")
            
            # Gráfico de mortalidad y descarte
            categorias_mortalidad = ["Mortalidad", "Aves_descartadas_seleccion", 
                                   "Aves_descartadas_venta", "Retiro_aves"]
            
            df_mortalidad = df_resultado[["Timestamp"] + [col for col in categorias_mortalidad if col in df_resultado.columns]]
            df_mortalidad = df_mortalidad.set_index("Timestamp")
            
            st.line_chart(df_mortalidad)
            st.caption("Mortalidad y Descarte de Aves")
            
            # Gráfico de consumo
            if "Consumo_concentrado" in df_resultado.columns:
                df_consumo = df_resultado[["Timestamp", "Consumo_concentrado"]]
                df_consumo = df_consumo.set_index("Timestamp")
                
                st.line_chart(df_consumo)
                st.caption("Consumo de Concentrado (kg)")
            
            # Consumo por ave (si existe)
            if "Consumo_por_ave" in df_resultado.columns:
                df_consumo_ave = df_resultado[["Timestamp", "Consumo_por_ave"]]
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
