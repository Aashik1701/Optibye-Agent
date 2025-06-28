# EMS Agent Troubleshooting Guide
## Common Issues and Solutions

**Last Updated:** June 28, 2025  
**Current System Status:** ✅ Operational (Hybrid AI Mode)

---

## 🚨 **Current Known Issues**

### **1. Microservices Dependencies**

#### **Advanced ML Service (Port 8003) - XGBoost Issue**
```
Error: XGBoost Library (libxgboost.dylib) could not be loaded
```

**Solution:**
```bash
# macOS
brew install libomp

# If brew is not available, install Xcode command line tools first
xcode-select --install
brew install libomp

# Alternative: Use conda
conda install libomp

# Ubuntu/Debian
sudo apt-get install libomp-dev

# After installing, restart the service
python -m services.advanced_ml.service
```

#### **Monitoring Service (Port 8004) - Missing psutil**
```
Error: ModuleNotFoundError: No module named 'psutil'
```

**Solution:**
```bash
# Install psutil
pip install psutil

# Or install from requirements
pip install -r requirements.optimized.txt

# Verify installation
python -c "import psutil; print('psutil installed successfully')"
```

### **2. Hybrid AI Routing Issues (88% Accuracy)**

#### **Incorrect Routing Examples:**
- "What are the latest news?" → Routes to EMS (should be General AI)
- "Help me" → Routes to General AI (should be EMS in context)
- "What can you do?" → Routes to General AI (should be EMS for capabilities)

**Solution (Code Fix Needed):**
```python
# In app.py, update routing keywords
general_keywords = [
    'weather', 'news', 'sports', 'movie', 'music', 'recipe', 'cooking',
    'joke', 'story', 'book', 'game', 'travel', 'shopping', 'entertainment',
    'latest', 'current events', 'today', 'recent'  # Add these
]

# Add capability-related keywords to EMS
ems_capability_keywords = [
    'what can you do', 'capabilities', 'features', 'help me with energy',
    'how to use', 'instructions'
]
```

---

## 🔧 **Port Conflicts**

### **Issue: Port 8000 Already in Use**
```
Error: [Errno 48] Address already in use
```

**Diagnosis:**
```bash
# Check what's using port 8000
lsof -i :8000

# Common culprits: Docker, other development servers
```

**Solutions:**
```bash
# Option 1: Kill the conflicting process
lsof -ti:8000 | xargs kill -9

# Option 2: Stop Docker containers
docker-compose down
docker stop $(docker ps -q)

# Option 3: Use different port
# Edit gateway/api_gateway.py line 597
# Change port=8000 to port=8001
```

### **Issue: Main App Port 5004 Conflicts**
```bash
# Check and kill process on 5004
lsof -ti:5004 | xargs kill -9

# Or find the specific Python process
ps aux | grep "python app.py"
kill -9 <PID>
```

---

## 🗄️ **Database Issues**

### **MongoDB Connection Failures**

#### **Issue: Connection Timeout**
```
Error: ServerSelectionTimeoutError: connection timeout
```

**Solutions:**
```bash
# 1. Check network connectivity
ping cluster20526.g4udhpz.mongodb.net

# 2. Verify connection string in .env
cat .env | grep MONGODB_URI

# 3. Test connection manually
python -c "
from pymongo import MongoClient
import os
from dotenv import load_dotenv
load_dotenv()
client = MongoClient(os.getenv('MONGODB_URI'))
print(client.admin.command('ping'))
"

# 4. Check firewall/VPN settings
# MongoDB Atlas requires whitelist IPs
```

#### **Issue: Authentication Failed**
```
Error: Authentication failed
```

**Solutions:**
```bash
# 1. Verify credentials in connection string
# Format: mongodb+srv://username:password@cluster.mongodb.net/

# 2. Check user permissions in MongoDB Atlas
# Ensure user has readWrite permissions

# 3. URL encode special characters in password
# @ → %40, # → %23, etc.
```

### **Database Collection Issues**
```
Error: 'raw_data' collection not found
```

**Solutions:**
```bash
# 1. Load sample data
python -c "
from data_loader import EMSDataLoader
loader = EMSDataLoader()
loader.load_excel_file('EMS_Energy_Meter_Data.xlsx')
"

# 2. Create collections manually
python -c "
from ems_search import EMSQueryEngine
engine = EMSQueryEngine()
engine.initialize_database()
"
```

---

## 🤖 **AI Service Issues**

### **Gemini API Problems**

#### **Issue: API Key Not Set**
```
Error: API key not configured for Gemini
```

**Solution:**
```bash
# 1. Get API key from Google AI Studio
# Visit: https://makersuite.google.com/app/apikey

# 2. Add to .env file
echo "GEMINI_API_KEY=your-actual-api-key-here" >> .env

# 3. Restart application
python app.py
```

#### **Issue: API Rate Limiting**
```
Error: 429 Too Many Requests
```

**Solutions:**
```bash
# 1. Implement retry logic (already done in app.py)
# 2. Check Gemini API quotas
# 3. Consider upgrading API plan
# 4. Add caching for repeated queries
```

### **EMS Specialist Performance Issues**

#### **Issue: Slow Response Times (>5 seconds)**
```bash
# Check database query performance
python -c "
import time
from ems_search import EMSQueryEngine
engine = EMSQueryEngine()
start = time.time()
result = engine.get_latest_readings()
print(f'Query time: {time.time() - start:.2f}s')
"

# Solutions:
# 1. Add database indexes
# 2. Optimize queries
# 3. Implement caching
```

