# RivalSearch Agent

A powerful, embeddable AI agent with RAG (Retrieval-Augmented Generation) capabilities that can be used as a CLI tool, API server, or embedded in other systems.

## 🚀 Features

- **🤖 Multi-Provider LLM Support**: OpenAI, Anthropic, Google, Grok, DeepSeek, Ollama
- **🔍 RAG with BGE Embeddings**: 100% free, local document processing
- **🗄️ pgvector Database**: Fast vector similarity search
- **🧠 Complete Conversation Memory**: Session-isolated memory with full recall
- **🖥️ CLI Interface**: Interactive chat and document management
- **🌐 API Server**: HTTP endpoints for integration
- **📦 Library Mode**: Direct Python imports for embedding
- **🔌 Framework Integration**: LangChain, AutoGen, and more

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CLI Mode      │    │   API Mode      │    │   Library Mode   │
│   (Direct Chat) │    │   (HTTP Calls)  │    │   (Import/Embed)│
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │   RivalSearch Agent       │
                    │   (Core Engine)           │
                    │   ┌─────────────────────┐ │
                    │   │   RAG System        │ │
                    │   │   + pgvector        │ │
                    │   │   + BGE Embeddings  │ │
                    │   └─────────────────────┘ │
                    │   ┌─────────────────────┐ │
                    │   │   Memory System     │ │
                    │   │   + Session Storage │ │
                    │   │   + Full Recall     │ │
                    │   └─────────────────────┘ │
                    └───────────────────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │   RivalSearchMCP │
                    │   (Web Research Tools)   │
                    └───────────────────────────┘
```

## 🔍 MCP Server Tools

The RivalSearch Agent integrates with **RivalSearchMCP** for powerful web research capabilities:

### Search Tools
- **`google_search`** - Comprehensive Google Search with multi-engine fallback, rich snippets detection, and advanced filtering options

### Retrieval Tools  
- **`retrieve_content`** - Enhanced content retrieval from URLs with support for batch operations and image extraction
- **`stream_content`** - Stream content from URLs for real-time processing

### Traversal Tools
- **`traverse_website`** - Comprehensive website traversal with three modes:
  - **Research mode** - General content exploration
  - **Documentation mode** - Focused on docs and guides
  - **Mapping mode** - Website structure analysis

### Analysis Tools
- **`analyze_content`** - Content analysis with sentiment analysis, key point extraction, and summarization
- **`research_topic`** - End-to-end research workflows combining search, retrieval, and analysis

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- PostgreSQL (for RAG functionality)
- API key for your chosen LLM provider

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/damionrashford/RivalSearchAgent
   cd RivalSearchAgent
   ```

2. **Run the master setup script:**
   ```bash
   python scripts/setup_master.py
   ```

3. **Configure your environment:**
   ```bash
   # The setup script will create .env from .env.example
   # Edit .env with your API keys and database URL
   ```

4. **Start using the agent:**
   ```bash
   # CLI mode
   python -m src.cli chat
   
   # API mode
   python -m src.api
   ```

## 📖 Usage

### CLI Mode (Interactive Chat)
```bash
# Start interactive chat
python -m src.cli chat

# Ask a single question
python -m src.cli chat --question "What is AI?"

# Upload a document
python -m src.cli upload document.pdf

# Show conversation history
python -m src.cli chat  # Then type 'history' in chat

# List all sessions
python -m src.cli chat  # Then type 'sessions' in chat
```

### API Server Mode
```bash
# Start API server
python -m src.api

# Server will be available at http://localhost:8000
# API documentation at http://localhost:8000/docs
```

### Library Mode (Python Import)
```python
from src.core.agent import RivalSearchAgent
from src.core.config import AgentConfig

# Initialize agent
config = AgentConfig()
agent = RivalSearchAgent(config)
await agent.initialize()

# Use the agent with session memory
response = await agent.run("Your question here", session_id="my-session")
print(response)
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with your configuration:

```bash
# LLM Provider API Keys (choose one)
GROK_API_KEY=your_grok_api_key
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
GOOGLE_API_KEY=your_google_api_key

# Database Configuration (for RAG and memory)
DATABASE_URL=postgresql://username:password@localhost:5432/rivalsearch_db

# RAG Configuration
RAG_ENABLED=true
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5

# Agent Configuration
RIVAL_SEARCH_MODEL_NAME=grok:groq-llama3-70b-8192
```

### Supported LLM Providers

| Provider | Model Format | API Key Required |
|----------|--------------|------------------|
| Grok | `grok:model-name` | `GROK_API_KEY` |
| OpenAI | `openai:model-name` | `OPENAI_API_KEY` |
| Anthropic | `anthropic:model-name` | `ANTHROPIC_API_KEY` |
| Google | `google:model-name` | `GOOGLE_API_KEY` |
| DeepSeek | `deepseek:model-name` | `DEEPSEEK_API_KEY` |
| Ollama | `ollama:model-name` | None (local) |

## 🧠 Memory System

The agent features complete conversation memory within sessions:

- **Session Isolation**: Each session is completely independent
- **Full Recall**: Agent remembers everything within a session
- **No Forgetting**: Complete conversation history preserved
- **Database Backed**: Persistent storage survives restarts

## 🔍 RAG System

Retrieval-Augmented Generation with local embeddings:

- **BGE Embeddings**: 100% free, local embedding model
- **pgvector**: Fast vector similarity search
- **Document Support**: PDF, DOCX, RTF, TXT files
- **Session Scoped**: Documents isolated per session

## 📄 License

MIT License - see LICENSE file for details.

## 🔗 Related Projects

- **[RivalSearchMCP](https://github.com/damionrashford/RivalSearchMCP)** - Web research MCP server
