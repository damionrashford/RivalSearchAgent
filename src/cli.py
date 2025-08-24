"""
RivalSearch Agent CLI - Multi-mode interface for the agent.

Supports:
- Interactive chat mode
- Single question mode  
- Document upload mode
- API server mode
"""

import asyncio
import click
import os
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from .core.agent import RivalSearchAgent
from .core.config import AgentConfig
from .core.services.rag_service import RAGDependencies

class RivalSearchCLI:
    """CLI interface for RivalSearch Agent."""
    
    def __init__(self):
        self.config = AgentConfig()
        self.agent = None
        self.session_id = None
        self.memory_service = None
        
        # Initialize memory service if database URL is available
        if self.config.database_url:
            from .core.services.memory_service import CompleteMemoryService
            self.memory_service = CompleteMemoryService(self.config.database_url)
    
    async def initialize_agent(self):
        """Initialize the agent."""
        if not self.agent:
            self.agent = RivalSearchAgent(self.config)
            await self.agent.initialize()
            print("✅ Agent initialized successfully")
    
    async def start_interactive_chat(self):
        """Start interactive chat session."""
        await self.initialize_agent()
        
        # Create or get session
        if self.memory_service:
            if not self.session_id:
                self.session_id = await self.memory_service.create_session()
            print(f"📝 Session ID: {self.session_id}")
        
        print("🤖 RivalSearch Agent - Interactive Chat")
        print("=" * 50)
        print("Commands:")
        print("  upload <file_path>  - Upload a document for RAG")
        print("  list                - List uploaded documents")
        print("  clear               - Clear session documents")
        print("  history             - Show conversation history")
        print("  sessions            - List all sessions")
        print("  quit                - Exit chat")
        print("=" * 50)
        
        while True:
            try:
                user_input = input("\n💬 You: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() == 'quit':
                    print("👋 Goodbye!")
                    break
                
                elif user_input.lower() == 'list':
                    await self.list_documents()
                
                elif user_input.lower() == 'clear':
                    await self.clear_documents()
                
                elif user_input.lower() == 'history':
                    await self.show_history()
                
                elif user_input.lower() == 'sessions':
                    await self.list_sessions()
                
                elif user_input.startswith('upload '):
                    file_path = user_input[7:].strip()
                    await self.upload_document(file_path)
                
                else:
                    # Regular chat message
                    response = await self.agent.run(user_input, session_id=self.session_id)
                    print(f"🤖 Agent: {response}")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    async def ask_single_question(self, question: str):
        """Ask a single question."""
        await self.initialize_agent()
        response = await self.agent.run(question, session_id=self.session_id)
        print(f"🤖 Agent: {response}")
    
    async def upload_document(self, file_path: str):
        """Upload a document for RAG."""
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return
        
        try:
            # Read file content
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            # Get file name
            file_name = os.path.basename(file_path)
            
            # Initialize RAG dependencies if needed
            if not self.session_id:
                self.session_id = "cli-session"
            
            # Process document
            from .core.services.rag_service import RAGService, RAGDependencies
            
            database_url = os.getenv('DATABASE_URL')
            if not database_url:
                print("❌ DATABASE_URL not set in environment")
                return
            
            deps = RAGDependencies(
                database_url=database_url,
                session_id=self.session_id
            )
            
            rag_service = RAGService(deps)
            result = await rag_service.process_uploaded_document(
                file_content=file_content,
                file_name=file_name
            )
            
            if result["success"]:
                print(f"✅ Uploaded {file_name} ({result['chunks_stored']} chunks)")
            else:
                print(f"❌ Failed to upload {file_name}: {result.get('error')}")
                
        except Exception as e:
            print(f"❌ Error uploading document: {e}")
    
    async def list_documents(self):
        """List uploaded documents."""
        if not self.session_id:
            print("ℹ️  No active session")
            return
        
        try:
            from .core.services.rag_service import RAGService, RAGDependencies
            
            database_url = os.getenv('DATABASE_URL')
            if not database_url:
                print("❌ DATABASE_URL not set in environment")
                return
            
            deps = RAGDependencies(
                database_url=database_url,
                session_id=self.session_id
            )
            
            rag_service = RAGService(deps)
            documents = await rag_service.get_session_documents()
            
            if not documents:
                print("📁 No documents uploaded")
                return
            
            print("📁 Uploaded Documents:")
            for i, doc in enumerate(documents, 1):
                print(f"  {i}. {doc['file_name']} ({doc['chunk_count']} chunks)")
                
        except Exception as e:
            print(f"❌ Error listing documents: {e}")
    
    async def clear_documents(self):
        """Clear session documents."""
        if not self.session_id:
            print("ℹ️  No active session")
            return
        
        try:
            from .core.services.rag_service import RAGService, RAGDependencies
            
            database_url = os.getenv('DATABASE_URL')
            if not database_url:
                print("❌ DATABASE_URL not set in environment")
                return
            
            deps = RAGDependencies(
                database_url=database_url,
                session_id=self.session_id
            )
            
            rag_service = RAGService(deps)
            success = await rag_service.delete_documents()
            
            if success:
                print("✅ Cleared all documents")
            else:
                print("❌ Failed to clear documents")
                
        except Exception as e:
            print(f"❌ Error clearing documents: {e}")
    
    async def show_history(self):
        """Show conversation history."""
        if not self.memory_service or not self.session_id:
            print("ℹ️  No conversation history available")
            return
        
        try:
            messages = await self.memory_service.get_complete_conversation(self.session_id)
            
            if not messages:
                print("📝 No conversation history yet")
                return
            
            print(f"\n📝 Conversation History (Session: {self.session_id})")
            print("=" * 60)
            
            for msg in messages:
                role_emoji = {"user": "👤", "assistant": "🤖", "system": "⚙️"}.get(msg['role'], "💬")
                print(f"{role_emoji} {msg['role'].upper()}: {msg['content'][:100]}{'...' if len(msg['content']) > 100 else ''}")
            
            print("=" * 60)
            
        except Exception as e:
            print(f"❌ Error showing history: {e}")
    
    async def list_sessions(self):
        """List all conversation sessions."""
        if not self.memory_service:
            print("ℹ️  Memory service not available")
            return
        
        try:
            sessions = await self.memory_service.list_sessions()
            
            if not sessions:
                print("📝 No conversation sessions found")
                return
            
            print(f"\n📝 Conversation Sessions ({len(sessions)} total)")
            print("=" * 60)
            
            for i, session in enumerate(sessions, 1):
                current_indicator = " (CURRENT)" if session['session_id'] == self.session_id else ""
                print(f"{i}. {session['session_id']}{current_indicator}")
                print(f"   Messages: {session['message_count']} | Tokens: {session['total_tokens']}")
                print(f"   Updated: {session['updated_at']}")
                print()
            
            print("=" * 60)
            
        except Exception as e:
            print(f"❌ Error listing sessions: {e}")

# CLI Commands
@click.group()
def cli():
    """RivalSearch Agent - Multi-mode AI agent with RAG capabilities"""
    pass

@cli.command()
@click.option('--interactive', '-i', is_flag=True, help='Start interactive chat')
@click.option('--question', '-q', help='Ask a single question')
def chat(interactive, question):
    """Chat with the agent"""
    cli_instance = RivalSearchCLI()
    
    if interactive:
        asyncio.run(cli_instance.start_interactive_chat())
    elif question:
        asyncio.run(cli_instance.ask_single_question(question))
    else:
        # Default to interactive mode
        asyncio.run(cli_instance.start_interactive_chat())

@cli.command()
@click.argument('file_path')
def upload(file_path):
    """Upload a document for RAG"""
    cli_instance = RivalSearchCLI()
    asyncio.run(cli_instance.upload_document(file_path))

@cli.command()
def serve():
    """Start API server"""
    from .api import start_server
    start_server()

@cli.command()
def version():
    """Show version information"""
    import sys
    sys.path.insert(0, '.')
    from __init__ import __version__
    print(f"RivalSearch Agent v{__version__}")

if __name__ == '__main__':
    cli()
