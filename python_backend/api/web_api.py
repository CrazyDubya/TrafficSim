"""
Web API for Traffic Simulation
Flask-based REST API and WebSocket interface for controlling and monitoring the simulation
"""
from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import json
import threading
import time
from typing import Dict, Any

from ..core.model import TrafficSimulationModel, SimulationObserver, SimulationState
from ..core.lane import Lane, LaneType, Coordinate
from ..core.driver import DriverType, Route


class WebSocketObserver(SimulationObserver):
    """Observer that broadcasts simulation updates via WebSocket"""
    
    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        self.last_broadcast_time = 0.0
        self.broadcast_interval = 0.1  # Broadcast every 100ms
    
    def simulation_updated(self, model: TrafficSimulationModel):
        """Send simulation data to connected clients"""
        current_time = time.time()
        if current_time - self.last_broadcast_time >= self.broadcast_interval:
            data = model.get_simulation_data()
            self.socketio.emit('simulation_update', data)
            self.last_broadcast_time = current_time


def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__, 
                template_folder='../../frontend/templates',
                static_folder='../../frontend/static')
    app.config['SECRET_KEY'] = 'traffic_sim_secret_key'
    
    # Enable CORS for all routes
    CORS(app)
    
    # Initialize SocketIO
    socketio = SocketIO(app, cors_allowed_origins="*")
    
    # Get simulation model instance
    model = TrafficSimulationModel.get_instance()
    
    # Create WebSocket observer
    ws_observer = WebSocketObserver(socketio)
    model.add_observer(ws_observer)
    
    # Web routes
    @app.route('/')
    def index():
        """Serve main simulation interface"""
        return render_template('index.html')
    
    @app.route('/api/status', methods=['GET'])
    def get_status():
        """Get current simulation status"""
        return jsonify(model.get_simulation_data())
    
    @app.route('/api/start', methods=['POST'])
    def start_simulation():
        """Start the simulation"""
        try:
            model.start_simulation()
            return jsonify({'status': 'success', 'message': 'Simulation started'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    @app.route('/api/pause', methods=['POST'])
    def pause_simulation():
        """Pause the simulation"""
        try:
            model.pause_simulation()
            return jsonify({'status': 'success', 'message': 'Simulation paused'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    @app.route('/api/resume', methods=['POST'])
    def resume_simulation():
        """Resume the simulation"""
        try:
            model.resume_simulation()
            return jsonify({'status': 'success', 'message': 'Simulation resumed'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    @app.route('/api/stop', methods=['POST'])
    def stop_simulation():
        """Stop the simulation"""
        try:
            model.stop_simulation()
            return jsonify({'status': 'success', 'message': 'Simulation stopped'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    @app.route('/api/step', methods=['POST'])
    def step_simulation():
        """Execute one simulation step"""
        try:
            model.step_simulation()
            return jsonify({'status': 'success', 'message': 'Simulation stepped'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    @app.route('/api/reset', methods=['POST'])
    def reset_simulation():
        """Reset the simulation"""
        try:
            model.stop_simulation()
            TrafficSimulationModel.reset_instance()
            # Reinitialize
            global model, ws_observer
            model = TrafficSimulationModel.get_instance()
            ws_observer = WebSocketObserver(socketio)
            model.add_observer(ws_observer)
            return jsonify({'status': 'success', 'message': 'Simulation reset'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    @app.route('/api/vehicles', methods=['GET'])
    def get_vehicles():
        """Get all vehicles"""
        vehicles = [vehicle.to_dict() for vehicle in model.get_vehicles()]
        return jsonify({'vehicles': vehicles})
    
    @app.route('/api/vehicles', methods=['POST'])
    def add_vehicle():
        """Add a new vehicle"""
        try:
            data = request.get_json()
            lane_id = data.get('lane_id')
            driver_type = DriverType(data.get('driver_type', 'IDM'))
            position = data.get('position', 0.0)
            
            # Create route if provided
            route = None
            if 'route' in data:
                route_data = data['route']
                route = Route(route_data['id'], route_data['lane_sequence'])
            
            vehicle = model.add_vehicle(lane_id, driver_type, position, route)
            
            if vehicle:
                return jsonify({
                    'status': 'success', 
                    'message': 'Vehicle added',
                    'vehicle': vehicle.to_dict()
                })
            else:
                return jsonify({'status': 'error', 'message': 'Failed to add vehicle'}), 400
                
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    @app.route('/api/vehicles/<int:vehicle_id>', methods=['DELETE'])
    def remove_vehicle(vehicle_id: int):
        """Remove a vehicle"""
        try:
            model.remove_vehicle(vehicle_id)
            return jsonify({'status': 'success', 'message': 'Vehicle removed'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    @app.route('/api/lanes', methods=['GET'])
    def get_lanes():
        """Get all lanes"""
        lanes = [lane.to_dict() for lane in model.get_lanes()]
        return jsonify({'lanes': lanes})
    
    @app.route('/api/lanes', methods=['POST'])
    def add_lane():
        """Add a new lane"""
        try:
            data = request.get_json()
            lane_id = data.get('id')
            lane_type = LaneType(data.get('type', 'NORMAL'))
            length = data.get('length', 1000.0)
            
            # Create coordinates if provided
            coordinates = None
            if 'coordinates' in data:
                coordinates = [Coordinate(c['x'], c['y']) for c in data['coordinates']]
            
            lane = Lane(lane_id, lane_type, length, coordinates)
            model.add_lane(lane)
            
            return jsonify({
                'status': 'success',
                'message': 'Lane added',
                'lane': lane.to_dict()
            })
            
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    @app.route('/api/scenarios', methods=['POST'])
    def load_scenario():
        """Load a predefined scenario"""
        try:
            data = request.get_json()
            model.load_scenario(data)
            return jsonify({'status': 'success', 'message': 'Scenario loaded'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    @app.route('/api/scenarios/simple', methods=['POST'])
    def load_simple_scenario():
        """Load a simple test scenario"""
        try:
            # Create a simple 3-lane highway scenario
            scenario = {
                'lanes': [
                    {
                        'id': 0,
                        'type': 'NORMAL',
                        'length': 2000.0,
                        'coordinates': [{'x': 0, 'y': 0}, {'x': 2000, 'y': 0}]
                    },
                    {
                        'id': 1,
                        'type': 'NORMAL',
                        'length': 2000.0,
                        'coordinates': [{'x': 0, 'y': 4}, {'x': 2000, 'y': 4}]
                    },
                    {
                        'id': 2,
                        'type': 'NORMAL',
                        'length': 2000.0,
                        'coordinates': [{'x': 0, 'y': 8}, {'x': 2000, 'y': 8}]
                    }
                ],
                'connections': [
                    {'lane_id': 0, 'right': 1},
                    {'lane_id': 1, 'left': 0, 'right': 2},
                    {'lane_id': 2, 'left': 1}
                ],
                'routes': [
                    {'id': 1, 'lane_sequence': [0]},
                    {'id': 2, 'lane_sequence': [1]},
                    {'id': 3, 'lane_sequence': [2]}
                ],
                'vehicles': [
                    {'lane_id': 0, 'position': 100, 'driver_type': 'IDM', 'route_id': 1},
                    {'lane_id': 1, 'position': 150, 'driver_type': 'IDM', 'route_id': 2},
                    {'lane_id': 2, 'position': 200, 'driver_type': 'IDM', 'route_id': 3}
                ],
                'settings': {
                    'time_step': 0.1,
                    'real_time_factor': 1.0,
                    'debug_mode': True
                }
            }
            
            model.load_scenario(scenario)
            return jsonify({'status': 'success', 'message': 'Simple scenario loaded'})
            
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    @app.route('/api/settings', methods=['GET'])
    def get_settings():
        """Get simulation settings"""
        return jsonify(model.settings.__dict__)
    
    @app.route('/api/settings', methods=['POST'])
    def update_settings():
        """Update simulation settings"""
        try:
            data = request.get_json()
            
            if 'time_step' in data:
                model.settings.time_step = float(data['time_step'])
            if 'real_time_factor' in data:
                model.settings.real_time_factor = float(data['real_time_factor'])
            if 'debug_mode' in data:
                model.settings.debug_mode = bool(data['debug_mode'])
            if 'max_simulation_time' in data:
                model.settings.max_simulation_time = float(data['max_simulation_time'])
            
            return jsonify({'status': 'success', 'message': 'Settings updated'})
            
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    # WebSocket events
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        print('Client connected')
        # Send current simulation state
        emit('simulation_update', model.get_simulation_data())
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        print('Client disconnected')
    
    @socketio.on('request_update')
    def handle_request_update():
        """Handle client request for current simulation state"""
        emit('simulation_update', model.get_simulation_data())
    
    return app, socketio


if __name__ == '__main__':
    app, socketio = create_app()
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)