# Backend: API de Autenticación con FastAPI

Este backend es un servidor API desarrollado con FastAPI que maneja la lógica de autenticación y la gestión de usuarios para el Chatbot USS. Utiliza PostgreSQL para la base de datos, Gemini para IA conversacional y `passlib` para el hashing seguro de contraseñas.

## ⚙️ Requisitos

- Python 3.9+
- pip
- PostgreSQL
- API Key de Google Gemini

## 🚀 Inicio Rápido

### Desarrollo Local

1. **Configurar Variables de Entorno**
   ```bash
   # Copia el archivo de ejemplo
   cp .env.example .env
   
   # Edita .env con tus valores reales:
   # - DATABASE_URL: Tu conexión a PostgreSQL
   # - GEMINI_API_KEY: Tu API key de Google Gemini
   # - SECRET_KEY: Una clave secreta para JWT
   ```

2. **Instalar Dependencias**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Configurar Base de Datos**
   - Asegúrate de tener PostgreSQL corriendo
   - Crea la base de datos especificada en tu DATABASE_URL

4. **Iniciar el Servidor**
   ```bash
   uvicorn main:app --reload
   ```

El servidor se ejecutará en `http://127.0.0.1:8000`.

## 🚀 Despliegue en Producción

### Render (Backend)

1. **Preparar el Repositorio**
   - Asegúrate de que todos los cambios estén en Git
   - El archivo `render.yaml` ya está configurado

2. **Crear Servicio en Render**
   - Ve a [render.com](https://render.com) y crea una cuenta
   - Conecta tu repositorio de GitHub
   - Selecciona "New Web Service"
   - Configura:
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
     - **Python Version**: 3.11

3. **Configurar Variables de Entorno en Render**
   ```
   DATABASE_URL=postgresql://usuario:password@host:puerto/database
   GEMINI_API_KEY=tu_api_key_de_gemini
   SECRET_KEY=clave_secreta_para_jwt
   ACCESS_TOKEN_EXPIRE_MINUTES=120
   ENVIRONMENT=production
   ```

4. **Configurar Base de Datos**
   - Crear PostgreSQL Database en Render
   - Usar la URL generada en DATABASE_URL

### Variables de Entorno Requeridas

- `DATABASE_URL`: Conexión a PostgreSQL
- `GEMINI_API_KEY`: API key de Google Gemini
- `SECRET_KEY`: Clave secreta para JWT
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Tiempo de expiración de tokens
- `ENVIRONMENT`: production/development

## 📌 Endpoints de la API

### Autenticación
- `POST /register/`: Registra un nuevo usuario
- `POST /login/`: Login de usuario

### Conversaciones
- `GET /conversations/`: Listar conversaciones del usuario
- `POST /conversations/`: Crear nueva conversación
- `PATCH /conversations/{id}/`: Renombrar conversación
- `DELETE /conversations/{id}/`: Eliminar conversación

### Mensajes
- `GET /conversations/{id}/messages/`: Obtener mensajes de una conversación
- `POST /conversations/{id}/messages/`: Enviar mensaje al chatbot

### Sistema
- `GET /`: Health check básico
- `GET /health`: Health check para monitoreo
- `GET /ai_health/`: Estado del sistema de IA
- `GET /chatbot_info/`: Información del chatbot

## 🔧 Configuración de Desarrollo

Para probar la funcionalidad de login, necesitas crear un usuario en tu base de datos PostgreSQL.

En el menú superior, haz clic en `Tools` y selecciona `Query Tool`.

Para generar el hash de una contraseña, abre una nueva terminal, navega a la carpeta de tu backend, activa tu entorno virtual y abre el intérprete de Python:

Intento

cd <ruta-a-tu-carpeta>/backend
`.\venv\Scripts\activate`
`python`
Pega y ejecuta el siguiente código en el intérprete de Python para generar la contraseña hasheada.

Pitón

`from passlib.context import CryptContext`
`pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")`
`password_hash = pwd_context.hash("password123")`
`print(password_hash)`
Copia la cadena de texto que el código te devuelva (comenzará con $2b$).

En pgAdmin, pega la siguiente consulta en el Query Tool, reemplazando [pega_aqui_el_hash] con el hash que acabas de copiar:

SQL

`INSERT INTO users (email, password_hash) VALUES ('demostracion@docente.uss.cl', '[pega_aqui_el_hash]');`
Si el usuario ya existe, te mostrará un error de llave duplicada, lo cual es normal.

Verifica que el usuario se haya creado correctamente ejecutando esta consulta:

SQL

`SELECT * FROM users;`
Deberías ver el correo demostracion@docente.uss.cl con su hash de contraseña en la tabla.

Ahora ya puedes probar el login en el frontend con el correo demostracion@docente.uss.cl y la contraseña password123.
