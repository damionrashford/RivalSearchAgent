docker build -t rival-search-mcp .
docker run -d --name rival-mcp -v /Users/damionrashford/rival_search_mcp/data_store.json:/app/data_store.json rival-search-mcp python scripts/run_server.py
