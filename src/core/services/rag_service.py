"""
RAG (Retrieval-Augmented Generation) service for the agent.

This service provides document search and retrieval capabilities to enhance
the agent's responses with relevant document content.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from pydantic_ai import RunContext
from pydantic_ai.messages import ToolReturn

from .document_service import DocumentProcessor

logger = logging.getLogger(__name__)

@dataclass
class RAGDependencies:
    """Dependencies for RAG functionality."""
    database_url: str
    session_id: str
    embedding_model: str = "text-embedding-3-small"

class RAGService:
    """Service for RAG functionality in the agent."""
    
    def __init__(self, deps: RAGDependencies):
        self.deps = deps
        self.document_processor = DocumentProcessor(
            database_url=deps.database_url,
            embedding_model=deps.embedding_model
        )
    
    async def search_documents(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search for relevant document chunks.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of relevant document chunks
        """
        try:
            results = await self.document_processor.search_documents(
                query=query,
                session_id=self.deps.session_id,
                limit=limit
            )
            
            logger.info(f"RAG search found {len(results)} relevant chunks for query: {query}")
            return results
            
        except Exception as e:
            logger.error(f"Error in RAG search: {e}")
            return []
    
    async def get_session_documents(self) -> List[Dict[str, Any]]:
        """Get all documents uploaded for the current session."""
        try:
            return await self.document_processor.get_session_documents(self.deps.session_id)
        except Exception as e:
            logger.error(f"Error getting session documents: {e}")
            return []
    
    async def process_uploaded_document(
        self, 
        file_content: bytes, 
        file_name: str, 
        file_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process an uploaded document and store it for RAG.
        
        Args:
            file_content: Raw file content
            file_name: Name of the uploaded file
            file_type: MIME type of the file
            
        Returns:
            Processing result
        """
        try:
            result = await self.document_processor.process_document(
                file_content=file_content,
                file_name=file_name,
                session_id=self.deps.session_id,
                file_type=file_type
            )
            
            if result["success"]:
                logger.info(f"Successfully processed document {file_name} with {result['chunks_stored']} chunks")
            else:
                logger.error(f"Failed to process document {file_name}: {result.get('error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing uploaded document: {e}")
            return {
                "success": False,
                "error": str(e),
                "file_name": file_name
            }
    
    async def delete_documents(self, file_name: Optional[str] = None) -> bool:
        """
        Delete documents for the current session.
        
        Args:
            file_name: Specific file to delete (if None, delete all)
            
        Returns:
            Success status
        """
        try:
            return await self.document_processor.delete_session_documents(
                session_id=self.deps.session_id,
                file_name=file_name
            )
        except Exception as e:
            logger.error(f"Error deleting documents: {e}")
            return False

def create_rag_tools(deps: RAGDependencies):
    """
    Create RAG tools for the agent.
    
    Args:
        deps: RAG dependencies
        
    Returns:
        List of tool functions
    """
    rag_service = RAGService(deps)
    
    async def search_documents_tool(ctx: RunContext[RAGDependencies], query: str, limit: int = 5) -> str:
        """
        Search for relevant document chunks based on a query.
        
        Args:
            ctx: Run context with RAG dependencies
            query: Search query to find relevant documents
            limit: Maximum number of results to return (default: 5)
            
        Returns:
            Formatted string with relevant document content
        """
        try:
            results = await rag_service.search_documents(query, limit)
            
            if not results:
                return "No relevant documents found for your query."
            
            # Format results for the model
            formatted_results = []
            for i, result in enumerate(results, 1):
                formatted_results.append(
                    f"Document {i}: {result['file_name']} (Chunk {result['chunk_index']})\n"
                    f"Relevance Score: {1 - result['distance']:.3f}\n"
                    f"Content:\n{result['content']}\n"
                )
            
            return f"Found {len(results)} relevant document chunks:\n\n" + "\n---\n".join(formatted_results)
            
        except Exception as e:
            logger.error(f"Error in search_documents_tool: {e}")
            return f"Error searching documents: {str(e)}"
    
    async def list_documents_tool(ctx: RunContext[RAGDependencies]) -> str:
        """
        List all documents uploaded for the current session.
        
        Args:
            ctx: Run context with RAG dependencies
            
        Returns:
            Formatted string with document list
        """
        try:
            documents = await rag_service.get_session_documents()
            
            if not documents:
                return "No documents have been uploaded for this session."
            
            formatted_docs = []
            for i, doc in enumerate(documents, 1):
                formatted_docs.append(
                    f"{i}. {doc['file_name']}\n"
                    f"   Chunks: {doc['chunk_count']}\n"
                    f"   Uploaded: {doc['first_uploaded']}\n"
                    f"   Last Updated: {doc['last_updated']}"
                )
            
            return f"Documents in this session ({len(documents)} total):\n\n" + "\n\n".join(formatted_docs)
            
        except Exception as e:
            logger.error(f"Error in list_documents_tool: {e}")
            return f"Error listing documents: {str(e)}"
    
    async def delete_documents_tool(ctx: RunContext[RAGDependencies], file_name: Optional[str] = None) -> str:
        """
        Delete documents for the current session.
        
        Args:
            ctx: Run context with RAG dependencies
            file_name: Specific file to delete (if None, delete all)
            
        Returns:
            Confirmation message
        """
        try:
            success = await rag_service.delete_documents(file_name)
            
            if success:
                if file_name:
                    return f"Successfully deleted document: {file_name}"
                else:
                    return "Successfully deleted all documents for this session."
            else:
                return "Failed to delete documents."
                
        except Exception as e:
            logger.error(f"Error in delete_documents_tool: {e}")
            return f"Error deleting documents: {str(e)}"
    
    return [
        search_documents_tool,
        list_documents_tool,
        delete_documents_tool
    ]

def create_rag_tool_return(query: str, results: List[Dict[str, Any]]) -> ToolReturn:
    """
    Create a ToolReturn with RAG search results.
    
    Args:
        query: Original search query
        results: Search results
        
    Returns:
        ToolReturn with formatted content
    """
    if not results:
        return ToolReturn(
            return_value="No relevant documents found.",
            content="No relevant documents were found for your query."
        )
    
    # Format results for the model
    formatted_results = []
    for i, result in enumerate(results, 1):
        formatted_results.append(
            f"Document {i}: {result['file_name']} (Chunk {result['chunk_index']})\n"
            f"Relevance Score: {1 - result['distance']:.3f}\n"
            f"Content:\n{result['content']}\n"
        )
    
    content = f"Found {len(results)} relevant document chunks for query '{query}':\n\n" + "\n---\n".join(formatted_results)
    
    return ToolReturn(
        return_value=f"Found {len(results)} relevant document chunks",
        content=content,
        metadata={
            "query": query,
            "results_count": len(results),
            "results": results
        }
    )
