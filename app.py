#!/usr/bin/env python3
"""
Traffic Simulation Application Entry Point
Starts the Flask web server with the traffic simulation backend
"""

import sys
import os
import argparse
import logging

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from python_backend.api.web_api import create_app
from python_backend.core.model import TrafficSimulationModel


def setup_logging(debug=False):
    """Set up logging configuration"""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('traffic_sim.log')
        ]
    )


def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(description='Traffic Simulation Web Application')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to (default: 5000)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--scenario', help='Load initial scenario file')
    
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.debug)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Traffic Simulation Application")
    
    try:
        # Create Flask app and SocketIO
        app, socketio = create_app()
        
        # Load initial scenario if provided
        if args.scenario:
            logger.info(f"Loading initial scenario: {args.scenario}")
            # TODO: Implement scenario file loading
            
        # Start the application
        logger.info(f"Starting server on {args.host}:{args.port}")
        logger.info(f"Debug mode: {args.debug}")
        logger.info("Visit http://localhost:5000 to access the simulation interface")
        
        socketio.run(
            app, 
            debug=args.debug, 
            host=args.host, 
            port=args.port,
            use_reloader=False  # Disable reloader to avoid double initialization
        )
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
        raise
    finally:
        # Clean up simulation
        try:
            model = TrafficSimulationModel.get_instance()
            model.stop_simulation()
        except:
            pass
        logger.info("Application shutdown complete")


if __name__ == '__main__':
    main()