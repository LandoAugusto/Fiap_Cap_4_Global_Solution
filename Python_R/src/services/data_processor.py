# python_server/data_processor.py
from  dotenv import load_dotenv
import paho.mqtt.client as mqtt  # Importa a biblioteca para comunicação MQTT.
# Importa a biblioteca para trabalhar com dados JSON.
import json
import time                     # Importa a biblioteca para funções de tempo.
# Importa a biblioteca Pandas para manipulação de dados em formato de tabela (DataFrames).
import pandas as pd
# Importa subprocess para executar comandos externos, como scripts R.
import subprocess
# Importa os para interagir com o sistema operacional (caminhos de arquivo, variáveis de ambiente).
import os
# Importa datetime para trabalhar com datas e horas.
from datetime import datetime

# --- Configurações MQTT ---
MQTT_BROKER_HOST = "broker.hivemq.com"
MQTT_BROKER_PORT = 1883
MQTT_TOPIC_ALL_DATA = "guardiao_natural/sensor_data"

# --- Caminhos dos Arquivos de Dados (simulação de Banco de Dados) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ALL_SENSOR_DATA_FILE = os.path.join(BASE_DIR, '..', 'r_analysis', 'temp_data', 'all_sensor_data.json')

# --- Arquivos para Integração com R ---
FLOOD_DATA_FOR_R = os.path.join(BASE_DIR, '..', 'r_analysis', 'temp_data', 'flood_data_for_r.csv')
FIRE_DATA_FOR_R = os.path.join(BASE_DIR, '..', 'r_analysis', 'temp_data', 'fire_data_for_r.csv')
FLOOD_RISK_OUTPUT_R = os.path.join(BASE_DIR, '..', 'r_analysis', 'temp_data', 'flood_risk_output.json')
FIRE_RISK_OUTPUT_R = os.path.join(BASE_DIR, '..', 'r_analysis', 'temp_data', 'fire_risk_output.json')
FLOOD_ANALYSIS_R  = os.path.join(BASE_DIR, '..', 'r_analysis', 'flood_analysis.R')
FIRE_ANALYSIS_R  = os.path.join(BASE_DIR, '..', 'r_analysis', 'fire_analysis.R')


# --- Chave da API do LM (SIMULADA) ---
# Mantemos o load_dotenv() caso outras variáveis de ambiente sejam adicionadas no futuro.
load_dotenv()

# --- Função de Callback MQTT: Quando o Cliente Conecta ao Broker ---


def on_connect(client, userdata, flags, rc):
    """Callback chamado quando o cliente MQTT se conecta ao broker."""
    print(f"Conectado ao broker MQTT com código: {rc}")
    client.subscribe(MQTT_TOPIC_ALL_DATA)
    print(f"Subscrito ao tópico: {MQTT_TOPIC_ALL_DATA}")

# --- Função de Callback MQTT: Quando uma Mensagem é Recebida ---


def on_message(client, userdata, msg):
    """Callback chamado quando uma mensagem MQTT é recebida em um tópico subscrito."""
    print(f"Mensagem recebida no tópico {msg.topic}: {msg.payload.decode()}")

    try:
        data = json.loads(msg.payload.decode())
        data['timestamp'] = datetime.now().isoformat()

        save_data(data, ALL_SENSOR_DATA_FILE)

        process_flood_data(data)
        process_fire_data(data)

    except json.JSONDecodeError:
        print("Erro ao decodificar JSON da mensagem MQTT.")
    except Exception as e:
        print(f"Erro no processamento da mensagem: {e}")


def save_data(data, filename):
    ensure_directory_exists(filename)
    if not os.path.exists(filename):
        with open(filename, 'w') as f:
            json.dump([], f)

    with open(filename, 'r+') as f:
        file_data = json.load(f)
        file_data.append(data)
        f.seek(0)
        json.dump(file_data, f, indent=4)


def load_data(filename):
    """Carrega dados de um arquivo JSON."""
    if not os.path.exists(filename):
        return []
    with open(filename, 'r') as f:
        return json.load(f)


def run_r_script(script_path, input_file, output_file):
    """Executa um script R."""
    try:
        cmd = ["Rscript", script_path, input_file, output_file]
        result = subprocess.run(
            cmd,timeout=60, capture_output=True, text=True, check=True)
        print(f"Script R '{script_path}' executado. Saída:\n{result.stdout}")
        if result.stderr:
            print(f"Erros/Warnings do R:\n{result.stderr}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar script R: {e}")
        print(f"Stderr: {e.stderr}")
        print(f"Stdout: {e.stdout}")
        return False
    except FileNotFoundError:
        print(f"Erro: Rscript não encontrado. Certifique-se de que R esteja no seu PATH.")
        return False

