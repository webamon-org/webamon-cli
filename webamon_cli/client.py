"""API client for Webamon API."""

import requests
from typing import Dict, List, Any, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import Config


class WebamonAPIError(Exception):
    """Custom exception for API errors."""
    pass


class WebamonClient:
    """Client for interacting with Webamon API."""
    
    def __init__(self, config: Config):
        """Initialize the client with configuration."""
        self.config = config
        self.session = requests.Session()
        
        # Set up retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set up headers
        self.session.headers.update({
            'User-Agent': 'webamon-cli/0.1.0',
        })
        
        # Add API key to headers if available
        if self.config.api_key:
            self.session.headers.update({
                'x-api-key': self.config.api_key
            })
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make an HTTP request to the API."""
        url = f"{self.config.api_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            
            # Handle empty responses
            if response.status_code == 204 or not response.content:
                return {}
                
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise WebamonAPIError("Authentication failed. Check your API key.")
            elif e.response.status_code == 403:
                if not self.config.api_key:
                    raise WebamonAPIError(
                        "Rate limit exceeded - you've hit the daily quota (20 queries/day for free tier).\n"
                        "Upgrade to Pro for 1,000+ daily queries, larger response sizes, and premium features:\n"
                        "https://webamon.com/pricing"
                    )
                else:
                    raise WebamonAPIError("Access forbidden. Check your permissions.")
            elif e.response.status_code == 404:
                raise WebamonAPIError("Resource not found.")
            elif e.response.status_code == 429:
                if not self.config.api_key:
                    raise WebamonAPIError(
                        "Rate limit exceeded - you've hit the daily quota (20 queries/day for free tier).\n"
                        "Upgrade to Pro for 1,000+ daily queries, larger response sizes, and premium features:\n"
                        "https://webamon.com/pricing"
                    )
                else:
                    raise WebamonAPIError(
                        "Rate limit exceeded - you've hit your daily API quota.\n"
                        "Check your usage or upgrade your plan at: https://webamon.com/pricing"
                    )
            else:
                try:
                    error_data = e.response.json()
                    message = error_data.get('message', str(e))
                except:
                    message = str(e)
                raise WebamonAPIError(f"API error: {message}")
                
        except requests.exceptions.ConnectionError as e:
            # Check if this might be a quota limit issue
            error_str = str(e).lower()
            # Look for specific quota-related error patterns
            quota_keywords = [
                'too many 429 error responses',
                '429 error responses',
                'max retries exceeded',
                'connection pool',
                'httpsconnectionpool'
            ]
            
            if any(keyword in error_str for keyword in quota_keywords):
                if not self.config.api_key:
                    raise WebamonAPIError(
                        "Rate limit exceeded - you've hit the daily quota (20 queries/day for free tier).\n"
                        "Upgrade to Pro for 1,000+ daily queries, larger response sizes, and premium features:\n"
                        "https://webamon.com/pricing"
                    )
                else:
                    raise WebamonAPIError(
                        "Rate limit exceeded - you've hit your daily API quota.\n"
                        "Check your usage or upgrade your plan at: https://webamon.com/pricing"
                    )
            else:
                raise WebamonAPIError("Connection failed. Check your network and API URL.")
        except requests.exceptions.Timeout:
            raise WebamonAPIError("Request timed out.")
        except requests.exceptions.RequestException as e:
            raise WebamonAPIError(f"Request failed: {e}")
    
    def search(self, search_term: str, results: str, size: int = 10, from_offset: int = 0) -> Dict[str, Any]:
        """Perform basic search with pagination support."""
        params = {
            'search': search_term,
            'results': results,
            'size': size
        }
        # Add pagination for Pro users (with API key)
        if self.config.api_key and from_offset > 0:
            params['from'] = from_offset
        return self._make_request('GET', '/search', params=params)
    
    def search_lucene(self, lucene_query: str, index: str, fields: Optional[str] = None, size: int = 10, from_offset: int = 0) -> Dict[str, Any]:
        """Perform Lucene search with pagination support."""
        params = {
            'lucene_query': lucene_query,
            'index': index,
            'size': size
        }
        if fields:
            params['fields'] = fields
        # Add pagination for Pro users (with API key)
        if self.config.api_key and from_offset > 0:
            params['from'] = from_offset
        return self._make_request('GET', '/search', params=params)
    
    def scan(self, submission_url: str) -> Dict[str, Any]:
        """Initiate a scan for the specified target."""
        params = {
            'submission_url': submission_url
        }
        return self._make_request('GET', '/scan', params=params)
    
    def screenshot(self, report_id: str) -> Dict[str, Any]:
        """Retrieve screenshot for a specific scan report."""
        params = {
            'report_id': report_id
        }
        return self._make_request('GET', '/screenshot', params=params)
    
    def test_connection(self) -> Dict[str, Any]:
        """Test API connection by performing a simple search."""
        try:
            # Test with a simple search that should work on both endpoints
            return self.search('example.com', 'domain.name', size=1)
        except Exception:
            # If search fails, try a basic request to root
            return self._make_request('GET', '/')