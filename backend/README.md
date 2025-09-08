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
