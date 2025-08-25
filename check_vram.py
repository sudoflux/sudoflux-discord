#!/usr/bin/env python3
"""Check VRAM usage and what's consuming it"""
import torch
import subprocess
import psutil

def check_vram():
    print("=" * 60)
    print("VRAM Usage Report")
    print("=" * 60)
    
    # Check if CUDA is available
    if not torch.cuda.is_available():
        print("CUDA is not available!")
        return
    
    # Get device info
    device = torch.cuda.current_device()
    device_name = torch.cuda.get_device_name(device)
    print(f"GPU: {device_name}")
    print()
    
    # Memory stats from PyTorch
    allocated = torch.cuda.memory_allocated(device) / 1024**3
    reserved = torch.cuda.memory_reserved(device) / 1024**3
    total = torch.cuda.get_device_properties(device).total_memory / 1024**3
    free = (torch.cuda.get_device_properties(device).total_memory - torch.cuda.memory_allocated(device)) / 1024**3
    
    print("PyTorch VRAM Stats:")
    print(f"  Total VRAM:     {total:.2f} GB")
    print(f"  Allocated:      {allocated:.2f} GB")
    print(f"  Reserved:       {reserved:.2f} GB")
    print(f"  Free:           {free:.2f} GB")
    print()
    
    # Try to get nvidia-smi output
    try:
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
        if result.returncode == 0:
            print("nvidia-smi output:")
            print("-" * 60)
            # Parse for memory usage
            for line in result.stdout.split('\n'):
                if 'MiB' in line and '/' in line:
                    print(line)
        print()
    except:
        print("nvidia-smi not available")
    
    # Check for running Python processes
    print("Python processes using GPU:")
    print("-" * 60)
    
    try:
        # Get all python processes
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            if 'python' in proc.info['name'].lower():
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if 'sd_server' in cmdline or 'stable' in cmdline.lower() or 'diffusion' in cmdline.lower():
                    print(f"PID {proc.info['pid']}: {cmdline[:100]}")
                    
                    # Try to get memory info
                    try:
                        mem_info = proc.memory_info()
                        print(f"  RAM: {mem_info.rss / 1024**3:.2f} GB")
                    except:
                        pass
    except Exception as e:
        print(f"Error checking processes: {e}")
    
    print()
    print("Possible causes of high VRAM usage:")
    print("-" * 60)
    print("1. SDXL model loaded (~6-7 GB)")
    print("2. VAE loaded separately (~1-2 GB)")
    print("3. Text encoders loaded (~1-2 GB)")
    print("4. Cached activations not cleared")
    print("5. Multiple model instances")
    print("6. Previous generations not cleaned up")
    print()
    
    print("Solutions:")
    print("-" * 60)
    print("1. Use sd_server_optimized.py instead of sd_server.py")
    print("2. Enable CPU offloading")
    print("3. Clear VRAM after each generation")
    print("4. Use VAE slicing and tiling")
    print("5. Restart the SD server periodically")

if __name__ == "__main__":
    check_vram()
    
    # Try to clear cache
    print()
    print("Attempting to clear PyTorch cache...")
    torch.cuda.empty_cache()
    torch.cuda.synchronize()
    
    # Check again
    allocated = torch.cuda.memory_allocated() / 1024**3
    print(f"After cache clear: {allocated:.2f} GB allocated")