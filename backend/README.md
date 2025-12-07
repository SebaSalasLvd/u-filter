# U-Filter Backend

Este es el servidor backend para la extensión U-Filter.

## Requisitos Previos

*   Python 3.8+ instalado.
*   PostgreSQL instalado y ejecutándose.
*   Google Chrome instalado (necesario para que Selenium funcione).

---

## Instalación y Configuración

Sigue estos pasos para configurar el entorno de desarrollo local.

### 1. Crear y Activar Entorno Virtual

Es recomendable usar un entorno virtual para aislar las dependencias.

**En Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate
```

**En Linux/macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Instalar Dependencias

Una vez activado el entorno virtual, instala las librerías necesarias listadas en `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 3. Configuración de Variables de Entorno

Crea un archivo `.env` en la carpeta `backend` basándote en el ejemplo proporcionado (`.env.example`).

```bash
# Copiar ejemplo a .env
cp .env.example .env
```

Edita el archivo `.env` con tus credenciales locales de PostgreSQL y tu cuenta de U-Cursos:

```ini
# Base de datos
DB_HOST=localhost
DB_PORT=5432
DB_NAME=proyecto
DB_USER=postgres
DB_PASSWORD=tu_password

# Credenciales U-Cursos
UCURSOS_USER=tu.usuario
UCURSOS_PASSWORD=tu_clave

FLASK_DEBUG=1
```

> **Importante:** Asegúrate de crear la base de datos en tu servidor PostgreSQL antes de continuar. Por defecto el nombre es `proyecto`.
> ```sql
> CREATE DATABASE proyecto;
> ```

### 4. Base de Datos y Migraciones

El proyecto incluye el script `apply_migrations.py` para gestionar el esquema de la base de datos.

**Opción A: Aplicar migraciones (Crear tablas)** Ejecuta este comando para crear las tablas necesarias (`links`, `posts`) si no existen:

```bash
python apply_migrations.py
```

**Opción B: Resetear base de datos (Borrar y crear)** Si necesitas reiniciar la base de datos desde cero (esto **borrará todos los datos** existentes en las tablas):

```bash
python apply_migrations.py reset
```

### 5. Ejecutar el Servidor

Para iniciar el servidor de desarrollo Flask, ejecuta el script `run.py`:

```bash
python run.py
```

El servidor se iniciará por defecto en `http://127.0.0.1:7020`.

---

## Documentación de la API

A continuación se describen los endpoints disponibles en la API.

### Clasificación (`/api/classify`)

*   **POST** `/api/classify`
    *   Clasifica un texto arbitrario utilizando el modelo de IA.
    *   **Body:**
        ```json
        {
          "text": "Texto a clasificar...",
          "model": "bert"  // Opcional, default: "bert"
        }
        ```

### Enlaces (`/api/links`)

*   **POST** `/api/links`
    *   Registra un nuevo foro/enlace en la base de datos para ser monitoreado.
    *   **Body:**
        ```json
        {
          "url": "https://www.u-cursos.cl/...",
          "name": "Nombre del Foro"
        }
        ```

*   **GET** `/api/links`
    *   Lista todos los enlaces registrados en el sistema.

*   **GET** `/api/links/search`
    *   Verifica si un enlace ya existe en la base de datos.
    *   **Query Params:** `?url=...` o `?name=...`

### Scraper (`/api/scraper`)

*   **POST** `/api/scraper/run`
    *   Ejecuta el scraper (Selenium) para un dominio específico, extrae posts y los clasifica.
    *   **Body:**
        ```json
        {
          "domain": "https://www.u-cursos.cl/..."
        }
        ```

*   **POST** `/api/scraper/run-all`
    *   Ejecuta el scraper secuencialmente para **todos** los enlaces registrados en la base de datos.

*   **GET** `/api/scraper/list`
    *   Lista los posts clasificados almacenados en la base de datos.
    *   **Query Params:** `?domain=...` (Opcional: filtrar por dominio)

