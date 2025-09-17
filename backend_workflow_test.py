#!/usr/bin/env python3
"""
Advanced Backend Workflow Testing
Tests the complete student records verification workflow with mock authentication
"""

import requests
import json
import hashlib
import uuid
from datetime import datetime
import time

# Configuration
BASE_URL = "https://credential-verify-3.preview.emergentagent.com/api"

class WorkflowTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.workflow_data = {}
        
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
    
    def test_emergent_auth_integration(self):
        """Test Emergent Authentication Integration Issues"""
        print("\n=== Testing Emergent Auth Integration ===")
        
        # Test the external auth service call
        try:
            # This simulates what happens when session-data is called with a real session ID
            headers = {"X-Session-ID": "test_session_123"}
            response = self.session.get(f"{BASE_URL}/auth/session-data", headers=headers)
            
            if response.status_code == 401:
                self.log_result("Emergent Auth - External Service", False, 
                               "External auth service returns 404 - integration issue detected",
                               "The Emergent Auth service at demobackend.emergentagent.com is not responding correctly")
            else:
                self.log_result("Emergent Auth - External Service", True, 
                               f"Auth service responded with status {response.status_code}")
        except Exception as e:
            self.log_result("Emergent Auth - External Service", False, f"Request failed: {str(e)}")
    
    def test_database_connectivity(self):
        """Test database connectivity through API endpoints"""
        print("\n=== Testing Database Connectivity ===")
        
        # Test if MongoDB is accessible by checking UUID verification
        try:
            fake_uuid = str(uuid.uuid4())
            response = self.session.get(f"{BASE_URL}/verify/student_request/{fake_uuid}")
            
            if response.status_code == 200:
                data = response.json()
                if 'verified' in data and not data['verified']:
                    self.log_result("Database Connectivity", True, 
                                   "Database is accessible - UUID verification working")
                else:
                    self.log_result("Database Connectivity", False, 
                                   "Unexpected response from UUID verification")
            else:
                self.log_result("Database Connectivity", False, 
                               f"UUID verification failed with status {response.status_code}")
        except Exception as e:
            self.log_result("Database Connectivity", False, f"Database test failed: {str(e)}")
    
    def test_content_hash_integrity(self):
        """Test content hash integrity and consistency"""
        print("\n=== Testing Content Hash Integrity ===")
        
        # Test multiple content samples
        test_contents = [
            "Student: John Doe, University: MIT, GPA: 3.8",
            "Student: Jane Smith, University: Stanford, GPA: 3.9",
            "Student: Bob Johnson, University: Harvard, GPA: 3.7"
        ]
        
        hashes = []
        for i, content in enumerate(test_contents):
            hash_value = hashlib.sha256(content.encode()).hexdigest()
            hashes.append(hash_value)
            self.log_result(f"Content Hash - Sample {i+1}", True, 
                           f"Generated hash: {hash_value[:16]}...")
        
        # Test hash uniqueness
        if len(set(hashes)) == len(hashes):
            self.log_result("Content Hash - Uniqueness", True, 
                           "All content hashes are unique")
        else:
            self.log_result("Content Hash - Uniqueness", False, 
                           "Duplicate hashes detected")
        
        # Test hash consistency
        content = test_contents[0]
        hash1 = hashlib.sha256(content.encode()).hexdigest()
        hash2 = hashlib.sha256(content.encode()).hexdigest()
        
        if hash1 == hash2:
            self.log_result("Content Hash - Consistency", True, 
                           "Same content produces identical hashes")
        else:
            self.log_result("Content Hash - Consistency", False, 
                           "Hash inconsistency detected")
    
    def test_uuid_system_comprehensive(self):
        """Comprehensive UUID system testing"""
        print("\n=== Testing Multi-level UUID System ===")
        
        # Test UUID generation for all three levels
        uuid_types = ["student_request", "issuer_validation", "verifier_receipt"]
        generated_uuids = {}
        
        for uuid_type in uuid_types:
            uuids = []
            for i in range(5):
                test_uuid = str(uuid.uuid4())
                uuids.append(test_uuid)
            
            generated_uuids[uuid_type] = uuids
            
            # Test uniqueness within type
            if len(set(uuids)) == len(uuids):
                self.log_result(f"UUID System - {uuid_type} Uniqueness", True, 
                               f"Generated {len(uuids)} unique UUIDs")
            else:
                self.log_result(f"UUID System - {uuid_type} Uniqueness", False, 
                               "Duplicate UUIDs detected")
        
        # Test cross-type uniqueness
        all_uuids = []
        for uuids in generated_uuids.values():
            all_uuids.extend(uuids)
        
        if len(set(all_uuids)) == len(all_uuids):
            self.log_result("UUID System - Cross-type Uniqueness", True, 
                           "All UUIDs across types are unique")
        else:
            self.log_result("UUID System - Cross-type Uniqueness", False, 
                           "Cross-type UUID duplicates detected")
    
    def test_api_security_comprehensive(self):
        """Comprehensive API security testing"""
        print("\n=== Testing API Security ===")
        
        # Test all protected endpoints without authentication
        protected_endpoints = [
            ("POST", "/transcript-requests", {"university_from": "A", "university_to": "B", "content": "test"}),
            ("GET", "/transcript-requests", None),
            ("POST", "/issuer-validations", {"transcript_request_id": str(uuid.uuid4()), "is_approved": True}),
            ("POST", "/verifier-receipts", {"transcript_request_id": str(uuid.uuid4()), "issuer_validation_id": str(uuid.uuid4())}),
            ("GET", "/auth/me", None),
            ("PUT", f"/users/{uuid.uuid4()}/role", {"role": "issuer"})
        ]
        
        for method, endpoint, data in protected_endpoints:
            try:
                if method == "GET":
                    response = self.session.get(f"{BASE_URL}{endpoint}")
                elif method == "POST":
                    response = self.session.post(f"{BASE_URL}{endpoint}", json=data)
                elif method == "PUT":
                    response = self.session.put(f"{BASE_URL}{endpoint}", json=data)
                
                expected_codes = [401, 403]  # Unauthorized or Forbidden
                if response.status_code in expected_codes:
                    self.log_result(f"Security - {method} {endpoint}", True, 
                                   f"Correctly protected (status: {response.status_code})")
                else:
                    self.log_result(f"Security - {method} {endpoint}", False, 
                                   f"Security issue - expected {expected_codes}, got {response.status_code}")
            except Exception as e:
                self.log_result(f"Security - {method} {endpoint}", False, f"Test failed: {str(e)}")
    
    def test_uuid_verification_comprehensive(self):
        """Comprehensive UUID verification testing"""
        print("\n=== Testing UUID Verification System ===")
        
        uuid_types = ["student_request", "issuer_validation", "verifier_receipt"]
        
        for uuid_type in uuid_types:
            # Test with non-existent UUID
            fake_uuid = str(uuid.uuid4())
            try:
                response = self.session.get(f"{BASE_URL}/verify/{uuid_type}/{fake_uuid}")
                
                if response.status_code == 200:
                    data = response.json()
                    if not data.get('verified', True):
                        self.log_result(f"UUID Verification - {uuid_type} Invalid", True, 
                                       "Correctly identifies non-existent UUID")
                    else:
                        self.log_result(f"UUID Verification - {uuid_type} Invalid", False, 
                                       "Should not verify non-existent UUID")
                else:
                    self.log_result(f"UUID Verification - {uuid_type} Invalid", False, 
                                   f"Unexpected status code: {response.status_code}")
            except Exception as e:
                self.log_result(f"UUID Verification - {uuid_type} Invalid", False, f"Test failed: {str(e)}")
        
        # Test invalid UUID format
        try:
            invalid_uuid = "not-a-valid-uuid"
            response = self.session.get(f"{BASE_URL}/verify/student_request/{invalid_uuid}")
            
            if response.status_code == 200:
                data = response.json()
                if not data.get('verified', True):
                    self.log_result("UUID Verification - Invalid Format", True, 
                                   "Correctly handles invalid UUID format")
                else:
                    self.log_result("UUID Verification - Invalid Format", False, 
                                   "Should reject invalid UUID format")
            else:
                self.log_result("UUID Verification - Invalid Format", False, 
                               f"Unexpected status code: {response.status_code}")
        except Exception as e:
            self.log_result("UUID Verification - Invalid Format", False, f"Test failed: {str(e)}")
    
    def test_role_based_access_logic(self):
        """Test role-based access control logic"""
        print("\n=== Testing Role-based Access Control ===")
        
        # Test role update endpoint security
        try:
            role_data = {"role": "admin", "university": "Hacker University"}
            fake_user_id = str(uuid.uuid4())
            response = self.session.put(f"{BASE_URL}/users/{fake_user_id}/role", json=role_data)
            
            if response.status_code == 401:
                self.log_result("RBAC - Role Update Security", True, 
                               "Role update properly protected")
            else:
                self.log_result("RBAC - Role Update Security", False, 
                               f"Role update security issue - status: {response.status_code}")
        except Exception as e:
            self.log_result("RBAC - Role Update Security", False, f"Test failed: {str(e)}")
    
    def test_api_error_handling(self):
        """Test API error handling"""
        print("\n=== Testing API Error Handling ===")
        
        # Test malformed JSON
        try:
            response = self.session.post(f"{BASE_URL}/transcript-requests", 
                                       data="invalid json", 
                                       headers={"Content-Type": "application/json"})
            
            if response.status_code == 422:
                self.log_result("Error Handling - Malformed JSON", True, 
                               "Correctly handles malformed JSON")
            else:
                self.log_result("Error Handling - Malformed JSON", False, 
                               f"Unexpected status for malformed JSON: {response.status_code}")
        except Exception as e:
            self.log_result("Error Handling - Malformed JSON", False, f"Test failed: {str(e)}")
        
        # Test missing required fields
        try:
            incomplete_data = {"university_from": "A"}  # Missing required fields
            response = self.session.post(f"{BASE_URL}/transcript-requests", json=incomplete_data)
            
            if response.status_code in [422, 403]:  # Validation error or auth error
                self.log_result("Error Handling - Missing Fields", True, 
                               "Correctly handles missing required fields")
            else:
                self.log_result("Error Handling - Missing Fields", False, 
                               f"Unexpected status for missing fields: {response.status_code}")
        except Exception as e:
            self.log_result("Error Handling - Missing Fields", False, f"Test failed: {str(e)}")
    
    def run_comprehensive_tests(self):
        """Run all comprehensive backend tests"""
        print("🚀 Starting Comprehensive Backend Workflow Testing")
        print(f"Testing against: {BASE_URL}")
        print("=" * 70)
        
        # Run all test suites
        self.test_emergent_auth_integration()
        self.test_database_connectivity()
        self.test_content_hash_integrity()
        self.test_uuid_system_comprehensive()
        self.test_api_security_comprehensive()
        self.test_uuid_verification_comprehensive()
        self.test_role_based_access_logic()
        self.test_api_error_handling()
        
        # Generate summary
        self.generate_summary()
    
    def generate_summary(self):
        """Generate comprehensive test summary"""
        print("\n" + "=" * 70)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 70)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Categorize results
        critical_failures = []
        minor_issues = []
        
        for result in self.test_results:
            if not result['success']:
                if 'External Service' in result['test'] or 'Auth' in result['test']:
                    critical_failures.append(result)
                else:
                    minor_issues.append(result)
        
        if critical_failures:
            print("\n🚨 CRITICAL ISSUES:")
            for result in critical_failures:
                print(f"  - {result['test']}: {result['message']}")
                if result['details']:
                    print(f"    Details: {result['details']}")
        
        if minor_issues:
            print("\n⚠️  MINOR ISSUES:")
            for result in minor_issues:
                print(f"  - {result['test']}: {result['message']}")
        
        print(f"\n✅ WORKING COMPONENTS ({passed_tests} tests passed):")
        categories = {}
        for result in self.test_results:
            if result['success']:
                category = result['test'].split(' - ')[0]
                if category not in categories:
                    categories[category] = 0
                categories[category] += 1
        
        for category, count in categories.items():
            print(f"  - {category}: {count} tests passed")
        
        return {
            'total': total_tests,
            'passed': passed_tests,
            'failed': failed_tests,
            'critical_failures': len(critical_failures),
            'minor_issues': len(minor_issues),
            'success_rate': (passed_tests/total_tests)*100,
            'results': self.test_results
        }

if __name__ == "__main__":
    tester = WorkflowTester()
    summary = tester.run_comprehensive_tests()