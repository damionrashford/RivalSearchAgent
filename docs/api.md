# RivalSearchMCP API Documentation

## 🔧 FastMCP Architecture

RivalSearchMCP uses FastMCP for type-safe, structured outputs with Pydantic models. All responses follow strict schemas for reliable integration.

### Transport Protocols
- **STDIO**: Default transport for Claude Desktop, Cursor, local clients
- **HTTP**: Streamable HTTP for web integrations and remote access  
- **SSE**: Server-Sent Events for real-time applications

### Response Format
All tools return structured Pydantic models (not plain text/JSON strings):
```python
# Example structured response
RetrieveResult(
    success=True,
    data=WebContent(content="...", url="https://example.com"),
    truncated=False,
    remaining_bytes=0,
    original_url="https://example.com",
    is_search=False
)
```

## 🛠️ Tools Reference

### 🌐 Web Retrieval Tools

#### `rival_retrieve`
**Description**: Retrieve any internet resource, bypassing limits/paywalls/anti-bot measures. Supports both direct URLs and Google search.

**Parameters**:
- `resource` (str | List[str]): URL or `"search:query"` for Google search, or list for batch
- `limit` (int, default=10): Max search results to return
- `privacy` (bool, default=False): Use privacy-focused retrieval
- `cache` (bool, default=False): Enable caching (if available)
- `store_data` (bool, default=False): Store retrieved data in graph store
- `max_length` (int, default=5000): Maximum content length
- `start_index` (int, default=0): Starting position for content retrieval
- `raw` (bool, default=False): Return raw content without truncation notice

**Returns**: `RetrieveResult`
```python
class RetrieveResult(BaseModel):
    success: bool
    data: Union[List[SearchResult], WebContent, Dict[str, str]]
    truncated: bool = False
    remaining_bytes: int = 0
    original_url: str
    is_search: bool
    error_message: Optional[str] = None
```

**Usage Examples**:
```python
# Web page retrieval
rival_retrieve(resource="https://example.com", max_length=1000)

# Google search
rival_retrieve(resource="search:FastMCP Python", limit=5)

# Batch retrieval
rival_retrieve(resource=["https://site1.com", "https://site2.com"])

# Paginated content
rival_retrieve(resource="https://long-article.com", start_index=5000, max_length=2000)
```

#### `stream_retrieve`
**Description**: Retrieve streaming data from WebSocket URLs.

**Parameters**:
- `url` (str): WebSocket URL to connect to

**Returns**: `StreamResult`
```python
class StreamResult(BaseModel):
    success: bool
    content: str
    url: str
    chunks_received: int
```

**Usage Example**:
```python
stream_retrieve(url="wss://echo.websocket.org")
```

### 🧠 Reasoning Tools

#### `adaptive_reason`
**Description**: Dynamic step-by-step reasoning with support for revisions, branching, and step extension.

**Parameters**:
- `step_content` (str): Content of the reasoning step
- `step_num` (int): Current step number
- `estimated_steps` (int): Estimated total steps needed
- `continue_reasoning` (bool): Whether to continue reasoning process
- `is_revision` (bool, default=False): Whether this is a revision of existing step
- `revises_step` (Optional[int]): Step number being revised
- `branch_from_step` (Optional[int]): Step to branch from
- `branch_id` (Optional[str]): Identifier for reasoning branch
- `needs_more_steps` (bool, default=False): Request additional steps

**Returns**: `ReasoningResult`
```python
class ReasoningResult(BaseModel):
    current_step: ReasoningStep
    paths: List[Dict[str, Any]]
    steps_count: int

class ReasoningStep(BaseModel):
    step_num: int
    content: str
    estimated_steps: int
    continue_reasoning: bool
    is_revision: bool = False
    revises_step: Optional[int] = None
    branch_from_step: Optional[int] = None
    branch_id: Optional[str] = None
    needs_more_steps: bool = False
```

**Usage Example**:
```python
adaptive_reason(
    step_content="Define the problem: Calculate compound interest",
    step_num=1,
    estimated_steps=4,
    continue_reasoning=True
)
```

### 💾 Data Store Tools

#### `add_nodes`
**Description**: Add new nodes to the graph data store.

**Parameters**:
- `nodes` (List[Dict[str, Any]]): List of node objects with name, type, and facts

**Returns**: `NodeOperationResult`
```python
class NodeOperationResult(BaseModel):
    success: bool
    affected_nodes: List[str]
    operation: str
    details: Optional[Dict[str, Any]] = None
```

**Usage Example**:
```python
add_nodes(nodes=[
    {
        "name": "Python",
        "type": "programming_language", 
        "facts": ["Created by Guido van Rossum", "First released in 1991"]
    }
])
```

#### `add_links`
**Description**: Add relationships between existing nodes.

**Parameters**:
- `links` (List[Dict[str, str]]): List of link objects with from, to, and relation

**Returns**: `LinkOperationResult`
```python
class LinkOperationResult(BaseModel):
    success: bool
    affected_links: List[Dict[str, str]]
    operation: str
```

**Usage Example**:
```python
add_links(links=[
    {"from": "Python", "to": "Guido van Rossum", "relation": "created_by"}
])
```

#### `add_facts`
**Description**: Add facts to existing nodes.

**Parameters**:
- `facts` (List[Dict[str, Any]]): List of fact objects with node_name and facts

**Returns**: `FactOperationResult`
```python
class FactOperationResult(BaseModel):
    success: bool
    affected_facts: Dict[str, List[str]]
    operation: str
```

**Usage Example**:
```python
add_facts(facts=[
    {"node_name": "Python", "facts": ["Supports multiple paradigms"]}
])
```

#### `remove_nodes`
**Description**: Remove nodes and their associated links from the store.

**Parameters**:
- `node_names` (List[str]): List of node names to remove

