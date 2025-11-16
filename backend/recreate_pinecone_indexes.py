"""
Script para recrear índices de Pinecone con la dimensión correcta (1024)
Ejecutar este script SOLO UNA VEZ para migrar de 384 a 1024 dimensiones
"""

import os
from dotenv import load_dotenv
from pinecone import Pinecone

load_dotenv()

def recreate_indexes():
    """Elimina y recrea todos los índices con dimensión 1024"""
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        print("❌ Error: PINECONE_API_KEY no encontrada")
        return
    
    pc = Pinecone(api_key=api_key)
    
    print("=" * 60)
    print("🔧 RECREACIÓN DE ÍNDICES PINECONE")
    print("=" * 60)
    
    # Listar índices existentes
    existing_indexes = pc.list_indexes()
    existing_names = [index.name for index in existing_indexes]
    
    print(f"\n📋 Índices existentes encontrados: {len(existing_names)}")
    for name in existing_names:
        print(f"   - {name}")
    
    if not existing_names:
        print("\n✅ No hay índices para recrear")
        return
    
    # Confirmar acción
    print("\n⚠️  ADVERTENCIA:")
    print("   - Esto eliminará TODOS los índices existentes")
    print("   - Se perderán todos los vectores almacenados")
    print("   - Los índices se recrearán con dimensión 1024")
    print("   - Necesitarás volver a procesar los documentos")
    
    confirm = input("\n¿Deseas continuar? (escribe 'SI' para confirmar): ")
    
    if confirm != "SI":
        print("\n❌ Operación cancelada")
        return
    
    # Eliminar índices existentes
    print("\n🗑️  Eliminando índices...")
    for name in existing_names:
        try:
            pc.delete_index(name)
            print(f"   ✅ Eliminado: {name}")
        except Exception as e:
            print(f"   ❌ Error eliminando {name}: {e}")
    
    # Recrear índices con dimensión correcta
    print("\n🔨 Recreando índices con dimensión 1024...")
    from pinecone import ServerlessSpec
    
    for name in existing_names:
        try:
            pc.create_index(
                name=name,
                dimension=1024,  # Nueva dimensión para multilingual-e5-large
                metric='cosine',
                spec=ServerlessSpec(
                    cloud='aws',
                    region='us-east-1'
                )
            )
            print(f"   ✅ Recreado: {name} (dimensión: 1024)")
        except Exception as e:
            print(f"   ❌ Error recreando {name}: {e}")
    
    print("\n" + "=" * 60)
    print("✅ PROCESO COMPLETADO")
    print("=" * 60)
    print("\n📝 Próximos pasos:")
    print("   1. Los chatbots ahora usarán embeddings de 1024 dimensiones")
    print("   2. Necesitas volver a subir y procesar los documentos")
    print("   3. El modelo usado será: multilingual-e5-large")
    print("\n")

if __name__ == "__main__":
    recreate_indexes()
