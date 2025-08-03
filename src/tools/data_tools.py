"""
Data storage and management tools for FastMCP server.
"""

import json
from typing import List, Dict, Union
from mcp.server.fastmcp import FastMCP

from src.data_store.manager import store_manager
from src.core.extract import extract_triples
from src.types.schemas import DataStoreResult


def register_data_tools(mcp: FastMCP):
    """Register all data storage and management tools."""
    
    @mcp.tool()
    def add_nodes(nodes: List[Dict[str, Union[str, List[str]]]]) -> DataStoreResult:
        """Add nodes to the knowledge graph with facts and relationships."""
        try:
            # Convert to expected format and add nodes
            formatted_nodes = []
            for node in nodes:
                formatted_node = {
                    "name": node.get("name", ""),
                    "type": node.get("type", "unknown"),
                    "facts": node.get("facts", [])
                }
                formatted_nodes.append(formatted_node)
            
            store_manager.add_nodes(formatted_nodes)
            
            return DataStoreResult(
                success=True,
                operation="add_nodes",
                affected_count=len(formatted_nodes),
                data={"added_nodes": [n["name"] for n in formatted_nodes]}
            )
        except Exception as e:
            return DataStoreResult(
                success=False,
                operation="add_nodes",
                affected_count=0,
                error_message=str(e)
            )

    @mcp.tool()
    def search_nodes(query: str, limit: int = 10) -> DataStoreResult:
        """Search nodes in the knowledge graph by content."""
        try:
            results = store_manager.search_nodes(query, limit)
            
            return DataStoreResult(
                success=True,
                operation="search_nodes",
                affected_count=len(results),
                data={"results": results, "query": query}
            )
        except Exception as e:
            return DataStoreResult(
                success=False,
                operation="search_nodes",
                affected_count=0,
                error_message=str(e)
            )

    @mcp.tool()
    def get_full_store() -> DataStoreResult:
        """Get the complete knowledge graph with all nodes and links."""
        try:
            data = store_manager.get_full_store()
            
            return DataStoreResult(
                success=True,
                operation="get_full_store",
                affected_count=len(data.get("nodes", [])),
                data=data
            )
        except Exception as e:
            return DataStoreResult(
                success=False,
                operation="get_full_store",
                affected_count=0,
                error_message=str(e)
            )

    @mcp.tool()
    def remove_nodes(node_names: List[str]) -> DataStoreResult:
        """Remove nodes from the knowledge graph."""
        try:
            count = store_manager.remove_nodes(node_names)
            
            return DataStoreResult(
                success=True,
                operation="remove_nodes",
                affected_count=count,
                data={"removed_nodes": node_names}
            )
        except Exception as e:
            return DataStoreResult(
                success=False,
                operation="remove_nodes",
                affected_count=0,
                error_message=str(e)
            )

    @mcp.tool()
    def add_links(links: List[Dict[str, str]]) -> DataStoreResult:
        """Add relationships between nodes in the knowledge graph."""
        try:
            # Convert to expected format
            formatted_links = []
            for link in links:
                formatted_link = {
                    "source": link.get("source", ""),
                    "target": link.get("target", ""),
                    "relationship": link.get("relationship", "related_to")
                }
                formatted_links.append(formatted_link)
            
            store_manager.add_links(formatted_links)
            
            return DataStoreResult(
                success=True,
                operation="add_links",
                affected_count=len(formatted_links),
                data={"added_links": formatted_links}
            )
        except Exception as e:
            return DataStoreResult(
                success=False,
                operation="add_links",
                affected_count=0,
                error_message=str(e)
            )

    @mcp.tool()
    def remove_links(links: List[Dict[str, str]]) -> DataStoreResult:
        """Remove relationships between nodes in the knowledge graph."""
        try:
            formatted_links = []
            for link in links:
                formatted_link = {
                    "source": link.get("source", ""),
                    "target": link.get("target", ""),
                    "relationship": link.get("relationship", "related_to")
                }
                formatted_links.append(formatted_link)
            
            count = store_manager.remove_links(formatted_links)
            
            return DataStoreResult(
                success=True,
                operation="remove_links",
                affected_count=count,
                data={"removed_links": formatted_links}
            )
        except Exception as e:
            return DataStoreResult(
                success=False,
                operation="remove_links",
                affected_count=0,
                error_message=str(e)
            )

    @mcp.tool()
    def add_facts(node_name: str, facts: List[str]) -> DataStoreResult:
        """Add facts to an existing node in the knowledge graph."""
        try:
            store_manager.add_facts(node_name, facts)
            
            return DataStoreResult(
                success=True,
                operation="add_facts",
                affected_count=len(facts),
                data={"node": node_name, "added_facts": facts}
            )
        except Exception as e:
            return DataStoreResult(
                success=False,
                operation="add_facts",
                affected_count=0,
                error_message=str(e)
            )

    @mcp.tool()
    def extract_and_store(content: str, node_name: str, node_type: str = "content") -> DataStoreResult:
        """Extract structured information from content and store as a node."""
        try:
            # Extract triples from content
            triples = extract_triples(content)
            
            # Create node with extracted facts
            node = {
                "name": node_name,
                "type": node_type,
                "facts": [f"{s} {p} {o}" for s, p, o in triples]
            }
            
            store_manager.add_nodes([node])
            
            return DataStoreResult(
                success=True,
                operation="extract_and_store",
                affected_count=len(triples),
                data={
                    "node": node_name,
                    "extracted_facts": len(triples),
                    "sample_facts": node["facts"][:5]  # Show first 5 facts
                }
            )
        except Exception as e:
            return DataStoreResult(
                success=False,
                operation="extract_and_store",
                affected_count=0,
                error_message=str(e)
            )

    @mcp.tool()
    def get_node_connections(node_name: str) -> DataStoreResult:
        """Get all connections and relationships for a specific node."""
        try:
            connections = store_manager.get_node_connections(node_name)
            
            return DataStoreResult(
                success=True,
                operation="get_node_connections",
                affected_count=len(connections),
                data={"node": node_name, "connections": connections}
            )
        except Exception as e:
            return DataStoreResult(
                success=False,
                operation="get_node_connections",
                affected_count=0,
                error_message=str(e)
            )

    @mcp.tool()
    def clear_store() -> DataStoreResult:
        """Clear all data from the knowledge graph."""
        try:
            count = store_manager.clear_store()
            
            return DataStoreResult(
                success=True,
                operation="clear_store",
                affected_count=count,
                data={"message": f"Cleared {count} items from store"}
            )
        except Exception as e:
            return DataStoreResult(
                success=False,
                operation="clear_store",
                affected_count=0,
                error_message=str(e)
            )