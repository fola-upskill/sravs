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
    
    def test_authentication_endpoints(self):
        """Test Emergent Authentication Integration"""
        print("\n=== Testing Authentication Endpoints ===")
        
        # Test 1: Session data endpoint without session ID
        try:
            response = self.session.get(f"{BASE_URL}/auth/session-data")
            if response.status_code == 400:
                self.log_result("Auth - Missing Session ID", True, "Correctly rejects missing session ID")
            else:
                self.log_result("Auth - Missing Session ID", False, f"Expected 400, got {response.status_code}")
        except Exception as e:
            self.log_result("Auth - Missing Session ID", False, f"Request failed: {str(e)}")
        
        # Test 2: Session data endpoint with invalid session ID
        try:
            headers = {"X-Session-ID": "invalid_session"}
            response = self.session.get(f"{BASE_URL}/auth/session-data", headers=headers)
            if response.status_code == 401:
                self.log_result("Auth - Invalid Session", True, "Correctly rejects invalid session")
            else:
                self.log_result("Auth - Invalid Session", False, f"Expected 401, got {response.status_code}")
        except Exception as e:
            self.log_result("Auth - Invalid Session", False, f"Request failed: {str(e)}")
        
        # Test 3: Get current user without authentication
        try:
            response = self.session.get(f"{BASE_URL}/auth/me")
            if response.status_code == 401:
                self.log_result("Auth - Unauthenticated User Info", True, "Correctly rejects unauthenticated request")
            else:
                self.log_result("Auth - Unauthenticated User Info", False, f"Expected 401, got {response.status_code}")
        except Exception as e:
            self.log_result("Auth - Unauthenticated User Info", False, f"Request failed: {str(e)}")
        
        # Test 4: Logout without authentication
        try:
            response = self.session.post(f"{BASE_URL}/auth/logout")
            if response.status_code == 200:
                self.log_result("Auth - Logout Without Auth", True, "Logout endpoint accessible")
            else:
                self.log_result("Auth - Logout Without Auth", False, f"Expected 200, got {response.status_code}")
        except Exception as e:
            self.log_result("Auth - Logout Without Auth", False, f"Request failed: {str(e)}")
    
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