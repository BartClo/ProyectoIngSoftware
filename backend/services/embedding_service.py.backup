import os
import logging
from typing import List, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
import pickle
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self):
        """Inicializa el servicio de embeddings con Sentence Transformers"""
        
        self.model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        self.cache_dir = os.path.join(".", "embeddings_cache")
        
        # Crear directorio de cache si no existe
        Path(self.cache_dir).mkdir(exist_ok=True)
        
        # Cargar modelo
        try:
            logger.info(f"Cargando modelo de embeddings: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            self.dimension = self.model.get_sentence_embedding_dimension()
            logger.info(f"Modelo cargado exitosamente. Dimensión: {self.dimension}")
        except Exception as e:
            logger.error(f"Error cargando modelo: {str(e)}")
            raise
        
        # Cache en memoria para embeddings frecuentes
        self.memory_cache = {}
        self.max_cache_size = 1000
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Genera embeddings para una lista de textos
        
        Args:
            texts: Lista de textos para generar embeddings
            
        Returns:
            List[List[float]]: Lista de vectores de embeddings
        """
        try:
            if not texts:
                return []
            
            # Verificar cache en memoria para textos individuales
            cached_embeddings = []
            texts_to_process = []
            cache_indices = []
            
            for i, text in enumerate(texts):
                text_hash = hash(text)
                if text_hash in self.memory_cache:
                    cached_embeddings.append((i, self.memory_cache[text_hash]))
                else:
                    texts_to_process.append(text)
                    cache_indices.append(i)
            
            # Generar embeddings para textos no cacheados
            new_embeddings = []
            if texts_to_process:
                logger.info(f"Generando embeddings para {len(texts_to_process)} textos")
                embeddings_array = self.model.encode(
                    texts_to_process,
                    convert_to_numpy=True,
                    show_progress_bar=len(texts_to_process) > 10
                )
                new_embeddings = embeddings_array.tolist()
                
                # Actualizar cache en memoria
                for text, embedding in zip(texts_to_process, new_embeddings):
                    text_hash = hash(text)
                    if len(self.memory_cache) >= self.max_cache_size:
                        # Eliminar entrada más antigua (FIFO simple)
                        oldest_key = next(iter(self.memory_cache))
                        del self.memory_cache[oldest_key]
                    self.memory_cache[text_hash] = embedding
            
            # Combinar embeddings cached y nuevos en el orden correcto
            final_embeddings = [None] * len(texts)
            
            # Insertar embeddings cacheados
            for idx, embedding in cached_embeddings:
                final_embeddings[idx] = embedding
            
            # Insertar embeddings nuevos
            for cache_idx, embedding in zip(cache_indices, new_embeddings):
                final_embeddings[cache_idx] = embedding
            
            return final_embeddings
            
        except Exception as e:
            logger.error(f"Error generando embeddings: {str(e)}")
            return []
    
    async def generate_single_embedding(self, text: str) -> List[float]:
        """
        Genera embedding para un solo texto
        
        Args:
            text: Texto para generar embedding
            
        Returns:
            List[float]: Vector de embedding
        """
        embeddings = await self.generate_embeddings([text])
        return embeddings[0] if embeddings else []
    
    def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calcula similitud coseno entre dos embeddings
        
        Args:
            embedding1: Primer vector
            embedding2: Segundo vector
            
        Returns:
            float: Similitud coseno (-1 a 1)
        """
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Similitud coseno
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error calculando similitud: {str(e)}")
            return 0.0
    
    async def save_embeddings_cache(self, chatbot_id: int, embeddings_data: Dict[str, Any]):
        """
        Guarda cache de embeddings para un chatbot específico
        
        Args:
            chatbot_id: ID del chatbot
            embeddings_data: Datos de embeddings para guardar
        """
        try:
            cache_file = os.path.join(self.cache_dir, f"chatbot_{chatbot_id}_embeddings.pkl")
            
            with open(cache_file, 'wb') as f:
                pickle.dump(embeddings_data, f)
            
            logger.info(f"Cache de embeddings guardado para chatbot {chatbot_id}")
            
        except Exception as e:
            logger.error(f"Error guardando cache de embeddings: {str(e)}")
    
    async def load_embeddings_cache(self, chatbot_id: int) -> Dict[str, Any]:
        """
        Carga cache de embeddings para un chatbot específico
        
        Args:
            chatbot_id: ID del chatbot
            
        Returns:
            Dict: Datos de embeddings cacheados
        """
        try:
            cache_file = os.path.join(self.cache_dir, f"chatbot_{chatbot_id}_embeddings.pkl")
            
            if os.path.exists(cache_file):
                with open(cache_file, 'rb') as f:
                    embeddings_data = pickle.load(f)
                
                logger.info(f"Cache de embeddings cargado para chatbot {chatbot_id}")
                return embeddings_data
            
            return {}
            
        except Exception as e:
            logger.error(f"Error cargando cache de embeddings: {str(e)}")
            return {}
    
    def get_model_info(self) -> Dict[str, Any]:
        """Retorna información sobre el modelo de embeddings"""
        return {
            "model_name": self.model_name,
            "dimension": self.dimension,
            "max_sequence_length": getattr(self.model, 'max_seq_length', 'N/A'),
            "cache_size": len(self.memory_cache)
        }
    
    def clear_cache(self):
        """Limpia el cache en memoria"""
        self.memory_cache.clear()
        logger.info("Cache de embeddings limpiado")
    
    def preprocess_text(self, text: str) -> str:
        """
        Preprocesa texto antes de generar embeddings
        
        Args:
            text: Texto a preprocesar
            
        Returns:
            str: Texto preprocesado
        """
        # Eliminar espacios extra
        text = ' '.join(text.split())
        
        # Limitar longitud (el modelo tiene un límite)
        max_length = getattr(self.model, 'max_seq_length', 512)
        if len(text) > max_length:
            # Truncar manteniendo palabras completas
            words = text[:max_length].split()
            text = ' '.join(words[:-1])  # Eliminar última palabra parcial
        
        return text.strip()


# Instancia global del servicio
embedding_service = EmbeddingService()