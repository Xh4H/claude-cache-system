#!/bin/bash
# Unified Web Scraper launcher for Claude

SCRAPER_DIR="/home/mik/PROJECTS/opensource-mcp-scrapers"
SCRAPER_SCRIPT="$SCRAPER_DIR/unified-scraper-mcp.py"

# Check if scraper exists
if [ ! -f "$SCRAPER_SCRIPT" ]; then
    echo "❌ Unified scraper not found at $SCRAPER_SCRIPT"
    echo "Run: cd $SCRAPER_DIR && ./setup-unified-scraper.sh"
    exit 1
fi

# Parse command
case "$1" in
    "serve"|"server"|"mcp")
        echo "🚀 Starting Unified Scraper MCP Server on port 8003..."
        cd "$SCRAPER_DIR"
        python unified-scraper-mcp.py --mcp
        ;;
    "test")
        echo "🧪 Running scraper tests..."
        cd "$SCRAPER_DIR"
        python test-unified-scraper.py
        ;;
    "help"|"--help"|"-h")
        echo "Unified Web Scraper - Claude Integration"
        echo ""
        echo "Usage:"
        echo "  unified-scraper <url>              # Scrape a URL"
        echo "  unified-scraper serve              # Start MCP server"
        echo "  unified-scraper test               # Run tests"
        echo "  unified-scraper help               # Show this help"
        echo ""
        echo "Examples:"
        echo "  unified-scraper https://example.com"
        echo "  unified-scraper https://example.com -s '.content'"
        echo "  unified-scraper https://example.com --search 'keyword'"
        ;;
    *)
        # Pass through to the Python script
        cd "$SCRAPER_DIR"
        python unified-scraper-mcp.py "$@"
        ;;
esac