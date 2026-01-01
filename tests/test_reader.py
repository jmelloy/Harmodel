"""
Tests for the HarReader class.
"""

import json
import pytest
from pathlib import Path
from harmodel.reader import HarReader


@pytest.fixture
def sample_har_file(tmp_path):
    """Create a sample HAR file for testing."""
    har_data = {
        "log": {
            "version": "1.2",
            "creator": {"name": "Test", "version": "1.0"},
            "entries": [
                {
                    "request": {
                        "method": "GET",
                        "url": "https://api.test.com/users",
                        "headers": [],
                        "queryString": [],
                    },
                    "response": {
                        "status": 200,
                        "content": {
                            "text": '{"users": []}'
                        }
                    }
                },
                {
                    "request": {
                        "method": "POST",
                        "url": "https://api.test.com/users",
                        "headers": [],
                        "queryString": [],
                    },
                    "response": {
                        "status": 201,
                        "content": {
                            "text": '{"id": 1}'
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


def test_har_reader_initialization(sample_har_file):
    """Test HarReader initialization."""
    reader = HarReader(sample_har_file)
    assert reader.har_path == sample_har_file
    assert reader._har_data is None
    assert reader._parser is None


def test_har_reader_load(sample_har_file):
    """Test loading a HAR file."""
    reader = HarReader(sample_har_file)
    reader.load()
    
    assert reader._har_data is not None
    assert reader._parser is not None
    assert "log" in reader._har_data


def test_get_entries(sample_har_file):
    """Test getting entries from HAR file."""
    reader = HarReader(sample_har_file)
    reader.load()
    
    entries = reader.get_entries()
    assert len(entries) == 2
    assert entries[0]['request']['method'] == 'GET'
    assert entries[1]['request']['method'] == 'POST'


def test_get_requests(sample_har_file):
    """Test getting requests from HAR file."""
    reader = HarReader(sample_har_file)
    reader.load()
    
    requests = reader.get_requests()
    assert len(requests) == 2
    assert all('method' in req for req in requests)


def test_get_responses(sample_har_file):
    """Test getting responses from HAR file."""
    reader = HarReader(sample_har_file)
    reader.load()
    
    responses = reader.get_responses()
    assert len(responses) == 2
    assert all('status' in resp for resp in responses)


def test_get_api_calls(sample_har_file):
    """Test getting API calls."""
    reader = HarReader(sample_har_file)
    reader.load()
    
    api_calls = reader.get_api_calls()
    assert len(api_calls) == 2
    assert all('url' in call for call in api_calls)
    assert all('method' in call for call in api_calls)
    assert all('request' in call for call in api_calls)
    assert all('response' in call for call in api_calls)


def test_filter_by_status(sample_har_file):
    """Test filtering entries by status code."""
    reader = HarReader(sample_har_file)
    reader.load()
    
    entries_200 = reader.filter_by_status(200)
    assert len(entries_200) == 1
    assert entries_200[0]['response']['status'] == 200
    
    entries_201 = reader.filter_by_status(201)
    assert len(entries_201) == 1
    assert entries_201[0]['response']['status'] == 201


def test_filter_by_method(sample_har_file):
    """Test filtering entries by HTTP method."""
    reader = HarReader(sample_har_file)
    reader.load()
    
    get_entries = reader.filter_by_method('GET')
    assert len(get_entries) == 1
    assert get_entries[0]['request']['method'] == 'GET'
    
    post_entries = reader.filter_by_method('POST')
    assert len(post_entries) == 1
    assert post_entries[0]['request']['method'] == 'POST'


def test_lazy_loading(sample_har_file):
    """Test that parser is loaded lazily."""
    reader = HarReader(sample_har_file)
    
    # Parser should be loaded on first access
    parser = reader.parser
    assert parser is not None
    assert reader._parser is not None