# FUNÇÃO MODIFICADA: AGORA SIMULA A RESPOSTA DO LM


def get_lm_response(prompt):
    """
    SIMULA a interação com um Large Language Model (LM)
    para gerar alertas com base no prompt.
    """
    print("SIMULANDO CHAMADA AO LM. Alerta gerado com base no nível de risco extraído do prompt.")

    # Extrai o nível de risco do prompt.
    # O prompt é o texto que enviaríamos a um LM real, e ele já contém o nível de risco.
    risk_level = "Baixo"  # Valor padrão se não for encontrado
    if "Nível de Risco Calculado pelo modelo de ML: Muito Alto" in prompt:
        risk_level = "Muito Alto"
    elif "Nível de Risco Calculado pelo modelo de ML: Alto" in prompt:
        risk_level = "Alto"
    elif "Nível de Risco Calculado pelo modelo de ML: Moderado" in prompt:
        risk_level = "Moderado"
    else:
        risk_level = "Baixo"  # Para qualquer outro caso ou se não encontrar no prompt

    # Gera uma mensagem de alerta simulada com base no nível de risco.
    # Esta lógica é a mesma que já está no dashboard para ser consistente.
    simulated_alert_message = ""
    if risk_level == "Muito Alto":
        simulated_alert_message = "🚨 ALERTA MÁXIMO! Risco IMINENTE. Busque abrigo seguro imediatamente e siga as instruções das autoridades. Sua segurança é prioridade! (Guardião Natural Simulado)"
    elif risk_level == "Alto":
        simulated_alert_message = "🟠 ALERTA: Risco ALTO. Prepare-se para possíveis impactos e monitore a situação de perto. Tenha um kit de emergência pronto. (Guardião Natural Simulado)"
    elif risk_level == "Moderado":
        simulated_alert_message = "🟡 ATENÇÃO: Risco MODERADO. Mantenha-se informado sobre as condições. Evite áreas de risco e tome precauções básicas. (Guardião Natural Simulado)"
    else:  # Baixo
        simulated_alert_message = "🟢 STATUS: Risco Baixo. Situação sob controle. Continue monitorando as informações oficiais. (Guardião Natural Simulado)"

    return simulated_alert_message


def process_flood_data(new_data):
    """Processa dados de enchente, chama o script R de análise e o LM para gerar alertas."""
    ensure_directory_exists(ALL_SENSOR_DATA_FILE)
    all_sensor_data = load_data(ALL_SENSOR_DATA_FILE)
    if not all_sensor_data:
        print("Dados de sensor insuficientes para análise de enchente.")
        return

    flood_specific_data = []
    for item in all_sensor_data:
        if 'water_level' in item and 'rainfall_intensity' in item and 'timestamp' in item:
            flood_specific_data.append({
                'timestamp': item['timestamp'],
                'water_level': item['water_level'],
                'rainfall_intensity': item['rainfall_intensity']
            })

    if not flood_specific_data:
        print("Nenhum dado de enchente relevante encontrado para análise.")
        return

    df_flood = pd.DataFrame(flood_specific_data)
    df_flood['timestamp'] = pd.to_datetime(df_flood['timestamp'])
    ensure_directory_exists(FIRE_DATA_FOR_R)
    df_flood.to_csv(FLOOD_DATA_FOR_R, index=False)
    print(f"Dados de enchente para R salvos em {FLOOD_DATA_FOR_R}")  

    ensure_directory_exists(FLOOD_ANALYSIS_R)
    if run_r_script(FLOOD_ANALYSIS_R, FLOOD_DATA_FOR_R, FLOOD_RISK_OUTPUT_R):
        try:
            with open(FLOOD_RISK_OUTPUT_R, 'r') as f:
                flood_risk_data = json.load(f)
            risk_level = flood_risk_data.get("risk_level", "Baixo")
            water_level_pred = flood_risk_data.get(
                "predicted_water_level", "N/A")
            rainfall_pred = flood_risk_data.get("predicted_rainfall", "N/A")

            lm_prompt = f"""
            **Guardião Natural - Alerta de Enchente:**
            Com base nos seguintes dados de sensor e previsões de risco de enchente:
            Nível atual da água: {new_data.get('water_level', 'N/A')}cm
            Intensidade de chuva atual: {new_data.get('rainfall_intensity', 'N/A')}%
            Previsão de Nível da Água (próximas horas): {water_level_pred}cm
            Previsão de Chuva (próximas horas): {rainfall_pred}%
            Nível de Risco Calculado pelo modelo de ML: {risk_level}

            Gere uma mensagem de alerta concisa e acionável para a população local,
            considerando o nível de risco.
            - Se o risco for 'Baixo', use uma mensagem tranquilizadora, indicando que a situação está sob controle.
            - Se for 'Moderado', alerte sobre a necessidade de monitoramento e precauções básicas.
            - Se for 'Alto' ou 'Muito Alto', instrua sobre precauções urgentes, como evitar áreas de risco, preparar kit de emergência ou considerar evacuação.
            A mensagem deve ser clara e direta.
            """
            print("\n--- Alerta de Enchente (LM) ---")
            alert_message = get_lm_response(lm_prompt)
            print(alert_message)
            print("---------------------------------\n")

        except FileNotFoundError:
            print(
                f"Arquivo de saída do R '{FLOOD_RISK_OUTPUT_R}' não encontrado.")
        except json.JSONDecodeError:
            print(f"Erro ao decodificar JSON do arquivo de saída do R para enchentes.")


