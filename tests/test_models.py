"""
Tests for the ModelGenerator class.
"""

import pytest
from harmodel.models import ModelGenerator


def test_model_generator_initialization():
    """Test ModelGenerator initialization."""
    gen = ModelGenerator()
    assert gen.har_reader is None
    assert gen.models == {}


def test_sanitize_field_name():
    """Test field name sanitization."""
    gen = ModelGenerator()
    
    # Normal field
    assert gen._sanitize_field_name("name") == "name"
    
    # Field with hyphens
    assert gen._sanitize_field_name("first-name") == "first_name"
    
    # Field starting with number
    assert gen._sanitize_field_name("1st_place") == "_1st_place"
    
    # Python keyword
    assert gen._sanitize_field_name("class") == "class_"


def test_infer_type():
    """Test type inference."""
    gen = ModelGenerator()
    
    assert gen._infer_type(None, "field") == "Optional[Any]"
    assert gen._infer_type(True, "field") == "bool"
    assert gen._infer_type(42, "field") == "int"
    assert gen._infer_type(3.14, "field") == "float"
    assert gen._infer_type("hello", "field") == "str"
    assert gen._infer_type([], "field") == "List[Any]"
    assert gen._infer_type([1, 2, 3], "field") == "List[int]"
    assert gen._infer_type({}, "field") == "Dict[str, Any]"


def test_analyze_json_structure_dict():
    """Test analyzing a dictionary structure."""
    gen = ModelGenerator()
    
    data = {
        "id": 1,
        "name": "John",
        "active": True
    }
    
    model = gen.analyze_json_structure(data, "User")
    
    assert "class User:" in model
    assert "@dataclass" in model
    assert "id: int" in model
    assert "name: str" in model
    assert "active: bool" in model


def test_analyze_json_structure_list():
    """Test analyzing a list structure."""
    gen = ModelGenerator()
    
    data = [
        {"id": 1, "name": "John"},
        {"id": 2, "name": "Jane"}
    ]
    
    model = gen.analyze_json_structure(data, "Users")
    
    assert "class UsersItem:" in model
    assert "id: int" in model
    assert "name: str" in model


def test_analyze_json_structure_empty_dict():
    """Test analyzing an empty dictionary."""
    gen = ModelGenerator()
    
    model = gen.analyze_json_structure({}, "Empty")
    
    assert "class Empty:" in model
    assert "pass" in model


def test_url_to_model_name():
    """Test URL to model name conversion."""
    gen = ModelGenerator()
    
    # Simple path
    name = gen._url_to_model_name("https://api.example.com/users", 0)
    assert name == "UsersModel"
    
    # Path with multiple segments
    name = gen._url_to_model_name("https://api.example.com/api/v1/users", 1)
    assert name == "UsersModel"
    
    # Path with query parameters
    name = gen._url_to_model_name("https://api.example.com/users?page=1", 2)
    assert name == "UsersModel"
    
    # Empty path
    name = gen._url_to_model_name("https://api.example.com/", 3)
    assert name == "Response3Model"
    
    # Path with special characters like @
    name = gen._url_to_model_name("https://api.example.com/user@email", 4)
    assert name == "UserEmailModel"
    assert "@" not in name


def test_generate_models_from_responses():
    """Test generating models from API responses."""
    gen = ModelGenerator()
    
    api_calls = [
        {
            "url": "https://api.example.com/users",
            "method": "GET",
            "response": {
                "content": {
                    "text": '{"id": 1, "name": "John"}'
                }
            }
        }
    ]
    
    models = gen.generate_models_from_responses(api_calls)
    
    assert len(models) == 1
    assert "https://api.example.com/users" in models
    assert "class UsersModel:" in models["https://api.example.com/users"]


def test_generate_models_skip_non_json():
    """Test that non-JSON responses are skipped."""
    gen = ModelGenerator()
    
    api_calls = [
        {
            "url": "https://api.example.com/page",
            "method": "GET",
            "response": {
                "content": {
                    "text": '<html>Not JSON</html>'
                }
            }
        }
    ]
    
    models = gen.generate_models_from_responses(api_calls)
    
    # Should skip non-JSON responses
    assert len(models) == 0
