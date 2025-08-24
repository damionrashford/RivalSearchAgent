#!/usr/bin/env python3
"""
Example usage of the RivalSearch Agent.

This script demonstrates how to use the agent for various tasks.
"""

import asyncio
import os
from dotenv import load_dotenv

from src.core.agent import RivalSearchAgent

# Load environment variables
load_dotenv()


async def main():
    """Main example function."""
    print("🚀 RivalSearch Agent Example")
    print("=" * 50)
    
    # Check if API key is set
    if not os.getenv('GROK_API_KEY'):
        print("❌ GROK_API_KEY environment variable is required")
        print("Please set it in your .env file or environment")
        return
    
    # Create agent instance
    print("📡 Initializing RivalSearch Agent...")
    agent = RivalSearchAgent()
    
    try:
        # Initialize the agent
        await agent.initialize()
        print("✅ Agent initialized successfully!")
        
        # Example 1: Simple question
        print("\n🔍 Example 1: Simple Question")
        print("-" * 30)
        query = "What are the latest developments in artificial intelligence?"
        print(f"Query: {query}")
        
        response = await agent.run(query, session_id="example-session")
        print(f"Response: {response[:200]}...")
        
        # Example 2: Follow-up question (testing memory)
        print("\n🔍 Example 2: Follow-up Question (Testing Memory)")
        print("-" * 30)
        follow_up = "Can you elaborate on the machine learning aspects you mentioned?"
        print(f"Follow-up: {follow_up}")
        
        response2 = await agent.run(follow_up, session_id="example-session")
        print(f"Response: {response2[:200]}...")
        
        # Example 3: Different session (testing isolation)
        print("\n🔍 Example 3: Different Session (Testing Isolation)")
        print("-" * 30)
        new_query = "What is quantum computing?"
        print(f"New session query: {new_query}")
        
        response3 = await agent.run(new_query, session_id="different-session")
        print(f"Response: {response3[:200]}...")
        
        print("\n✅ All examples completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
