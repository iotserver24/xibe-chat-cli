#!/usr/bin/env python3
"""
Test script for XIBE-CHAT Analytics Server
"""

import requests
import json
import time

def test_analytics_server(base_url="http://localhost:5000"):
    """Test the analytics server endpoints."""
    
    print(f"🧪 Testing Analytics Server at {base_url}")
    print("=" * 50)
    
    # Test 1: Check if server is running
    try:
        response = requests.get(f"{base_url}/api/stats", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running!")
            stats = response.json()
            print(f"📊 Current stats: {json.dumps(stats, indent=2)}")
        else:
            print(f"❌ Server responded with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Server is not responding: {e}")
        return False
    
    # Test 2: Send test analytics data
    test_data = {
        "machine_id": "test-machine-123",
        "version": "1.6.0",
        "platform": "Windows",
        "python_version": "3.11.0",
        "event_type": "test_event",
        "event_data": {"test": "data"}
    }
    
    try:
        response = requests.post(
            f"{base_url}/track",
            json=test_data,
            timeout=5
        )
        if response.status_code == 200:
            print("✅ Analytics tracking works!")
            result = response.json()
            print(f"📡 Response: {json.dumps(result, indent=2)}")
        else:
            print(f"❌ Analytics tracking failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Analytics tracking failed: {e}")
        return False
    
    # Test 3: Check updated stats
    time.sleep(1)  # Wait a moment for data to be processed
    try:
        response = requests.get(f"{base_url}/api/stats", timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print("✅ Updated stats retrieved!")
            print(f"📊 Updated stats: {json.dumps(stats, indent=2)}")
        else:
            print(f"❌ Failed to get updated stats: {response.status_code}")
    except Exception as e:
        print(f"❌ Failed to get updated stats: {e}")
    
    # Test 4: Check dashboard
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print("✅ Dashboard is accessible!")
            if "XIBE-CHAT Analytics Dashboard" in response.text:
                print("✅ Dashboard content looks correct!")
            else:
                print("⚠️ Dashboard content might be incorrect")
        else:
            print(f"❌ Dashboard failed with status {response.status_code}")
    except Exception as e:
        print(f"❌ Dashboard test failed: {e}")
    
    print("\n🎉 Analytics server test completed!")
    return True

if __name__ == "__main__":
    import sys
    
    # Allow custom URL via command line
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
    
    success = test_analytics_server(url)
    exit(0 if success else 1)
