import requests
import re
import csv
from bs4 import BeautifulSoup
import psycopg2  # NUEVO (POSTGRES): Importamos psycopg2 en lugar de sqlite3

# ---Configuración de la Base de Datos ---
# Modifica estos valores con los que creaste en el Paso 1
PG_CONFIG = {
    "dbname": "ucursos_db",
    "user": "scraper_user",
    "password": "tu_password_seguro_aqui",
    "host": "localhost",  # IP
    "port": "5432"        # Puerto por defecto de Postgres
}

# --- NUEVO (POSTGRES): Función para obtener links existentes de la BD ---
def get_existing_links():
    """
    Se conecta a la base de datos PostgreSQL y obtiene un set de todos los
    links de la tabla 'mensajes' para evitar duplicados.
    """
    existing_links = set()
    conn = None  # Inicia la conexión como None
    try:
        # Conectarse a la BD de Postgres
        conn = psycopg2.connect(**PG_CONFIG)
        cursor = conn.cursor()
        
        # Asegurarse de que la tabla exista 
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS mensajes (
            id SERIAL PRIMARY KEY,
            autor TEXT,
            titulo TEXT,
            fecha TEXT,
            contenido TEXT,
            link TEXT UNIQUE NOT NULL
        )
        """)
        conn.commit() # Guardar la creación de la tabla
        
        # Obtener todos los links
        cursor.execute("SELECT link FROM mensajes")
        links = cursor.fetchall()
        
        # Añadirlos al set (fila[0] es el primer campo)
        for fila in links:
            if fila[0]:
                existing_links.add(fila[0])
                
        print(f"Se cargaron {len(existing_links)} links existentes desde la BD Postgres.")

    except (Exception, psycopg2.Error) as e:
        print(f"Error al leer links de la BD Postgres: {e}")
    finally:
        if conn:
            conn.close()
            
    return existing_links



# url objetivo
login_url = "https://www.u-cursos.cl/upasaporte/adi"

# datos usuario y contraseña
login_data = {
    "servicio": "ucursos",
    "debug": "0",
    "extras[_LB]": "ucursos03-int",
    "extras[lang]": "es",
    "extras[_sess]": "dc57oo5eb9fd48pshd67cen9r1",
    "extras[recordar]": "1",
    "username": "usuario",
    "password": "contraseña",
    "recordar": "1"
}

# NUEVO: Cargar los links que ya tenemos ANTES de empezar
saved_links = get_existing_links()

session = requests.Session()
response = session.post(login_url, data=login_data)
rows = []

if response.status_code == 200:
    print("Login exitoso!")

    forum_url_base = 'https://www.u-cursos.cl/ingenieria/2/foro_institucion/'
    numero_pagina = 0
    seguir = True
    while seguir:
        forum_url = f"{forum_url_base}?id_tema=&offset={numero_pagina}"
        print(f"Obteniendo offset = {numero_pagina} …")
        forum_page = session.get(forum_url)

        soup = BeautifulSoup(forum_page.text, 'html.parser')

        mensajes = [
            div for div in soup.find_all('div', class_='new')
        ]
        if mensajes and numero_pagina < 735:
            print(f"scrapeando pagina {numero_pagina}")
        else:
            print("No se encontraron más mensajes o se alcanzó el límite.")
            break

        for mensaje in mensajes:
            titulo_tag = mensaje.find('a', id='mensaje-titulo')
            titulo = titulo_tag.text.strip() if titulo_tag else "Sin titulo"
            contenidos = [
                div for div in mensaje.find_all('div', class_='msg')
                if 'hijo' not in div.get('class', [])
            ]

            for contenido in contenidos:
                autor_tag = contenido.find('a', class_='usuario')
                autor = autor_tag.text.strip() if autor_tag else "Desconocido"
                fecha_tag = contenido.find('span', class_='tiempo_rel')
                fecha_texto_completo = fecha_tag.text.strip() if fecha_tag else "0000-00-00"
                fecha_match = re.search(r'\b\d{4}-\d{2}-\d{2}\b', fecha_texto_completo)
                fecha_sql = fecha_match.group() if fecha_match else "0000-00-00"
                texto_tag = contenido.find('span', class_='ta')
                texto = texto_tag.get_text(separator="\n", strip=True) if texto_tag else "Sin mensaje"
                link_tag = contenido.find('a', class_='permalink')
                link = link_tag['href'] if link_tag and link_tag.has_attr('href') else "Desconocido"
                
                if link in saved_links:
                    print(f"\nPost encontrado ya existe en la BD (Link: {link}).")
                    print("Deteniendo el scraping para evitar duplicados.")
                    seguir = False
                    break

                if texto == "Sin mensaje":
                    continue
                
                rows.append([autor, titulo, fecha_sql, texto, link])
            
            if not seguir:
                break
        
        numero_pagina += 1
else:
    print("Error al intentar iniciar sesión.")


if rows:
    print(f"Se recopilaron {len(rows)} filas NUEVAS. Insertando en la base de datos Postgres...")
    
    conn = None
    try:
        conn = psycopg2.connect(**PG_CONFIG)
        cursor = conn.cursor()
        
        sql_insert = """
        INSERT INTO mensajes (autor, titulo, fecha, contenido, link) 
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (link) DO NOTHING
        """
        
        cursor.executemany(sql_insert, rows)

        conn.commit() # Guardar los cambios en la BD
        print(f"¡Datos guardados exitosamente en la base de datos Postgres!")

    except (Exception, psycopg2.Error) as e:
        print(f"Ocurrió un error con la base de datos Postgres: {e}")
        
    finally:
        if conn:
            conn.close()
            print("Conexión a la base de datos Postgres cerrada.")

    # Guardar en CSV (sin cambios, sigue funcionando)
    print("Guardando en CSV...")
    with open("./mensajes.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="|")
        writer.writerows(rows)
else:
    print("No se recopilaron filas nuevas. La base de datos está actualizada.")

print("Proceso completado.")