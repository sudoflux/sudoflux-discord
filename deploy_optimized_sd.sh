#!/bin/bash
# Deploy optimized SD server to GPU machine

GPU_HOST="192.168.100.20"
GPU_USER="josh"  # Change if different

echo "Deploying optimized SD server to $GPU_HOST..."
echo ""

# Step 1: Copy the optimized server
echo "Step 1: Copying optimized SD server..."
scp sd_server_optimized.py ${GPU_USER}@${GPU_HOST}:~/sd_server_optimized.py
scp check_vram.py ${GPU_USER}@${GPU_HOST}:~/check_vram.py

echo ""
echo "Step 2: Connect to GPU server and switch to optimized version"
echo "Run these commands after connecting:"
echo ""

cat << 'EOF'
# Connect to GPU server
ssh josh@192.168.100.20

# Once connected, run:

# 1. Check current VRAM usage
nvidia-smi

# 2. Find and kill the old SD server
ps aux | grep sd_server.py
# Note the PID and kill it
pkill -f sd_server.py
# or if that doesn't work:
# kill -9 <PID>

# 3. Verify it's killed
ps aux | grep sd_server

# 4. Check VRAM cleared
nvidia-smi

# 5. Start the optimized server
cd ~
nohup python3 sd_server_optimized.py > sd_server.log 2>&1 &

# 6. Check it's running
ps aux | grep sd_server_optimized
tail -f sd_server.log

# 7. Test the health endpoint
curl http://localhost:7860/health

# 8. Monitor VRAM usage
watch -n 1 nvidia-smi

# The optimized server should show:
# - Initial load: ~6-7 GB
# - After model loads: ~2-3 GB (with CPU offloading)
# - During generation: ~6-8 GB
# - After generation: back to ~2-3 GB

# To run in tmux/screen for persistence:
tmux new -s sd_server
python3 sd_server_optimized.py
# Ctrl+B, D to detach

# To reattach:
tmux attach -t sd_server

EOF

echo ""
echo "Optional: Create a systemd service for auto-start"
echo ""

cat << 'EOF'
# Create service file (on GPU server)
sudo tee /etc/systemd/system/sd-server.service << 'SERVICE'
[Unit]
Description=Stable Diffusion API Server
After=network.target

[Service]
Type=simple
User=josh
WorkingDirectory=/home/josh
ExecStart=/usr/bin/python3 /home/josh/sd_server_optimized.py
Restart=always
RestartSec=10
Environment="CUDA_VISIBLE_DEVICES=0"

[Install]
WantedBy=multi-user.target
SERVICE

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable sd-server
sudo systemctl start sd-server
sudo systemctl status sd-server

# View logs
sudo journalctl -u sd-server -f
EOF