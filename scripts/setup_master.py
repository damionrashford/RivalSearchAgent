#!/usr/bin/env python3
"""
Master Setup Script for RivalSearch Agent

This script handles the complete setup process:
1. Project initialization
2. Database setup with pgvector
3. Conversation memory schema
4. Environment configuration
"""

import os
import sys
import subprocess
import shutil
import tempfile
import psycopg2
from pathlib import Path
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def run_command(cmd, cwd=None, check=True, description=""):
    """Run a shell command and handle errors."""
    if description:
        print(f"🔄 {description}...")
    
    if isinstance(cmd, str):
        print(f"Running: {cmd}")
    else:
        print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd, 
            shell=isinstance(cmd, str),
            cwd=cwd,
            check=check,
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(result.stdout)
        if description:
            print(f"✅ {description} completed successfully")
        return result
    except subprocess.CalledProcessError as e:
        if result.stderr:
            print(f"Error output: {e.stderr}")
        if description:
            print(f"❌ {description} failed: {e}")
        raise

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 10):
        print("❌ Python 3.10 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version {sys.version.split()[0]} is compatible")
    return True

def create_virtual_environment():
    """Create a virtual environment."""
    if os.path.exists("venv"):
        print("✅ Virtual environment already exists")
        return True
    
    return run_command("python -m venv venv", description="Creating virtual environment")

def install_dependencies():
    """Install project dependencies."""
    # Determine the correct pip command
    if os.name == 'nt':  # Windows
        pip_cmd = "venv\\Scripts\\pip"
    else:  # Unix/Linux/macOS
        pip_cmd = "venv/bin/pip"
    
    # Upgrade pip first
    if not run_command(f"{pip_cmd} install --upgrade pip", description="Upgrading pip"):
        return False
    
    # Install dependencies
    if not run_command(f"{pip_cmd} install -r requirements.txt", description="Installing project dependencies"):
        return False
    
    return True

def setup_environment_file():
    """Set up the environment configuration file."""
    env_file = Path(".env")
    env_example = Path("env.example")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    if not env_example.exists():
        print("❌ env.example file not found")
        return False
    
    # Copy env.example to .env
    try:
        with open(env_example, 'r') as src, open(env_file, 'w') as dst:
            dst.write(src.read())
        print("✅ Created .env file from env.example")
        print("⚠️  Please edit .env file with your API keys and database URL")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def check_postgres_installation():
    """Check if PostgreSQL is installed and get pg_config path."""
    try:
        # Try to find pg_config
        result = run_command("which pg_config", check=False)
        if result.returncode == 0:
            pg_config_path = result.stdout.strip()
            print(f"Found pg_config at: {pg_config_path}")
            return pg_config_path
        
        # Try common locations
        common_paths = [
            "/usr/bin/pg_config",
            "/usr/local/bin/pg_config",
            "/opt/homebrew/bin/pg_config",
            "/Library/PostgreSQL/*/bin/pg_config"
        ]
        
        for path in common_paths:
            if "*" in path:
                # Handle wildcard paths
                import glob
                matches = glob.glob(path)
                if matches:
                    pg_config_path = matches[0]
                    print(f"Found pg_config at: {pg_config_path}")
                    return pg_config_path
            elif os.path.exists(path):
                print(f"Found pg_config at: {path}")
                return path
                
        raise FileNotFoundError("pg_config not found. Please install PostgreSQL development files.")
        
    except Exception as e:
        print(f"Error checking PostgreSQL installation: {e}")
        return None

def install_pgvector():
    """Clone, compile, and install pgvector."""
    pg_config_path = check_postgres_installation()
    if not pg_config_path:
        print("PostgreSQL not found. Please install PostgreSQL first.")
        return False
    
    # Set PG_CONFIG environment variable
    os.environ['PG_CONFIG'] = pg_config_path
    
    # Create temporary directory for building
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Building pgvector in: {temp_dir}")
        
        # Clone pgvector
        print("Cloning pgvector repository...")
        run_command([
            "git", "clone", "--branch", "v0.8.0", 
            "https://github.com/pgvector/pgvector.git", "pgvector"
        ], cwd=temp_dir, description="Cloning pgvector")
        
        pgvector_dir = os.path.join(temp_dir, "pgvector")
        
        # Compile pgvector
        run_command("make", cwd=pgvector_dir, description="Compiling pgvector")
        
        # Install pgvector
        run_command("sudo make install", cwd=pgvector_dir, description="Installing pgvector")
        
        print("✅ pgvector installed successfully")
        return True

