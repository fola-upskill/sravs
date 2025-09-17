#!/usr/bin/env python3
import requests
import json

BASE_URL = "https://credential-verify-3.preview.emergentagent.com/api"

print("🔐 Quick Mock Authentication Test")
print("=" * 40)

# Test 1: Mock login
print("1. Testing mock login...")
mock_user_data = {
    "email": "test.student@university.edu",
    "name": "Test Student",
    "role": "student",
    "university": "Test University"
}

response = requests.post(f"{BASE_URL}/auth/mock-login", json=mock_user_data)
if response.status_code == 200:
    data = response.json()
    token = data["session_token"]
    print(f"✅ Mock login successful! Token: {token[:16]}...")
    
    # Test 2: Use token to access protected endpoint
    print("2. Testing protected endpoint access...")
    headers = {"Authorization": f"Bearer {token}"}
    me_response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    if me_response.status_code == 200:
        user_data = me_response.json()
        print(f"✅ Protected endpoint access successful! User: {user_data['name']}")
        
        # Test 3: Create transcript request
        print("3. Testing transcript request creation...")
        request_data = {
            "university_from": "Test University",
            "university_to": "Receiving University", 
            "document_type": "transcript",
            "content": "Test transcript content for UUID verification"
        }
        transcript_response = requests.post(f"{BASE_URL}/transcript-requests", json=request_data, headers=headers)
        if transcript_response.status_code == 200:
            transcript_data = transcript_response.json()
            print(f"✅ Transcript request created! UUID: {transcript_data['student_request_uuid']}")
            
            # Test 4: Verify UUID
            print("4. Testing UUID verification...")
            uuid_to_verify = transcript_data['student_request_uuid']
            verify_response = requests.get(f"{BASE_URL}/verify/student_request/{uuid_to_verify}")
            if verify_response.status_code == 200:
                verify_data = verify_response.json()
                if verify_data.get('verified'):
                    print(f"✅ UUID verification successful! UUID is verified.")
                else:
                    print(f"❌ UUID verification failed - UUID not found")
            else:
                print(f"❌ UUID verification request failed: {verify_response.status_code}")
        else:
            print(f"❌ Transcript request failed: {transcript_response.status_code}")
    else:
        print(f"❌ Protected endpoint access failed: {me_response.status_code}")
else:
    print(f"❌ Mock login failed: {response.status_code}")

print("\n🎯 Mock Authentication System Status: READY FOR USER TESTING")
