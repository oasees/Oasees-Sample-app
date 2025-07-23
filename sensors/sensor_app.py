from flask import Flask, jsonify, request
import os
import random
import time
from datetime import datetime, timedelta
import threading
import requests

app = Flask(__name__)

# Configuration from environment variables
SENSOR_TYPE = os.environ.get('SENSOR_TYPE', 'generic')
SENSOR_NAME = os.environ.get('SENSOR_NAME', 'Generic Sensor')
PORT = int(os.environ.get('PORT', 5000))

# System stability goal - sensors work together to maintain this
system_mode = "normal"  # normal, cooling, reducing, emergency
mode_end_time = None
received_messages = []

# Iris dataset - using actual values for realistic sensor data
IRIS_DATA = {
    'sepal_length': [5.1, 4.9, 4.7, 4.6, 5.0, 5.4, 4.6, 5.0, 4.4, 4.9, 5.4, 4.8, 4.8, 4.3, 5.8, 5.7, 5.4, 5.1, 5.7, 5.1, 5.4, 5.1, 4.6, 5.1, 4.8, 5.0, 5.0, 5.2, 5.2, 4.7, 4.8, 5.4, 5.2, 5.5, 4.9, 5.0, 5.5, 4.9, 4.4, 5.1, 5.0, 4.5, 4.4, 5.0, 5.1, 4.8, 5.1, 4.6, 5.3, 5.0],
    'sepal_width': [3.5, 3.0, 3.2, 3.1, 3.6, 3.9, 3.4, 3.4, 2.9, 3.1, 3.7, 3.4, 3.0, 3.0, 4.0, 4.4, 3.9, 3.5, 3.8, 3.8, 3.4, 3.7, 3.6, 3.3, 3.4, 3.0, 3.4, 3.5, 3.4, 3.2, 3.1, 3.4, 4.1, 4.2, 3.1, 3.2, 3.5, 3.6, 3.0, 3.4, 3.5, 2.3, 3.2, 3.5, 3.8, 3.0, 3.8, 3.2, 3.7, 3.3],
    'petal_length': [1.4, 1.4, 1.3, 1.5, 1.4, 1.7, 1.4, 1.5, 1.4, 1.5, 1.5, 1.6, 1.4, 1.1, 1.2, 1.5, 1.3, 1.4, 1.7, 1.5, 1.7, 1.5, 1.0, 1.7, 1.9, 1.6, 1.6, 1.5, 1.4, 1.6, 1.6, 1.5, 1.5, 1.4, 1.5, 1.2, 1.3, 1.4, 1.3, 1.5, 1.3, 1.3, 1.3, 1.6, 1.9, 1.4, 1.6, 1.4, 1.5, 1.4],
    'petal_width': [0.2, 0.2, 0.2, 0.2, 0.2, 0.4, 0.3, 0.2, 0.2, 0.1, 0.2, 0.2, 0.1, 0.1, 0.2, 0.4, 0.4, 0.3, 0.3, 0.3, 0.2, 0.4, 0.2, 0.5, 0.2, 0.2, 0.4, 0.2, 0.2, 0.2, 0.2, 0.4, 0.1, 0.2, 0.2, 0.2, 0.2, 0.1, 0.2, 0.2, 0.3, 0.3, 0.2, 0.6, 0.4, 0.3, 0.2, 0.2, 0.2, 0.2]
}

# Sensor data storage
sensor_data = {
    'value': 0,
    'timestamp': None,
    'status': 'online',
    'readings_count': 0
}

# Force standard metrics storage
force_metrics = {
    'active': False,
    'value': 0,
    'end_time': None
}

