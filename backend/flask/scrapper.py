import time
import re
import psycopg2
import torch
from transformers import pipeline
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# --- CONFIGURACIÓN ---
USUARIO_UCURSOS = "usuario"
CLAVE_UCURSOS   = "contraseña"
MODEL_PATH = "/Users/inost/Documents/universidad/2025/proyecto_ia/entrenamiento/modelo_finetuned_ufilter"
TIEMPO_ENTRE_EJECUCIONES = 3600 

PG_CONFIG = {
    "dbname": "proyecto",
    "user": "postgres",
    "password": "password",
    "host": "localhost",
    "port": "5432"
}


try:
    classifier = pipeline(
        "text-classification",
        model=MODEL_PATH,
        tokenizer=MODEL_PATH,
        device=0 if torch.cuda.is_available() else -1,
        truncation=True, 
        max_length=512
    )
    print(f"✅ Modelo cargado en: {classifier.device}")
except Exception as e:
    print(f"Error crítico cargando modelo: {e}")
    exit()

def prediccion_modelo(text):
    try:
        results = classifier(text)
        return {"label": results[0]['label'], "score": results[0]['score']}
    except:
        return None

# --- BASE DE DATOS ---

def get_urls_registrados():
    """Obtiene la lista de URLs a scrapear."""
    urls = []
    conn = None
    try:
        conn = psycopg2.connect(**PG_CONFIG)
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT link FROM link_registrados;")
        rows = cur.fetchall()
        # Convertir lista de tuplas [(url1,), (url2,)] a lista simple [url1, url2]
        urls = [row[0] for row in rows]
    except Exception as e:
        print(f"Error obteniendo URLs: {e}")
    finally:
        if conn: conn.close()
    return urls

def get_existing_post_urls():
    """Obtiene los posts que YA existen para no duplicarlos."""
    existing = set()
    conn = None
    try:
        conn = psycopg2.connect(**PG_CONFIG)
        cur = conn.cursor()
        # Crear tabla si no existe
        cur.execute("""
            CREATE TABLE IF NOT EXISTS classifications (
                id BIGSERIAL PRIMARY KEY,
                post_url TEXT UNIQUE,
                title TEXT,
                input_text TEXT,
                author TEXT,
                post_date TIMESTAMPTZ,
                label TEXT,
                score DOUBLE PRECISION,
                post_url_domain TEXT,
                created_at TIMESTAMPTZ DEFAULT now(),
                updated_at TIMESTAMPTZ DEFAULT now()
            );
        """)
        conn.commit()
        cur.execute("SELECT post_url FROM classifications")
        for row in cur.fetchall():
            if row[0]: existing.add(row[0])
    except Exception as e:
        print(f"Error BD Init: {e}")
    finally:
        if conn: conn.close()
    return existing



def guardar_datos_masivo(rows):
    """Guarda toda la lista de datos recolectados de una sola vez."""
    if not rows:
        print("No hay datos nuevos para guardar.")
        return

    print(f"Guardando {len(rows)} registros en Base de Datos...")
    conn = None
    try:
        conn = psycopg2.connect(**PG_CONFIG)
        cur = conn.cursor()
        sql = """
            INSERT INTO classifications (author, title, input_text, post_url, label, score, post_url_domain, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, now(), now())
            ON CONFLICT (post_url) DO NOTHING;
        """
        cur.executemany(sql, rows)
        conn.commit()
        print("Guardado exitoso.")
    except Exception as e:
        print(f"Error SQL: {e}")
    finally:
        if conn: conn.close()

# --- 3. LÓGICA DEL SCRAPER ---

def iniciar_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # options.add_argument("--headless") 
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def login_ucursos(driver):
    """Realiza el login una única vez."""
    print("Iniciando sesión en U-Cursos...")
    driver.get("https://www.u-cursos.cl/")
    
    wait = WebDriverWait(driver, 10)
    try:
        wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(USUARIO_UCURSOS)
        driver.find_element(By.NAME, "password").send_keys(CLAVE_UCURSOS + Keys.RETURN)
        time.sleep(5) # Esperar redirección
        
        if "Visitante" in driver.page_source:
            print("Login fallido (Checkea credenciales)")
            return False
        print("Login correcto.")
        return True
    except Exception as e:
        print(f"Error en login: {e}")
        return False

