import httpx
import logging
from ..core.config import settings

# Configuração básica de logger para facilitar o rastreio de erros
logger = logging.getLogger(__name__)

class LLMService:
    async def analyze_anomaly_context(self, current_data: dict, anomaly_data: dict) -> str:
        """
        Envia o contexto da anomalia para a APIFreeLLM avaliar causas e efeitos,
        retornando uma interpretação em linguagem natural.
        """
        prompt = f"""
        Você é um analista de dados especialista em refrigeração industrial.
        Analise o seguinte evento da câmara fria e infira causas e efeitos em linguagem natural.
        
        Dados atuais: {current_data}
        Classificação do Isolation Forest: {anomaly_data}
        
        Responda de forma concisa explicando a possível causa raiz desta anomalia e o impacto imediato. Não use markdown.
        """

        headers = {
            "Authorization": f"Bearer {settings.API_FREE_LLM_KEY}",
            "Content-Type": "application/json"
        }
        
        # Novo formato de payload de acordo com o contrato da API
        payload = {
            "message": prompt
        }

        # Utilizamos httpx.AsyncClient para não bloquear a thread principal do FastAPI
        # O timeout foi ajustado para 60 segundos por conta do "delaySeconds: 25" do tier free
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    settings.API_FREE_LLM_URL, 
                    json=payload, 
                    headers=headers
                )
                response.raise_for_status()
                result = response.json()
                
                # Validação estrutural baseada no novo contrato de resposta
                if result.get("success") is True:
                    return result.get("response", "Análise concluída, mas nenhuma resposta de texto foi retornada.")
                else:
                    logger.error(f"APIFreeLLM retornou sucesso=false. Payload de resposta: {result}")
                    return "Falha na análise: A APIFreeLLM não conseguiu processar a solicitação."
                    
            except httpx.RequestError as exc:
                logger.error(f"Erro de rede ao conectar com APIFreeLLM: {exc}")
                return "Indisponibilidade temporária no serviço de análise de IA."
            except httpx.HTTPStatusError as exc:
                logger.error(f"APIFreeLLM retornou erro HTTP {exc.response.status_code}: {exc.response.text}")
                return f"Erro de integração com a IA (Status {exc.response.status_code})."

llm_service = LLMService()