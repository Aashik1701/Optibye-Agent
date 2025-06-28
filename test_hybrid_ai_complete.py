"""
Comprehensive test suite for the Hybrid AI Chatbot functionality
Tests both EMS Specialist and General AI routing
"""

import requests
import time
import json
from typing import Dict, Any, List

# Configuration
EMS_AGENT_URL = "http://localhost:5004"
API_GATEWAY_URL = "http://localhost:8000"

class HybridAITester:
    """Test class for Hybrid AI functionality"""
    
    def __init__(self):
        self.ems_url = EMS_AGENT_URL
        self.gateway_url = API_GATEWAY_URL
        self.test_results = []
    
    def test_query(self, query: str, expected_ai_type: str, test_name: str) -> Dict[str, Any]:
        """Test a single query and validate the response"""
        print(f"\n🧪 Testing: {test_name}")
        print(f"📝 Query: '{query}'")
        print(f"🎯 Expected AI: {expected_ai_type}")
        
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{self.ems_url}/api/query",
                json={"query": query},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            if response.status_code == 200:
                data = response.json()
                actual_ai_type = data.get("ai_type", "Unknown")
                routing_decision = data.get("routing_decision", "Unknown")
                processing_time = data.get("processing_time", 0)
                
                # Validate routing
                routing_correct = actual_ai_type == expected_ai_type
                
                result = {
                    "test_name": test_name,
                    "query": query,
                    "expected_ai": expected_ai_type,
                    "actual_ai": actual_ai_type,
                    "routing_correct": routing_correct,
                    "routing_decision": routing_decision,
                    "response_time": response_time,
                    "processing_time": processing_time,
                    "success": data.get("success", False),
                    "response_length": len(data.get("response", "")),
                    "status": "PASS" if routing_correct and data.get("success", False) else "FAIL"
                }
                
                # Print results
                status_emoji = "✅" if result["status"] == "PASS" else "❌"
                print(f"{status_emoji} {result['status']}")
                print(f"🤖 Actual AI: {actual_ai_type}")
                print(f"⚡ Response Time: {response_time:.3f}s")
                print(f"🔧 Processing Time: {processing_time:.3f}s")
                print(f"📊 Response Length: {result['response_length']} chars")
                
                if not routing_correct:
                    print(f"⚠️  ROUTING ERROR: Expected {expected_ai_type}, got {actual_ai_type}")
                
            else:
                result = {
                    "test_name": test_name,
                    "query": query,
                    "status": "FAIL",
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                print(f"❌ FAIL - HTTP {response.status_code}")
                
        except Exception as e:
            result = {
                "test_name": test_name,
                "query": query,
                "status": "ERROR",
                "error": str(e)
            }
            print(f"💥 ERROR: {e}")
        
        self.test_results.append(result)
        return result
    
    def run_comprehensive_tests(self):
        """Run comprehensive test suite"""
        print("🚀 Starting Comprehensive Hybrid AI Tests")
        print("=" * 60)
        
        # Test EMS Specialist routing
        print("\n🔋 TESTING EMS SPECIALIST ROUTING")
        print("-" * 40)
        
        ems_tests = [
            ("What is the current power consumption?", "EMS_Specialist", "Power Consumption Query"),
            ("Show me energy anomalies", "EMS_Specialist", "Anomaly Detection"),
            ("What is the voltage quality?", "EMS_Specialist", "Voltage Analysis"),
            ("Calculate energy costs", "EMS_Specialist", "Cost Calculation"),
            ("Analyze power trends", "EMS_Specialist", "Trend Analysis"),
            ("Check system status", "EMS_Specialist", "System Status"),
            ("What is the current consumption?", "EMS_Specialist", "Current Analysis"),
            ("Show me the power factor", "EMS_Specialist", "Power Factor Query"),
            ("Energy usage optimization", "EMS_Specialist", "Energy Optimization"),
            ("System health check", "EMS_Specialist", "Health Check")
        ]
        
        for query, expected_ai, test_name in ems_tests:
            self.test_query(query, expected_ai, test_name)
        
        # Test General AI routing
        print("\n🧠 TESTING GENERAL AI ROUTING")
        print("-" * 40)
        
        general_tests = [
            ("Tell me a joke", "General_AI", "Joke Request"),
            ("What is artificial intelligence?", "General_AI", "AI Explanation"),
            ("How do I cook pasta?", "General_AI", "Cooking Instructions"),
            ("What's the weather like?", "General_AI", "Weather Query"),
            ("Explain machine learning", "General_AI", "ML Explanation"),
            ("Tell me a story", "General_AI", "Story Request"),
            ("What is Python programming?", "General_AI", "Programming Query"),
            ("How to learn data science?", "General_AI", "Learning Guidance"),
            ("What are the latest news?", "General_AI", "News Query"),
            ("Recommend a good book", "General_AI", "Book Recommendation")
        ]
        
        for query, expected_ai, test_name in general_tests:
            self.test_query(query, expected_ai, test_name)
        
        # Test ambiguous queries (should default to EMS)
        print("\n❓ TESTING AMBIGUOUS QUERIES")
        print("-" * 40)
        
        ambiguous_tests = [
            ("Hello", "EMS_Specialist", "Greeting"),
            ("Help me", "EMS_Specialist", "Help Request"),
            ("Status", "EMS_Specialist", "Simple Status"),
            ("What can you do?", "EMS_Specialist", "Capability Query"),
            ("How are you?", "EMS_Specialist", "Casual Greeting")
        ]
        
        for query, expected_ai, test_name in ambiguous_tests:
            self.test_query(query, expected_ai, test_name)
    
    def test_system_health(self):
        """Test system health and availability"""
        print("\n🏥 TESTING SYSTEM HEALTH")
        print("-" * 40)
        
        # Test EMS Agent status
        try:
            response = requests.get(f"{self.ems_url}/api/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print("✅ EMS Agent: HEALTHY")
                print(f"   Mode: {data.get('mode', 'unknown')}")
                print(f"   AI Capabilities: {data.get('ai_capabilities', {})}")
                print(f"   Database: {data.get('database_stats', {}).get('status', 'unknown')}")
            else:
                print(f"❌ EMS Agent: UNHEALTHY (HTTP {response.status_code})")
        except Exception as e:
            print(f"💥 EMS Agent: ERROR - {e}")
        
        # Test API Gateway if available
        try:
            response = requests.get(f"{self.gateway_url}/health", timeout=3)
            if response.status_code == 200:
                data = response.json()
                print("✅ API Gateway: HEALTHY")
                print(f"   Status: {data.get('overall_status', 'unknown')}")
            else:
                print(f"⚠️  API Gateway: DEGRADED (HTTP {response.status_code})")
        except Exception as e:
            print(f"⚠️  API Gateway: NOT AVAILABLE - {e}")
    
    def generate_report(self):
        """Generate test report"""
        print("\n📊 TEST REPORT")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r.get("status") == "PASS"])
        failed_tests = len([r for r in self.test_results if r.get("status") == "FAIL"])
        error_tests = len([r for r in self.test_results if r.get("status") == "ERROR"])
        
        print(f"📈 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"💥 Errors: {error_tests}")
        print(f"📊 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Performance statistics
        response_times = [r.get("response_time", 0) for r in self.test_results if r.get("response_time")]
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            print(f"⚡ Avg Response Time: {avg_response_time:.3f}s")
            print(f"⚡ Max Response Time: {max_response_time:.3f}s")
        
        # Routing accuracy
        routing_tests = [r for r in self.test_results if "routing_correct" in r]
        if routing_tests:
            correct_routing = len([r for r in routing_tests if r.get("routing_correct", False)])
            routing_accuracy = (correct_routing / len(routing_tests)) * 100
            print(f"🎯 Routing Accuracy: {routing_accuracy:.1f}%")
        
        # Show failed tests
        failed_tests_list = [r for r in self.test_results if r.get("status") != "PASS"]
        if failed_tests_list:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests_list:
                print(f"   • {test.get('test_name', 'Unknown')}: {test.get('error', 'Unknown error')}")
        
        print("\n🎉 Testing Complete!")
        return {
            "total": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "errors": error_tests,
            "success_rate": (passed_tests/total_tests)*100 if total_tests > 0 else 0,
            "avg_response_time": sum(response_times) / len(response_times) if response_times else 0
        }

def main():
    """Main test execution"""
    print("🤖 EMS Agent Hybrid AI Chatbot Test Suite")
    print("=" * 60)
    
    tester = HybridAITester()
    
    # Test system health first
    tester.test_system_health()
    
    # Run comprehensive tests
    tester.run_comprehensive_tests()
    
    # Generate report
    report = tester.generate_report()
    
    # Save results to file
    with open("hybrid_ai_test_results.json", "w") as f:
        json.dump({
            "summary": report,
            "detailed_results": tester.test_results,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }, f, indent=2)
    
    print(f"\n💾 Results saved to: hybrid_ai_test_results.json")
    
    return report["success_rate"] >= 90  # Return True if 90%+ tests pass

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
