# RivalSearchMCP Usage Guide

## 🚀 Getting Started

Once your server is running and connected to your AI assistant, you can start using the powerful web research and data management tools. This guide shows you practical examples and common workflows.

## 🌐 Web Research Tools

### `rival_retrieve` - Your Swiss Army Knife

The main tool for accessing web content with advanced capabilities.

**Basic Usage:**
```python
# Get any webpage
rival_retrieve(resource="https://example.com")

# Search Google
rival_retrieve(resource="search:artificial intelligence trends 2024", limit=10)

# Get with link traversal for comprehensive content
rival_retrieve(
    resource="https://research-site.com", 
    traverse_links=True, 
    max_depth=2, 
    max_pages=8
)
```

**Key Parameters:**
- `resource`: URL or `search:query` for Google search
- `traverse_links`: Enable intelligent link following (default: False)
- `max_depth`: How many link levels to follow (1-3 recommended)
- `max_pages`: Total pages to fetch (5-20 depending on needs)
- `same_domain_only`: Stay within original domain (default: True)
- `store_data`: Save findings to knowledge graph (default: False)

### `research_website` - Deep Topic Exploration

Optimized for comprehensive research across related content.

```python
# Research a topic thoroughly
research_website(
    url="https://blog.openai.com/some-article",
    max_pages=12,
    store_data=True
)

# Academic research
research_website(
    url="https://arxiv.org/abs/2401.12345",
    max_pages=6,
    store_data=True
)
```

**Best For:**
- Academic research
- Market analysis
- Competitive intelligence
- Content discovery

### `explore_docs` - Technical Documentation

Specialized for navigating documentation sites efficiently.

```python
# Explore API documentation
explore_docs(
    url="https://docs.fastapi.tiangolo.com",
    max_pages=25,
    store_data=True
)

# Learn a new framework
explore_docs(
    url="https://docs.react.dev",
    max_pages=15
)
```

**Best For:**
- Learning new technologies
- API reference exploration
- Technical documentation
- Tutorial discovery

### `map_website` - Site Structure Analysis

Understand website architecture and discover key pages.

```python
# Analyze competitor site
map_website(
    url="https://competitor.com",
    max_pages=30,
    store_data=True
)

# Audit your own site
map_website(
    url="https://mysite.com",
    max_pages=50
)
```

**Best For:**
- Competitive analysis
- Site audits
- Content strategy
- SEO research

### `stream_retrieve` - Real-time Data

Access WebSocket streams and live data feeds.

```python
# Connect to data stream
stream_retrieve(url="wss://api.example.com/stream")

# Monitor live feeds
stream_retrieve(url="wss://news-feed.com/live")
```

### `extract_images` - Visual Content

Extract and analyze images from web pages.

```python
# Extract images with OCR
extract_images(
    url="https://document-site.com/report",
    include_ocr=True,
    max_images=10
)
```

## 🧠 AI Processing Tools

### `adaptive_reason` - Smart Problem Solving

Multi-step reasoning with branching and revision capabilities.

```python
# Start reasoning process
adaptive_reason(
    step_content="Let's analyze the AI market trends I've researched",
    step_num=1,
    estimated_steps=5,
    continue_reasoning=True
)

# Continue reasoning
adaptive_reason(
    step_content="Based on the data, I see three key trends...",
    step_num=2,
    estimated_steps=5,
    continue_reasoning=True
)

# Branch reasoning path
adaptive_reason(
    step_content="Alternative analysis considering market volatility",
    step_num=2,
    estimated_steps=4,
    continue_reasoning=True,
    is_revision=True,
    revises_step=2,
    branch_id="market_volatility"
)
```

**Parameters:**
- `step_content`: Your reasoning content for this step
- `step_num`: Current step number
- `estimated_steps`: Total steps you expect
- `continue_reasoning`: Whether to continue the chain
- `is_revision`: True if revising a previous step
- `branch_from_step`: Step number to branch from
- `branch_id`: Unique identifier for this reasoning branch

## 💾 Data Management Tools

### `add_nodes` - Store Your Discoveries

Build your personal knowledge graph.

```python
# Store research findings
add_nodes([
    {
        "name": "AI Trends 2024",
        "type": "research_topic",
        "facts": [
            "GPT-4 adoption increased 400% in enterprise",
            "Multi-modal AI is the fastest growing segment",
            "Retrieval-augmented generation is becoming standard"
        ]
    },
    {
        "name": "OpenAI Research",
        "type": "organization",
        "facts": [
            "Released GPT-4 in March 2023",
            "Focus on safety and alignment",
            "Leading in language model research"
        ]
    }
])
```

### `search_nodes` - Find Stored Information

Query your knowledge graph efficiently.

```python
# Find relevant stored information
search_nodes(query="GPT-4 enterprise adoption")

# Search for specific topics
search_nodes(query="AI safety research")

# Find organizations
search_nodes(query="OpenAI")
```

### `get_full_store` - View Complete Knowledge Graph

Export and analyze your entire knowledge base.

```python
# Get everything you've stored
get_full_store()
```

### Additional Data Tools

- `add_links`: Connect related nodes with relationships
- `remove_nodes`: Clean up outdated information
- `add_facts`: Add new facts to existing nodes
- `get_node_connections`: See how concepts are related

## 🔍 Common Workflows

### 1. Comprehensive Topic Research

Perfect for academic research, market analysis, or learning new subjects.

