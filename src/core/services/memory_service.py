"""
Complete Conversation Memory Service

This service ensures the agent NEVER forgets any part of the conversation.
Every message is stored permanently and can be recalled in full.
"""

import json
import logging
import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone

import asyncpg
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, UserPromptPart, TextPart, SystemPromptPart

logger = logging.getLogger(__name__)

class CompleteMemoryService:
    """Service for complete conversation memory - NO FORGETTING."""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self._pool = None
    
    async def _get_pool(self) -> asyncpg.Pool:
        """Get or create database connection pool."""
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                self.database_url,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
        return self._pool
    
    async def create_session(self, session_id: Optional[str] = None, metadata: Dict[str, Any] = None) -> str:
        """Create a new conversation session."""
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO conversation_sessions (session_id, metadata)
                VALUES ($1, $2)
                ON CONFLICT (session_id) DO NOTHING
            """, session_id, json.dumps(metadata or {}))
        
        logger.info(f"Created conversation session: {session_id}")
        return session_id
    
    async def add_message(
        self, 
        session_id: str, 
        role: str, 
        content: str, 
        metadata: Dict[str, Any] = None,
        token_count: int = 0
    ) -> int:
        """Add a message to the conversation history - NEVER DELETED."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            # Get next sequence number
            result = await conn.fetchval("""
                SELECT COALESCE(MAX(sequence_number), 0) + 1
                FROM conversation_messages 
                WHERE session_id = $1
            """, session_id)
            
            sequence_number = result or 1
            
            # Insert message
            await conn.execute("""
                INSERT INTO conversation_messages 
                (session_id, role, content, metadata, sequence_number, token_count)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, session_id, role, content, json.dumps(metadata or {}), sequence_number, token_count)
            
            logger.info(f"Added message {sequence_number} to session {session_id}")
            return sequence_number
    
    async def get_complete_conversation(self, session_id: str) -> List[Dict[str, Any]]:
        """Get the COMPLETE conversation history - NO TRUNCATION."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT role, content, timestamp, sequence_number, metadata
                FROM conversation_messages
                WHERE session_id = $1
                ORDER BY sequence_number ASC
            """, session_id)
            
            messages = []
            for row in rows:
                messages.append({
                    'role': row['role'],
                    'content': row['content'],
                    'timestamp': row['timestamp'],
                    'sequence_number': row['sequence_number'],
                    'metadata': row['metadata']
                })
            
            logger.info(f"Retrieved {len(messages)} messages from session {session_id}")
            return messages
    
    async def get_conversation_as_pydantic_messages(self, session_id: str) -> List[ModelMessage]:
        """Get complete conversation as Pydantic AI ModelMessage objects."""
        messages_data = await self.get_complete_conversation(session_id)
        pydantic_messages = []
        
        for msg_data in messages_data:
            if msg_data['role'] == 'user':
                pydantic_messages.append(
                    ModelRequest(parts=[UserPromptPart(content=msg_data['content'])])
                )
            elif msg_data['role'] == 'assistant':
                pydantic_messages.append(
                    ModelResponse(parts=[TextPart(content=msg_data['content'])])
                )
            elif msg_data['role'] == 'system':
                pydantic_messages.append(
                    ModelRequest(parts=[SystemPromptPart(content=msg_data['content'])])
                )
        
        return pydantic_messages
    
    async def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """Get session metadata and statistics."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT session_id, created_at, updated_at, metadata, message_count, total_tokens
                FROM conversation_sessions
                WHERE session_id = $1
            """, session_id)
            
            if row:
                return {
                    'session_id': row['session_id'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at'],
                    'metadata': row['metadata'],
                    'message_count': row['message_count'],
                    'total_tokens': row['total_tokens']
                }
            return None
    
    async def list_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List all conversation sessions."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT session_id, created_at, updated_at, message_count, total_tokens
                FROM conversation_sessions
                ORDER BY updated_at DESC
                LIMIT $1
            """, limit)
            
            sessions = []
            for row in rows:
                sessions.append({
                    'session_id': row['session_id'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at'],
                    'message_count': row['message_count'],
                    'total_tokens': row['total_tokens']
                })
            
            return sessions
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session and ALL its messages - USE WITH CAUTION."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            result = await conn.execute("""
                DELETE FROM conversation_sessions WHERE session_id = $1
            """, session_id)
            
            deleted = result.split()[-1] != '0'
            if deleted:
                logger.warning(f"DELETED session {session_id} and all its messages")
            return deleted
    
    async def search_conversations(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search through conversation content."""
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT DISTINCT 
                    cs.session_id,
                    cs.created_at,
                    cs.message_count,
                    cm.content as matching_content,
                    cm.sequence_number
                FROM conversation_sessions cs
                JOIN conversation_messages cm ON cs.session_id = cm.session_id
                WHERE cm.content ILIKE $1
                ORDER BY cs.updated_at DESC
                LIMIT $2
            """, f'%{query}%', limit)
            
            results = []
            for row in rows:
                results.append({
                    'session_id': row['session_id'],
                    'created_at': row['created_at'],
                    'message_count': row['message_count'],
                    'matching_content': row['matching_content'],
                    'sequence_number': row['sequence_number']
                })
            
            return results
    
    async def close(self):
        """Close database connections."""
        if self._pool:
            await self._pool.close()
            self._pool = None
