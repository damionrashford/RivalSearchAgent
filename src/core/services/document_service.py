"""
Document processing service for RAG functionality.

This service handles:
- Document upload and processing
- Text chunking and embedding generation
- Vector storage and retrieval
"""

import hashlib
import json
import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any, BinaryIO
from urllib.parse import urlparse

import asyncpg
from pydantic import BaseModel

logger = logging.getLogger(__name__)

@dataclass
class DocumentChunk:
    """Represents a chunk of document content with metadata."""
    content: str
    chunk_index: int
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None

class DocumentProcessor:
    """Handles document processing for RAG functionality."""
    
    def __init__(self, database_url: str, embedding_model: str = "BAAI/bge-small-en-v1.5"):
        self.database_url = database_url
        self.embedding_model = embedding_model
        self.chunk_size = 1000  # characters per chunk
        self.chunk_overlap = 200  # characters overlap between chunks
        
    async def process_document(
        self, 
        file_content: bytes, 
        file_name: str, 
        session_id: str,
        file_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a document file and store its chunks with embeddings.
        
        Args:
            file_content: Raw file content
            file_name: Name of the uploaded file
            session_id: Session ID
            file_type: MIME type of the file
            
        Returns:
            Processing result with metadata
        """
        try:
            # Determine file type if not provided
            if not file_type:
                file_type = self._infer_file_type(file_name, file_content)
            
            # Extract text content based on file type
            text_content = await self._extract_text(file_content, file_type, file_name)
            
            # Chunk the text
            chunks = self._chunk_text(text_content, file_name)
            
            # Generate embeddings for chunks
            await self._generate_embeddings(chunks)
            
            # Store chunks in database
            stored_chunks = await self._store_chunks(chunks, session_id, file_name)
            
            return {
                "success": True,
                "file_name": file_name,
                "file_type": file_type,
                "chunks_processed": len(chunks),
                "chunks_stored": stored_chunks,
                "total_content_length": len(text_content)
            }
            
        except Exception as e:
            logger.error(f"Error processing document {file_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "file_name": file_name
            }
    
    def _infer_file_type(self, file_name: str, content: bytes) -> str:
        """Infer the MIME type of a file based on its name and content."""
        # Check file extension first
        file_ext = Path(file_name).suffix.lower()
        
        if file_ext == '.pdf':
            return 'application/pdf'
        elif file_ext in ['.doc', '.docx']:
            return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        elif file_ext == '.rtf':
            return 'application/rtf'
        elif file_ext in ['.txt', '.md']:
            return 'text/plain'
        else:
            # Try to infer from content
            if content.startswith(b'%PDF'):
                return 'application/pdf'
            elif content.startswith(b'PK'):
                return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            elif content.startswith(b'{\\rtf'):
                return 'application/rtf'
            else:
                return 'text/plain'
    
    async def _extract_text(self, content: bytes, file_type: str, file_name: str) -> str:
        """Extract text content from different file types."""
        try:
            if file_type == 'application/pdf':
                return await self._extract_pdf_text(content)
            elif file_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                return await self._extract_docx_text(content)
            elif file_type == 'application/rtf':
                return await self._extract_rtf_text(content)
            else:
                # Assume plain text
                return content.decode('utf-8', errors='ignore')
                
        except Exception as e:
            logger.error(f"Error extracting text from {file_name}: {e}")
            raise
    
    async def _extract_pdf_text(self, content: bytes) -> str:
        """Extract text from PDF content."""
        try:
            import PyPDF2
            from io import BytesIO
            
            pdf_file = BytesIO(content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            return text.strip()
            
        except ImportError:
            raise ImportError("PyPDF2 is required for PDF processing. Install with: pip install PyPDF2")
    
    async def _extract_docx_text(self, content: bytes) -> str:
        """Extract text from DOCX content."""
        try:
            from docx import Document
            from io import BytesIO
            
            doc_file = BytesIO(content)
            doc = Document(doc_file)
            
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            
            return text.strip()
            
        except ImportError:
            raise ImportError("python-docx is required for DOCX processing. Install with: pip install python-docx")
    
    async def _extract_rtf_text(self, content: bytes) -> str:
        """Extract text from RTF content."""
        try:
            import striprtf
            from striprtf.striprtf import rtf_to_text
            
            rtf_text = content.decode('utf-8', errors='ignore')
            plain_text = rtf_to_text(rtf_text)
            return plain_text.strip()
            
        except ImportError:
            raise ImportError("striprtf is required for RTF processing. Install with: pip install striprtf")
    
    def _chunk_text(self, text: str, file_name: str) -> List[DocumentChunk]:
        """Split text into overlapping chunks."""
        chunks = []
        chunk_index = 0
        
        # Clean and normalize text
        text = re.sub(r'\s+', ' ', text).strip()
        
        if len(text) <= self.chunk_size:
            # Single chunk for short text
            chunks.append(DocumentChunk(
                content=text,
                chunk_index=chunk_index,
                metadata={
                    "file_name": file_name,
                    "chunk_size": len(text),
                    "total_chunks": 1
                }
            ))
        else:
            # Split into overlapping chunks
            start = 0
            while start < len(text):
                end = start + self.chunk_size
                
                # Try to break at sentence boundary
                if end < len(text):
                    # Look for sentence endings
                    sentence_end = text.rfind('.', start, end)
                    if sentence_end > start + self.chunk_size * 0.7:  # At least 70% of chunk size
                        end = sentence_end + 1
                
                chunk_text = text[start:end].strip()
                if chunk_text:
                    chunks.append(DocumentChunk(
                        content=chunk_text,
                        chunk_index=chunk_index,
                        metadata={
                            "file_name": file_name,
                            "chunk_size": len(chunk_text),
                            "total_chunks": len(chunks) + 1
                        }
                    ))
                    chunk_index += 1
                
                # Move start position with overlap
                start = end - self.chunk_overlap
                if start >= len(text):
                    break
        
        return chunks
    
    async def _generate_embeddings(self, chunks: List[DocumentChunk]) -> None:
        """Generate embeddings for document chunks using BGE model."""
        try:
            # Import SentenceTransformers
            from sentence_transformers import SentenceTransformer
            
            # Initialize BGE model (load once and reuse)
            if not hasattr(self, '_embedding_model'):
                logger.info("Loading BGE embedding model...")
                self._embedding_model = SentenceTransformer('BAAI/bge-small-en-v1.5')
                logger.info("BGE embedding model loaded successfully")
            
            # Generate embeddings for all chunks
            texts = [chunk.content for chunk in chunks]
            embeddings = self._embedding_model.encode(texts, convert_to_tensor=False)
            
            # Assign embeddings to chunks
            for i, chunk in enumerate(chunks):
                chunk.embedding = embeddings[i].tolist()
                    
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise
    
    async def _store_chunks(self, chunks: List[DocumentChunk], session_id: str, file_name: str) -> int:
        """Store document chunks with embeddings in the database."""
        try:
            # Connect to database
            conn = await asyncpg.connect(self.database_url)
            
            stored_count = 0
            
            for chunk in chunks:
                if chunk.embedding:
                    # Convert embedding to JSON string for storage
                    embedding_json = json.dumps(chunk.embedding)
                    
                    # Insert chunk into database
                    await conn.execute("""
                        INSERT INTO document_chunks 
                        (session_id, file_name, chunk_index, content, embedding, metadata)
                        VALUES ($1, $2, $3, $4, $5, $6)
                        ON CONFLICT (session_id, file_name, chunk_index) 
                        DO UPDATE SET 
                            content = EXCLUDED.content,
                            embedding = EXCLUDED.embedding,
                            metadata = EXCLUDED.metadata
                    """, session_id, file_name, chunk.chunk_index, 
                         chunk.content, embedding_json, json.dumps(chunk.metadata))
                    
                    stored_count += 1
            
            await conn.close()
            return stored_count
            
        except Exception as e:
            logger.error(f"Error storing chunks: {e}")
            raise
    
    async def search_documents(self, query: str, session_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for relevant document chunks using vector similarity.
        
        Args:
            query: Search query
            session_id: Session ID
            limit: Maximum number of results to return
            
        Returns:
            List of relevant document chunks with metadata
        """
        try:
            # Generate embedding for the query
            query_chunk = DocumentChunk(content=query, chunk_index=0, metadata={})
            await self._generate_embeddings([query_chunk])
            
            if not query_chunk.embedding:
                return []
            
            # Connect to database
            conn = await asyncpg.connect(self.database_url)
            
            # Search for similar chunks
            embedding_json = json.dumps(query_chunk.embedding)
            
            rows = await conn.fetch("""
                SELECT 
                    dc.content,
                    dc.file_name,
                    dc.chunk_index,
                    dc.metadata,
                    dc.embedding <-> $1 as distance
                FROM document_chunks dc
                WHERE dc.session_id = $2
                ORDER BY dc.embedding <-> $1
                LIMIT $3
            """, embedding_json, session_id, limit)
            
            await conn.close()
            
            # Convert results to list of dictionaries
            results = []
            for row in rows:
                results.append({
                    "content": row['content'],
                    "file_name": row['file_name'],
                    "chunk_index": row['chunk_index'],
                    "metadata": row['metadata'],
                    "distance": float(row['distance'])
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
    
    async def get_session_documents(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all documents uploaded for a specific session."""
        try:
            conn = await asyncpg.connect(self.database_url)
            
            rows = await conn.fetch("""
                SELECT DISTINCT 
                    file_name,
                    COUNT(*) as chunk_count,
                    MIN(created_at) as first_uploaded,
                    MAX(created_at) as last_updated
                FROM document_chunks
                WHERE session_id = $1
                GROUP BY file_name
                ORDER BY first_uploaded DESC
            """, session_id)
            
            await conn.close()
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Error getting session documents: {e}")
            return []
    
    async def delete_session_documents(self, session_id: str, file_name: Optional[str] = None) -> bool:
        """Delete documents for a session (or specific file)."""
        try:
            conn = await asyncpg.connect(self.database_url)
            
            if file_name:
                await conn.execute("""
                    DELETE FROM document_chunks 
                    WHERE session_id = $1 AND file_name = $2
                """, session_id, file_name)
            else:
                await conn.execute("""
                    DELETE FROM document_chunks 
                    WHERE session_id = $1
                """, session_id)
            
            await conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error deleting session documents: {e}")
            return False
