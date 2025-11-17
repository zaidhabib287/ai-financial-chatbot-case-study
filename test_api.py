import requests
import json

# Test root endpoint
response = requests.get("http://localhost:8000/")
print("Root endpoint:", json.dumps(response.json(), indent=2))

# Test health endpoint
response = requests.get("http://localhost:8000/health")
print("\nHealth endpoint:", json.dumps(response.json(), indent=2))

# Test API docs availability
response = requests.get("http://localhost:8000/openapi.json")
print("\nAPI Documentation available:", response.status_code == 200)
