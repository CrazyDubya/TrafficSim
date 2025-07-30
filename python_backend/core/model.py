"""
Traffic Simulation Model - Python equivalent of Java jModel class
Main simulation engine that coordinates all traffic simulation components
"""
from typing import List, Dict, Optional, Any, Set
import time
import threading
import json
from dataclasses import dataclass, asdict
from enum import Enum

from .vehicle import Vehicle, VehicleInterface, Observer as VehicleObserver
from .driver import DriverInterface, create_driver, DriverType, Route
from .lane import Lane, LaneType, Coordinate


class SimulationState(Enum):
    """Simulation states"""
    STOPPED = "STOPPED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STEP = "STEP"


@dataclass
class SimulationSettings:
    """Simulation configuration settings"""
    time_step: float = 0.1  # Time step in seconds
    max_simulation_time: float = 3600.0  # Maximum simulation time in seconds
    debug_mode: bool = False
    real_time_factor: float = 1.0  # 1.0 = real time, 2.0 = 2x speed, etc.
    

@dataclass
class SimulationStats:
    """Simulation statistics"""
    current_time: float = 0.0
    total_vehicles: int = 0
    active_vehicles: int = 0
    completed_vehicles: int = 0
    crashed_vehicles: int = 0
    average_speed: float = 0.0
    total_flow: float = 0.0
    average_density: float = 0.0


