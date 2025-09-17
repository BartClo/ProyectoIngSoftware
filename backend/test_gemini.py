#!/usr/bin/env python3
"""
Script de prueba para verificar que Gemini funcione correctamente
"""

import google.generativeai as genai

def test_gemini():
    """Prueba básica de la API de Gemini"""
    try:
        # Configurar API key
        genai.configure(api_key="AIzaSyDO1JayjGYlDCMi08zvFKa-VGRAQIzMEXA")
        
        # Crear modelo
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        # Prueba simple
        print("🔄 Probando conexión con Gemini...")
        response = model.generate_content(
            "Di 'Hola, soy Gemini y estoy funcionando correctamente!'",
            generation_config={
                "temperature": 0.1,
                "max_output_tokens": 50,
            }
        )
        
        result = getattr(response, "text", "") or ""
        if result:
            print(f"✅ Gemini responde: {result}")
            return True
        else:
            print("❌ Gemini no devolvió respuesta")
            return False
            
    except Exception as e:
        print(f"❌ Error conectando con Gemini: {e}")
        return False

def test_conversation():
    """Prueba una conversación simple"""
    try:
        genai.configure(api_key="AIzaSyDO1JayjGYlDCMi08zvFKa-VGRAQIzMEXA")
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        print("\n🔄 Probando conversación...")
        
        # Simular conversación
        prompt = """
Eres un asistente de IA útil y amigable. Responde de manera natural y conversacional.

Usuario: Hola, ¿cómo estás?

Asistente:"""
        
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.7,
                "max_output_tokens": 100,
            }
        )
        
        result = getattr(response, "text", "") or ""
        if result:
            print(f"✅ Conversación exitosa: {result}")
            return True
        else:
            print("❌ No se pudo generar respuesta conversacional")
            return False
            
    except Exception as e:
        print(f"❌ Error en conversación: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando pruebas de Gemini...")
    print("=" * 50)
    
    # Ejecutar pruebas
    test1 = test_gemini()
    test2 = test_conversation()
    
    print("\n" + "=" * 50)
    if test1 and test2:
        print("✅ Todas las pruebas pasaron. Gemini está funcionando correctamente!")
        print("🎉 El chatbot está listo para usar sin RAG.")
    else:
        print("❌ Algunas pruebas fallaron. Revisa la configuración.")
    
    print("\n📋 Resumen:")
    print(f"   - Conexión básica: {'✅' if test1 else '❌'}")
    print(f"   - Conversación: {'✅' if test2 else '❌'}")
