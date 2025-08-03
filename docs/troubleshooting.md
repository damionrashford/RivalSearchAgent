# Troubleshooting Guide for RivalSearchMCP

## Common Issues

### Installation Errors
- Missing deps: Run pip install -r requirements.txt
- Tesseract not found: Install system package (e.g., apt install tesseract-ocr)
- IPFS connect fail: Start IPFS daemon or disable cache

### Runtime Errors
- Fetch timeouts: Increase timeout in config.py or check network
- Proxy empty: Run await refresh_proxies() manually or check free-proxy-list.net access
- Paywall not bypassed: Add more ARCHIVE_FALLBACKS in core/bypass.py
- OCR fails: Ensure Tesseract languages installed (tesseract --list-langs)
- Data store corruption: Delete data_store.json and restart

### Performance Issues
- Slow fetches: Reduce batch size or disable multi-modal for non-image needs
- High memory: Limit graph size or use external DB (future extension)
- Anti-bot blocks: Rotate proxies/UA more frequently (adjust in bypass.py)

### MCP Integration
- Tool not found: Restart client/server
- Invalid params: Check tool schemas in api.md
- No response: Verify stdio connection, check logger.py output

### Logs/Debug
- Enable verbose: Set LOG_LEVEL=DEBUG in env
- Suppress reasoning logs: SUPPRESS_LOGS=true

If issue persists, check GitHub issues or file new with logs.
