from transformers import pipeline
import torch
import logging

logger = logging.getLogger(__name__)

class AIService:
    _pipeline = None
    _model_path = "Recognai/bert-base-spanish-wwm-cased-xnli"

    @classmethod
    def get_pipeline(cls):
        """Carga diferida del modelo (Singleton)"""
        if cls._pipeline is None:
            try:
                cls._pipeline = pipeline(
                    "zero-shot-classification",
                    model=cls._model_path,
                    device=0 if torch.cuda.is_available() else -1
                )
                logger.info("Modelo BERT cargado exitosamente.")
            except Exception as e:
                logger.error(f"Error cargando modelo: {e}")
                return None
        return cls._pipeline

    @staticmethod
    def classify_bert(text):
        classifier = AIService.get_pipeline()
        if not classifier:
            raise Exception("No disponible")
        
        candidate_labels = ["Venta", "Compra", "Arriendo", "Clases", "Otro"]
        result = classifier(text, candidate_labels)
        
        return {
            "label": result['labels'][0],
            "score": result['scores'][0],
            "model": "bert"
        }

    @staticmethod
    def classify_gpt(text):
        # TODO
        return {
            "label": "Simulado_GPT",
            "score": 0.99,
            "model": "gpt"
        }