def setup_database_schema():
    """Set up the complete database schema including pgvector and conversation memory."""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not set in environment")
        print("Please set DATABASE_URL in your .env file")
        return False
    
    try:
        # Connect to database
        conn = psycopg2.connect(database_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("🔄 Setting up database schema...")
        
        # Enable pgvector extension
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        print("✅ pgvector extension enabled")
        
        # Create conversation memory schema
        conversation_schema = """
        -- Enable UUID extension for better session IDs
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

        -- Conversation sessions table
        CREATE TABLE IF NOT EXISTS conversation_sessions (
            session_id VARCHAR(255) PRIMARY KEY,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            metadata JSONB DEFAULT '{}',
            message_count INTEGER DEFAULT 0,
            total_tokens INTEGER DEFAULT 0
        );

        -- Complete message history - NEVER DELETE ANYTHING
        CREATE TABLE IF NOT EXISTS conversation_messages (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR(255) NOT NULL REFERENCES conversation_sessions(session_id) ON DELETE CASCADE,
            role VARCHAR(50) NOT NULL CHECK (role IN ('user', 'assistant', 'system', 'tool')),
            content TEXT NOT NULL,
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            metadata JSONB DEFAULT '{}',
            sequence_number INTEGER NOT NULL,
            token_count INTEGER DEFAULT 0,
            
            -- Ensure no messages are ever lost
            UNIQUE(session_id, sequence_number)
        );

        -- Indexes for optimal performance
        CREATE INDEX IF NOT EXISTS idx_conversation_messages_session_id ON conversation_messages(session_id);
        CREATE INDEX IF NOT EXISTS idx_conversation_messages_sequence ON conversation_messages(session_id, sequence_number);
        CREATE INDEX IF NOT EXISTS idx_conversation_messages_timestamp ON conversation_messages(timestamp);

        -- RAG Document Chunks table
        CREATE TABLE IF NOT EXISTS document_chunks (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR(255) NOT NULL,
            file_name VARCHAR(255) NOT NULL,
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL,
            embedding VECTOR(384) NOT NULL,
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            
            UNIQUE(session_id, file_name, chunk_index)
        );

        -- Indexes for document chunks
        CREATE INDEX IF NOT EXISTS idx_document_chunks_session_id ON document_chunks(session_id);
        CREATE INDEX IF NOT EXISTS idx_document_chunks_file_name ON document_chunks(file_name);
        CREATE INDEX IF NOT EXISTS idx_document_chunks_created_at ON document_chunks(created_at);

        -- HNSW index for vector similarity search
        CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding ON document_chunks 
        USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
        """
        
        # Execute schema creation
        cursor.execute(conversation_schema)
        print("✅ Database schema created successfully")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def create_logs_directory():
    """Create logs directory."""
    logs_dir = Path("logs")
    if not logs_dir.exists():
        logs_dir.mkdir()
        print("✅ Created logs directory")
    else:
        print("✅ Logs directory already exists")
    return True

def main():
    """Main setup function."""
    print("🚀 RivalSearch Agent - Master Setup")
    print("=" * 50)
    
    # Step 1: Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Step 2: Create virtual environment
    if not create_virtual_environment():
        sys.exit(1)
    
    # Step 3: Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Step 4: Setup environment file
    if not setup_environment_file():
        sys.exit(1)
    
    # Step 5: Create logs directory
    if not create_logs_directory():
        sys.exit(1)
    
    # Step 6: Install pgvector (optional - only if DATABASE_URL is set)
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        print("\n📊 Database setup detected...")
        
        # Install pgvector
        if not install_pgvector():
            print("⚠️  pgvector installation failed. RAG functionality may not work.")
        
        # Setup database schema
        if not setup_database_schema():
            print("⚠️  Database schema setup failed. Some features may not work.")
    else:
        print("\n⚠️  DATABASE_URL not set. Skipping database setup.")
        print("   Set DATABASE_URL in .env file to enable RAG and conversation memory.")
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Edit .env file with your API keys")
    print("2. Set DATABASE_URL for RAG and memory features")
    print("3. Run: python cli.py chat")
    print("4. Or run: python api.py")

if __name__ == "__main__":
    main()
