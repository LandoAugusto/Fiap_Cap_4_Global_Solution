# r_analysis/fire_analysis.R
# Este script realiza a análise de risco de incêndio usando dados históricos para treinamento
# de um modelo de Machine Learning e aplicando-o aos dados atuais dos sensores.

# --- Instalação de Pacotes (se ainda não tiver) ---
# A linha abaixo deve ser executada uma vez no RStudio, não no script.
# install.packages(c("jsonlite", "randomForest", "dplyr", "forecast"))

library(jsonlite)     # Para ler e escrever arquivos JSON.
library(dplyr)        # Para manipulação de dados.
library(forecast)     # Para modelos de séries temporais (previsão de temperatura/fumaça).
library(randomForest) # Para o modelo Random Forest, usado para classificação de risco de incêndio.


# --- Argumentos de Linha de Comando ---
args <- commandArgs(trailingOnly = TRUE)
input_file <- args[1] # Ex: "r_analysis/temp_data/fire_data_for_r.csv"
output_file <- args[2] # Ex: "r_analysis/temp_data/fire_risk_output.json"

# --- Carregar Dados Atuais dos Sensores ---
if (!file.exists(input_file)) {
  stop(paste("ERRO: Arquivo de entrada de dados atuais não encontrado:", input_file))
}
current_sensor_data <- read.csv(input_file)
current_sensor_data$timestamp <- as.POSIXct(current_sensor_data$timestamp)

if (nrow(current_sensor_data) == 0) {
  output_data <- list(
    risk_level = "Baixo",
    predicted_temperature = NA,
    predicted_smoke = NA,
    timestamp_analysis = format(Sys.time(), "%Y-%m-%dT%H:%M:%S"),
    message = "Dados insuficientes para análise preditiva."
  )
  write_json(output_data, output_file, auto_unbox = TRUE)
  quit(save = "no")
}

# --- Carregar Dados Históricos para Treinamento do Modelo de ML ---
historical_data_path <- "/../r_analysis/datasets/historical_fire_data.csv"
if (!file.exists(historical_data_path)) {
  stop(paste("ERRO: Arquivo de dados históricos não encontrado:", historical_data_path))
}
historical_fire_data <- read.csv(historical_data_path)
historical_fire_data$timestamp <- as.POSIXct(historical_fire_data$timestamp)

# --- Preparação de Dados para o Modelo de ML ---
historical_fire_data$fire_risk_category <- factor(
  historical_fire_data$fire_risk_category,
  levels = c("Baixo", "Moderado", "Alto", "Muito Alto")
)

# --- Treinamento do Modelo de Machine Learning (Random Forest) ---
set.seed(456) # Para reprodutibilidade
m_fire_risk <- randomForest(
  fire_risk_category ~ temperature_avg_24h + humidity_avg_24h + wind_speed_avg_24h + vegetation_dryness_index + smoke_concentration_avg_6h,
  data = historical_fire_data,
  ntree = 100
)
message("Modelo Random Forest para incêndios treinado com sucesso.")

# --- Realizar Previsões para Dados Atuais ---
latest_sensor_data <- tail(current_sensor_data, 1)

current_temperature <- latest_sensor_data$temperature
current_humidity <- latest_sensor_data$humidity
current_smoke_concentration <- latest_sensor_data$smoke_concentration

# Simula as features para a previsão (assumindo que wind_speed e vegetation_dryness não vêm do sensor diretamente)
# Em um sistema real, você teria estas informações de outras fontes ou calculadas.
newdata_for_prediction <- data.frame(
  temperature_avg_24h = current_temperature,
  humidity_avg_24h = current_humidity,
  wind_speed_avg_24h = 10, # Placeholder. Assumir um valor médio/constante para a simulação.
  vegetation_dryness_index = 0.5, # Placeholder. Assumir um valor médio/constante.
  smoke_concentration_avg_6h = current_smoke_concentration
)

predicted_risk_category <- predict(m_fire_risk, newdata = newdata_for_prediction)
risk_level <- as.character(predicted_risk_category[1])

# --- Previsão de Níveis Futuros (Exemplo com ARIMA) ---
predicted_temperature <- NA
predicted_smoke <- NA

if (nrow(current_sensor_data) >= 5) {
  ts_temp <- ts(current_sensor_data$temperature, frequency = 1)
  fit_temp <- auto.arima(ts_temp)
  forecast_temp <- forecast(fit_temp, h = 1)
  predicted_temperature <- round(forecast_temp$mean[1], 2)

  ts_smoke <- ts(current_sensor_data$smoke_concentration, frequency = 1)
  fit_smoke <- auto.arima(ts_smoke)
  forecast_smoke <- forecast(fit_smoke, h = 1)
  predicted_smoke <- round(forecast_smoke$mean[1], 2)
} else {
  predicted_temperature <- current_temperature
  predicted_smoke <- current_smoke_concentration
}

# --- Criar o Objeto JSON de Saída ---
output_data <- list(
  risk_level = risk_level,
  predicted_temperature = predicted_temperature,
  predicted_smoke = predicted_smoke,
  timestamp_analysis = format(Sys.time(), "%Y-%m-%dT%H:%M:%S")
)

# --- Salvar o Resultado em JSON ---
write_json(output_data, output_file, auto_unbox = TRUE)

message(paste("Análise de incêndio concluída. Risco:", risk_level))
