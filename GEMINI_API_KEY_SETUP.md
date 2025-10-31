# 🔑 Configuración de API Key de Google Gemini

## ⚠️ **Problema Actual**
La API Key de Gemini no es válida. El error indica:
```
400 API Key not found. Please pass a valid API key.
```

## 🚀 **Solución: Obtener Nueva API Key**

### 1. **Ir a Google AI Studio**
- Visita: https://makersuite.google.com/app/apikey
- **O** https://aistudio.google.com/app/apikey

### 2. **Iniciar Sesión**
- Usar cuenta de Google (Gmail, etc.)
- Aceptar términos y condiciones si es necesario

### 3. **Crear Nueva API Key**
- Hacer clic en **"Create API Key"**
- Seleccionar proyecto existente o crear uno nuevo
- Copiar la API Key generada (formato: `AIzaSy...`)

### 4. **Configurar en el Proyecto**
Editar archivo `backend/.env`:

```env
# === CONFIGURACIÓN DE GEMINI IA ===
GEMINI_API_KEY=AIzaSyC_TU_NUEVA_API_KEY_AQUI_COMPLETA
GEMINI_MODEL=gemini-1.5-flash
```

### 5. **Reiniciar el Servidor**
```bash
# En terminal del backend
# Ctrl+C para parar
uvicorn main:app --reload
```

## ✅ **Verificación**

### Probar API Key
Después de configurar, el servidor debe mostrar:
```
API Key cargada: AIzaSyC_TU...COMPLETA
Servicio Gemini inicializado correctamente
```

### Endpoint de Verificación
```bash
GET http://localhost:8000/ai_health/
```
Debe retornar estado "healthy" si la API Key funciona.

## 🎯 **Notas Importantes**

- **Gratuito**: Gemini tiene cuota gratuita generosa
- **Límites**: 15 RPM (requests por minuto) en plan gratuito
- **Seguridad**: Nunca subir API Keys al repositorio
- **Renovación**: Las API Keys no expiran automáticamente

## 🔧 **Solución Alternativa (Temporal)**

Si no puedes obtener API Key inmediatamente, puedes usar respuestas mock:

1. Editar `backend/services/gemini_service.py`
2. Agregar modo desarrollo sin API Key
3. Retornar respuestas de ejemplo

## 📞 **Soporte**

- **Google AI Studio**: https://aistudio.google.com/
- **Documentación**: https://ai.google.dev/docs
- **Límites de Uso**: https://ai.google.dev/pricing

---

**🎉 Una vez configurada la API Key válida, el sistema RAG funcionará completamente!**