def procesar_ciclo_completo():
    # 1. OBTENER URLS OBJETIVO
    target_urls = get_urls_registrados()
    if not target_urls:
        print("⚠️ No hay URLs registradas en la tabla 'link_registrados'.")
        return

    # 2. OBTENER LINKS YA PROCESADOS (Para evitar duplicados)
    saved_links = get_existing_post_urls()
    
    # Lista para acumular TODOS los datos de TODAS las urls
    todos_los_datos = []

    driver = iniciar_driver()
    
    try:
        # 3. LOGIN 
        if not login_ucursos(driver):
            driver.quit()
            return

        # 4. ITERAR URLS REGISTRADA
        for index, domain_url in enumerate(target_urls):
            print(f"\n[{index+1}/{len(target_urls)}] Scrapeando: {domain_url}")
            
            try:
                # Paginación interna (ej: revisar primeras 3 páginas del foro) cambiar a lo necesario
                for offset in range(0, 3): 
                    # Construcción de URL con offset 
                    url_paginada = f"{domain_url}?id_tema=&offset={offset}"
                    driver.get(url_paginada)
                    time.sleep(2) # Espera cortés

                    soup = BeautifulSoup(driver.page_source, 'html.parser')
                    mensajes = soup.find_all('div', class_='new') or soup.find_all('div', class_='msg')

                    if not mensajes: 
                        print("   No hay más mensajes en esta paginación.")
                        break

                    for mensaje in mensajes:
                        # --- Extracción de datos (Misma lógica que tenías) ---
                        content_divs = [div for div in mensaje.find_all('div', class_='msg') if 'hijo' not in div.get('class', [])]
                        
                        for content in content_divs:
                            link_tag = content.find('a', class_='permalink')
                            link = link_tag['href'] if link_tag else None
                            
                            # Validar existencia previa
                            if not link or link in saved_links: continue 

                            txt_tag = content.find('span', class_='ta')
                            texto = txt_tag.get_text(separator="\n", strip=True) if txt_tag else ""
                            if not texto or texto == "Sin mensaje": continue

                            # Clasificar
                            pred = prediccion_modelo(texto)
                            if not pred: continue

                            # Metadata
                            titulo_tag = mensaje.find('a', id='mensaje-titulo')
                            titulo = titulo_tag.text.strip() if titulo_tag else "Sin titulo"
                            
                            autor_tag = content.find('a', class_='usuario')
                            autor = autor_tag.text.strip() if autor_tag else "Anon"
                            
                            # Agregar a la lista MASIVA
                            todos_los_datos.append((autor, titulo, texto, link, pred['label'], pred['score'], domain_url))
                            
                            # Agregar a saved_links temporalmente para no repetir en este mismo ciclo
                            saved_links.add(link) 
                            
                            print(f" Recolectado: {pred['label']} - {titulo[:20]}...")

            except Exception as e:
                print(f"Error procesando URL {domain_url}: {e}")
                # Continuamos con la siguiente URL, no paramos todo el proceso
                continue

    except Exception as main_e:
        print(f"Error crítico en el proceso de scraping: {main_e}")
    finally:
        print("Cerrando navegador...")
        driver.quit()

    # 5. FINALMENTE: LLENAR LA BASE DE DATOS
    guardar_datos_masivo(todos_los_datos)


# --- BUCLE PRINCIPAL ---
if __name__ == "__main__":
    while True:
        procesar_ciclo_completo()
        
        print(f"\nCiclo terminado. Esperando {TIEMPO_ENTRE_EJECUCIONES} segundos...")
        time.sleep(TIEMPO_ENTRE_EJECUCIONES)