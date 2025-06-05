# r_analysis/flood_analysis.R
# Este script realiza a análise de risco de enchente usando dados históricos para treinamento
# de um modelo de Machine Learning e aplicando-o aos dados atuais dos sensores.

# --- Instalação de Pacotes (se ainda não tiver) ---
# A linha abaixo deve ser executada uma vez no RStudio, não no script.
# install.packages(c("jsonlite", "randomForest", "dplyr", "forecast"))

library(jsonlite)    # Para ler e escrever arquivos JSON.
library(forecast)    # Para modelos de séries temporais como ARIMA, essencial para previsão.
library(dplyr)       # Para manipulação de dados (filtrar, agrupar, etc.).
library(randomForest) # Para o modelo Random Forest, que pode ser usado para classificação de risco.

# --- Argumentos de Linha de Comando ---
# O Python passa o caminho do arquivo de entrada (dados atuais do sensor) e do arquivo de saída (resultado do risco).
args <- commandArgs(trailingOnly = TRUE)
input_file <- args[1] # Ex: "r_analysis/temp_data/flood_data_for_r.csv"
output_file <- args[2] # Ex: "r_analysis/temp_data/flood_risk_output.json"

# --- Carregar Dados Atuais dos Sensores ---
# Estes são os dados mais recentes recebidos do ESP32 via MQTT.
if (!file.exists(input_file)) {
  stop(paste("ERRO: Arquivo de entrada de dados atuais não encontrado:", input_file))
}
current_sensor_data <- read.csv(input_file)
current_sensor_data$timestamp <- as.POSIXct(current_sensor_data$timestamp) # Converte para formato de data/hora.

# Garante que temos pelo menos um ponto de dado para processar.
if (nrow(current_sensor_data) == 0) {
  # Se não há dados, retorna um risco baixo e valores NA.
  output_data <- list(
    risk_level = "Baixo",
    predicted_water_level = NA,
    predicted_rainfall = NA,
    timestamp_analysis = format(Sys.time(), "%Y-%m-%dT%H:%M:%S"),
    message = "Dados insuficientes para análise preditiva."
  )
  write_json(output_data, output_file, auto_unbox = TRUE)
  quit(save = "no")
}

# --- Carregar Dados Históricos para Treinamento do Modelo de ML ---
# Estes dados simulam informações de disasterscharter.org para treinar o modelo.
historical_data_path <- "C:\\Work\\Fiap\\Python\\Fase_4\\Projeto\\GuardiaoNatural\\GuardiaoNatural\\master\\src\\r_analysis\\datasets\\historical_flood_data.csv"
if (!file.exists(historical_data_path)) {
  stop(paste("ERRO: Arquivo de dados históricos não encontrado:", historical_data_path))
}
historical_flood_data <- read.csv(historical_data_path)
historical_flood_data$timestamp <- as.POSIXct(historical_flood_data$timestamp)

# --- Preparação de Dados para o Modelo de ML ---
# Para um modelo de classificação de risco, precisamos que a coluna 'flood_risk_category' seja um fator.
# A ordem dos níveis é importante para o LM entender a gravidade.
historical_flood_data$flood_risk_category <- factor(
  historical_flood_data$flood_risk_category,
  levels = c("Baixo", "Moderado", "Alto", "Muito Alto")
)

# --- Treinamento do Modelo de Machine Learning (Random Forest) ---
# Usamos Random Forest para classificar o risco de enchente.
# Ele é robusto e funciona bem com dados tabulares.
# As features (variáveis preditoras) devem ser aquelas que influenciam o risco.
# 'ntree' é o número de árvores na floresta (ajuste para desempenho vs. precisão).
# 'mtry' é o número de variáveis aleatoriamente amostradas em cada divisão (geralmente sqrt(num_features)).
set.seed(123) # Para reprodutibilidade
m_flood_risk <- randomForest(
  flood_risk_category ~ water_level_avg_24h + rainfall_total_24h + water_level_change_12h + previous_flood_event_in_region,
  data = historical_flood_data,
  ntree = 100
)
message("Modelo Random Forest para enchentes treinado com sucesso.")

