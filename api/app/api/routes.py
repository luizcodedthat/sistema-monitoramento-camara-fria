from fastapi import APIRouter, HTTPException
from ..schemas.payloads import (
    Esp32Payload, 
    DashboardSimulatedState, 
    ConsolidatedResponse,
    LLMAnalysisResponse
)
from ..services.data_service import data_service
from ..services.llm_service import llm_service

router = APIRouter()

@router.post("/esp32/reading", response_model=ConsolidatedResponse, tags=["IoT"])
async def receive_reading(payload: Esp32Payload):
    """Recebe os dados reais do hardware ESP32 e processa anomalias."""
    return data_service.process_esp32_reading(payload)

@router.post("/dashboard/simulate", tags=["Dashboard"])
async def update_simulation(payload: DashboardSimulatedState):
    """Atualiza as variáveis mockadas via interface do usuário."""
    state = data_service.update_simulated_state(payload)
    return {"message": "Estado simulado atualizado", "current_state": state}

@router.get("/dashboard/current", tags=["Dashboard"])
async def get_current_data():
    """Retorna o estado consolidado mais recente para a Dashboard."""
    return data_service.get_latest_state()

@router.get("/analysis/llm", response_model=LLMAnalysisResponse, tags=["AI Analysis"])
async def get_llm_analysis():
    """Solicita à APIFreeLLM uma análise em linguagem natural da última leitura."""
    latest_state = data_service.get_latest_state()
    
    if "message" in latest_state:
        raise HTTPException(status_code=400, detail="Sem dados para analisar.")
    
    analysis_text = await llm_service.analyze_anomaly_context(
        current_data=latest_state["current"],
        anomaly_data=latest_state["anomaly"]
    )
    
    return LLMAnalysisResponse(
        analysis=analysis_text,
        inferred_causes=["Ganho térmico por porta aberta", "Alta temperatura ambiente"] # Mock
    )