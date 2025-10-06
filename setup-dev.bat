@echo off
REM Script de desarrollo local para Windows - Chatbot USS

echo 🚀 Iniciando Chatbot USS en modo desarrollo local
echo ==================================================

REM Verificar si estamos en el directorio correcto
if not exist "README.md" (
    echo ❌ Ejecuta este script desde el directorio raíz del proyecto
    exit /b 1
)

REM Verificar Node.js
echo 🔍 Verificando Node.js...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js no encontrado. Instálalo desde https://nodejs.org/
    exit /b 1
) else (
    echo ✅ Node.js detectado
)

REM Verificar Python
echo 🔍 Verificando Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python no encontrado. Instálalo desde https://python.org/
    exit /b 1
) else (
    echo ✅ Python detectado
)

REM Verificar archivos .env
echo 🔍 Verificando configuración...
if not exist "backend\.env" (
    echo ⚠️  Creando archivo .env para backend...
    copy "backend\.env.example" "backend\.env"
    echo 📝 Edita backend\.env con tu configuración de PostgreSQL y API keys
)

if not exist "frontend\.env" (
    echo ⚠️  Creando archivo .env para frontend...
    echo VITE_API_BASE_URL=http://localhost:8000 > frontend\.env
    echo VITE_ENVIRONMENT=development >> frontend\.env
)

REM Instalar dependencias del backend
echo 📦 Instalando dependencias del backend...
cd backend

if not exist "venv" (
    echo 🐍 Creando entorno virtual...
    python -m venv venv
)

REM Activar entorno virtual
call venv\Scripts\activate.bat

pip install -r requirements.txt

REM Verificar conexión a base de datos
echo 🔗 Verificando conexión a base de datos...
python -c "from database import engine; import sys; exec('try:\n with engine.connect() as conn:\n  print(\"✅ Conexión exitosa a PostgreSQL\")\nexcept Exception as e:\n print(f\"❌ Error de conexión: {e}\")\n print(\"📝 Verifica tu configuración en backend/.env\")\n sys.exit(1)')"
if %errorlevel% neq 0 exit /b 1

cd ..

REM Instalar dependencias del frontend
echo 📦 Instalando dependencias del frontend...
cd frontend
npm install
cd ..

echo.
echo 🎉 ¡Configuración completada!
echo.
echo 📋 Próximos pasos:
echo 1. Configura tus API keys en backend\.env:
echo    - GEMINI_API_KEY (https://makersuite.google.com/app/apikey)
echo    - PINECONE_API_KEY (https://www.pinecone.io/)
echo    - DATABASE_URL (tu configuración de PostgreSQL)
echo.
echo 2. Inicializa el sistema RAG:
echo    cd backend ^&^& python setup_rag.py
echo.
echo 3. Ejecuta el sistema:
echo    📟 Backend: cd backend ^&^& uvicorn main:app --reload
echo    🌐 Frontend: cd frontend ^&^& npm run dev
echo.
echo 🔗 URLs:
echo    Frontend: http://localhost:5173
echo    Backend API: http://localhost:8000
echo    API Docs: http://localhost:8000/docs

pause