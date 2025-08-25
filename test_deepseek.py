#!/usr/bin/env python3
import asyncio
from ai_chat import AIChat

async def test():
    chat = AIChat('192.168.100.20', 11434, 'deepseek-r1:14b')
    await chat.start()
    response = await chat.generate_response('Say hello in 10 words or less', user_id='test123')
    print(f"Response: {response}")
    await chat.close()

if __name__ == "__main__":
    asyncio.run(test())