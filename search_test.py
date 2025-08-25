#!/usr/bin/env python3
import aiohttp
import asyncio
import json
from typing import List, Dict

async def search_brave(query: str) -> List[Dict]:
    """Search using Brave Search API (free tier)"""
    # Note: This would require a Brave API key
    # For now, let's use a different approach
    pass

async def search_searx(query: str) -> List[Dict]:
    """Search using public SearX instances"""
    searx_instances = [
        "https://searx.be",
        "https://searx.info", 
        "https://searx.xyz",
        "https://search.bus-hit.me",
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0'
    }
    
    async with aiohttp.ClientSession() as session:
        for instance in searx_instances:
            try:
                url = f"{instance}/search"
                params = {
                    'q': query,
                    'format': 'json',
                    'language': 'en-US'
                }
                
                async with session.get(url, params=params, headers=headers, timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = []
                        for r in data.get('results', [])[:5]:
                            results.append({
                                'title': r.get('title', 'No title'),
                                'url': r.get('url', ''),
                                'snippet': r.get('content', '')
                            })
                        if results:
                            print(f"Success with {instance}")
                            return results
            except Exception as e:
                print(f"Failed {instance}: {e}")
                continue
    
    return []

async def search_ddg_api(query: str) -> List[Dict]:
    """Use DuckDuckGo Instant Answer API"""
    url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                results = []
                
                # Get abstract if available
                if data.get('Abstract'):
                    results.append({
                        'title': data.get('Heading', query),
                        'url': data.get('AbstractURL', ''),
                        'snippet': data.get('Abstract', '')
                    })
                
                # Get related topics
                for topic in data.get('RelatedTopics', [])[:4]:
                    if isinstance(topic, dict) and 'Text' in topic:
                        results.append({
                            'title': topic.get('Text', '')[:100],
                            'url': topic.get('FirstURL', ''),
                            'snippet': topic.get('Text', '')
                        })
                
                return results
    
    return []

async def main():
    query = "python asyncio tutorial"
    
    print("Testing DuckDuckGo API...")
    results = await search_ddg_api(query)
    if results:
        print(f"Found {len(results)} results:")
        for r in results:
            print(f"  - {r['title'][:50]}...")
    else:
        print("No results")
    
    print("\nTesting SearX instances...")
    results = await search_searx(query)
    if results:
        print(f"Found {len(results)} results:")
        for r in results:
            print(f"  - {r['title'][:50]}...")
    else:
        print("No results from any SearX instance")

if __name__ == "__main__":
    asyncio.run(main())