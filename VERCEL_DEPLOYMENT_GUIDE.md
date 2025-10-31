# 🚀 Guía de Despliegue Completo en Vercel

## 📋 Resumen
Despliegue completo de **Frontend + Backend** en una sola plataforma Vercel.

**Stack Tecnológico:**
- **Frontend**: React + TypeScript + Vite → Vercel Static
- **Backend**: FastAPI + Python → Vercel Serverless Functions
- **Base de Datos**: NeonDB (PostgreSQL serverless gratuito)
- **AI**: Groq API con Llama 3.1 8B Instant
- **Vector Store**: Pinecone para RAG

---

## 🛠️ Pasos de Configuración

### 1. 🗄️ Configurar Base de Datos (NeonDB)

#### Paso 1: Crear cuenta en NeonDB
1. Ve a [neon.tech](https://neon.tech) y regístrate
2. Crea un nuevo proyecto: `chatbot-rag-db`
3. Región: US East (más cerca de Vercel)
4. Copia la `DATABASE_URL` que aparece

#### Paso 2: Obtener credenciales
La URL será algo como:
```
postgresql://username:password@ep-xyz.us-east-1.aws.neon.tech/neondb?sslmode=require
```

---

### 2. 🔑 Obtener API Keys

#### Groq API Key
1. Ve a [console.groq.com](https://console.groq.com)
2. Regístrate → "API Keys" → "Create API Key"
3. Copia la key: `gsk_...`

#### Pinecone API Key  
1. Ve a [pinecone.io](https://www.pinecone.io)
2. Regístrate → "API Keys" 
3. Crea un índice: `chatbot-rag-index` (dimensión: 384)
4. Copia la key: `pcsk_...`

---

### 3. 🚀 Desplegar en Vercel

#### Paso 1: Instalar Vercel CLI
```bash
npm i -g vercel
```

#### Paso 2: Desplegar proyecto
```bash
# En tu directorio del proyecto
cd ProyectoIngSoftware
vercel

# Configuración:
# - Set up and deploy: Yes
# - Which scope: [tu usuario/team]
# - Link to existing project: No  
# - Project name: chatbot-rag-fullstack
# - Directory: ./ (raíz del proyecto)
```

#### Paso 3: Configurar Variables de Entorno
```bash
# Ejecutar uno por uno:
vercel env add GROQ_API_KEY
# Pegar: gsk_tu_key_real_aqui

vercel env add PINECONE_API_KEY  
# Pegar: pcsk_tu_key_real_aqui

vercel env add DATABASE_URL
# Pegar: postgresql://user:pass@host/db?sslmode=require

vercel env add SECRET_KEY
# Pegar: tu-jwt-secret-super-seguro-aqui

vercel env add VITE_API_URL
# Pegar: https://tu-proyecto.vercel.app
```

#### Paso 4: Redesplegar con variables
```bash
vercel --prod
```

---

## ✅ Verificación del Despliegue

### 1. Backend API
```bash
# Health check general
curl https://tu-proyecto.vercel.app/api/health

# Health check de AI (Groq)  
curl https://tu-proyecto.vercel.app/api/ai_health/

# Documentación interactiva
# Abrir: https://tu-proyecto.vercel.app/docs
```

### 2. Frontend
- Ir a: `https://tu-proyecto.vercel.app`
- Debería cargar la página de login
- Registrar usuario de prueba
- Probar funcionalidad de chat

### 3. Database
La base de datos se inicializará automáticamente en el primer request.

---

## 🔧 Estructura del Proyecto

```
ProyectoIngSoftware/
├── api.py                 # 🔧 Adaptador para Vercel Functions
├── requirements.txt       # 🐍 Dependencias Python  
├── vercel.json           # ⚙️ Configuración Vercel
├── backend/              # 🔙 Código FastAPI
│   ├── main.py          # 🚀 Aplicación principal
│   ├── models.py        # 🗄️ Modelos SQLAlchemy
│   ├── services/        # 🤖 Servicios AI y RAG
│   └── routes/          # 🛣️ Rutas API
└── frontend/            # 🎨 Aplicación React
    ├── src/
    ├── package.json
    └── dist/            # 📦 Build de producción
```

---

## 🚨 Troubleshooting

### Backend no responde en `/api/*`
1. Verifica que `api.py` esté en la raíz
2. Revisa logs en Vercel Dashboard → Functions
3. Confirma que las variables de entorno estén configuradas

### Error de base de datos
1. Verifica la `DATABASE_URL` en variables de entorno  
2. Asegúrate de que incluya `?sslmode=require`
3. Revisa el estado de NeonDB en su dashboard

### Frontend no carga
1. Verifica que `VITE_API_URL` apunte a tu dominio de Vercel
2. Asegúrate de que el build de React se completó correctamente
3. Revisa la consola del navegador para errores

### Chat no funciona
1. Verifica que Groq API key sea válida en variables de entorno
2. Confirma que Pinecone index existe y es accesible  
3. Revisa logs de functions en Vercel Dashboard

---

## 💡 Ventajas de Vercel vs Render

✅ **Vercel**:
- Serverless functions → no límite de 30min como Render
- CDN global automático
- Mejor integración con React/Next.js
- Despliegue desde Git automático
- Functions escalables según demanda
- Plan gratuito muy generoso

❌ **Render**:
- Timeouts en plan gratuito
- Dependencias de Rust problemáticas
- Menos optimizado para apps full-stack

---

## 💰 Costos Estimados

### Plan Gratuito Vercel:
- **Frontend**: Hosting gratuito ilimitado
- **Backend**: 100GB-horas de functions gratis/mes
- **NeonDB**: PostgreSQL gratuito hasta 3GB
- **Groq**: $0.59/M tokens (muy económico)  
- **Pinecone**: Plan gratuito hasta 1M vectores

### **Total mensual: $0-5 USD** 🎉

---

## 🔄 Flujo de Desarrollo

### Desarrollo Local:
```bash
# Backend (terminal 1)
cd backend
uvicorn main:app --reload

# Frontend (terminal 2)  
cd frontend
npm run dev
```

### Deploy a Producción:
```bash
git push origin main
# Vercel hace autodeploy automáticamente! 🚀
```

---

¡Tu chatbot RAG está listo para escalar globalmente con Vercel! 🌍✨