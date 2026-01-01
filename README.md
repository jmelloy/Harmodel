# Harmodel

A Python library that uses [haralyzer](https://github.com/haralyzer/haralyzer) to read HAR (HTTP Archive) files and outputs a simple client and Python models for the outputs of API calls.

## Features

- **HAR File Reading**: Parse and analyze HAR files using the haralyzer library
- **Model Generation**: Automatically generate Python dataclass models from JSON API responses
- **Client Generation**: Create a simple HTTP client that can replay requests from HAR files
- **Filtering**: Filter HAR entries by HTTP method, status code, and more

## Installation

```bash
pip install harmodel
```

Or install from source:

```bash
git clone https://github.com/jmelloy/Harmodel.git
cd Harmodel
pip install -e .
```

## Usage

### Basic Example

```python
from harmodel import HarReader, ModelGenerator, ClientGenerator

# Read a HAR file
reader = HarReader("path/to/your/file.har")
reader.load()

# Get API calls
api_calls = reader.get_api_calls()
print(f"Found {len(api_calls)} API calls")

# Generate Python models from responses
model_gen = ModelGenerator(reader)
models = model_gen.generate_from_har_reader()
model_gen.save_models("generated_models.py")

# Generate an HTTP client
client_gen = ClientGenerator(reader)
client_code = client_gen.generate_from_har_reader()
client_gen.save_client("generated_client.py")
```

### Reading HAR Files

```python
from harmodel import HarReader

reader = HarReader("myfile.har")
reader.load()

# Get all entries
entries = reader.get_entries()

# Get all requests
requests = reader.get_requests()

# Get all responses
responses = reader.get_responses()

# Get API calls with request and response pairs
api_calls = reader.get_api_calls()

# Filter by status code
success_calls = reader.filter_by_status(200)

# Filter by HTTP method
get_requests = reader.filter_by_method("GET")
```

### Generating Models

```python
from harmodel import HarReader, ModelGenerator

reader = HarReader("myfile.har")
model_gen = ModelGenerator(reader)

# Generate models from HAR file
models = model_gen.generate_from_har_reader()

# Save to a Python file
model_gen.save_models("models.py")
```

The generated models use Python dataclasses and include type hints:

```python
from typing import Optional, List, Dict, Any
from dataclasses import dataclass


@dataclass
class UsersModel:
    """Model generated from HAR response data."""
    id: int
    name: str
    email: str
    active: bool
```

### Generating Clients

```python
from harmodel import HarReader, ClientGenerator

reader = HarReader("myfile.har")
client_gen = ClientGenerator(reader)

# Generate client code
client_code = client_gen.generate_from_har_reader()

# Save to a Python file
client_gen.save_client("client.py")
```

The generated client can be used to replay requests:

```python
from client import HarClient

# Use with original URLs
client = HarClient()
response = client.get_users()

# Or override the base URL
client = HarClient(base_url="https://staging.api.example.com")
response = client.get_users()
print(response.json())
```

## Example

See the [examples](examples/) directory for a complete example:

```bash
python examples/usage_example.py
```

This will:
1. Read the example HAR file
2. Generate Python models
3. Generate an HTTP client
4. Save both to the `examples/generated/` directory

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/jmelloy/Harmodel.git
cd Harmodel

# Install with development dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Running Tests with Coverage

```bash
pytest --cov=harmodel --cov-report=html
```

## Requirements

- Python 3.8+
- haralyzer >= 2.0.0
- requests >= 2.25.0

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
