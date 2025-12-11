from bs4 import BeautifulSoup
from app.extensions import db
from app.models.link import Link
from app.models.post import Post
from app.services.ai_service import AIService
import logging
import os
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)

class ScraperService:
    """
    Service for scraping data from U-Cursos forums and saving it to the database.
    """

    LOGIN_URL = "https://www.u-cursos.cl/upasaporte/adi"

    @staticmethod
    def _init_driver():
        """
        Initialize a headless Chrome WebDriver with optimized options.

        Returns:
            WebDriver: An instance of the Chrome WebDriver.
        """
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--headless") 
        return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    @staticmethod
    def _login(driver):
        """
        Handle login to U-Cursos using Selenium.

        Args:
            driver (WebDriver): The Selenium WebDriver instance.

        Returns:
            bool: True if login was successful, False otherwise.
        """
        username = os.getenv("UCURSOS_USER")
        password = os.getenv("UCURSOS_PASSWORD")

        if not username or not password:
            logger.error("Credenciales no encontradas en .env")
            return False

        try:
            logger.info("Iniciando sesión en U-Cursos...")
            driver.get("https://www.u-cursos.cl/")
            wait = WebDriverWait(driver, 10)
            user_field = wait.until(EC.presence_of_element_located((By.NAME, "username")))
            user_field.clear()
            user_field.send_keys(username)
            
            pass_field = driver.find_element(By.NAME, "password")
            pass_field.clear()
            pass_field.send_keys(password + Keys.RETURN)
            
            time.sleep(5)

            if "Visitante" in driver.page_source:
                logger.error("Login fallido: Aún aparece como Visitante.")
                return False
            
            logger.info("Login exitoso.")
            return True
        except Exception as e:
            logger.error(f"Excepción durante el login: {e}")
            return False

    @staticmethod
    def run_scraper(domain, model):
        """
        Execute the scraping process for a specific domain.

        Args:
            domain (str): The URL of the forum to scrape.
            model (str): The model to use for classification ("bert" or "gpt").

        Returns:
            dict: A summary of the scraping process, including the number of processed posts.
        """
        driver = None
        processed_count = 0
        
        try:
            driver = ScraperService._init_driver()
            
            parent_link = Link.query.filter_by(url=domain).first()

            if not ScraperService._login(driver):
                raise Exception("Fallo en la autenticación con U-Cursos")

            forum_url_base = domain.split('?')[0]
            
            numero_pagina = 0
            seguir = True

            while seguir:
                logger.info(f"Modelo {model}")
                url_paginada = f"{forum_url_base}?id_tema=&offset={numero_pagina}"
                logger.info(f"Scrapeando página {numero_pagina}: {url_paginada}")
                
                driver.get(url_paginada)
                time.sleep(2)

                soup = BeautifulSoup(driver.page_source, 'html.parser')
                
                mensajes = soup.find_all('div', class_='new') or soup.find_all('div', class_='msg')

                if not mensajes or numero_pagina > 5:
                    logger.info("Fin del scraping (sin mensajes o límite alcanzado).")
                    break

                for mensaje in mensajes:
                    titulo_tag = mensaje.find('a', id='mensaje-titulo')
                    titulo = titulo_tag.text.strip() if titulo_tag else "Sin titulo"
                    
                    contenidos = [div for div in mensaje.find_all('div', class_='msg') if 'hijo' not in div.get('class', [])]

                    for contenido in contenidos:
                        link_tag = contenido.find('a', class_='permalink')
                        url = link_tag['href'] if link_tag and link_tag.has_attr('href') else None

                        if not url:
                            continue
                        
                        existing_post = Post.query.filter_by(post_url=url, model_used=model).first()
                        if existing_post:
                            logger.info(f"Post ya existe con el mismo modelo: {url}. Saltando.")
                            continue

                        txt_tag = contenido.find('span', class_='ta')
                        texto = txt_tag.get_text(separator="\n", strip=True) if txt_tag else ""

                        if not texto or texto == "Sin mensaje":
                            continue

                        autor_tag = contenido.find('a', class_='usuario')
                        autor = autor_tag.text.strip() if autor_tag else "Desconocido"

                        fecha_tag = contenido.find('span', class_='tiempo_rel')
                        fecha_raw = fecha_tag.text.strip() if fecha_tag else ""

                        fecha_match = re.search(r'\d{4}-\d{2}-\d{2}(?: \d{2}:\d{2}:\d{2})?', fecha_raw)
                        fecha_texto = fecha_match.group(0) if fecha_match else fecha_raw

                        try:
                            if model == "gpt":
                                classification = AIService.classify_gpt(texto + titulo)
                            else:
                                classification = AIService.classify_bert(texto + titulo)
                        except Exception as e:
                            logger.error(f"Error IA: {e}")
                            classification = {"label": "Error", "score": 0.0, "model": model}

                        try:
                            new_post = Post(
                                title=titulo,
                                content=texto,
                                author=autor,
                                post_date=fecha_texto,
                                post_url=url,
                                classification_label=classification['label'],
                                classification_score=classification['score'],
                                model_used=classification['model'],
                                link_id=parent_link.id if parent_link else None
                            )
                            db.session.add(new_post)
                            db.session.commit()
                            processed_count += 1
                            # logger.info(f"Guardado: {titulo[:30]}... ({classification['label']})")

                        except Exception as e:
                            db.session.rollback()
                            logger.error(f"Error guardando en BD: {e}")

                numero_pagina += 1

        except Exception as e:
            logger.error(f"Error crítico en scraper: {e}")
            return {"error": str(e)}
        finally:
            if driver:
                driver.quit()

        return {"message": "Scraping completado", "processed": processed_count}
    
    @staticmethod
    def run_all_scrapers(model="bert"):
        """
        Ejecuta el scraper para todos los links registrados en la BD.
        Retorna un resumen de la ejecución.

        Args:
            model (str): El modelo a usar para la clasificación ("bert" o "gpt"). Default: "bert".
        """
        logger.info(f"Modelo recibido en scraper_service.py: {model}")
        links = Link.query.all()
        if not links:
            return {"message": "No hay links registrados.", "results": []}

        results = []
        errors = []
        logger.info(f"Iniciando tarea programada: Scraping masivo para {len(links)} foros.")

        for link in links:
            try:
                scrape_result = ScraperService.run_scraper(link.url, model)
                results.append({"url": link.url, "status": "success", "details": scrape_result})
            except Exception as e:
                logger.error(f"Error auto-scraping {link.url}: {e}")
                errors.append({"url": link.url, "status": "error", "error": str(e)})

        return {
            "total": len(links),
            "successful": len(results),
            "failed": len(errors),
            "results": results
        }
