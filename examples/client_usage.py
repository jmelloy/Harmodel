"""
Example showing how to use the generated client.

This demonstrates importing and using the generated HarClient.
Note: This is a demonstration - actual API calls would require the API to be available.
"""

import sys
from pathlib import Path

# Add the generated directory to the path
sys.path.insert(0, str(Path(__file__).parent / "generated"))

try:
    from client import HarClient
    
    print("=" * 60)
    print("Generated Client Usage Example")
    print("=" * 60)
    print()
    
    # Create a client instance
    print("1. Creating client with original URLs...")
    client = HarClient()
    print("   Client created successfully")
    print()
    
    # Show available methods
    print("2. Available methods in the generated client:")
    methods = [m for m in dir(client) if not m.startswith('_') and callable(getattr(client, m))]
    for method in methods:
        if method not in ['session']:
            print(f"   - {method}()")
    print()
    
    # Example with base URL override
    print("3. Creating client with custom base URL...")
    staging_client = HarClient(base_url="https://staging.api.example.com")
    print("   Client created with base_url='https://staging.api.example.com'")
    print()
    
    # Show how to use the methods (without actually calling them)
    print("4. Example usage (pseudo-code, not executed):")
    print()
    print("   # Make a GET request")
    print("   response = client.get_users()")
    print("   data = response.json()")
    print()
    print("   # Make a POST request with custom data")
    print("   response = client.post_users(")
    print("       json={'name': 'Bob', 'email': 'bob@example.com'}")
    print("   )")
    print()
    print("   # Override headers")
    print("   response = client.get_users(")
    print("       headers={'Authorization': 'Bearer token123'}")
    print("   )")
    print()
    print("   # Add query parameters")
    print("   response = client.get_users(")
    print("       params={'page': 2, 'limit': 50}")
    print("   )")
    print()
    
    print("=" * 60)
    print("Client Usage Example Complete!")
    print("=" * 60)
    
except ImportError as e:
    print("Error: Could not import generated client.")
    print(f"Details: {e}")
    print()
    print("Please run 'python examples/usage_example.py' first to generate the client.")
