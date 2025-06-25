#!/usr/bin/env python3
"""
Test script for Hybrid EMS Chatbot
Tests both energy-specific questions and general AI questions
"""

import asyncio
import json
import websockets
import time

async def test_hybrid_chatbot():
    """Test the hybrid chatbot functionality"""
    
    # Test questions - mix of energy and general
    test_questions = [
        # Energy questions (should go to EMS specialist)
        "What is the current power consumption?",
        "Show me any anomalies in the system",
        "What are the energy costs today?",
        "Analyze voltage quality",
        "Generate a comprehensive energy report",
        
        # General questions (should go to Gemini AI)
        "What is artificial intelligence?",
        "Explain how machine learning works",
        "What's the weather like?",
        "Tell me a joke",
        "How do I cook pasta?",
        
        # Borderline questions (test routing logic)
        "How can I optimize my system?",
        "What is energy efficiency?",
        "Hello, how are you?"
    ]
    
    print("🤖 Testing Hybrid EMS Chatbot")
    print("=" * 50)
    
    try:
        async with websockets.connect("ws://localhost:8091/ws") as websocket:
            print("✅ Connected to chatbot")
            
            # Receive welcome message
            welcome = await websocket.recv()
            welcome_data = json.loads(welcome)
            print(f"Welcome: {welcome_data.get('ai_type', 'Unknown')} - {welcome_data['message'][:100]}...")
            print()
            
            # Test each question
            for i, question in enumerate(test_questions, 1):
                print(f"🔍 Test {i}: {question}")
                
                # Send question
                await websocket.send(json.dumps({"message": question}))
                
                # Receive response
                response = await websocket.recv()
                response_data = json.loads(response)
                
                ai_type = response_data.get('ai_type', 'Unknown')
                processing_time = response_data.get('processing_time', 0)
                routing_decision = response_data.get('intent', 'unknown')
                
                # Determine if routing was correct
                is_energy_question = any(keyword in question.lower() for keyword in 
                    ['power', 'energy', 'voltage', 'current', 'consumption', 'anomal', 'cost', 'system', 'optimize'])
                
                expected_ai = "EMS" if is_energy_question else "General"
                actual_ai = "EMS" if "EMS" in ai_type else "General" if "General" in ai_type else "Unknown"
                
                routing_correct = "✅" if expected_ai == actual_ai else "⚠️"
                
                print(f"   {routing_correct} AI: {ai_type}")
                print(f"   ⏱️  Time: {processing_time:.2f}s")
                print(f"   💬 Response: {response_data['message'][:150]}...")
                print()
                
                # Small delay between questions
                await asyncio.sleep(1)
                
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure the chatbot is running on localhost:8091")

if __name__ == "__main__":
    print("🚀 Starting Hybrid Chatbot Test")
    print("Make sure to:")
    print("1. Set GEMINI_API_KEY in your environment")
    print("2. Start the chatbot: python ems_chatbot.py")
    print("3. Wait for it to be available on localhost:8091")
    print()
    
    asyncio.run(test_hybrid_chatbot())
