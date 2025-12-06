from flask import Blueprint, request, jsonify
from app.services.ai_service import AIService

classify_bp = Blueprint('classify', __name__, url_prefix='/api')

@classify_bp.route('/classify', methods=['POST'])
def classify():
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
        return jsonify({"error": str(e)}), 500