import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import pypdf
from docx import Document
import markdown
import re
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class DocumentProcessor:
    def __init__(self):
        """Inicializa el procesador de documentos"""
        
        self.chunk_size = int(os.getenv("CHUNK_SIZE", "1000"))
        self.chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "200"))
        self.allowed_extensions = os.getenv("ALLOWED_EXTENSIONS", "pdf,docx,txt,md").split(",")
        self.upload_folder = os.getenv("UPLOAD_FOLDER", "./uploads")
        
        # Crear carpeta de uploads si no existe
        Path(self.upload_folder).mkdir(exist_ok=True)
        
        logger.info(f"DocumentProcessor inicializado. Chunk size: {self.chunk_size}, Overlap: {self.chunk_overlap}")
    
    def is_valid_file_type(self, filename: str) -> bool:
        """
        Verifica si el tipo de archivo es válido
        
        Args:
            filename: Nombre del archivo
            
        Returns:
            bool: True si es válido
        """
        extension = filename.lower().split('.')[-1]
        return extension in self.allowed_extensions
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Obtiene información básica del archivo
        
        Args:
            file_path: Ruta del archivo
            
        Returns:
            Dict: Información del archivo
        """
        try:
            path_obj = Path(file_path)
            stat = path_obj.stat()
            
            return {
                "filename": path_obj.name,
                "extension": path_obj.suffix.lower(),
                "size_bytes": stat.st_size,
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "modified": datetime.fromtimestamp(stat.st_mtime),
                "exists": path_obj.exists()
            }
        except Exception as e:
            logger.error(f"Error obteniendo info del archivo {file_path}: {str(e)}")
            return {}
    
    async def extract_text_from_pdf(self, file_path: str) -> Dict[str, Any]:
        """
        Extrae texto de un archivo PDF
        
        Args:
            file_path: Ruta del archivo PDF
            
        Returns:
            Dict: Texto extraído y metadatos
        """
        try:
            with open(file_path, 'rb') as file:
                reader = pypdf.PdfReader(file)
                
                text_pages = []
                total_text = ""
                
                for page_num, page in enumerate(reader.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text.strip():
                            text_pages.append({
                                "page": page_num,
                                "text": page_text.strip()
                            })
                            total_text += page_text + "\n\n"
                    except Exception as e:
                        logger.warning(f"Error extrayendo página {page_num}: {str(e)}")
                        continue
                
                return {
                    "success": True,
                    "text": total_text.strip(),
                    "pages": text_pages,
                    "total_pages": len(reader.pages),
                    "extracted_pages": len(text_pages),
                    "metadata": {
                        "title": reader.metadata.get('/Title', '') if reader.metadata else '',
                        "author": reader.metadata.get('/Author', '') if reader.metadata else '',
                        "creator": reader.metadata.get('/Creator', '') if reader.metadata else ''
                    }
                }
                
        except Exception as e:
            logger.error(f"Error extrayendo texto de PDF {file_path}: {str(e)}")
            return {
                "success": False,
                "text": "",
                "pages": [],
                "error": str(e)
            }
    
    async def extract_text_from_docx(self, file_path: str) -> Dict[str, Any]:
        """
        Extrae texto de un archivo DOCX
        
        Args:
            file_path: Ruta del archivo DOCX
            
        Returns:
            Dict: Texto extraído y metadatos
        """
        try:
            doc = Document(file_path)
            
            paragraphs = []
            full_text = ""
            
            for para in doc.paragraphs:
                if para.text.strip():
                    paragraphs.append(para.text.strip())
                    full_text += para.text + "\n"
            
            return {
                "success": True,
                "text": full_text.strip(),
                "paragraphs": paragraphs,
                "total_paragraphs": len(paragraphs),
                "metadata": {
                    "title": doc.core_properties.title or '',
                    "author": doc.core_properties.author or '',
                    "created": doc.core_properties.created,
                    "modified": doc.core_properties.modified
                }
            }
            
        except Exception as e:
            logger.error(f"Error extrayendo texto de DOCX {file_path}: {str(e)}")
            return {
                "success": False,
                "text": "",
                "paragraphs": [],
                "error": str(e)
            }
    
    async def extract_text_from_txt(self, file_path: str) -> Dict[str, Any]:
        """
        Extrae texto de un archivo TXT
        
        Args:
            file_path: Ruta del archivo TXT
            
        Returns:
            Dict: Texto extraído
        """
        try:
            # Intentar diferentes encodings
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        content = file.read()
                        
                        return {
                            "success": True,
                            "text": content.strip(),
                            "encoding_used": encoding,
                            "lines": len(content.splitlines()),
                            "metadata": {}
                        }
                except UnicodeDecodeError:
                    continue
            
            # Si ningún encoding funcionó
            return {
                "success": False,
                "text": "",
                "error": "No se pudo decodificar el archivo con ningún encoding estándar"
            }
            
        except Exception as e:
            logger.error(f"Error extrayendo texto de TXT {file_path}: {str(e)}")
            return {
                "success": False,
                "text": "",
                "error": str(e)
            }
    
    async def extract_text_from_markdown(self, file_path: str) -> Dict[str, Any]:
        """
        Extrae texto de un archivo Markdown
        
        Args:
            file_path: Ruta del archivo MD
            
        Returns:
            Dict: Texto extraído
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                md_content = file.read()
            
            # Convertir Markdown a texto plano
            html = markdown.markdown(md_content)
            # Remover tags HTML básicos
            text = re.sub('<[^<]+?>', '', html)
            # Limpiar espacios extra
            text = re.sub(r'\n\s*\n', '\n\n', text)
            
            return {
                "success": True,
                "text": text.strip(),
                "original_markdown": md_content,
                "lines": len(md_content.splitlines()),
                "metadata": {}
            }
            
        except Exception as e:
            logger.error(f"Error extrayendo texto de Markdown {file_path}: {str(e)}")
            return {
                "success": False,
                "text": "",
                "error": str(e)
            }
    
    async def extract_text_from_file(self, file_path: str) -> Dict[str, Any]:
        """
        Extrae texto de un archivo según su extensión
        
        Args:
            file_path: Ruta del archivo
            
        Returns:
            Dict: Texto extraído y metadatos
        """
        file_info = self.get_file_info(file_path)
        if not file_info.get("exists"):
            return {"success": False, "error": "Archivo no encontrado"}
        
        extension = file_info.get("extension", "").lower()
        
        if extension == ".pdf":
            return await self.extract_text_from_pdf(file_path)
        elif extension == ".docx":
            return await self.extract_text_from_docx(file_path)
        elif extension == ".txt":
            return await self.extract_text_from_txt(file_path)
        elif extension == ".md":
            return await self.extract_text_from_markdown(file_path)
        else:
            return {
                "success": False,
                "error": f"Tipo de archivo no soportado: {extension}"
            }
    
    def create_text_chunks(
        self,
        text: str,
        metadata: Dict[str, Any] = None,
        preserve_paragraphs: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Divide texto en chunks para procesamiento RAG
        
        Args:
            text: Texto a dividir
            metadata: Metadatos adicionales
            preserve_paragraphs: Si preservar párrafos cuando sea posible
            
        Returns:
            List[Dict]: Lista de chunks con metadatos
        """
        if not text.strip():
            return []
        
        chunks = []
        metadata = metadata or {}
        
        if preserve_paragraphs:
            # Dividir por párrafos primero
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
            
            current_chunk = ""
            chunk_num = 1
            
            for paragraph in paragraphs:
                # Si el párrafo solo ya es muy largo, dividirlo
                if len(paragraph) > self.chunk_size:
                    # Guardar chunk actual si existe
                    if current_chunk:
                        chunks.append(self._create_chunk_dict(
                            current_chunk, chunk_num, metadata
                        ))
                        chunk_num += 1
                        current_chunk = ""
                    
                    # Dividir párrafo largo
                    para_chunks = self._split_large_text(paragraph)
                    for para_chunk in para_chunks:
                        chunks.append(self._create_chunk_dict(
                            para_chunk, chunk_num, metadata
                        ))
                        chunk_num += 1
                
                # Si agregar este párrafo excede el tamaño del chunk
                elif len(current_chunk) + len(paragraph) + 2 > self.chunk_size:
                    if current_chunk:
                        chunks.append(self._create_chunk_dict(
                            current_chunk, chunk_num, metadata
                        ))
                        chunk_num += 1
                    
                    # Comenzar nuevo chunk con overlap si es necesario
                    if self.chunk_overlap > 0 and current_chunk:
                        overlap_text = current_chunk[-self.chunk_overlap:]
                        current_chunk = overlap_text + "\n\n" + paragraph
                    else:
                        current_chunk = paragraph
                else:
                    # Agregar párrafo al chunk actual
                    if current_chunk:
                        current_chunk += "\n\n" + paragraph
                    else:
                        current_chunk = paragraph
            
            # Agregar último chunk si existe
            if current_chunk:
                chunks.append(self._create_chunk_dict(
                    current_chunk, chunk_num, metadata
                ))
        
        else:
            # División simple por caracteres
            text_chunks = self._split_large_text(text)
            for i, chunk_text in enumerate(text_chunks, 1):
                chunks.append(self._create_chunk_dict(chunk_text, i, metadata))
        
        logger.info(f"Texto dividido en {len(chunks)} chunks")
        return chunks
    
    def _split_large_text(self, text: str) -> List[str]:
        """Divide texto largo en chunks respetando palabras"""
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            if end >= len(text):
                chunks.append(text[start:])
                break
            
            # Buscar el último espacio antes del límite
            while end > start and text[end] != ' ':
                end -= 1
            
            if end == start:  # No se encontró espacio, cortar en el límite
                end = start + self.chunk_size
            
            chunks.append(text[start:end].strip())
            
            # Aplicar overlap
            start = end - self.chunk_overlap if self.chunk_overlap > 0 else end
            start = max(start, 0)
        
        return chunks
    
    def _create_chunk_dict(
        self,
        text: str,
        chunk_number: int,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Crea diccionario de chunk con metadatos"""
        return {
            "text": text.strip(),
            "chunk_number": chunk_number,
            "char_count": len(text),
            "word_count": len(text.split()),
            "metadata": {
                **metadata,
                "chunk_size": len(text),
                "processed_at": datetime.now().isoformat()
            }
        }
    
    def get_supported_extensions(self) -> List[str]:
        """Retorna lista de extensiones soportadas"""
        return self.allowed_extensions.copy()


# Instancia global del servicio
document_processor = DocumentProcessor()