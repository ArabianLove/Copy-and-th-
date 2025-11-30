import pytest
from src.osint_utils import get_dns_records, fetch_headers

def test_get_dns_records_google():
    """Test DNS lookup for a known domain (google.com)."""
    records = get_dns_records("google.com", "A")
    assert len(records) > 0
    # Basic check to ensure we got IP addresses
    assert any("." in r for r in records)

def test_fetch_headers_example():
    """Test fetching headers from a stable site."""
    headers = fetch_headers("https://www.example.com")
    assert "Content-Type" in headers
    assert headers["Content-Type"].startswith("text/html")
