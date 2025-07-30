"""
Vehicle module - Python equivalent of Java Vehicle classes
Converts the Java vehicle hierarchy to Python with similar functionality
"""
from typing import Optional, Dict, List, Any
from abc import ABC, abstractmethod
from enum import Enum
import math
import time
from dataclasses import dataclass


class LatDirection(Enum):
    """Lateral direction for lane changes"""
    LEFT = "LEFT"
    RIGHT = "RIGHT"


class Enclosure(Enum):
    """Areas around a vehicle for neighbor detection"""
    FRONT = "FRONT"
    BACK = "BACK"
    LEFT_FRONT = "LEFT_FRONT"
    LEFT_BACK = "LEFT_BACK"
    RIGHT_FRONT = "RIGHT_FRONT"
    RIGHT_BACK = "RIGHT_BACK"


@dataclass
class VehicleState:
    """Current state of a vehicle"""
    x: float = 0.0  # Position along lane [m]
    y: float = 0.0  # Lateral position [m]
    velocity: float = 0.0  # Current velocity [m/s]
    acceleration: float = 0.0  # Current acceleration [m/s²]
    lane_change_progress: float = 0.0  # Lane change progress [0-1]
    crashed: bool = False
    

class VehicleInterface(ABC):
    """Abstract interface for vehicles - Python equivalent of jVehicle"""
    
    @abstractmethod
    def get_vehicle(self, area: Enclosure) -> Optional['VehicleInterface']:
        """Get neighboring vehicle in specified area"""
        pass
    
    @abstractmethod
    def update_surrounding(self, area: Enclosure, vehicle: Optional['VehicleInterface']):
        """Update neighboring vehicle information"""
        pass
    
    @abstractmethod
    def get_lane(self) -> 'Lane':
        """Get current lane"""
        pass
    
    @abstractmethod
    def get_x(self) -> float:
        """Get position along current lane [m]"""
        pass
    
    @abstractmethod
    def get_gap(self, leader: 'VehicleInterface') -> float:
        """Get net headway to leading vehicle [m]"""
        pass
    
    @abstractmethod
    def move(self, dt: float):
        """Move vehicle for time step dt"""
        pass


