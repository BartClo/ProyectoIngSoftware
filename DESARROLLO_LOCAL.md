# 🚀 Guía de Inicio Rápido - Desarrollo Local

Tu proyecto ya está configurado para desarrollo local con PostgreSQL. Aquí tienes los pasos para ejecutarlo:

## ✅ Estado Actual del Proyecto

- ✅ PostgreSQL configurado localmente
- ✅ Variables de entorno configuradas
- ✅ Sistema RAG implementado
- ✅ Frontend con TypeScript configurado

## 🏃‍♂️ Inicio Rápido (3 pasos)

### 1. Instalar Dependencias

```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

### 2. Inicializar RAG (primera vez)

```bash
cd backend
python setup_rag.py
```

### 3. Ejecutar el Sistema

**Opción A: Dos terminales separadas**
```bash
# Terminal 1 - Backend
cd backend
uvicorn main:app --reload

# Terminal 2 - Frontend  
cd frontend
npm run dev
```

**Opción B: Script automático**
```bash
# Ejecutar desde la raíz del proyecto
./setup-dev.bat    # Windows
./setup-dev.sh     # Linux/Mac
```

## 🔗 URLs de Acceso

Una vez ejecutado:

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **Documentación**: http://localhost:8000/docs
- **Estado RAG**: http://localhost:8000/rag_status/

## 🔧 Configuración Actual

Tu archivo `.env` en backend ya está configurado con:
- ✅ PostgreSQL local
- ✅ API keys de Gemini y Pinecone
- ✅ Configuración de desarrollo

## 📊 Verificar que Todo Funciona

### Backend
```bash
curl http://localhost:8000/
# Debe devolver: {"message": "Chatbot USS API está funcionando", ...}
```

### RAG System
```bash
curl http://localhost:8000/rag_status/
# Debe mostrar: {"rag_initialized": true, ...}
```

### Frontend
Abre http://localhost:5173 y verifica que:
- ✅ La interfaz carga sin errores de TypeScript
- ✅ Puedes crear conversaciones
- ✅ El chatbot responde con fuentes cuando hay documentos

## 🎯 Funcionalidades del Sistema

### Sistema RAG Completo
- **Embeddings**: Hugging Face (gratuito, se ejecuta solo una vez)
- **Vector DB**: Pinecone (almacena embeddings permanentemente)
- **LLM**: Gemini (solo para generar respuestas)
- **Caché**: Embeddings se guardan localmente

### Frontend Actualizado
- **Mostrar fuentes**: Las respuestas incluyen las fuentes de información
- **TypeScript**: Configurado para desarrollo (menos estricto)
- **API optimizada**: Configurada para desarrollo local

## 🐛 Solución de Problemas Comunes

### Error de PostgreSQL
```bash
# Verificar que PostgreSQL esté ejecutándose
pg_isready

# Si no está ejecutándose, iniciarlo:
# Windows: buscar "Services" y iniciar PostgreSQL
# Linux: sudo systemctl start postgresql
# Mac: brew services start postgresql
```

### Error de TypeScript en Frontend
```bash
cd frontend
npm install
# Los errores de TypeScript ya están solucionados
```

### Error de RAG no inicializado
```bash
cd backend
python setup_rag.py
```

### Verificar logs del sistema
```bash
# Backend logs
cd backend
uvicorn main:app --reload --log-level debug

# Ver logs específicos del RAG
cd backend
python test_rag.py
```

## 📝 Próximos Pasos

1. **Agregar más documentos**: Coloca PDFs en `backend/context_docs/`
2. **Rebuild index**: `POST http://localhost:8000/rebuild_index/`
3. **Personalizar respuestas**: Edita prompts en `rag_manager.py`
4. **Configurar producción**: Usar `docker-compose.yml` para deploy

---

🎉 **¡Tu chatbot RAG está listo para desarrollo local!**

El sistema responderá basándose exclusivamente en los documentos que agregues en `context_docs/`, optimizando el uso de tokens y proporcionando respuestas contextuales con fuentes transparentes.