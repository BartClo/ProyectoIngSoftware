import os
import logging
from typing import List, Dict, Any, Optional
from pinecone import Pinecone, ServerlessSpec
import uuid
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Importar el servicio de embeddings correcto según el entorno
USE_LITE_EMBEDDINGS = os.getenv("USE_LITE_EMBEDDINGS", "false").lower() == "true"

if USE_LITE_EMBEDDINGS:
    logger.info("Usando embedding service lite para Render")
    from .embedding_service_lite import embedding_service
else:
    logger.info("Usando embedding service completo para desarrollo")
    try:
        from .embedding_service import embedding_service
    except ImportError:
        logger.warning("Embedding service completo no disponible, usando lite")
        from .embedding_service_lite import embedding_service


class PineconeService:
    def __init__(self):
        """Inicializa el servicio de Pinecone"""
        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            raise ValueError("PINECONE_API_KEY no encontrada en las variables de entorno")
        
        self.pc = Pinecone(api_key=api_key)
        self.environment = os.getenv("PINECONE_ENVIRONMENT", "us-east-1")
        self.dimension = 384  # Dimensión para all-MiniLM-L6-v2
        
        logger.info(f"PineconeService inicializado con environment: {self.environment}")
        
    async def create_index(self, index_name: str) -> bool:
        """
        Crea un nuevo índice en Pinecone para un chatbot
        
        Args:
            index_name: Nombre único del índice
            
        Returns:
            bool: True si se creó exitosamente
        """
        try:
            logger.info(f"Intentando crear índice: {index_name}")
            
            # Verificar si ya existe
            existing_indexes = self.pc.list_indexes()
            existing_names = [index.name for index in existing_indexes]
            logger.info(f"Índices existentes: {existing_names}")
            
            if index_name in existing_names:
                logger.info(f"El índice {index_name} ya existe")
                return True
            
            # Crear nuevo índice con configuración correcta para el plan gratuito
            logger.info(f"Creando nuevo índice {index_name} con dimensión {self.dimension}")
            self.pc.create_index(
                name=index_name,
                dimension=self.dimension,
                metric='cosine',
                spec=ServerlessSpec(
                    cloud='aws',
                    region='us-east-1'  # Región fija para el plan gratuito
                )
            )
            
            # Esperar a que el índice esté listo
            import time
            max_attempts = 30
            for attempt in range(max_attempts):
                try:
                    index = self.pc.Index(index_name)
                    stats = index.describe_index_stats()
                    logger.info(f"Índice {index_name} creado y disponible")
                    return True
                except Exception:
                    if attempt < max_attempts - 1:
                        logger.info(f"Esperando que el índice {index_name} esté listo (intento {attempt + 1}/{max_attempts})")
                        time.sleep(2)
                    else:
                        logger.error(f"Índice {index_name} no estuvo listo después de {max_attempts} intentos")
                        return False
            
            logger.info(f"Índice {index_name} creado exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"Error creando índice {index_name}: {str(e)}")
            logger.exception("Detalles completos del error:")
            return False
    
    async def delete_index(self, index_name: str) -> bool:
        """
        Elimina un índice de Pinecone
        
        Args:
            index_name: Nombre del índice a eliminar
            
        Returns:
            bool: True si se eliminó exitosamente
        """
        try:
            logger.info(f"Intentando eliminar índice: {index_name}")
            
            # Verificar si el índice existe antes de intentar eliminarlo
            existing_indexes = self.pc.list_indexes()
            existing_names = [index.name for index in existing_indexes]
            
            if index_name not in existing_names:
                logger.warning(f"El índice {index_name} no existe, considerando eliminación exitosa")
                return True
                
            self.pc.delete_index(index_name)
            logger.info(f"Índice {index_name} eliminado exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"Error eliminando índice {index_name}: {str(e)}")
            # No fallar si el índice no existe
            if "not found" in str(e).lower() or "404" in str(e):
                logger.info(f"Índice {index_name} no encontrado, considerando eliminación exitosa")
                return True
            return False
    
    async def upsert_vectors(
        self,
        index_name: str,
        vectors: List[Dict[str, Any]],
        namespace: Optional[str] = None
    ) -> bool:
        """
        Inserta o actualiza vectores en un índice
        
        Args:
            index_name: Nombre del índice
            vectors: Lista de vectores con formato: 
                    [{"id": "unique_id", "values": [0.1, 0.2, ...], "metadata": {...}}]
            namespace: Namespace opcional para organizar vectores
            
        Returns:
            bool: True si se insertaron exitosamente
        """
        try:
            logger.info(f"Intentando insertar {len(vectors)} vectores en índice: {index_name}")
            
            # Verificar que el índice existe
            existing_indexes = self.pc.list_indexes()
            existing_names = [index.name for index in existing_indexes]
            
            if index_name not in existing_names:
                logger.error(f"El índice {index_name} no existe. Índices disponibles: {existing_names}")
                return False
            
            index = self.pc.Index(index_name)
            
            # Insertar vectores en batches de 100
            batch_size = 100
            total_inserted = 0
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                result = index.upsert(vectors=batch, namespace=namespace)
                total_inserted += len(batch)
                logger.info(f"Batch insertado: {len(batch)} vectores (total: {total_inserted}/{len(vectors)})")
            
            logger.info(f"Insertados exitosamente {len(vectors)} vectores en {index_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error insertando vectores en {index_name}: {str(e)}")
            logger.exception("Detalles completos del error:")
            return False
    
    async def query_vectors(
        self,
        index_name: str,
        query_vector: List[float],
        top_k: int = 5,
        namespace: Optional[str] = None,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Busca vectores similares en un índice
        
        Args:
            index_name: Nombre del índice
            query_vector: Vector de consulta
            top_k: Número de resultados a retornar
            namespace: Namespace a consultar
            filter_metadata: Filtros adicionales de metadatos
            
        Returns:
            List[Dict]: Lista de resultados con scores y metadatos
        """
        try:
            index = self.pc.Index(index_name)
            
            results = index.query(
                vector=query_vector,
                top_k=top_k,
                namespace=namespace,
                filter=filter_metadata,
                include_metadata=True,
                include_values=False
            )
            
            # Formatear resultados
            formatted_results = []
            for match in results.matches:
                formatted_results.append({
                    "id": match.id,
                    "score": match.score,
                    "metadata": match.metadata
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error consultando {index_name}: {str(e)}")
            return []
    
    async def delete_vectors(
        self,
        index_name: str,
        vector_ids: List[str],
        namespace: Optional[str] = None
    ) -> bool:
        """
        Elimina vectores específicos de un índice
        
        Args:
            index_name: Nombre del índice
            vector_ids: Lista de IDs a eliminar
            namespace: Namespace donde están los vectores
            
        Returns:
            bool: True si se eliminaron exitosamente
        """
        try:
            index = self.pc.Index(index_name)
            index.delete(ids=vector_ids, namespace=namespace)
            
            logger.info(f"Eliminados {len(vector_ids)} vectores de {index_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error eliminando vectores de {index_name}: {str(e)}")
            return False
    
    async def get_index_stats(self, index_name: str) -> Dict[str, Any]:
        """
        Obtiene estadísticas de un índice
        
        Args:
            index_name: Nombre del índice
            
        Returns:
            Dict: Estadísticas del índice
        """
        try:
            index = self.pc.Index(index_name)
            stats = index.describe_index_stats()
            
            return {
                "total_vectors": stats.total_vector_count,
                "dimension": stats.dimension,
                "namespaces": dict(stats.namespaces) if stats.namespaces else {}
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo stats de {index_name}: {str(e)}")
            return {}
    
    def generate_unique_id(self, prefix: str = "doc") -> str:
        """Genera un ID único para vectores"""
        return f"{prefix}_{uuid.uuid4().hex[:12]}"


# Instancia global del servicio
pinecone_service = PineconeService()