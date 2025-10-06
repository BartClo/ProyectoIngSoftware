# Setup para PostgreSQL Local

Este proyecto usa PostgreSQL como base de datos. Aquí tienes las instrucciones para configurarlo localmente:

## 📋 Prerrequisitos

1. **PostgreSQL instalado localmente**
   - Windows: Descargar de https://www.postgresql.org/download/
   - Ya tienes esto configurado ✅

## 🛠️ Configuración de Base de Datos

### 1. Crear Base de Datos

Ejecuta estos comandos en PostgreSQL (psql o pgAdmin):

```sql
-- Crear base de datos
CREATE DATABASE chatbot_uss_db;

-- Crear usuario (opcional, puedes usar postgres)
CREATE USER chatbot_user WITH PASSWORD 'chatbot_password';

-- Dar permisos al usuario
GRANT ALL PRIVILEGES ON DATABASE chatbot_uss_db TO chatbot_user;
```

### 2. Configurar Variables de Entorno

Edita el archivo `backend/.env` con tu configuración:

```env
# Opción 1: Usuario postgres (más simple)
DATABASE_URL=postgresql://postgres:TU_PASSWORD@localhost:5432/chatbot_uss_db

# Opción 2: Usuario personalizado
DATABASE_URL=postgresql://chatbot_user:chatbot_password@localhost:5432/chatbot_uss_db
```

### 3. Verificar Conexión

Ejecuta este comando para verificar que la conexión funciona:

```bash
cd backend
python -c "
from database import engine
try:
    with engine.connect() as conn:
        print('✅ Conexión exitosa a PostgreSQL')
except Exception as e:
    print(f'❌ Error de conexión: {e}')
"
```

## 🚀 Inicializar Sistema

### 1. Instalar Dependencias
```bash
cd backend
pip install -r requirements.txt
```

### 2. Crear Tablas
```bash
# Las tablas se crean automáticamente al iniciar la aplicación
python -c "from main import app; print('Tablas creadas')"
```

### 3. Configurar APIs

Necesitas obtener API keys para:

- **Gemini**: https://makersuite.google.com/app/apikey
- **Pinecone**: https://www.pinecone.io/ (cuenta gratuita)

Agrégalas al archivo `.env`

### 4. Inicializar RAG
```bash
python setup_rag.py
```

### 5. Ejecutar Aplicación
```bash
# Backend
uvicorn main:app --reload

# Frontend (nueva terminal)
cd frontend
npm install
npm run dev
```

## 🔧 Comandos Útiles

```bash
# Verificar estado de PostgreSQL
pg_isready

# Conectar a la base de datos
psql -U postgres -d chatbot_uss_db

# Ver tablas creadas
\dt

# Reiniciar base de datos (si es necesario)
DROP DATABASE chatbot_uss_db;
CREATE DATABASE chatbot_uss_db;
```

## 📊 Estructura de Tablas

El sistema crea automáticamente estas tablas:

- **users**: Usuarios del sistema
- **conversations**: Conversaciones del chatbot
- **messages**: Mensajes individuales

## 🎯 URLs de Desarrollo

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- Documentación API: http://localhost:8000/docs
- Estado RAG: http://localhost:8000/rag_status/