# python_server/dashboard.py
# Biblioteca principal para criar o dashboard web interativo.
import streamlit as st
import pandas as pd    # Para manipulação e análise de dados (DataFrames).
import json            # Para ler e escrever arquivos JSON.
import time            # Para pausas e controle de tempo.
import os              # Para operações de sistema de arquivos.
# Para criar gráficos interativos e visualmente atraentes.
import plotly.express as px
from datetime import datetime  # Para trabalhar com timestamps.

# --- Caminhos dos Arquivos de Dados ---
# Estes são os mesmos arquivos que o data_processor.py gera.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ALL_SENSOR_DATA_FILE = os.path.join(BASE_DIR, '..', 'r_analysis', 'temp_data', 'all_sensor_data.json')
FLOOD_RISK_OUTPUT_R = os.path.join(BASE_DIR, '..', 'r_analysis', 'temp_data', 'flood_risk_output.json')
FIRE_RISK_OUTPUT_R = os.path.join(BASE_DIR, '..', 'r_analysis', 'temp_data', 'fire_risk_output.json')


# --- Configuração da Página do Streamlit ---
st.set_page_config(
    layout="wide", page_title="Guardião Natural - Dashboard de Desastres")

st.title("🌎 Guardião Natural - Monitoramento e Prevenção de Desastres")
st.markdown(
    "Dashboard interativo para visualização de dados de sensores e alertas de risco.")

# --- Função para Carregar Dados JSON de Forma Segura ---


# Cache os dados por 1 segundo para evitar leituras excessivas (melhora performance).
@st.cache_data(ttl=1)
def load_json_data(filepath):
    """Carrega dados de um arquivo JSON, retornando uma lista vazia se o arquivo não existir."""
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            return data
    except json.JSONDecodeError:
        st.warning(
            f"Erro ao decodificar JSON em {filepath}. O arquivo pode estar vazio ou corrompido.")
        return []
    except Exception as e:
        st.error(f"Erro ao carregar {filepath}: {e}")
        return []

# --- Função para Carregar o Último Alerta de Risco ---


@st.cache_data(ttl=1)  # Cache também para os alertas de risco.
def load_latest_risk_alert(filepath):
    """Carrega o último objeto de risco de um arquivo JSON."""
    if not os.path.exists(filepath):
        return {}
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            return data
    except json.JSONDecodeError:
        # Retorna vazio se o arquivo não for um JSON válido (ex: vazio)
        return {}
    except Exception as e:
        st.error(f"Erro ao carregar alerta de risco de {filepath}: {e}")
        return {}


# --- Layout do Dashboard ---
# Usamos colunas para organizar o conteúdo visualmente.
col1, col2 = st.columns(2)

# --- Seção de Enchentes ---
with col1:
    st.header("💧 Monitoramento de Enchentes")
    # Carrega todos os dados dos sensores e filtra para enchentes
    all_sensor_data = load_json_data(ALL_SENSOR_DATA_FILE)
    df_flood_raw = pd.DataFrame(all_sensor_data)

    if not df_flood_raw.empty:
        # Garante que as colunas existam e não são nulas
        df_flood = df_flood_raw[['timestamp',
                                 'water_level', 'rainfall_intensity']].copy()
        df_flood['timestamp'] = pd.to_datetime(df_flood['timestamp'])
        df_flood = df_flood.dropna()  # Remove linhas com NaN nas colunas relevantes
        df_flood = df_flood.sort_values(
            'timestamp', ascending=True)  # Ordena por timestamp

        # Exibe os últimos valores
        latest_flood_data = df_flood.tail(1)
        if not latest_flood_data.empty:
            st.metric(label="Nível da Água Atual",
                      value=f"{latest_flood_data['water_level'].iloc[0]:.0f}%")
            st.metric(label="Intensidade da Chuva Atual",
                      value=f"{latest_flood_data['rainfall_intensity'].iloc[0]:.0f}%")

        # Gráfico de Nível da Água ao longo do tempo
        # Precisa de pelo menos 2 pontos para gráfico de linha
        if len(df_flood['water_level']) > 1:
            fig_water_level = px.line(
                df_flood, x='timestamp', y='water_level', title='Histórico do Nível da Água (%)')
            st.plotly_chart(fig_water_level, use_container_width=True)

        # Gráfico de Intensidade da Chuva ao longo do tempo
        if len(df_flood['rainfall_intensity']) > 1:
            fig_rainfall = px.line(df_flood, x='timestamp', y='rainfall_intensity',
                                   title='Histórico da Intensidade da Chuva (%)')
            st.plotly_chart(fig_rainfall, use_container_width=True)
    else:
        st.info("Aguardando dados de enchentes do sensor...")

    # --- Alerta de Risco de Enchente (do R e LM) ---
    st.subheader("⚠️ Alerta de Risco de Enchente")
    flood_risk_data = load_latest_risk_alert(FLOOD_RISK_OUTPUT_R)

    if flood_risk_data:
        risk_level = flood_risk_data.get("risk_level", "Desconhecido")
        pred_water = flood_risk_data.get("predicted_water_level", "N/A")
        pred_rainfall = flood_risk_data.get("predicted_rainfall", "N/A")
        analysis_time = flood_risk_data.get("timestamp_analysis", "N/A")

        st.write(f"**Nível de Risco Calculado:** **{risk_level}**")
        st.write(f"Previsão Nível Água: {pred_water}%")
        st.write(f"Previsão Chuva: {pred_rainfall}%")
        st.caption(f"Última análise: {analysis_time}")

        # O dashboard pode exibir uma mensagem de alerta do LM
    
        if risk_level == "Muito Alto":
            st.error(
                "🚨 ALERTA MÁXIMO! Risco de enchente iminente. Busque abrigo seguro imediatamente!")
        elif risk_level == "Alto":
            st.warning(
                "🟠 ALERTA: Risco ALTO de enchente. Prepare-se para evacuação e monitore a situação.")
        elif risk_level == "Moderado":
            st.info(
                "🟡 Atenção: Risco MODERADO de enchente. Monitore o nível da água e as condições climáticas.")
        else:
            st.success("🟢 Risco de enchente: Baixo. Situação sob controle.")
    else:
        st.info("Aguardando resultados da análise de risco de enchente (Python/R)...")

