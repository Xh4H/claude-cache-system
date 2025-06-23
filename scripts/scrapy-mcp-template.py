#!/usr/bin/env python3
"""
Scrapy-based MCP Server Template
Professional web scraping with Scrapy (100% open source)
"""

import json
import asyncio
from typing import Dict, Any, List
import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import tempfile
import os

class MCPSpider(scrapy.Spider):
    """Base spider for MCP scraping tasks"""
    name = 'mcp_spider'
    
    def __init__(self, urls=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = urls or []
        self.results = []
    
    def parse(self, response):
        # Extract data
        data = {
            'url': response.url,
            'title': response.css('title::text').get(),
            'headers': dict(response.headers),
            'links': response.css('a::attr(href)').getall(),
            'images': response.css('img::attr(src)').getall(),
            'text': ' '.join(response.css('p::text').getall()),
            'meta': self.extract_meta(response)
        }
        self.results.append(data)
        
        # Follow pagination if needed
        next_page = response.css('a.next::attr(href)').get()
        if next_page:
            yield response.follow(next_page, self.parse)
    
    def extract_meta(self, response):
        """Extract metadata"""
        meta = {}
        # Open Graph
        for prop in response.css('meta[property^="og:"]'):
            name = prop.css('::attr(property)').get()
            content = prop.css('::attr(content)').get()
            if name and content:
                meta[name] = content
        
        # Standard meta
        for tag in response.css('meta[name]'):
            name = tag.css('::attr(name)').get()
            content = tag.css('::attr(content)').get()
            if name and content:
                meta[name] = content
        
        return meta

class ScrapyMCPServer:
    """MCP Server using Scrapy for professional scraping"""
    
    def __init__(self):
        self.settings = {
            'USER_AGENT': 'Mozilla/5.0 (compatible; MCP-Scrapy/1.0)',
            'ROBOTSTXT_OBEY': True,
            'CONCURRENT_REQUESTS': 16,
            'DOWNLOAD_DELAY': 0.5,
            'COOKIES_ENABLED': False,
            'LOG_LEVEL': 'WARNING',
            'FEEDS': {},  # We'll handle results manually
        }
    
    async def scrape_site(self, urls: List[str], follow_links: bool = False, 
                         max_depth: int = 2) -> List[Dict]:
        """Scrape one or more URLs"""
        
        # Configure spider
        settings = get_project_settings()
        settings.update(self.settings)
        
        if follow_links:
            settings['DEPTH_LIMIT'] = max_depth
        
        # Run spider
        process = CrawlerProcess(settings)
        spider = MCPSpider
        spider.start_urls = urls
        
        # Store results
        results = []
        
        def collect_results(spider):
            results.extend(spider.results)
        
        # Connect signal
        from scrapy.signalmanager import dispatcher
        from scrapy import signals
        dispatcher.connect(collect_results, signal=signals.spider_closed)
        
        # Run crawler
        process.crawl(spider, urls=urls)
        process.start()
        
        return results
    
    async def scrape_with_rules(self, start_url: str, rules: Dict) -> List[Dict]:
        """Advanced scraping with custom rules"""
        
        class RuleSpider(scrapy.Spider):
            name = 'rule_spider'
            start_urls = [start_url]
            
            def parse(self, response):
                # Extract based on rules
                item = {}
                
                for field, selector in rules.get('fields', {}).items():
                    if selector.startswith('xpath:'):
                        item[field] = response.xpath(selector[6:]).get()
                    else:
                        item[field] = response.css(selector).get()
                
                # Extract lists
                for field, selector in rules.get('lists', {}).items():
                    if selector.startswith('xpath:'):
                        item[field] = response.xpath(selector[6:]).getall()
                    else:
                        item[field] = response.css(selector).getall()
                
                yield item
                
                # Follow links if specified
                if 'follow' in rules:
                    for link in response.css(rules['follow']):
                        yield response.follow(link, self.parse)
        
        # Run spider
        settings = get_project_settings()
        settings.update(self.settings)
        
        process = CrawlerProcess(settings)
        
        # Collect items
        items = []
        
        def item_scraped(item):
            items.append(dict(item))
        
        from scrapy.signalmanager import dispatcher
        from scrapy import signals
        dispatcher.connect(item_scraped, signal=signals.item_scraped)
        
        process.crawl(RuleSpider)
        process.start()
        
        return items
    
    async def scrape_api(self, api_url: str, params: Dict = None, 
                        pagination_key: str = 'next') -> List[Dict]:
        """Scrape JSON APIs with pagination support"""
        
        import requests
        
        results = []
        url = api_url
        
        while url:
            response = requests.get(url, params=params)
            data = response.json()
            
            # Extract items (handle different structures)
            if isinstance(data, list):
                results.extend(data)
                break  # No pagination
            elif isinstance(data, dict):
                # Look for common data keys
                for key in ['results', 'data', 'items']:
                    if key in data:
                        results.extend(data[key])
                        break
                
                # Check for pagination
                url = data.get(pagination_key)
                if not url and 'links' in data:
                    url = data['links'].get('next')
            
            # Safety limit
            if len(results) > 1000:
                break
        
        return results

# Example MCP tool definitions
MCP_TOOLS = {
    "scrapy_scrape": {
        "description": "Scrape websites using Scrapy",
        "parameters": {
            "urls": {"type": "array", "description": "URLs to scrape"},
            "follow_links": {"type": "boolean", "default": False},
            "max_depth": {"type": "integer", "default": 2}
        }
    },
    "scrapy_rules": {
        "description": "Scrape with custom extraction rules",
        "parameters": {
            "url": {"type": "string"},
            "rules": {
                "type": "object",
                "properties": {
                    "fields": {"type": "object", "description": "Single value selectors"},
                    "lists": {"type": "object", "description": "Multi value selectors"},
                    "follow": {"type": "string", "description": "Links to follow"}
                }
            }
        }
    },
    "scrapy_api": {
        "description": "Scrape JSON APIs with pagination",
        "parameters": {
            "api_url": {"type": "string"},
            "params": {"type": "object"},
            "pagination_key": {"type": "string", "default": "next"}
        }
    }
}

if __name__ == "__main__":
    # Example usage
    server = ScrapyMCPServer()
    
    # Example: Scrape with rules
    rules = {
        "fields": {
            "title": "h1::text",
            "price": ".price::text",
            "description": "xpath://div[@class='description']/text()"
        },
        "lists": {
            "features": ".feature-list li::text",
            "images": "img::attr(src)"
        },
        "follow": "a.next-page::attr(href)"
    }
    
    print("Scrapy MCP Server Template ready!")
    print("Example rules:", json.dumps(rules, indent=2))