# 🚀 Guía Completa de Despliegue - Chatbot USS

Esta guía te llevará paso a paso para desplegar tu aplicación en producción usando **Render** para el backend y **Vercel** para el frontend.

## 📋 Preparativos Iniciales

### 1. Verificar que todo funcione localmente
```bash
# Backend
cd backend
uvicorn main:app --reload

# Frontend (en otra terminal)
cd frontend
npm run dev
```

### 2. Subir cambios a Git
```bash
git add .
git commit -m "feat: Configurar proyecto para despliegue en producción"
git push origin feature/ia
```

---

## 🗄️ PASO 1: Desplegar Backend en Render

### 1.1 Crear cuenta en Render
1. Ve a [render.com](https://render.com)
2. Crea una cuenta (puedes usar GitHub)
3. Conecta tu repositorio de GitHub

### 1.2 Crear Base de Datos PostgreSQL
1. En el dashboard de Render, haz clic en **"New +"**
2. Selecciona **"PostgreSQL"**
3. Configura:
   - **Name**: `chatbot-uss-db`
   - **Database Name**: `chatbot_uss`
   - **User**: `chatbot_user`
   - **Region**: Elige la más cercana
   - **PostgreSQL Version**: 15
   - **Plan**: Free (para desarrollo)
4. Haz clic en **"Create Database"**
5. **IMPORTANTE**: Guarda la **External Database URL** que aparece (la necesitarás después)

### 1.3 Crear Web Service para el Backend
1. Haz clic en **"New +"** → **"Web Service"**
2. Conecta tu repositorio de GitHub
3. Configura:
   - **Name**: `chatbot-uss-backend`
   - **Region**: La misma que la base de datos
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### 1.4 Configurar Variables de Entorno en Render
En la sección **Environment Variables**, agrega:

```
DATABASE_URL=postgresql://chatbot_user:TU_PASSWORD@dpg-xxxxx-a.oregon-postgres.render.com/chatbot_uss
GEMINI_API_KEY=AIzaSyDO1JayjGYlDCMi08zvFKa-VGRAQIzMEXA
SECRET_KEY=super_secret_jwt_key_for_production_change_this
ACCESS_TOKEN_EXPIRE_MINUTES=120
ENVIRONMENT=production
```

**IMPORTANTE**: 
- Reemplaza `DATABASE_URL` con la URL real de tu base de datos de Render
- Cambia `SECRET_KEY` por una clave más segura
- Guarda la URL de tu backend (será algo como `https://chatbot-uss-backend.onrender.com`)

### 1.5 Desplegar
1. Haz clic en **"Create Web Service"**
2. Espera a que termine el despliegue (puede tomar 5-10 minutos)
3. Verifica que funcione visitando: `https://tu-backend.onrender.com/`

---

## 🌐 PASO 2: Desplegar Frontend en Vercel

### 2.1 Crear cuenta en Vercel
1. Ve a [vercel.com](https://vercel.com)
2. Crea una cuenta usando GitHub
3. Conecta tu repositorio

### 2.2 Importar Proyecto
1. En el dashboard de Vercel, haz clic en **"New Project"**
2. Busca tu repositorio y haz clic en **"Import"**
3. Configura:
   - **Framework Preset**: `Vite`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Install Command**: `npm install`

### 2.3 Configurar Variables de Entorno
En la sección **Environment Variables**, agrega:

```
VITE_API_BASE_URL=https://chatbot-uss-backend.onrender.com
```

**IMPORTANTE**: Reemplaza la URL con la URL real de tu backend en Render (sin barra final)

### 2.4 Desplegar
1. Haz clic en **"Deploy"**
2. Espera a que termine el despliegue (2-5 minutos)
3. Verifica que funcione visitando tu URL de Vercel

---

## 🔧 PASO 3: Configurar Conexiones

### 3.1 Actualizar CORS en Backend
Tu backend ya está configurado para permitir dominios de Vercel, pero si tienes problemas:

1. Ve a tu servicio en Render
2. En **Environment Variables**, asegúrate de que `ENVIRONMENT=production`
3. Redeploy si es necesario

### 3.2 Probar la Conexión
1. Ve a tu frontend en Vercel
2. Intenta registrar un usuario
3. Intenta hacer login
4. Envía un mensaje al chatbot

---

## 🔍 PASO 4: Verificación y Pruebas

### 4.1 Endpoints de Verificación
Prueba estos endpoints en tu backend:

- `GET https://tu-backend.onrender.com/` - Debe devolver info de la API
- `GET https://tu-backend.onrender.com/health` - Health check
- `GET https://tu-backend.onrender.com/ai_health/` - Estado de Gemini

### 4.2 Pruebas del Frontend
1. **Registro**: Crea un nuevo usuario con email `@docente.uss.cl`
2. **Login**: Inicia sesión con las credenciales
3. **Chat**: Envía mensajes y verifica respuestas
4. **Conversaciones**: Crea, renombra y elimina conversaciones

---

## 🚨 Solución de Problemas Comunes

### Backend no inicia
- **Error de base de datos**: Verifica que `DATABASE_URL` sea correcta
- **Error de Gemini**: Verifica que `GEMINI_API_KEY` sea válida
- **Error de dependencias**: Verifica que `requirements.txt` esté actualizado

### Frontend no conecta con Backend
- **Error de CORS**: Verifica que `ENVIRONMENT=production` en Render
- **URL incorrecta**: Verifica que `VITE_API_BASE_URL` sea correcta
- **HTTPS/HTTP**: Asegúrate de usar HTTPS para el backend

### Problemas de Base de Datos
```sql
-- Conectarse a la base de datos y crear las tablas manualmente si es necesario
-- (Render debería crear las tablas automáticamente)
```

---

## 📝 URLs Finales

Después del despliegue, tendrás:

- **Backend**: `https://chatbot-uss-backend.onrender.com`
- **Frontend**: `https://chatbot-uss-frontend.vercel.app`
- **Base de Datos**: Gestionada por Render

---

## 🔄 Actualizaciones Futuras

Para actualizar tu aplicación:

1. **Hacer cambios en local**
2. **Commit y push a GitHub**
   ```bash
   git add .
   git commit -m "feat: nueva funcionalidad"
   git push origin feature/ia
   ```
3. **Auto-deploy**: Tanto Render como Vercel se actualizarán automáticamente

---

## 🎉 ¡Listo!

Tu Chatbot USS ahora está desplegado en producción y listo para usar. Los usuarios pueden acceder desde cualquier lugar usando la URL de Vercel.

### Próximos pasos sugeridos:
- [ ] Configurar dominio personalizado
- [ ] Configurar monitoreo y alertas
- [ ] Implementar backups de base de datos
- [ ] Configurar SSL personalizado
- [ ] Agregar analytics y métricas