def generate_sensor_value():
    """Generate sensor values from iris dataset based on sensor type and system mode"""
    global system_mode, mode_end_time
    
    # Check if mode has expired
    if mode_end_time and datetime.now() > mode_end_time:
        system_mode = "normal"
        mode_end_time = None
    
    if SENSOR_TYPE == 'vibration':
        base_value = random.choice(IRIS_DATA['sepal_length'])
        value = base_value * 2.5
        # Adjust based on system mode
        if system_mode == "cooling":
            value = value * 0.8  # Reduce vibration when cooling
        elif system_mode == "reducing":
            value = value * 0.6  # Further reduce when in reducing mode
        return round(value, 2)
        
    elif SENSOR_TYPE == 'thermal':
        base_value = random.choice(IRIS_DATA['sepal_width'])
        value = base_value * 8 + 45
        # Adjust based on system mode
        if system_mode == "cooling":
            value = value - 10  # Reduce temperature when cooling
        elif system_mode == "emergency":
            value = value + 15  # Increase in emergency mode
        return round(value, 2)
        
    elif SENSOR_TYPE == 'pressure':
        base_value = random.choice(IRIS_DATA['petal_length'])
        value = base_value * 25 + 10
        # Adjust based on system mode
        if system_mode == "reducing":
            value = value * 0.7  # Reduce pressure
        elif system_mode == "emergency":
            value = value * 1.3  # Increase in emergency
        return round(value, 2)
        
    elif SENSOR_TYPE == 'flow':
        base_value = random.choice(IRIS_DATA['petal_width'])
        value = base_value * 50 + 15
        # Adjust based on system mode
        if system_mode == "reducing":
            value = value * 0.5  # Reduce flow rate
        elif system_mode == "cooling":
            value = value * 1.2  # Increase flow for cooling
        return round(value, 2)
    else:
        return round(random.uniform(0.0, 100.0), 2)

def get_unit():
    """Get the unit for the sensor type"""
    units = {
        'vibration': 'mm/s',
        'thermal': '°C',
        'pressure': 'bar',
        'flow': 'L/min'
    }
    return units.get(SENSOR_TYPE, 'units')

def get_current_value():
    """Get the current sensor value, considering force metrics"""
    if force_metrics['active'] and datetime.now() < force_metrics['end_time']:
        return force_metrics['value']
    else:
        # Reset force metrics if time has expired
        if force_metrics['active']:
            force_metrics['active'] = False
            force_metrics['end_time'] = None
        return sensor_data['value']

def update_sensor_data():
    """Background thread to continuously update sensor data"""
    while True:
        sensor_data['value'] = generate_sensor_value()
        sensor_data['timestamp'] = datetime.now().isoformat()
        sensor_data['readings_count'] += 1
        time.sleep(2)  # Update every 2 seconds

# Start background thread for sensor updates
sensor_thread = threading.Thread(target=update_sensor_data, daemon=True)
sensor_thread.start()

@app.route('/')
def home():
    """Basic info about the sensor"""
    return jsonify({
        'sensor_name': SENSOR_NAME,
        'sensor_type': SENSOR_TYPE,
        'status': 'online',
        'system_mode': system_mode,
        'endpoints': {
            'metrics': '/metrics',
            'health': '/health',
            'force_metrics': '/force_metrics',
            'send_message': '/send_message'
        }
    })

@app.route('/metrics')
def metrics():
    """Main metrics endpoint"""
    current_value = get_current_value()
    return jsonify({
        'sensor_name': SENSOR_NAME,
        'sensor_type': SENSOR_TYPE,
        SENSOR_TYPE+'_value': current_value,
        'unit': get_unit(),
        'readings_count': sensor_data['readings_count'],
        'status': sensor_data['status'],
        'forced_metrics': force_metrics['active'],
        'system_mode': system_mode,
        'messages_received': len(received_messages)
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'uptime': sensor_data['readings_count'] * 2,
        'last_reading': sensor_data['timestamp'],
        'system_mode': system_mode
    })

