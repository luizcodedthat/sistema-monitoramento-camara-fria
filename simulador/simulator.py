import time
import random
import requests
import logging

# Configuração de log para o terminal
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Esp32Simulator:
    def __init__(self, base_url: str, device_id: str):
        self.base_url = base_url
        self.device_id = device_id
        
        # Estado inicial interno
        self.current_internal_temp = 22.0
        self.current_internal_hum = 80.0

    def setup_external_environment(self):
        """
        Injeta no backend os valores climáticos padrões da Mata Sul de Pernambuco.
        (Palmares/PE no mês de Junho: ~26°C e umidade ~88%)
        """
        url = f"{self.base_url}/dashboard/simulate"
        payload = {
            "temperature_external": 26.0,
            "humidity_external": 88.0,
            "door_state": "closed"
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            logging.info(f"Ambiente externo configurado (Mata Sul/PE): {payload}")
        except requests.RequestException as e:
            logging.error(f"Falha ao configurar ambiente externo: {e}")

    def simulate_reading(self):
        """
        Gera pequenas flutuações na temperatura e na umidade interna.
        A umidade varia de forma ligeiramente inversa à temperatura em um ambiente fechado,
        mas aqui manteremos uma correlação simples e proporcional.
        """
        # Flutuação de temperatura entre -0.3 e +0.3 graus
        temp_delta = random.uniform(-0.3, 0.3)
        self.current_internal_temp += temp_delta
        
        # Garante que a temperatura fique próxima aos 22°C
        self.current_internal_temp = max(20.0, min(24.0, self.current_internal_temp))
        
        # Ajuste proporcional de umidade (+ temp, - umidade relativa e vice-versa)
        hum_delta = temp_delta * -1.5 + random.uniform(-0.5, 0.5)
        self.current_internal_hum += hum_delta
        
        # Limita a umidade entre 75% e 85%
        self.current_internal_hum = max(75.0, min(85.0, self.current_internal_hum))

    def send_reading(self):
        """
        Envia o payload formatado conforme o contrato da API.
        """
        url = f"{self.base_url}/esp32/reading"
        payload = {
            "device_id": self.device_id,
            "temperature_internal": round(self.current_internal_temp, 2),
            "humidity_internal": round(self.current_internal_hum, 2)
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            anomaly_label = data.get("anomaly", {}).get("label", "desconhecido")
            logging.info(f"Enviado: {payload} | Status da Anomalia: {anomaly_label.upper()}")
        except requests.RequestException as e:
            logging.error(f"Falha ao enviar leitura do ESP32: {e}")

    def run(self, interval_seconds: int = 5):
        """
        Inicia o loop infinito de envio de dados.
        """
        logging.info("Iniciando simulador do ESP32...")
        self.setup_external_environment()
        
        try:
            while True:
                self.simulate_reading()
                self.send_reading()
                time.sleep(interval_seconds)
        except KeyboardInterrupt:
            logging.info("Simulador encerrado pelo usuário.")

if __name__ == "__main__":
    # URL base da sua API FastAPI local
    API_BASE_URL = "http://localhost:8000/api/v1"
    
    simulator = Esp32Simulator(base_url=API_BASE_URL, device_id="esp32-camara-fria-01")
    simulator.run(interval_seconds=3)