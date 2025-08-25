import aiohttp
import logging
from typing import List, Dict, Optional
import json
import re
from urllib.parse import quote_plus
import gzip

logger = logging.getLogger('sudoflux-bot.search')

class WebSearchV2:
    def __init__(self):
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    async def start(self):
        """Initialize the aiohttp session"""
        if not self.session:
            self.session = aiohttp.ClientSession()
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session:
            await self.session.close()
    
    async def search_ddg_lite(self, query: str, max_results: int = 5) -> List[Dict]:
        """Use DuckDuckGo Lite version which is simpler to parse"""
        try:
            if not self.session:
                await self.start()
            
            # Use the lite version of DuckDuckGo
            url = f"https://lite.duckduckgo.com/lite/?q={quote_plus(query)}"
            
            async with self.session.get(url, headers=self.headers) as response:
                if response.status != 200:
                    logger.error(f"DDG Lite returned status {response.status}")
                    return []
                
                html = await response.text()
                results = []
                
                # The lite version has simpler HTML structure
                # Look for result links - they're in a simpler format
                # Pattern: <a class="result-link" href="URL">Title</a>
                # Or simpler: <a href="http...">...</a> after "Web results"
                
                # Split by "Web results" to get to the actual results section
                if "Web results" in html:
                    results_section = html.split("Web results", 1)[1]
                else:
                    results_section = html
                
                # Find all external links
                link_pattern = r'<a[^>]*href=["\']?(https?://[^"\'>\s]+)[^>]*>([^<]+)</a>'
                matches = re.findall(link_pattern, results_section, re.IGNORECASE)
                
                seen_urls = set()
                for url, title in matches[:max_results * 2]:
                    # Clean up and filter
                    url = url.strip()
                    title = self.clean_html(title).strip()
                    
                    # Skip DDG internal links and duplicates
                    if ('duckduckgo.com' not in url and 
                        url not in seen_urls and 
                        len(title) > 5):
                        
                        seen_urls.add(url)
                        results.append({
                            'title': title[:200],
                            'url': url,
                            'snippet': ''  # Keep empty for cleaner output
                        })
                        
                        if len(results) >= max_results:
                            break
                
                return results
                
        except Exception as e:
            logger.error(f"DDG Lite search error: {e}")
            return []
    
    async def search_google_cse(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        Use Google Custom Search Engine JSON API
        Note: This requires API key and CSE ID to be configured
        Free tier: 100 queries/day
        """
        # These would need to be configured
        api_key = None  # Would need to be set
        cse_id = None   # Would need to be set
        
        if not api_key or not cse_id:
            return []
        
        try:
            if not self.session:
                await self.start()
            
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': api_key,
                'cx': cse_id,
                'q': query,
                'num': max_results
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    results = []
                    
                    for item in data.get('items', []):
                        results.append({
                            'title': item.get('title', ''),
                            'url': item.get('link', ''),
                            'snippet': item.get('snippet', '')
                        })
                    
                    return results
        except Exception as e:
            logger.error(f"Google CSE error: {e}")
        
        return []
    
    async def search(self, query: str, max_results: int = 5) -> List[Dict]:
        """Main search function that tries multiple methods"""
        # Try DDG Lite first
        results = await self.search_ddg_lite(query, max_results)
        
        if results:
            logger.info(f"Found {len(results)} results using DDG Lite")
            return results
        
        # Could try other methods here
        logger.warning(f"No results found for query: {query}")
        return []
    
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
            snippet = result.get('snippet', 'No description')[:200]
            
            output += f"**{i}. {title}**\n"
            if snippet:
                output += f"{snippet}...\n"
            output += f"🔗 <{url}>\n\n"
        
        return output[:2000]  # Discord message limit
    
    async def search_for_ai(self, query: str, max_results: int = 3) -> str:
        """Search and format results for AI context"""
        results = await self.search(query, max_results=max_results)
        
        if not results:
            return "No search results found."
        
        output = f"Web search results for '{query}':\n\n"
        for i, r in enumerate(results, 1):
            output += f"{i}. {r['title']}\n"
            output += f"   URL: {r['url']}\n"
            if r.get('snippet'):
                output += f"   {r['snippet']}\n\n"
        
        return output