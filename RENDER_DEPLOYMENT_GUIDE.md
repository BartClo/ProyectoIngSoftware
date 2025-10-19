# 🚀 Deploy con Render + Vercel (Optimizado)

## 📋 Arquitectura
- **Frontend**: Vercel (React + Vite)
- **Backend**: Render (FastAPI + Python optimizado)
- **Database**: Render PostgreSQL

---

## ✅ **Optimizaciones aplicadas para Render:**
- ✅ **requirements-render.txt**: Sin torch/transformers (evita errores Rust)
- ✅ **embedding_service_lite.py**: Embeddings ligeros sin dependencies pesadas
- ✅ **Variable USE_LITE_EMBEDDINGS=true**: Activa modo optimizado
- ✅ **render.yaml actualizado**: Usa requirements optimizados

---

## 🎯 **Paso 1: Deploy Backend en Render**

### 1.1 Crear cuenta Render
1. Ve a 👉 [render.com](https://render.com)
2. **Sign up with GitHub**
3. Conecta tu repositorio

### 1.2 Crear Web Service
1. **New Web Service** → **Connect GitHub**
2. Selecciona: `BartClo/ProyectoIngSoftware`
3. **Auto-configuración desde render.yaml** ✅

### 1.3 Configuración detectada automáticamente:
- ✅ **Name**: `chatbot-rag-backend`
- ✅ **Environment**: `Python`
- ✅ **Root Directory**: `backend`
- ✅ **Build Command**: `pip install -r requirements-render.txt`
- ✅ **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### 1.4 Variables de Entorno críticas
**Agregar manualmente estas variables:**

```bash
GROQ_API_KEY=XXXXXXXXXXXXXXXXXXXXXXX
PINECONE_API_KEY=[TU_PINECONE_API_KEY]
```

**Las demás se configuran automáticamente desde render.yaml** ✅

### 1.5 PostgreSQL Database
- ✅ **Auto-creada**: Render creará `chatbot-rag-db` automáticamente
- ✅ **DATABASE_URL**: Se generará y configurará automáticamente
- ✅ **Plan gratuito**: PostgreSQL incluido

### 1.6 Deploy!
1. Click **"Create Web Service"**
2. Espera ~5-8 minutos (primera vez tarda más)
3. **URL del backend**: `https://chatbot-rag-backend.onrender.com`

---

## 🎯 **Paso 2: Deploy Frontend en Vercel**

### 2.1 Import en Vercel
1. Ve a 👉 [vercel.com](https://vercel.com)
2. **"New Project"** → **Import** `BartClo/ProyectoIngSoftware`
3. **Framework**: React/Vite (detectado automáticamente)

### 2.2 Build Settings Vercel
```bash
Build Command: cd frontend && npm run build
Output Directory: frontend/dist
Install Command: cd frontend && npm install
```

### 2.3 Variable de Entorno Vercel
```bash
VITE_API_URL=https://chatbot-rag-backend.onrender.com
```

### 2.4 Deploy Frontend
1. Click **"Deploy"**
2. Espera ~2-3 minutos
3. **URL del frontend**: `https://tu-proyecto.vercel.app`

---

## ✅ **Verificación Final**

### Backend (Render):
```bash
curl https://chatbot-rag-backend.onrender.com/health
curl https://chatbot-rag-backend.onrender.com/ai_health/
```

### Frontend (Vercel):
- Abre tu URL de Vercel
- Debería conectarse al backend en Render
- Test login y chat functionality

---

## 💰 **Costos - Plan Gratuito**

### Render Free Plan:
- ✅ **750 horas/mes** de compute
- ✅ **PostgreSQL gratuito** (90 días, luego $7/mes)
- ✅ **SSL/TLS incluido**
- ⚠️ **Hiberna después de 15 min** de inactividad

### Vercel Free Plan:
- ✅ **100GB bandwidth/mes**
- ✅ **Always on**
- ✅ **SSL/TLS incluido**
- ✅ **Edge network global**

---

## 🚀 **¿Por qué Render + Vercel?**

✅ **Estabilidad**: Sin errores de dependencias
✅ **Gratuito**: Ambas plataformas tienen planes free generosos
✅ **Simple**: Deploy automático desde GitHub
✅ **Escalable**: Fácil upgrade cuando necesites más recursos

---

## 🛠️ **Troubleshooting**

### Si Render sigue fallando:
1. Verificar que usa `requirements-render.txt` ✅
2. Confirmar `USE_LITE_EMBEDDINGS=true` en variables ✅
3. Revisar logs en Render dashboard para errores específicos

### Si Frontend no conecta:
1. Verificar `VITE_API_URL` apunta a Render URL ✅
2. Confirmar que backend está running (no hibernando)
3. Hacer una request test al backend

---

¡Tu chatbot estará online con Render + Vercel! 🌐✨