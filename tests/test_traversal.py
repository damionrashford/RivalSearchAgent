import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from src.core.traversal import LinkTraverser, TraversalConfig, traverse_website, research_topic

@pytest.fixture
def sample_html():
    return """
    <html>
    <head><title>Test Page</title></head>
    <body>
        <h1>Welcome to Test Site</h1>
        <p>This is a test page with some content.</p>
        <a href="/page1">Page 1</a>
        <a href="/page2">Page 2</a>
        <a href="https://external.com">External Link</a>
        <a href="#anchor">Anchor Link</a>
        <a href="javascript:void(0)">JS Link</a>
    </body>
    </html>
    """

def test_link_traverser_init():
    """Test LinkTraverser initialization."""
    config = TraversalConfig(max_depth=3, max_pages=5)
    traverser = LinkTraverser(config)
    
    assert traverser.config.max_depth == 3
    assert traverser.config.max_pages == 5
    assert len(traverser.visited_urls) == 0
    assert len(traverser.results) == 0

def test_normalize_url():
    """Test URL normalization."""
    traverser = LinkTraverser()
    
    # Test basic normalization
    assert traverser.normalize_url("https://Example.com/Path/") == "https://example.com/Path"
    assert traverser.normalize_url("https://example.com/path#fragment") == "https://example.com/path"
    
    # Test relative URL resolution
    base_url = "https://example.com/dir/"
    assert traverser.normalize_url("page.html", base_url) == "https://example.com/dir/page.html"
    assert traverser.normalize_url("/absolute", base_url) == "https://example.com/absolute"

def test_extract_links(sample_html):
    """Test link extraction from HTML."""
    traverser = LinkTraverser()
    base_url = "https://example.com"
    
    links = traverser.extract_links(sample_html, base_url)
    
    # Should extract valid links and skip invalid ones
    expected_links = [
        "https://example.com/page1",
        "https://example.com/page2", 
        "https://external.com"
    ]
    
    assert all(link in links for link in expected_links)
    # Should not include anchor or javascript links
    assert not any("#" in link or "javascript:" in link for link in links)

def test_should_follow_link():
    """Test link following logic."""
    config = TraversalConfig(same_domain_only=True)
    traverser = LinkTraverser(config)
    base_domain = "example.com"
    
    # Same domain should be followed
    assert traverser.should_follow_link("https://example.com/page", base_domain)
    
    # External domain should not be followed when same_domain_only=True
    assert not traverser.should_follow_link("https://other.com/page", base_domain)
    
    # PDF files should not be followed
    assert not traverser.should_follow_link("https://example.com/file.pdf", base_domain)

def test_should_follow_link_with_patterns():
    """Test link following with include/exclude patterns."""
    config = TraversalConfig(
        same_domain_only=False,
        link_patterns=[r"/docs/", r"/api/"],
        exclude_patterns=[r"/admin/", r"/private/"]
    )
    traverser = LinkTraverser(config)
    base_domain = "example.com"
    
    # Should follow links matching include patterns
    assert traverser.should_follow_link("https://example.com/docs/guide", base_domain)
    assert traverser.should_follow_link("https://example.com/api/v1", base_domain)
    
    # Should not follow links matching exclude patterns
    assert not traverser.should_follow_link("https://example.com/admin/panel", base_domain)
    assert not traverser.should_follow_link("https://example.com/private/data", base_domain)
    
    # Should not follow links not matching include patterns
    assert not traverser.should_follow_link("https://example.com/blog/post", base_domain)

def test_extract_page_title(sample_html):
    """Test page title extraction."""
    traverser = LinkTraverser()
    
    title = traverser.extract_page_title(sample_html)
    assert title == "Test Page"
    
    # Test fallback to h1
    html_no_title = "<html><body><h1>Main Heading</h1></body></html>"
    title = traverser.extract_page_title(html_no_title)
    assert title == "Main Heading"
    
    # Test fallback for no title or h1
    html_empty = "<html><body><p>Content</p></body></html>"
    title = traverser.extract_page_title(html_empty)
    assert title == "Untitled"

