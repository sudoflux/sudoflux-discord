#!/usr/bin/env python3
"""
Optimized Stable Diffusion API Server with better VRAM management
"""

import asyncio
import base64
import io
import logging
import gc
from typing import Optional
import aiohttp
from aiohttp import web
import torch
from diffusers import StableDiffusionXLPipeline, DPMSolverMultistepScheduler
from PIL import Image
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('sd-server-optimized')

class OptimizedSDServer:
    def __init__(self, model_id: str = "stabilityai/sdxl-turbo", port: int = 7860):
        self.model_id = model_id
        self.port = port
        self.pipe = None
        self.use_cpu_offload = True  # Enable CPU offloading
        self.clear_after_gen = True  # Clear VRAM after each generation
        
    async def load_model(self):
        """Load the Stable Diffusion model with optimizations"""
        logger.info(f"Loading model {self.model_id} with optimizations...")
        
        # Clear any existing VRAM
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
            
        # Log initial VRAM
        if torch.cuda.is_available():
            allocated = torch.cuda.memory_allocated() / 1024**3
            reserved = torch.cuda.memory_reserved() / 1024**3
            logger.info(f"Initial VRAM: {allocated:.2f}GB allocated, {reserved:.2f}GB reserved")
        
        # Load with memory optimizations
        self.pipe = StableDiffusionXLPipeline.from_pretrained(
            self.model_id,
            torch_dtype=torch.float16,
            variant="fp16",
            use_safetensors=True,
            low_cpu_mem_usage=True  # Reduce CPU memory during loading
        )
        
        # Use sequential CPU offloading - moves model layers to CPU when not in use
        if self.use_cpu_offload:
            logger.info("Enabling sequential CPU offloading...")
            self.pipe.enable_sequential_cpu_offload()
        else:
            # If not using CPU offload, at least use model CPU offload
            logger.info("Enabling model CPU offloading...")
            self.pipe.enable_model_cpu_offload()
        
        # Memory efficient attention
        logger.info("Enabling memory optimizations...")
        self.pipe.enable_attention_slicing()
        self.pipe.enable_vae_slicing()
        self.pipe.enable_vae_tiling()  # Additional VAE optimization
        
        # Use faster scheduler
        self.pipe.scheduler = DPMSolverMultistepScheduler.from_config(
            self.pipe.scheduler.config
        )
        
        # Clear cache after loading
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            allocated = torch.cuda.memory_allocated() / 1024**3
            reserved = torch.cuda.memory_reserved() / 1024**3
            logger.info(f"After loading - VRAM: {allocated:.2f}GB allocated, {reserved:.2f}GB reserved")
        
        logger.info("Model loaded with optimizations!")
    
    def cleanup_vram(self):
        """Clean up VRAM usage"""
        if torch.cuda.is_available():
            # Force garbage collection
            gc.collect()
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
            
            # Log VRAM after cleanup
            allocated = torch.cuda.memory_allocated() / 1024**3
            reserved = torch.cuda.memory_reserved() / 1024**3
            logger.info(f"After cleanup - VRAM: {allocated:.2f}GB allocated, {reserved:.2f}GB reserved")
    
    async def generate_image(self, request):
        """API endpoint to generate images with VRAM management"""
        try:
            data = await request.json()
            prompt = data.get('prompt', 'a beautiful landscape')
            negative_prompt = data.get('negative_prompt', 'blurry, bad quality')
            width = data.get('width', 1024)
            height = data.get('height', 1024)
            steps = data.get('steps', 8)
            guidance_scale = data.get('guidance_scale', 2.0)
            seed = data.get('seed', -1)
            
            if seed == -1:
                seed = torch.randint(0, 2**32, (1,)).item()
            
            logger.info(f"Generating image: {prompt[:50]}... (steps={steps}, guidance={guidance_scale})")
            
            # Log VRAM before generation
            if torch.cuda.is_available():
                allocated = torch.cuda.memory_allocated() / 1024**3
                logger.info(f"Before generation - VRAM: {allocated:.2f}GB allocated")
            
            # Set seed for reproducibility
            generator = torch.Generator(device="cuda").manual_seed(seed)
            
            # Generate image
            with torch.no_grad():
                with torch.cuda.amp.autocast():  # Use automatic mixed precision
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
            
            # Clean up VRAM after generation if enabled
            if self.clear_after_gen:
                self.cleanup_vram()
            
            return web.json_response({
                'success': True,
                'image': img_base64,
                'seed': seed,
                'prompt': prompt
            })
            
        except Exception as e:
            logger.error(f"Error generating image: {e}")
            # Clean up on error
            self.cleanup_vram()
            return web.json_response({
                'success': False,
                'error': str(e)
            }, status=500)
    
    async def health_check(self, request):
        """Health check endpoint with memory stats"""
        stats = {
            'status': 'healthy',
            'model': self.model_id,
            'cuda_available': torch.cuda.is_available()
        }
        
        if torch.cuda.is_available():
            stats['vram_allocated_gb'] = round(torch.cuda.memory_allocated() / 1024**3, 2)
            stats['vram_reserved_gb'] = round(torch.cuda.memory_reserved() / 1024**3, 2)
            stats['vram_free_gb'] = round((torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated()) / 1024**3, 2)
        
        return web.json_response(stats)
    
    async def clear_vram_endpoint(self, request):
        """Endpoint to manually clear VRAM"""
        logger.info("Manual VRAM clear requested...")
        self.cleanup_vram()
        return web.json_response({'status': 'VRAM cleared'})
    
    async def start(self):
        """Start the API server"""
        await self.load_model()
        
        app = web.Application()
        app.router.add_post('/generate', self.generate_image)
        app.router.add_get('/health', self.health_check)
        app.router.add_post('/clear_vram', self.clear_vram_endpoint)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', self.port)
        
        logger.info(f"Starting optimized SD server on port {self.port}")
        logger.info("Features enabled:")
        logger.info(f"  - CPU offloading: {self.use_cpu_offload}")
        logger.info(f"  - Clear VRAM after generation: {self.clear_after_gen}")
        logger.info("  - Memory efficient attention: Yes")
        logger.info("  - VAE slicing and tiling: Yes")
        logger.info("  - Automatic mixed precision: Yes")
        
        await site.start()
        
        # Periodic VRAM cleanup (every 5 minutes)
        asyncio.create_task(self.periodic_cleanup())
    
    async def periodic_cleanup(self):
        """Periodically clean up VRAM"""
        while True:
            await asyncio.sleep(300)  # Every 5 minutes
            logger.info("Running periodic VRAM cleanup...")
            self.cleanup_vram()

async def main():
    # Check for environment variables
    model_id = os.getenv('SD_MODEL', 'stabilityai/sdxl-turbo')
    port = int(os.getenv('SD_PORT', '7860'))
    
    server = OptimizedSDServer(model_id=model_id, port=port)
    await server.start()
    
    # Keep running
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())