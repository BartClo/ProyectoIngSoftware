# ✅ Checklist de Deployment Rápido

## 🎯 Pre-requisitos (Crear Cuentas)

- [ ] Cuenta en [Render.com](https://render.com) 
- [ ] Cuenta en [Vercel](https://vercel.com)
- [ ] Cuenta en [Groq](https://console.groq.com) → Obtener API Key
- [ ] Cuenta en [Pinecone](https://www.pinecone.io) → Obtener API Key
- [ ] Repositorio en GitHub conectado

---

## 📦 1. Configurar Pinecone (5 min)

- [ ] Ir a [Pinecone Console](https://app.pinecone.io)
- [ ] Crear índice:
  - Name: `chatbot-rag-index`
  - Dimensions: `384`
  - Metric: `cosine`
  - Region: `us-east-1` (free)
- [ ] Copiar API Key

---

## 🗄️ 2. Deploy Backend en Render (10 min)

### A. PostgreSQL Database
- [ ] New → PostgreSQL
- [ ] Name: `chatbot-rag-db`
- [ ] Plan: Free
- [ ] Create Database
- [ ] Copiar `Internal Database URL`

### B. Web Service
- [ ] New → Blueprint (o Web Service)
- [ ] Conectar GitHub repo
- [ ] Render detecta `render.yaml` automáticamente
- [ ] Configurar Environment Variables:

```bash
DATABASE_URL=<Internal DB URL copiada>
GROQ_API_KEY=gsk_XXXXXXXX
PINECONE_API_KEY=pcsk_XXXXXXXX
PINECONE_ENVIRONMENT=us-east-1
PINECONE_INDEX_NAME=chatbot-rag-index
SECRET_KEY=<generar-random>
FRONTEND_URL=https://tu-app.vercel.app (actualizar después)
```

- [ ] Deploy
- [ ] Esperar 5-10 min (primera vez)
- [ ] Copiar URL: `https://chatbot-rag-backend.onrender.com`

### C. Verificar
- [ ] Ir a `/docs` → Debería ver FastAPI Swagger
- [ ] Probar `/health` → `{"status": "healthy"}`

---

## 🎨 3. Deploy Frontend en Vercel (5 min)

- [ ] New Project
- [ ] Importar GitHub repo
- [ ] Framework: `Vite`
- [ ] Root Directory: `frontend`
- [ ] Build Command: `npm run build`
- [ ] Output Directory: `dist`

### Variables de Entorno
- [ ] Agregar: `VITE_API_URL=https://chatbot-rag-backend.onrender.com`
- [ ] Deploy
- [ ] Copiar URL: `https://tu-app.vercel.app`

---

## 🔄 4. Actualizar CORS en Backend

- [ ] Volver a Render → Web Service → Environment
- [ ] Actualizar:
  ```bash
  FRONTEND_URL=https://tu-app.vercel.app
  ALLOWED_ORIGINS=https://tu-app.vercel.app
  ```
- [ ] Save → Auto-redeploy (1-2 min)

---

## ✅ 5. Verificación Final

### Backend
- [ ] `https://chatbot-rag-backend.onrender.com/health` → `{"status": "healthy"}`
- [ ] `/docs` carga correctamente
- [ ] No hay errores en Render Logs

### Frontend
- [ ] `https://tu-app.vercel.app` carga
- [ ] Registrar usuario funciona
- [ ] Login funciona
- [ ] No hay errores de CORS en Console

### Funcionalidad Completa
- [ ] Crear chatbot
- [ ] Subir documento (PDF/DOCX)
- [ ] Esperar procesamiento
- [ ] Crear conversación
- [ ] Hacer pregunta sobre el documento
- [ ] Recibir respuesta con fuentes

---

## 🎉 ¡Deployment Completado!

URLs importantes:
- **Backend**: https://chatbot-rag-backend.onrender.com
- **Frontend**: https://tu-app.vercel.app
- **API Docs**: https://chatbot-rag-backend.onrender.com/docs

---

## 🐛 Troubleshooting Rápido

**Backend no responde**
- ✅ Render free tier "duerme" después de 15 min → Primera request tarda 30-60s

**Error de CORS**
- ✅ Verifica `FRONTEND_URL` y `ALLOWED_ORIGINS` en Render
- ✅ Asegúrate de incluir `https://` en las URLs

**Pinecone error**
- ✅ Verifica que el índice existe en Pinecone Console
- ✅ Dimensions deben ser exactamente `384`
- ✅ Nombre del índice coincide: `chatbot-rag-index`

**Database error**
- ✅ Usa `Internal Database URL` (no Externa)
- ✅ Verifica que DB y Web Service están en la misma región

---

**Tiempo total estimado**: 20-25 minutos ⏱️

**Costo**: $0.00 (todo free tier) 💰
