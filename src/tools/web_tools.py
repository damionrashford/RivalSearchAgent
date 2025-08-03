"""
Web retrieval and research tools for FastMCP server.
Modular FastMCP approach - tools defined here, registered in server.py
"""

import asyncio
import json
from typing import Union, List
from mcp.server.fastmcp import FastMCP

from src.core.fetch import base_fetch_url, batch_rival_retrieve, stream_fetch
from src.core.bypass import refresh_proxies
from src.core.extract import extract_search_results, extract_triples
from src.core.traversal import traverse_website, research_topic, explore_documentation, map_website_structure
from src.data_store.manager import store_manager
from src.types.schemas import (
    RetrieveResult, StreamResult, TraversalResult, TraversalPage,
    SearchResult, WebContent
)


def register_web_tools(mcp: FastMCP):
    """Register all web retrieval and research tools."""
    
    @mcp.tool()
    async def rival_retrieve(
        resource: Union[str, List[str]],
        limit: int = 10,
        privacy: bool = False,
        cache: bool = False,
        store_data: bool = False,
        max_length: int = 5000,
        start_index: int = 0,
        raw: bool = False,
        traverse_links: bool = False,
        max_depth: int = 2,
        max_pages: int = 10,
        same_domain_only: bool = True
    ) -> RetrieveResult:
        """
        Retrieve any internet resource, bypassing limits/paywalls/anti-bot. 
        Use 'search:query' for Google search. Set traverse_links=True for deep content discovery.
        """
        await refresh_proxies()
        
        if isinstance(resource, list):
            # Batch retrieval mode
            contents = await batch_rival_retrieve(resource, {
                'limit': limit, 'privacy': privacy, 'cache': cache,
                'store_data': store_data, 'max_length': max_length,
                'start_index': start_index, 'raw': raw
            })
            
            return RetrieveResult(
                success=True,
                data=dict(zip(resource, contents)),
                truncated=False,
                remaining_bytes=0,
                original_url=str(resource),
                is_search=False
            )
        
        else:
            # Single resource mode
            is_search = resource.startswith("search:")
            url = resource[7:] if is_search else resource
            
            try:
                content = await base_fetch_url(url)
                
                if is_search:
                    # Search mode - extract results
                    results = extract_search_results(content, limit)
                    search_results = [
                        SearchResult(
                            title=r.get('title', ''),
                            link=r.get('link', ''),
                            snippet=r.get('snippet', '')
                        ) for r in results
                    ]
                    
                    # Store data if requested
                    if store_data:
                        triples = extract_triples(json.dumps(results))
                        node = {"name": url, "type": "resource", "facts": [f"{s} {p} {o}" for s, p, o in triples]}
                        store_manager.add_nodes([node])
                    
                    return RetrieveResult(
                        success=True,
                        data=search_results,
                        truncated=False,
                        remaining_bytes=0,
                        original_url=resource,
                        is_search=True
                    )
                
                else:
                    # Check if link traversal is requested
                    if traverse_links:
                        # Perform link traversal for comprehensive content discovery
                        traversal_result = await traverse_website(
                            start_url=url,
                            max_depth=max_depth,
                            max_pages=max_pages,
                            same_domain_only=same_domain_only
                        )
                        
                        # Convert to TraversalResult schema
                        pages = [
                            TraversalPage(
                                url=page["url"],
                                title=page["title"],
                                content=page["content"],
                                depth=page["depth"]
                            ) for page in traversal_result["pages"]
                        ]
                        
                        traversal_data = TraversalResult(
                            start_url=traversal_result["start_url"],
                            pages_fetched=traversal_result["pages_fetched"],
                            total_attempts=traversal_result["total_attempts"],
                            unique_links_found=traversal_result["unique_links_found"],
                            max_depth_reached=traversal_result["max_depth_reached"],
                            pages=pages,
                            summary=traversal_result["summary"],
                            config=traversal_result["config"]
                        )
                        
                        # Store traversal data if requested
                        if store_data:
                            for page in pages:
                                triples = extract_triples(page.content)
                                node = {
                                    "name": page.url, 
                                    "type": "webpage", 
                                    "facts": [f"title: {page.title}", f"depth: {page.depth}"] + [f"{s} {p} {o}" for s, p, o in triples]
                                }
                                store_manager.add_nodes([node])
                        
                        return RetrieveResult(
                            success=True,
                            data=traversal_data,
                            truncated=False,
                            remaining_bytes=0,
                            original_url=resource,
                            is_search=False,
                            is_traversal=True
                        )
                    
                    else:
                        # Regular web content mode
                        original_length = len(content)
                        
                        if start_index >= original_length:
                            return RetrieveResult(
                                success=False,
                                data=WebContent(content="", url=url),
                                truncated=False,
                                remaining_bytes=0,
                                original_url=resource,
                                is_search=False,
                                error_message="No more content."
                            )
                        
                        # Apply truncation logic
                        truncated = content[start_index:start_index + max_length]
                        remaining = original_length - (start_index + len(truncated))
                        is_truncated = len(truncated) == max_length and remaining > 0
                        
                        if is_truncated and not raw:
                            truncated += f"\n<error>Truncated. Retrieve with start_index {start_index + max_length} for more.</error>"
                        
                        final_content = truncated if not raw else content
                        
                        # Store data if requested
                        if store_data:
                            triples = extract_triples(final_content)
                            node = {"name": url, "type": "resource", "facts": [f"{s} {p} {o}" for s, p, o in triples]}
                            store_manager.add_nodes([node])
                        
                        return RetrieveResult(
                            success=True,
                            data=WebContent(content=final_content, url=url),
                            truncated=is_truncated,
                            remaining_bytes=remaining,
                            original_url=resource,
                            is_search=False
                        )
                        
            except Exception as e:
                return RetrieveResult(
                    success=False,
                    data=WebContent(content="", url=url),
                    truncated=False,
                    remaining_bytes=0,
                    original_url=resource,
                    is_search=is_search,
                    error_message=str(e)
                )


    @mcp.tool()
    async def research_website(
        url: str,
        max_pages: int = 5,
        store_data: bool = False
    ) -> RetrieveResult:
        """
        Research a topic by intelligently following related links on a website.
        Optimized for content discovery and research workflows.
        """
        try:
            await refresh_proxies()
            
            # Use the research-optimized traversal
            result = await research_topic(url, max_pages)
            
            # Convert to schema format
            pages = [
                TraversalPage(
                    url=page["url"],
                    title=page["title"],
                    content=page["content"],
                    depth=page["depth"]
                ) for page in result["pages"]
            ]
            
            traversal_data = TraversalResult(
                start_url=result["start_url"],
                pages_fetched=result["pages_fetched"],
                total_attempts=result["total_attempts"],
                unique_links_found=result["unique_links_found"],
                max_depth_reached=result["max_depth_reached"],
                pages=pages,
                summary=f"Research completed: {result['summary']}",
                config=result["config"]
            )
            
            # Store data if requested
            if store_data:
                for page in pages:
                    triples = extract_triples(page.content)
                    node = {
                        "name": page.url,
                        "type": "research_page",
                        "facts": [f"title: {page.title}", f"research_depth: {page.depth}"] + [f"{s} {p} {o}" for s, p, o in triples]
                    }
                    store_manager.add_nodes([node])
            
            return RetrieveResult(
                success=True,
                data=traversal_data,
                truncated=False,
                remaining_bytes=0,
                original_url=url,
                is_search=False,
                is_traversal=True
            )
            
        except Exception as e:
            return RetrieveResult(
                success=False,
                data=WebContent(content="", url=url),
                truncated=False,
                remaining_bytes=0,
                original_url=url,
                is_search=False,
                is_traversal=True,
                error_message=str(e)
            )


    @mcp.tool()
    async def explore_docs(
        url: str,
        max_pages: int = 15,
        store_data: bool = False
    ) -> RetrieveResult:
        """
        Explore documentation sites by following documentation links.
        Optimized for technical documentation and API references.
        """
        try:
            await refresh_proxies()
            
            # Use documentation-optimized traversal
            result = await explore_documentation(url, max_pages)
            
            # Convert to schema format
            pages = [
                TraversalPage(
                    url=page["url"],
                    title=page["title"],
                    content=page["content"],
                    depth=page["depth"]
                ) for page in result["pages"]
            ]
            
            traversal_data = TraversalResult(
                start_url=result["start_url"],
                pages_fetched=result["pages_fetched"],
                total_attempts=result["total_attempts"],
                unique_links_found=result["unique_links_found"],
                max_depth_reached=result["max_depth_reached"],
                pages=pages,
                summary=f"Documentation exploration: {result['summary']}",
                config=result["config"]
            )
            
            # Store data if requested
            if store_data:
                for page in pages:
                    triples = extract_triples(page.content)
                    node = {
                        "name": page.url,
                        "type": "documentation",
                        "facts": [f"title: {page.title}", f"doc_depth: {page.depth}"] + [f"{s} {p} {o}" for s, p, o in triples]
                    }
                    store_manager.add_nodes([node])
            
            return RetrieveResult(
                success=True,
                data=traversal_data,
                truncated=False,
                remaining_bytes=0,
                original_url=url,
                is_search=False,
                is_traversal=True
            )
            
        except Exception as e:
            return RetrieveResult(
                success=False,
                data=WebContent(content="", url=url),
                truncated=False,
                remaining_bytes=0,
                original_url=url,
                is_search=False,
                is_traversal=True,
                error_message=str(e)
            )


    @mcp.tool()
    async def map_website(
        url: str,
        max_pages: int = 20,
        store_data: bool = False
    ) -> RetrieveResult:
        """
        Map the overall structure and content of a website.
        Useful for understanding site architecture and discovering key pages.
        """
        try:
            await refresh_proxies()
            
            # Use structure mapping traversal
            result = await map_website_structure(url, max_pages)
            
            # Convert to schema format
            pages = [
                TraversalPage(
                    url=page["url"],
                    title=page["title"],
                    content=page["content"],
                    depth=page["depth"]
                ) for page in result["pages"]
            ]
            
            traversal_data = TraversalResult(
                start_url=result["start_url"],
                pages_fetched=result["pages_fetched"],
                total_attempts=result["total_attempts"],
                unique_links_found=result["unique_links_found"],
                max_depth_reached=result["max_depth_reached"],
                pages=pages,
                summary=f"Website mapping: {result['summary']}",
                config=result["config"]
            )
            
            # Store data if requested
            if store_data:
                for page in pages:
                    triples = extract_triples(page.content)
                    node = {
                        "name": page.url,
                        "type": "site_page",
                        "facts": [f"title: {page.title}", f"site_depth: {page.depth}"] + [f"{s} {p} {o}" for s, p, o in triples]
                    }
                    store_manager.add_nodes([node])
            
            return RetrieveResult(
                success=True,
                data=traversal_data,
                truncated=False,
                remaining_bytes=0,
                original_url=url,
                is_search=False,
                is_traversal=True
            )
            
        except Exception as e:
            return RetrieveResult(
                success=False,
                data=WebContent(content="", url=url),
                truncated=False,
                remaining_bytes=0,
                original_url=url,
                is_search=False,
                is_traversal=True,
                error_message=str(e)
            )


    @mcp.tool()
    async def stream_retrieve(url: str) -> StreamResult:
        """Retrieve streaming data from WebSocket URL."""
        try:
            content = await stream_fetch(url)
            # Count chunks by splitting on newlines (matches original logic)
            chunks = content.split('\n') if content else []
            
            return StreamResult(
                success=True,
                content=content,
                url=url,
                chunks_received=len(chunks)
            )
        except Exception as _:
            return StreamResult(
                success=False,
                content="",
                url=url,
                chunks_received=0
            )


    @mcp.tool()
    async def extract_images(
        url: str,
        include_ocr: bool = True,
        max_images: int = 10
    ) -> RetrieveResult:
        """
        Extract images from a web page with optional OCR text extraction.
        Demonstrates advanced multimedia content handling.
        """
        try:
            await refresh_proxies()
            
            # Get the page content
            content = await base_fetch_url(url)
            
            if not content:
                return RetrieveResult(
                    success=False,
                    data=WebContent(content="", url=url),
                    truncated=False,
                    remaining_bytes=0,
                    original_url=url,
                    is_search=False,
                    error_message="Could not retrieve page content"
                )
            
            # Extract images and OCR if requested
            from src.core.multi_modal import process_images_ocr
            from bs4 import BeautifulSoup
            import base64
            import httpx
            
            soup = BeautifulSoup(content, 'html.parser')
            img_tags = soup.find_all('img', limit=max_images)
            
            images = []
            ocr_texts = []
            
            if include_ocr:
                ocr_texts = await process_images_ocr(soup, url)
            
            # Process image tags to create image objects
            for img_tag in img_tags:
                img_src = img_tag.get('src', '')
                if not img_src:
                    continue
                    
                # Convert relative URLs to absolute
                if img_src.startswith('/'):
                    from urllib.parse import urljoin
                    img_src = urljoin(url, img_src)
                elif not img_src.startswith('http'):
                    continue
                
                try:
                    # Fetch image data (with size limit)
                    async with httpx.AsyncClient() as client:
                        img_response = await client.get(img_src, timeout=10)
                        if img_response.status_code == 200 and len(img_response.content) < 5 * 1024 * 1024:  # 5MB limit
                            # Create image object
                            img_data = base64.b64encode(img_response.content).decode('utf-8')
                            content_type = img_response.headers.get('content-type', 'image/jpeg')
                            
                            images.append({
                                "data": img_data,
                                "mimeType": content_type,
                                "url": img_src,
                                "alt": img_tag.get('alt', ''),
                                "size_bytes": len(img_response.content)
                            })
                            
                            if len(images) >= max_images:
                                break
                except:
                    continue  # Skip problematic images
            
            # Create enhanced WebContent with images
            web_content = WebContent(
                content=f"Extracted {len(images)} images from {url}",
                url=url,
                content_type="text/html",
                ocr_text=ocr_texts,
                images=images,
                has_multimedia=len(images) > 0
            )
            
            return RetrieveResult(
                success=True,
                data=web_content,
                truncated=False,
                remaining_bytes=0,
                original_url=url,
                is_search=False
            )
            
        except Exception as e:
            return RetrieveResult(
                success=False,
                data=WebContent(content="", url=url),
                truncated=False,
                remaining_bytes=0,
                original_url=url,
                is_search=False,
                error_message=f"Image extraction failed: {str(e)}"
            )