from flask import Blueprint, request, jsonify
from app.services.ai_service import AIService
import logging

logger = logging.getLogger(__name__)

classify_bp = Blueprint('classify', __name__, url_prefix='/api')

@classify_bp.route('/classify', methods=['POST'])
def classify():
    """
    Classify a given text using the specified model.

    Request Body:
        - text (str): The text to classify.
        - model (str, optional): The model to use ('bert' or 'gpt'). Defaults to 'bert'.

    Responses:
        - 200: Classification result as JSON.
        - 400: Missing or invalid input.
        - 500: Internal server error.
    """
    data = request.get_json()
    text = data.get('text')
    model_type = data.get('model', 'bert').lower()

    if not text:
        return jsonify({"error": "Texto requerido"}), 400

    try:
        if model_type == 'gpt':
            result = AIService.classify_gpt(text)
        else:
            result = AIService.classify_bert(text)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error processing classification: {e}", exc_info=True)
        return jsonify({"error": "Internal Server Error"}), 500