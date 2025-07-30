#!/usr/bin/env python3
"""
Simple test server to demonstrate the traffic simulation without external dependencies
"""

import sys
import os
import json
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from python_backend.core.model import TrafficSimulationModel, SimulationSettings
from python_backend.core.lane import Lane, LaneType, Coordinate
from python_backend.core.driver import DriverType, Route


class TrafficSimHandler(SimpleHTTPRequestHandler):
    """Simple HTTP handler for the traffic simulation"""
    
    def __init__(self, *args, **kwargs):
        # Set the directory to serve files from
        super().__init__(*args, directory='frontend', **kwargs)
    
    def do_GET(self):
        """Handle GET requests"""
        path = urlparse(self.path).path
        
        if path == '/':
            # Serve the simple page
            self.serve_file('frontend/simple.html', 'text/html')
        elif path.startswith('/api/'):
            self.handle_api_get(path)
        else:
            # Serve static files
            super().do_GET()
    
    def do_POST(self):
        """Handle POST requests"""
        path = urlparse(self.path).path
        
        if path.startswith('/api/'):
            self.handle_api_post(path)
        else:
            self.send_error(404)
    
    def serve_file(self, file_path, content_type):
        """Serve a file with the specified content type"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-type', content_type)
            self.end_headers()
            self.wfile.write(content.encode())
        except FileNotFoundError:
            self.send_error(404)
    
    def handle_api_get(self, path):
        """Handle API GET requests"""
        model = TrafficSimulationModel.get_instance()
        
        if path == '/api/status':
            data = model.get_simulation_data()
            self.send_json_response(data)
        elif path == '/api/vehicles':
            vehicles = [v.to_dict() for v in model.get_vehicles()]
            self.send_json_response({'vehicles': vehicles})
        elif path == '/api/lanes':
            lanes = [l.to_dict() for l in model.get_lanes()]
            self.send_json_response({'lanes': lanes})
        else:
            self.send_error(404)
    
    def handle_api_post(self, path):
        """Handle API POST requests"""
        model = TrafficSimulationModel.get_instance()
        
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode()) if content_length > 0 else {}
            
            if path == '/api/start':
                model.start_simulation()
                self.send_json_response({'status': 'success', 'message': 'Simulation started'})
            elif path == '/api/pause':
                model.pause_simulation()
                self.send_json_response({'status': 'success', 'message': 'Simulation paused'})
            elif path == '/api/resume':
                model.resume_simulation()
                self.send_json_response({'status': 'success', 'message': 'Simulation resumed'})
            elif path == '/api/stop':
                model.stop_simulation()
                self.send_json_response({'status': 'success', 'message': 'Simulation stopped'})
            elif path == '/api/reset':
                model.stop_simulation()
                TrafficSimulationModel.reset_instance()
                self.send_json_response({'status': 'success', 'message': 'Simulation reset'})
            elif path == '/api/step':
                model.step_simulation()
                self.send_json_response({'status': 'success', 'message': 'Simulation stepped'})
            elif path == '/api/scenarios/simple':
                self.load_simple_scenario()
                self.send_json_response({'status': 'success', 'message': 'Simple scenario loaded'})
            elif path == '/api/vehicles':
                self.add_vehicle(data)
            else:
                self.send_error(404)
                
        except Exception as e:
            self.send_json_response({'status': 'error', 'message': str(e)}, 500)
    
    def load_simple_scenario(self):
        """Load a simple 3-lane highway scenario"""
        model = TrafficSimulationModel.get_instance()
        
        # Create lanes
        lane1 = Lane(0, LaneType.NORMAL, 2000.0, [Coordinate(0, 0), Coordinate(2000, 0)])
        lane2 = Lane(1, LaneType.NORMAL, 2000.0, [Coordinate(0, 4), Coordinate(2000, 4)])
        lane3 = Lane(2, LaneType.NORMAL, 2000.0, [Coordinate(0, 8), Coordinate(2000, 8)])
        
        # Connect lanes
        lane1.set_right_lane(lane2)
        lane2.set_left_lane(lane1)
        lane2.set_right_lane(lane3)
        lane3.set_left_lane(lane2)
        
        # Initialize model
        model.initialize([lane1, lane2, lane3])
        
        # Add some vehicles
        route1 = Route(1, [0])
        route2 = Route(2, [1])
        route3 = Route(3, [2])
        
        model.add_route(route1)
        model.add_route(route2)
        model.add_route(route3)
        
        model.add_vehicle(0, DriverType.IDM, 100.0, route1)
        model.add_vehicle(1, DriverType.AGGRESSIVE, 150.0, route2)
        model.add_vehicle(2, DriverType.CAUTIOUS, 200.0, route3)
    
    def add_vehicle(self, data):
        """Add a vehicle to the simulation"""
        model = TrafficSimulationModel.get_instance()
        
        lane_id = data.get('lane_id', 0)
        position = data.get('position', 0.0)
        driver_type = DriverType(data.get('driver_type', 'IDM'))
        
        vehicle = model.add_vehicle(lane_id, driver_type, position)
        
        if vehicle:
            self.send_json_response({
                'status': 'success',
                'message': 'Vehicle added',
                'vehicle': vehicle.to_dict()
            })
        else:
            self.send_json_response({'status': 'error', 'message': 'Failed to add vehicle'}, 400)
    
    def send_json_response(self, data, status_code=200):
        """Send a JSON response"""
        json_data = json.dumps(data)
        
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json_data.encode())
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()


def main():
    """Main function"""
    port = 8000
    
    print(f"Starting Traffic Simulation Server on port {port}")
    print(f"Visit http://localhost:{port} to access the simulation")
    
    try:
        with HTTPServer(('localhost', port), TrafficSimHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")


if __name__ == '__main__':
    main()