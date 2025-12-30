"""
Integration tests for the complete Harmodel workflow.
"""

import json
import tempfile
from pathlib import Path
import pytest
from harmodel import HarReader, ModelGenerator, ClientGenerator


@pytest.fixture
def complete_har_file(tmp_path):
    """Create a complete HAR file with various scenarios."""
    har_data = {
        "log": {
            "version": "1.2",
            "creator": {"name": "Test", "version": "1.0"},
            "entries": [
                {
                    "request": {
                        "method": "GET",
                        "url": "https://api.test.com/users",
                        "headers": [
                            {"name": "Accept", "value": "application/json"}
                        ],
                        "queryString": [
                            {"name": "page", "value": "1"}
                        ],
                    },
                    "response": {
                        "status": 200,
                        "content": {
                            "text": json.dumps([
                                {"id": 1, "name": "John", "email": "john@test.com"},
                                {"id": 2, "name": "Jane", "email": "jane@test.com"}
                            ])
                        }
                    }
                },
                {
                    "request": {
                        "method": "POST",
                        "url": "https://api.test.com/users",
                        "headers": [
                            {"name": "Content-Type", "value": "application/json"}
                        ],
                        "postData": {
                            "text": json.dumps({"name": "Alice", "email": "alice@test.com"})
                        }
                    },
                    "response": {
                        "status": 201,
                        "content": {
                            "text": json.dumps({"id": 3, "name": "Alice", "email": "alice@test.com"})
                        }
                    }
                }
            ]
        }
    }
    
    har_file = tmp_path / "test.har"
    with open(har_file, 'w') as f:
        json.dump(har_data, f)
    
    return har_file


def test_complete_workflow(complete_har_file, tmp_path):
    """Test the complete workflow from HAR file to generated code."""
    # 1. Read HAR file
    reader = HarReader(complete_har_file)
    reader.load()
    
    api_calls = reader.get_api_calls()
    assert len(api_calls) == 2
    
    # 2. Generate models
    model_gen = ModelGenerator(reader)
    models = model_gen.generate_from_har_reader()
    
    # Both URLs point to the same endpoint, so only one model is generated
    # (the second one overwrites the first)
    assert len(models) >= 1
    assert "https://api.test.com/users" in models
    
    # Check that the model contains expected fields
    users_model = models["https://api.test.com/users"]
    # The model could be for a list or single item depending on which was last
    assert ("class UsersModel:" in users_model or "class UsersItemModel:" in users_model)
    assert "id: int" in users_model
    assert "name: str" in users_model
    assert "email: str" in users_model
    
    # 3. Save models
    models_file = tmp_path / "models.py"
    model_gen.save_models(models_file)
    
    assert models_file.exists()
    content = models_file.read_text()
    assert "from dataclasses import dataclass" in content
    
    # 4. Generate client
    client_gen = ClientGenerator(reader)
    client_code = client_gen.generate_from_har_reader()
    
    assert "class HarClient:" in client_code
    assert "def get_users(" in client_code
    assert "def post_users(" in client_code
    
    # 5. Save client
    client_file = tmp_path / "client.py"
    client_gen.save_client(client_file)
    
    assert client_file.exists()
    content = client_file.read_text()
    assert "import requests" in content
    assert "self.session = requests.Session()" in content


def test_filtering_workflow(complete_har_file):
    """Test filtering functionality in the workflow."""
    reader = HarReader(complete_har_file)
    reader.load()
    
    # Filter by method
    get_requests = reader.filter_by_method("GET")
    assert len(get_requests) == 1
    assert get_requests[0]['request']['method'] == "GET"
    
    post_requests = reader.filter_by_method("POST")
    assert len(post_requests) == 1
    assert post_requests[0]['request']['method'] == "POST"
    
    # Filter by status
    status_200 = reader.filter_by_status(200)
    assert len(status_200) == 1
    
    status_201 = reader.filter_by_status(201)
    assert len(status_201) == 1


def test_client_generation_with_complex_data(complete_har_file):
    """Test that generated client includes all necessary data."""
    reader = HarReader(complete_har_file)
    reader.load()
    
    client_gen = ClientGenerator(reader)
    client_code = client_gen.generate_from_har_reader()
    
    # Check for query parameters
    assert "params" in client_code
    
    # Check for headers
    assert "headers" in client_code
    
    # Check for POST data
    assert "json_data" in client_code
    
    # Check for flexible overriding
    assert "kwargs.get" in client_code
    assert "update(" in client_code
