import requests
import re
import csv
from bs4 import BeautifulSoup

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

# login y sesion activa
session = requests.Session()

# solicitud post del login
response = session.post(login_url, data=login_data)
rows = []
# auth exitosa :D
if response.status_code == 200:
    print("Login exitoso!")
    
    forum_url = 'https://www.u-cursos.cl/ingenieria/2/foro_institucion/'
    # El limite de los numeros de pagina es 412 seguidas en el csv ya estan las primeras 412 paginas para empezar desde despues hay que cambiar el numero de pagina inicial.
    numero_pagina = 411 #
    seguir = True
    while seguir :
        forum_url = f"{forum_url}?id_tema=&offset={numero_pagina}"
        print(f"Obteniendo offset = {numero_pagina} …") 
        forum_page = session.get(forum_url)

        soup = BeautifulSoup(forum_page.text, 'html.parser')

        # busca en los divs los divs que contienen el post completo(titulo incluido)
        mensajes = [
        div for div in soup.find_all('div', class_='new')
    ]   
        if mensajes and numero_pagina < 735: #El programa se para en la pagina 735 por alguna razon
            print(f"scrapeando pagina {numero_pagina}")
        else:
            break

        for mensaje in mensajes:

            titulo_tag = mensaje.find('a', id='mensaje-titulo')
            titulo = titulo_tag.text.strip() if titulo_tag else "Sin titulo"

            #Para cada post grande del foro buscamos los divs interiores para obtener el resto de informacion
            contenidos = [
                div for div in mensaje.find_all('div', class_='msg')
                if 'hijo' not in div.get('class', [])
            ]

            for contenido in contenidos:
                autor_tag = contenido.find('a', class_='usuario')
                autor = autor_tag.text.strip() if autor_tag else "Desconocido"

                fecha_tag = contenido.find('span', class_='tiempo_rel')
                fecha = fecha_tag.text.strip() if fecha_tag else "0000-00-00"

                fecha_lista = re.search(r'\b\d{4}-\d{2}-\d{2}\b', fecha)

                texto_tag = contenido.find('span', class_='ta')
                texto = texto_tag.get_text(separator="\n", strip=True) if texto_tag else "Sin mensaje"
                if texto == "Sin mensaje":
                    continue
                rows.append([autor, titulo, fecha_lista.group(), texto])
            
        numero_pagina +=1
else:
    print("Error al intentar iniciar sesión.")

with open("./mensajes.csv", "a", newline="", encoding="utf-8") as f:#se usa a para hacer append de las nuevas filas
    writer = csv.writer(f,delimiter="|")
    #writer.writerow(["autor","title", "date", "content"])  # encabezados
    writer.writerows(rows)
