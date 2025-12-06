from flask import Blueprint, request, jsonify
from app.services.scraper_service import ScraperService
from app.models.post import Post
from app.models.link import Link
import logging

logger = logging.getLogger(__name__)

scraper_bp = Blueprint('scraper', __name__, url_prefix='/api/scraper')

@scraper_bp.route('/run', methods=['POST'])
def run_scraper():
    data = request.get_json()
    domain = data.get('domain')
    if not domain:
        return jsonify({"error": "Domain es requerido"}), 400
    
    try:
        result = ScraperService.run_scraper(domain)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@scraper_bp.route('/run-all', methods=['POST'])
def run_scraper_all():
    try:
        links = Link.query.all()
        
        if not links:
            return jsonify({"message": "No hay links registrados en la base de datos."}), 200

        results = []
        errors = []

        logger.info(f"Iniciando scraping masivo para {len(links)} foros.")

        for link in links:
            try:
                logger.info(f"Procesando: {link.url}")
                scrape_result = ScraperService.run_scraper(link.url)
                
                results.append({
                    "url": link.url,
                    "status": "success",
                    "details": scrape_result
                })
            except Exception as e:
                logger.error(f"Error scrapeando {link.url}: {e}")
                errors.append({
                    "url": link.url,
                    "status": "error",
                    "error": str(e)
                })

        return jsonify({
            "message": "Proceso masivo finalizado",
            "total_links": len(links),
            "successful": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors
        })

    except Exception as e:
        logger.error(f"Error crítico en run-all: {e}")
        return jsonify({"error": str(e)}), 500

@scraper_bp.route('/list', methods=['GET'])
def list_posts_by_domain():
    domain = request.args.get('domain')
    
    query = Post.query.join(Link).order_by(Post.created_at.desc())
    
    if domain:
        query = query.filter(Link.url.contains(domain))
        
    posts = query.limit(100).all()
    
    output = []
    for post in posts:
        output.append({
            "id": post.id,
            "title": post.title,
            "user": post.author,
            "date": post.post_date,
            "url": post.post_url,
            "label": post.classification_label,
            "score": post.classification_score,
            "text": post.content,
            "created_at": post.created_at.isoformat()
        })
        
    return jsonify(output)