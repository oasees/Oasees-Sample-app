import requests

# Send POST request to force metrics
# Change localhost:50000 to the actual endpoint
response = requests.post(
    'http://localhost:5000/force_metrics',
    json={
        'value': 42.5,
        'duration': 60
    }
)

print(response.json())