@pytest.mark.asyncio
async def test_fetch_page():
    """Test page fetching functionality."""
    traverser = LinkTraverser()
    
    with patch('src.core.traversal.base_fetch_url') as mock_fetch:
        mock_fetch.return_value = "<html><head><title>Test</title></head><body><a href='/link'>Link</a></body></html>"
        
        result = await traverser.fetch_page("https://example.com", 0)
        
        assert result.success
        assert result.url == "https://example.com"
        assert result.title == "Test"
        assert result.depth == 0
        assert len(result.links_found) > 0

@pytest.mark.asyncio
async def test_traverse_website_function():
    """Test high-level traverse_website function."""
    with patch('src.core.traversal.refresh_proxies') as mock_refresh, \
         patch('src.core.traversal.base_fetch_url') as mock_fetch:
        
        mock_refresh.return_value = None
        mock_fetch.return_value = """
        <html>
        <head><title>Home Page</title></head>
        <body>
            <h1>Welcome</h1>
            <p>Content here</p>
            <a href="/about">About Us</a>
        </body>
        </html>
        """
        
        result = await traverse_website(
            start_url="https://example.com",
            max_depth=1,
            max_pages=2
        )
        
        assert result["start_url"] == "https://example.com"
        assert result["pages_fetched"] >= 1
        assert len(result["pages"]) >= 1
        assert result["pages"][0]["title"] == "Home Page"
        assert "config" in result

@pytest.mark.asyncio  
async def test_research_topic_function():
    """Test research_topic convenience function."""
    with patch('src.core.traversal.traverse_website') as mock_traverse:
        mock_traverse.return_value = {
            "start_url": "https://example.com",
            "pages_fetched": 3,
            "pages": [
                {"url": "https://example.com", "title": "Home", "content": "Content", "depth": 0}
            ]
        }
        
        result = await research_topic("https://example.com", max_pages=5)
        
        assert result["start_url"] == "https://example.com"
        assert result["pages_fetched"] == 3
        
        # Check that traverse_website was called with research-specific settings
        mock_traverse.assert_called_once_with(
            start_url="https://example.com",
            max_depth=2,
            max_pages=5,
            same_domain_only=True,
            exclude_patterns=[
                r'/tag/', r'/category/', r'/archive/', r'/search/',
                r'\.pdf$', r'\.doc$', r'/login', r'/register'
            ]
        )

def test_traversal_config_defaults():
    """Test TraversalConfig default values."""
    config = TraversalConfig()
    
    assert config.max_depth == 2
    assert config.max_pages == 10
    assert config.max_content_per_page == 3000
    assert config.follow_external_links == False
    assert config.same_domain_only == True
    assert config.respect_robots_txt == True
    assert config.delay_between_requests == 1.0
    assert config.link_patterns is None
    assert config.exclude_patterns is None

@pytest.mark.asyncio
async def test_traverse_links_depth_limit():
    """Test that traversal respects depth limits."""
    config = TraversalConfig(max_depth=0, max_pages=10)
    traverser = LinkTraverser(config)
    
    with patch('src.core.traversal.refresh_proxies') as mock_refresh, \
         patch('src.core.traversal.base_fetch_url') as mock_fetch:
        
        mock_refresh.return_value = None
        mock_fetch.return_value = """
        <html>
        <head><title>Test</title></head>
        <body><a href="/link1">Link</a></body>
        </html>
        """
        
        results = await traverser.traverse_links("https://example.com")
        
        # Should only fetch the starting page (depth 0)
        assert len(results) == 1
        assert results[0].depth == 0

@pytest.mark.asyncio
async def test_traverse_links_page_limit():
    """Test that traversal respects page limits."""
    config = TraversalConfig(max_depth=2, max_pages=1)
    traverser = LinkTraverser(config)
    
    with patch('src.core.traversal.refresh_proxies') as mock_refresh, \
         patch('src.core.traversal.base_fetch_url') as mock_fetch:
        
        mock_refresh.return_value = None
        mock_fetch.return_value = """
        <html>
        <head><title>Test</title></head>
        <body><a href="/link1">Link 1</a><a href="/link2">Link 2</a></body>
        </html>
        """
        
        results = await traverser.traverse_links("https://example.com")
        
        # Should only fetch 1 page due to max_pages limit
        assert len(results) == 1