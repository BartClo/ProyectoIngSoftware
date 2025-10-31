# 🚀 Guía de Despliegue Split: Vercel + Railway

## 📋 Arquitectura
- **Frontend**: Vercel (React + Vite)
- **Backend**: Railway (FastAPI + Python + ML)
- **Database**: Railway PostgreSQL

---

## 🎯 **Paso 1: Deploy Backend en Railway**

### 1.1 Crear cuenta Railway
1. Ve a [railway.app](https://railway.app)
2. Sign up with GitHub
3. Connect tu repositorio

### 1.2 Deploy Backend
1. Click "New Project" → "Deploy from GitHub repo"
2. Selecciona: `BartClo/ProyectoIngSoftware`
3. Railway detectará automáticamente que es Python
4. **IMPORTANTE**: En configuración, setear:
   - **Root Directory**: `backend` (sin slash inicial)
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Railway instalará automáticamente desde `backend/requirements.txt`

### 1.3 Agregar Base de Datos
1. En tu proyecto Railway, click "New Service" → "Database" → "PostgreSQL"
2. Railway automáticamente conectará la `DATABASE_URL`
3. No necesitas configurar nada más, Railway maneja la conexión automáticamente

### 1.4 Variables de Entorno Railway
En tu servicio backend, ve a **Variables** y agrega una por una:

```bash
GROQ_API_KEY=gsk_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
PINECONE_API_KEY=pcsk_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
PINECONE_ENVIRONMENT=gcp-starter
PINECONE_INDEX_NAME=chatbot-rag-index
SECRET_KEY=super-secret-jwt-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ENVIRONMENT=production
```

⚠️ **Nota**: La `DATABASE_URL` se genera automáticamente cuando agregas PostgreSQL.

### 1.5 Obtener URL del Backend
Una vez desplegado, obtendrás algo como:
```
https://chatbot-rag-backend-production.up.railway.app
```

---

## 🎯 **Paso 2: Deploy Frontend en Vercel**

### 2.1 Configurar Frontend
En tu proyecto local, actualiza la configuración del frontend para apuntar al backend de Railway.

### 2.2 Deploy en Vercel
1. Ve a [vercel.com](https://vercel.com)
2. "New Project" → Import `BartClo/ProyectoIngSoftware`
3. Framework Settings:
   - **Build Command**: `cd frontend && npm run build`
   - **Output Directory**: `frontend/dist`
   - **Install Command**: `cd frontend && npm install`

### 2.3 Variable de Entorno Vercel
```bash
VITE_API_URL=https://tu-backend.up.railway.app
```

---

## ✅ **Verificación del Deploy**

### Backend (Railway):
```bash
curl https://tu-backend.up.railway.app/health
curl https://tu-backend.up.railway.app/ai_health/
```

### Frontend (Vercel):
- Ve a `https://tu-frontend.vercel.app`
- Debería conectarse al backend en Railway

---

## 🔧 **Configuración CORS**

El backend necesita permitir requests desde Vercel. En `backend/main.py`:

```python
origins = [
    "http://localhost:5173",
    "https://tu-frontend.vercel.app",  # Tu dominio Vercel
    "https://*.vercel.app",
]
```

---

## 💰 **Costos**

### Gratis por completo:
- **Railway**: 500 horas gratis/mes + PostgreSQL gratis
- **Vercel**: Frontend hosting ilimitado gratis
- **Total**: $0/mes para desarrollo y uso moderado

---

## 🚀 **Ventajas de esta arquitectura**

✅ **Railway para Backend**:
- Mejor soporte para dependencias ML (torch, transformers)
- PostgreSQL incluido gratis
- Sin límites de memoria como Vercel
- Ideal para FastAPI + Python

✅ **Vercel para Frontend**:
- CDN global ultrarrápido
- Deploy automático desde Git
- Optimizado para React/Vite
- Excelente performance

---

## 🔄 **Workflow de Desarrollo**

1. **Desarrollo local**: Todo funciona igual
2. **Deploy**: Push a main → ambos se actualizan automáticamente
3. **Variables**: Configuradas por separado en cada plataforma

¡Tu chatbot estará distribuido globalmente con la mejor performance! 🌍✨