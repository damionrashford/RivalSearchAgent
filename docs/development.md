# Development Guide for RivalSearchMCP

## Project Structure
- src/: Core code (core for retrieval, data_store for graph, reasoning for processor, tools for MCP handlers)
- tests/: Unit tests (use pytest)
- docs/: This documentation
- scripts/: Helpers (run_server.py main entry)

## Contributing
1. Fork repo
2. Create branch: git checkout -b feature/new
3. Develop/test: pytest tests/
4. Lint: ruff check .
5. Commit: git commit -m "Add feature"
6. PR to main

## Building/Testing
- Install dev deps: pip install pytest ruff
- Run tests: pytest tests/
- Lint: ruff check . --fix
- Build package: python setup.py sdist bdist_wheel

## Extending Tools
- Add new tool in src/tools/new_tool.py
- Define schema in API.md style
- Register in src/server.py list_tools/call_tool

## Deployment
- Use scripts/deploy.sh for Docker
- Prod: gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.server:app (if networked)

## Code Standards
- PEP8 via ruff
- Type hints everywhere
- Docstrings for all funcs/classes
- Keep files <200 LOC
