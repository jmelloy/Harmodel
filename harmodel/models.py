"""
Model generator for creating Python data models from HAR responses.
"""

import json
from typing import Dict, Any, List, Set, Optional
from pathlib import Path


class ModelGenerator:
    """
    Generates Python data models from HTTP response data in HAR files.
    
    Analyzes JSON responses and creates Pydantic-compatible model classes.
    """
    
    def __init__(self, har_reader=None):
        """
        Initialize the model generator.
        
        Args:
            har_reader: Optional HarReader instance to use
        """
        self.har_reader = har_reader
        self.models: Dict[str, str] = {}
    
    def analyze_json_structure(self, data: Any, model_name: str = "Response") -> str:
        """
        Analyze JSON structure and generate a Python model.
        
        Args:
            data: JSON data to analyze
            model_name: Name for the generated model class
            
        Returns:
            Python code for the model class
        """
        if isinstance(data, dict):
            return self._generate_dict_model(data, model_name)
        elif isinstance(data, list) and len(data) > 0:
            return self._generate_list_model(data, model_name)
        else:
            return f"# Simple type: {type(data).__name__}"
    
    def _generate_dict_model(self, data: Dict[str, Any], model_name: str) -> str:
        """Generate a model for a dictionary structure."""
        lines = [
            "from typing import Optional, List, Dict, Any",
            "from dataclasses import dataclass",
            "",
            "",
            "@dataclass",
            f"class {model_name}:",
            f'    """Model generated from HAR response data."""',
        ]
        
        if not data:
            lines.append("    pass")
            return "\n".join(lines)
        
        # Analyze fields
        for key, value in data.items():
            python_key = self._sanitize_field_name(key)
            type_hint = self._infer_type(value, key)
            lines.append(f"    {python_key}: {type_hint}")
        
        return "\n".join(lines)
    
    def _generate_list_model(self, data: List[Any], model_name: str) -> str:
        """Generate a model for a list structure."""
        if not data:
            return f"# {model_name} is an empty list"
        
        # Take the first item as representative
        first_item = data[0]
        if isinstance(first_item, dict):
            item_model = self._generate_dict_model(first_item, f"{model_name}Item")
            return item_model + f"\n\n# {model_name} = List[{model_name}Item]"
        else:
            item_type = self._infer_type(first_item, "item")
            return f"# {model_name} = List[{item_type}]"
    
    def _sanitize_field_name(self, name: str) -> str:
        """Sanitize field name to be valid Python identifier."""
        # Replace invalid characters
        sanitized = name.replace("-", "_").replace(".", "_").replace(" ", "_")
        
        # If starts with number, prefix with underscore
        if sanitized and sanitized[0].isdigit():
            sanitized = "_" + sanitized
        
        # Handle Python keywords
        keywords = {'class', 'def', 'return', 'if', 'else', 'for', 'while', 'import', 'from', 'as', 'is'}
        if sanitized.lower() in keywords:
            sanitized = sanitized + "_"
        
        return sanitized
    
    def _infer_type(self, value: Any, field_name: str) -> str:
        """Infer Python type hint from value."""
        if value is None:
            return "Optional[Any]"
        elif isinstance(value, bool):
            return "bool"
        elif isinstance(value, int):
            return "int"
        elif isinstance(value, float):
            return "float"
        elif isinstance(value, str):
            return "str"
        elif isinstance(value, list):
            if len(value) == 0:
                return "List[Any]"
            # Check first item
            first_type = self._infer_type(value[0], field_name)
            return f"List[{first_type}]"
        elif isinstance(value, dict):
            # For nested objects, use Dict or create nested model
            return "Dict[str, Any]"
        else:
            return "Any"
    
    def generate_models_from_responses(self, api_calls: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Generate models from API call responses.
        
        Args:
            api_calls: List of API call data from HarReader
            
        Returns:
            Dictionary mapping endpoint paths to model code
        """
        models = {}
        
        for idx, call in enumerate(api_calls):
            response = call['response']
            
            # Try to parse response content as JSON
            try:
                content = response.get('content', {})
                text = content.get('text', '')
                
                if text:
                    data = json.loads(text)
                    
                    # Generate a model name from the URL
                    url = call['url']
                    model_name = self._url_to_model_name(url, idx)
                    
                    model_code = self.analyze_json_structure(data, model_name)
                    models[url] = model_code
            except (json.JSONDecodeError, KeyError):
                # Skip non-JSON responses
                continue
        
        self.models = models
        return models
    
    def _url_to_model_name(self, url: str, index: int) -> str:
        """Convert URL to a valid model name."""
        # Extract path from URL
        from urllib.parse import urlparse
        
        parsed = urlparse(url)
        path = parsed.path.strip('/')
        
        # Convert to PascalCase
        if path:
            parts = path.split('/')
            # Take last meaningful part
            name_part = parts[-1] if parts else f"Response{index}"
            # Remove query parameters and file extensions
            name_part = name_part.split('?')[0].split('.')[0]
            # Convert to PascalCase
            words = name_part.replace('_', ' ').replace('-', ' ').split()
            model_name = ''.join(word.capitalize() for word in words if word)
            
            if not model_name or model_name[0].isdigit():
                model_name = f"Response{index}"
        else:
            model_name = f"Response{index}"
        
        return model_name + "Model"
    
    def save_models(self, output_path: Path):
        """
        Save generated models to a Python file.
        
        Args:
            output_path: Path where to save the models file
        """
        output_path = Path(output_path)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('"""\nGenerated models from HAR file analysis.\n"""\n\n')
            
            for url, model_code in self.models.items():
                f.write(f"# Model for: {url}\n")
                f.write(model_code)
                f.write("\n\n\n")
    
    def generate_from_har_reader(self) -> Dict[str, str]:
        """
        Generate models using the associated HarReader.
        
        Returns:
            Dictionary of generated models
        """
        if self.har_reader is None:
            raise ValueError("No HarReader instance provided")
        
        api_calls = self.har_reader.get_api_calls()
        return self.generate_models_from_responses(api_calls)
