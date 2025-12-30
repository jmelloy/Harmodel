"""
Tests for the ClientGenerator class.
"""

import pytest
from harmodel.client import ClientGenerator


def test_client_generator_initialization():
    """Test ClientGenerator initialization."""
    gen = ClientGenerator()
    assert gen.har_reader is None
    assert gen.client_code == ""


def test_generate_method_name():
    """Test method name generation."""
    gen = ClientGenerator()
    
    call = {
        "url": "https://api.example.com/users",
        "method": "GET"
    }
    
    name = gen._generate_method_name(call, 0)
    assert name == "get_users"
    
    call = {
        "url": "https://api.example.com/users",
        "method": "POST"
    }
    
    name = gen._generate_method_name(call, 1)
    assert name == "post_users"


def test_generate_method_name_with_path_segments():
    """Test method name generation with path segments."""
    gen = ClientGenerator()
    
    call = {
        "url": "https://api.example.com/api/v1/users/123",
        "method": "GET"
    }
    
    name = gen._generate_method_name(call, 0)
    assert name == "get_123"


def test_generate_method_name_with_query_params():
    """Test method name generation ignoring query parameters."""
    gen = ClientGenerator()
    
    call = {
        "url": "https://api.example.com/users?page=1&limit=10",
        "method": "GET"
    }
    
    name = gen._generate_method_name(call, 0)
    assert name == "get_users"


def test_generate_client():
    """Test client generation."""
    gen = ClientGenerator()
    
    api_calls = [
        {
            "url": "https://api.example.com/users",
            "method": "GET",
            "request": {
                "method": "GET",
                "url": "https://api.example.com/users",
                "headers": [
                    {"name": "Accept", "value": "application/json"}
                ]
            },
            "response": {
                "status": 200
            }
        }
    ]
    
    client_code = gen.generate_client(api_calls)
    
    assert "class HarClient:" in client_code
    assert "def get_users(" in client_code
    assert "import requests" in client_code
    assert "self.session = requests.Session()" in client_code


def test_generate_client_with_post_data():
    """Test client generation with POST data."""
    gen = ClientGenerator()
    
    api_calls = [
        {
            "url": "https://api.example.com/users",
            "method": "POST",
            "request": {
                "method": "POST",
                "url": "https://api.example.com/users",
                "headers": [
                    {"name": "Content-Type", "value": "application/json"}
                ],
                "postData": {
                    "text": '{"name": "John"}'
                }
            },
            "response": {
                "status": 201
            }
        }
    ]
    
    client_code = gen.generate_client(api_calls)
    
    assert "def post_users(" in client_code
    assert "json_data" in client_code


def test_generate_client_filters_headers():
    """Test that certain headers are filtered out."""
    gen = ClientGenerator()
    
    api_calls = [
        {
            "url": "https://api.example.com/users",
            "method": "GET",
            "request": {
                "method": "GET",
                "url": "https://api.example.com/users",
                "headers": [
                    {"name": "Accept", "value": "application/json"},
                    {"name": "Host", "value": "api.example.com"},
                    {"name": "Content-Length", "value": "123"},
                    {"name": "Connection", "value": "keep-alive"}
                ]
            },
            "response": {
                "status": 200
            }
        }
    ]
    
    client_code = gen.generate_client(api_calls)
    
    # Should include Accept but not Host, Content-Length, Connection
    assert '"Accept"' in client_code
    assert '"Host"' not in client_code
    assert '"Content-Length"' not in client_code
    assert '"Connection"' not in client_code


def test_generate_client_no_duplicate_methods():
    """Test that duplicate methods are not generated."""
    gen = ClientGenerator()
    
    api_calls = [
        {
            "url": "https://api.example.com/users",
            "method": "GET",
            "request": {
                "method": "GET",
                "url": "https://api.example.com/users",
                "headers": []
            },
            "response": {"status": 200}
        },
        {
            "url": "https://api.example.com/users",
            "method": "GET",
            "request": {
                "method": "GET",
                "url": "https://api.example.com/users",
                "headers": []
            },
            "response": {"status": 200}
        }
    ]
    
    client_code = gen.generate_client(api_calls)
    
    # Should only have one definition of get_users
    assert client_code.count("def get_users(") == 1