# --- Realizar Previsões para Dados Atuais ---
# Extrair o último ponto de dados recebido do sensor virtual.
latest_sensor_data <- tail(current_sensor_data, 1)

# Simular 'features' para a previsão (pode precisar de mais dados históricos do que um ponto).
# Para este MVP, vamos criar um 'newdata' simples com base no último ponto.
# Em um sistema real, você calcularia 'water_level_avg_24h', 'rainfall_total_24h' etc.
# a partir de uma janela de tempo dos dados atuais.
# Para manter a POC simples, mapeamos diretamente as leituras atuais para as features de previsão.
# A precisão aqui dependerá da similaridade entre os dados do sensor e as features de treinamento.
current_water_level <- latest_sensor_data$water_level
current_rainfall_intensity <- latest_sensor_data$rainfall_intensity

# Ajuste para simular as features do modelo de treinamento:
# water_level_avg_24h: Usamos o current_water_level.
# rainfall_total_24h: Usamos o current_rainfall_intensity.
# water_level_change_12h: Simula uma mudança (pode ser 0 para o primeiro ponto, ou baseado nos últimos 2 pontos).
# previous_flood_event_in_region: Simula (0 ou 1, aqui 0 para não ter impacto direto do sensor).
# Em um cenário real, estas features seriam calculadas ou obtidas de outras fontes.
newdata_for_prediction <- data.frame(
  water_level_avg_24h = current_water_level,
  rainfall_total_24h = current_rainfall_intensity,
  water_level_change_12h = 0, # Placeholder. Em um sistema real, calculava-se do histórico.
  previous_flood_event_in_region = 0 # Placeholder. Em um sistema real, seria uma flag externa.
)

# Prever a categoria de risco usando o modelo treinado.
predicted_risk_category <- predict(m_flood_risk, newdata = newdata_for_prediction)
risk_level <- as.character(predicted_risk_category[1])

# --- Previsão de Níveis Futuros (Exemplo com ARIMA para séries temporais) ---
# Se você tiver dados de séries temporais suficientes no current_sensor_data, pode fazer previsões.
# Aqui, é um exemplo simplificado para a POC.
predicted_water_level <- NA
predicted_rainfall <- NA

# Se houver dados suficientes para uma série temporal básica (min. 5-10 pontos)
if (nrow(current_sensor_data) >= 5) {
  # Cria uma série temporal com os últimos N níveis de água.
  # Frequência 1 significa que os dados são sequenciais, sem sazonalidade por enquanto.
  ts_water <- ts(current_sensor_data$water_level, frequency = 1)
  # Previsão com ARIMA (AutoRegressive Integrated Moving Average).
  # auto.arima tenta encontrar o melhor modelo ARIMA automaticamente.
  fit_water <- auto.arima(ts_water)
  forecast_water <- forecast(fit_water, h = 1) # Prever 1 período à frente.
  predicted_water_level <- round(forecast_water$mean[1], 2) # Pega o valor previsto.

  ts_rainfall <- ts(current_sensor_data$rainfall_intensity, frequency = 1)
  fit_rainfall <- auto.arima(ts_rainfall)
  forecast_rainfall <- forecast(fit_rainfall, h = 1)
  predicted_rainfall <- round(forecast_rainfall$mean[1], 2)
} else {
  # Se não há dados suficientes para ARIMA, use os últimos valores.
  predicted_water_level <- current_water_level
  predicted_rainfall <- current_rainfall_intensity
}


# --- Criar o Objeto JSON de Saída ---
# Este JSON será lido pelo script Python.
output_data <- list(
  risk_level = risk_level,
  predicted_water_level = predicted_water_level,
  predicted_rainfall = predicted_rainfall,
  timestamp_analysis = format(Sys.time(), "%Y-%m-%dT%H:%M:%S")
)

# --- Salvar o Resultado em JSON ---
write_json(output_data, output_file, auto_unbox = TRUE)

message(paste("Análise de enchente concluída. Risco:", risk_level))