# --- Seção de Incêndios ---
with col2:
    st.header("🔥 Monitoramento de Incêndios")
    df_fire_raw = pd.DataFrame(all_sensor_data)

    if not df_fire_raw.empty:
        df_fire = df_fire_raw[['timestamp', 'temperature',
                               'humidity', 'smoke_concentration']].copy()
        df_fire['timestamp'] = pd.to_datetime(df_fire['timestamp'])
        df_fire = df_fire.dropna()
        df_fire = df_fire.sort_values('timestamp', ascending=True)

        # Exibe os últimos valores
        latest_fire_data = df_fire.tail(1)
        if not latest_fire_data.empty:
            st.metric(label="Temperatura Atual",
                      value=f"{latest_fire_data['temperature'].iloc[0]:.1f}°C")
            st.metric(label="Umidade Atual",
                      value=f"{latest_fire_data['humidity'].iloc[0]:.0f}%")
            st.metric(label="Fumaça Atual",
                      value=f"{latest_fire_data['smoke_concentration'].iloc[0]:.0f}%")

        # Gráfico de Temperatura
        if len(df_fire['temperature']) > 1:
            fig_temp = px.line(
                df_fire, x='timestamp', y='temperature', title='Histórico da Temperatura (°C)')
            st.plotly_chart(fig_temp, use_container_width=True)

        # Gráfico de Fumaça
        if len(df_fire['smoke_concentration']) > 1:
            fig_smoke = px.line(df_fire, x='timestamp', y='smoke_concentration',
                                title='Histórico da Concentração de Fumaça (%)')
            st.plotly_chart(fig_smoke, use_container_width=True)
    else:
        st.info("Aguardando dados de incêndio do sensor...")

    # --- Alerta de Risco de Incêndio (do R e LM) ---
    st.subheader("🔥 Alerta de Risco de Incêndio")
    fire_risk_data = load_latest_risk_alert(FIRE_RISK_OUTPUT_R)

    if fire_risk_data:
        risk_level = fire_risk_data.get("risk_level", "Desconhecido")
        pred_temp = fire_risk_data.get("predicted_temperature", "N/A")
        pred_smoke = fire_risk_data.get("predicted_smoke", "N/A")
        analysis_time = fire_risk_data.get("timestamp_analysis", "N/A")

        st.write(f"**Nível de Risco Calculado:** **{risk_level}**")
        st.write(f"Previsão Temperatura: {pred_temp}°C")
        st.write(f"Previsão Fumaça: {pred_smoke}%")
        st.caption(f"Última análise: {analysis_time}")

        if risk_level == "Muito Alto":
            st.error(
                "🚨 ALERTA MÁXIMO! Risco de incêndio iminente. Evacue a área e chame os bombeiros!")
        elif risk_level == "Alto":
            st.warning(
                "🟠 ALERTA: Risco ALTO de incêndio. Fique atento a sinais de fumaça e prepare-se.")
        elif risk_level == "Moderado":
            st.info(
                "🟡 Atenção: Risco MODERADO de incêndio. Evite atividades com fogo e monitore a umidade.")
        else:
            st.success("🟢 Risco de incêndio: Baixo. Situação sob controle.")
    else:
        st.info("Aguardando resultados da análise de risco de incêndio (Python/R)...")


# --- Atualização Automática ---
UPDATE_INTERVAL_SECONDS = 5  # Atualiza o dashboard a cada 5 segundos.

st.markdown("---")
st.write(f"Dashboard atualizando a cada {UPDATE_INTERVAL_SECONDS} segundos...")
# Placeholder que mantém a página atualizada
time.sleep(UPDATE_INTERVAL_SECONDS)
st.rerun()  # Força o Streamlit a reexecutar o script
