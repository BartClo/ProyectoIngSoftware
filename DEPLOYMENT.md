# 🚀 Guía de Deployment - Render + Vercel

Esta guía te ayudará a desplegar el proyecto completo:
- **Backend + Base de Datos**: Render.com (Free Tier)
- **Frontend**: Vercel (Free Tier)

---

## 📋 Pre-requisitos

Antes de comenzar, necesitas tener:

1. ✅ Cuenta en [Render.com](https://render.com)
2. ✅ Cuenta en [Vercel](https://vercel.com)
3. ✅ Cuenta en [Groq](https://console.groq.com) (API Key gratuita)
4. ✅ Cuenta en [Pinecone](https://www.pinecone.io) (Free Tier)
5. ✅ Repositorio Git (GitHub/GitLab)

---

## 🗄️ PARTE 1: Deploy Backend + Database en Render

### Paso 1: Crear PostgreSQL Database

1. Inicia sesión en [Render Dashboard](https://dashboard.render.com)
2. Click en **"New +"** → **"PostgreSQL"**
3. Configura:
   - **Name**: `chatbot-rag-db`
   - **Database**: `chatbot_rag`
   - **User**: `chatbot_user`
   - **Region**: `Oregon (us-west)` o el más cercano
   - **Plan**: `Free`
4. Click en **"Create Database"**
5. ⏳ Espera 2-3 minutos a que se cree
6. 📋 **Guarda** la `Internal Database URL` (la necesitarás)

### Paso 2: Deploy Backend (Web Service)

#### Opción A: Deploy desde GitHub (Recomendado)

1. En Render Dashboard, click **"New +"** → **"Web Service"**
2. Conecta tu repositorio de GitHub
3. Configura:
   - **Name**: `chatbot-rag-backend`
   - **Region**: `Oregon` (mismo que la DB)
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: `Free`

#### Opción B: Deploy desde `render.yaml`

1. En Render Dashboard, click **"New +"** → **"Blueprint"**
2. Conecta tu repositorio
3. Render detectará automáticamente `render.yaml`
4. Click en **"Apply"**

### Paso 3: Configurar Variables de Entorno

En el dashboard del Web Service, ve a **"Environment"** y agrega:

```bash
# Database (auto-linked si creaste desde render.yaml)
DATABASE_URL=<Tu Internal Database URL de Paso 1>

# Groq AI (obtén en https://console.groq.com)
GROQ_API_KEY=gsk_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# Pinecone (obtén en https://www.pinecone.io)
PINECONE_API_KEY=pcsk_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX_NAME=chatbot-rag-index

# Security (Render puede generar automáticamente)
SECRET_KEY=<genera-una-clave-secreta-aleatoria>

# App Settings
ACCESS_TOKEN_EXPIRE_MINUTES=30
ENVIRONMENT=production
TOP_K_RESULTS=5

# CORS (actualizarás después con tu URL de Vercel)
FRONTEND_URL=https://tu-app.vercel.app
ALLOWED_ORIGINS=https://tu-app.vercel.app
```

### Paso 4: Crear Índice en Pinecone

1. Ve a [Pinecone Console](https://app.pinecone.io)
2. Click en **"Create Index"**
3. Configura:
   - **Index Name**: `chatbot-rag-index`
   - **Dimensions**: `384` (para sentence-transformers)
   - **Metric**: `cosine`
   - **Region**: `us-east-1` (Free Tier)
4. Click en **"Create Index"**

### Paso 5: Deploy y Verificar

1. Click en **"Manual Deploy"** → **"Deploy latest commit"**
2. ⏳ Espera 5-10 minutos (primera vez descarga dependencias)
3. Una vez completado, verifica:
   - Ve a tu URL: `https://chatbot-rag-backend.onrender.com/docs`
   - Deberías ver la documentación de FastAPI
   - Prueba el endpoint `/health` → debería retornar `{"status": "healthy"}`

📋 **Guarda tu Backend URL**: `https://chatbot-rag-backend.onrender.com`

---

## 🎨 PARTE 2: Deploy Frontend en Vercel

### Paso 1: Preparar el Frontend

1. En tu proyecto local, crea `.env.production` (NO lo subas a Git):

```bash
VITE_API_URL=https://chatbot-rag-backend.onrender.com
```

2. Verifica que `frontend/src/lib/api.ts` use `import.meta.env.VITE_API_URL`

### Paso 2: Deploy en Vercel

1. Inicia sesión en [Vercel Dashboard](https://vercel.com/dashboard)
2. Click en **"Add New"** → **"Project"**
3. Importa tu repositorio de GitHub
4. Configura:
   - **Framework Preset**: `Vite`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Install Command**: `npm install`

### Paso 3: Configurar Variables de Entorno en Vercel

En **"Settings"** → **"Environment Variables"**, agrega:

```bash
VITE_API_URL=https://chatbot-rag-backend.onrender.com
```

- Aplica a: **Production**, **Preview**, **Development**

### Paso 4: Deploy

1. Click en **"Deploy"**
2. ⏳ Espera 2-3 minutos
3. Una vez completado, obtendrás tu URL: `https://tu-app.vercel.app`

### Paso 5: Actualizar CORS en Backend

1. Regresa a **Render Dashboard** → Tu Web Service
2. Ve a **"Environment"**
3. Actualiza las variables:

```bash
FRONTEND_URL=https://tu-app.vercel.app
ALLOWED_ORIGINS=https://tu-app.vercel.app,http://localhost:5173
```

4. Click en **"Save Changes"**
5. Render redeplegará automáticamente (1-2 min)

---

## ✅ Verificación Final

### Backend Health Check

```bash
curl https://chatbot-rag-backend.onrender.com/health
# Debería retornar: {"status": "healthy"}
```

### Frontend

1. Abre tu app: `https://tu-app.vercel.app`
2. Intenta:
   - ✅ Registrar usuario
   - ✅ Iniciar sesión
   - ✅ Crear chatbot
   - ✅ Subir documento
   - ✅ Iniciar conversación
   - ✅ Hacer preguntas

---

## 🔧 Troubleshooting

### Backend no despliega

- ✅ Verifica que `requirements.txt` esté en `backend/`
- ✅ Revisa los logs en Render Dashboard → "Logs"
- ✅ Asegúrate de que `DATABASE_URL` esté configurada

### Frontend no conecta con Backend

- ✅ Verifica CORS: `ALLOWED_ORIGINS` debe incluir tu URL de Vercel
- ✅ Revisa `VITE_API_URL` en variables de entorno de Vercel
- ✅ Abre DevTools → Console → busca errores de CORS

### Errores de Pinecone

- ✅ Verifica que el índice existe en Pinecone Console
- ✅ Asegúrate de que `PINECONE_INDEX_NAME` coincida exactamente
- ✅ Revisa que las dimensiones sean `384`

### Base de datos no conecta

- ✅ Usa la `Internal Database URL` de Render (no la Externa)
- ✅ Formato: `postgresql://user:password@host:port/database`
- ✅ Verifica que la DB esté en la misma región que el backend

---

## 📊 Monitoreo

### Render

- **Logs**: Dashboard → Web Service → "Logs"
- **Metrics**: Dashboard → Web Service → "Metrics"
- **Events**: Dashboard → Web Service → "Events"

### Vercel

- **Logs**: Dashboard → Project → "Deployments" → Click en deployment
- **Analytics**: Dashboard → Project → "Analytics"
- **Speed Insights**: Dashboard → Project → "Speed Insights"

---

## 💰 Costos (Free Tier)

- ✅ **Render PostgreSQL**: Free (90 días de inactividad = suspend)
- ✅ **Render Web Service**: Free (spins down después de 15 min de inactividad)
- ✅ **Vercel**: Free (100 GB bandwidth/mes)
- ✅ **Groq**: Free (previa aprobación, límites generosos)
- ✅ **Pinecone**: Free (1 índice, 100k vectores)

**Nota**: El free tier de Render hace que el backend entre en "sleep" después de 15 minutos de inactividad. La primera request después del sleep puede tardar 30-60 segundos en responder.

---

## 🔐 Seguridad

- ✅ NUNCA subas `.env` o `.env.production` a Git
- ✅ Usa variables de entorno en Render/Vercel
- ✅ Genera `SECRET_KEY` único para producción
- ✅ Configura CORS correctamente
- ✅ Usa HTTPS (Render y Vercel lo proveen automáticamente)

---

## 🚀 CI/CD Automático

Una vez configurado:

1. **Push a `main`** en GitHub
2. Vercel despliega frontend automáticamente ⚡
3. Render despliega backend automáticamente ⚡
4. ¡Cambios en producción en ~3-5 minutos!

---

## 📚 Recursos Adicionales

- [Render Docs](https://render.com/docs)
- [Vercel Docs](https://vercel.com/docs)
- [Groq API Docs](https://console.groq.com/docs)
- [Pinecone Docs](https://docs.pinecone.io)

---

¡Deployment completado! 🎉
