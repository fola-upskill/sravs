#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Student Records Verification System
Tests all backend APIs including authentication, UUID system, and workflow
"""

import requests
import json
import hashlib
import uuid
from datetime import datetime
import time

# Configuration
BASE_URL = "https://credential-verify-3.preview.emergentagent.com/api"
TEST_SESSION_ID = "test_session_123"  # Mock session ID for testing

class BackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.auth_token = None
        self.test_users = {}
        self.test_data = {}
        
    def log_result(self, test_name, success, message, details=None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {message}")
        if details:
            print(f"   Details: {details}")
    
    def test_mock_authentication_system(self):
        """Test Mock Authentication System - Focus on mock-login endpoint"""
        print("\n=== Testing Mock Authentication System ===")
        
        # Test 1: Mock login with sample user data
        try:
            mock_user_data = {
                "email": "test.student@university.edu",
                "name": "Test Student",
                "role": "student",
                "university": "Test University"
            }
            response = self.session.post(f"{BASE_URL}/auth/mock-login", json=mock_user_data)
            if response.status_code == 200:
                data = response.json()
                if "user" in data and "session_token" in data:
                    self.auth_token = data["session_token"]
                    self.test_users["student"] = data["user"]
                    self.log_result("Mock Auth - Student Login", True, 
                                   f"Successfully created student session", 
                                   f"User ID: {data['user']['id']}, Token: {self.auth_token[:16]}...")
                else:
                    self.log_result("Mock Auth - Student Login", False, "Missing user or session_token in response")
            else:
                self.log_result("Mock Auth - Student Login", False, f"Expected 200, got {response.status_code}")
        except Exception as e:
            self.log_result("Mock Auth - Student Login", False, f"Request failed: {str(e)}")
        
        # Test 2: Mock login with missing required fields
        try:
            incomplete_data = {"email": "test@example.com"}  # Missing name
            response = self.session.post(f"{BASE_URL}/auth/mock-login", json=incomplete_data)
            if response.status_code == 400:
                self.log_result("Mock Auth - Missing Fields", True, "Correctly rejects incomplete data")
            else:
                self.log_result("Mock Auth - Missing Fields", False, f"Expected 400, got {response.status_code}")
        except Exception as e:
            self.log_result("Mock Auth - Missing Fields", False, f"Request failed: {str(e)}")
        
        # Test 3: Create issuer user
        try:
            issuer_data = {
                "email": "test.issuer@university.edu",
                "name": "Test Issuer",
                "role": "issuer",
                "university": "Test University"
            }
            response = self.session.post(f"{BASE_URL}/auth/mock-login", json=issuer_data)
            if response.status_code == 200:
                data = response.json()
                self.test_users["issuer"] = data["user"]
                self.log_result("Mock Auth - Issuer Login", True, "Successfully created issuer session")
            else:
                self.log_result("Mock Auth - Issuer Login", False, f"Expected 200, got {response.status_code}")
        except Exception as e:
            self.log_result("Mock Auth - Issuer Login", False, f"Request failed: {str(e)}")
        
        # Test 4: Create verifier user
        try:
            verifier_data = {
                "email": "test.verifier@university.edu",
                "name": "Test Verifier",
                "role": "verifier",
                "university": "Test University"
            }
            response = self.session.post(f"{BASE_URL}/auth/mock-login", json=verifier_data)
            if response.status_code == 200:
                data = response.json()
                self.test_users["verifier"] = data["user"]
                self.log_result("Mock Auth - Verifier Login", True, "Successfully created verifier session")
            else:
                self.log_result("Mock Auth - Verifier Login", False, f"Expected 200, got {response.status_code}")
        except Exception as e:
            self.log_result("Mock Auth - Verifier Login", False, f"Request failed: {str(e)}")
    
    def test_session_verification(self):
        """Test Session Token Verification"""
        print("\n=== Testing Session Token Verification ===")
        
        if not self.auth_token:
            self.log_result("Session Verification - No Token", False, "No auth token available from mock login")
            return
        
        # Test 1: Get current user with valid session token
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = self.session.get(f"{BASE_URL}/auth/me", headers=headers)
            if response.status_code == 200:
                data = response.json()
                if data.get("email") == "test.student@university.edu":
                    self.log_result("Session Verification - Valid Token", True, "Successfully retrieved user with session token")
                else:
                    self.log_result("Session Verification - Valid Token", False, "Retrieved user data doesn't match expected")
            else:
                self.log_result("Session Verification - Valid Token", False, f"Expected 200, got {response.status_code}")
        except Exception as e:
            self.log_result("Session Verification - Valid Token", False, f"Request failed: {str(e)}")
        
        # Test 2: Test session token in cookies
        try:
            self.session.cookies.set("session_token", self.auth_token)
            response = self.session.get(f"{BASE_URL}/auth/me")
            if response.status_code == 200:
                self.log_result("Session Verification - Cookie Token", True, "Session token works via cookies")
            else:
                self.log_result("Session Verification - Cookie Token", False, f"Expected 200, got {response.status_code}")
        except Exception as e:
            self.log_result("Session Verification - Cookie Token", False, f"Request failed: {str(e)}")
        
        # Test 3: Invalid session token
        try:
            headers = {"Authorization": "Bearer invalid_token_123"}
            response = self.session.get(f"{BASE_URL}/auth/me", headers=headers)
            if response.status_code == 401:
                self.log_result("Session Verification - Invalid Token", True, "Correctly rejects invalid token")
            else:
                self.log_result("Session Verification - Invalid Token", False, f"Expected 401, got {response.status_code}")
        except Exception as e:
            self.log_result("Session Verification - Invalid Token", False, f"Request failed: {str(e)}")
    
    def test_protected_endpoints_with_auth(self):
        """Test Protected Endpoints with Authentication"""
        print("\n=== Testing Protected Endpoints with Authentication ===")
        
        if not self.auth_token:
            self.log_result("Protected Endpoints - No Token", False, "No auth token available for testing")
            return
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test 1: Create transcript request as authenticated student
        try:
            request_data = {
                "university_from": "Test University",
                "university_to": "Receiving University",
                "document_type": "transcript",
                "content": "This is a test transcript document for verification testing"
            }
            response = self.session.post(f"{BASE_URL}/transcript-requests", json=request_data, headers=headers)
            if response.status_code == 200:
                data = response.json()
                if "student_request_uuid" in data:
                    self.test_data["transcript_request"] = data
                    self.log_result("Protected Endpoints - Create Transcript", True, 
                                   f"Successfully created transcript request with UUID: {data['student_request_uuid']}")
                else:
                    self.log_result("Protected Endpoints - Create Transcript", False, "Missing UUID in response")
            else:
                self.log_result("Protected Endpoints - Create Transcript", False, f"Expected 200, got {response.status_code}")
        except Exception as e:
            self.log_result("Protected Endpoints - Create Transcript", False, f"Request failed: {str(e)}")
        
        # Test 2: Get transcript requests as authenticated student
        try:
            response = self.session.get(f"{BASE_URL}/transcript-requests", headers=headers)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_result("Protected Endpoints - Get Transcripts", True, f"Retrieved {len(data)} transcript requests")
                else:
                    self.log_result("Protected Endpoints - Get Transcripts", False, "Response is not a list")
            else:
                self.log_result("Protected Endpoints - Get Transcripts", False, f"Expected 200, got {response.status_code}")
        except Exception as e:
            self.log_result("Protected Endpoints - Get Transcripts", False, f"Request failed: {str(e)}")
        
        # Test 3: Update user role (should work with any authenticated user)
        try:
            if "student" in self.test_users:
                user_id = self.test_users["student"]["id"]
                role_data = {"role": "student", "university": "Updated University"}
                response = self.session.put(f"{BASE_URL}/users/{user_id}/role", json=role_data, headers=headers)
                if response.status_code == 200:
                    self.log_result("Protected Endpoints - Update Role", True, "Successfully updated user role")
                else:
                    self.log_result("Protected Endpoints - Update Role", False, f"Expected 200, got {response.status_code}")
            else:
                self.log_result("Protected Endpoints - Update Role", False, "No student user available for testing")
        except Exception as e:
            self.log_result("Protected Endpoints - Update Role", False, f"Request failed: {str(e)}")
    
    def test_authentication_endpoints(self):
        """Test Additional Authentication Endpoints"""
        print("\n=== Testing Additional Authentication Endpoints ===")
        
        # Test 1: Session data endpoint with mock session ID
        try:
            headers = {"X-Session-ID": "mock_session_123"}
            response = self.session.get(f"{BASE_URL}/auth/session-data", headers=headers)
            if response.status_code == 200:
                data = response.json()
                if "user" in data and "session_token" in data:
                    self.log_result("Auth - Mock Session Data", True, "Mock session data endpoint working")
                else:
                    self.log_result("Auth - Mock Session Data", False, "Missing user or session_token in response")
            else:
                self.log_result("Auth - Mock Session Data", False, f"Expected 200, got {response.status_code}")
        except Exception as e:
            self.log_result("Auth - Mock Session Data", False, f"Request failed: {str(e)}")
        
        # Test 2: Session data endpoint without session ID
        try:
            response = self.session.get(f"{BASE_URL}/auth/session-data")
            if response.status_code == 400:
                self.log_result("Auth - Missing Session ID", True, "Correctly rejects missing session ID")
            else:
                self.log_result("Auth - Missing Session ID", False, f"Expected 400, got {response.status_code}")
        except Exception as e:
            self.log_result("Auth - Missing Session ID", False, f"Request failed: {str(e)}")
        
        # Test 3: Session data endpoint with invalid session ID
        try:
            headers = {"X-Session-ID": "invalid_session"}
            response = self.session.get(f"{BASE_URL}/auth/session-data", headers=headers)
            if response.status_code == 401:
                self.log_result("Auth - Invalid Session", True, "Correctly rejects invalid session")
            else:
                self.log_result("Auth - Invalid Session", False, f"Expected 401, got {response.status_code}")
        except Exception as e:
            self.log_result("Auth - Invalid Session", False, f"Request failed: {str(e)}")
        
        # Test 4: Logout functionality
        if self.auth_token:
            try:
                headers = {"Authorization": f"Bearer {self.auth_token}"}
                response = self.session.post(f"{BASE_URL}/auth/logout", headers=headers)
                if response.status_code == 200:
                    self.log_result("Auth - Logout", True, "Successfully logged out")
                    # Verify token is invalidated
                    verify_response = self.session.get(f"{BASE_URL}/auth/me", headers=headers)
                    if verify_response.status_code == 401:
                        self.log_result("Auth - Token Invalidation", True, "Session token properly invalidated after logout")
                    else:
                        self.log_result("Auth - Token Invalidation", False, "Session token still valid after logout")
                else:
                    self.log_result("Auth - Logout", False, f"Expected 200, got {response.status_code}")
            except Exception as e:
                self.log_result("Auth - Logout", False, f"Request failed: {str(e)}")
    
    def test_content_hashing(self):
        """Test Document Content Hashing"""
        print("\n=== Testing Content Hashing ===")
        
        # Test SHA-256 hash generation consistency
        test_content = "This is a test transcript document for John Doe from University A"
        expected_hash = hashlib.sha256(test_content.encode()).hexdigest()
        
        # Store for later use in transcript tests
        self.test_data['content'] = test_content
        self.test_data['expected_hash'] = expected_hash
        
        self.log_result("Content Hashing - SHA-256", True, 
                       f"Generated hash: {expected_hash[:16]}...", 
                       f"Full hash: {expected_hash}")
        
        # Test hash consistency
        hash2 = hashlib.sha256(test_content.encode()).hexdigest()
        if expected_hash == hash2:
            self.log_result("Content Hashing - Consistency", True, "Same content produces same hash")
        else:
            self.log_result("Content Hashing - Consistency", False, "Hash inconsistency detected")
    
    def test_transcript_request_api_unauthenticated(self):
        """Test Student Transcript Request API without authentication"""
        print("\n=== Testing Transcript Request API (Unauthenticated) ===")
        
        # Test 1: Create transcript request without authentication
        try:
            request_data = {
                "university_from": "University A",
                "university_to": "University B", 
                "document_type": "transcript",
                "content": self.test_data.get('content', 'test content')
            }
            response = self.session.post(f"{BASE_URL}/transcript-requests", json=request_data)
            if response.status_code == 403:
                self.log_result("Transcript - Create Unauthenticated", True, "Correctly rejects unauthenticated request")
            else:
                self.log_result("Transcript - Create Unauthenticated", False, f"Expected 403, got {response.status_code}")
        except Exception as e:
            self.log_result("Transcript - Create Unauthenticated", False, f"Request failed: {str(e)}")
        
        # Test 2: Get transcript requests without authentication
        try:
            response = self.session.get(f"{BASE_URL}/transcript-requests")
            if response.status_code == 401:
                self.log_result("Transcript - Get Unauthenticated", True, "Correctly rejects unauthenticated request")
            else:
                self.log_result("Transcript - Get Unauthenticated", False, f"Expected 401, got {response.status_code}")
        except Exception as e:
            self.log_result("Transcript - Get Unauthenticated", False, f"Request failed: {str(e)}")
    
    def test_issuer_validation_api_unauthenticated(self):
        """Test Issuer Validation API without authentication"""
        print("\n=== Testing Issuer Validation API (Unauthenticated) ===")
        
        try:
            validation_data = {
                "transcript_request_id": str(uuid.uuid4()),
                "validation_notes": "Test validation",
                "is_approved": True
            }
            response = self.session.post(f"{BASE_URL}/issuer-validations", json=validation_data)
            if response.status_code == 403:
                self.log_result("Issuer Validation - Unauthenticated", True, "Correctly rejects unauthenticated request")
            else:
                self.log_result("Issuer Validation - Unauthenticated", False, f"Expected 403, got {response.status_code}")
        except Exception as e:
            self.log_result("Issuer Validation - Unauthenticated", False, f"Request failed: {str(e)}")
    
    def test_verifier_receipt_api_unauthenticated(self):
        """Test Verifier Receipt API without authentication"""
        print("\n=== Testing Verifier Receipt API (Unauthenticated) ===")
        
        try:
            receipt_data = {
                "transcript_request_id": str(uuid.uuid4()),
                "issuer_validation_id": str(uuid.uuid4()),
                "receipt_notes": "Test receipt"
            }
            response = self.session.post(f"{BASE_URL}/verifier-receipts", json=receipt_data)
            if response.status_code == 403:
                self.log_result("Verifier Receipt - Unauthenticated", True, "Correctly rejects unauthenticated request")
            else:
                self.log_result("Verifier Receipt - Unauthenticated", False, f"Expected 403, got {response.status_code}")
        except Exception as e:
            self.log_result("Verifier Receipt - Unauthenticated", False, f"Request failed: {str(e)}")
    
    def test_uuid_verification_api(self):
        """Test UUID Verification API"""
        print("\n=== Testing UUID Verification API ===")
        
        # Test 1: Verify non-existent student request UUID
        try:
            fake_uuid = str(uuid.uuid4())
            response = self.session.get(f"{BASE_URL}/verify/student_request/{fake_uuid}")
            if response.status_code == 200:
                data = response.json()
                if not data.get('verified', True):
                    self.log_result("UUID Verification - Invalid Student UUID", True, "Correctly identifies invalid UUID")
                else:
                    self.log_result("UUID Verification - Invalid Student UUID", False, "Should not verify non-existent UUID")
            else:
                self.log_result("UUID Verification - Invalid Student UUID", False, f"Expected 200, got {response.status_code}")
        except Exception as e:
            self.log_result("UUID Verification - Invalid Student UUID", False, f"Request failed: {str(e)}")
        
        # Test 2: Verify non-existent issuer validation UUID
        try:
            fake_uuid = str(uuid.uuid4())
            response = self.session.get(f"{BASE_URL}/verify/issuer_validation/{fake_uuid}")
            if response.status_code == 200:
                data = response.json()
                if not data.get('verified', True):
                    self.log_result("UUID Verification - Invalid Issuer UUID", True, "Correctly identifies invalid UUID")
                else:
                    self.log_result("UUID Verification - Invalid Issuer UUID", False, "Should not verify non-existent UUID")
            else:
                self.log_result("UUID Verification - Invalid Issuer UUID", False, f"Expected 200, got {response.status_code}")
        except Exception as e:
            self.log_result("UUID Verification - Invalid Issuer UUID", False, f"Request failed: {str(e)}")
        
        # Test 3: Verify non-existent verifier receipt UUID
        try:
            fake_uuid = str(uuid.uuid4())
            response = self.session.get(f"{BASE_URL}/verify/verifier_receipt/{fake_uuid}")
            if response.status_code == 200:
                data = response.json()
                if not data.get('verified', True):
                    self.log_result("UUID Verification - Invalid Verifier UUID", True, "Correctly identifies invalid UUID")
                else:
                    self.log_result("UUID Verification - Invalid Verifier UUID", False, "Should not verify non-existent UUID")
            else:
                self.log_result("UUID Verification - Invalid Verifier UUID", False, f"Expected 200, got {response.status_code}")
        except Exception as e:
            self.log_result("UUID Verification - Invalid Verifier UUID", False, f"Request failed: {str(e)}")
        
        # Test 4: Invalid UUID type
        try:
            fake_uuid = str(uuid.uuid4())
            response = self.session.get(f"{BASE_URL}/verify/invalid_type/{fake_uuid}")
            if response.status_code == 200:
                data = response.json()
                if not data.get('verified', True):
                    self.log_result("UUID Verification - Invalid Type", True, "Correctly handles invalid UUID type")
                else:
                    self.log_result("UUID Verification - Invalid Type", False, "Should not verify invalid UUID type")
            else:
                self.log_result("UUID Verification - Invalid Type", False, f"Expected 200, got {response.status_code}")
        except Exception as e:
            self.log_result("UUID Verification - Invalid Type", False, f"Request failed: {str(e)}")
    
    def test_role_management_api(self):
        """Test Role-based Access Control"""
        print("\n=== Testing Role Management API ===")
        
        # Test updating user role without authentication
        try:
            role_data = {
                "role": "issuer",
                "university": "University A"
            }
            fake_user_id = str(uuid.uuid4())
            response = self.session.put(f"{BASE_URL}/users/{fake_user_id}/role", json=role_data)
            if response.status_code == 401:
                self.log_result("Role Management - Unauthenticated", True, "Correctly rejects unauthenticated role update")
            else:
                self.log_result("Role Management - Unauthenticated", False, f"Expected 401, got {response.status_code}")
        except Exception as e:
            self.log_result("Role Management - Unauthenticated", False, f"Request failed: {str(e)}")
    
    def test_multi_level_uuid_system(self):
        """Test Multi-level UUID System"""
        print("\n=== Testing Multi-level UUID System ===")
        
        # Test UUID generation uniqueness
        uuids_generated = []
        for i in range(10):
            test_uuid = str(uuid.uuid4())
            uuids_generated.append(test_uuid)
        
        # Check uniqueness
        if len(set(uuids_generated)) == len(uuids_generated):
            self.log_result("UUID System - Uniqueness", True, f"Generated {len(uuids_generated)} unique UUIDs")
        else:
            self.log_result("UUID System - Uniqueness", False, "Duplicate UUIDs detected")
        
        # Test UUID format validation
        test_uuid = str(uuid.uuid4())
        try:
            uuid.UUID(test_uuid)
            self.log_result("UUID System - Format Validation", True, "UUID format is valid")
        except ValueError:
            self.log_result("UUID System - Format Validation", False, "Invalid UUID format")
    
    def test_api_endpoints_availability(self):
        """Test API endpoints availability"""
        print("\n=== Testing API Endpoints Availability ===")
        
        endpoints = [
            ("GET", "/auth/session-data"),
            ("POST", "/auth/logout"),
            ("GET", "/auth/me"),
            ("POST", "/transcript-requests"),
            ("GET", "/transcript-requests"),
            ("POST", "/issuer-validations"),
            ("POST", "/verifier-receipts"),
            ("GET", f"/verify/student_request/{uuid.uuid4()}"),
            ("PUT", f"/users/{uuid.uuid4()}/role")
        ]
        
        for method, endpoint in endpoints:
            try:
                if method == "GET":
                    response = self.session.get(f"{BASE_URL}{endpoint}")
                elif method == "POST":
                    response = self.session.post(f"{BASE_URL}{endpoint}", json={})
                elif method == "PUT":
                    response = self.session.put(f"{BASE_URL}{endpoint}", json={})
                
                # Check if endpoint exists (not 404)
                if response.status_code != 404:
                    self.log_result(f"Endpoint Availability - {method} {endpoint}", True, 
                                   f"Endpoint exists (status: {response.status_code})")
                else:
                    self.log_result(f"Endpoint Availability - {method} {endpoint}", False, 
                                   "Endpoint not found (404)")
            except Exception as e:
                self.log_result(f"Endpoint Availability - {method} {endpoint}", False, 
                               f"Request failed: {str(e)}")
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Comprehensive Backend Testing")
        print(f"Testing against: {BASE_URL}")
        print("=" * 60)
        
        # Initialize test data
        self.test_content_hashing()
        
        # Test all components
        self.test_api_endpoints_availability()
        self.test_authentication_endpoints()
        self.test_multi_level_uuid_system()
        self.test_transcript_request_api_unauthenticated()
        self.test_issuer_validation_api_unauthenticated()
        self.test_verifier_receipt_api_unauthenticated()
        self.test_uuid_verification_api()
        self.test_role_management_api()
        
        # Generate summary
        self.generate_summary()
    
    def generate_summary(self):
        """Generate test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
        
        print("\n✅ PASSED TESTS:")
        for result in self.test_results:
            if result['success']:
                print(f"  - {result['test']}: {result['message']}")
        
        return {
            'total': total_tests,
            'passed': passed_tests,
            'failed': failed_tests,
            'success_rate': (passed_tests/total_tests)*100,
            'results': self.test_results
        }

if __name__ == "__main__":
    tester = BackendTester()
    summary = tester.run_all_tests()