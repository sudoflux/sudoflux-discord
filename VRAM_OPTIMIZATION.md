# VRAM Optimization Guide

## Problem: 13GB VRAM Usage with SDXL-Turbo

SDXL-Turbo should only use ~6-7GB VRAM, but you're seeing 13GB. Here's why and how to fix it.

## What's Using VRAM

### SDXL Model Components:
- **UNet**: ~5 GB (the main model)
- **VAE**: ~1.5 GB (encoder/decoder)
- **Text Encoders**: ~1.5 GB (CLIP models)
- **Cached Activations**: ~2-4 GB (intermediate tensors)
- **PyTorch Reserved**: ~2-3 GB (memory pool)

**Total**: Can easily reach 12-13 GB if not optimized!

## Check What's Running

Run on your GPU server (192.168.100.20):

```bash
# Check VRAM usage
nvidia-smi

# Find Python processes
ps aux | grep python | grep -E "sd|stable|diffusion"

# Check with our script
python3 check_vram.py
```

## Solutions

### 1. Use the Optimized Server (RECOMMENDED)

Replace `sd_server.py` with `sd_server_optimized.py`:

```bash
# Stop current server
pkill -f sd_server.py

# Start optimized version
python3 sd_server_optimized.py
```

**Benefits:**
- CPU offloading (keeps only active parts in VRAM)
- Clears VRAM after each generation
- VAE tiling and slicing
- Automatic mixed precision
- Periodic cleanup

### 2. Quick Fixes for Current Server

If you can't restart the server:

```bash
# Clear VRAM via API (if using optimized server)
curl -X POST http://192.168.100.20:7860/clear_vram

# Or restart the Python process
ssh 192.168.100.20
pkill -f sd_server.py
python3 sd_server.py
```

### 3. Configuration Options

Edit `sd_server_optimized.py` settings:

```python
# Aggressive memory saving (slower but uses ~4GB)
self.use_cpu_offload = True
self.clear_after_gen = True

# Balanced (faster, uses ~8GB)
self.use_cpu_offload = False  # Use model_cpu_offload instead
self.clear_after_gen = True

# Performance mode (fastest, uses ~12GB)
self.use_cpu_offload = False
self.clear_after_gen = False
```

### 4. Alternative Models

Consider switching to smaller models:

- **SDXL-Turbo**: Current, 6-7GB base
- **SD 1.5**: Only 2-3GB, still good quality
- **SDXL-Lightning**: 4-step model, similar to Turbo
- **LCM models**: Very fast, lower memory

### 5. Check for Other GPU Users

Your Ollama server might also be using VRAM:

```bash
# Check if Ollama is running
ps aux | grep ollama

# Check Ollama models loaded
curl http://192.168.100.20:11434/api/tags
```

## Monitoring Commands

```bash
# Watch VRAM in real-time
watch -n 1 nvidia-smi

# Check memory fragmentation
nvidia-smi -q -d MEMORY

# Python VRAM check
python3 -c "import torch; print(f'Allocated: {torch.cuda.memory_allocated()/1024**3:.2f}GB')"
```

## Expected VRAM Usage After Optimization

With `sd_server_optimized.py`:

- **Idle**: 2-3 GB (model in CPU RAM)
- **During generation**: 6-8 GB
- **After generation**: Back to 2-3 GB

## Emergency VRAM Clear

If VRAM is stuck:

```python
import torch
import gc

# Force cleanup
torch.cuda.empty_cache()
torch.cuda.synchronize()
gc.collect()

# Nuclear option - reset CUDA
torch.cuda.reset_peak_memory_stats()
torch.cuda.reset_accumulated_memory_stats()
```

## Recommended Setup

1. Use `sd_server_optimized.py`
2. Enable CPU offloading
3. Set quality presets in Discord bot:
   - fast: 4 steps (less VRAM)
   - balanced: 8 steps
   - quality: 12 steps (more VRAM)
4. Monitor with `check_vram.py`