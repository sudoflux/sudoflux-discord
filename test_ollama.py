#!/usr/bin/env python3
"""Test Ollama connection and model"""
import asyncio
import aiohttp

async def test_ollama():
    host = "192.168.100.20"
    port = 11434
    model = "qwen3:14b"
    
    print(f"Testing Ollama at {host}:{port} with model {model}")
    
    async with aiohttp.ClientSession() as session:
        # Test health
        async with session.get(f"http://{host}:{port}/api/tags") as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"✓ Ollama is running with {len(data['models'])} models")
                for m in data['models']:
                    print(f"  - {m['name']} ({m['details']['parameter_size']})")
            else:
                print(f"✗ Failed to connect to Ollama")
                return
        
        # Test generation
        print(f"\nTesting generation with {model}...")
        payload = {
            "model": model,
            "prompt": "Say hello in 5 words or less",
            "stream": False
        }
        
        async with session.post(
            f"http://{host}:{port}/api/generate",
            json=payload,
            timeout=aiohttp.ClientTimeout(total=60)
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                response = data.get('response', '').strip()
                print(f"✓ Model response: {response}")
                print(f"  Generation took: {data.get('total_duration', 0) / 1e9:.2f}s")
            else:
                print(f"✗ Generation failed: {resp.status}")

if __name__ == "__main__":
    asyncio.run(test_ollama())