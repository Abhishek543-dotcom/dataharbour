#!/usr/bin/env python3
"""
Comprehensive API Test Script for DataHarbour
Tests all API endpoints and reports their status
"""

import requests
import json
import os
import time
from typing import Dict, List, Tuple
import sys

# Configuration
BASE_URL = "http://localhost:8000"
TIMEOUT = 10

class APITester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results: List[Dict] = []
        self.auth_token = None

    def log_test(self, endpoint: str, method: str, status: str, details: str = ""):
        """Log a test result"""
        result = {
            "endpoint": endpoint,
            "method": method,
            "status": status,
            "details": details
        }
        self.test_results.append(result)
        print(f"[{status}] {method} {endpoint} - {details}")

    def make_request(self, method: str, endpoint: str, **kwargs) -> Tuple[bool, str]:
        """Make an HTTP request and return success status and response details"""
        try:
            url = f"{self.base_url}{endpoint}"
            response = self.session.request(method, url, timeout=TIMEOUT, **kwargs)

            if response.status_code < 400:
                return True, f"Status: {response.status_code}"
            else:
                return False, f"Status: {response.status_code}, Response: {response.text[:200]}"

        except requests.exceptions.RequestException as e:
            return False, f"Request failed: {str(e)}"

    def test_auth_endpoints(self):
        """Test authentication endpoints"""
        print("\n=== Testing Authentication Endpoints ===")

        # Test login
        success, details = self.make_request("POST", "/auth/login",
                                           json={"username": "test", "password": "test"})
        self.log_test("/auth/login", "POST", "PASS" if success else "FAIL", details)

        # Test logout
        success, details = self.make_request("POST", "/auth/logout")
        self.log_test("/auth/logout", "POST", "PASS" if success else "FAIL", details)

    def test_minio_endpoints(self):
        """Test MinIO/S3 endpoints"""
        print("\n=== Testing MinIO Endpoints ===")

        # List buckets
        success, details = self.make_request("GET", "/dhfs/buckets")
        self.log_test("/dhfs/buckets", "GET", "PASS" if success else "FAIL", details)

        # Create bucket
        success, details = self.make_request("POST", "/dhfs/buckets/test-bucket")
        self.log_test("/dhfs/buckets/{bucket_name}", "POST", "PASS" if success else "FAIL", details)

        # Upload file (if bucket creation succeeded)
        if success:
            try:
                with open("workspace/data/sample.json", "rb") as f:
                    files = {"file": ("sample.json", f, "application/json")}
                    success, details = self.make_request("POST", "/minio/upload/test-bucket",
                                                       files=files)
                    self.log_test("/minio/upload/{bucket}", "POST", "PASS" if success else "FAIL", details)
            except FileNotFoundError:
                self.log_test("/minio/upload/{bucket}", "POST", "SKIP", "Sample file not found")

        # List files in bucket
        success, details = self.make_request("GET", "/dhfs/files/test-bucket")
        self.log_test("/dhfs/files/{bucket_name}", "GET", "PASS" if success else "FAIL", details)

        # Download file
        success, details = self.make_request("GET", "/dhfs/download/test-bucket/sample.json")
        self.log_test("/dhfs/download/{bucket_name}/{file_key}", "GET", "PASS" if success else "FAIL", details)

        # Delete file
        success, details = self.make_request("DELETE", "/minio/delete/test-bucket/sample.json")
        self.log_test("/minio/delete/{bucket}/{key}", "DELETE", "PASS" if success else "FAIL", details)

        # Delete bucket
        success, details = self.make_request("DELETE", "/dhfs/buckets/test-bucket")
        self.log_test("/dhfs/buckets/{bucket_name}", "DELETE", "PASS" if success else "FAIL", details)

    def test_database_endpoints(self):
        """Test database management endpoints"""
        print("\n=== Testing Database Endpoints ===")

        # List databases
        success, details = self.make_request("GET", "/catalog/databases")
        self.log_test("/catalog/databases", "GET", "PASS" if success else "FAIL", details)

        # Create database
        success, details = self.make_request("POST", "/database/create/test_db")
        self.log_test("/database/create/{db_name}", "POST", "PASS" if success else "FAIL", details)

        # Create table (if database creation succeeded)
        if success:
            success, details = self.make_request("POST", "/table/create/test_db/test_table")
            self.log_test("/table/create/{db_name}/{table_name}", "POST", "PASS" if success else "FAIL", details)

            # List tables
            success, details = self.make_request("GET", "/catalog/databases/test_db/tables")
            self.log_test("/catalog/databases/{db_name}/tables", "GET", "PASS" if success else "FAIL", details)

            # Delete table
            success, details = self.make_request("DELETE", "/table/delete/test_db/test_table")
            self.log_test("/table/delete/{db_name}/{table_name}", "DELETE", "PASS" if success else "FAIL", details)

        # Delete database
        success, details = self.make_request("DELETE", "/database/delete/test_db")
        self.log_test("/database/delete/{db_name}", "DELETE", "PASS" if success else "FAIL", details)

    def test_iceberg_endpoints(self):
        """Test Iceberg catalog endpoints"""
        print("\n=== Testing Iceberg Endpoints ===")

        # List Iceberg tables
        success, details = self.make_request("GET", "/catalog/iceberg/tables")
        self.log_test("/catalog/iceberg/tables", "GET", "PASS" if success else "FAIL", details)

        # Get table details (if tables exist)
        if success:
            try:
                response = self.session.get(f"{self.base_url}/catalog/iceberg/tables", timeout=TIMEOUT)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("tables"):
                        table_name = data["tables"][0]["name"]
                        success, details = self.make_request("GET", f"/catalog/iceberg/tables/{table_name}")
                        self.log_test("/catalog/iceberg/tables/{table_name}", "GET", "PASS" if success else "FAIL", details)
                    else:
                        self.log_test("/catalog/iceberg/tables/{table_name}", "GET", "SKIP", "No tables available")
                else:
                    self.log_test("/catalog/iceberg/tables/{table_name}", "GET", "SKIP", "Cannot list tables")
            except:
                self.log_test("/catalog/iceberg/tables/{table_name}", "GET", "SKIP", "Error checking tables")

    def test_notebook_endpoints(self):
        """Test notebook management endpoints"""
        print("\n=== Testing Notebook Endpoints ===")

        # List notebooks
        success, details = self.make_request("GET", "/notebooks")
        self.log_test("/notebooks", "GET", "PASS" if success else "FAIL", details)

        # Create notebook
        success, details = self.make_request("POST", "/notebooks",
                                           json={"name": "test_notebook.ipynb"})
        self.log_test("/notebooks", "POST", "PASS" if success else "FAIL", details)

        # Get notebook (if creation succeeded)
        if success:
            success, details = self.make_request("GET", "/notebooks/test_notebook.ipynb")
            self.log_test("/notebooks/{notebook_name}", "GET", "PASS" if success else "FAIL", details)

            # Update notebook
            success, details = self.make_request("PUT", "/notebooks/test_notebook.ipynb",
                                               json={
                                                   "cells": [{"cell_type": "code", "source": ["print('test')"]}],
                                                   "metadata": {},
                                                   "nbformat": 4,
                                                   "nbformat_minor": 5
                                               })
            self.log_test("/notebooks/{notebook_name}", "PUT", "PASS" if success else "FAIL", details)

            # Execute notebook
            success, details = self.make_request("POST", "/notebooks/test_notebook.ipynb/execute")
            self.log_test("/notebooks/{notebook_name}/execute", "POST", "PASS" if success else "FAIL", details)

            # Delete notebook
            success, details = self.make_request("DELETE", "/notebooks/test_notebook.ipynb")
            self.log_test("/notebooks/{notebook_name}", "DELETE", "PASS" if success else "FAIL", details)

    def test_job_endpoints(self):
        """Test job management endpoints"""
        print("\n=== Testing Job Endpoints ===")

        # Get jobs
        success, details = self.make_request("GET", "/jobs")
        self.log_test("/jobs", "GET", "PASS" if success else "FAIL", details)

        # Get running jobs
        success, details = self.make_request("GET", "/jobs/running")
        self.log_test("/jobs/running", "GET", "PASS" if success else "FAIL", details)

        # Get pending jobs
        success, details = self.make_request("GET", "/jobs/pending")
        self.log_test("/jobs/pending", "GET", "PASS" if success else "FAIL", details)

        # Get completed jobs
        success, details = self.make_request("GET", "/jobs/completed")
        self.log_test("/jobs/completed", "GET", "PASS" if success else "FAIL", details)

        # Submit job
        try:
            with open("workspace/jobs/sample_job.py", "rb") as f:
                files = {"file": ("sample_job.py", f, "text/plain")}
                success, details = self.make_request("POST", "/jobs/submit", files=files)
                self.log_test("/jobs/submit", "POST", "PASS" if success else "FAIL", details)
        except FileNotFoundError:
            self.log_test("/jobs/submit", "POST", "SKIP", "Sample job file not found")

    def test_cluster_endpoints(self):
        """Test cluster status endpoints"""
        print("\n=== Testing Cluster Endpoints ===")

        # Get cluster status
        success, details = self.make_request("GET", "/cluster/status")
        self.log_test("/cluster/status", "GET", "PASS" if success else "FAIL", details)

        # Get cluster workers
        success, details = self.make_request("GET", "/cluster/workers")
        self.log_test("/cluster/workers", "GET", "PASS" if success else "FAIL", details)

        # Get cluster applications
        success, details = self.make_request("GET", "/cluster/applications")
        self.log_test("/cluster/applications", "GET", "PASS" if success else "FAIL", details)

        # Legacy cluster endpoint
        success, details = self.make_request("GET", "/cluster")
        self.log_test("/cluster", "GET", "PASS" if success else "FAIL", details)

    def test_stats_endpoints(self):
        """Test statistics and dashboard endpoints"""
        print("\n=== Testing Stats Endpoints ===")

        # Get stats summary
        success, details = self.make_request("GET", "/stats/summary")
        self.log_test("/stats/summary", "GET", "PASS" if success else "FAIL", details)

        # Get recent activities
        success, details = self.make_request("GET", "/activities/recent")
        self.log_test("/activities/recent", "GET", "PASS" if success else "FAIL", details)

    def test_logs_endpoint(self):
        """Test logs endpoint"""
        print("\n=== Testing Logs Endpoint ===")

        success, details = self.make_request("GET", "/logs")
        self.log_test("/logs", "GET", "PASS" if success else "FAIL", details)

    def check_service_health(self) -> bool:
        """Check if the API service is running"""
        try:
            response = requests.get(f"{self.base_url}/docs", timeout=5)
            return response.status_code == 200
        except:
            return False

    def run_all_tests(self):
        """Run all API tests"""
        print("DataHarbour API Test Suite")
        print("=" * 50)

        # Check if service is running
        if not self.check_service_health():
            print("❌ API service is not running at", self.base_url)
            print("Please start the services with: docker-compose up -d")
            return

        print("✅ API service is running")

        # Run all test suites
        self.test_auth_endpoints()
        self.test_minio_endpoints()
        self.test_database_endpoints()
        self.test_iceberg_endpoints()
        self.test_notebook_endpoints()
        self.test_job_endpoints()
        self.test_cluster_endpoints()
        self.test_stats_endpoints()
        self.test_logs_endpoint()

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 50)
        print("TEST SUMMARY")
        print("=" * 50)

        passed = len([r for r in self.test_results if r["status"] == "PASS"])
        failed = len([r for r in self.test_results if r["status"] == "FAIL"])
        skipped = len([r for r in self.test_results if r["status"] == "SKIP"])

        print(f"Total Tests: {len(self.test_results)}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⏭️  Skipped: {skipped}")

        if failed > 0:
            print(f"\n❌ Failed Tests:")
            for result in self.test_results:
                if result["status"] == "FAIL":
                    print(f"  - {result['method']} {result['endpoint']}: {result['details']}")

        if skipped > 0:
            print(f"\n⏭️  Skipped Tests:")
            for result in self.test_results:
                if result["status"] == "SKIP":
                    print(f"  - {result['method']} {result['endpoint']}: {result['details']}")


def main():
    """Main function"""
    tester = APITester()

    # Allow custom base URL
    if len(sys.argv) > 1:
        tester.base_url = sys.argv[1]

    tester.run_all_tests()


if __name__ == "__main__":
    main()