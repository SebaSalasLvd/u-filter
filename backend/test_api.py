# test_api.py
import requests
import json

# URL de la API que está corriendo localmente
# http://127.0.0.1:5000/proyecto/u-filter/backend
API_URL = "https://grupo2.jb.dcc.uchile.cl/proyecto/u-filter/backend"

# --- Define aquí todas las pruebas que quieras hacer ---
# Puedes añadir más diccionarios a esta lista para probar más casos.
casos_de_prueba = [
    {
        "text": "Clases particulares plan común \n Holaa! Nuevamente este semestre estaré haciendo clases particulares de los siguientes cursos de plan común \n - Introducción al álgebra \n - Introducción al cálculo \n - Cálculo diferencial e integral \n - Termodinámica química \n - Química \n Soy estudiante de 4to año de ingeniería civil química y he tenido experiencia docente en la mayoría de estos ramos. Además, ya llevo varios semestres ofreciendo clases particulares de estos mismos. Las clases pueden ser online o presenciales en la u, y los contenidos de estas se adaptan a las necesidades de cada estudiante. \n Más información \n Dejo mi número para cualquier consulta: +56 9 9503 0612 \n Saludos y éxito en el semestre!",
    },
    {
        "text": "[VENDO] Entrada Oasis - 19 de noviembre\n Hola!\n Estoy vendiendo mi entrada para el concierto de Oasis (ubicación andes)\n Me pueden contactar al +569 5946 2404 :)",
    },
    {
        "text": "[VENDO] Nintendo 3Ds + Juegos\n Hola. Estoy vendiendo mi consola y 10 juegos. Todo a $225.000 (conversable)\nLa consola es antigua por lo que tiene ciertos problemas de batería y cargador (tiene que conectarse de una manera muy especifica)\n A continuación me gustaría detallar cómo llegué al precio. Busqué consolas y juegos de segunda mano en internet y utilicé los precios más baratos que encontré en sitios chilenos:\n -Consola: $100.000\n -Juegos: $15.000 c/u (en promedio)\n El total calculado es $250.000 pero debido al tema de la batería y cargador lo dejé todo en \n$225.000 además de regalar el estuche de la nintendo e incluir la carta de AR games.\n Si prefieren no comprar todo junto podemos llegar a algún acuerdo sin problemas.\n Dejo mi número: +56 9 54742425\n y una foto con los juegos y la nintendo\n Nota: Los juegos Ice Age Continental Drift, Pokemon: Super Mystery Dungeon y Pokemon White\n Version 2 están en Inglés. ",
    },
    {
        # Caso de prueba con texto ambiguo
        "text": "VENDO MIEL $5000\n Vendo miel pura multifloral de cordillera de la zona de Curicó a $5000 el envase de 1 kg +56954519417",
    },
    {
        # Caso de prueba con texto ambiguo
        "text": "TechnologiesInc esta ofriendo trabajos de titulo/trabajo. \n Se buscan ingenieros con interes en la ciencia de datos y la creacion y entrenamiento de modelos de machine learning. \n Cualquier consulta o postulacion mandar un mail a mailgenerico@techinc.com",
    }
    
]

# --- El script enviará una petición por cada caso de prueba ---
for i, prueba in enumerate(casos_de_prueba):
    print(f"--- Enviando Prueba #{i+1} ---")
    print(f"Texto: '{prueba['text']}'")
    
    try:
        # Hacemos la petición POST, enviando los datos en formato JSON
        response = requests.post(API_URL, json=prueba)

        # Verificamos si la petición fue exitosa (código 200 OK)
        if response.status_code == 200:
            print("✅ Respuesta recibida:")
            # Usamos json.dumps para imprimir el JSON de forma ordenada (pretty-print)
            # ensure_ascii=False es clave para que muestre tildes y ñ correctamente
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        else:
            # Si hay un error del servidor (ej: 400, 500)
            print(f"❌ Error: El servidor respondió con el código {response.status_code}")
            print(f"Mensaje: {response.text}")

    except requests.exceptions.ConnectionError as e:
        # Si la API no está corriendo
        print("❌ Error de conexión: No se pudo conectar a la API.")
        print("Asegúrate de que tu servidor Flask (app.py) esté en ejecución.")
        break # Detenemos el script si no hay conexión

    print("-" * 30 + "\n")