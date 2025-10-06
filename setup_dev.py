#!/usr/bin/env python3
"""
Script de desarrollo local para el Chatbot USS
Configura y ejecuta el proyecto en modo desarrollo
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def print_status(message, is_error=False):
    """Imprime mensajes con formato"""
    prefix = "❌" if is_error else "✅"
    print(f"{prefix} {message}")

def check_python_version():
    """Verifica la versión de Python"""
    if sys.version_info < (3, 8):
        print_status("Python 3.8+ es requerido", True)
        return False
    print_status(f"Python {sys.version_info.major}.{sys.version_info.minor} detectado")
    return True

def check_file_exists(file_path, description):
    """Verifica si un archivo existe"""
    if not os.path.exists(file_path):
        print_status(f"{description} no encontrado: {file_path}", True)
        return False
    print_status(f"{description} encontrado")
    return True

def setup_backend():
    """Configura el backend"""
    print("\n🔧 Configurando Backend...")
    
    backend_dir = Path(__file__).parent / "backend"
    os.chdir(backend_dir)
    
    # Verificar archivos necesarios
    if not check_file_exists(".env", "Archivo de configuración backend"):
        print("💡 Copia .env.example a .env y configura tus API keys")
        return False
    
    # Instalar dependencias
    print("📦 Instalando dependencias del backend...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        print_status("Dependencias instaladas")
    except subprocess.CalledProcessError as e:
        print_status(f"Error instalando dependencias: {e}", True)
        return False
    
    # Crear base de datos SQLite si no existe
    if not os.path.exists("chatbot.db"):
        print("🗄️ Creando base de datos local...")
        try:
            # Importar y crear tablas
            from database import engine, Base
            from models import User, Conversation, Message
            Base.metadata.create_all(bind=engine)
            print_status("Base de datos creada")
        except Exception as e:
            print_status(f"Error creando base de datos: {e}", True)
            return False
    
    return True

def setup_frontend():
    """Configura el frontend"""
    print("\n🎨 Configurando Frontend...")
    
    frontend_dir = Path(__file__).parent / "frontend"
    
    # Verificar archivos
    if not check_file_exists(frontend_dir / ".env", "Archivo de configuración frontend"):
        print("💡 El archivo .env ya debería estar creado para desarrollo local")
    
    os.chdir(frontend_dir)
    
    # Verificar Node.js
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        print_status(f"Node.js {result.stdout.strip()} detectado")
    except FileNotFoundError:
        print_status("Node.js no encontrado. Instala Node.js desde https://nodejs.org/", True)
        return False
    
    # Instalar dependencias
    print("📦 Instalando dependencias del frontend...")
    try:
        subprocess.run(["npm", "install"], check=True, capture_output=True)
        print_status("Dependencias instaladas")
    except subprocess.CalledProcessError as e:
        print_status(f"Error instalando dependencias: {e}", True)
        return False
    
    return True

def start_development():
    """Inicia los servidores de desarrollo"""
    print("\n🚀 Iniciando servidores de desarrollo...")
    
    backend_dir = Path(__file__).parent / "backend"
    frontend_dir = Path(__file__).parent / "frontend"
    
    # Verificar configuración
    backend_env = backend_dir / ".env"
    if not backend_env.exists():
        print_status("Archivo .env del backend no encontrado", True)
        print("💡 Ejecuta primero: python setup_dev.py --setup")
        return False
    
    print("📋 Instrucciones para iniciar desarrollo:")
    print("\n1. 🔧 Backend (FastAPI):")
    print(f"   cd {backend_dir}")
    print("   uvicorn main:app --reload --host 0.0.0.0 --port 8000")
    
    print("\n2. 🎨 Frontend (React + Vite):")
    print(f"   cd {frontend_dir}")
    print("   npm run dev")
    
    print("\n3. 🌐 URLs de desarrollo:")
    print("   - Frontend: http://localhost:5173")
    print("   - Backend API: http://localhost:8000")
    print("   - Documentación API: http://localhost:8000/docs")
    
    print("\n⚠️ IMPORTANTE:")
    print("   - Configura tus API keys en backend/.env:")
    print("     * GEMINI_API_KEY (Google AI Studio)")
    print("     * PINECONE_API_KEY (Pinecone)")
    print("   - Ejecuta: python backend/setup_rag.py para inicializar RAG")

def main():
    """Función principal"""
    print("🎯 Chatbot USS - Configuración de Desarrollo Local")
    print("=" * 50)
    
    # Verificar Python
    if not check_python_version():
        sys.exit(1)
    
    # Cambiar al directorio del proyecto
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    # Procesar argumentos
    if len(sys.argv) > 1 and sys.argv[1] == "--setup":
        # Configurar proyecto
        if not setup_backend():
            sys.exit(1)
        
        if not setup_frontend():
            sys.exit(1)
        
        print("\n🎉 ¡Configuración completada!")
        print("💡 Ahora ejecuta: python setup_dev.py --start")
    
    elif len(sys.argv) > 1 and sys.argv[1] == "--start":
        # Mostrar instrucciones para iniciar
        start_development()
    
    else:
        # Mostrar ayuda
        print("\nUso:")
        print("  python setup_dev.py --setup   # Configurar proyecto")
        print("  python setup_dev.py --start   # Ver instrucciones de inicio")
        print("\nPrimera vez:")
        print("  1. python setup_dev.py --setup")
        print("  2. Configura API keys en backend/.env")
        print("  3. python setup_dev.py --start")

if __name__ == "__main__":
    main()