from datetime import datetime, timezone
from ..schemas.payloads import Esp32Payload, DashboardSimulatedState, ConsolidatedResponse, Thresholds
from ..services.ml_service import ml_service

class DataService:
    def __init__(self):
        self.simulated_state = {
            "temperature_external": 25.0,
            "humidity_external": 60.0,
            "door_state": "closed"
        }
        self.last_internal_reading = {}
        self.history = []
        
        self.door_opened_at: datetime | None = None
        self.door_open_count: int = 0
        
        # NOVO: Inicializa os limiares da câmara fria na memória
        self.thresholds = Thresholds()

    def update_simulated_state(self, state: DashboardSimulatedState):
        new_state = state.model_dump()
        old_door = self.simulated_state["door_state"]
        new_door = new_state["door_state"]
        
        if old_door == "closed" and new_door == "open":
            self.door_opened_at = datetime.now(timezone.utc)
            self.door_open_count += 1
        elif new_door == "closed":
            self.door_opened_at = None
            
        self.simulated_state = new_state
        return {
            **self.simulated_state, 
            "door_open_count": self.door_open_count
        }

    def process_esp32_reading(self, payload: Esp32Payload) -> ConsolidatedResponse:
        self.last_internal_reading = payload.model_dump()
        
        porta_aberta_min = 0.0
        if self.simulated_state["door_state"] == "open" and self.door_opened_at:
            delta = datetime.now(timezone.utc) - self.door_opened_at
            porta_aberta_min = delta.total_seconds() / 60.0

        current_context = {
            "temperature_internal": payload.temperature_internal,
            "humidity_internal": payload.humidity_internal,
            "door_open_duration_minutes": round(porta_aberta_min, 2),
            "door_open_count_total": self.door_open_count,
            **self.simulated_state
        }
        
        anomaly = ml_service.evaluate_reading(
            internal_temp=current_context["temperature_internal"],
            internal_hum=current_context["humidity_internal"],
            external_temp=current_context["temperature_external"],
            external_hum=current_context["humidity_external"],
            porta_aberta_min=porta_aberta_min
        )

        # ATUALIZADO: Inclui o objeto thresholds na resposta consolidada
        record = ConsolidatedResponse(
            current=current_context, 
            anomaly=anomaly,
            thresholds=self.thresholds
        )
        
        self.history.append(record.model_dump())
        if len(self.history) > 100:
            self.history.pop(0)

        return record

    def get_latest_state(self) -> dict:
        if not self.history:
            return {"message": "Nenhum dado recebido do ESP32 ainda."}
        return self.history[-1]

data_service = DataService()