```python
# Step 1: Initial search to find sources
rival_retrieve(resource="search:quantum computing applications 2024", limit=15)

# Step 2: Deep dive into promising sources
research_website(
    url="https://promising-research-site.com",
    max_pages=10,
    store_data=True
)

# Step 3: Explore technical documentation
explore_docs(
    url="https://qiskit.org/documentation",
    max_pages=20,
    store_data=True
)

# Step 4: Search stored information
search_nodes(query="quantum applications")

# Step 5: Analyze findings with AI reasoning
adaptive_reason(
    step_content="Analyzing quantum computing applications based on research",
    step_num=1,
    estimated_steps=4,
    continue_reasoning=True
)
```

### 2. Competitive Analysis

Understand your competition and market landscape.

```python
# Step 1: Map competitor website
map_website(
    url="https://competitor.com",
    max_pages=25,
    store_data=True
)

# Step 2: Research their product pages
research_website(
    url="https://competitor.com/products",
    max_pages=8,
    store_data=True
)

# Step 3: Analyze pricing and features
rival_retrieve(
    resource="https://competitor.com/pricing",
    traverse_links=True,
    max_pages=5,
    store_data=True
)

# Step 4: Search collected data
search_nodes(query="competitor pricing features")

# Step 5: Strategic analysis
adaptive_reason(
    step_content="Strategic analysis of competitor positioning",
    step_num=1,
    estimated_steps=3,
    continue_reasoning=True
)
```

### 3. Technical Learning

Master new technologies and frameworks.

```python
# Step 1: Start with official documentation
rival_retrieve(resource="https://docs.newframework.com")

# Step 2: Systematically explore docs
explore_docs(
    url="https://docs.newframework.com",
    max_pages=30,
    store_data=True
)

# Step 3: Find tutorials and examples
rival_retrieve(
    resource="search:newframework tutorial examples",
    limit=10
)

# Step 4: Search stored learning materials
search_nodes(query="newframework examples")

# Step 5: Create learning plan
adaptive_reason(
    step_content="Creating learning plan for new framework",
    step_num=1,
    estimated_steps=3,
    continue_reasoning=True
)
```

### 4. Content Discovery with Link Traversal

Find comprehensive information across multiple related pages.

```python
# Start from a seed page and discover related content
rival_retrieve(
    resource="https://research-hub.com/ai-safety",
    traverse_links=True,
    max_depth=2,
    max_pages=12,
    same_domain_only=False,  # Explore external links too
    store_data=True
)

# Search discoveries
search_nodes(query="AI safety research methods")
```

## 🎯 Best Practices

### Link Traversal Guidelines

**Depth Settings:**
- `max_depth=1`: Stay close to original content (safe, focused)
- `max_depth=2`: Good balance of breadth and depth (recommended)
- `max_depth=3`: Very comprehensive but slower (use carefully)

**Page Limits:**
- `max_pages=5-10`: Quick exploration
- `max_pages=10-20`: Thorough research
- `max_pages=20+`: Comprehensive analysis (slower)

**Domain Strategy:**
- `same_domain_only=True`: Focused research within one site
- `same_domain_only=False`: Broader discovery across sites

### Data Storage Strategy

**When to Store Data:**
- Set `store_data=True` when building knowledge base
- Store important research findings
- Keep data from comprehensive analysis sessions

**Node Organization:**
- Use descriptive names for easy searching
- Choose meaningful node types (research_topic, organization, etc.)
- Include relevant facts that capture key insights

### Performance Optimization

**For Faster Results:**
- Use smaller `max_pages` values
- Limit `max_depth` to 1-2
- Use `same_domain_only=True` when appropriate

**For Comprehensive Research:**
- Increase `max_pages` for thorough coverage
- Use `max_depth=2-3` for deep discovery
- Enable cross-domain exploration carefully

## 🔧 Advanced Techniques

### Combining Tools Effectively

```python
# Use multiple tools in sequence for best results
# 1. Broad search
rival_retrieve(resource="search:topic", limit=10)

# 2. Focused exploration
research_website(url="best_source", max_pages=8, store_data=True)

# 3. Technical deep-dive
explore_docs(url="technical_source", max_pages=15, store_data=True)

# 4. Analysis and synthesis
search_nodes(query="key findings")
adaptive_reason(step_content="Synthesizing research", ...)
```

### Smart Query Strategies

**Search Queries:**
```python
# Broad exploration
rival_retrieve(resource="search:machine learning 2024")

# Specific research
rival_retrieve(resource="search:transformer architecture explained")

# Latest developments
rival_retrieve(resource="search:AI news January 2024")
```

**Node Searches:**
```python
# Find specific topics
search_nodes(query="neural networks")

# Find organizations or people
search_nodes(query="OpenAI research")

# Find methodologies
search_nodes(query="training techniques")
```

## 🚨 Important Notes

### Rate Limiting and Ethics
- The server includes automatic delays and proxy rotation
- Respect website terms of service
- Use reasonable page limits to avoid overloading sites
- Consider using cache when available

### Data Privacy
- Stored data is local to your machine
- No data is sent to external services except for web requests
- Clear stored data periodically if handling sensitive information

### Performance Considerations
- Link traversal can be resource-intensive
- Start with small limits and scale up as needed
- Monitor your network usage with large operations

---

**Ready to start researching?** Begin with simple `rival_retrieve` calls and gradually explore the more advanced features. The combination of intelligent web access and knowledge management makes RivalSearchMCP a powerful research companion! 🚀