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
    "username": "nicolas.inostroza.n",
    "password": "Salsadeperro12",
    "recordar": "1"
}
mensajes_inutiles = ["UP","Up","up",".","+1","+ 1","-1","x2","X2",",",":c",":(",":C",":)","Sin mensaje"]
# login y sesion activa
session = requests.Session()

# solicitud post del login
response = session.post(login_url, data=login_data)
rows = []
# auth exitosa :D
if response.status_code == 200:
    print("Login exitoso!")
    
    forum_url = 'https://www.u-cursos.cl/ingenieria/2/foro_institucion/'
    numero_pagina = 0
    while numero_pagina < 412:
        forum_url = f"{forum_url}?id_tema=&offset={numero_pagina}"
        print(f"Obteniendo offset = {numero_pagina} …") 
        forum_page = session.get(forum_url)

        soup = BeautifulSoup(forum_page.text, 'html.parser')

        # busca en los divs
        mensajes = [
        div for div in soup.find_all('div', class_='msg')
        if 'hijo' not in div.get('class', [])
    ]   
        if mensajes:
            print(f"scrapeando pagina {numero_pagina}")
        for mensaje in mensajes:

            autor_tag = mensaje.find('a', class_='usuario')
            autor = autor_tag.text.strip() if autor_tag else "Desconocido"

            fecha_tag = mensaje.find('span', class_='tiempo_rel')
            fecha = fecha_tag.text.strip() if fecha_tag else "0000-00-00"

            fecha_lista = re.search(r'\b\d{4}-\d{2}-\d{2}\b', fecha)

            texto_tag = mensaje.find('span', class_='ta')
            texto = texto_tag.get_text(separator="\n", strip=True) if texto_tag else "Sin mensaje"
            if texto == "Sin mensaje":
                continue
            rows.append([autor, fecha_lista.group(), texto])
        
        numero_pagina +=1
else:
    print("Error al intentar iniciar sesión.")

with open("mensajes.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f,delimiter="|")
    writer.writerow(["autor", "date", "content"])  # encabezados
    writer.writerows(rows)
