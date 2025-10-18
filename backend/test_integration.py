"""
Quick test script to verify RAG system functionality after frontend integration
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rag_service import RAGService

def test_rag_basic():
    """Test basic RAG functionality"""
    try:
        # Initialize RAG service
        rag = RAGService()
        
        # Test query
        test_query = "¿Qué documentos están disponibles?"
        
        # Get response
        response = rag.query("1", test_query, k=3)
        
        print("✅ RAG Service Test Results:")
        print(f"Query: {test_query}")
        print(f"Response: {response.get('response', 'No response')}")
        print(f"Sources: {len(response.get('sources', []))} documents found")
        
        return True
        
    except Exception as e:
        print(f"❌ RAG Service Error: {e}")
        return False

def test_embedding_service():
    """Test embedding service"""
    try:
        from embedding_service import EmbeddingService
        
        embedder = EmbeddingService()
        
        # Test embedding generation
        test_text = "Este es un texto de prueba"
        embedding = embedder.get_embedding(test_text)
        
        print("✅ Embedding Service Test Results:")
        print(f"Text: {test_text}")
        print(f"Embedding dimensions: {len(embedding) if embedding else 'None'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Embedding Service Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing RAG System Integration...\n")
    
    rag_ok = test_rag_basic()
    embedding_ok = test_embedding_service()
    
    print(f"\n📊 Test Summary:")
    print(f"RAG Service: {'✅ OK' if rag_ok else '❌ FAILED'}")
    print(f"Embedding Service: {'✅ OK' if embedding_ok else '❌ FAILED'}")
    
    if rag_ok and embedding_ok:
        print("\n🎉 All tests passed! RAG system is ready for frontend integration.")
    else:
        print("\n⚠️ Some tests failed. Check the error messages above.")