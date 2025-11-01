# Dockerfile para Frontend React + Vite
# Construcción optimizada en múltiples etapas

# ===== ETAPA 1: Build =====
FROM node:18-alpine AS builder

# Establecer directorio de trabajo
WORKDIR /app

# Copiar archivos de dependencias
COPY package*.json ./

# Instalar dependencias
RUN npm ci --only=production --silent

# Copiar código fuente
COPY . .

# Construir aplicación para producción
RUN npm run build

# ===== ETAPA 2: Producción con Nginx =====
FROM nginx:alpine

# Copiar archivos construidos desde la etapa builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Copiar configuración personalizada de Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Exponer puerto 80
EXPOSE 80

# Comando de inicio
CMD ["nginx", "-g", "daemon off;"]
