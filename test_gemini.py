#!/usr/bin/env python3
"""
Quick test of Gemini integration
"""

import asyncio
import sys
import os

# Add current directory to path to import from ems_chatbot
sys.path.append('.')

from ems_chatbot import GeminiAI

async def test_gemini():
    """Test Gemini AI integration"""
    print("🧪 Testing Gemini AI Integration")
    print("=" * 40)
    
    # Check if API key is set
    api_key = os.getenv('GEMINI_API_KEY', 'AIzaSyAqib60Hqzz36ygA5cv4QRl8y6CKO9spLs')
    if not api_key or api_key == 'your-gemini-api-key-here':
        print("⚠️  Warning: Using default API key. Set GEMINI_API_KEY environment variable for production.")
    else:
        print("✅ API key configured")
    
    gemini = GeminiAI()
    
    # Test questions
    test_questions = [
        "What is artificial intelligence?",
        "Explain machine learning in simple terms",
        "Tell me a short joke"
    ]
    
    for question in test_questions:
        print(f"\n🔍 Question: {question}")
        try:
            response = await gemini.get_gemini_response(question)
            print(f"🤖 Response: {response[:200]}...")
            print("✅ Success!")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n🎉 Gemini integration test complete!")

if __name__ == "__main__":
    asyncio.run(test_gemini())
