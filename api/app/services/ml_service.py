import joblib
import pandas as pd
from pathlib import Path
from datetime import datetime
from collections import deque
from ..schemas.payloads import AnomalyResult
import logging

logger = logging.getLogger(__name__)

# Ordem EXATA das features usada no treinamento (isolationforest_v3.py → FEATURES).
# Deve ser mantida em sincronia com o script de treino ao re-treinar o modelo.
FEATURE_NAMES = [
    "temp_interna",
    "umidade_interna",
    "porta_aberta_min",
    "temp_externa",
    "umidade_externa",
    "hora_leitura",
    "residual_temp",
    "temp_delta",
    "taxa_variacao_temp",
    "interacao_porta_temp",
]


class MLService:
    def __init__(self):
        model_path = Path(__file__).resolve().parent.parent / "model" / "isolation_forest_model.joblib"

        try:
            self.model = joblib.load(model_path)
            logger.info(f"Modelo carregado de: {model_path}")
        except FileNotFoundError:
            logger.warning(f"Modelo não encontrado em {model_path}. Usando fallback.")
            self.model = None

        # Histórico das últimas 5 temperaturas internas para calcular
        # taxa_variacao_temp como rolling mean dos diffs (janela 4 leituras = 1 h),
        # espelhando exatamente o que foi feito no treino em add_contextual_features().
        self._temp_history: deque[float] = deque(maxlen=5)

    def _build_features(
        self,
        internal_temp: float,
        internal_hum: float,
        external_temp: float,
        external_hum: float,
        porta_aberta_min: float,
    ) -> list[float]:
        hora_leitura = datetime.now().hour + datetime.now().minute / 60.0

        # residual_temp: quanto a temperatura real desvia do esperado dado o contexto.
        # Usa os mesmos coeficientes do gerador de dados de treino.
        # Em produção futura: substituir pela regressão linear calibrada por câmara.
        temp_esperada = 22.0 + 0.1 * (external_temp - 26) + 0.05 * porta_aberta_min
        residual_temp = internal_temp - temp_esperada

        temp_delta = internal_temp - external_temp

        # taxa_variacao_temp: rolling mean dos diffs de temperatura interna.
        # Espelha o .diff().rolling(window=4).mean() do treino,
        # aplicado aqui de forma incremental leitura a leitura.
        self._temp_history.append(internal_temp)
        if len(self._temp_history) >= 2:
            diffs = [
                self._temp_history[i] - self._temp_history[i - 1]
                for i in range(1, len(self._temp_history))
            ]
            taxa_variacao_temp = sum(diffs) / len(diffs)
        else:
            taxa_variacao_temp = 0.0  # fallback na primeira leitura

        interacao_porta_temp = porta_aberta_min * internal_temp

        # Ordem OBRIGATÓRIA — deve espelhar FEATURE_NAMES acima.
        return [
            internal_temp,          # temp_interna
            internal_hum,           # umidade_interna
            porta_aberta_min,       # porta_aberta_min
            external_temp,          # temp_externa
            external_hum,           # umidade_externa
            hora_leitura,           # hora_leitura
            residual_temp,          # residual_temp
            temp_delta,             # temp_delta
            taxa_variacao_temp,     # taxa_variacao_temp
            interacao_porta_temp,   # interacao_porta_temp
        ]

    def evaluate_reading(
        self,
        internal_temp: float,
        internal_hum: float,
        external_temp: float,
        external_hum: float,
        porta_aberta_min: float,
    ) -> AnomalyResult:

        if self.model is None:
            return self._mock_evaluation(internal_temp, porta_aberta_min)

        features = self._build_features(
            internal_temp,
            internal_hum,
            external_temp,
            external_hum,
            porta_aberta_min,
        )

        # Usa FEATURE_NAMES local em vez de self.model.feature_names_in_
        # para funcionar também no modo fallback e tornar a dependência explícita.
        df_input = pd.DataFrame([features], columns=FEATURE_NAMES)

        prediction = self.model.predict(df_input)[0]
        anomaly_score = float(self.model.decision_function(df_input)[0])

        if prediction == -1:
            label = "anômala" if anomaly_score < -0.1 else "suspeita"
        else:
            label = "normal"

        return AnomalyResult(label=label, score=anomaly_score)

    def _mock_evaluation(self, internal_temp: float, porta_aberta_min: float) -> AnomalyResult:
        if porta_aberta_min > 2.0 and internal_temp > 8.0:
            return AnomalyResult(label="anômala", score=-0.85)
        return AnomalyResult(label="normal", score=0.15)


ml_service = MLService()
