"""
Client generator for creating a simple HTTP client from HAR files.
"""

import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from urllib.parse import urlparse, parse_qs


class ClientGenerator:
    """
    Generates a simple HTTP client from HAR file data.
    
    Creates Python code that can replay HTTP requests from a HAR file.
    """
    
    def __init__(self, har_reader=None):
        """
        Initialize the client generator.
        
        Args:
            har_reader: Optional HarReader instance to use
        """
        self.har_reader = har_reader
        self.client_code = ""
    
    def generate_client(self, api_calls: Optional[List[Dict[str, Any]]] = None) -> str:
        """
        Generate a simple HTTP client from API calls.
        
        Args:
            api_calls: Optional list of API calls. If not provided, uses har_reader.
            
        Returns:
            Python code for the client
        """
        if api_calls is None:
            if self.har_reader is None:
                raise ValueError("No API calls or HarReader provided")
            api_calls = self.har_reader.get_api_calls()
        
        lines = [
            '"""',
            'Generated HTTP client from HAR file.',
            '"""',
            '',
            'import requests',
            'from typing import Dict, Any, Optional',
            '',
            '',
            'class HarClient:',
            '    """Simple HTTP client generated from HAR file data."""',
            '',
            '    def __init__(self, base_url: Optional[str] = None):',
            '        """',
            '        Initialize the client.',
            '        ',
            '        Args:',
            '            base_url: Optional base URL to override the original URLs',
            '        """',
            '        self.base_url = base_url',
            '        self.session = requests.Session()',
            '',
        ]
        
        # Generate methods for each unique endpoint
        endpoints_seen = set()
        
        for idx, call in enumerate(api_calls):
            method_name = self._generate_method_name(call, idx)
            
            # Skip duplicates
            if method_name in endpoints_seen:
                continue
            endpoints_seen.add(method_name)
            
            method_code = self._generate_method(call, method_name)
            lines.extend(method_code)
            lines.append('')
        
        self.client_code = '\n'.join(lines)
        return self.client_code
    
    def _generate_method_name(self, call: Dict[str, Any], index: int) -> str:
        """Generate a method name from the API call."""
        url = call['url']
        method = call['method'].lower()
        
        # Parse URL to get path
        parsed = urlparse(url)
        path = parsed.path.strip('/')
        
        if path:
            # Get last part of path
            parts = path.split('/')
            endpoint = parts[-1] if parts else 'request'
            
            # Clean up the endpoint name
            endpoint = endpoint.split('.')[0]  # Remove extensions
            endpoint = endpoint.split('?')[0]  # Remove query params
            endpoint = endpoint.replace('-', '_').replace(' ', '_')
            
            # Create method name
            method_name = f"{method}_{endpoint}"
        else:
            method_name = f"{method}_request_{index}"
        
        # Ensure valid Python identifier
        if method_name and method_name[0].isdigit():
            method_name = f"call_{method_name}"
        
        return method_name
    
    def _generate_method(self, call: Dict[str, Any], method_name: str) -> List[str]:
        """Generate a single method for an API call."""
        request = call['request']
        method = request['method']
        url = call['url']
        
        # Parse URL components
        parsed = urlparse(url)
        path = parsed.path
        
        # Extract headers
        headers = {}
        for header in request.get('headers', []):
            name = header['name']
            value = header['value']
            # Skip headers that should be set automatically
            if name.lower() not in ['host', 'content-length', 'connection']:
                headers[name] = value
        
        # Extract query parameters
        query_params = parse_qs(parsed.query)
        # Flatten single-value lists
        query_params = {k: v[0] if len(v) == 1 else v for k, v in query_params.items()}
        
        # Extract body
        post_data = request.get('postData', {})
        body_text = post_data.get('text', '')
        
        lines = [
            f'    def {method_name}(self, **kwargs):',
            f'        """',
            f'        {method} {path}',
            f'        ',
            f'        Original URL: {url}',
            f'        """',
            f'        url = self.base_url + "{path}" if self.base_url else "{url}"',
            f'        ',
        ]
        
        # Add headers
        if headers:
            lines.append(f'        headers = {json.dumps(headers, indent=12)[:-1]}        }}')
            lines.append('        headers.update(kwargs.get("headers", {}))')
        else:
            lines.append('        headers = kwargs.get("headers", {})')
        
        lines.append('')
        
        # Add query parameters
        if query_params:
            lines.append(f'        params = {json.dumps(query_params, indent=12)[:-1]}        }}')
            lines.append('        params.update(kwargs.get("params", {}))')
        else:
            lines.append('        params = kwargs.get("params", {})')
        
        lines.append('')
        
        # Add request body
        if body_text:
            try:
                # Try to parse as JSON
                body_json = json.loads(body_text)
                lines.append(f'        json_data = {json.dumps(body_json, indent=12)[:-1]}        }}')
                lines.append('        json_data.update(kwargs.get("json", {}))')
                lines.append('')
                lines.append(f'        response = self.session.request(')
                lines.append(f'            "{method}",')
                lines.append(f'            url,')
                lines.append(f'            headers=headers,')
                lines.append(f'            params=params,')
                lines.append(f'            json=json_data,')
                lines.append(f'        )')
            except json.JSONDecodeError:
                # Use as plain data
                lines.append(f'        data = kwargs.get("data", {json.dumps(body_text)})')
                lines.append('')
                lines.append(f'        response = self.session.request(')
                lines.append(f'            "{method}",')
                lines.append(f'            url,')
                lines.append(f'            headers=headers,')
                lines.append(f'            params=params,')
                lines.append(f'            data=data,')
                lines.append(f'        )')
        else:
            lines.append(f'        response = self.session.request(')
            lines.append(f'            "{method}",')
            lines.append(f'            url,')
            lines.append(f'            headers=headers,')
            lines.append(f'            params=params,')
            lines.append(f'        )')
        
        lines.append('        return response')
        
        return lines
    
    def save_client(self, output_path: Path):
        """
        Save generated client to a Python file.
        
        Args:
            output_path: Path where to save the client file
        """
        output_path = Path(output_path)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(self.client_code)
    
    def generate_from_har_reader(self) -> str:
        """
        Generate client using the associated HarReader.
        
        Returns:
            Generated client code
        """
        if self.har_reader is None:
            raise ValueError("No HarReader instance provided")
        
        return self.generate_client()
