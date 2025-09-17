import requests
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
    "username": "john.doe",
    "password": "johnspassword",
    "recordar": "1"
}

# login y sesion activa
session = requests.Session()

# solicitud post del login
response = session.post(login_url, data=login_data)

# auth exitosa :D
if response.status_code == 200:
    print("Login exitoso!")
    
    forum_url = 'https://www.u-cursos.cl/ingenieria/2/foro_institucion/'
    forum_page = session.get(forum_url)

    soup = BeautifulSoup(forum_page.text, 'html.parser')

    # busca en los divs
    mensajes = soup.find_all('div', class_='msg')
    for mensaje in mensajes:

        autor_tag = mensaje.find('a', class_='usuario')
        autor = autor_tag.text.strip() if autor_tag else "Desconocido"

        fecha_tag = mensaje.find('span', class_='tiempo_rel')
        fecha = fecha_tag.text.strip() if fecha_tag else "Sin fecha"

        texto_tag = mensaje.find('span', class_='ta')
        texto = texto_tag.get_text(separator="\n", strip=True) if texto_tag else "Sin mensaje"

        print(f"Autor: {autor}")
        print(f"Fecha: {fecha}")
        print(f"Mensaje: {texto}")
        print("-" * 40)
else:
    print("Error al intentar iniciar sesión.")
