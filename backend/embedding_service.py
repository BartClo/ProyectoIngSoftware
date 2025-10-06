# embedding_service.py
import os
import pickle
import hashlib
from typing import List, Dict, Optional, Tuple
from sentence_transformers import SentenceTransformer
import numpy as np
from pypdf import PdfReader
import glob
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmbeddingService:
    """
    Servicio para generar embeddings usando Hugging Face (gratuito)
    y gestionar el caché local para evitar regenerar embeddings
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Inicializa el servicio de embeddings
        
        Args:
            model_name: Modelo de Hugging Face para embeddings (gratuito)
        """
        self.model_name = model_name
        self.model = None
        self.context_dir = os.path.join(os.path.dirname(__file__), "context_docs")
        self.cache_dir = os.path.join(os.path.dirname(__file__), "embeddings_cache")
        self.metadata_file = os.path.join(self.cache_dir, "metadata.pkl")
        
        # Crear directorio de caché si no existe
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def _load_model(self):
        """Carga el modelo de embeddings solo cuando es necesario"""
        if self.model is None:
            logger.info(f"Cargando modelo de embeddings: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info("Modelo cargado exitosamente")
    
    def _get_file_hash(self, file_path: str) -> str:
        """Genera un hash MD5 de un archivo para detectar cambios"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Divide el texto en chunks con superposición"""
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = min(start + chunk_size, text_length)
            chunks.append(text[start:end])
            
            if end == text_length:
                break
                
            start = end - overlap
            if start < 0:
                start = 0
        
        return chunks
    
    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extrae texto de un archivo PDF"""
        try:
            reader = PdfReader(pdf_path)
            pages_text = [page.extract_text() or "" for page in reader.pages]
            full_text = "\n".join(pages_text)
            
            # Si el texto está vacío, intentar OCR como fallback
            if not full_text.strip():
                logger.warning(f"No se pudo extraer texto de {pdf_path} con PyPDF")
                # Aquí podrías agregar OCR como fallback si es necesario
                
            return full_text
        except Exception as e:
            logger.error(f"Error al extraer texto de {pdf_path}: {e}")
            return ""
    
    def _load_documents(self) -> List[Dict]:
        """Carga y procesa todos los documentos PDF del directorio"""
        documents = []
        
        if not os.path.isdir(self.context_dir):
            logger.warning(f"Directorio de contexto no encontrado: {self.context_dir}")
            return documents
        
        pdf_paths = sorted(glob.glob(os.path.join(self.context_dir, "*.pdf")))
        logger.info(f"Encontrados {len(pdf_paths)} archivos PDF")
        
        for pdf_path in pdf_paths:
            filename = os.path.basename(pdf_path)
            file_hash = self._get_file_hash(pdf_path)
            
            logger.info(f"Procesando: {filename}")
            full_text = self._extract_text_from_pdf(pdf_path)
            
            if full_text.strip():
                chunks = self._chunk_text(full_text)
                
                for i, chunk in enumerate(chunks):
                    if chunk.strip():  # Solo agregar chunks no vacíos
                        documents.append({
                            "id": f"{filename}_chunk_{i}",
                            "text": chunk.strip(),
                            "source": filename,
                            "chunk_index": i,
                            "file_hash": file_hash
                        })
                
                logger.info(f"Extraídos {len(chunks)} chunks de {filename}")
            else:
                logger.warning(f"No se pudo extraer texto útil de {filename}")
        
        logger.info(f"Total de chunks procesados: {len(documents)}")
        return documents
    
    def _load_metadata(self) -> Optional[Dict]:
        """Carga metadatos del caché"""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, "rb") as f:
                    return pickle.load(f)
            except Exception as e:
                logger.error(f"Error al cargar metadatos: {e}")
        return None
    
    def _save_metadata(self, metadata: Dict):
        """Guarda metadatos del caché"""
        try:
            with open(self.metadata_file, "wb") as f:
                pickle.dump(metadata, f)
        except Exception as e:
            logger.error(f"Error al guardar metadatos: {e}")
    
    def _needs_reprocessing(self, documents: List[Dict]) -> bool:
        """Determina si los documentos necesitan ser reprocesados"""
        metadata = self._load_metadata()
        
        if not metadata:
            logger.info("No hay metadatos previos, se requiere procesamiento")
            return True
        
        # Verificar si el modelo cambió
        if metadata.get("model_name") != self.model_name:
            logger.info("Modelo cambió, se requiere reprocesamiento")
            return True
        
        # Verificar hashes de archivos
        current_hashes = {doc["source"]: doc["file_hash"] for doc in documents}
        stored_hashes = metadata.get("file_hashes", {})
        
        if current_hashes != stored_hashes:
            logger.info("Archivos cambiaron, se requiere reprocesamiento")
            return True
        
        # Verificar que existen los embeddings
        embeddings_file = os.path.join(self.cache_dir, "embeddings.pkl")
        documents_file = os.path.join(self.cache_dir, "documents.pkl")
        
        if not (os.path.exists(embeddings_file) and os.path.exists(documents_file)):
            logger.info("Archivos de caché faltantes, se requiere reprocesamiento")
            return True
        
        logger.info("Usando embeddings en caché")
        return False
    
    def generate_embeddings(self, force_refresh: bool = False) -> Tuple[np.ndarray, List[Dict]]:
        """
        Genera embeddings para todos los documentos
        
        Args:
            force_refresh: Si True, regenera embeddings incluso si existe caché
            
        Returns:
            Tuple de (embeddings_matrix, documents_list)
        """
        logger.info("Iniciando generación/carga de embeddings")
        
        # Cargar documentos
        documents = self._load_documents()
        
        if not documents:
            logger.warning("No se encontraron documentos válidos")
            return np.array([]), []
        
        # Verificar si necesitamos reprocesar
        if not force_refresh and not self._needs_reprocessing(documents):
            # Cargar desde caché
            try:
                embeddings_file = os.path.join(self.cache_dir, "embeddings.pkl")
                documents_file = os.path.join(self.cache_dir, "documents.pkl")
                
                with open(embeddings_file, "rb") as f:
                    embeddings = pickle.load(f)
                
                with open(documents_file, "rb") as f:
                    cached_documents = pickle.load(f)
                
                logger.info(f"Embeddings cargados desde caché: {embeddings.shape}")
                return embeddings, cached_documents
                
            except Exception as e:
                logger.error(f"Error al cargar caché: {e}")
                # Continuar con generación
        
        # Generar nuevos embeddings
        logger.info("Generando nuevos embeddings")
        self._load_model()
        
        # Extraer textos para embeddings
        texts = [doc["text"] for doc in documents]
        
        # Generar embeddings en lotes para eficiencia
        logger.info("Generando embeddings con Hugging Face...")
        embeddings = self.model.encode(
            texts,
            batch_size=32,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        
        # Guardar en caché
        try:
            embeddings_file = os.path.join(self.cache_dir, "embeddings.pkl")
            documents_file = os.path.join(self.cache_dir, "documents.pkl")
            
            with open(embeddings_file, "wb") as f:
                pickle.dump(embeddings, f)
            
            with open(documents_file, "wb") as f:
                pickle.dump(documents, f)
            
            # Guardar metadatos
            file_hashes = {doc["source"]: doc["file_hash"] for doc in documents}
            metadata = {
                "model_name": self.model_name,
                "file_hashes": file_hashes,
                "num_documents": len(documents),
                "embedding_dim": embeddings.shape[1] if len(embeddings) > 0 else 0
            }
            self._save_metadata(metadata)
            
            logger.info(f"Embeddings guardados en caché: {embeddings.shape}")
            
        except Exception as e:
            logger.error(f"Error al guardar caché: {e}")
        
        return embeddings, documents
    
    def get_embedding(self, text: str) -> np.ndarray:
        """
        Genera embedding para un texto específico
        
        Args:
            text: Texto para generar embedding
            
        Returns:
            Vector de embedding
        """
        self._load_model()
        return self.model.encode([text], convert_to_numpy=True)[0]