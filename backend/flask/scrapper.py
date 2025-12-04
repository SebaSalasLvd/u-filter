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
TIEMPO_ENTRE_EJECUCIONES = 3600  # 1 hora en segundos (ajusta esto a tu gusto)

PG_CONFIG = {
    "dbname": "proyecto",
    "user": "postgres",
    "password": "password",
    "host": "localhost",
    "port": "5432"
}

# --- CARGAR MODELO (Solo una vez al inicio) ---
try:
    classifier = pipeline(
        "text-classification",
        model=MODEL_PATH,
        tokenizer=MODEL_PATH,
        device=0 if torch.cuda.is_available() else -1,
        truncation=True,  # <--- Agregar esto
        max_length=512
    )
    print(f"✅ Modelo cargado en: {classifier.device}")
except Exception as e:
    print(f"❌ Error crítico cargando modelo: {e}")
    exit()

def prediccion_modelo(text):
    try:
        results = classifier(text)
        return {"label": results[0]['label'], "score": results[0]['score']}
    except:
        return None

def get_existing_links():
    existing = set()
    conn = None
    try:
        conn = psycopg2.connect(**PG_CONFIG)
        cur = conn.cursor()
        # Asegurar que la tabla existe
        cur.execute("""
            CREATE TABLE IF NOT EXISTS classifications (
                id BIGSERIAL PRIMARY KEY,
                post_url TEXT UNIQUE, -- Agregamos UNIQUE para evitar duplicados a nivel BD
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
        print(f"Error BD: {e}")
    finally:
        if conn: conn.close()
    return existing

def ejecutar_scrapper():
    domain = "u-cursos.cl" # Dominio fijo o dinámico según prefieras
    saved_links = get_existing_links()
    rows = []
    
    print(f"\n--- INICIANDO CICLO DE SCRAPING: {time.strftime('%H:%M:%S')} ---")
    
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # options.add_argument("--headless") # Descomenta para que no se vea el navegador

    driver = None
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.delete_all_cookies()

        driver.get("https://www.u-cursos.cl/ingenieria/2/foro_institucion/")
        
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.NAME, "username"))).send_keys(USUARIO_UCURSOS)
        driver.find_element(By.NAME, "password").send_keys(CLAVE_UCURSOS + Keys.RETURN)
        
        time.sleep(5)

        if "Visitante" in driver.page_source:
            print("❌ Login fallido")
            return

        # Logica simplificada de paginación
        for offset in range(0, 3): # Ejemplo: Revisa las primeras 3 páginas (0, 1, 2)
            print(f"📄 Revisando página {offset}...")
            driver.get(f"https://www.u-cursos.cl/ingenieria/2/foro_institucion/?id_tema=&offset={offset}")
            time.sleep(2)
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            mensajes = soup.find_all('div', class_='new') or soup.find_all('div', class_='msg')

            if not mensajes: break

            for mensaje in mensajes:
                # Extraer Link
                content_divs = [div for div in mensaje.find_all('div', class_='msg') if 'hijo' not in div.get('class', [])]
                for content in content_divs:
                    link_tag = content.find('a', class_='permalink')
                    link = link_tag['href'] if link_tag else None
                    
                    if not link or link in saved_links: continue # Saltar si ya existe

                    # Extraer Texto
                    txt_tag = content.find('span', class_='ta')
                    texto = txt_tag.get_text(separator="\n", strip=True) if txt_tag else ""
                    if not texto or texto == "Sin mensaje": continue

                    # Clasificar
                    pred = prediccion_modelo(texto)
                    if not pred: continue

                    # Extraer Metadata
                    titulo = mensaje.find('a', id='mensaje-titulo').text.strip() if mensaje.find('a', id='mensaje-titulo') else "Sin titulo"
                    autor = content.find('a', class_='usuario').text.strip() if content.find('a', class_='usuario') else "Anon"
                    
                    # Guardar en memoria temporal
                    rows.append((autor, titulo, texto, link, pred['label'], pred['score'], domain))
                    saved_links.add(link) # Para no repetirlo en este mismo ciclo
                    print(f"   Found: {pred['label']} ({pred['score']:.2f}) - {titulo[:30]}...")

    except Exception as e:
        print(f"❌ Error en Selenium: {e}")
    finally:
        if driver: driver.quit()

    # Guardar en BD al final del ciclo
    if rows:
        print(f"💾 Guardando {len(rows)} nuevos posts en BD...")
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
            print("✅ Guardado exitoso.")
        except Exception as e:
            print(f"❌ Error SQL: {e}")
        finally:
            if conn: conn.close()
    else:
        print("💤 No hubo posts nuevos.")

# --- BUCLE PRINCIPAL ---
if __name__ == "__main__":
    while True:
        ejecutar_scrapper()
        print(f"⏳ Esperando {TIEMPO_ENTRE_EJECUCIONES} segundos para la siguiente vuelta...")
        time.sleep(TIEMPO_ENTRE_EJECUCIONES)