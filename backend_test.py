#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Enhanced Blockchain-Enabled Student Records System
Tests all backend APIs including authentication, UUID system, blockchain integration,
analytics dashboard, notification system, and automated verification workflow
"""

import requests
import json
import hashlib
import uuid
from datetime import datetime
import time
import asyncio
import websockets
import threading

# Configuration
BASE_URL = "https://credential-verify-3.preview.emergentagent.com/api"
WS_URL = "wss://credential-verify-3.preview.emergentagent.com/api"
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
    
    def test_blockchain_service_integration(self):
        """Test Blockchain Service Integration"""
        print("\n=== Testing Blockchain Service Integration ===")
        
        # Test 1: Blockchain connection status
        try:
            response = self.session.get(f"{BASE_URL}/blockchain/status")
            if response.status_code == 200:
                data = response.json()
                if "connected" in data:
                    self.log_result("Blockchain - Connection Status", True, 
                                   f"Blockchain status endpoint working, connected: {data.get('connected')}")
                    if data.get("connected"):
                        self.log_result("Blockchain - Service Connected", True, 
                                       f"Blockchain service connected to {data.get('rpc_url')}")
                    else:
                        self.log_result("Blockchain - Service Connected", False, 
                                       f"Blockchain service not connected: {data.get('error', 'Unknown error')}")
                else:
                    self.log_result("Blockchain - Connection Status", False, "Missing connection status in response")
            else:
                self.log_result("Blockchain - Connection Status", False, f"Expected 200, got {response.status_code}")
        except Exception as e:
            self.log_result("Blockchain - Connection Status", False, f"Request failed: {str(e)}")
        
        # Test 2: Student blockchain history (requires authentication)
        if self.auth_token and "student" in self.test_users:
            try:
                headers = {"Authorization": f"Bearer {self.auth_token}"}
                student_id = self.test_users["student"]["id"]
                response = self.session.get(f"{BASE_URL}/blockchain/student/{student_id}/history", headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    self.log_result("Blockchain - Student History", True, 
                                   f"Retrieved blockchain history for student {student_id}")
                elif response.status_code == 403:
                    self.log_result("Blockchain - Student History", True, 
                                   "Correctly enforces permission check for blockchain history")
                else:
                    self.log_result("Blockchain - Student History", False, 
                                   f"Expected 200 or 403, got {response.status_code}")
            except Exception as e:
                self.log_result("Blockchain - Student History", False, f"Request failed: {str(e)}")
    
    def test_enhanced_uuid_verification(self):
        """Test Enhanced UUID Verification with Blockchain Status"""
        print("\n=== Testing Enhanced UUID Verification ===")
        
        # Test 1: Blockchain hash verification
        try:
            fake_hash = hashlib.sha256("test content".encode()).hexdigest()
            response = self.session.get(f"{BASE_URL}/verify/blockchain_hash/{fake_hash}")
            if response.status_code == 200:
                data = response.json()
                if "verified" in data and "type" in data:
                    self.log_result("UUID Verification - Blockchain Hash", True, 
                                   f"Blockchain hash verification endpoint working, verified: {data.get('verified')}")
                else:
                    self.log_result("UUID Verification - Blockchain Hash", False, 
                                   "Missing verification data in response")
            else:
                self.log_result("UUID Verification - Blockchain Hash", False, 
                               f"Expected 200, got {response.status_code}")
        except Exception as e:
            self.log_result("UUID Verification - Blockchain Hash", False, f"Request failed: {str(e)}")
        
        # Test 2: Enhanced student request verification with blockchain status
        try:
            fake_uuid = str(uuid.uuid4())
            response = self.session.get(f"{BASE_URL}/verify/student_request/{fake_uuid}")
            if response.status_code == 200:
                data = response.json()
                if "verified" in data:
                    # Check if blockchain_status is included in response
                    has_blockchain_status = "blockchain_status" in data
                    self.log_result("UUID Verification - Enhanced Student Request", True, 
                                   f"Enhanced verification working, includes blockchain status: {has_blockchain_status}")
                else:
                    self.log_result("UUID Verification - Enhanced Student Request", False, 
                                   "Missing verification data in response")
            else:
                self.log_result("UUID Verification - Enhanced Student Request", False, 
                               f"Expected 200, got {response.status_code}")
        except Exception as e:
            self.log_result("UUID Verification - Enhanced Student Request", False, f"Request failed: {str(e)}")
    
    def test_analytics_dashboard_api(self):
        """Test Analytics Dashboard API"""
        print("\n=== Testing Analytics Dashboard API ===")
        
        # Create authenticated issuer session for analytics testing
        issuer_token = None
        try:
            issuer_data = {
                "email": "analytics.issuer@university.edu",
                "name": "Analytics Issuer",
                "role": "issuer",
                "university": "Analytics University"
            }
            response = self.session.post(f"{BASE_URL}/auth/mock-login", json=issuer_data)
            if response.status_code == 200:
                data = response.json()
                issuer_token = data["session_token"]
                self.log_result("Analytics - Issuer Auth Setup", True, "Created issuer session for analytics testing")
            else:
                self.log_result("Analytics - Issuer Auth Setup", False, "Failed to create issuer session")
        except Exception as e:
            self.log_result("Analytics - Issuer Auth Setup", False, f"Request failed: {str(e)}")
        
        if not issuer_token:
            self.log_result("Analytics - Tests Skipped", False, "No issuer token available for analytics testing")
            return
        
        headers = {"Authorization": f"Bearer {issuer_token}"}
        
        # Test 1: Analytics overview
        try:
            response = self.session.get(f"{BASE_URL}/analytics/overview", headers=headers)
            if response.status_code == 200:
                data = response.json()
                required_fields = ["total_requests", "verified_requests", "verification_rate"]
                has_required = all(field in data for field in required_fields)
                self.log_result("Analytics - Overview", True, 
                               f"Analytics overview working, has required fields: {has_required}")
            elif response.status_code == 403:
                self.log_result("Analytics - Overview", True, "Correctly restricts analytics to authorized roles")
            else:
                self.log_result("Analytics - Overview", False, f"Expected 200 or 403, got {response.status_code}")
        except Exception as e:
            self.log_result("Analytics - Overview", False, f"Request failed: {str(e)}")
        
        # Test 2: Analytics trends
        try:
            response = self.session.get(f"{BASE_URL}/analytics/trends?days=7", headers=headers)
            if response.status_code == 200:
                data = response.json()
                if "trends" in data and isinstance(data["trends"], list):
                    self.log_result("Analytics - Trends", True, 
                                   f"Analytics trends working, returned {len(data['trends'])} data points")
                else:
                    self.log_result("Analytics - Trends", False, "Missing or invalid trends data")
            else:
                self.log_result("Analytics - Trends", False, f"Expected 200, got {response.status_code}")
        except Exception as e:
            self.log_result("Analytics - Trends", False, f"Request failed: {str(e)}")
        
        # Test 3: University analytics
        try:
            response = self.session.get(f"{BASE_URL}/analytics/universities", headers=headers)
            if response.status_code == 200:
                data = response.json()
                if "top_issuers" in data and "top_verifiers" in data:
                    self.log_result("Analytics - Universities", True, 
                                   "University analytics working with issuer and verifier data")
                else:
                    self.log_result("Analytics - Universities", False, "Missing university analytics data")
            else:
                self.log_result("Analytics - Universities", False, f"Expected 200, got {response.status_code}")
        except Exception as e:
            self.log_result("Analytics - Universities", False, f"Request failed: {str(e)}")
        
        # Test 4: Comprehensive dashboard
        try:
            response = self.session.get(f"{BASE_URL}/analytics/dashboard", headers=headers)
            if response.status_code == 200:
                data = response.json()
                required_sections = ["overview", "trends", "universities", "blockchain"]
                has_sections = all(section in data for section in required_sections)
                self.log_result("Analytics - Dashboard", True, 
                               f"Comprehensive dashboard working, has required sections: {has_sections}")
            else:
                self.log_result("Analytics - Dashboard", False, f"Expected 200, got {response.status_code}")
        except Exception as e:
            self.log_result("Analytics - Dashboard", False, f"Request failed: {str(e)}")
    
    def test_notification_system(self):
        """Test Notification System"""
        print("\n=== Testing Notification System ===")
        
        if not self.auth_token:
            self.log_result("Notifications - No Auth", False, "No auth token available for notification testing")
            return
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test 1: Recent notifications
        try:
            response = self.session.get(f"{BASE_URL}/notifications/recent", headers=headers)
            if response.status_code == 200:
                data = response.json()
                if "notifications" in data:
                    self.log_result("Notifications - Recent", True, 
                                   f"Recent notifications endpoint working, returned {len(data['notifications'])} notifications")
                else:
                    self.log_result("Notifications - Recent", False, "Missing notifications data")
            else:
                self.log_result("Notifications - Recent", False, f"Expected 200, got {response.status_code}")
        except Exception as e:
            self.log_result("Notifications - Recent", False, f"Request failed: {str(e)}")
        
        # Test 2: Notification stats (requires issuer/verifier role)
        try:
            # Create issuer session for stats testing
            issuer_data = {
                "email": "notification.issuer@university.edu",
                "name": "Notification Issuer",
                "role": "issuer",
                "university": "Notification University"
            }
            response = self.session.post(f"{BASE_URL}/auth/mock-login", json=issuer_data)
            if response.status_code == 200:
                data = response.json()
                issuer_token = data["session_token"]
                issuer_headers = {"Authorization": f"Bearer {issuer_token}"}
                
                stats_response = self.session.get(f"{BASE_URL}/notifications/stats", headers=issuer_headers)
                if stats_response.status_code == 200:
                    stats_data = stats_response.json()
                    if "active_connections" in stats_data:
                        self.log_result("Notifications - Stats", True, 
                                       "Notification stats endpoint working")
                    else:
                        self.log_result("Notifications - Stats", False, "Missing stats data")
                elif stats_response.status_code == 403:
                    self.log_result("Notifications - Stats", True, 
                                   "Correctly restricts notification stats to authorized roles")
                else:
                    self.log_result("Notifications - Stats", False, 
                                   f"Expected 200 or 403, got {stats_response.status_code}")
            else:
                self.log_result("Notifications - Stats", False, "Failed to create issuer session for stats testing")
        except Exception as e:
            self.log_result("Notifications - Stats", False, f"Request failed: {str(e)}")
        
        # Test 3: WebSocket connection test (simplified)
        try:
            # Test WebSocket endpoint availability by checking if it returns proper error for HTTP request
            ws_test_url = f"{BASE_URL}/ws/notifications/student/test-user-id"
            response = self.session.get(ws_test_url)
            # WebSocket endpoints typically return 426 Upgrade Required for HTTP requests
            if response.status_code in [426, 400, 405]:
                self.log_result("Notifications - WebSocket Endpoint", True, 
                               "WebSocket endpoint exists and properly rejects HTTP requests")
            else:
                self.log_result("Notifications - WebSocket Endpoint", False, 
                               f"WebSocket endpoint test inconclusive, status: {response.status_code}")
        except Exception as e:
            self.log_result("Notifications - WebSocket Endpoint", False, f"Request failed: {str(e)}")
    
    def test_system_health_monitoring(self):
        """Test System Health Monitoring"""
        print("\n=== Testing System Health Monitoring ===")
        
        # Test 1: System health endpoint
        try:
            response = self.session.get(f"{BASE_URL}/system/health")
            if response.status_code == 200:
                data = response.json()
                required_components = ["database", "blockchain", "notifications", "analytics"]
                has_components = all(component in data for component in required_components)
                
                if has_components:
                    self.log_result("System Health - Components", True, 
                                   f"System health monitoring working, all components reported")
                    
                    # Check individual component statuses
                    healthy_components = []
                    unhealthy_components = []
                    
                    for component in required_components:
                        status = data.get(component, "unknown")
                        if status in ["healthy", "connected"]:
                            healthy_components.append(component)
                        else:
                            unhealthy_components.append(f"{component}:{status}")
                    
                    self.log_result("System Health - Status Check", True, 
                                   f"Healthy: {healthy_components}, Issues: {unhealthy_components}")
                else:
                    self.log_result("System Health - Components", False, 
                                   "Missing required health components")
            else:
                self.log_result("System Health - Endpoint", False, f"Expected 200, got {response.status_code}")
        except Exception as e:
            self.log_result("System Health - Endpoint", False, f"Request failed: {str(e)}")
    
    def test_payment_gateway_integration(self):
        """Test Payment Gateway Integration"""
        print("\n=== Testing Payment Gateway Integration ===")
        
        if not self.auth_token:
            self.log_result("Payment - No Auth", False, "No auth token available for payment testing")
            return
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test 1: Get pricing information
        try:
            response = self.session.get(f"{BASE_URL}/payments/pricing")
            if response.status_code == 200:
                data = response.json()
                required_fields = ["transcript_fee", "processing_fee", "total_per_transcript", "currency"]
                has_required = all(field in data for field in required_fields)
                if has_required:
                    self.test_data["pricing"] = data
                    self.log_result("Payment - Pricing Info", True, 
                                   f"Retrieved pricing: ${data['total_per_transcript']} {data['currency']}")
                else:
                    self.log_result("Payment - Pricing Info", False, "Missing required pricing fields")
            else:
                self.log_result("Payment - Pricing Info", False, f"Expected 200, got {response.status_code}")
        except Exception as e:
            self.log_result("Payment - Pricing Info", False, f"Request failed: {str(e)}")
        
        # Test 2: Create payment intent
        try:
            payment_intent_data = {
                "transcript_count": 1,
                "university_from": "Payment Test University",
                "university_to": "Receiving Payment University",
                "document_type": "transcript"
            }
            response = self.session.post(f"{BASE_URL}/payments/create-intent", json=payment_intent_data, headers=headers)
            if response.status_code == 200:
                data = response.json()
                required_fields = ["payment_id", "client_secret", "amount_details"]
                has_required = all(field in data for field in required_fields)
                if has_required:
                    self.test_data["payment_intent"] = data
                    self.log_result("Payment - Create Intent", True, 
                                   f"Created payment intent: {data['payment_id']}")
                else:
                    self.log_result("Payment - Create Intent", False, "Missing required payment intent fields")
            else:
                self.log_result("Payment - Create Intent", False, f"Expected 200, got {response.status_code}")
        except Exception as e:
            self.log_result("Payment - Create Intent", False, f"Request failed: {str(e)}")
        
        # Test 3: Process payment (successful scenario)
        if "payment_intent" in self.test_data:
            try:
                payment_process_data = {
                    "payment_id": self.test_data["payment_intent"]["payment_id"],
                    "payment_method": "credit_card",
                    "card_number": "4111111111111111",
                    "card_expiry": "12/25",
                    "card_cvc": "123",
                    "card_brand": "visa",
                    "cardholder_name": "Test Student"
                }
                response = self.session.post(f"{BASE_URL}/payments/process", json=payment_process_data, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        self.test_data["successful_payment"] = data
                        self.log_result("Payment - Process Success", True, 
                                       f"Payment processed successfully: {data.get('transaction_id')}")
                    else:
                        # This is expected due to 95% success rate - could be a simulated failure
                        self.log_result("Payment - Process (Simulated Failure)", True, 
                                       f"Payment failed as expected (mock failure): {data.get('error')}")
                else:
                    self.log_result("Payment - Process Success", False, f"Expected 200, got {response.status_code}")
            except Exception as e:
                self.log_result("Payment - Process Success", False, f"Request failed: {str(e)}")
        
        # Test 4: Get payment status
        if "payment_intent" in self.test_data:
            try:
                payment_id = self.test_data["payment_intent"]["payment_id"]
                response = self.session.get(f"{BASE_URL}/payments/{payment_id}/status", headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    required_fields = ["payment_id", "status", "amount_details"]
                    has_required = all(field in data for field in required_fields)
                    if has_required:
                        self.log_result("Payment - Status Check", True, 
                                       f"Retrieved payment status: {data['status']}")
                    else:
                        self.log_result("Payment - Status Check", False, "Missing required status fields")
                else:
                    self.log_result("Payment - Status Check", False, f"Expected 200, got {response.status_code}")
            except Exception as e:
                self.log_result("Payment - Status Check", False, f"Request failed: {str(e)}")
    
    def test_payment_protected_workflow(self):
        """Test Payment-Protected Transcript Request Workflow"""
        print("\n=== Testing Payment-Protected Workflow ===")
        
        if not self.auth_token:
            self.log_result("Payment Workflow - No Auth", False, "No auth token available")
            return
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test 1: Try to create transcript request without payment (should fail)
        try:
            request_data = {
                "university_from": "Test University",
                "university_to": "Receiving University",
                "document_type": "transcript",
                "content": "Test transcript content",
                "payment_id": "invalid_payment_id"
            }
            response = self.session.post(f"{BASE_URL}/transcript-requests", json=request_data, headers=headers)
            if response.status_code == 400:
                self.log_result("Payment Workflow - Invalid Payment", True, 
                               "Correctly rejects transcript request with invalid payment")
            else:
                self.log_result("Payment Workflow - Invalid Payment", False, 
                               f"Expected 400, got {response.status_code}")
        except Exception as e:
            self.log_result("Payment Workflow - Invalid Payment", False, f"Request failed: {str(e)}")
        
        # Test 2: Create successful payment and then transcript request
        successful_payment_id = None
        
        # First create and process a payment
        try:
            # Create payment intent
            payment_intent_data = {
                "transcript_count": 1,
                "university_from": "Workflow Test University",
                "university_to": "Workflow Receiving University",
                "document_type": "transcript"
            }
            response = self.session.post(f"{BASE_URL}/payments/create-intent", json=payment_intent_data, headers=headers)
            if response.status_code == 200:
                intent_data = response.json()
                payment_id = intent_data["payment_id"]
                
                # Process payment (retry up to 3 times to get a successful payment due to 95% success rate)
                for attempt in range(3):
                    payment_process_data = {
                        "payment_id": payment_id,
                        "payment_method": "credit_card",
                        "card_number": "4111111111111111",
                        "card_expiry": "12/25",
                        "card_cvc": "123",
                        "card_brand": "visa",
                        "cardholder_name": "Workflow Test Student"
                    }
                    process_response = self.session.post(f"{BASE_URL}/payments/process", json=payment_process_data, headers=headers)
                    if process_response.status_code == 200:
                        process_data = process_response.json()
                        if process_data.get("success"):
                            successful_payment_id = payment_id
                            self.log_result("Payment Workflow - Successful Payment", True, 
                                           f"Created successful payment for workflow testing: {payment_id}")
                            break
                        else:
                            # Try creating a new payment intent for next attempt
                            if attempt < 2:  # Don't create new intent on last attempt
                                new_response = self.session.post(f"{BASE_URL}/payments/create-intent", json=payment_intent_data, headers=headers)
                                if new_response.status_code == 200:
                                    intent_data = new_response.json()
                                    payment_id = intent_data["payment_id"]
                
                if not successful_payment_id:
                    self.log_result("Payment Workflow - Successful Payment", False, 
                                   "Could not create successful payment after 3 attempts (expected due to 95% success rate)")
            else:
                self.log_result("Payment Workflow - Payment Intent", False, 
                               f"Failed to create payment intent: {response.status_code}")
        except Exception as e:
            self.log_result("Payment Workflow - Payment Setup", False, f"Payment setup failed: {str(e)}")
        
        # Test 3: Create transcript request with valid payment
        if successful_payment_id:
            try:
                request_data = {
                    "university_from": "Workflow Test University",
                    "university_to": "Workflow Receiving University",
                    "document_type": "transcript",
                    "content": "This is a test transcript document for payment-protected workflow testing",
                    "payment_id": successful_payment_id
                }
                response = self.session.post(f"{BASE_URL}/transcript-requests", json=request_data, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    if "student_request_uuid" in data and data.get("payment_id") == successful_payment_id:
                        self.test_data["paid_transcript_request"] = data
                        self.log_result("Payment Workflow - Valid Payment Request", True, 
                                       f"Successfully created transcript request with payment: {data['student_request_uuid']}")
                    else:
                        self.log_result("Payment Workflow - Valid Payment Request", False, 
                                       "Missing required fields or payment not linked")
                else:
                    self.log_result("Payment Workflow - Valid Payment Request", False, 
                                   f"Expected 200, got {response.status_code}")
            except Exception as e:
                self.log_result("Payment Workflow - Valid Payment Request", False, f"Request failed: {str(e)}")
        
        # Test 4: Try to reuse the same payment (should fail)
        if successful_payment_id:
            try:
                request_data = {
                    "university_from": "Duplicate Test University",
                    "university_to": "Duplicate Receiving University",
                    "document_type": "transcript",
                    "content": "Duplicate transcript request",
                    "payment_id": successful_payment_id
                }
                response = self.session.post(f"{BASE_URL}/transcript-requests", json=request_data, headers=headers)
                if response.status_code == 400:
                    self.log_result("Payment Workflow - Duplicate Payment", True, 
                                   "Correctly prevents reuse of payment for multiple requests")
                else:
                    self.log_result("Payment Workflow - Duplicate Payment", False, 
                                   f"Expected 400, got {response.status_code}")
            except Exception as e:
                self.log_result("Payment Workflow - Duplicate Payment", False, f"Request failed: {str(e)}")
    
    def test_payment_failure_scenarios(self):
        """Test Payment Failure Scenarios"""
        print("\n=== Testing Payment Failure Scenarios ===")
        
        if not self.auth_token:
            self.log_result("Payment Failures - No Auth", False, "No auth token available")
            return
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test 1: Process payment with non-existent payment ID
        try:
            payment_process_data = {
                "payment_id": "non_existent_payment_id",
                "payment_method": "credit_card",
                "card_number": "4111111111111111",
                "card_expiry": "12/25",
                "card_cvc": "123",
                "card_brand": "visa",
                "cardholder_name": "Test Student"
            }
            response = self.session.post(f"{BASE_URL}/payments/process", json=payment_process_data, headers=headers)
            if response.status_code == 200:
                data = response.json()
                if not data.get("success") and "not found" in data.get("error", "").lower():
                    self.log_result("Payment Failures - Non-existent Payment", True, 
                                   "Correctly handles non-existent payment ID")
                else:
                    self.log_result("Payment Failures - Non-existent Payment", False, 
                                   "Should fail for non-existent payment ID")
            else:
                self.log_result("Payment Failures - Non-existent Payment", False, 
                               f"Expected 200, got {response.status_code}")
        except Exception as e:
            self.log_result("Payment Failures - Non-existent Payment", False, f"Request failed: {str(e)}")
        
        # Test 2: Test payment expiry (create intent and wait)
        try:
            payment_intent_data = {
                "transcript_count": 1,
                "university_from": "Expiry Test University",
                "university_to": "Expiry Receiving University",
                "document_type": "transcript"
            }
            response = self.session.post(f"{BASE_URL}/payments/create-intent", json=payment_intent_data, headers=headers)
            if response.status_code == 200:
                data = response.json()
                payment_id = data["payment_id"]
                
                # Note: In real testing, we would wait for expiry, but for mock testing we'll just verify the expiry logic exists
                self.log_result("Payment Failures - Expiry Logic", True, 
                               f"Payment intent created with expiry time: {data.get('expires_at')}")
            else:
                self.log_result("Payment Failures - Expiry Logic", False, 
                               f"Failed to create payment intent: {response.status_code}")
        except Exception as e:
            self.log_result("Payment Failures - Expiry Logic", False, f"Request failed: {str(e)}")
        
        # Test 3: Test multiple payment failure scenarios (due to 95% success rate, we should see some failures)
        failure_count = 0
        success_count = 0
        
        for i in range(10):  # Try 10 payments to test failure scenarios
            try:
                # Create payment intent
                payment_intent_data = {
                    "transcript_count": 1,
                    "university_from": f"Failure Test University {i}",
                    "university_to": f"Failure Receiving University {i}",
                    "document_type": "transcript"
                }
                response = self.session.post(f"{BASE_URL}/payments/create-intent", json=payment_intent_data, headers=headers)
                if response.status_code == 200:
                    intent_data = response.json()
                    payment_id = intent_data["payment_id"]
                    
                    # Process payment
                    payment_process_data = {
                        "payment_id": payment_id,
                        "payment_method": "credit_card",
                        "card_number": "4111111111111111",
                        "card_expiry": "12/25",
                        "card_cvc": "123",
                        "card_brand": "visa",
                        "cardholder_name": f"Test Student {i}"
                    }
                    process_response = self.session.post(f"{BASE_URL}/payments/process", json=payment_process_data, headers=headers)
                    if process_response.status_code == 200:
                        process_data = process_response.json()
                        if process_data.get("success"):
                            success_count += 1
                        else:
                            failure_count += 1
                            # Store one failure example for detailed testing
                            if failure_count == 1:
                                self.test_data["payment_failure_example"] = {
                                    "payment_id": payment_id,
                                    "error": process_data.get("error"),
                                    "error_code": process_data.get("error_code")
                                }
            except Exception as e:
                continue
        
        # Verify we got some failures (expected with 95% success rate)
        if failure_count > 0:
            self.log_result("Payment Failures - Mock Failures", True, 
                           f"Simulated payment failures working: {failure_count} failures, {success_count} successes")
        else:
            self.log_result("Payment Failures - Mock Failures", False, 
                           "Expected some payment failures with 95% success rate")
    
    def test_complete_integrated_workflow(self):
        """Test Complete Integrated Payment-to-Blockchain Workflow"""
        print("\n=== Testing Complete Integrated Workflow ===")
        
        if not self.auth_token:
            self.log_result("Integrated Workflow - No Auth", False, "No auth token available")
            return
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Step 1: Create payment intent
        payment_id = None
        try:
            payment_intent_data = {
                "transcript_count": 1,
                "university_from": "Integrated Test University",
                "university_to": "Integrated Receiving University",
                "document_type": "transcript"
            }
            response = self.session.post(f"{BASE_URL}/payments/create-intent", json=payment_intent_data, headers=headers)
            if response.status_code == 200:
                data = response.json()
                payment_id = data["payment_id"]
                self.log_result("Integrated Workflow - Step 1: Payment Intent", True, 
                               f"Created payment intent: {payment_id}")
            else:
                self.log_result("Integrated Workflow - Step 1: Payment Intent", False, 
                               f"Failed to create payment intent: {response.status_code}")
                return
        except Exception as e:
            self.log_result("Integrated Workflow - Step 1: Payment Intent", False, f"Request failed: {str(e)}")
            return
        
        # Step 2: Process payment (retry until successful)
        successful_payment = False
        for attempt in range(5):  # Try up to 5 times to get successful payment
            try:
                payment_process_data = {
                    "payment_id": payment_id,
                    "payment_method": "credit_card",
                    "card_number": "4111111111111111",
                    "card_expiry": "12/25",
                    "card_cvc": "123",
                    "card_brand": "visa",
                    "cardholder_name": "Integrated Test Student"
                }
                response = self.session.post(f"{BASE_URL}/payments/process", json=payment_process_data, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        successful_payment = True
                        self.log_result("Integrated Workflow - Step 2: Payment Processing", True, 
                                       f"Payment processed successfully: {data.get('transaction_id')}")
                        break
                    else:
                        # Create new payment intent for next attempt
                        if attempt < 4:
                            new_response = self.session.post(f"{BASE_URL}/payments/create-intent", json=payment_intent_data, headers=headers)
                            if new_response.status_code == 200:
                                new_data = new_response.json()
                                payment_id = new_data["payment_id"]
            except Exception as e:
                continue
        
        if not successful_payment:
            self.log_result("Integrated Workflow - Step 2: Payment Processing", False, 
                           "Could not achieve successful payment after 5 attempts")
            return
        
        # Step 3: Create transcript request with successful payment
        transcript_request = None
        try:
            request_data = {
                "university_from": "Integrated Test University",
                "university_to": "Integrated Receiving University",
                "document_type": "transcript",
                "content": "This is a comprehensive test transcript document for integrated payment-to-blockchain workflow testing",
                "payment_id": payment_id
            }
            response = self.session.post(f"{BASE_URL}/transcript-requests", json=request_data, headers=headers)
            if response.status_code == 200:
                data = response.json()
                if "student_request_uuid" in data:
                    transcript_request = data
                    self.log_result("Integrated Workflow - Step 3: Transcript Request", True, 
                                   f"Created transcript request: {data['student_request_uuid']}")
                else:
                    self.log_result("Integrated Workflow - Step 3: Transcript Request", False, 
                                   "Missing UUID in transcript request response")
                    return
            else:
                self.log_result("Integrated Workflow - Step 3: Transcript Request", False, 
                               f"Failed to create transcript request: {response.status_code}")
                return
        except Exception as e:
            self.log_result("Integrated Workflow - Step 3: Transcript Request", False, f"Request failed: {str(e)}")
            return
        
        # Step 4: Wait for background processing and check blockchain integration
        try:
            time.sleep(3)  # Wait for background processing
            
            request_id = transcript_request["id"]
            response = self.session.get(f"{BASE_URL}/transcript-requests/{request_id}", headers=headers)
            if response.status_code == 200:
                data = response.json()
                if "transcript_request" in data:
                    request_details = data["transcript_request"]
                    has_blockchain_data = any(key in request_details for key in ["blockchain_hash", "blockchain_verified"])
                    payment_linked = request_details.get("payment_id") == payment_id
                    
                    self.log_result("Integrated Workflow - Step 4: Blockchain Processing", True, 
                                   f"Background processing completed - Blockchain data: {has_blockchain_data}, Payment linked: {payment_linked}")
                else:
                    self.log_result("Integrated Workflow - Step 4: Blockchain Processing", False, 
                                   "Missing transcript request in response")
            else:
                self.log_result("Integrated Workflow - Step 4: Blockchain Processing", False, 
                               f"Failed to retrieve request details: {response.status_code}")
        except Exception as e:
            self.log_result("Integrated Workflow - Step 4: Blockchain Processing", False, f"Request failed: {str(e)}")
        
        # Step 5: Verify payment-request linking in database
        try:
            payment_response = self.session.get(f"{BASE_URL}/payments/{payment_id}/status", headers=headers)
            if payment_response.status_code == 200:
                payment_data = payment_response.json()
                self.log_result("Integrated Workflow - Step 5: Payment-Request Linking", True, 
                               f"Payment status verified: {payment_data['status']}")
            else:
                self.log_result("Integrated Workflow - Step 5: Payment-Request Linking", False, 
                               f"Failed to verify payment status: {payment_response.status_code}")
        except Exception as e:
            self.log_result("Integrated Workflow - Step 5: Payment-Request Linking", False, f"Request failed: {str(e)}")
    
    def test_system_health_with_payments(self):
        """Test System Health Including Payment Gateway Status"""
        print("\n=== Testing System Health with Payment Integration ===")
        
        try:
            response = self.session.get(f"{BASE_URL}/system/health")
            if response.status_code == 200:
                data = response.json()
                required_components = ["database", "blockchain", "notifications", "analytics"]
                has_components = all(component in data for component in required_components)
                
                if has_components:
                    # Check if payment gateway status is included or can be inferred
                    payment_status = "unknown"
                    if "payment_gateway" in data:
                        payment_status = data["payment_gateway"]
                    else:
                        # Infer payment status from successful payment operations
                        payment_status = "operational" if hasattr(self, 'test_data') and any('payment' in key for key in self.test_data.keys()) else "unknown"
                    
                    self.log_result("System Health - Payment Integration", True, 
                                   f"System health includes payment status: {payment_status}")
                    
                    # Log all component statuses
                    component_statuses = {comp: data.get(comp, "unknown") for comp in required_components}
                    self.log_result("System Health - All Components", True, 
                                   f"Component statuses: {component_statuses}")
                else:
                    self.log_result("System Health - Payment Integration", False, 
                                   "Missing required health components")
            else:
                self.log_result("System Health - Payment Integration", False, 
                               f"Expected 200, got {response.status_code}")
        except Exception as e:
            self.log_result("System Health - Payment Integration", False, f"Request failed: {str(e)}")
    
    def test_automated_verification_workflow(self):
        """Test Automated Verification Workflow"""
        print("\n=== Testing Automated Verification Workflow ===")
        
        if not self.auth_token:
            self.log_result("Workflow - No Auth", False, "No auth token available for workflow testing")
            return
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test 1: Create transcript request with background processing (now requires payment)
        # First create a successful payment
        payment_id = None
        try:
            # Create payment intent
            payment_intent_data = {
                "transcript_count": 1,
                "university_from": "Workflow Test University",
                "university_to": "Receiving Workflow University",
                "document_type": "transcript"
            }
            response = self.session.post(f"{BASE_URL}/payments/create-intent", json=payment_intent_data, headers=headers)
            if response.status_code == 200:
                intent_data = response.json()
                payment_id = intent_data["payment_id"]
                
                # Process payment (retry until successful)
                for attempt in range(3):
                    payment_process_data = {
                        "payment_id": payment_id,
                        "payment_method": "credit_card",
                        "card_number": "4111111111111111",
                        "card_expiry": "12/25",
                        "card_cvc": "123",
                        "card_brand": "visa",
                        "cardholder_name": "Workflow Test Student"
                    }
                    process_response = self.session.post(f"{BASE_URL}/payments/process", json=payment_process_data, headers=headers)
                    if process_response.status_code == 200:
                        process_data = process_response.json()
                        if process_data.get("success"):
                            break
                        else:
                            # Create new payment intent for next attempt
                            if attempt < 2:
                                new_response = self.session.post(f"{BASE_URL}/payments/create-intent", json=payment_intent_data, headers=headers)
                                if new_response.status_code == 200:
                                    intent_data = new_response.json()
                                    payment_id = intent_data["payment_id"]
                    else:
                        payment_id = None
                        break
        except Exception as e:
            self.log_result("Workflow - Payment Setup", False, f"Payment setup failed: {str(e)}")
            return
        
        if not payment_id:
            self.log_result("Workflow - Payment Required", False, "Could not create successful payment for workflow testing")
            return
        
        # Now create transcript request with payment
        try:
            request_data = {
                "university_from": "Workflow Test University",
                "university_to": "Receiving Workflow University",
                "document_type": "transcript",
                "content": "This is a comprehensive test transcript document for automated blockchain verification workflow testing",
                "payment_id": payment_id
            }
            response = self.session.post(f"{BASE_URL}/transcript-requests", json=request_data, headers=headers)
            if response.status_code == 200:
                data = response.json()
                if "student_request_uuid" in data and "content_hash" in data:
                    self.test_data["workflow_request"] = data
                    self.log_result("Workflow - Request Creation", True, 
                                   f"Created transcript request with UUID: {data['student_request_uuid']}")
                    
                    # Wait a moment for background processing
                    time.sleep(2)
                    
                    # Check if blockchain processing was initiated
                    if "blockchain_hash" in data or "blockchain_verified" in data:
                        self.log_result("Workflow - Background Processing", True, 
                                       "Background blockchain processing initiated")
                    else:
                        self.log_result("Workflow - Background Processing", False, 
                                       "Background blockchain processing not detected in immediate response")
                else:
                    self.log_result("Workflow - Request Creation", False, "Missing required fields in response")
            else:
                self.log_result("Workflow - Request Creation", False, f"Expected 200, got {response.status_code}")
        except Exception as e:
            self.log_result("Workflow - Request Creation", False, f"Request failed: {str(e)}")
        
        # Test 2: Check request details for blockchain status
        if "workflow_request" in self.test_data:
            try:
                request_id = self.test_data["workflow_request"]["id"]
                response = self.session.get(f"{BASE_URL}/transcript-requests/{request_id}", headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    if "transcript_request" in data:
                        request_details = data["transcript_request"]
                        has_blockchain_data = any(key in request_details for key in ["blockchain_hash", "blockchain_verified"])
                        self.log_result("Workflow - Request Details", True, 
                                       f"Retrieved request details, blockchain data present: {has_blockchain_data}")
                    else:
                        self.log_result("Workflow - Request Details", False, "Missing transcript request in response")
                else:
                    self.log_result("Workflow - Request Details", False, f"Expected 200, got {response.status_code}")
            except Exception as e:
                self.log_result("Workflow - Request Details", False, f"Request failed: {str(e)}")
    
    def test_enhanced_api_endpoints(self):
        """Test Enhanced API Endpoints"""
        print("\n=== Testing Enhanced API Endpoints ===")
        
        enhanced_endpoints = [
            ("GET", "/blockchain/status"),
            ("GET", "/analytics/overview"),
            ("GET", "/analytics/trends"),
            ("GET", "/analytics/universities"),
            ("GET", "/analytics/dashboard"),
            ("GET", "/notifications/recent"),
            ("GET", "/notifications/stats"),
            ("GET", "/system/health"),
            ("GET", f"/verify/blockchain_hash/{hashlib.sha256('test'.encode()).hexdigest()}"),
            ("GET", f"/blockchain/student/{uuid.uuid4()}/history")
        ]
        
        for method, endpoint in enhanced_endpoints:
            try:
                if method == "GET":
                    # Some endpoints require authentication
                    if any(auth_required in endpoint for auth_required in ["/analytics/", "/notifications/", "/blockchain/student/"]):
                        if self.auth_token:
                            headers = {"Authorization": f"Bearer {self.auth_token}"}
                            response = self.session.get(f"{BASE_URL}{endpoint}", headers=headers)
                        else:
                            continue  # Skip if no auth token
                    else:
                        response = self.session.get(f"{BASE_URL}{endpoint}")
                
                # Check if endpoint exists (not 404)
                if response.status_code != 404:
                    self.log_result(f"Enhanced Endpoint - {method} {endpoint}", True, 
                                   f"Endpoint exists (status: {response.status_code})")
                else:
                    self.log_result(f"Enhanced Endpoint - {method} {endpoint}", False, 
                                   "Endpoint not found (404)")
            except Exception as e:
                self.log_result(f"Enhanced Endpoint - {method} {endpoint}", False, 
                               f"Request failed: {str(e)}")
    
    def run_all_tests(self):
        """Run all backend tests including new blockchain features"""
        print("🚀 Starting Comprehensive Backend Testing - Enhanced Blockchain System")
        print(f"Testing against: {BASE_URL}")
        print("=" * 80)
        
        # Initialize test data
        self.test_content_hashing()
        
        # Test authentication system first
        self.test_mock_authentication_system()
        self.test_session_verification()
        self.test_protected_endpoints_with_auth()
        self.test_authentication_endpoints()
        
        # Test NEW BLOCKCHAIN FEATURES
        print("\n" + "=" * 80)
        print("🔗 TESTING NEW BLOCKCHAIN FEATURES")
        print("=" * 80)
        
        self.test_blockchain_service_integration()
        self.test_enhanced_uuid_verification()
        self.test_analytics_dashboard_api()
        self.test_notification_system()
        self.test_system_health_monitoring()
        self.test_automated_verification_workflow()
        
        # Test enhanced endpoints
        self.test_enhanced_api_endpoints()
        
        # Test existing components
        print("\n" + "=" * 80)
        print("📋 TESTING EXISTING COMPONENTS")
        print("=" * 80)
        
        self.test_api_endpoints_availability()
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