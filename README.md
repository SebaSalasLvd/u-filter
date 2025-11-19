<div align="center">
  <img src="./logo.svg" alt="Logo" width="300" style="margin-bottom: 24px;">
</div>

En el contexto del curso CC6409 - Taller de Desarrollo de Proyectos de IA, desarrollamos como proyecto semestral un plugin web que permite filtrar foros de U-Cursos.

Este proyecto tiene un desarrollo [frontend](frontend/README.md) y [backend](backend/README.md), y considera un avance por hitos.

---

### Stack
React, TypeScript, Flask, Python y wxt.

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

   ---

   **Stack:** React, TypeScript, Flask, Python, wxt.

   ---

   ## Instrucciones para el Backend

   Abajo están los pasos mínimos para dejar el backend en marcha en Windows (PowerShell). También incluyo alternativas para Linux/macOS.

   1) Crear y activar un entorno virtual

   PowerShell (Windows):
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   Linux/macOS:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

   2) Instalar dependencias

   ```powershell
   pip install -r .\backend\requirements.txt
   ```

   3) Configurar variables de entorno (BD)

   Puedes copiar `backend\.env.example` a `backend\.env` y editarlo, o exportar variables en la sesión.

   PowerShell (temporal para la sesión):
   ```powershell
   $env:DB_HOST = "localhost";
   $env:DB_PORT = "5432";
   $env:DB_NAME = "proyecto";
   $env:DB_USER = "postgres";
   $env:DB_PASSWORD = "password";
   ```

   Linux/macOS (export):
   ```bash
   export DB_HOST=localhost
   export DB_PORT=5432
   export DB_NAME=proyecto
   export DB_USER=postgres
   export DB_PASSWORD=password
   ```

   4) Aplicar migraciones SQL

   El proyecto incluye `backend/apply_migrations.py` que ejecuta los `*_up.sql` en `backend/migrations`.

   ```powershell
   python .\backend\apply_migrations.py
   ```

   Esto crea la tabla `classifications` (según `0001_create_classifications_up.sql`).

   5) Iniciar la aplicación

   Forma directa (usa el `app.run` que viene en el archivo):
   ```powershell
   python .\backend\flask\app.py
   ```

