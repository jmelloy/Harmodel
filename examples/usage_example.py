"""
Example usage of the Harmodel library.

This script demonstrates how to:
1. Read a HAR file
2. Generate Python models from API responses
3. Generate a simple HTTP client
"""

from pathlib import Path
from harmodel import HarReader, ModelGenerator, ClientGenerator


def main():
    # Path to the example HAR file
    har_file = Path(__file__).parent / "example.har"
    
    print("=" * 60)
    print("Harmodel Example Usage")
    print("=" * 60)
    print()
    
    # 1. Read the HAR file
    print("1. Reading HAR file...")
    reader = HarReader(har_file)
    reader.load()
    
    entries = reader.get_entries()
    print(f"   Found {len(entries)} HTTP entries")
    
    api_calls = reader.get_api_calls()
    print(f"   Found {len(api_calls)} API calls")
    print()
    
    # Show some details
    for i, call in enumerate(api_calls, 1):
        print(f"   Call {i}: {call['method']} {call['url']}")
        print(f"           Status: {call['response']['status']}")
    print()
    
    # 2. Generate models
    print("2. Generating Python models from responses...")
    model_gen = ModelGenerator(reader)
    models = model_gen.generate_from_har_reader()
    
    print(f"   Generated {len(models)} models")
    
    # Save models to file
    output_dir = Path(__file__).parent / "generated"
    output_dir.mkdir(exist_ok=True)
    
    models_file = output_dir / "models.py"
    model_gen.save_models(models_file)
    print(f"   Saved models to: {models_file}")
    print()
    
    # 3. Generate client
    print("3. Generating HTTP client...")
    client_gen = ClientGenerator(reader)
    client_code = client_gen.generate_from_har_reader()
    
    # Save client to file
    client_file = output_dir / "client.py"
    client_gen.save_client(client_file)
    print(f"   Saved client to: {client_file}")
    print()
    
    # Show a preview of the generated client
    print("=" * 60)
    print("Preview of Generated Client")
    print("=" * 60)
    lines = client_code.split('\n')
    for line in lines[:30]:  # Show first 30 lines
        print(line)
    print("...")
    print()
    
    print("=" * 60)
    print("Example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
