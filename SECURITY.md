# 🔐 Guía de Seguridad - Variables de Entorno

## ⚠️ **IMPORTANTE: Protección de API Keys**

### 🚫 **NO HACER - Nunca en el Repositorio:**
```env
# ❌ MAL - Keys reales expuestas
GROQ_API_KEY=gsk_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
PINECONE_API_KEY=pcsk_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

### ✅ **HACER - Ejemplos Seguros:**
```env
# ✅ BIEN - Keys ejemplo/placeholder
GROQ_API_KEY=gsk_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
PINECONE_API_KEY=pcsk_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

---

## 🛡️ **Configuración Segura por Entorno**

### 📝 **Desarrollo Local (.env - NO subir a Git)**
```env
# Archivo local - incluido en .gitignore
DATABASE_URL=postgresql://postgres:tu_password@localhost:5432/mi_proyecto
GROQ_API_KEY=tu_key_real_de_groq
PINECONE_API_KEY=tu_key_real_de_pinecone
SECRET_KEY=desarrollo_secret_key_muy_larga
ENVIRONMENT=development
```

### 🌐 **Producción (Render - Variables de Entorno)**
```env
# Configurar en Render Dashboard > Environment
DATABASE_URL=postgresql://user:pass@host:5432/db  # Auto-generada por Render
GROQ_API_KEY=gsk_tu_key_real_de_groq_aqui
PINECONE_API_KEY=pcsk_tu_key_real_de_pinecone_aqui  
SECRET_KEY=production_secret_muy_larga_y_segura_12345
ENVIRONMENT=production
```

### 🚀 **Frontend (Vercel - Variables de Entorno)**
```env
# Configurar en Vercel Dashboard > Settings > Environment Variables
VITE_API_BASE_URL=https://tu-backend.onrender.com
```

---

## 📋 **Checklist de Seguridad**

### ✅ **Archivos Protegidos:**
- [ ] `.env` incluido en `.gitignore`
- [ ] API Keys reales NO en archivos de documentación
- [ ] Passwords NO hardcodeadas en código
- [ ] Variables de entorno usando placeholders públicos

### 🔄 **Proceso de Deploy:**
1. **Local**: Usar `.env` con keys reales (no subir)
2. **Git**: Solo archivos con placeholders/ejemplos  
3. **Render**: Configurar variables reales en dashboard
4. **Vercel**: Configurar variables reales en dashboard

### 🔍 **Verificación:**
```bash
# Buscar keys expuestas antes de commit
git log --oneline -p | grep -E "(gsk_|pcsk_|AIzaSy)"
```

---

## 🚨 **Si se Expuso una Key Accidentalmente:**

### 1️⃣ **Inmediato**
- Regenerar API Key en el proveedor
- Actualizar variable en producción
- Confirmar que la key vieja no funciona

### 2️⃣ **Git Cleanup**
```bash
# Eliminar de historial si es necesario
git filter-branch --force --index-filter \
'git rm --cached --ignore-unmatch archivo_con_key.env' \
--prune-empty --tag-name-filter cat -- --all
```

### 3️⃣ **Prevención**
- Usar `git-secrets` o similar
- Pre-commit hooks para detectar keys
- Review de código obligatorio

---

## 🎯 **Buenas Prácticas**

### 📁 **Estructura Recomendada:**
```
proyecto/
├── .env                 # ❌ NO subir (en .gitignore)
├── .env.example         # ✅ SI subir (sin valores reales)
├── README.md           # ✅ Solo placeholders
└── docs/
    └── security.md     # ✅ Este archivo
```

### 🔒 **Variables Críticas:**
- `GROQ_API_KEY` - Acceso a IA
- `PINECONE_API_KEY` - Base de datos vectorial  
- `DATABASE_URL` - Conexión a BD
- `SECRET_KEY` - Firma JWT

### 🛠️ **Herramientas Útiles:**
- **git-secrets**: Prevenir commits con secrets
- **TruffleHog**: Detectar keys en historial
- **GitLeaks**: Scanner de seguridad
- **dotenv-vault**: Gestión segura de .env

---

**🔐 Recuerda: La seguridad es responsabilidad de todos en el equipo.**