**Returns**: `NodeOperationResult`

#### `remove_facts`
**Description**: Remove specific facts from nodes.

**Parameters**:
- `removals` (List[Dict[str, Any]]): List of removal objects with node_name and facts

**Returns**: `FactOperationResult`

#### `remove_links`
**Description**: Remove specific relationships between nodes.

**Parameters**:
- `links` (List[Dict[str, str]]): List of link objects to remove

**Returns**: `LinkOperationResult`

#### `get_full_store`
**Description**: Retrieve the complete graph data store.

**Parameters**: None

**Returns**: `GraphData`
```python
class GraphData(BaseModel):
    nodes: List[Node]
    links: List[Link]

class Node(BaseModel):
    name: str
    type: str
    facts: List[str]

class Link(BaseModel):
    from_node: str
    to_node: str
    relation: str
```

#### `search_nodes`
**Description**: Search for nodes by query string.

**Parameters**:
- `query` (str): Search query to match against node names and facts

**Returns**: `SearchNodesResult`
```python
class SearchNodesResult(BaseModel):
    success: bool
    query: str
    nodes: List[Node]
    links: List[Link]
    total_matches: int
```

#### `get_specific_nodes`
**Description**: Retrieve specific nodes by their names.

**Parameters**:
- `names` (List[str]): List of node names to retrieve

**Returns**: `GraphData`

## 🔍 Search Functionality

### Google Search Integration
Use `rival_retrieve` with `resource="search:query"` format:

```python
# Basic search
rival_retrieve(resource="search:Python MCP", limit=10)

# Advanced search with data storage
rival_retrieve(
    resource="search:FastMCP tutorial",
    limit=5,
    store_data=True  # Stores results in graph store
)
```

### Search Result Format
```python
class SearchResult(BaseModel):
    title: str = Field(description="Search result title")
    link: str = Field(description="URL of the search result")
    snippet: str = Field(description="Brief description/snippet")
```

## 🌐 Web Content Types

### Supported Formats
- **HTML**: Parsed and cleaned for AI consumption
- **JSON**: Direct JSON responses
- **Images**: OCR text extraction (if Tesseract available)
- **Streaming**: WebSocket data streams

### Content Processing
```python
class WebContent(BaseModel):
    content: str = Field(description="Processed web content")
    url: str = Field(description="Source URL")
    content_type: str = Field(default="text/html", description="MIME type")
    ocr_text: List[str] = Field(default_factory=list, description="Extracted OCR text")
```

## 🚦 Error Handling

### Error Response Format
All tools include error handling with structured error messages:
```python
# Example error response
RetrieveResult(
    success=False,
    data=WebContent(content="", url="invalid-url"),
    error_message="Connection timeout after 30 seconds",
    original_url="invalid-url",
    is_search=False
)
```

### Common Error Types
- **Connection Errors**: Network timeouts, DNS failures
- **Authentication Errors**: Blocked by anti-bot measures
- **Validation Errors**: Invalid parameters or malformed requests
- **Processing Errors**: Content parsing or OCR failures

## 📊 Performance Characteristics

### Response Times (Typical)
- **Data Store Operations**: < 1 second
- **Web Retrieval**: 2-30 seconds (depends on target site)
- **Search Queries**: 5-15 seconds
- **Reasoning Steps**: < 1 second
- **Streaming**: Real-time (depends on source)

### Resource Limits
- **Max Content Length**: 5000 characters (configurable)
- **Search Results**: 10 results (configurable)
- **Concurrent Requests**: Handled gracefully
- **Memory Usage**: ~500MB baseline

## 🔧 Integration Examples

### Claude Desktop Integration
```json
{
  "mcpServers": {
    "rival-search": {
      "command": "python",
      "args": ["/path/to/rival_search_mcp/src/server.py"],
      "env": {
        "DEBUG": "false",
        "DATA_STORE_PATH": "./data_store.json"
      }
    }
  }
}
```

### HTTP Client Example
```python
import requests

response = requests.post("http://localhost:8000/mcp", json={
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "rival_retrieve",
        "arguments": {
            "resource": "https://example.com",
            "max_length": 1000
        }
    }
}, headers={
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream"
})

result = response.json()
```

### Python SDK Example
```python
import asyncio
from src.server import mcp

async def test_tools():
    # List available tools
    tools = await mcp.list_tools()
    print(f"Available tools: {[tool.name for tool in tools]}")
    
    # Call a tool
    result = await mcp.call_tool("rival_retrieve", {
        "resource": "https://httpbin.org/json"
    })
    print(f"Result: {result}")

asyncio.run(test_tools())
```

## 🔒 Security Considerations

### Input Validation
- All parameters validated against Pydantic schemas
- URL validation for web requests
- Sanitization of search queries
- Protection against injection attacks

### Rate Limiting
- Automatic proxy rotation for web requests
- Built-in delays to respect target sites
- Graceful handling of rate limit responses

### Data Privacy
- Optional privacy mode for sensitive requests
- No automatic logging of request content
- Local data storage only

## 📋 Schema Definitions

All structured outputs use these base schemas defined in `src/types/schemas.py`:

```python
from pydantic import BaseModel, Field
from typing import Union, List, Optional, Dict, Any

# Complete schema definitions available in source code
# See src/types/schemas.py for full type definitions
```

This comprehensive API provides type-safe, reliable access to web content, search functionality, data storage, and reasoning capabilities through the Model Context Protocol.
- Returns: Matching nodes/links JSON

### get_specific_nodes
- Args: names (list[str])
- Returns: Specific nodes/links JSON

## Error Handling
- INVALID_PARAMS: Bad args
- INTERNAL_ERROR: Fetch/store fails

## Extensibility
Tools are modular; add new in src/tools.
