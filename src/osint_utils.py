import dns.resolver
import requests
import whois
from typing import Dict, Any, List, Optional

def get_dns_records(domain: str, record_type: str = "A") -> List[str]:
    """
    Performs a DNS lookup for the specified domain and record type.

    Args:
        domain (str): The domain name to query.
        record_type (str): The type of DNS record (e.g., 'A', 'MX', 'TXT').

    Returns:
        List[str]: A list of string representations of the DNS records.
    """
    try:
        answers = dns.resolver.resolve(domain, record_type)
        return [str(rdata) for rdata in answers]
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.exception.Timeout):
        return []

def get_whois_info(domain: str) -> Optional[Any]:
    """
    Retrieves WHOIS information for a domain.

    Args:
        domain (str): The domain to query.

    Returns:
        Optional[Any]: The WHOIS data object or None if failed.
    """
    try:
        return whois.whois(domain)
    except Exception:
        return None

def fetch_headers(url: str) -> Dict[str, str]:
    """
    Fetches HTTP headers from a URL.

    Args:
        url (str): The URL to request.

    Returns:
        Dict[str, str]: A dictionary of response headers.
    """
    try:
        response = requests.head(url, timeout=5)
        return dict(response.headers)
    except requests.RequestException:
        return {}
