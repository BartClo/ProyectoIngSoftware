# 🔧 Guía de Configuración Vercel

## ❌ Error Actual

```
A variable with the name 'VITE_API_URL' already exists for the target 
production,preview,development on branch undefined
```

## ✅ Solución

La variable `VITE_API_URL` ya existe. Necesitas **editarla** en lugar de crear una nueva.

---

## 📋 Pasos para Configurar en Vercel

### Opción 1: Editar Variable Existente (Recomendado)

1. **En la página de Environment Variables:**
   - Busca `VITE_API_URL` en la lista
   - Haz clic en el **ícono de lápiz (✏️)** al lado derecho
   
2. **Edita el valor:**
   ```
   https://chatbot-rag-backend-vl70.onrender.com
   ```
   
3. **Verifica que esté seleccionado:**
   - ✅ Production
   - ✅ Preview
   - ✅ Development
   
4. **Guarda** los cambios

### Opción 2: Eliminar y Recrear

1. **Eliminar variable existente:**
   - Busca `VITE_API_URL` en la lista
   - Haz clic en el **botón menos (⊖)** o **ícono de basura (🗑️)**
   - Confirma la eliminación
   
2. **Crear nueva variable:**
   - Haz clic en **"Add Another"**
   - **Key:** `VITE_API_URL`
   - **Value:** `https://chatbot-rag-backend-vl70.onrender.com`
   - **Selecciona todos los entornos:**
     - ✅ Production
     - ✅ Preview  
     - ✅ Development
   - **Guarda**

---

## 🔄 Después de Configurar

### 1. Redeploy del Frontend

Ve a: **Deployments** → Selecciona el último deployment → **Redeploy**

O simplemente haz un nuevo commit:
```powershell
# Cualquier cambio mínimo para trigger redeploy
git commit --allow-empty -m "Trigger redeploy with new backend URL"
git push origin main
```

### 2. Verifica la Configuración

Una vez desplegado, abre la consola del navegador en tu app y verifica:

```javascript
console.log(import.meta.env.VITE_API_URL)
// Debe mostrar: https://chatbot-rag-backend-vl70.onrender.com
```

---

## ✅ URLs Correctas Verificadas

### Backend (Render) ✅
```
https://chatbot-rag-backend-vl70.onrender.com
```

**Status:** ✅ Funcionando correctamente
- Health: `{"status":"healthy"}`
- Embedding Model: `multilingual-e5-large` (Pinecone Inference)
- AI Provider: `Groq`

### Frontend (Vercel)
```
Tu URL de Vercel (ej: https://tu-app.vercel.app)
```

---

## 🔍 Verificación Completa

### 1. Test del Backend
```bash
curl https://chatbot-rag-backend-vl70.onrender.com/health
# Debe retornar: {"status":"healthy","timestamp":"..."}
```

### 2. Test de CORS
El backend ya está configurado para aceptar:
- ✅ `https://*.vercel.app` (todos los deployments de Vercel)
- ✅ `http://localhost:5173` (desarrollo local)

### 3. Test del Frontend
Una vez desplegado:
1. Abre tu app en Vercel
2. Abre DevTools (F12)
3. Ve a Console
4. Verifica que no haya errores de CORS
5. Intenta hacer login

---

## 🐛 Solución de Problemas

### Error: "Network Error" o "Failed to Fetch"

**Causa:** Variable de entorno no aplicada o URL incorrecta

**Solución:**
1. Verifica en Vercel → Settings → Environment Variables
2. La variable debe estar en **Production**, **Preview**, y **Development**
3. Redeploy después de cambiar variables

### Error: CORS

**Causa:** El backend no permite tu dominio

**Solución:** El backend ya está configurado para `*.vercel.app`, debería funcionar automáticamente.

### Backend en "Sleep Mode"

**Render Free Tier:** El backend se duerme después de 15 min de inactividad

**Síntoma:** Primera request tarda 30-60 segundos

**Solución:** Normal en free tier. Considera:
- Upgrade a Starter ($7/mes) para always-on
- O acepta el cold start

---

## 📝 Checklist Final

Antes de marcar como completo:

- [ ] Variable `VITE_API_URL` configurada en Vercel
- [ ] Valor: `https://chatbot-rag-backend-vl70.onrender.com`
- [ ] Aplicada a Production, Preview, Development
- [ ] Frontend redeployado
- [ ] Backend responde en `/health`
- [ ] Login funciona desde el frontend
- [ ] No hay errores de CORS en consola

---

## 🎯 Resumen Rápido

**Lo que tienes que hacer AHORA:**

1. ✏️ **Edita** (no crees nueva) la variable `VITE_API_URL`
2. 📝 **Valor:** `https://chatbot-rag-backend-vl70.onrender.com`
3. 🔄 **Redeploy** el frontend
4. ✅ **Prueba** que funcione

**Tiempo estimado:** 2-3 minutos

---

**Estado del Backend:** ✅ Funcionando (verificado)  
**Embedding Service:** ✅ Pinecone Inference API  
**Memoria:** ✅ ~150MB (optimizada)  
**CORS:** ✅ Configurado para Vercel