@app.route('/force_metrics', methods=['POST'])
def force_standard_metrics():
    """Force metrics to emit a standard value for a given period"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'JSON body required'}), 400
        
        # Get parameters
        value = data.get('value')
        duration = data.get('duration', 60)  # Default to 60 seconds
        
        if value is None:
            return jsonify({'error': 'value parameter is required'}), 400
        
        # Validate duration
        if not isinstance(duration, (int, float)) or duration <= 0:
            return jsonify({'error': 'duration must be a positive number'}), 400
        
        # Set force metrics
        force_metrics['active'] = True
        force_metrics['value'] = float(value)
        force_metrics['end_time'] = datetime.now() + timedelta(seconds=duration)
        
        return jsonify({
            'message': f'Forcing {SENSOR_TYPE} metrics to {value} {get_unit()} for {duration} seconds',
            'forced_value': force_metrics['value'],
            'duration': duration,
            'end_time': force_metrics['end_time'].isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/force_metrics', methods=['GET'])
def get_force_metrics_status():
    """Get current force metrics status"""
    if force_metrics['active']:
        remaining_time = (force_metrics['end_time'] - datetime.now()).total_seconds()
        if remaining_time > 0:
            return jsonify({
                'active': True,
                'forced_value': force_metrics['value'],
                'remaining_time': round(remaining_time, 2),
                'end_time': force_metrics['end_time'].isoformat()
            })
        else:
            force_metrics['active'] = False
            force_metrics['end_time'] = None
    
    return jsonify({
        'active': False,
        'message': 'No forced metrics active'
    })

@app.route('/force_metrics', methods=['DELETE'])
def stop_force_metrics():
    """Stop forcing metrics immediately"""
    if force_metrics['active']:
        force_metrics['active'] = False
        force_metrics['end_time'] = None
        return jsonify({'message': 'Forced metrics stopped'})
    else:
        return jsonify({'message': 'No forced metrics were active'})

# Simple inter-sensor communication endpoint
@app.route('/send_message', methods=['POST'])
def send_message():
    """Send a message to one or more containers to coordinate system stability"""
    global system_mode, mode_end_time
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'JSON body required'}), 400
        
        target_sensors = data.get('target_sensors', [])
        action = data.get('action', 'stabilize')
        duration = data.get('duration', 30)
        
        # Ensure target_sensors is a list
        if isinstance(target_sensors, str):
            target_sensors = [target_sensors]
        
        if not target_sensors:
            return jsonify({'error': 'target_sensors parameter is required'}), 400
        
        results = {}
        
        # Send message to each target container
        for container_name in target_sensors:
            try:
                message_payload = {
                    'from': SENSOR_NAME,
                    'from_type': SENSOR_TYPE,
                    'action': action,
                    'timestamp': datetime.now().isoformat()
                }
                
                response = requests.post(
                    f"http://{container_name}:5000/receive_message",
                    json=message_payload,
                    timeout=5
                )
                
                if response.status_code == 200:
                    results[container_name] = {
                        'status': 'success',
                        'response': response.json()
                    }
                else:
                    results[container_name] = {
                        'status': 'failed',
                        'error': f'HTTP {response.status_code}'
                    }
                
            except Exception as e:
                results[container_name] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        # Change our own behavior based on the action
        if action == 'cool_down':
            system_mode = "cooling"
            mode_end_time = datetime.now() + timedelta(seconds=duration)
        elif action == 'reduce_load':
            system_mode = "reducing" 
            mode_end_time = datetime.now() + timedelta(seconds=duration)
        elif action == 'emergency':
            system_mode = "emergency"
            mode_end_time = datetime.now() + timedelta(seconds=duration)
        elif action == 'stabilize':
            system_mode = "normal"
            mode_end_time = None
        
        return jsonify({
            'message': f'Sent {action} command to {len(target_sensors)} sensor(s)',
            'target_sensors': target_sensors,
            'my_new_mode': system_mode,
            'action': action,
            'duration': duration,
            'results': results
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/receive_message', methods=['POST'])
def receive_message():
    """Receive a message from another sensor and adjust behavior"""
    global system_mode, mode_end_time
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'JSON body required'}), 400
        
        from_sensor = data.get('from', 'unknown')
        action = data.get('action', 'stabilize')
        
        # Store the message
        message = {
            'from': from_sensor,
            'action': action,
            'received_at': datetime.now().isoformat(),
            'original_timestamp': data.get('timestamp')
        }
        received_messages.append(message)
        
        if len(received_messages) > 10:
            received_messages.pop(0)
        
        duration = 30 
        
        if action == 'cool_down':
            system_mode = "cooling"
            mode_end_time = datetime.now() + timedelta(seconds=duration)
        elif action == 'reduce_load':
            system_mode = "reducing"
            mode_end_time = datetime.now() + timedelta(seconds=duration) 
        elif action == 'emergency':
            system_mode = "emergency"
            mode_end_time = datetime.now() + timedelta(seconds=duration)
        elif action == 'stabilize':
            system_mode = "normal"
            mode_end_time = None
        
        return jsonify({
            'status': 'received',
            'from': from_sensor,
            'action': action,
            'new_mode': system_mode,
            'message': f'Switched to {system_mode} mode based on {action} command from {from_sensor}'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/messages')
def get_messages():
    """Get received messages"""
    return jsonify({
        'messages': received_messages,
        'count': len(received_messages),
        'current_mode': system_mode
    })

if __name__ == '__main__':
    print(f"Starting {SENSOR_NAME} on port {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False)