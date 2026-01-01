"""
Client generator for creating a simple HTTP client from HAR files.
"""

import json
import re
from typing import Dict, Any, List, Optional
from pathlib import Path
from urllib.parse import urlparse, parse_qs


class ClientGenerator:
    """
    Generates a simple HTTP client from HAR file data.
    
    Creates Python code that can replay HTTP requests from a HAR file.
    """
    
    def __init__(self, har_reader=None, model_generator=None):
        """
        Initialize the client generator.
        
        Args:
            har_reader: Optional HarReader instance to use
            model_generator: Optional ModelGenerator instance for type hints
        """
        self.har_reader = har_reader
        self.model_generator = model_generator
        self.client_code = ""
    
    def generate_client(self, api_calls: Optional[List[Dict[str, Any]]] = None, use_models: bool = False) -> str:
        """
        Generate a simple HTTP client from API calls.
        
        Args:
            api_calls: Optional list of API calls. If not provided, uses har_reader.
            use_models: Whether to include model type hints in the generated client
            
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
        ]
        
        # Add model imports if using models
        if use_models and self.model_generator:
            lines.append('# Import generated models for type hints')
            lines.append('try:')
            lines.append('    from .models import *')
            lines.append('except ImportError:')
            lines.append('    pass  # Models not available')
            lines.append('')
        
        lines.extend([
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
        ])
        
        # Group API calls by method name to combine headers
        endpoint_calls: Dict[str, List[Dict[str, Any]]] = {}
        
        for idx, call in enumerate(api_calls):
            method_name = self._generate_method_name(call, idx)
            if method_name not in endpoint_calls:
                endpoint_calls[method_name] = []
            endpoint_calls[method_name].append(call)
        
        # Generate methods for each unique endpoint, combining headers
        for method_name, calls in endpoint_calls.items():
            # Get model name if using models
            model_name = None
            if use_models and self.model_generator:
                model_name = self._get_model_name_for_call(calls[0])
            
            method_code = self._generate_method(calls[0], method_name, calls, model_name)
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
            
            # Remove special characters like @, #, %, etc. - keep only alphanumeric and underscore
            endpoint = re.sub(r'[^a-zA-Z0-9_]', '_', endpoint)
            
            # Remove consecutive underscores
            endpoint = re.sub(r'_+', '_', endpoint)
            
            # Strip leading/trailing underscores
            endpoint = endpoint.strip('_')
            
            # Create method name
            method_name = f"{method}_{endpoint}"
        else:
            method_name = f"{method}_request_{index}"
        
        # Ensure valid Python identifier
        if method_name and method_name[0].isdigit():
            method_name = f"call_{method_name}"
        
        return method_name
    
    def _generate_method(self, call: Dict[str, Any], method_name: str, all_calls: Optional[List[Dict[str, Any]]] = None, model_name: Optional[str] = None) -> List[str]:
        """Generate a single method for an API call, optionally combining headers from multiple calls."""
        if all_calls is None:
            all_calls = [call]
            
        request = call['request']
        method = request['method']
        url = call['url']
        
        # Parse URL components
        parsed = urlparse(url)
        path = parsed.path
        
        # Combine headers from all calls to this endpoint
        combined_headers = {}
        for c in all_calls:
            for header in c['request'].get('headers', []):
                name = header['name']
                value = header['value']
                # Skip headers that should be set automatically
                if name.lower() not in ['host', 'content-length', 'connection']:
                    # Keep the first value for each header
                    if name not in combined_headers:
                        combined_headers[name] = value
        
        # Extract query parameters
        query_params = parse_qs(parsed.query)
        # Flatten single-value lists
        query_params = {k: v[0] if len(v) == 1 else v for k, v in query_params.items()}
        
        # Extract body
        post_data = request.get('postData', {})
        body_text = post_data.get('text', '')
        
        # Determine return type
        return_type = f" -> {model_name}" if model_name else ""
        
        lines = [
            f'    def {method_name}(self, **kwargs){return_type}:',
            f'        """',
            f'        {method} {path}',
            f'        ',
            f'        Original URL: {url}',
            f'        """',
            f'        url = self.base_url + "{path}" if self.base_url else "{url}"',
            f'        ',
        ]
        
        # Add headers
        if combined_headers:
            lines.append(f'        headers = {repr(combined_headers)}')
            lines.append('        headers.update(kwargs.get("headers", {}))')
        else:
            lines.append('        headers = kwargs.get("headers", {})')
        
        lines.append('')
        
        # Add query parameters
        if query_params:
            lines.append(f'        params = {repr(query_params)}')
            lines.append('        params.update(kwargs.get("params", {}))')
        else:
            lines.append('        params = kwargs.get("params", {})')
        
        lines.append('')
        
        # Add request body
        if body_text:
            try:
                # Try to parse as JSON
                body_json = json.loads(body_text)
                lines.append(f'        json_data = {repr(body_json)}')
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
    
    def _get_model_name_for_call(self, call: Dict[str, Any]) -> Optional[str]:
        """Get the model name for an API call from the model generator."""
        if not self.model_generator:
            return None
        
        url = call['url']
        # The model generator uses URL as the key in its models dict
        if url in self.model_generator.models:
            # Extract the model class name from the generated model code
            model_code = self.model_generator.models[url]
            # Look for "class ModelName:" pattern
            import re
            match = re.search(r'class\s+(\w+):', model_code)
            if match:
                return match.group(1)
        
        return None
    
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