def process_fire_data(new_data):
    """Processa dados de incêndio, chama o script R de análise e o LM para gerar alertas."""
    all_sensor_data = load_data(ALL_SENSOR_DATA_FILE)
    if not all_sensor_data:
        print("Dados de sensor insuficientes para análise de incêndio.")
        return

    fire_specific_data = []
    for item in all_sensor_data:
        if 'temperature' in item and 'humidity' in item and 'smoke_concentration' in item and 'timestamp' in item:
            fire_specific_data.append({
                'timestamp': item['timestamp'],
                'temperature': item['temperature'],
                'humidity': item['humidity'],
                'smoke_concentration': item['smoke_concentration']
            })

    if not fire_specific_data:
        print("Nenhum dado de incêndio relevante encontrado para análise.")
        return

    df_fire = pd.DataFrame(fire_specific_data)
    df_fire['timestamp'] = pd.to_datetime(df_fire['timestamp'])

    ensure_directory_exists(FIRE_DATA_FOR_R)
    df_fire.to_csv(FIRE_DATA_FOR_R, index=False)
    print(f"Dados de incêndio para R salvos em {FIRE_DATA_FOR_R}")

    if run_r_script(FIRE_ANALYSIS_R, FIRE_DATA_FOR_R, FIRE_RISK_OUTPUT_R):
        try:
            with open(FIRE_RISK_OUTPUT_R, 'r') as f:
                fire_risk_data = json.load(f)
            risk_level = fire_risk_data.get("risk_level", "Baixo")
            pred_temp = fire_risk_data.get("predicted_temperature", "N/A")
            pred_smoke = fire_risk_data.get("predicted_smoke", "N/A")

            lm_prompt = f"""
            **Guardião Natural - Alerta de Incêndio:**
            Com base nos seguintes dados de sensor e previsões de risco de incêndio:
            Temperatura atual: {new_data.get('temperature', 'N/A')}°C
            Umidade atual: {new_data.get('humidity', 'N/A')}%
            Concentração de Fumaça atual: {new_data.get('smoke_concentration', 'N/A')}%
            Previsão de Temperatura (próximas horas): {pred_temp}°C
            Previsão de Fumaça (próximas horas): {pred_smoke}%
            Nível de Risco Calculado pelo modelo de ML: {risk_level}

            Gere uma mensagem de alerta concisa e acionável para a população local e autoridades (Defesa Civil, Bombeiros),
            considerando o nível de risco.
            - Se o risco for 'Baixo', use uma mensagem tranquilizadora.
            - Se for 'Moderado', alerte sobre o monitoramento e a necessidade de evitar atividades que gerem faíscas.
            - Se for 'Alto' ou 'Muito Alto', instrua sobre a evacuação imediata da área,
              contato com emergência e não tentar combater o fogo por conta própria.
            A mensagem deve ser clara e direta.
            """
            print("\n--- Alerta de Incêndio (LM) ---")
            alert_message = get_lm_response(lm_prompt)
            print(alert_message)
            print("---------------------------------\n")

        except FileNotFoundError:
            print(
                f"Arquivo de saída do R '{FIRE_RISK_OUTPUT_R}' não encontrado.")
        except json.JSONDecodeError:
            print(f"Erro ao decodificar JSON do arquivo de saída do R para incêndios.")
    
def ensure_directory_exists(path):
    """Garante que o diretório para o caminho especificado exista."""
    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)


# --- Inicialização do Cliente MQTT ---
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

print(f"Conectando ao broker MQTT: {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}")
try:
    client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
except Exception as e:
    print(f"Não foi possível conectar ao broker MQTT: {e}")
    exit()

# --- Loop Principal para Manter o Cliente MQTT Executando ---
client.loop_forever()
