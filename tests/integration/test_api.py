"""Integration tests for EMS Agent API endpoints"""

import pytest
import requests
import json
from typing import Dict, Any

# Test configuration
BASE_URL = "http://localhost:5004"
GATEWAY_URL = "http://localhost:8000"

class TestEMSAgentIntegration:
    """Integration tests for EMS Agent API endpoints"""
    
    @pytest.fixture(scope="class")
    def base_url(self):
        """Base URL for the EMS Agent"""
        return BASE_URL
    
    @pytest.fixture(scope="class") 
    def gateway_url(self):
        """Base URL for the API Gateway"""
        return GATEWAY_URL
    
    def test_ems_agent_health_endpoint(self, base_url):
        """Test EMS Agent health check endpoint"""
        response = requests.get(f"{base_url}/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "online"]
    
    def test_ems_agent_status_endpoint(self, base_url):
        """Test EMS Agent status endpoint with hybrid AI info"""
        response = requests.get(f"{base_url}/api/status")
        assert response.status_code == 200
        data = response.json()
        
        # Check hybrid AI capabilities
        assert "ai_capabilities" in data
        assert data["ai_capabilities"]["energy_specialist"] is True
        assert data["ai_capabilities"]["general_ai"] is True
        assert data["ai_capabilities"]["hybrid_routing"] is True
        
        # Check components
        assert "components" in data
        assert data["components"]["hybrid_router"] is True
        assert data["components"]["query_engine"] is True
        
        # Check mode
        assert data["mode"] == "hybrid_ai"
        assert data["status"] == "online"
    
    def test_hybrid_ai_energy_query(self, base_url):
        """Test hybrid AI routing for energy-related questions"""
        query_data = {"query": "What is the current power consumption?"}
        response = requests.post(
            f"{base_url}/api/query",
            json=query_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert data["success"] is True
        assert data["ai_type"] == "EMS_Specialist"
        assert data["routing_decision"] == "energy_related"
        assert "response" in data
        assert "processing_time" in data
        assert "timestamp" in data
        
        # Check that we got actual energy data
        assert "power" in data["response"].lower() or "energy" in data["response"].lower()
    
    def test_hybrid_ai_general_query(self, base_url):
        """Test hybrid AI routing for general questions"""
        query_data = {"query": "Tell me a joke"}
        response = requests.post(
            f"{base_url}/api/query",
            json=query_data,
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert data["success"] is True
        assert data["ai_type"] == "General_AI"
        assert data["routing_decision"] == "general_question"
        assert "response" in data
        assert "processing_time" in data
        
        # Check that we got a general AI response
        assert len(data["response"]) > 10  # Should be a substantive response
    
    def test_hybrid_ai_energy_analysis_query(self, base_url):
        """Test hybrid AI with complex energy analysis questions"""
        test_queries = [
            "Show me energy anomalies",
            "What is the voltage quality?",
            "Calculate energy costs",
            "Analyze power consumption trends"
        ]
        
        for query in test_queries:
            query_data = {"query": query}
            response = requests.post(
                f"{base_url}/api/query",
                json=query_data,
                headers={"Content-Type": "application/json"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["ai_type"] == "EMS_Specialist"
            assert data["routing_decision"] == "energy_related"
    
    def test_api_gateway_health(self, gateway_url):
        """Test API Gateway health check if available"""
        try:
            response = requests.get(f"{gateway_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                assert "gateway" in data
                assert data["gateway"] == "healthy"
        except requests.exceptions.RequestException:
            # Gateway might not be running, skip this test
            pytest.skip("API Gateway not available")
    
    def test_invalid_query_handling(self, base_url):
        """Test handling of invalid queries"""
        # Empty query
        response = requests.post(
            f"{base_url}/api/query",
            json={},
            headers={"Content-Type": "application/json"}
        )
        
        # Should handle gracefully (might return 400 or a fallback response)
        assert response.status_code in [200, 400]
        
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
        
    def test_data_summary_endpoint(self, base_url):
        """Test data summary endpoint"""
        response = requests.get(f"{base_url}/api/data_summary")
        assert response.status_code == 200
        data = response.json()
        
        # Should have database statistics
        assert "status" in data
        assert "collections" in data or "total_records" in data
    
    def test_response_time_performance(self, base_url):
        """Test that API responses are within acceptable time limits"""
        import time
        
        # Test energy query performance
        start_time = time.time()
        query_data = {"query": "What is the current energy status?"}
        response = requests.post(
            f"{base_url}/api/query",
            json=query_data,
            headers={"Content-Type": "application/json"}
        )
        end_time = time.time()
        
        assert response.status_code == 200
        response_time = end_time - start_time
        
        # Should respond within 5 seconds for energy queries
        assert response_time < 5.0
        
        # Check internal processing time from response
        data = response.json()
        if "processing_time" in data:
            # Internal processing should be under 2 seconds
            assert data["processing_time"] < 2.0
