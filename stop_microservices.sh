#!/bin/bash

# EMS Agent Microservices Stop Script
# This script stops all running microservices

set -e

echo "🛑 Stopping EMS Agent Microservices..."
echo "====================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Load PIDs if available
if [ -f "pids.sh" ]; then
    source pids.sh
    
    # Kill processes by PID
    for pid_var in GATEWAY_PID DATA_INGESTION_PID ANALYTICS_PID ADVANCED_ML_PID MONITORING_PID QUERY_PROCESSOR_PID; do
        pid=${!pid_var}
        if [ ! -z "$pid" ] && kill -0 $pid 2>/dev/null; then
            echo -e "${YELLOW}Stopping process $pid_var ($pid)...${NC}"
            kill -TERM $pid 2>/dev/null || true
            sleep 2
            # Force kill if still running
            if kill -0 $pid 2>/dev/null; then
                kill -KILL $pid 2>/dev/null || true
                echo -e "${RED}Force killed $pid_var${NC}"
            else
                echo -e "${GREEN}✅ Stopped $pid_var${NC}"
            fi
        fi
    done
    
    # Remove PID file
    rm -f pids.sh
fi

# Also kill by port as backup
echo -e "${YELLOW}Cleaning up any remaining processes on microservice ports...${NC}"
for port in 8000 8001 8002 8003 8004 8005; do
    if lsof -ti:$port > /dev/null 2>&1; then
        echo "Killing remaining process on port $port"
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
    fi
done

# Clean up log files (optional)
read -p "Do you want to clean up log files? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Cleaning up log files...${NC}"
    rm -rf logs/*.log
    echo -e "${GREEN}✅ Log files cleaned${NC}"
fi

echo -e "${GREEN}🎉 All microservices stopped successfully!${NC}"
