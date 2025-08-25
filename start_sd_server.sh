#!/bin/bash
# On-demand script to start SD server when needed

echo "Starting SD server on 192.168.100.20..."

# Check if already running
ssh josh@192.168.100.20 "ps aux | grep -q '[s]d_server' && echo 'SD server already running!' && exit 1"

# Start the optimized server
ssh josh@192.168.100.20 "cd ~; nohup python3 sd_server_optimized.py > sd_server.log 2>&1 & echo Started SD server with PID: \$!"

echo ""
echo "Waiting for server to be ready..."
sleep 10

# Check health
curl -s http://192.168.100.20:7860/health | python3 -m json.tool

echo ""
echo "SD server is ready at http://192.168.100.20:7860"
echo "To stop it: ssh josh@192.168.100.20 'pkill -f sd_server_optimized'"