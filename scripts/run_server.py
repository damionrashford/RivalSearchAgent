import argparse
import asyncio
from src.server import serve

parser = argparse.ArgumentParser(description="Run RivalSearchMCP Server")
parser.add_argument("--user-agent", type=str, help="Custom User-Agent")
parser.add_argument("--ignore-robots-txt", action="store_true", help="Ignore robots.txt")
parser.add_argument("--proxy-url", type=str, help="Proxy URL")
args = parser.parse_args()

asyncio.run(serve(args.user_agent, args.ignore_robots_txt, args.proxy_url))
