#!/bin/bash
# Setup web scraping MCP servers for Claude Code

CONFIG_FILE="$HOME/.claude.json"

echo "Setting up web scraping MCP servers..."

# Backup current config
cp "$CONFIG_FILE" "$CONFIG_FILE.backup-$(date +%Y%m%d-%H%M%S)"

# Install Playwright MCP
echo "1. Installing Playwright MCP Server..."
npm install -g @playwright/mcp@latest

# Create example scraping script
cat > "$HOME/.claude/scripts/web-scrape-demo.js" << 'EOF'
// Example: Using Playwright MCP for scraping
const playwright = require('playwright');

async function scrapeWithPlaywright(url) {
    const browser = await playwright.chromium.launch();
    const page = await browser.newPage();
    
    await page.goto(url);
    
    // Get page title
    const title = await page.title();
    
    // Get all links
    const links = await page.$$eval('a', links => 
        links.map(link => ({
            text: link.textContent,
            href: link.href
        }))
    );
    
    await browser.close();
    
    return { title, links };
}

// Usage
if (require.main === module) {
    scrapeWithPlaywright('https://example.com')
        .then(console.log)
        .catch(console.error);
}
EOF

echo "
✅ Web scraping setup complete!

To add Playwright MCP to Claude Code:
1. Open ~/.claude.json
2. Add to mcpServers section:
   
   \"playwright\": {
     \"command\": \"npx\",
     \"args\": [\"@playwright/mcp@latest\"]
   }

3. Restart Claude Code

For Firecrawl (needs API key):
   \"firecrawl\": {
     \"command\": \"npx\",
     \"args\": [\"-y\", \"firecrawl-mcp\"],
     \"env\": {
       \"FIRECRAWL_API_KEY\": \"your-key-here\"
     }
   }

Demo script created at: ~/.claude/scripts/web-scrape-demo.js
"