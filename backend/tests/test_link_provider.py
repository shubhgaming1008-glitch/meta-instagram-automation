"""
Tests for the link provider.
"""
import pytest
from app.services.link_provider import LinkProvider


class TestLinkProviderValidation:
    def test_blocks_localhost(self):
        provider = LinkProvider(None)
        with pytest.raises(ValueError, match="restricted"):
            provider._validate_url("http://localhost/internal")

    def test_blocks_private_ip(self):
        provider = LinkProvider(None)
        with pytest.raises(ValueError, match="restricted"):
            provider._validate_url("http://192.168.1.1/internal")

    def test_blocks_169_254(self):
        provider = LinkProvider(None)
        with pytest.raises(ValueError, match="restricted"):
            provider._validate_url("http://169.254.169.254/latest/meta-data/")

    def test_allows_valid_url(self):
        provider = LinkProvider(None)
        # Should not raise
        provider._validate_url("https://example.com/download")

    def test_blocks_non_http(self):
        provider = LinkProvider(None)
        with pytest.raises(ValueError, match="must start"):
            provider._validate_url("ftp://example.com/file")

    def test_utm_append(self):
        provider = LinkProvider(None)
        result = provider._append_utm("https://example.com", {"utm_source": "instagram"})
        assert "utm_source=instagram" in result

    def test_utm_append_existing_params(self):
        provider = LinkProvider(None)
        result = provider._append_utm("https://example.com?ref=bio", {"utm_campaign": "reel"})
        assert "utm_campaign=reel" in result
        assert result.startswith("https://example.com?ref=bio&")

    def test_ip_hash(self):
        provider = LinkProvider(None)
        h1 = provider._hash_ip("1.2.3.4")
        h2 = provider._hash_ip("1.2.3.4")
        assert h1 == h2
        assert len(h1) == 64  # SHA256 hex
