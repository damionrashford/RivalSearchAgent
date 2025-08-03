import random
import asyncio
import httpx
from typing import List
from bs4 import BeautifulSoup
from src.config import DEFAULT_UA_LIST, PAYWALL_INDICATORS, ARCHIVE_FALLBACKS

async def get_proxies(count=20) -> List[str]:
    url = "https://free-proxy-list.net/"
    try:
        resp = await httpx.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        table = soup.find('table')
        proxies_list = []
        if table:
            rows = table.find_all('tr')[1:]
            for row in rows:
                cols = row.find_all('td')
                if len(cols) > 7 and cols[6].text.lower() == 'yes' and cols[4].text.lower() in ['elite proxy', 'anonymous']:
                    proxies_list.append(f"{cols[0].text}:{cols[1].text}")
                if len(proxies_list) >= count:
                    break
        return proxies_list
    except:
        return []

proxies = []

async def refresh_proxies():
    global proxies
    proxies = await get_proxies()

def select_ua():
    return random.choice(DEFAULT_UA_LIST)

def select_proxy():
    return random.choice(proxies) if proxies else None

def detect_paywall(content: str) -> bool:
    return any(ind in content.lower() for ind in PAYWALL_INDICATORS)
