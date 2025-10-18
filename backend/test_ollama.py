#!/usr/bin/env python3
"""
Script de prueba para verificar la configuración de Ollama
"""

import asyncio
import sys
import os

# Agregar el directorio actual al path para importar servicios
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.ollama_service import ollama_service


async def test_ollama():
    """Prueba la conectividad y funcionalidad de Ollama"""
    
    print("🔍 Verificando configuración de Ollama...")
    print(f"   Base URL: {ollama_service.base_url}")
    print(f"   Modelo: {ollama_service.model_name}")
    print()
    
    # Verificar salud de Ollama
    print("🏥 Verificando salud del servicio...")
    health = await ollama_service._check_ollama_health()
    if health:
        print("   ✅ Ollama está ejecutándose")
    else:
        print("   ❌ Ollama no está disponible")
        print("\n💡 Soluciones:")
        print("   1. Instala Ollama desde https://ollama.ai")
        print("   2. Ejecuta: ollama serve")
        print("   3. Verifica que el puerto 11434 esté libre")
        return False
    
    # Verificar modelo
    print("\n🤖 Verificando modelo...")
    model_available = await ollama_service._ensure_model_available()
    if model_available:
        print(f"   ✅ Modelo {ollama_service.model_name} disponible")
    else:
        print(f"   ❌ Modelo {ollama_service.model_name} no disponible")
        print(f"\n💡 Solución: ollama pull {ollama_service.model_name}")
        return False
    
    # Prueba de generación
    print("\n💬 Probando generación de respuesta...")
    try:
        response = await ollama_service.generate_response(
            user_question="Hola, ¿cómo estás?",
            chatbot_name="Asistente de Prueba"
        )
        
        if response.get("success"):
            print("   ✅ Generación exitosa")
            print(f"   Respuesta: {response.get('response', '')[:100]}...")
        else:
            print("   ❌ Error en generación")
            print(f"   Error: {response.get('error', 'Desconocido')}")
            return False
            
    except Exception as e:
        print(f"   ❌ Excepción durante generación: {str(e)}")
        return False
    
    # Prueba de título
    print("\n📝 Probando generación de título...")
    try:
        title = await ollama_service.generate_title_for_conversation(
            "¿Cuáles son las mejores prácticas de programación?"
        )
        print(f"   ✅ Título generado: {title}")
    except Exception as e:
        print(f"   ❌ Error generando título: {str(e)}")
    
    print("\n🎉 ¡Todas las pruebas completadas exitosamente!")
    print("\n🚀 El chatbot está listo para usar Ollama local")
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 PRUEBA DE CONFIGURACIÓN OLLAMA")
    print("=" * 60)
    
    success = asyncio.run(test_ollama())
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)