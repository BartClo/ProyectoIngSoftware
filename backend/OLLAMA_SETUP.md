# Configuración de Ollama Local

Este proyecto ha sido actualizado para usar **Ollama** como servicio de IA local en lugar de Gemini. Esto permite ejecutar modelos de IA localmente sin depender de servicios externos.

## ¿Qué es Ollama?

Ollama es una herramienta que permite ejecutar modelos de lenguaje grande (LLMs) localmente en tu máquina. Es ideal para:
- **Privacidad**: Los datos no salen de tu máquina
- **Velocidad**: No hay latencia de red
- **Costo**: Sin límites de API ni costos por token
- **Disponibilidad**: Funciona sin conexión a internet

## Instalación de Ollama

### Windows
1. Visita [https://ollama.ai](https://ollama.ai)
2. Descarga el instalador para Windows
3. Ejecuta el instalador y sigue las instrucciones
4. Ollama se iniciará automáticamente como servicio

### macOS
```bash
# Usando Homebrew
brew install ollama

# O descarga desde https://ollama.ai
```

### Linux
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

## Configuración del Proyecto

### 1. Variables de Entorno

Agrega estas variables a tu archivo `.env`:

```bash
# Configuración de Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

### 2. Instalar Dependencias

```bash
cd backend
pip install aiohttp>=3.9.0
```

### 3. Descargar un Modelo

Ollama necesita descargar un modelo la primera vez:

```bash
# Modelo recomendado (más pequeño y rápido)
ollama pull llama3.2

# Otros modelos populares
ollama pull mistral
ollama pull codellama
ollama pull llama2
```

## Verificar Instalación

### 1. Comprobar que Ollama está ejecutándose

```bash
# En Windows/macOS/Linux
ollama list
```

Deberías ver una lista de modelos instalados.

### 2. Probar Ollama desde línea de comandos

```bash
ollama run llama3.2
```

### 3. Verificar API REST

```bash
curl http://localhost:11434/api/version
```

Debería devolver información de versión de Ollama.

## Modelos Recomendados

| Modelo | Tamaño | Descripción | Recomendado para |
|--------|--------|-------------|------------------|
| `llama3.2` | ~2GB | Llama 3.2 3B | Uso general, rápido |
| `llama3.2:1b` | ~1GB | Llama 3.2 1B | Máquinas con poca RAM |
| `mistral` | ~4GB | Mistral 7B | Mejor calidad |
| `codellama` | ~4GB | Code Llama | Programación |
| `llama2` | ~4GB | Llama 2 7B | Uso general |

## Configuración Avanzada

### Cambiar Modelo

Edita tu archivo `.env`:

```bash
OLLAMA_MODEL=mistral  # Cambia a mistral u otro modelo
```

### Configuración de Rendimiento

Puedes ajustar los parámetros de generación en `ollama_service.py`:

```python
self.generation_options = {
    'temperature': 0.7,      # Creatividad (0.0-1.0)
    'top_p': 0.8,           # Diversidad de tokens
    'top_k': 40,            # Vocabulario limitado
    'num_predict': 2048,    # Máx tokens de respuesta
    'repeat_penalty': 1.1,  # Penalización repetición
}
```

## Troubleshooting

### Problema: "Ollama no está disponible"

1. **Verificar que Ollama esté ejecutándose:**
   ```bash
   ollama serve
   ```

2. **Verificar el puerto:**
   ```bash
   netstat -an | grep 11434
   ```

3. **Reiniciar Ollama:**
   ```bash
   # Windows (como administrador)
   net stop ollama
   net start ollama
   
   # macOS/Linux
   sudo systemctl restart ollama
   ```

### Problema: "Modelo no disponible"

1. **Listar modelos instalados:**
   ```bash
   ollama list
   ```

2. **Descargar el modelo:**
   ```bash
   ollama pull llama3.2
   ```

3. **Verificar en .env que el nombre coincida:**
   ```bash
   OLLAMA_MODEL=llama3.2  # Sin espacios ni caracteres especiales
   ```

### Problema: Respuestas lentas

1. **Usar un modelo más pequeño:**
   ```bash
   OLLAMA_MODEL=llama3.2:1b
   ```

2. **Verificar recursos del sistema:**
   - RAM disponible
   - CPU/GPU utilización

3. **Ajustar num_predict:**
   ```python
   'num_predict': 1024,  # Respuestas más cortas
   ```

## Migración desde Gemini

El código de Gemini permanece comentado en el proyecto para facilitar el cambio:

### Para volver a Gemini:

1. **Descomentar en `chat_rag.py`:**
   ```python
   from services.gemini_service import gemini_service
   # from services.ollama_service import ollama_service
   ```

2. **Cambiar las llamadas de función:**
   ```python
   response_data = await gemini_service.generate_response(...)
   ```

3. **Descomentar en `requirements.txt`:**
   ```
   google-generativeai>=0.8.0
   ```

## Rendimiento y Recursos

### Requisitos Mínimos
- **RAM**: 4GB (para modelos pequeños como llama3.2:1b)
- **Almacenamiento**: 2-10GB (dependiendo del modelo)
- **CPU**: Cualquier CPU moderna

### Requisitos Recomendados
- **RAM**: 8GB+ (para mejores modelos)
- **GPU**: NVIDIA con CUDA (opcional, mejora velocidad)
- **Almacenamiento**: SSD para mejor rendimiento

## Conclusión

Ollama ofrece una excelente alternativa local a servicios como Gemini, especialmente útil para:
- Desarrollo y testing
- Aplicaciones con requisitos de privacidad
- Reducción de costos de API
- Independencia de servicios externos

El chatbot debería funcionar de manera similar a como funcionaba con Gemini, pero ahora completamente local.