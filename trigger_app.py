import requests
import json

# Send message to multiple sensors
response = requests.post(
    'http://10.160.1.227:32687/send_message',
    headers={'Content-Type': 'application/json'},
    json={
        "target_sensors": ["vibration-sensor", "pressure-sensor", "flow-sensor"],
        "action": "emergency", 
        "duration": 5
    }
)

print(response.text)
# Print the response
# print("Status Code:", response.status_code)
# print("Response:")
# print(json.dumps(response.json(), indent=2))