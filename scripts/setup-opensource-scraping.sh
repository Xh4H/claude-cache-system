#!/bin/bash
# Setup completely free, open source web scraping for Claude Code

echo "🆓 Setting up Open Source Web Scraping Stack..."

# Create project directory
mkdir -p ~/PROJECTS/opensource-mcp-scrapers
cd ~/PROJECTS/opensource-mcp-scrapers

# 1. Clone Microsoft Playwright MCP
echo "1. Cloning official Playwright MCP..."
git clone https://github.com/microsoft/playwright-mcp playwright-official

# 2. Clone community versions
echo "2. Cloning community scrapers..."
git clone https://github.com/MaitreyaM/WEB-SCRAPING-MCP web-scraping-mcp
git clone https://github.com/executeautomation/mcp-playwright playwright-community

# 3. Create Python environment for custom scrapers
echo "3. Setting up Python environment..."
python3 -m venv scraper-env
source scraper-env/bin/activate

# Install scraping libraries
pip install beautifulsoup4 scrapy requests lxml pyquery mechanicalsoup

# 4. Create simple MCP wrapper
cat > simple-scraper-mcp.py << 'EOF'
#!/usr/bin/env python3
"""Minimal MCP server for web scraping"""

import sys
import json
import requests
from bs4 import BeautifulSoup

def scrape(url):
    try:
        resp = requests.get(url)
        soup = BeautifulSoup(resp.content, 'html.parser')
        return {
            "title": soup.title.string if soup.title else None,
            "text": soup.get_text()[:1000],
            "links": [a.get('href') for a in soup.find_all('a', href=True)][:10]
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    if len(sys.argv) > 1:
        result = scrape(sys.argv[1])
        print(json.dumps(result, indent=2))
    else:
        print("Usage: python simple-scraper-mcp.py <URL>")
EOF

chmod +x simple-scraper-mcp.py

# 5. Create requirements file
cat > requirements.txt << 'EOF'
beautifulsoup4>=4.12.0
scrapy>=2.11.0
requests>=2.31.0
lxml>=4.9.0
pyquery>=2.0.0
mechanicalsoup>=1.3.0
playwright>=1.40.0
EOF

echo "
✅ Open Source Scraping Setup Complete!

📁 Created in: ~/PROJECTS/opensource-mcp-scrapers/

🔧 Available Tools:
1. playwright-official/     - Microsoft's official Playwright MCP
2. web-scraping-mcp/       - crawl4ai-based scraper with Docker
3. playwright-community/   - ExecuteAutomation's enhanced version
4. simple-scraper-mcp.py  - Basic BeautifulSoup scraper
5. scraper-env/           - Python environment with all libraries

🚀 Quick Start:
1. For Playwright MCP:
   cd playwright-official && npm install

2. For Python scrapers:
   source scraper-env/bin/activate
   python simple-scraper-mcp.py https://example.com

3. For Docker-based:
   cd web-scraping-mcp && docker-compose up

💡 All 100% free, open source, and self-hosted!
"