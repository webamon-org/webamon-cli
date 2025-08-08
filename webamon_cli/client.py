"""API client for Webamon API."""

import requests
from typing import Dict, List, Any, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from rich.console import Console

from .config import Config

console = Console()


class WebamonAPIError(Exception):
    """Custom exception for API errors."""
    pass


class WebamonClient:
    """Client for interacting with Webamon API."""
    
    def __init__(self, config: Config, verbose: bool = False):
        """Initialize the client with configuration."""
        self.config = config
        self.verbose = verbose
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
            'User-Agent': 'webamon-cli/0.1.1',
        })
        
        # Add API key to headers if available
        if self.config.api_key:
            self.session.headers.update({
                'x-api-key': self.config.api_key
            })
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make an HTTP request to the API."""
        url = f"{self.config.api_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        # Show request details if verbose mode is enabled
        if self.verbose:
            # Construct the full URL with parameters for display
            if 'params' in kwargs and kwargs['params']:
                param_str = "&".join([f"{k}={v}" for k, v in kwargs['params'].items() if v is not None])
                full_url = f"{url}?{param_str}"
            else:
                full_url = url
            console.print(f"[dim]→ {method} {full_url}[/dim]")
        
        try:
            response = self.session.request(method, url, **kwargs)
            
            # Show response status if verbose mode is enabled
            if self.verbose:
                status_color = "green" if 200 <= response.status_code < 300 else "red"
                console.print(f"[dim]← [{status_color}]{response.status_code}[/{status_color}] {response.reason}[/dim]")
            
            # Handle status codes before raise_for_status() to avoid retry complications
            if response.status_code == 401:
                raise WebamonAPIError("Authentication failed. Check your API key.")
            elif response.status_code == 403:
                if not self.config.api_key:
                    raise WebamonAPIError(
                        "Rate limit exceeded - you've hit the daily quota (20 queries/day for free tier).\n"
                        "Upgrade to Pro for 1,000+ daily queries, larger response sizes, and premium features:\n"
                        "https://webamon.com/pricing"
                    )
                else:
                    raise WebamonAPIError("Access forbidden. Check your permissions.")
            elif response.status_code == 404:
                raise WebamonAPIError("Resource not found.")
            elif response.status_code == 429:
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
            elif not response.ok:
                # Handle other HTTP errors
                try:
                    error_data = response.json()
                    message = error_data.get('message', f"HTTP {response.status_code} error")
                except:
                    message = f"HTTP {response.status_code} error"
                raise WebamonAPIError(f"API error: {message}")
            
            # Handle successful responses
            if response.status_code == 204 or not response.content:
                return {}
                
            return response.json()
            
        except WebamonAPIError:
            # Re-raise our custom errors
            raise
        except requests.exceptions.ConnectionError:
            raise WebamonAPIError("Connection failed. Check your network and API URL.")
        except requests.exceptions.Timeout:
            raise WebamonAPIError("Request timed out.")
        except requests.exceptions.RequestException as e:
            raise WebamonAPIError(f"Request failed: {e}")
    
    def search(self, search_term: str, results: str, size: int = 10, from_offset: int = 0, fields: Optional[str] = None) -> Dict[str, Any]:
        """Perform basic search with pagination support."""
        params = {
            'search': search_term,
            'results': results,
            'size': size
        }
        # Add fields parameter if provided
        if fields:
            params['fields'] = fields
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