class Vehicle(VehicleInterface):
    """Main vehicle implementation - Python equivalent of Java Vehicle class"""
    
    def __init__(self, vehicle_id: int, lane: 'Lane', initial_x: float = 0.0):
        self.id = vehicle_id
        self.lane = lane
        self.state = VehicleState(x=initial_x)
        
        # Vehicle properties
        self.length = 4.5  # Vehicle length [m]
        self.width = 2.0   # Vehicle width [m]
        self.v_max = 50.0  # Maximum speed [m/s]
        self.class_id = 1
        
        # Lane change properties
        self.lc_direction: Optional[LatDirection] = None
        self.dy = 0.0  # Lateral speed
        
        # Surrounding vehicles
        self.surrounding: Dict[Enclosure, Optional['Vehicle']] = {
            area: None for area in Enclosure
        }
        
        # Driver (will be set externally)
        self.driver: Optional['Driver'] = None
        
        # Observers
        self.observers: List['Observer'] = []
        
        # Debug data
        self.accelerations: Dict[float, float] = {}
        
    def get_vehicle(self, area: Enclosure) -> Optional['Vehicle']:
        """Get neighboring vehicle in specified area"""
        return self.surrounding.get(area)
    
    def update_surrounding(self, area: Enclosure, vehicle: Optional['Vehicle']):
        """Update neighboring vehicle information"""
        self.surrounding[area] = vehicle
    
    def get_lane(self) -> 'Lane':
        """Get current lane"""
        return self.lane
    
    def get_x(self) -> float:
        """Get position along current lane [m]"""
        return self.state.x
    
    def get_y(self) -> float:
        """Get lateral position [m]"""
        return self.state.y
    
    def get_velocity(self) -> float:
        """Get current velocity [m/s]"""
        return self.state.velocity
    
    def get_acceleration(self) -> float:
        """Get current acceleration [m/s²]"""
        return self.state.acceleration
    
    def is_changing_lane(self) -> bool:
        """Check if vehicle is currently changing lanes"""
        return self.state.lane_change_progress > 0
    
    def get_lane_change_progress(self) -> float:
        """Get lane change progress [0-1]"""
        return self.state.lane_change_progress
    
    def get_lane_change_direction(self) -> Optional[LatDirection]:
        """Get lane change direction if changing lanes"""
        if self.is_changing_lane():
            return self.lc_direction
        return None
    
    def get_gap(self, leader: 'Vehicle') -> float:
        """Get net headway to leading vehicle [m]"""
        if leader is None:
            return float('inf')
        
        # Simple distance calculation (could be enhanced for curved lanes)
        gap = leader.get_x() - self.get_x() - leader.length
        return max(0.0, gap)
    
    def start_lane_change(self, direction: LatDirection, duration: float = 3.0):
        """Start a lane change maneuver"""
        if not self.is_changing_lane():
            self.lc_direction = direction
            self.dy = 1.0 / duration  # Complete lane change in 'duration' seconds
    
    def end_lane_change(self):
        """Complete lane change and move to new lane"""
        if self.is_changing_lane():
            # Get target lane
            target_lane = None
            if self.lc_direction == LatDirection.LEFT:
                target_lane = self.lane.get_left_lane()
            elif self.lc_direction == LatDirection.RIGHT:
                target_lane = self.lane.get_right_lane()
            
            if target_lane:
                # Remove from current lane
                self.lane.remove_vehicle(self)
                # Add to new lane
                self.lane = target_lane
                target_lane.add_vehicle(self)
                
            # Reset lane change state
            self.state.lane_change_progress = 0.0
            self.lc_direction = None
            self.dy = 0.0
    
    def move(self, dt: float):
        """Move vehicle for time step dt - equivalent to Java move() method"""
        if self.state.crashed:
            return
        
        # Store acceleration for debugging
        current_time = time.time()
        self.accelerations[current_time] = self.state.acceleration
        
        # Lateral movement (lane changing)
        if self.dy != 0:
            self.state.lane_change_progress += self.dy * dt
            if self.state.lane_change_progress >= 1.0:
                self.end_lane_change()
        
        # Longitudinal movement
        dx = dt * self.state.velocity + 0.5 * self.state.acceleration * dt * dt
        dx = max(0.0, dx)  # Ensure non-negative movement
        
        # Update velocity
        self.state.velocity += dt * self.state.acceleration
        self.state.velocity = max(0.0, self.state.velocity)  # Ensure non-negative velocity
        
        # Update position
        self.state.x += dx
        self.state.y += self.dy * dt if self.is_changing_lane() else 0.0
        
        # Notify observers
        for observer in self.observers:
            observer.observe_vehicle_move(self)
    
    def set_acceleration(self, acceleration: float):
        """Set vehicle acceleration"""
        self.state.acceleration = acceleration
    
    def set_velocity(self, velocity: float):
        """Set vehicle velocity"""
        self.state.velocity = max(0.0, velocity)
    
    def crash(self):
        """Mark vehicle as crashed"""
        self.state.crashed = True
        self.state.velocity = 0.0
        self.state.acceleration = 0.0
    
    def add_observer(self, observer: 'Observer'):
        """Add observer for vehicle state changes"""
        if observer not in self.observers:
            self.observers.append(observer)
    
    def remove_observer(self, observer: 'Observer'):
        """Remove observer"""
        if observer in self.observers:
            self.observers.remove(observer)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert vehicle to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'x': self.state.x,
            'y': self.state.y,
            'velocity': self.state.velocity,
            'acceleration': self.state.acceleration,
            'lane_id': self.lane.id if self.lane else None,
            'length': self.length,
            'width': self.width,
            'is_changing_lane': self.is_changing_lane(),
            'lane_change_progress': self.state.lane_change_progress,
            'lane_change_direction': self.lc_direction.value if self.lc_direction else None,
            'crashed': self.state.crashed
        }
    
    def __str__(self):
        return f"Vehicle({self.id}, x={self.state.x:.1f}, v={self.state.velocity:.1f})"
    
    def __repr__(self):
        return self.__str__()


# Observer interface for vehicle monitoring
class Observer(ABC):
    """Observer interface for monitoring vehicle changes"""
    
    @abstractmethod
    def observe_vehicle_move(self, vehicle: Vehicle):
        """Called when vehicle moves"""
        pass