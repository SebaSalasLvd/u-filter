from transformers import pipeline
from openai import OpenAI
import torch
import logging
import os

logger = logging.getLogger(__name__)

class AIService:
    """
    Service for handling AI-based text classification using pre-trained models.
    """

    _pipeline = None
    _model_path = "Recognai/bert-base-spanish-wwm-cased-xnli"

    @classmethod
    def get_pipeline(cls):
        """
        Lazily load the BERT model pipeline (Singleton pattern).

        Returns:
            Pipeline: The zero-shot classification pipeline.
        """
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
        """
        Classify text using the BERT zero-shot classification model.

        Args:
            text (str): The input text to classify.

        Returns:
            dict: Classification result with the top label, score, and model name.

        Raises:
            Exception: If the model pipeline is not available.
        """
        classifier = AIService.get_pipeline()
        if not classifier:
            raise Exception("No disponible")
        
        candidate_labels = ["Venta", "Compra", "Arriendo", "Clases Particulares", "Oferta laboral/practica"]
        result = classifier(text, candidate_labels)
        
        threshold = 0.5
        top_label = result['labels'][0]
        top_score = result['scores'][0]

        if top_score < threshold:
            top_label = "Otro"

        return {
            "label": top_label,
            "score": top_score,
            "model": "bert"
        }

    @staticmethod
    def classify_gpt(text):
        pass