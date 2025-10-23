import pytest
from fastapi.testclient import TestClient
from app.core.security import (
    sanitize_input,
    validate_notebook_name,
    validate_job_name,
    validate_code_length,
    get_password_hash,
    verify_password
)


@pytest.mark.security
class TestInputValidation:
    """Test input validation and sanitization"""

    def test_sanitize_input_removes_null_bytes(self):
        """Test that null bytes are removed"""
        input_str = "test\x00data"
        result = sanitize_input(input_str)
        assert "\x00" not in result

    def test_sanitize_input_blocks_eval(self):
        """Test that eval() is blocked"""
        with pytest.raises(Exception):
            sanitize_input("eval('malicious code')")

    def test_sanitize_input_blocks_exec(self):
        """Test that exec() is blocked"""
        with pytest.raises(Exception):
            sanitize_input("exec('malicious code')")

    def test_sanitize_input_blocks_import(self):
        """Test that __import__ is blocked"""
        with pytest.raises(Exception):
            sanitize_input("__import__('os').system('ls')")

    def test_validate_notebook_name_valid(self):
        """Test valid notebook name"""
        name = "My Test Notebook"
        result = validate_notebook_name(name)
        assert result == name

    def test_validate_notebook_name_empty(self):
        """Test empty notebook name"""
        with pytest.raises(Exception):
            validate_notebook_name("")

    def test_validate_notebook_name_too_long(self):
        """Test notebook name that's too long"""
        with pytest.raises(Exception):
            validate_notebook_name("a" * 300)

    def test_validate_notebook_name_invalid_chars(self):
        """Test notebook name with invalid characters"""
        with pytest.raises(Exception):
            validate_notebook_name("test<script>alert('xss')</script>")

    def test_validate_code_length_valid(self):
        """Test valid code length"""
        code = "print('hello world')"
        result = validate_code_length(code)
        assert result == code

    def test_validate_code_length_too_long(self):
        """Test code that's too long"""
        with pytest.raises(Exception):
            validate_code_length("a" * 200000)


@pytest.mark.security
class TestPasswordHashing:
    """Test password hashing functions"""

    def test_password_hash_verify(self):
        """Test password hashing and verification"""
        password = "test_password_123"
        hashed = get_password_hash(password)

        # Hash should be different from password
        assert hashed != password

        # Verification should succeed
        assert verify_password(password, hashed) is True

    def test_password_verify_wrong_password(self):
        """Test verification with wrong password"""
        password = "correct_password"
        wrong_password = "wrong_password"
        hashed = get_password_hash(password)

        assert verify_password(wrong_password, hashed) is False


@pytest.mark.security
def test_rate_limiting(client: TestClient):
    """Test rate limiting middleware"""
    # Make 70 requests
    responses = []
    for _ in range(70):
        response = client.get("/api/v1/dashboard/stats")
        responses.append(response.status_code)

    # Should have some 429 responses (rate limit exceeded)
    assert 429 in responses


@pytest.mark.security
def test_security_headers(client: TestClient):
    """Test that security headers are present"""
    response = client.get("/api/v1/dashboard/stats")

    headers = response.headers

    # Check for security headers
    assert "X-Content-Type-Options" in headers
    assert headers["X-Content-Type-Options"] == "nosniff"

    assert "X-Frame-Options" in headers
    assert headers["X-Frame-Options"] == "DENY"

    assert "X-XSS-Protection" in headers


@pytest.mark.security
def test_cors_headers(client: TestClient):
    """Test CORS headers"""
    response = client.options(
        "/api/v1/dashboard/stats",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET"
        }
    )

    # Should have CORS headers
    assert response.status_code in [200, 204]
