import os
import logging
from typing import List
from pinecone import Pinecone
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class EmbeddingServicePinecone:
    """
    Servicio de embeddings usando Pinecone Inference API
    NO requiere cargar modelos localmente - ahorra RAM
    """
    
    def __init__(self):
        """Inicializa el servicio usando Pinecone Inference"""
        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            raise ValueError("PINECONE_API_KEY no encontrada")
        
        self.pc = Pinecone(api_key=api_key)
        
        # Usar modelo de Pinecone que genera 384 dimensiones
        self.model_name = "multilingual-e5-small"  # 384 dimensiones
        self.dimension = 384
        
        logger.info(f"EmbeddingServicePinecone inicializado con modelo: {self.model_name}")
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Genera embeddings usando Pinecone Inference API
        
        Args:
            texts: Lista de textos
            
        Returns:
            Lista de vectores de embeddings
        """
        try:
            if not texts:
                return []
            
            # Usar Pinecone Inference API
            embeddings = self.pc.inference.embed(
                model=self.model_name,
                inputs=texts,
                parameters={"input_type": "passage"}
            )
            
            # Extraer los vectores
            vectors = [embedding['values'] for embedding in embeddings]
            
            logger.info(f"Generados {len(vectors)} embeddings usando Pinecone Inference")
            return vectors
            
        except Exception as e:
            logger.error(f"Error generando embeddings con Pinecone: {str(e)}")
            raise
    
    async def generate_query_embedding(self, query: str) -> List[float]:
        """
        Genera embedding para una consulta
        
        Args:
            query: Texto de la consulta
            
        Returns:
            Vector de embedding
        """
        try:
            # Usar Pinecone Inference API con input_type query
            embeddings = self.pc.inference.embed(
                model=self.model_name,
                inputs=[query],
                parameters={"input_type": "query"}
            )
            
            vector = embeddings[0]['values']
            logger.info(f"Generado embedding para query (dimensión: {len(vector)})")
            return vector
            
        except Exception as e:
            logger.error(f"Error generando query embedding: {str(e)}")
            raise


# Instancia global
embedding_service = EmbeddingServicePinecone()
