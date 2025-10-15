<div align="center">
  <img src="./logo.svg" alt="Logo" width="300" style="margin-bottom: 24px;">
</div>

En el contexto del curso CC6409 - Taller de Desarrollo de Proyectos de IA, desarrollamos como proyecto semestral un plugin web que permite filtrar foros de U-Cursos.

Este proyecto tiene un desarrollo [frontend](frontend/README.md) y [backend](backend/README.md), y considera un avance por hitos.

---

### Stack
React, TypeScript, Django, Python y wxt.

---

## Instrucciones de Instalación y Ejecución

### 1. Instalación del frontend con WXT

Para configurar el entorno de frontend utilizando WXT:

1. **Instalar dependencias de frontend:**
   Abre la terminal en la carpeta `frontend` y ejecuta:
   ```bash
   npm install
   ```

2. **Ejecutar el plugin:**
   Una vez instaladas las dependencias, necesitarás chrome o firefox para probar el plugin. Luego, inicia el servidor de desarrollo con el siguiente comando para Chrome:

   ```bash
   npm run dev
   ```

    Alternativamente puedes hacerlo en Firefox con:
   ```bash
    npm run dev:firefox
   ```

### 2. Instalación del entorno de Python para usar Django

Para configurar el entorno de backend con Django:

1. **Crear un entorno virtual:**
   Crea un entorno virtual en Python ejecutando:

   ```bash
   python -m venv nombrevenv
   ```

2. **Activar el entorno virtual:**
   En Windows, activa el entorno con:

   ```bash
   nombrevenv\Scripts\activate
   ```

   En Linux/macOS, usa:

   ```bash
   source nombrevenv/bin/activate
   ```

3. **Instalar dependencias de backend:**
   Instala los paquetes requeridos para Django:

   ```bash
   pip install -r requirements.txt
   ```

   *Nota:* El archivo `requirements.txt` está ubicado en la carpeta `backend`.

### 3. Ejecutar el servidor Django y el modelo BERT

Para iniciar el servidor y cargar el modelo BERT de Django:

1. **Ejecutar el servidor:**
   En la terminal, dentro de la carpeta de backend, ejecuta:

   ```bash
   python manage.py runserver
   ```

   Esto iniciará el servidor en `localhost:8000`.

   *Nota:* Actualmente, al acceder a cualquier página de `localhost` podrías ver un error.

### 4. Probar el modelo BERT

Para probar la respuesta del modelo BERT, puedes hacer una petición POST utilizando `curl` o `Invoke-RestMethod`.

#### En Windows (PowerShell):

Ejecuta el siguiente comando en la terminal de PowerShell:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/u_filter/bert/" `
    -Method POST `
    -Headers @{ "Content-Type" = "application/json" } `
    -Body '{"text": "texto que va a evaluar"}'
```

#### En Linux/macOS:

Ejecuta el siguiente comando en la terminal:

```bash
curl -X POST http://127.0.0.1:8000/api/spanish-bert/ \
    -H "Content-Type: application/json" \
    -d '{"text": "texto que va a evaluar"}'
```
