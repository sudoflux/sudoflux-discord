import aiohttp
import json
import logging
from typing import Optional, List, Dict
import asyncio
from collections import deque
from datetime import datetime, timedelta

logger = logging.getLogger('sudoflux-bot.ai')

class AIChat:
    def __init__(self, ollama_host: str = "192.168.100.20", ollama_port: int = 11434, model: str = "qwen2.5:14b"):
        self.base_url = f"http://{ollama_host}:{ollama_port}"
        self.model = model
        self.session = None
        
        # Conversation memory per user/channel
        self.conversations = {}
        self.max_context_messages = 10
        
        # Rate limiting
        self.user_last_message = {}
        self.rate_limit_seconds = 2
        
        # System prompt
        self.system_prompt = """You are a helpful Discord bot assistant for the sudoflux.io community server. 
You're friendly, knowledgeable about tech, gaming, retro computing, mechanical keyboards, and homelabs.
Keep responses concise and engaging. Use Discord markdown when helpful.
Be helpful but also casual and fun. You can use appropriate emojis occasionally.
If asked about the server, mention it's a tech and gaming community focused on DevOps, retro gaming, keyboards, and homelabs."""
    
    async def start(self):
        """Initialize the aiohttp session"""
        if not self.session:
            self.session = aiohttp.ClientSession()
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session:
            await self.session.close()
    
    def get_conversation_key(self, user_id: int, channel_id: Optional[int] = None) -> str:
        """Get a unique key for storing conversation context"""
        if channel_id:
            return f"{channel_id}:{user_id}"
        return f"dm:{user_id}"
    
    def add_to_context(self, key: str, role: str, content: str):
        """Add a message to conversation context"""
        if key not in self.conversations:
            self.conversations[key] = deque(maxlen=self.max_context_messages)
        
        self.conversations[key].append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow()
        })
    
    def get_context(self, key: str) -> List[Dict]:
        """Get conversation context, filtering out old messages"""
        if key not in self.conversations:
            return []
        
        # Filter messages older than 30 minutes
        cutoff = datetime.utcnow() - timedelta(minutes=30)
        recent = [msg for msg in self.conversations[key] 
                  if msg["timestamp"] > cutoff]
        
        # Update the deque with only recent messages
        self.conversations[key] = deque(recent, maxlen=self.max_context_messages)
        
        return [{"role": msg["role"], "content": msg["content"]} 
                for msg in self.conversations[key]]
    
    async def check_rate_limit(self, user_id: int) -> bool:
        """Check if user is rate limited"""
        now = datetime.utcnow()
        if user_id in self.user_last_message:
            time_passed = (now - self.user_last_message[user_id]).total_seconds()
            if time_passed < self.rate_limit_seconds:
                return False
        
        self.user_last_message[user_id] = now
        return True
    
    async def generate_response(self, prompt: str, user_id: int, channel_id: Optional[int] = None, search_context: str = "") -> Optional[str]:
        """Generate a response using Ollama"""
        try:
            if not self.session:
                await self.start()
            
            # Check rate limit
            if not await self.check_rate_limit(user_id):
                return "⏳ Please wait a moment before sending another message!"
            
            # Get conversation context
            conv_key = self.get_conversation_key(user_id, channel_id)
            context = self.get_context(conv_key)
            
            # Build the full prompt with context
            full_prompt = self.system_prompt + "\n\n"
            
            # Add search context if provided
            if search_context:
                full_prompt += f"Web Search Information:\n{search_context}\n\n"
            
            # Add conversation history
            for msg in context:
                if msg["role"] == "user":
                    full_prompt += f"User: {msg['content']}\n"
                else:
                    full_prompt += f"Assistant: {msg['content']}\n"
            
            # Add current message
            full_prompt += f"User: {prompt}\nAssistant: "
            
            # Make request to Ollama
            async with self.session.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "max_tokens": 500
                    }
                },
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    ai_response = data.get("response", "").strip()
                    
                    # Add to context
                    self.add_to_context(conv_key, "user", prompt)
                    self.add_to_context(conv_key, "assistant", ai_response)
                    
                    return ai_response
                else:
                    logger.error(f"Ollama API error: {response.status}")
                    return None
                    
        except asyncio.TimeoutError:
            logger.error("Ollama request timed out")
            return "⏱️ The AI is taking too long to respond. Please try again!"
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return None
    
    async def clear_context(self, user_id: int, channel_id: Optional[int] = None):
        """Clear conversation context for a user"""
        key = self.get_conversation_key(user_id, channel_id)
        if key in self.conversations:
            del self.conversations[key]
            return True
        return False