---

## 🌐 **Network & Connectivity**

### **Service Discovery Issues**

#### **Issue: Microservices Can't Find Each Other**
```bash
# Check service URLs
curl -I http://localhost:8001/health
curl -I http://localhost:8002/health

# Update service URLs if needed
export ANALYTICS_SERVICE_URL=http://localhost:8002
export DATA_INGESTION_SERVICE_URL=http://localhost:8001
```

#### **Issue: API Gateway Circuit Breaker Open**
```json
{
  "circuit_breaker": {
    "analytics": {"state": "open", "failures": 7}
  }
}
```

**Solutions:**
```bash
# 1. Restart the failed service
python -m services.analytics.service

# 2. Reset circuit breaker (wait 30 seconds)
# Circuit breaker automatically attempts reset

# 3. Check service health directly
curl http://localhost:8002/health
```

---

## 📊 **Performance Issues**

### **High Memory Usage**
```bash
# Check memory usage
ps aux | grep python | awk '{print $6, $11}' | sort -n

# Solutions:
# 1. Restart services periodically
# 2. Optimize data processing
# 3. Implement connection pooling
```

### **Slow Response Times**
```bash
# Profile response times
curl -w "@curl-format.txt" -s -o /dev/null http://localhost:5004/api/status

# Create curl-format.txt:
echo "
     time_namelookup:  %{time_namelookup}
        time_connect:  %{time_connect}
     time_appconnect:  %{time_appconnect}
    time_pretransfer:  %{time_pretransfer}
       time_redirect:  %{time_redirect}
  time_starttransfer:  %{time_starttransfer}
                     ----------
          time_total:  %{time_total}
" > curl-format.txt
```

---

## 🛠️ **Development Issues**

### **Import Errors**
```
ModuleNotFoundError: No module named 'common'
```

**Solutions:**
```bash
# 1. Set PYTHONPATH
export PYTHONPATH=/path/to/EMS-Agent:$PYTHONPATH

# 2. Add to your shell profile
echo 'export PYTHONPATH="/path/to/EMS-Agent:$PYTHONPATH"' >> ~/.zshrc

# 3. Use absolute imports
python -m services.analytics.service
```

### **Docker Issues**
```bash
# Invalid docker-compose.yml
docker-compose config

# Fix duplicate service names
# Edit docker-compose.yml to remove duplicates

# Clean Docker state
docker system prune -a
docker-compose down --volumes
```

---

## 🔍 **Debugging Tools**

### **Log Analysis**
```bash
# Real-time logs
tail -f logs/*.log

# Search for errors
grep -i error logs/*.log

# Check specific service logs
tail -f logs/analytics.log
tail -f logs/gateway.log
```

### **Health Check Script**
```bash
#!/bin/bash
# save as check_health.sh

echo "🔍 EMS Agent Health Check"
echo "========================="

# Main application
echo -n "Main App (5004): "
curl -s -f http://localhost:5004/health > /dev/null && echo "✅ OK" || echo "❌ FAIL"

# API Gateway
echo -n "API Gateway (8000): "
curl -s -f http://localhost:8000/health > /dev/null && echo "✅ OK" || echo "❌ FAIL"

# Microservices
for port in 8001 8002 8003 8004 8005; do
    echo -n "Service ($port): "
    curl -s -f http://localhost:$port/health > /dev/null && echo "✅ OK" || echo "❌ FAIL"
done

# Database
echo -n "Database: "
python -c "
try:
    from ems_search import EMSQueryEngine
    engine = EMSQueryEngine()
    engine.get_latest_readings()
    print('✅ OK')
except:
    print('❌ FAIL')
"
```

### **Performance Monitoring**
```bash
# Monitor resource usage
top -pid $(pgrep -f "python app.py")

# Network connections
netstat -an | grep LISTEN | grep -E ":(5004|8000|800[1-5])"

# Disk usage
du -sh logs/
df -h
```

---

## 📋 **Quick Fixes Checklist**

### **When Starting Fresh:**
```bash
# 1. Kill all existing processes
./stop_microservices.sh
pkill -f "python app.py"

# 2. Clear logs
rm -f logs/*.log

# 3. Start in order
./start_microservices.sh  # Optional
python app.py             # Main application

# 4. Verify
python test_hybrid_ai_complete.py
```

### **For Production Issues:**
```bash
# 1. Check system resources
free -h
df -h
ps aux | grep python

# 2. Check service health
curl http://localhost:5004/api/status | jq

# 3. Check logs for errors
grep -i "error\|exception\|traceback" logs/*.log

# 4. Restart problematic services
# Individual service restart based on logs
```

---

## 📞 **Getting Help**

### **Log Collection**
```bash
# Collect all logs for support
tar -czf ems-logs-$(date +%Y%m%d).tar.gz logs/
tar -czf ems-config-$(date +%Y%m%d).tar.gz .env docker-compose.yml requirements*.txt
```

### **System Information**
```bash
# Collect system info
python --version > system-info.txt
pip list >> system-info.txt
uname -a >> system-info.txt
docker --version >> system-info.txt
```

### **Test Results**
```bash
# Run diagnostics
python test_hybrid_ai_complete.py > test-results.txt 2>&1
```

---

**📋 Remember:** Most issues can be resolved by restarting services and checking logs. The system is designed to be resilient and will often recover automatically from transient issues.