class TrafficSimulationModel:
    """
    Main traffic simulation model - Python equivalent of Java jModel
    Manages the entire simulation including vehicles, drivers, lanes, and timing
    """
    
    _instance: Optional['TrafficSimulationModel'] = None
    
    def __init__(self):
        if TrafficSimulationModel._instance is not None:
            raise Exception("TrafficSimulationModel is a singleton!")
        
        TrafficSimulationModel._instance = self
        
        # Simulation state
        self.state = SimulationState.STOPPED
        self.settings = SimulationSettings()
        self.stats = SimulationStats()
        
        # Network components
        self.lanes: Dict[int, Lane] = {}
        self.vehicles: Dict[int, Vehicle] = {}
        self.drivers: Dict[int, DriverInterface] = {}
        self.routes: Dict[int, Route] = {}
        
        # Traffic generators
        self.generators: List['TrafficGenerator'] = []
        
        # Simulation timing
        self.start_time = 0.0
        self.current_time = 0.0
        self.last_update_time = 0.0
        
        # Threading
        self.simulation_thread: Optional[threading.Thread] = None
        self.stop_simulation_flag = False
        
        # Observers for real-time updates
        self.observers: List['SimulationObserver'] = []
        
        # Vehicle ID counter
        self.next_vehicle_id = 1
        self.next_driver_id = 1
        
    @classmethod
    def get_instance(cls) -> 'TrafficSimulationModel':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = TrafficSimulationModel()
        return cls._instance
    
    @classmethod
    def reset_instance(cls):
        """Reset singleton instance"""
        cls._instance = None
    
    def initialize(self, lanes: List[Lane], settings: Optional[SimulationSettings] = None):
        """Initialize simulation with network and settings"""
        if settings:
            self.settings = settings
        
        # Add lanes to network
        for lane in lanes:
            self.lanes[lane.id] = lane
        
        # Update lane connections and vehicle surroundings
        self._update_network()
        
        self.state = SimulationState.STOPPED
        self.stats = SimulationStats()
        
    def add_lane(self, lane: Lane):
        """Add a lane to the network"""
        self.lanes[lane.id] = lane
        self._update_network()
    
    def remove_lane(self, lane_id: int):
        """Remove a lane from the network"""
        if lane_id in self.lanes:
            # Remove all vehicles from the lane first
            lane = self.lanes[lane_id]
            vehicles_to_remove = lane.get_vehicles().copy()
            for vehicle in vehicles_to_remove:
                self.remove_vehicle(vehicle.id)
            
            del self.lanes[lane_id]
            self._update_network()
    
    def add_vehicle(self, lane_id: int, driver_type: DriverType = DriverType.IDM, 
                   initial_position: float = 0.0, route: Optional[Route] = None) -> Optional[Vehicle]:
        """Add a vehicle to the simulation"""
        if lane_id not in self.lanes:
            return None
        
        lane = self.lanes[lane_id]
        
        # Create vehicle
        vehicle = Vehicle(self.next_vehicle_id, lane, initial_position)
        
        # Create driver
        driver = create_driver(self.next_driver_id, driver_type)
        driver.set_vehicle(vehicle)
        
        if route:
            driver.set_route(route)
        
        # Add to collections
        self.vehicles[vehicle.id] = vehicle
        self.drivers[driver.get_id()] = driver
        lane.add_vehicle(vehicle)
        
        # Update counters
        self.next_vehicle_id += 1
        self.next_driver_id += 1
        self.stats.total_vehicles += 1
        self.stats.active_vehicles += 1
        
        return vehicle
    
    def remove_vehicle(self, vehicle_id: int):
        """Remove a vehicle from the simulation"""
        if vehicle_id in self.vehicles:
            vehicle = self.vehicles[vehicle_id]
            
            # Remove from lane
            vehicle.get_lane().remove_vehicle(vehicle)
            
            # Remove driver
            if vehicle.driver:
                driver_id = vehicle.driver.get_id()
                if driver_id in self.drivers:
                    del self.drivers[driver_id]
            
            # Remove vehicle
            del self.vehicles[vehicle_id]
            
            # Update stats
            self.stats.active_vehicles -= 1
            if vehicle.state.crashed:
                self.stats.crashed_vehicles += 1
            else:
                self.stats.completed_vehicles += 1
    
    def add_route(self, route: Route):
        """Add a route to the simulation"""
        self.routes[route.id] = route
    
    def get_vehicles(self) -> List[Vehicle]:
        """Get all vehicles in simulation"""
        return list(self.vehicles.values())
    
    def get_lanes(self) -> List[Lane]:
        """Get all lanes in simulation"""
        return list(self.lanes.values())
    
    def get_vehicle_by_id(self, vehicle_id: int) -> Optional[Vehicle]:
        """Get vehicle by ID"""
        return self.vehicles.get(vehicle_id)
    
    def get_lane_by_id(self, lane_id: int) -> Optional[Lane]:
        """Get lane by ID"""
        return self.lanes.get(lane_id)
    
    def start_simulation(self):
        """Start the simulation"""
        if self.state == SimulationState.RUNNING:
            return
        
        self.state = SimulationState.RUNNING
        self.start_time = time.time()
        self.current_time = 0.0
        self.stop_simulation_flag = False
        
        # Start simulation thread
        self.simulation_thread = threading.Thread(target=self._simulation_loop)
        self.simulation_thread.start()
    
    def pause_simulation(self):
        """Pause the simulation"""
        if self.state == SimulationState.RUNNING:
            self.state = SimulationState.PAUSED
    
    def resume_simulation(self):
        """Resume the simulation"""
        if self.state == SimulationState.PAUSED:
            self.state = SimulationState.RUNNING
    
    def stop_simulation(self):
        """Stop the simulation"""
        self.stop_simulation_flag = True
        self.state = SimulationState.STOPPED
        
        if self.simulation_thread and self.simulation_thread.is_alive():
            self.simulation_thread.join(timeout=1.0)
    
    def step_simulation(self):
        """Execute one simulation step"""
        if self.state in [SimulationState.STOPPED, SimulationState.PAUSED]:
            self._update_simulation(self.settings.time_step)
            self.state = SimulationState.PAUSED
    
    def _simulation_loop(self):
        """Main simulation loop running in separate thread"""
        last_real_time = time.time()
        
        while not self.stop_simulation_flag and self.state != SimulationState.STOPPED:
            if self.state == SimulationState.RUNNING:
                # Calculate time step
                current_real_time = time.time()
                real_dt = current_real_time - last_real_time
                sim_dt = real_dt * self.settings.real_time_factor
                
                # Use fixed time step for stability
                dt = self.settings.time_step
                
                # Update simulation
                self._update_simulation(dt)
                
                # Sleep to maintain real-time factor
                sleep_time = self.settings.time_step / self.settings.real_time_factor
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
                last_real_time = current_real_time
            else:
                # Paused - small sleep to avoid busy waiting
                time.sleep(0.01)
    
    def _update_simulation(self, dt: float):
        """Update simulation by one time step"""
        # Update current simulation time
        self.current_time += dt
        self.stats.current_time = self.current_time
        
        # Update all lanes (vehicle surroundings)
        for lane in self.lanes.values():
            lane.update_vehicle_surroundings()
        
        # Execute driver behaviors
        for driver in self.drivers.values():
            try:
                driver.drive()
            except Exception as e:
                print(f"Error in driver {driver.get_id()}: {e}")
        
        # Move all vehicles
        for vehicle in list(self.vehicles.values()):
            try:
                vehicle.move(dt)
                
                # Check if vehicle has left the network
                if self._has_vehicle_exited(vehicle):
                    self.remove_vehicle(vehicle.id)
                    
            except Exception as e:
                print(f"Error moving vehicle {vehicle.id}: {e}")
        
        # Run traffic generators
        for generator in self.generators:
            try:
                generator.update(dt)
            except Exception as e:
                print(f"Error in traffic generator: {e}")
        
        # Update statistics
        self._update_statistics()
        
        # Notify observers
        for observer in self.observers:
            try:
                observer.simulation_updated(self)
            except Exception as e:
                print(f"Error notifying observer: {e}")
    
    def _has_vehicle_exited(self, vehicle: Vehicle) -> bool:
        """Check if vehicle has exited the network"""
        lane = vehicle.get_lane()
        position = vehicle.get_x()
        
        # Vehicle exits if it goes beyond the lane length and there's no downstream lane
        if position > lane.length and lane.get_downstream_lane() is None:
            return True
        
        return False
    
    def _update_network(self):
        """Update network connectivity and vehicle surroundings"""
        for lane in self.lanes.values():
            lane.update_vehicle_surroundings()
    
    def _update_statistics(self):
        """Update simulation statistics"""
        self.stats.active_vehicles = len(self.vehicles)
        
        if self.vehicles:
            total_speed = sum(v.get_velocity() for v in self.vehicles.values())
            self.stats.average_speed = total_speed / len(self.vehicles)
        else:
            self.stats.average_speed = 0.0
        
        # Calculate total flow and average density
        total_flow = 0.0
        total_density = 0.0
        lane_count = len(self.lanes)
        
        for lane in self.lanes.values():
            total_flow += lane.get_flow()
            total_density += lane.get_density()
        
        self.stats.total_flow = total_flow
        self.stats.average_density = total_density / lane_count if lane_count > 0 else 0.0
    
    def add_observer(self, observer: 'SimulationObserver'):
        """Add simulation observer"""
        if observer not in self.observers:
            self.observers.append(observer)
    
    def remove_observer(self, observer: 'SimulationObserver'):
        """Remove simulation observer"""
        if observer in self.observers:
            self.observers.remove(observer)
    
    def get_simulation_data(self) -> Dict[str, Any]:
        """Get current simulation data for API/frontend"""
        return {
            'state': self.state.value,
            'stats': asdict(self.stats),
            'settings': asdict(self.settings),
            'vehicles': [vehicle.to_dict() for vehicle in self.vehicles.values()],
            'lanes': [lane.to_dict() for lane in self.lanes.values()],
            'timestamp': time.time()
        }
    
    def load_scenario(self, scenario_data: Dict[str, Any]):
        """Load a predefined scenario"""
        # Clear existing simulation
        self.stop_simulation()
        self.vehicles.clear()
        self.drivers.clear()
        self.lanes.clear()
        self.routes.clear()
        
        # Load lanes
        if 'lanes' in scenario_data:
            for lane_data in scenario_data['lanes']:
                lane = Lane(
                    lane_id=lane_data['id'],
                    lane_type=LaneType(lane_data.get('type', 'NORMAL')),
                    length=lane_data.get('length', 1000.0)
                )
                if 'coordinates' in lane_data:
                    lane.coordinates = [
                        Coordinate(c['x'], c['y']) for c in lane_data['coordinates']
                    ]
                self.add_lane(lane)
        
        # Set up lane connections
        if 'connections' in scenario_data:
            for conn in scenario_data['connections']:
                lane_id = conn['lane_id']
                if lane_id in self.lanes:
                    lane = self.lanes[lane_id]
                    if 'left' in conn and conn['left'] in self.lanes:
                        lane.set_left_lane(self.lanes[conn['left']])
                    if 'right' in conn and conn['right'] in self.lanes:
                        lane.set_right_lane(self.lanes[conn['right']])
                    if 'upstream' in conn and conn['upstream'] in self.lanes:
                        lane.set_upstream_lane(self.lanes[conn['upstream']])
                    if 'downstream' in conn and conn['downstream'] in self.lanes:
                        lane.set_downstream_lane(self.lanes[conn['downstream']])
        
        # Load routes
        if 'routes' in scenario_data:
            for route_data in scenario_data['routes']:
                route = Route(route_data['id'], route_data['lane_sequence'])
                self.add_route(route)
        
        # Load initial vehicles
        if 'vehicles' in scenario_data:
            for vehicle_data in scenario_data['vehicles']:
                driver_type = DriverType(vehicle_data.get('driver_type', 'IDM'))
                route_id = vehicle_data.get('route_id')
                route = self.routes.get(route_id) if route_id else None
                
                self.add_vehicle(
                    lane_id=vehicle_data['lane_id'],
                    driver_type=driver_type,
                    initial_position=vehicle_data.get('position', 0.0),
                    route=route
                )
        
        # Load settings
        if 'settings' in scenario_data:
            settings_data = scenario_data['settings']
            self.settings = SimulationSettings(
                time_step=settings_data.get('time_step', 0.1),
                max_simulation_time=settings_data.get('max_simulation_time', 3600.0),
                debug_mode=settings_data.get('debug_mode', False),
                real_time_factor=settings_data.get('real_time_factor', 1.0)
            )


class SimulationObserver:
    """Observer interface for simulation updates"""
    
    def simulation_updated(self, model: TrafficSimulationModel):
        """Called when simulation is updated"""
        pass


# Traffic generator interface
class TrafficGenerator:
    """Base class for traffic generators"""
    
    def __init__(self, lane: Lane, generation_rate: float = 0.1):
        self.lane = lane
        self.generation_rate = generation_rate  # vehicles per second
        self.last_generation_time = 0.0
    
    def update(self, dt: float):
        """Update generator - create vehicles as needed"""
        pass