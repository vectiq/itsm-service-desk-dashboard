#!/usr/bin/env python3
"""
Test script to debug AI incident generation issues
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.data_ingest import data_ingest_manager
from utils.bedrock_client import bedrock_client
from utils.settings_manager import settings_manager

def test_ai_generation():
    print("🔍 Testing AI Incident Generation")
    print("=" * 50)
    
    # Test 1: Check Bedrock availability
    print("\n1. Testing Bedrock Client...")
    if bedrock_client.is_available():
        print("✅ Bedrock client is available")
        models = bedrock_client.get_available_models()
        print(f"   Available models: {len(models)}")
    else:
        print("❌ Bedrock client is NOT available")
        return False
    
    # Test 2: Check settings
    print("\n2. Testing Settings Manager...")
    if settings_manager.is_available():
        print("✅ Settings manager is available")
        ai_settings = settings_manager.get_ai_model_settings()
        print(f"   Model ID: {ai_settings.get('selected_model_id')}")
        print(f"   Model Name: {ai_settings.get('selected_model_name')}")
        print(f"   Max Tokens: {ai_settings.get('max_tokens')}")
        print(f"   Temperature: {ai_settings.get('temperature')}")
    else:
        print("❌ Settings manager is NOT available")
        return False
    
    # Test 3: Test small AI generation
    print("\n3. Testing Small AI Generation (2 incidents)...")
    try:
        success = data_ingest_manager.generate_ai_incidents(2, 0.5)
        if success:
            print("✅ AI generation succeeded!")
            
            # Check what was generated
            incidents = data_ingest_manager.get_incidents(limit=5)
            print(f"   Total incidents in DB: {len(incidents)}")
            
            if incidents:
                incident = incidents[0]
                print(f"   Sample incident ID: {incident.get('incident_id')}")
                print(f"   Sample title: {incident.get('title')}")
                print(f"   Sample status: {incident.get('status')}")
                print(f"   Sample priority: {incident.get('priority')}")
                print(f"   Sample category: {incident.get('category_id')}")
        else:
            print("❌ AI generation failed!")
            return False
            
    except Exception as e:
        print(f"❌ AI generation error: {str(e)}")
        import traceback
        print("Full traceback:")
        print(traceback.format_exc())
        return False
    
    print("\n🎉 All tests passed!")
    return True

if __name__ == "__main__":
    test_ai_generation()
