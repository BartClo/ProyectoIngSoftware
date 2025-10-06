#!/bin/bash

# Script de desarrollo local para el Chatbot USS

echo "🚀 Iniciando Chatbot USS en modo desarrollo local"
echo "=================================================="

# Verificar si estamos en el directorio correcto
if [ ! -f "README.md" ]; then
    echo "❌ Ejecuta este script desde el directorio raíz del proyecto"
    exit 1
fi

# Verificar PostgreSQL
echo "🔍 Verificando PostgreSQL..."
if command -v pg_isready >/dev/null 2>&1; then
    if pg_isready; then
        echo "✅ PostgreSQL está corriendo"
    else
        echo "❌ PostgreSQL no está disponible. Asegúrate de que esté ejecutándose."
        exit 1
    fi
else
    echo "⚠️  PostgreSQL no detectado en PATH. Asegúrate de que esté instalado y ejecutándose."
fi

# Verificar Node.js
echo "🔍 Verificando Node.js..."
if command -v node >/dev/null 2>&1; then
    echo "✅ Node.js $(node --version) detectado"
else
    echo "❌ Node.js no encontrado. Instálalo desde https://nodejs.org/"
    exit 1
fi

# Verificar Python
echo "🔍 Verificando Python..."
if command -v python >/dev/null 2>&1; then
    echo "✅ Python $(python --version) detectado"
elif command -v python3 >/dev/null 2>&1; then
    echo "✅ Python $(python3 --version) detectado"
    alias python=python3
else
    echo "❌ Python no encontrado. Instálalo desde https://python.org/"
    exit 1
fi

# Verificar archivos .env
echo "🔍 Verificando configuración..."
if [ ! -f "backend/.env" ]; then
    echo "⚠️  Creando archivo .env para backend..."
    cp backend/.env.example backend/.env
    echo "📝 Edita backend/.env con tu configuración de PostgreSQL y API keys"
fi

if [ ! -f "frontend/.env" ]; then
    echo "⚠️  Creando archivo .env para frontend..."
    echo "VITE_API_BASE_URL=http://localhost:8000" > frontend/.env
    echo "VITE_ENVIRONMENT=development" >> frontend/.env
fi

# Instalar dependencias del backend
echo "📦 Instalando dependencias del backend..."
cd backend
if [ ! -d "venv" ]; then
    echo "🐍 Creando entorno virtual..."
    python -m venv venv
fi

# Activar entorno virtual
if [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate  # Windows
elif [ -f "venv/bin/activate" ]; then
    source venv/bin/activate      # Linux/Mac
fi

pip install -r requirements.txt

# Verificar conexión a base de datos
echo "🔗 Verificando conexión a base de datos..."
python -c "
from database import engine
try:
    with engine.connect() as conn:
        print('✅ Conexión exitosa a PostgreSQL')
except Exception as e:
    print(f'❌ Error de conexión: {e}')
    print('📝 Verifica tu configuración en backend/.env')
    exit(1)
" || exit 1

cd ..

# Instalar dependencias del frontend
echo "📦 Instalando dependencias del frontend..."
cd frontend
npm install
cd ..

echo ""
echo "🎉 ¡Configuración completada!"
echo ""
echo "📋 Próximos pasos:"
echo "1. Configura tus API keys en backend/.env:"
echo "   - GEMINI_API_KEY (https://makersuite.google.com/app/apikey)"
echo "   - PINECONE_API_KEY (https://www.pinecone.io/)"
echo "   - DATABASE_URL (tu configuración de PostgreSQL)"
echo ""
echo "2. Inicializa el sistema RAG:"
echo "   cd backend && python setup_rag.py"
echo ""
echo "3. Ejecuta el sistema:"
echo "   📟 Backend: cd backend && uvicorn main:app --reload"
echo "   🌐 Frontend: cd frontend && npm run dev"
echo ""
echo "🔗 URLs:"
echo "   Frontend: http://localhost:5173"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"