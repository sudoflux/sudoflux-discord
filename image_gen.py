import aiohttp
import base64
import io
import logging
from typing import Optional, Dict
from PIL import Image

logger = logging.getLogger('sudoflux-bot.image')

class ImageGenerator:
    def __init__(self, sd_host: str = "192.168.100.20", sd_port: int = 7860):
        self.base_url = f"http://{sd_host}:{sd_port}"
        self.session = None
    
    async def start(self):
        """Initialize the aiohttp session"""
        if not self.session:
            self.session = aiohttp.ClientSession()
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session:
            await self.session.close()
    
    async def check_health(self) -> bool:
        """Check if SD server is running"""
        try:
            if not self.session:
                await self.start()
            
            async with self.session.get(f"{self.base_url}/health", timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('status') == 'healthy'
        except:
            return False
        return False
    
    async def generate(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        width: int = 1024,
        height: int = 1024,
        steps: int = 4,
        seed: int = -1
    ) -> Optional[Dict]:
        """Generate an image using Stable Diffusion"""
        try:
            if not self.session:
                await self.start()
            
            # Prepare request
            payload = {
                'prompt': prompt,
                'negative_prompt': negative_prompt or 'blurry, bad quality, watermark',
                'width': width,
                'height': height,
                'steps': steps,
                'guidance_scale': 0.0,  # SDXL-Turbo doesn't use CFG
                'seed': seed
            }
            
            # Make request with longer timeout for generation
            async with self.session.post(
                f"{self.base_url}/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('success'):
                        return {
                            'image_base64': data['image'],
                            'seed': data['seed'],
                            'prompt': data['prompt']
                        }
                    else:
                        logger.error(f"SD generation failed: {data.get('error')}")
                else:
                    logger.error(f"SD server returned status {response.status}")
                    
        except aiohttp.ClientTimeout:
            logger.error("Image generation timed out")
        except Exception as e:
            logger.error(f"Error generating image: {e}")
        
        return None
    
    async def base64_to_file(self, base64_str: str) -> io.BytesIO:
        """Convert base64 string to file-like object for Discord"""
        image_data = base64.b64decode(base64_str)
        return io.BytesIO(image_data)