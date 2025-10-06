# 🚀 Guía de Desarrollo Local

## Inicio Rápido

### 1. Configuración Automática
```bash
# Ejecutar desde la raíz del proyecto
python setup_dev.py --setup
```

### 2. Configurar API Keys
Edita `backend/.env`:
```env
GEMINI_API_KEY=tu_api_key_aqui
PINECONE_API_KEY=tu_api_key_aqui
```

### 3. Inicializar RAG (opcional)
```bash
cd backend
python setup_rag.py
```

### 4. Iniciar Desarrollo
```bash
# Terminal 1 - Backend
cd backend
uvicorn main:app --reload

# Terminal 2 - Frontend  
cd frontend
npm run dev
```

## URLs de Desarrollo

- **Frontend**: http://localhost:5173
- **Backend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Diferencias con Producción

### Base de Datos
- **Desarrollo**: SQLite local (`chatbot.db`)
- **Producción**: PostgreSQL

### Configuración
- **Desarrollo**: Archivos `.env` locales
- **Producción**: Variables de entorno del servidor

### APIs
- **Desarrollo**: URLs localhost
- **Producción**: URLs de dominio

## Solución de Problemas

### Error: "DATABASE_URL no configurada"
```bash
# El sistema usará SQLite automáticamente
# Mensaje: "DATABASE_URL no configurada, usando SQLite local"
```

### Error: TypeScript estricto
```bash
# Ya configurado para ser menos estricto en desarrollo
# tsconfig.app.json tiene strict: false
```

### Error: CORS en desarrollo
```bash
# Vite proxy configurado automáticamente
# Las peticiones a /api se redirigen al backend
```

### Error: "API keys no encontradas"
```bash
# Edita backend/.env con tus keys reales
# O usa el sistema sin RAG (respuestas genéricas)
```

## Archivos de Configuración Local

```
├── backend/.env                 # Config backend (SQLite, APIs)
├── frontend/.env               # Config frontend (URLs locales)
├── setup_dev.py               # Script de configuración
└── DEVELOPMENT.md             # Esta guía
```

## Comandos Útiles

```bash
# Ver estado del sistema RAG
curl http://localhost:8000/rag_status/

# Reconstruir índice RAG
curl -X POST http://localhost:8000/rebuild_index/

# Ver info del chatbot
curl http://localhost:8000/chatbot_info/

# Probar backend
curl http://localhost:8000/

# Instalar dependencias frontend
cd frontend && npm install

# Instalar dependencias backend  
cd backend && pip install -r requirements.txt
```

## Desarrollo vs Producción

| Aspecto | Desarrollo | Producción |
|---------|------------|------------|
| Base de datos | SQLite local | PostgreSQL |
| Frontend URL | localhost:5173 | Vercel/dominio |
| Backend URL | localhost:8000 | Render/dominio |
| Configuración | Archivos .env | Variables de entorno |
| CORS | Permisivo | Restrictivo |
| TypeScript | Menos estricto | Estricto |
| Logs | Detallados | Optimizados |

## Tips de Desarrollo

1. **Usa SQLite**: Más fácil para desarrollo, datos en `chatbot.db`
2. **Proxy de Vite**: Frontend puede llamar `/api/...` y se redirige al backend
3. **Hot Reload**: Ambos servidores se reinician automáticamente
4. **Debug**: Logs detallados en consola para troubleshooting
5. **Sin Docker**: Desarrollo directo para mayor velocidad

¡Happy Coding! 🎉