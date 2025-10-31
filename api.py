# api.py - Adaptador para Vercel
# Este archivo permite que FastAPI funcione con las rutas /api/* de Vercel

from backend.main import app

# Vercel busca por defecto una variable llamada 'app' o 'handler'
# Exportamos la aplicación FastAPI
handler = app

# También exportamos como 'app' para compatibilidad
__all__ = ['app', 'handler']