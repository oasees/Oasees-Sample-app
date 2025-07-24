import requests
import numpy as np

data = np.load('iris_data.npy')
node_ip = ""
model_port = ""
response = requests.post(f'http://{node_ip}:{model_port}/predict', 
                json={'data': data.tolist()})
y_pred = response.json()['predictions']


y_true = np.load('iris_target.npy')


accuracy = sum(1 for true, pred in zip(y_true, y_pred) if true == pred) / len(y_true)
print(f"Accuracy: {accuracy:.4f}")
print(y_pred)
