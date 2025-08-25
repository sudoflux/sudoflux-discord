#!/bin/bash
# Script to stop SD server and save power

echo "Stopping SD server on 192.168.100.20..."

# Kill the server
ssh josh@192.168.100.20 "pkill -f sd_server"

echo "Waiting for GPU to idle..."
sleep 5

# Check GPU state
ssh josh@192.168.100.20 "nvidia-smi --query-gpu=name,pstate,power.draw,memory.used --format=csv"

echo ""
echo "SD server stopped. GPU should be in P8 state (low power)."