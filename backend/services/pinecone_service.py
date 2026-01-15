import os
import logging
from typing import List, Dict, Any, Optional
from pinecone import Pinecone, ServerlessSpec
import uuid
import asyncio
from functools import partial
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class PineconeService:
    def __init__(self):
        """Inicializa el servicio de Pinecone"""
        api_key = os.getenv("PINECONE_API_KEY")
        if not api_key:
            raise ValueError("PINECONE_API_KEY no encontrada en las variables de entorno")
        
        self.pc = Pinecone(api_key=api_key)
        self.environment = os.getenv("PINECONE_ENVIRONMENT", "us-east-1")
        self.dimension = 1024  # Dimensión para multilingual-e5-large
        self._embedding_service = None  # Lazy loading
        
        logger.info(f"PineconeService inicializado con environment: {self.environment}")
    
    def _get_embedding_service(self):
        """Lazy loading del embedding service"""
        if self._embedding_service is None:
            # Usar Pinecone Inference en producción para ahorrar RAM
            use_pinecone_inference = os.getenv("USE_PINECONE_INFERENCE", "true").lower() == "true"
            
            if use_pinecone_inference:
                logger.info("Usando Pinecone Inference API (sin carga de modelos local)")
                from .embedding_service_pinecone import embedding_service
            else:
                logger.info("Usando embedding service local (desarrollo)")
                from .embedding_service import embedding_service
            
            self._embedding_service = embedding_service
        return self._embedding_service
    
    async def _run_in_executor(self, func, *args, **kwargs):
        """Ejecuta una función bloqueante en un executor thread pool"""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, partial(func, *args, **kwargs))

    async def create_index(self, index_name: str) -> bool:
        """Crea un nuevo índice en Pinecone (Async Wrapper)"""
        try:
            logger.info(f"Intentando crear índice: {index_name}")
            
            def _create_impl():
                existing_indexes = self.pc.list_indexes()
                existing_names = [index.name for index in existing_indexes]
                
                if index_name in existing_names:
                    return True
                
                self.pc.create_index(
                    name=index_name,
                    dimension=self.dimension,
                    metric='cosine',
                    spec=ServerlessSpec(
                        cloud='aws',
                        region='us-east-1'
                    )
                )
                return True

            await self._run_in_executor(_create_impl)
            
            # Esperar a que el índice esté listo (polling asíncrono)
            for attempt in range(30):
                try:
                    index = self.pc.Index(index_name)
                    # stats call is light but blocking, wrap it? usually fast enough but let's be safe
                    await self._run_in_executor(index.describe_index_stats)
                    logger.info(f"Índice {index_name} creado y disponible")
                    return True
                except Exception:
                    await asyncio.sleep(2)
            
            return False
            
        except Exception as e:
            logger.error(f"Error creando índice {index_name}: {str(e)}")
            return False

    async def delete_index(self, index_name: str) -> bool:
        """Elimina un índice de Pinecone (Async Wrapper)"""
        try:
            await self._run_in_executor(self.pc.delete_index, index_name)
            return True
        except Exception as e:
            logger.error(f"Error eliminando índice {index_name}: {str(e)}")
            return False

    async def upsert_vectors(
        self,
        index_name: str,
        vectors: List[Dict[str, Any]],
        namespace: Optional[str] = None
    ) -> bool:
        """Inserta vectores en un índice (Async Wrapper)"""
        try:
            index = self.pc.Index(index_name)
            
            # Insertar en batches
            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                # upsert is blocking
                await self._run_in_executor(index.upsert, vectors=batch, namespace=namespace)
            
            return True
        except Exception as e:
            logger.error(f"Error insertando vectores en {index_name}: {str(e)}")
            return False

    async def query_vectors(
        self,
        index_name: str,
        query_vector: List[float],
        top_k: int = 5,
        namespace: Optional[str] = None,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Busca vectores similares (Async Wrapper)"""
        try:
            index = self.pc.Index(index_name)
            
            # query is blocking
            results = await self._run_in_executor(
                partial(
                    index.query,
                    vector=query_vector,
                    top_k=top_k,
                    namespace=namespace,
                    filter=filter_metadata,
                    include_metadata=True,
                    include_values=False
                )
            )
            
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
        """Elimina vectores específicos (Async Wrapper)"""
        try:
            index = self.pc.Index(index_name)
            await self._run_in_executor(index.delete, ids=vector_ids, namespace=namespace)
            return True
        except Exception as e:
            logger.error(f"Error eliminando vectores de {index_name}: {str(e)}")
            return False
            
    async def get_index_stats(self, index_name: str) -> Dict[str, Any]:
        """Obtiene estadísticas de un índice (Async Wrapper)"""
        try:
            index = self.pc.Index(index_name)
            stats = await self._run_in_executor(index.describe_index_stats)
            
            return {
                "total_vectors": stats.total_vector_count,
                "dimension": stats.dimension,
                "namespaces": dict(stats.namespaces) if stats.namespaces else {}
            }
        except Exception as e:
            logger.error(f"Error obteniendo stats de {index_name}: {str(e)}")
            return {}
            
    def generate_unique_id(self, prefix: str = "doc") -> str:
        return f"{prefix}_{uuid.uuid4().hex[:12]}"


# Instancia global del servicio
pinecone_service = PineconeService()