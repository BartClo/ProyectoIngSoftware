# pinecone_service.py
import os
import logging
import time
from typing import List, Dict, Optional, Tuple
import numpy as np
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

logger = logging.getLogger(__name__)

class PineconeService:
    """
    Servicio para gestionar el almacenamiento y búsqueda de embeddings en Pinecone
    """
    
    def __init__(self, index_name: str = "uss-chatbot-rag"):
        """
        Inicializa el servicio de Pinecone
        
        Args:
            index_name: Nombre del índice en Pinecone
        """
        self.index_name = index_name
        self.dimension = 384  # Dimensión para all-MiniLM-L6-v2
        self.metric = "cosine"
        self.cloud = "aws"
        self.region = "us-east-1"
        
        # Inicializar cliente Pinecone
        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            raise ValueError("PINECONE_API_KEY no encontrada en variables de entorno")
        
        self.pc = Pinecone(api_key=api_key)
        self.index = None
        
        # Inicializar índice
        self._initialize_index()
    
    def _initialize_index(self):
        """Inicializa o conecta al índice de Pinecone"""
        try:
            # Verificar si el índice existe
            existing_indexes = [index.name for index in self.pc.list_indexes()]
            
            if self.index_name not in existing_indexes:
                logger.info(f"Creando nuevo índice: {self.index_name}")
                
                # Crear índice
                self.pc.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    metric=self.metric,
                    spec=ServerlessSpec(
                        cloud=self.cloud,
                        region=self.region
                    )
                )
                
                # Esperar a que el índice esté listo
                self._wait_for_index_ready()
            else:
                logger.info(f"Conectando a índice existente: {self.index_name}")
            
            # Conectar al índice
            self.index = self.pc.Index(self.index_name)
            
            # Verificar estadísticas del índice
            stats = self.index.describe_index_stats()
            logger.info(f"Índice conectado. Vectores almacenados: {stats.total_vector_count}")
            
        except Exception as e:
            logger.error(f"Error al inicializar índice Pinecone: {e}")
            raise
    
    def _wait_for_index_ready(self, timeout: int = 300):
        """Espera a que el índice esté listo para usar"""
        logger.info("Esperando que el índice esté listo...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                index_desc = self.pc.describe_index(self.index_name)
                if index_desc.status.ready:
                    logger.info("Índice listo para usar")
                    return
            except Exception as e:
                logger.warning(f"Error al verificar estado del índice: {e}")
            
            time.sleep(10)
        
        raise TimeoutError(f"Índice no estuvo listo después de {timeout} segundos")
    
    def index_exists_and_has_data(self) -> bool:
        """Verifica si el índice existe y tiene datos"""
        try:
            if not self.index:
                return False
            
            stats = self.index.describe_index_stats()
            return stats.total_vector_count > 0
        except Exception as e:
            logger.error(f"Error al verificar datos del índice: {e}")
            return False
    
    def upload_embeddings(self, embeddings: np.ndarray, documents: List[Dict], batch_size: int = 100):
        """
        Sube embeddings al índice de Pinecone
        
        Args:
            embeddings: Array de embeddings
            documents: Lista de documentos correspondientes
            batch_size: Tamaño del lote para upload
        """
        if len(embeddings) != len(documents):
            raise ValueError("El número de embeddings debe coincidir con el número de documentos")
        
        if len(embeddings) == 0:
            logger.warning("No hay embeddings para subir")
            return
        
        logger.info(f"Subiendo {len(embeddings)} vectores a Pinecone en lotes de {batch_size}")
        
        # Preparar vectores para upsert
        vectors = []
        for i, (embedding, doc) in enumerate(zip(embeddings, documents)):
            vector_data = {
                "id": doc["id"],
                "values": embedding.tolist(),
                "metadata": {
                    "text": doc["text"][:1000],  # Limitar texto en metadata (máx 40KB por vector)
                    "source": doc["source"],
                    "chunk_index": doc["chunk_index"]
                }
            }
            vectors.append(vector_data)
        
        # Subir en lotes
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            try:
                self.index.upsert(vectors=batch)
                logger.info(f"Lote {i//batch_size + 1}/{(len(vectors)-1)//batch_size + 1} subido exitosamente")
            except Exception as e:
                logger.error(f"Error al subir lote {i//batch_size + 1}: {e}")
                raise
        
        # Verificar que se subieron correctamente
        time.sleep(2)  # Dar tiempo para que se procesen
        stats = self.index.describe_index_stats()
        logger.info(f"Upload completado. Total de vectores en índice: {stats.total_vector_count}")
    
    def search_similar(self, query_embedding: np.ndarray, top_k: int = 5, 
                      min_score: float = 0.3) -> List[Dict]:
        """
        Busca vectores similares en Pinecone
        
        Args:
            query_embedding: Vector de consulta
            top_k: Número máximo de resultados
            min_score: Score mínimo de similitud
            
        Returns:
            Lista de documentos similares con scores
        """
        if not self.index:
            logger.error("Índice no inicializado")
            return []
        
        try:
            # Realizar búsqueda
            results = self.index.query(
                vector=query_embedding.tolist(),
                top_k=top_k,
                include_metadata=True
            )
            
            # Procesar resultados
            similar_docs = []
            for match in results.matches:
                # Filtrar por score mínimo
                if match.score >= min_score:
                    doc = {
                        "id": match.id,
                        "score": float(match.score),
                        "text": match.metadata.get("text", ""),
                        "source": match.metadata.get("source", ""),
                        "chunk_index": match.metadata.get("chunk_index", 0)
                    }
                    similar_docs.append(doc)
            
            logger.info(f"Encontrados {len(similar_docs)} documentos similares (score >= {min_score})")
            return similar_docs
            
        except Exception as e:
            logger.error(f"Error en búsqueda de Pinecone: {e}")
            return []
    
    def clear_index(self):
        """Limpia todos los vectores del índice"""
        try:
            # Obtener todos los IDs
            stats = self.index.describe_index_stats()
            if stats.total_vector_count == 0:
                logger.info("El índice ya está vacío")
                return
            
            # Eliminar todos los vectores
            self.index.delete(delete_all=True)
            logger.info("Índice limpiado exitosamente")
            
        except Exception as e:
            logger.error(f"Error al limpiar índice: {e}")
            raise
    
    def get_index_stats(self) -> Dict:
        """Obtiene estadísticas del índice"""
        try:
            stats = self.index.describe_index_stats()
            return {
                "total_vector_count": stats.total_vector_count,
                "dimension": self.dimension,
                "index_name": self.index_name
            }
        except Exception as e:
            logger.error(f"Error al obtener estadísticas: {e}")
            return {}
    
    def delete_index(self):
        """Elimina completamente el índice de Pinecone"""
        try:
            self.pc.delete_index(self.index_name)
            logger.info(f"Índice {self.index_name} eliminado exitosamente")
        except Exception as e:
            logger.error(f"Error al eliminar índice: {e}")
            raise