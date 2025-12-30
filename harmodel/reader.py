"""
HAR file reader using haralyzer library.
"""

import json
from pathlib import Path
from typing import Union, Dict, Any, List
from haralyzer import HarParser


class HarReader:
    """
    Reader for HAR (HTTP Archive) files.
    
    Uses haralyzer to parse and analyze HAR files, providing access to
    HTTP requests and responses.
    """
    
    def __init__(self, har_path: Union[str, Path]):
        """
        Initialize the HAR reader with a path to a HAR file.
        
        Args:
            har_path: Path to the HAR file to read
        """
        self.har_path = Path(har_path)
        self._har_data = None
        self._parser = None
        
    def load(self) -> 'HarReader':
        """
        Load and parse the HAR file.
        
        Returns:
            Self for method chaining
        """
        with open(self.har_path, 'r', encoding='utf-8') as f:
            self._har_data = json.load(f)
        
        self._parser = HarParser(self._har_data)
        return self
    
    @property
    def parser(self) -> HarParser:
        """Get the HarParser instance."""
        if self._parser is None:
            self.load()
        return self._parser
    
    def get_entries(self) -> List[Any]:
        """
        Get all HTTP entries from the HAR file.
        
        Returns:
            List of HAR entries containing request/response data
        """
        return self.parser.har_data.get('entries', [])
    
    def get_requests(self) -> List[Dict[str, Any]]:
        """
        Get all HTTP requests from the HAR file.
        
        Returns:
            List of request data dictionaries
        """
        return [entry['request'] for entry in self.get_entries()]
    
    def get_responses(self) -> List[Dict[str, Any]]:
        """
        Get all HTTP responses from the HAR file.
        
        Returns:
            List of response data dictionaries
        """
        return [entry['response'] for entry in self.get_entries()]
    
    def get_api_calls(self) -> List[Dict[str, Any]]:
        """
        Get API calls with both request and response data.
        
        Returns:
            List of dictionaries containing url, method, request, and response
        """
        api_calls = []
        for entry in self.get_entries():
            request = entry['request']
            response = entry['response']
            
            api_call = {
                'url': request['url'],
                'method': request['method'],
                'request': request,
                'response': response,
            }
            api_calls.append(api_call)
        
        return api_calls
    
    def filter_by_status(self, status_code: int) -> List[Dict[str, Any]]:
        """
        Filter entries by HTTP status code.
        
        Args:
            status_code: HTTP status code to filter by
            
        Returns:
            List of entries with the specified status code
        """
        return [
            entry for entry in self.get_entries()
            if entry['response']['status'] == status_code
        ]
    
    def filter_by_method(self, method: str) -> List[Dict[str, Any]]:
        """
        Filter entries by HTTP method.
        
        Args:
            method: HTTP method to filter by (e.g., 'GET', 'POST')
            
        Returns:
            List of entries with the specified method
        """
        return [
            entry for entry in self.get_entries()
            if entry['request']['method'].upper() == method.upper()
        ]
