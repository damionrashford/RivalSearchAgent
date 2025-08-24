"""
Command-line interface for the RivalSearch Agent.

Provides a user-friendly CLI for interacting with the agent.
"""

import asyncio
import argparse
import sys

from .core.agent import RivalSearchAgent
from .core.config import AgentConfig
from .models.schemas import SearchRequest, ContentRequest, AnalysisRequest
from .utils.logging import setup_logging, get_logger

logger = None


async def main():
    """Main CLI entry point."""
    global logger
    
    parser = argparse.ArgumentParser(
        description="RivalSearch Agent - Production-ready AI agent for web research",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run a simple query
  rival-search-agent query "What are the latest AI developments?"
  
  # Perform a web search
  rival-search-agent search "quantum computing breakthroughs"
  
  # Retrieve content from a URL
  rival-search-agent retrieve "https://example.com"
  
  # Analyze content
  rival-search-agent analyze "This is some content to analyze"
  
  # Check agent status
  rival-search-agent status
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Query command
    query_parser = subparsers.add_parser('query', help='Run a natural language query')
    query_parser.add_argument('query', help='The query to run')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Perform a web search')
    search_parser.add_argument('query', help='Search query')
    search_parser.add_argument('--num-results', type=int, default=10, help='Number of results')
    search_parser.add_argument('--lang', default='en', help='Language')
    search_parser.add_argument('--region', help='Geographic region')
    
    # Retrieve command
    retrieve_parser = subparsers.add_parser('retrieve', help='Retrieve content from URL')
    retrieve_parser.add_argument('url', help='URL to retrieve content from')
    retrieve_parser.add_argument('--max-length', type=int, default=2000, help='Maximum content length')
    retrieve_parser.add_argument('--extract-images', action='store_true', help='Extract images with OCR')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze content')
    analyze_parser.add_argument('content', help='Content to analyze')
    analyze_parser.add_argument('--type', choices=['general', 'sentiment', 'technical', 'business'], 
                               default='general', help='Analysis type')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Check agent status')
    
    # Global options
    parser.add_argument('--config', help='Path to configuration file')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       default='INFO', help='Logging level')
    parser.add_argument('--log-file', help='Log file path')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Setup logging
    setup_logging(
        level=args.log_level,
        log_file=args.log_file
    )
    logger = get_logger(__name__)
    
    try:
        # Load configuration
        config = AgentConfig()
        if args.config:
            # Configuration file loading will be implemented in future version
            print(f"Warning: Config file loading not yet implemented. Using default configuration.")
        
        # Create agent
        agent = RivalSearchAgent(config)
        
        # Execute command
        if args.command == 'query':
            await run_query(agent, args.query)
        elif args.command == 'search':
            await run_search(agent, args)
        elif args.command == 'retrieve':
            await run_retrieve(agent, args)
        elif args.command == 'analyze':
            await run_analyze(agent, args)
        elif args.command == 'status':
            await run_status(agent)
        else:
            print(f"Unknown command: {args.command}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        if logger:
            logger.error(f"CLI error: {e}")
        sys.exit(1)


async def run_query(agent: RivalSearchAgent, query: str):
    """Run a natural language query."""
    print(f"Running query: {query}")
    print("-" * 50)
    
    async with agent:
        response = await agent.run_query(query)
        print(response)


async def run_search(agent: RivalSearchAgent, args):
    """Run a web search."""
    print(f"Searching for: {args.query}")
    print("-" * 50)
    
    request = SearchRequest(
        query=args.query,
        num_results=args.num_results,
        lang=args.lang,
        region=args.region
    )
    
    async with agent:
        response = await agent.search(request)
        
        if response.success:
            print(f"Found {response.total_results} results:")
            for i, result in enumerate(response.results, 1):
                print(f"\n{i}. {result.title}")
                print(f"   URL: {result.url}")
                print(f"   Description: {result.description}")
        else:
            print(f"Search failed: {response.error}")


async def run_retrieve(agent: RivalSearchAgent, args):
    """Retrieve content from URL."""
    print(f"Retrieving content from: {args.url}")
    print("-" * 50)
    
    request = ContentRequest(
        resource=args.url,
        max_length=args.max_length,
        extract_images=args.extract_images
    )
    
    async with agent:
        response = await agent.retrieve_content(request)
        
        if response.success:
            print(f"Content retrieved successfully")
            print(f"URL: {response.url}")
            print(f"Method: {response.method}")
            print(f"Content length: {len(response.content)} characters")
            print("\nContent:")
            print(response.content)
        else:
            print(f"Retrieval failed: {response.error}")


async def run_analyze(agent: RivalSearchAgent, args):
    """Analyze content."""
    print(f"Analyzing content with type: {args.type}")
    print("-" * 50)
    
    request = AnalysisRequest(
        content=args.content,
        analysis_type=args.type,
        extract_key_points=True,
        summarize=True
    )
    
    async with agent:
        response = await agent.analyze_content(request)
        
        if response.success:
            print(f"Analysis completed successfully")
            print(f"Content length: {response.content_length} characters")
            print(f"Word count: {response.word_count}")
            print(f"Analysis type: {response.analysis_type}")
            
            if response.key_points:
                print("\nKey Points:")
                for i, point in enumerate(response.key_points, 1):
                    print(f"{i}. {point}")
            
            if response.summary:
                print(f"\nSummary:")
                print(response.summary)
        else:
            print(f"Analysis failed: {response.error}")


async def run_status(agent: RivalSearchAgent):
    """Check agent status."""
    print("Agent Status")
    print("-" * 50)
    
    async with agent:
        status = await agent.get_status()
        
        print(f"Connected: {status.connected}")
        print(f"Model: {status.model_name}")
        print(f"Uptime: {status.uptime:.2f} seconds")
        
        if status.last_activity:
            print(f"Last activity: {status.last_activity}")
        
        if status.available_tools:
            print(f"\nAvailable tools ({len(status.available_tools)}):")
            for tool in status.available_tools:
                print(f"  - {tool}")


if __name__ == "__main__":
    asyncio.run(main())
