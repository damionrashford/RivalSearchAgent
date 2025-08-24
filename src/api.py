"""
RivalSearch Agent API Server - HTTP API for agent integration.

Provides REST API endpoints for:
- Chat with streaming responses
- Document upload and management
- Session management
"""

import asyncio
import json
import logging
import os
from typing import List, Optional
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from .core.agent import RivalSearchAgent
from .core.config import AgentConfig
from .core.services.rag_service import RAGService, RAGDependencies

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="RivalSearch Agent API",
    description="API for RivalSearch Agent with RAG capabilities",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global agent instance
_agent = None
_rag_dependencies = {}
_memory_service = None

# Pydantic models
class ChatRequest(BaseModel):
    message: str
    session_id: str
    thread_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str

class SessionResponse(BaseModel):
    session_id: str
    created_at: str

class DocumentResponse(BaseModel):
    file_name: str
    chunks_stored: int
    success: bool
    error: Optional[str] = None

async def get_agent() -> RivalSearchAgent:
    """Get or create agent instance."""
    global _agent
    if _agent is None:
        config = AgentConfig()
        _agent = RivalSearchAgent(config)
        await _agent.initialize()
        logger.info("Agent initialized successfully")
    return _agent

async def get_rag_service(session_id: str) -> RAGService:
    """Get or create RAG service for session."""
    if session_id not in _rag_dependencies:
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise HTTPException(status_code=500, detail="DATABASE_URL not configured")
        
        deps = RAGDependencies(
            database_url=database_url,
            session_id=session_id
        )
        _rag_dependencies[session_id] = RAGService(deps)
    
    return _rag_dependencies[session_id]

async def get_memory_service():
    """Get or create memory service."""
    global _memory_service
    if _memory_service is None:
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise HTTPException(status_code=500, detail="DATABASE_URL not configured")
        
        from .core.services.memory_service import CompleteMemoryService
        _memory_service = CompleteMemoryService(database_url)
    
    return _memory_service

@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "message": "RivalSearch Agent API",
        "version": "1.0.0",
        "endpoints": {
            "chat": "/api/chat/stream",
            "sessions": "/api/sessions",
            "upload": "/api/upload-document",
            "documents": "/api/documents/{session_id}"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "agent": "ready"}

@app.post("/api/sessions", response_model=SessionResponse)
async def create_session():
    """Create a new chat session."""
    import uuid
    from datetime import datetime
    
    session_id = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat()
    
    logger.info(f"Created new session: {session_id}")
    
    return SessionResponse(
        session_id=session_id,
        created_at=created_at
    )

@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """Stream chat response from agent."""
    try:
        agent = await get_agent()
        
        # Get memory service
        memory_service = await get_memory_service()
        
        # Create session if it doesn't exist
        await memory_service.create_session(request.session_id)
        
        # Get complete conversation history
        message_history = await memory_service.get_conversation_as_pydantic_messages(request.session_id)
        
        # Add user message to history
        await memory_service.add_message(request.session_id, 'user', request.message)
        
        # Get RAG service for session
        rag_service = await get_rag_service(request.session_id)
        
        # Create RAG tools for this session
        from .core.services.rag_service import create_rag_tools
        rag_tools = create_rag_tools(rag_service.deps)
        
        # Add RAG tools to agent temporarily
        original_tools = getattr(agent, '_tools', [])
        agent._tools = original_tools + rag_tools
        
        try:
            # Stream response
            async def generate():
                full_response = ""
                async for text_chunk in agent.run_stream(
                    request.message, 
                    session_id=request.session_id,
                    thread_id=request.thread_id
                ):
                    full_response += text_chunk
                    yield f"data: {json.dumps({'text': text_chunk})}\n\n"
                
                # Store assistant response in memory
                await memory_service.add_message(request.session_id, 'assistant', full_response)
                yield "data: [DONE]\n\n"
            
            return StreamingResponse(
                generate(),
                media_type="text/plain",
                headers={"Cache-Control": "no-cache"}
            )
            
        finally:
            # Restore original tools
            agent._tools = original_tools
            
    except Exception as e:
        logger.error(f"Error in chat stream: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload-document", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    session_id: str = Form(...)
):
    """Upload a document for RAG processing."""
    try:
        # Read file content
        file_content = await file.read()
        
        # Get RAG service
        rag_service = await get_rag_service(session_id)
        
        # Process document
        result = await rag_service.process_uploaded_document(
            file_content=file_content,
            file_name=file.filename
        )
        
        if result["success"]:
            logger.info(f"Document uploaded successfully: {file.filename}")
            return DocumentResponse(
                file_name=file.filename,
                chunks_stored=result["chunks_stored"],
                success=True
            )
        else:
            logger.error(f"Document upload failed: {result.get('error')}")
            return DocumentResponse(
                file_name=file.filename,
                chunks_stored=0,
                success=False,
                error=result.get('error')
            )
            
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents/{session_id}")
async def get_session_documents(session_id: str):
    """Get documents for a session."""
    try:
        rag_service = await get_rag_service(session_id)
        documents = await rag_service.get_session_documents()
        
        return {
            "session_id": session_id,
            "documents": documents,
            "count": len(documents)
        }
        
    except Exception as e:
        logger.error(f"Error getting documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/documents/{session_id}")
async def delete_session_documents(
    session_id: str,
    file_name: Optional[str] = None
):
    """Delete documents for a session."""
    try:
        rag_service = await get_rag_service(session_id)
        success = await rag_service.delete_documents(file_name)
        
        if success:
            return {"message": "Documents deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete documents")
            
    except Exception as e:
        logger.error(f"Error deleting documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/conversations/{session_id}")
async def get_conversation_history(session_id: str):
    """Get complete conversation history for a session."""
    try:
        memory_service = await get_memory_service()
        messages = await memory_service.get_complete_conversation(session_id)
        
        return {
            "session_id": session_id,
            "messages": messages,
            "count": len(messages)
        }
        
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/conversations")
async def list_conversations(limit: int = 50):
    """List all conversation sessions."""
    try:
        memory_service = await get_memory_service()
        sessions = await memory_service.list_sessions(limit)
        
        return {
            "sessions": sessions,
            "count": len(sessions)
        }
        
    except Exception as e:
        logger.error(f"Error listing conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/conversations/{session_id}")
async def delete_conversation(session_id: str):
    """Delete a conversation session and all its messages."""
    try:
        memory_service = await get_memory_service()
        success = await memory_service.delete_session(session_id)
        
        if success:
            return {"message": "Conversation deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Session not found")
            
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def start_server(host: str = "0.0.0.0", port: int = 8000):
    """Start the API server."""
    logger.info(f"Starting RivalSearch Agent API server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    start_server()
