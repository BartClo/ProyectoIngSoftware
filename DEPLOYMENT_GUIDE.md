# 🚀 Guía de Despliegue en Producción

## 📋 Resumen del Proyecto

**Chatbot RAG** es un sistema completo de chatbot con Retrieval-Augmented Generation (RAG) que utiliza:
- **Backend**: FastAPI + PostgreSQL + Pinecone + Groq AI
- **Frontend**: React + TypeScript + Vite
- **AI**: Groq API con modelo Llama 3.1 8B Instant
- **Vector Store**: Pinecone para búsqueda semántica

---

## 🛠️ Configuración de Producción

### 1. 📱 Backend en Render

#### Paso 1: Crear cuenta en Render
1. Ve a [render.com](https://render.com) y crea una cuenta
2. Conecta tu repositorio de GitHub

#### Paso 2: Crear base de datos PostgreSQL
1. En el dashboard de Render, click "New" → "PostgreSQL"
2. Nombre: `chatbot-rag-db`
3. Plan: Free (para desarrollo)
4. Guarda la `DATABASE_URL` generada

#### Paso 3: Desplegar Backend
1. Click "New" → "Web Service"
2. Conecta tu repositorio GitHub
3. Configuración:
   - **Name**: `chatbot-rag-backend`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Root Directory**: `/backend`

#### Paso 4: Variables de Entorno en Render
```bash
# Variables requeridas:
DATABASE_URL=postgresql://user:password@host:port/database
GROQ_API_KEY=gsk_tu_api_key_real_aqui
PINECONE_API_KEY=pcsk_tu_api_key_real_aqui
PINECONE_ENVIRONMENT=gcp-starter
PINECONE_INDEX_NAME=chatbot-rag-index
SECRET_KEY=tu-secret-key-super-segura-para-jwt
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

---

### 2. 🌐 Frontend en Vercel

#### Paso 1: Crear cuenta en Vercel
1. Ve a [vercel.com](https://vercel.com) y crea una cuenta
2. Instala Vercel CLI: `npm i -g vercel`

#### Paso 2: Desplegar Frontend
```bash
# En tu proyecto local:
cd ProyectoIngSoftware
vercel

# Sigue las instrucciones:
# - Set up and deploy: Yes
# - Which scope: [tu usuario]
# - Link to existing project: No
# - Project name: chatbot-rag-frontend
# - Directory: ./frontend
```

#### Paso 3: Variables de Entorno en Vercel
```bash
# En el dashboard de Vercel o por CLI:
vercel env add VITE_API_URL

# Valor: https://tu-backend.onrender.com
```

---

## 🔧 Pasos de Configuración Detallados

### 1. 🔑 Obtener API Keys

#### Groq API Key
1. Ve a [console.groq.com](https://console.groq.com)
2. Regístrate/inicia sesión
3. Ve a "API Keys" → "Create API Key"
4. Copia la key que empieza con `gsk_`

#### Pinecone API Key
1. Ve a [pinecone.io](https://www.pinecone.io)
2. Regístrate/inicia sesión
3. Ve a "API Keys" en el dashboard
4. Copia la key que empieza con `pcsk_`
5. Crea un índice llamado `chatbot-rag-index`

### 2. 🛢️ Configurar Base de Datos

#### Render PostgreSQL
1. Una vez creada la DB en Render
2. Ve a tu servicio de DB → "Connect"
3. Copia la `DATABASE_URL` completa
4. Añádela a las variables de entorno del backend

### 3. 🔐 Configurar CORS

El backend automáticamente detectará tu URL de frontend de Vercel para CORS.

---

## ✅ Verificación de Despliegue

### 1. Backend Health Check
```bash
# Verifica que el backend esté funcionando:
curl https://tu-backend.onrender.com/health/

# Respuesta esperada:
{"status": "ok", "timestamp": "2024-01-20T10:30:00.000Z"}
```

### 2. AI Service Check
```bash
# Verifica la integración con Groq:
curl https://tu-backend.onrender.com/ai_health/

# Respuesta esperada:
{"status": "healthy", "service": "groq", "model": "llama-3.1-8b-instant"}
```

### 3. Frontend Access
- Ve a tu URL de Vercel
- Deberías ver la página de login
- Registra un usuario de prueba
- Verifica que puedes hacer chat

---

## 🚨 Troubleshooting

### Backend no inicia
1. Revisa los logs en Render
2. Verifica que todas las variables de entorno estén configuradas
3. Asegúrate de que la `DATABASE_URL` sea correcta

### Frontend no conecta al backend
1. Verifica la variable `VITE_API_URL` en Vercel
2. Asegúrate de que termine sin `/` (ejemplo: `https://backend.onrender.com`)
3. Revisa la consola del navegador para errores de CORS

### Error de Groq API
1. Verifica que la `GROQ_API_KEY` sea válida
2. Asegúrate de tener créditos en tu cuenta de Groq
3. Revisa los logs del backend para errores específicos

### Error de Pinecone
1. Verifica que el índice `chatbot-rag-index` exista
2. Confirma que la `PINECONE_API_KEY` sea correcta
3. Asegúrate de estar en el plan correcto de Pinecone

---

## 🔄 Actualizaciones Futuras

### Para actualizar el backend:
```bash
git push origin main
# Render se actualiza automáticamente
```

### Para actualizar el frontend:
```bash
git push origin main
# Vercel se actualiza automáticamente
```

---

## 📱 URLs de Ejemplo

Una vez desplegado, tendrás:
- **Backend**: `https://chatbot-rag-backend.onrender.com`
- **Frontend**: `https://chatbot-rag-frontend.vercel.app`
- **Docs API**: `https://chatbot-rag-backend.onrender.com/docs`

---

## 🔒 Seguridad en Producción

✅ **Implementado:**
- Variables de entorno para todas las credenciales
- CORS configurado automáticamente
- JWT con secret key única
- Validación de entrada en todos los endpoints
- Rate limiting básico

⚠️ **Recomendaciones adicionales:**
- Activar HTTPS en ambos servicios
- Configurar un dominio personalizado
- Implementar logging avanzado
- Configurar backup automático de la base de datos
- Implementar monitoring con alertas

---

## 💰 Costos Estimados

### Plan Gratuito:
- **Render**: PostgreSQL gratuito + Web Service gratuito
- **Vercel**: Hosting frontend gratuito
- **Groq**: $0.59/M tokens (muy económico)
- **Pinecone**: Plan gratuito hasta 1M vectores

### Total mensual estimado: $0-5 USD (dependiendo del uso)

---

¡Tu chatbot RAG está listo para producción! 🎉