#!/usr/bin/env python3
"""
Stable Diffusion API Server for Discord Bot
Runs on GPU server and provides image generation endpoint
"""

import asyncio
import base64
import io
import logging
from typing import Optional
import aiohttp
from aiohttp import web
import torch
from diffusers import StableDiffusionXLPipeline, DPMSolverMultistepScheduler
from PIL import Image
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('sd-server')

class SDServer:
    def __init__(self, model_id: str = "stabilityai/sdxl-turbo", port: int = 7860):
        self.model_id = model_id
        self.port = port
        self.pipe = None
        
    async def load_model(self):
        """Load the Stable Diffusion model"""
        logger.info(f"Loading model {self.model_id}...")
        
        # Use SDXL-Turbo for fast generation (1-4 steps)
        self.pipe = StableDiffusionXLPipeline.from_pretrained(
            self.model_id,
            torch_dtype=torch.float16,
            variant="fp16",
            use_safetensors=True
        )
        
        # Move to GPU
        self.pipe = self.pipe.to("cuda")
        
        # Use faster scheduler for turbo model
        self.pipe.scheduler = DPMSolverMultistepScheduler.from_config(
            self.pipe.scheduler.config
        )
        
        # Enable memory efficient attention
        self.pipe.enable_attention_slicing()
        self.pipe.enable_vae_slicing()
        
        logger.info("Model loaded successfully!")
    
    async def generate_image(self, request):
        """API endpoint to generate images"""
        try:
            data = await request.json()
            prompt = data.get('prompt', 'a beautiful landscape')
            negative_prompt = data.get('negative_prompt', 'blurry, bad quality')
            width = data.get('width', 1024)
            height = data.get('height', 1024)
            steps = data.get('steps', 4)  # SDXL-Turbo only needs 1-4 steps
            guidance_scale = data.get('guidance_scale', 0.0)  # Turbo doesn't use CFG
            seed = data.get('seed', -1)
            
            if seed == -1:
                seed = torch.randint(0, 2**32, (1,)).item()
            
            logger.info(f"Generating image: {prompt[:50]}...")
            
            # Set seed for reproducibility
            generator = torch.Generator(device="cuda").manual_seed(seed)
            
            # Generate image
            with torch.no_grad():
                image = self.pipe(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    width=width,
                    height=height,
                    num_inference_steps=steps,
                    guidance_scale=guidance_scale,
                    generator=generator
                ).images[0]
            
            # Convert to base64
            buffered = io.BytesIO()
            image.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()
            
            return web.json_response({
                'success': True,
                'image': img_base64,
                'seed': seed,
                'prompt': prompt
            })
            
        except Exception as e:
            logger.error(f"Error generating image: {e}")
            return web.json_response({
                'success': False,
                'error': str(e)
            }, status=500)
    
    async def health_check(self, request):
        """Health check endpoint"""
        return web.json_response({
            'status': 'healthy',
            'model': self.model_id,
            'cuda_available': torch.cuda.is_available()
        })
    
    async def start(self):
        """Start the API server"""
        await self.load_model()
        
        app = web.Application()
        app.router.add_post('/generate', self.generate_image)
        app.router.add_get('/health', self.health_check)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', self.port)
        
        logger.info(f"Starting SD server on port {self.port}")
        await site.start()

async def main():
    server = SDServer()
    await server.start()
    
    # Keep running
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())