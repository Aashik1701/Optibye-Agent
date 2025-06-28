#!/bin/bash

# EMS Agent Microservices Startup Script
# This script starts all microservices individually for development

set -e

echo "🚀 Starting EMS Agent Microservices..."
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -i :$port > /dev/null 2>&1; then
        echo -e "${RED}Port $port is already in use${NC}"
        return 1
    fi
    return 0
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=1
    
    echo -e "${YELLOW}Waiting for $service_name to be ready...${NC}"
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $service_name is ready!${NC}"
            return 0
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo -e "${RED}❌ $service_name failed to start within timeout${NC}"
    return 1
}

# Kill any existing processes on our ports
echo -e "${YELLOW}Cleaning up existing processes...${NC}"
for port in 8000 8001 8002 8003 8004 8005; do
    if lsof -ti:$port > /dev/null 2>&1; then
        echo "Killing process on port $port"
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
    fi
done

sleep 2

# Set environment variables
export ENVIRONMENT=development
export MICROSERVICES_MODE=true
export PYTHONPATH=/Users/aashik/Documents/Sustainabyte/Optibyte_Agent

# Start services in background

echo -e "${BLUE}Starting API Gateway (Port 8000)...${NC}"
cd /Users/aashik/Documents/Sustainabyte/Optibyte_Agent
python -m gateway.api_gateway > logs/gateway.log 2>&1 &
GATEWAY_PID=$!
echo "Gateway PID: $GATEWAY_PID"

sleep 3

echo -e "${BLUE}Starting Data Ingestion Service (Port 8001)...${NC}"
cd /Users/aashik/Documents/Sustainabyte/Optibyte_Agent
python -m services.data_ingestion.service > logs/data_ingestion.log 2>&1 &
DATA_INGESTION_PID=$!
echo "Data Ingestion PID: $DATA_INGESTION_PID"

sleep 2

echo -e "${BLUE}Starting Analytics Service (Port 8002)...${NC}"
cd /Users/aashik/Documents/Sustainabyte/Optibyte_Agent
python -m services.analytics.service > logs/analytics.log 2>&1 &
ANALYTICS_PID=$!
echo "Analytics PID: $ANALYTICS_PID"

sleep 2

echo -e "${BLUE}Starting Advanced ML Service (Port 8003)...${NC}"
cd /Users/aashik/Documents/Sustainabyte/Optibyte_Agent
python -m services.advanced_ml.service > logs/advanced_ml.log 2>&1 &
ADVANCED_ML_PID=$!
echo "Advanced ML PID: $ADVANCED_ML_PID"

sleep 2

echo -e "${BLUE}Starting Monitoring Service (Port 8004)...${NC}"
cd /Users/aashik/Documents/Sustainabyte/Optibyte_Agent
python -m services.monitoring.service > logs/monitoring.log 2>&1 &
MONITORING_PID=$!
echo "Monitoring PID: $MONITORING_PID"

sleep 2

echo -e "${BLUE}Starting Query Processor Service (Port 8005)...${NC}"
cd /Users/aashik/Documents/Sustainabyte/Optibyte_Agent
python -m services.query_processor.service > logs/query_processor.log 2>&1 &
QUERY_PROCESSOR_PID=$!
echo "Query Processor PID: $QUERY_PROCESSOR_PID"

# Create logs directory if it doesn't exist
mkdir -p logs

# Save PIDs to file for easy cleanup later
echo "export GATEWAY_PID=$GATEWAY_PID" > pids.sh
echo "export DATA_INGESTION_PID=$DATA_INGESTION_PID" >> pids.sh
echo "export ANALYTICS_PID=$ANALYTICS_PID" >> pids.sh
echo "export ADVANCED_ML_PID=$ADVANCED_ML_PID" >> pids.sh
echo "export MONITORING_PID=$MONITORING_PID" >> pids.sh
echo "export QUERY_PROCESSOR_PID=$QUERY_PROCESSOR_PID" >> pids.sh

echo ""
echo -e "${YELLOW}Waiting for services to start up...${NC}"
sleep 10

# Check service health
echo ""
echo -e "${YELLOW}Checking service health...${NC}"

# Check each service
services=(
    "http://localhost:8000/health:API Gateway"
    "http://localhost:8001/health:Data Ingestion"
    "http://localhost:8002/health:Analytics"
    "http://localhost:8003/health:Advanced ML"
    "http://localhost:8004/health:Monitoring"
    "http://localhost:8005/health:Query Processor"
)

all_healthy=true

for service in "${services[@]}"; do
    url=$(echo $service | cut -d: -f1-2)
    name=$(echo $service | cut -d: -f3-)
    
    if curl -s -f "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $name: HEALTHY${NC}"
    else
        echo -e "${RED}❌ $name: UNHEALTHY${NC}"
        all_healthy=false
    fi
done

echo ""
if [ "$all_healthy" = true ]; then
    echo -e "${GREEN}🎉 All microservices are running successfully!${NC}"
    echo ""
    echo -e "${BLUE}📊 Service Endpoints:${NC}"
    echo "  • API Gateway:       http://localhost:8000"
    echo "  • Data Ingestion:    http://localhost:8001" 
    echo "  • Analytics:         http://localhost:8002"
    echo "  • Advanced ML:       http://localhost:8003"
    echo "  • Monitoring:        http://localhost:8004"
    echo "  • Query Processor:   http://localhost:8005"
    echo ""
    echo -e "${BLUE}🔍 Health Checks:${NC}"
    for service in "${services[@]}"; do
        url=$(echo $service | cut -d: -f1-2)
        name=$(echo $service | cut -d: -f3-)
        echo "  • $name: $url"
    done
    echo ""
    echo -e "${YELLOW}📝 Logs are available in the logs/ directory${NC}"
    echo -e "${YELLOW}🛑 To stop services, run: ./stop_services.sh${NC}"
    echo ""
    echo -e "${GREEN}Now you can start the main EMS Agent on port 5004:${NC}"
    echo -e "${BLUE}python app.py${NC}"
else
    echo -e "${RED}❌ Some services failed to start. Check logs for details.${NC}"
    echo -e "${YELLOW}Check individual service logs in the logs/ directory${NC}"
    exit 1
fi
