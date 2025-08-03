import asyncio
import random
import httpx
import cloudscraper
from typing import List
from urllib.parse import urlparse
from src.core.bypass import select_ua, select_proxy, detect_paywall
from src.config import ARCHIVE_FALLBACKS
from src.core.multi_modal import process_images_ocr
from bs4 import BeautifulSoup
import websockets

async def base_fetch_url(url: str, timeout: int = 30) -> str:
    ua = select_ua()
    proxy = select_proxy()
    proxies_dict = {'http://': f"http://{proxy}", 'https://': f"http://{proxy}"} if proxy else None
    headers = {'User-Agent': ua}
    await asyncio.sleep(random.uniform(0.5, 2))
    try:
        if cloudscraper and random.random() < 0.3:
            scraper = cloudscraper.create_scraper()
            resp = scraper.get(url, proxies=proxies_dict, timeout=timeout)
        else:
            async with httpx.AsyncClient(proxies=proxies_dict if proxies_dict else None, follow_redirects=True) as client:
                resp = await client.get(url, headers=headers, timeout=timeout)
        content = resp.text
        if detect_paywall(content):
            for archive in ARCHIVE_FALLBACKS:
                archive_url = archive + url
                async with httpx.AsyncClient(proxies=proxies_dict if proxies_dict else None) as client:
                    resp = await client.get(archive_url, headers=headers, timeout=timeout)
                content = resp.text
                if not detect_paywall(content):
                    break
        soup = BeautifulSoup(content, 'html.parser')
        ocr_results = await process_images_ocr(soup, url)
        content += "\nImage Texts: \n" + "\n".join(ocr_results)
        return content
    except Exception as e:
        raise ValueError(f"Fetch failed: {str(e)}")

async def batch_rival_retrieve(resources: List[str], opts: dict) -> List[str]:
    tasks = [base_fetch_url(r) for r in resources]
    return await asyncio.gather(*tasks, return_exceptions=True)

async def stream_fetch(url: str) -> str:
    chunks = []
    async with websockets.connect(url) as ws:
        for _ in range(10):
            chunk = await ws.recv()
            chunks.append(str(chunk))
    return "\n".join(chunks)
