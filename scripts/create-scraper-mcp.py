#!/usr/bin/env python3
"""
Template for creating your own open source MCP web scraping server
Using BeautifulSoup and Requests (100% free)
"""

import json
import asyncio
from typing import Dict, Any, List
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re

# MCP Protocol Implementation
class SimpleMCPServer:
    def __init__(self):
        self.tools = {
            "scrape_page": self.scrape_page,
            "extract_links": self.extract_links,
            "extract_text": self.extract_text,
            "extract_tables": self.extract_tables,
            "search_content": self.search_content
        }
    
    async def scrape_page(self, url: str, selector: str = None) -> Dict[str, Any]:
        """Scrape a webpage and optionally extract specific elements"""
        try:
            response = requests.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (compatible; MCP-Scraper/1.0)'
            })
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            if selector:
                elements = soup.select(selector)
                return {
                    "url": url,
                    "elements": [elem.get_text(strip=True) for elem in elements],
                    "count": len(elements)
                }
            else:
                return {
                    "url": url,
                    "title": soup.title.string if soup.title else None,
                    "text": soup.get_text(separator='\n', strip=True)[:5000],
                    "meta": self._extract_meta(soup)
                }
        except Exception as e:
            return {"error": str(e), "url": url}
    
    async def extract_links(self, url: str, pattern: str = None) -> List[str]:
        """Extract all links from a webpage"""
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            links = []
            for link in soup.find_all('a', href=True):
                href = urljoin(url, link['href'])
                if pattern:
                    if re.search(pattern, href):
                        links.append(href)
                else:
                    links.append(href)
            
            return list(set(links))  # Remove duplicates
        except Exception as e:
            return {"error": str(e)}
    
    async def extract_text(self, url: str, tag: str = None) -> str:
        """Extract clean text from a webpage"""
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            if tag:
                elements = soup.find_all(tag)
                text = '\n'.join([elem.get_text(strip=True) for elem in elements])
            else:
                text = soup.get_text(separator='\n', strip=True)
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return text[:10000]  # Limit response size
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def extract_tables(self, url: str) -> List[Dict]:
        """Extract tables from a webpage as structured data"""
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            tables = []
            for table in soup.find_all('table'):
                headers = []
                rows = []
                
                # Extract headers
                for th in table.find_all('th'):
                    headers.append(th.get_text(strip=True))
                
                # Extract rows
                for tr in table.find_all('tr'):
                    cells = [td.get_text(strip=True) for td in tr.find_all('td')]
                    if cells:
                        rows.append(cells)
                
                if rows:
                    tables.append({
                        "headers": headers,
                        "rows": rows
                    })
            
            return tables
        except Exception as e:
            return {"error": str(e)}
    
    async def search_content(self, url: str, query: str, context_chars: int = 100) -> List[Dict]:
        """Search for content in a webpage and return matches with context"""
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            text = soup.get_text()
            
            matches = []
            pattern = re.compile(re.escape(query), re.IGNORECASE)
            
            for match in pattern.finditer(text):
                start = max(0, match.start() - context_chars)
                end = min(len(text), match.end() + context_chars)
                context = text[start:end].strip()
                
                matches.append({
                    "match": match.group(),
                    "context": context,
                    "position": match.start()
                })
            
            return matches[:10]  # Limit results
        except Exception as e:
            return {"error": str(e)}
    
    def _extract_meta(self, soup) -> Dict[str, str]:
        """Extract metadata from HTML"""
        meta = {}
        
        # Open Graph tags
        for tag in soup.find_all('meta', property=re.compile(r'^og:')):
            if tag.get('content'):
                meta[tag['property']] = tag['content']
        
        # Twitter Card tags
        for tag in soup.find_all('meta', attrs={'name': re.compile(r'^twitter:')}):
            if tag.get('content'):
                meta[tag['name']] = tag['content']
        
        # Standard meta tags
        for tag in soup.find_all('meta', attrs={'name': ['description', 'keywords', 'author']}):
            if tag.get('content'):
                meta[tag['name']] = tag['content']
        
        return meta

# Example usage
if __name__ == "__main__":
    server = SimpleMCPServer()
    
    # Test the scraper
    async def test():
        result = await server.scrape_page("https://example.com")
        print(json.dumps(result, indent=2))
        
        links = await server.extract_links("https://example.com")
        print(f"\nFound {len(links)} links")
        
        tables = await server.extract_tables("https://example.com")
        print(f"\nFound {len(tables)} tables")
    
    asyncio.run(test())