import aiohttp
import logging
from typing import List, Dict, Optional
import re
from urllib.parse import quote_plus
import json

logger = logging.getLogger('sudoflux-bot.search')

class WebSearch:
    def __init__(self):
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    async def start(self):
        """Initialize the aiohttp session"""
        if not self.session:
            self.session = aiohttp.ClientSession()
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session:
            await self.session.close()
    
    async def search_duckduckgo(self, query: str, max_results: int = 5) -> List[Dict]:
        """Search using DuckDuckGo HTML scraping"""
        try:
            if not self.session:
                await self.start()
            
            url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
            
            async with self.session.get(url, headers=self.headers) as response:
                if response.status != 200:
                    return []
                
                html = await response.text()
                results = []
                
                # Simple HTML parsing for results
                # DuckDuckGo HTML format: <a class="result__a" href="URL">Title</a>
                # <a class="result__snippet">Description</a>
                
                # Extract result blocks
                result_pattern = r'<div class="result results_links.*?>(.*?)</div>\s*</div>'
                matches = re.findall(result_pattern, html, re.DOTALL)
                
                for match in matches[:max_results]:
                    # Extract URL
                    url_match = re.search(r'href="(https?://[^"]+)"', match)
                    # Extract title
                    title_match = re.search(r'class="result__a"[^>]*>([^<]+)</a>', match)
                    # Extract snippet
                    snippet_match = re.search(r'class="result__snippet"[^>]*>([^<]+)', match)
                    
                    if url_match and title_match:
                        results.append({
                            'title': self.clean_html(title_match.group(1)),
                            'url': url_match.group(1),
                            'snippet': self.clean_html(snippet_match.group(1)) if snippet_match else ''
                        })
                
                return results
                
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    async def search_searxng(self, query: str, searxng_url: str = "http://192.168.100.20:8888", max_results: int = 5) -> List[Dict]:
        """Search using SearXNG instance"""
        try:
            if not self.session:
                await self.start()
            
            # Try SearXNG JSON API
            url = f"{searxng_url}/search"
            params = {
                'q': query,
                'format': 'json',
                'language': 'en',
                'safesearch': 0
            }
            
            async with self.session.get(url, params=params, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    results = []
                    for r in data.get('results', [])[:max_results]:
                        results.append({
                            'title': r.get('title', 'No title'),
                            'url': r.get('url', ''),
                            'snippet': r.get('content', '')
                        })
                    return results
                else:
                    # Fallback to DuckDuckGo
                    return await self.search_duckduckgo(query, max_results)
                    
        except Exception as e:
            logger.error(f"SearXNG search error: {e}, falling back to DuckDuckGo")
            return await self.search_duckduckgo(query, max_results)
    
    def clean_html(self, text: str) -> str:
        """Remove HTML tags and clean text"""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Decode HTML entities
        text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        text = text.replace('&quot;', '"').replace('&#39;', "'")
        text = text.replace('&nbsp;', ' ')
        # Clean up whitespace
        text = ' '.join(text.split())
        return text.strip()
    
    def format_results(self, results: List[Dict], query: str) -> str:
        """Format search results for Discord"""
        if not results:
            return f"No results found for: **{query}**"
        
        output = f"🔍 **Search results for: {query}**\n\n"
        
        for i, result in enumerate(results, 1):
            title = result['title'][:100]  # Limit title length
            url = result['url']
            snippet = result['snippet'][:200] if result['snippet'] else 'No description'
            
            output += f"**{i}. {title}**\n"
            output += f"{snippet}...\n"
            output += f"🔗 <{url}>\n\n"
        
        return output[:2000]  # Discord message limit
    
    async def search_for_ai(self, query: str, max_results: int = 3) -> str:
        """Search and format results for AI context"""
        results = await self.search_searxng(query, max_results=max_results)
        
        if not results:
            return "No search results found."
        
        output = f"Web search results for '{query}':\n\n"
        for i, r in enumerate(results, 1):
            output += f"{i}. {r['title']}\n"
            output += f"   URL: {r['url']}\n"
            output += f"   {r['snippet']}\n\n"
        
        return output