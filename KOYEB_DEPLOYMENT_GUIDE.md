# 🚀 Deploy con Koyeb + Vercel

## 📋 Arquitectura
- **Frontend**: Vercel (React + Vite)
- **Backend**: Koyeb (FastAPI + Python + ML)
- **Database**: Koyeb PostgreSQL

---

## 🎯 **Paso 1: Deploy Backend en Koyeb**

### 1.1 Crear cuenta Koyeb
1. Ve a [koyeb.com](https://www.koyeb.com)
2. Sign up with GitHub
3. Conecta tu repositorio

### 1.2 Deploy Backend
1. Click "Create Service" → "GitHub"
2. Selecciona: `BartClo/ProyectoIngSoftware`
3. Configuración:
   - **Name**: `chatbot-rag-backend`
   - **Branch**: `main`
   - **Build directory**: `backend`
   - **Build command**: `pip install -r requirements.txt`
   - **Run command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Port**: `8000`

### 1.3 Variables de Entorno Koyeb
En la sección "Environment variables":

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

### 1.4 Agregar PostgreSQL
1. En tu proyecto, ve a "Data Stores"
2. Click "Create Data Store" → "PostgreSQL"
3. Koyeb generará automáticamente `DATABASE_URL`
4. Agregar `DATABASE_URL` como variable de entorno (valor auto-generado)

### 1.5 URL del Backend
Una vez desplegado:
```
https://chatbot-rag-backend-[tu-id].koyeb.app
```

---

## 🎯 **Paso 2: Deploy Frontend en Vercel**

### 2.1 Import en Vercel
1. Ve a [vercel.com](https://vercel.com)
2. "New Project" → Import `BartClo/ProyectoIngSoftware`
3. Framework Settings:
   - **Build Command**: `cd frontend && npm run build`
   - **Output Directory**: `frontend/dist`
   - **Install Command**: `cd frontend && npm install`

### 2.2 Variable de Entorno Vercel
```bash
VITE_API_URL=https://chatbot-rag-backend-[tu-id].koyeb.app
```

---

## ✅ **Verificación**

### Backend (Koyeb):
```bash
curl https://chatbot-rag-backend-[tu-id].koyeb.app/health
curl https://chatbot-rag-backend-[tu-id].koyeb.app/ai_health/
```

### Frontend (Vercel):
- Ve a tu URL de Vercel
- Debería conectarse al backend en Koyeb

---

## 💰 **Costos Koyeb vs Railway**

### Koyeb Gratuito:
- **Compute**: 2.5M requests/mes
- **Storage**: PostgreSQL incluido
- **Bandwidth**: 100GB/mes
- **Sleep**: No (always on)

### Comparación:
- **Koyeb**: Mejor para Python/ML, always-on
- **Railway**: 500 horas/mes, luego hiberna
- **Ambos**: PostgreSQL gratis incluido

---

## 🚀 **Ventajas Koyeb**

✅ **Especializado en Python/ML**:
- Mejor manejo de dependencias pesadas
- Sin problemas de memoria con torch/transformers
- Always-on (no hibernación)

✅ **Developer Experience**:
- Deploy automático desde Git
- Logs en tiempo real
- Auto-scaling global

✅ **Production Ready**:
- Health checks automáticos
- SSL/TLS incluido
- Global edge network

---

¡Tu chatbot tendrá performance global con Koyeb + Vercel! 🌍✨