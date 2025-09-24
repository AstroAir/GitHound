"""Tests for authentication provider factory functions."""

import os
from unittest.mock import Mock, patch

from githound.mcp.auth.factory import (
    create_auth_provider,
    create_authorization_provider,
    create_provider_from_config,
    create_provider_from_environment,
    get_available_providers,
    validate_provider_config,
)
from githound.mcp.auth.providers.base import AuthProvider


class MockAuthProvider(AuthProvider):
    """Mock authentication provider for testing."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.config = kwargs  # [attr-defined]

    async def authenticate(self, token: str) -> None:
        return Mock(success=True, user=Mock(username="test"))

    async def validate_token(self, token: str) -> None:
        return Mock(username="test")

    def get_oauth_metadata(self) -> None:
        return None

    def supports_dynamic_client_registration(self) -> None:
        return False


class TestCreateAuthProvider:
    """Test authentication provider creation."""

    @patch("githound.mcp.auth.providers.jwt.JWTVerifier")
    def test_create_jwt_provider(self, mock_jwt) -> None:
        """Test creating JWT provider."""
        mock_jwt.return_value = MockAuthProvider()

        provider = create_auth_provider(
            "jwt",
            jwks_uri="https://example.com/.well-known/jwks.json",
            issuer="test-issuer",
            audience="test-audience",
        )

        assert provider is not None
        mock_jwt.assert_called_once_with(
            jwks_uri="https://example.com/.well-known/jwks.json",
            issuer="test-issuer",
            audience="test-audience",
        )

    @patch("githound.mcp.auth.providers.github.GitHubProvider")
    def test_create_github_provider(self, mock_github) -> None:
        """Test creating GitHub provider."""
        mock_github.return_value = MockAuthProvider()

        provider = create_auth_provider(
            "github", client_id="test-client-id", client_secret="test-client-secret"
        )

        assert provider is not None
        mock_github.assert_called_once_with(
            client_id="test-client-id", client_secret="test-client-secret"
        )

    @patch("githound.mcp.auth.providers.google.GoogleProvider")
    def test_create_google_provider(self, mock_google) -> None:
        """Test creating Google provider."""
        mock_google.return_value = MockAuthProvider()

        provider = create_auth_provider(
            "google",
            client_id="test-client-id.apps.googleusercontent.com",
            client_secret="test-client-secret",
        )

        assert provider is not None
        mock_google.assert_called_once_with(
            client_id="test-client-id.apps.googleusercontent.com",
            client_secret="test-client-secret",
        )

    def test_create_unknown_provider(self) -> None:
        """Test creating unknown provider type."""
        provider = create_auth_provider("unknown", param="value")
        assert provider is None

    @patch("githound.mcp.auth.providers.jwt.JWTVerifier")
    def test_create_provider_with_exception(self, mock_jwt) -> None:
        """Test provider creation with exception."""
        mock_jwt.side_effect = Exception("Test error")

        provider = create_auth_provider("jwt", jwks_uri="https://example.com")
        assert provider is None


class TestCreateAuthorizationProvider:
    """Test authorization provider creation."""

    def test_create_eunomia_provider_not_available(self) -> None:
        """Test creating Eunomia provider when not available."""
        base_provider = MockAuthProvider()

        with patch("githound.mcp.auth.factory.EUNOMIA_AVAILABLE", False):
            provider = create_authorization_provider(base_provider, "eunomia")
            assert provider is base_provider  # Should return original provider

    def test_create_permit_provider_not_available(self) -> None:
        """Test creating Permit.io provider when not available."""
        base_provider = MockAuthProvider()

        with patch("githound.mcp.auth.factory.PERMIT_AVAILABLE", False):
            provider = create_authorization_provider(base_provider, "permit")
            assert provider is base_provider  # Should return original provider

    @patch("githound.mcp.auth.factory.EUNOMIA_AVAILABLE", True)
    @patch("githound.mcp.auth.factory.EunomiaAuthorizationProvider")
    def test_create_eunomia_provider_available(self, mock_eunomia) -> None:
        """Test creating Eunomia provider when available."""
        base_provider = MockAuthProvider()
        mock_eunomia.return_value = MockAuthProvider()

        provider = create_authorization_provider(
            base_provider, "eunomia", policy_file="test_policies.json"
        )

        assert provider is not None
        mock_eunomia.assert_called_once_with(base_provider, policy_file="test_policies.json")

    @patch("githound.mcp.auth.factory.PERMIT_AVAILABLE", True)
    @patch("githound.mcp.auth.factory.PermitAuthorizationProvider")
    def test_create_permit_provider_available(self, mock_permit) -> None:
        """Test creating Permit.io provider when available."""
        base_provider = MockAuthProvider()
        mock_permit.return_value = MockAuthProvider()

        provider = create_authorization_provider(
            base_provider, "permit", permit_api_key="test-api-key"
        )

        assert provider is not None
        mock_permit.assert_called_once_with(base_provider, permit_api_key="test-api-key")

    def test_create_unknown_authorization_provider(self) -> None:
        """Test creating unknown authorization provider."""
        base_provider = MockAuthProvider()

        provider = create_authorization_provider(base_provider, "unknown")
        assert provider is base_provider  # Should return original provider


class TestCreateProviderFromConfig:
    """Test provider creation from configuration."""

    @patch("githound.mcp.auth.factory.create_auth_provider")
    def test_create_provider_auth_only(self, mock_create_auth) -> None:
        """Test creating provider with authentication only."""
        mock_create_auth.return_value = MockAuthProvider()

        config = {
            "auth": {
                "type": "jwt",
                "config": {
                    "jwks_uri": "https://example.com/.well-known/jwks.json",
                    "issuer": "test-issuer",
                },
            }
        }

        provider = create_provider_from_config(config)
        assert provider is not None
        mock_create_auth.assert_called_once_with(
            "jwt", jwks_uri="https://example.com/.well-known/jwks.json", issuer="test-issuer"
        )

    @patch("githound.mcp.auth.factory.create_auth_provider")
    @patch("githound.mcp.auth.factory.create_authorization_provider")
    def test_create_provider_with_authorization(self, mock_create_authz, mock_create_auth) -> None:
        """Test creating provider with authentication and authorization."""
        base_provider = MockAuthProvider()
        authz_provider = MockAuthProvider()

        mock_create_auth.return_value = base_provider
        mock_create_authz.return_value = authz_provider

        config = {
            "auth": {
                "type": "github",
                "config": {"client_id": "test-client-id", "client_secret": "test-client-secret"},
            },
            "authorization": {"type": "eunomia", "config": {"policy_file": "test_policies.json"}},
        }

        provider = create_provider_from_config(config)
        assert provider is authz_provider

        mock_create_auth.assert_called_once_with(
            "github", client_id="test-client-id", client_secret="test-client-secret"
        )
        mock_create_authz.assert_called_once_with(
            base_provider, "eunomia", policy_file="test_policies.json"
        )

    def test_create_provider_no_auth_type(self) -> None:
        """Test creating provider without auth type."""
        config = {"auth": {"config": {"param": "value"}}}

        provider = create_provider_from_config(config)
        assert provider is None

    def test_create_provider_no_auth_section(self) -> None:
        """Test creating provider without auth section."""
        config = {"authorization": {"type": "eunomia"}}

        provider = create_provider_from_config(config)
        assert provider is None


class TestCreateProviderFromEnvironment:
    """Test provider creation from environment variables."""

    @patch.dict(os.environ, {}, clear=True)
    def test_no_auth_type_environment(self) -> None:
        """Test with no auth type in environment."""
        provider = create_provider_from_environment()
        assert provider is None

    @patch.dict(
        os.environ,
        {
            "GITHOUND_AUTH_TYPE": "jwt",
            "GITHOUND_AUTH_JWKS_URI": "https://example.com/.well-known/jwks.json",
            "GITHOUND_AUTH_ISSUER": "test-issuer",
            "GITHOUND_AUTH_AUDIENCE": "test-audience",
        },
    )
    @patch("githound.mcp.auth.factory.create_auth_provider")
    def test_jwt_from_environment(self, mock_create_auth) -> None:
        """Test creating JWT provider from environment."""
        mock_create_auth.return_value = MockAuthProvider()

        provider = create_provider_from_environment()
        assert provider is not None

        mock_create_auth.assert_called_once_with(
            "jwt",
            jwks_uri="https://example.com/.well-known/jwks.json",
            issuer="test-issuer",
            audience="test-audience",
        )

    @patch.dict(
        os.environ,
        {
            "GITHOUND_AUTH_TYPE": "github",
            "GITHOUND_AUTH_CLIENT_ID": "test-client-id",
            "GITHOUND_AUTH_CLIENT_SECRET": "test-client-secret",
            "GITHOUND_AUTHORIZATION_TYPE": "eunomia",
            "GITHOUND_AUTHORIZATION_POLICY_FILE": "test_policies.json",
        },
    )
    @patch("githound.mcp.auth.factory.create_auth_provider")
    @patch("githound.mcp.auth.factory.create_authorization_provider")
    def test_github_with_eunomia_from_environment(
        self, mock_create_authz, mock_create_auth
    ) -> None:
        """Test creating GitHub + Eunomia from environment."""
        base_provider = MockAuthProvider()
        authz_provider = MockAuthProvider()

        mock_create_auth.return_value = base_provider
        mock_create_authz.return_value = authz_provider

        provider = create_provider_from_environment()
        assert provider is authz_provider

        mock_create_auth.assert_called_once_with(
            "github", client_id="test-client-id", client_secret="test-client-secret"
        )
        mock_create_authz.assert_called_once_with(
            base_provider, "eunomia", policy_file="test_policies.json"
        )


class TestGetAvailableProviders:
    """Test getting available provider information."""

    def test_get_available_providers(self) -> None:
        """Test getting available providers."""
        providers = get_available_providers()

        assert "authentication" in providers
        assert "authorization" in providers

        # Check authentication providers
        auth_providers = providers["authentication"]
        assert "jwt" in auth_providers
        assert "github" in auth_providers
        assert "google" in auth_providers

        for provider_info in auth_providers.values():
            assert "name" in provider_info
            assert "description" in provider_info
            assert "available" in provider_info
            # Core providers should always be available
            assert provider_info["available"] is True

        # Check authorization providers
        authz_providers = providers["authorization"]
        assert "eunomia" in authz_providers
        assert "permit" in authz_providers

        for provider_info in authz_providers.values():
            assert "name" in provider_info
            assert "description" in provider_info
            assert "available" in provider_info
            assert "package" in provider_info


class TestValidateProviderConfig:
    """Test provider configuration validation."""

    def test_validate_valid_config(self) -> None:
        """Test validating valid configuration."""
        config = {
            "auth": {
                "type": "jwt",
                "config": {"jwks_uri": "https://example.com/.well-known/jwks.json"},
            }
        }

        assert validate_provider_config(config) is True

    def test_validate_config_with_authorization(self) -> None:
        """Test validating configuration with authorization."""
        config = {
            "auth": {"type": "github", "config": {"client_id": "test-client-id"}},
            "authorization": {"type": "eunomia", "config": {"policy_file": "test_policies.json"}},
        }

        assert validate_provider_config(config) is True

    def test_validate_config_missing_auth(self) -> None:
        """Test validating configuration missing auth section."""
        config = {"authorization": {"type": "eunomia"}}

        assert validate_provider_config(config) is False

    def test_validate_config_missing_auth_type(self) -> None:
        """Test validating configuration missing auth type."""
        config = {"auth": {"config": {"param": "value"}}}

        assert validate_provider_config(config) is False

    def test_validate_config_invalid_auth_type(self) -> None:
        """Test validating configuration with invalid auth type."""
        config = {"auth": {"type": "invalid", "config": {}}}

        assert validate_provider_config(config) is False

    def test_validate_config_invalid_authorization_type(self) -> None:
        """Test validating configuration with invalid authorization type."""
        config = {
            "auth": {"type": "jwt", "config": {}},
            "authorization": {"type": "invalid", "config": {}},
        }

        assert validate_provider_config(config) is False


class TestEnvironmentVariableHandling:
    """Test environment variable parsing and handling."""

    @patch.dict(
        os.environ,
        {
            "GITHOUND_AUTH_TYPE": "jwt",
            "GITHOUND_AUTH_JWKS_URI": "https://example.com/.well-known/jwks.json",
            "GITHOUND_AUTH_ISSUER": "test-issuer",
            "GITHOUND_AUTH_AUDIENCE": "test-audience",
            "GITHOUND_AUTH_ALGORITHM": "RS256",
        },
    )
    def test_environment_variable_parsing(self) -> None:
        """Test parsing of environment variables."""
        from githound.mcp.auth.factory import create_provider_from_environment

        with patch("githound.mcp.auth.factory.create_auth_provider") as mock_create:
            mock_create.return_value = MockAuthProvider()

            provider = create_provider_from_environment()

            # Verify all environment variables were parsed correctly
            mock_create.assert_called_once_with(
                "jwt",
                jwks_uri="https://example.com/.well-known/jwks.json",
                issuer="test-issuer",
                audience="test-audience",
                algorithm="RS256",
            )
