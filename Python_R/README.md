# 🌎 Guardião Natural: Sistema Inteligente de Prevenção e Alerta de Desastres

![Diagrama de Arquitetura do Guardião Natural](doc/arquitetura.png) 
_Um sistema integrado para monitoramento e prevenção de desastres naturais._

## 📋 Sobre o Projeto

Este projeto, desenvolvido para a Global Solution 2025.1 da FIAP, propõe uma solução tecnológica para prever, monitorar e mitigar os impactos de eventos naturais extremos, focando inicialmente em **enchentes e incêndios**.

Utilizando dados de sensores em tempo real e aplicando inteligência artificial (Machine Learning e simulação de Large Language Models), o "Guardião Natural" visa fornecer alertas rápidos e inteligentes para a população e autoridades, auxiliando na tomada de decisões e na proteção de vidas e bens.

A imprevisibilidade da natureza exige respostas rápidas e inteligentes, e nossa solução se alinha a esse cenário, transformando dados brutos em informações acionáveis.

## 🚀 Tecnologias Utilizadas

* **ESP32:** Microcontrolador para coleta de dados ambientais em tempo real com diversos sensores.
* **MQTT:** Protocolo de comunicação leve e eficiente para transmissão de dados entre o ESP32 e o servidor.
* **Python:** Linguagem principal para processamento de dados, orquestração do sistema, interação com a lógica de IA e desenvolvimento do Dashboard interativo.
* **R:** Linguagem e ambiente para análise estatística avançada e construção de modelos de Machine Learning para previsão de risco (Random Forest, ARIMA).
* **Large Language Model (LLM - Simulado):** A funcionalidade de geração de alertas em linguagem natural é simulada no código Python para fins de demonstração, representando a capacidade de um LLM real (como Google Gemini ou OpenAI).
* **Streamlit:** Framework Python para criação rápida de dashboards web interativos para visualização dos dados e alertas.
* **Wokwi:** Simulador online para prototipagem e teste do hardware ESP32 e seus sensores.
* **GitHub:** Plataforma para controle de versão e hospedagem do código-fonte.

## ⚙️ Componentes do Sistema

O sistema "Guardião Natural" é composto por três módulos principais:

1.  **Módulo de Sensores (ESP32 - Simulado no Wokwi):**
    * **Sensores de Enchente:** Sensor Ultrassônico (nível de água) e Photoresistor (intensidade da chuva).
    * **Sensores de Incêndio:** DHT22 (temperatura e umidade) e MQ-2 (concentração de fumaça/gás).
    * **Saída:** OLED SSD1306 para visualização local e LED de alerta.
    * **Comunicação:** Envio de dados em JSON via MQTT para o servidor central.

2.  **Módulo de Processamento e Inteligência (Python/R):**
    * **Servidor de Dados (`data_processor.py`):** Recebe dados MQTT, armazena, e coordena a análise.
    * **Análise Preditiva (R):** Scripts (`flood_analysis.R`, `fire_analysis.R`) utilizam modelos de Machine Learning (e.g., Random Forest, ARIMA) treinados com dados históricos (simulados baseados em `disasterscharter.org`) para prever o risco de desastre.
    * **Geração de Alertas (LM Simulado):** A função de gerar mensagens de alerta dinâmicas e acionáveis é simulada no código Python, demonstrando o potencial de um LLM real para criar comunicações humanizadas com base nos níveis de risco previstos.

3.  **Módulo de Visualização (Dashboard Streamlit):**
    * Interface web interativa que exibe dados dos sensores em tempo real, gráficos de tendências e os alertas de risco gerados pelo sistema, fornecendo uma visão clara da situação.
