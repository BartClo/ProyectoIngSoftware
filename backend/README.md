# Backend: API de Autenticación con FastAPI

Este backend es un servidor API desarrollado con FastAPI que maneja la lógica de autenticación y la gestión de usuarios para el Chatbot USS. Utiliza PostgreSQL para la base de datos y `passlib` para el hashing seguro de contraseñas.

## ⚙️ Requisitos

- Python 3.9+
- pip
- PostgreSQL

## 🚀 Inicio Rápido

1.  Asegúrate de tener un servidor de **PostgreSQL** corriendo y de que la base de datos `mi_proyecto` exista.
2.  Navega a la carpeta de este proyecto en tu terminal.
    `cd <ruta-a-tu-carpeta>/backend`
3.  Activa tu entorno virtual:
    `.\venv\Scripts\activate`
4.  Instala las dependencias necesarias. Puedes verlas en el archivo `requirements.txt`:
    `pip install -r requirements.txt`
5.  Inicia el servidor de Uvicorn:
    `uvicorn main:app --reload`

El servidor de la API se ejecutará en `http://127.0.0.1:8000`.

## 📌 Endpoints de la API

-   `POST /register/`: Registra un nuevo usuario en la base de datos.
-   `POST /login/`: Verifica las credenciales de un usuario y permite el acceso.

##Creación de un usuario de prueba
Para probar la funcionalidad de login, necesitas un usuario con una contraseña hasheada en tu base de datos. Sigue estos pasos para crear el usuario de demostración.

Abre pgAdmin y asegúrate de que tu base de datos mi_proyecto esté activa.

En el menú superior, haz clic en Tools y selecciona Query Tool.

Para generar el hash de una contraseña, abre una nueva terminal, navega a la carpeta de tu backend, activa tu entorno virtual y abre el intérprete de Python:

Intento

cd <ruta-a-tu-carpeta>/backend
.\venv\Scripts\activate
python
Pega y ejecuta el siguiente código en el intérprete de Python para generar la contraseña hasheada.

Pitón

from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
password_hash = pwd_context.hash("password123")
print(password_hash)
Copia la cadena de texto que el código te devuelva (comenzará con $2b$).

En pgAdmin, pega la siguiente consulta en el Query Tool, reemplazando [pega_aqui_el_hash] con el hash que acabas de copiar:

SQL

INSERT INTO users (email, password_hash) VALUES ('demostracion@docente.uss.cl', '[pega_aqui_el_hash]');
Si el usuario ya existe, te mostrará un error de llave duplicada, lo cual es normal.

Verifica que el usuario se haya creado correctamente ejecutando esta consulta:

SQL

SELECT * FROM users;
Deberías ver el correo demostracion@docente.uss.cl con su hash de contraseña en la tabla.

Ahora ya puedes probar el login en el frontend con el correo demostracion@docente.uss.cl y la contraseña password123.
