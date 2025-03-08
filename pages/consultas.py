import time
import json
from datetime import datetime, timedelta
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# Configuración de la página
st.set_page_config(page_title="Sistema de Gestión Avícola - Consultas", layout="wide")

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
col1, col2 = st.columns(2)

with col1:
    # Rango de tiempo para la consulta
    tiempo_consulta = st.slider('Selecciona el período de consulta (días)', 1, 90, 30)
    
    # Opciones de filtrado
    tipo_consulta = st.radio(
        "Tipo de consulta:",
        ["Todos los lotes", "Lote específico"]
    )

with col2:
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

# Función para realizar consulta a InfluxDB
def consultar_datos(tiempo_dias, lote=None):
    datos = {campo: [] for campo in campos_avicolas}
    datos["Timestamp"] = []  # Para almacenar los timestamps
    
    try:
        # Crear el filtro de lote si es necesario
        filtro_lote = f'|> filter(fn: (r) => r.lote == "{lote}")' if lote else ""
        
        # Consultar cada campo
        for campo in campos_avicolas:
            query = f'from(bucket: "{bucket}")' \
                    f'|> range(start: -{tiempo_dias}d)' \
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
        df = pd.DataFrame(datos)
        
        # Si no hay datos, retornar DataFrame vacío
        if df.empty:
            return pd.DataFrame()
        
        return df
    
    except Exception as e:
        st.error(f"Error al consultar datos: {str(e)}")
        return pd.DataFrame()

# Botón para realizar la consulta
if st.button('Consultar Datos'):
    with st.spinner('Consultando datos...'):
        if tipo_consulta == "Lote específico" and lote_seleccionado:
            df_resultado = consultar_datos(tiempo_consulta, lote_seleccionado)
            titulo_consulta = f"Datos del lote: {lote_seleccionado}"
        else:
            df_resultado = consultar_datos(tiempo_consulta)
            titulo_consulta = "Datos de todos los lotes"
    
    # Mostrar resultados
    if not df_resultado.empty:
        st.subheader(titulo_consulta)
        
        # Formatear el DataFrame para mostrar
        df_display = df_resultado.copy()
        
        # Convertir timestamp a formato legible
        if "Timestamp" in df_display.columns:
            df_display["Fecha"] = df_display["Timestamp"].dt.strftime('%Y-%m-%d %H:%M:%S')
            df_display = df_display.drop("Timestamp", axis=1)
        
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
        
        # Visualizaciones
        st.subheader("Visualizaciones")
        
        # Gráfico de producción de huevos
        fig_huevos = go.Figure()
        categorias_huevos = ["Huevos_yumbo", "Huevos_extra", "Huevos_aa", "Huevos_a", 
                           "Huevos_b", "Huevos_c", "Huevos_pipo", "Huevos_sucios", 
                           "Huevos_toteados", "Yemas"]
        
        for categoria in categorias_huevos:
            if categoria in df_resultado.columns:
                fig_huevos.add_trace(go.Scatter(
                    x=df_resultado["Timestamp"],
                    y=df_resultado[categoria],
                    mode='lines+markers',
                    name=categoria.replace("_", " ")
                ))
        
        fig_huevos.update_layout(
            title="Producción de Huevos por Categoría",
            xaxis_title="Fecha",
            yaxis_title="Cantidad",
            legend_title="Categoría",
            height=500
        )
        
        st.plotly_chart(fig_huevos, use_container_width=True)
        
        # Gráfico de mortalidad y descarte
        fig_mortalidad = go.Figure()
        categorias_mortalidad = ["Mortalidad", "Aves_descartadas_seleccion", 
                               "Aves_descartadas_venta", "Retiro_aves"]
        
        for categoria in categorias_mortalidad:
            if categoria in df_resultado.columns:
                fig_mortalidad.add_trace(go.Scatter(
                    x=df_resultado["Timestamp"],
                    y=df_resultado[categoria],
                    mode='lines+markers',
                    name=categoria.replace("_", " ")
                ))
        
        fig_mortalidad.update_layout(
            title="Mortalidad y Descarte de Aves",
            xaxis_title="Fecha",
            yaxis_title="Cantidad",
            legend_title="Categoría",
            height=400
        )
        
        st.plotly_chart(fig_mortalidad, use_container_width=True)
        
        # Gráfico de consumo
        if "Consumo_concentrado" in df_resultado.columns and "Consumo_por_ave" in df_resultado.columns:
            fig_consumo = go.Figure()
            
            fig_consumo.add_trace(go.Scatter(
                x=df_resultado["Timestamp"],
                y=df_resultado["Consumo_concentrado"],
                mode='lines+markers',
                name='Consumo total (kg)',
                yaxis='y'
            ))
            
            fig_consumo.add_trace(go.Scatter(
                x=df_resultado["Timestamp"],
                y=df_resultado["Consumo_por_ave"],
                mode='lines+markers',
                name='Consumo por ave (kg)',
                yaxis='y2'
            ))
            
            fig_consumo.update_layout(
                title="Consumo de Concentrado",
                xaxis_title="Fecha",
                yaxis_title="Consumo Total (kg)",
                yaxis2=dict(
                    title="Consumo por Ave (kg)",
                    overlaying='y',
                    side='right'
                ),
                legend_title="Medida",
                height=400
            )
            
            st.plotly_chart(fig_consumo, use_container_width=True)
    else:
        st.warning("No se encontraron datos para los criterios seleccionados.")
else:
    st.info("Presiona el botón 'Consultar Datos' para ver la información.")

# Añadir información adicional
st.markdown("---")
st.write("Esta aplicación consulta datos de producción avícola desde InfluxDB.")
st.write("Para registrar nuevos datos, utilice la aplicación de registro correspondiente.")
