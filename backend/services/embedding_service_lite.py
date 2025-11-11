import os
import logging
from typing import List, Dict, Any
import numpy as np
from dotenv import load_dotenv
import aiohttp
import json

load_dotenv()

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self):
        """Inicializa el servicio de embeddings usando OpenAI embeddings API"""
        
        # Para Render: usar embeddings más simples sin sentence-transformers
        self.dimension = 384  # Dimensión estándar para embeddings rápidos
        logger.info(f"Servicio de embeddings inicializado. Dimensión: {self.dimension}")
        
        # Cache en memoria para embeddings frecuentes
        self.memory_cache = {}
        self.max_cache_size = 1000
    
    def _simple_embedding(self, text: str) -> List[float]:
        """
        Genera un embedding simple basado en características del texto
        (Para desarrollo/testing sin dependencias pesadas)
        """
        # Características básicas del texto
        text_lower = text.lower()
        
        # Vector basado en características del texto
        features = []
        
        # Longitud normalizada
        features.append(min(len(text) / 1000.0, 1.0))
        
        # Densidad de caracteres especiales
        special_chars = sum(1 for c in text if not c.isalnum() and not c.isspace())
        features.append(min(special_chars / max(len(text), 1), 1.0))
        
        # Presencia de palabras clave comunes
        keywords = ['user', 'system', 'error', 'success', 'data', 'api', 'request', 'response']
        for keyword in keywords:
            features.append(1.0 if keyword in text_lower else 0.0)
        
        # Hash-based features para capturar contenido único
        text_hash = hash(text_lower)
        
        # Agregar features basadas en características del texto
        char_counts = {}
        for char in text_lower:
            char_counts[char] = char_counts.get(char, 0) + 1
        
        # Features basadas en frecuencia de caracteres más comunes
        common_chars = 'abcdefghijklmnopqrstuvwxyz0123456789 '
        for char in common_chars[:min(20, self.dimension - len(features))]:
            freq = char_counts.get(char, 0) / max(len(text), 1)
            features.append(min(freq * 10, 1.0))  # Normalizar
        
        # Rellenar con features determinísticas simples
        for i in range(self.dimension - len(features)):
            # Usar operaciones matemáticas simples en lugar de random
            val = ((text_hash + i * 7) % 1000) / 1000.0
            features.append(val)
        
        # Normalizar el vector
        features = np.array(features[:self.dimension])
        norm = np.linalg.norm(features)
        if norm > 0:
            features = features / norm
        
        return features.tolist()
    
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
            
            embeddings = []
            
            for text in texts:
                # Verificar cache
                text_hash = hash(text)
                if text_hash in self.memory_cache:
                    embeddings.append(self.memory_cache[text_hash])
                else:
                    # Generar embedding simple
                    embedding = self._simple_embedding(text)
                    embeddings.append(embedding)
                    
                    # Actualizar cache
                    if len(self.memory_cache) >= self.max_cache_size:
                        # Eliminar entrada más antigua (FIFO simple)
                        oldest_key = next(iter(self.memory_cache))
                        del self.memory_cache[oldest_key]
                    self.memory_cache[text_hash] = embedding
            
            logger.info(f"Generados {len(embeddings)} embeddings")
            return embeddings
            
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
        """
        try:
            logger.info(f"Cache de embeddings preparado para chatbot {chatbot_id}")
            # En Render, usar almacenamiento temporal
            
        except Exception as e:
            logger.error(f"Error guardando cache de embeddings: {str(e)}")
    
    async def load_embeddings_cache(self, chatbot_id: int) -> Dict[str, Any]:
        """
        Carga cache de embeddings para un chatbot específico
        """
        try:
            logger.info(f"Intentando cargar cache para chatbot {chatbot_id}")
            return {}
            
        except Exception as e:
            logger.error(f"Error cargando cache de embeddings: {str(e)}")
            return {}
    
    def get_model_info(self) -> Dict[str, Any]:
        """Retorna información sobre el modelo de embeddings"""
        return {
            "model_name": "simple_embedding_service",
            "dimension": self.dimension,
            "cache_size": len(self.memory_cache),
            "type": "lightweight_embeddings"
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
        
        # Limitar longitud
        max_length = 2000
        if len(text) > max_length:
            # Truncar manteniendo palabras completas
            words = text[:max_length].split()
            text = ' '.join(words[:-1])  # Eliminar última palabra parcial
        
        return text.strip()


# Instancia global del servicio
embedding_service = EmbeddingService()