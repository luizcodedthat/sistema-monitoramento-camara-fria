from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone

class Esp32Payload(BaseModel):
    device_id: str
    # Se o ESP32 não enviar o campo 'timestamp', o Pydantic assume o 'agora' em UTC
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    temperature_internal: float
    humidity_internal: float

class DashboardSimulatedState(BaseModel):
    temperature_external: float
    humidity_external: float
    door_state: str = Field(pattern="^(open|closed)$")

class Thresholds(BaseModel):
    temp_min: float = 19.0   # Temperatura mínima aceitável (°C)
    temp_max: float = 25.0   # Temperatura máxima aceitável (°C)
    hum_min: float = 60.0   # Umidade mínima aceitável (%)
    hum_max: float = 85.0   # Umidade máxima aceitável (%)

class AnomalyResult(BaseModel):
    label: str
    score: float

# Bug corrigido: thresholds adicionado ao schema.
# Estava sendo passado pelo data_service mas ignorado silenciosamente pelo Pydantic,
# fazendo o campo sumir da resposta da API.
class ConsolidatedResponse(BaseModel):
    current: dict
    anomaly: AnomalyResult
    thresholds: Thresholds

class LLMAnalysisResponse(BaseModel):
    analysis: str
    inferred_causes: list[str]
