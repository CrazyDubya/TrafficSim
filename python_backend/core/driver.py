"""
Driver module - Python equivalent of Java Driver classes
Implements vehicle control logic and driving behavior models
"""
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod
from enum import Enum
import math
import random


class DriverType(Enum):
    """Types of drivers with different behaviors"""
    AGGRESSIVE = "AGGRESSIVE"
    NORMAL = "NORMAL"
    CAUTIOUS = "CAUTIOUS"
    IDM = "IDM"  # Intelligent Driver Model


class Route:
    """Represents a route through the network"""
    
    def __init__(self, route_id: int, lane_sequence: List[int]):
        self.id = route_id
        self.lane_sequence = lane_sequence  # List of lane IDs to follow
        self.current_index = 0
    
    def get_current_target_lane(self) -> Optional[int]:
        """Get current target lane ID"""
        if self.current_index < len(self.lane_sequence):
            return self.lane_sequence[self.current_index]
        return None
    
    def advance_route(self):
        """Move to next lane in route"""
        if self.current_index < len(self.lane_sequence) - 1:
            self.current_index += 1
    
    def is_route_complete(self) -> bool:
        """Check if route is completed"""
        return self.current_index >= len(self.lane_sequence)


class DriverInterface(ABC):
    """Abstract interface for drivers - Python equivalent of jDriver"""
    
    @abstractmethod
    def get_id(self) -> int:
        """Get driver ID"""
        pass
    
    @abstractmethod
    def drive(self):
        """Execute driving behavior for current time step"""
        pass
    
    @abstractmethod
    def get_route(self) -> Optional[Route]:
        """Get driver's route"""
        pass
    
    @abstractmethod
    def set_route(self, route: Route):
        """Set driver's route"""
        pass
    
    @abstractmethod
    def set_vehicle(self, vehicle: 'Vehicle'):
        """Set vehicle controlled by this driver"""
        pass
    
    @abstractmethod
    def get_vehicle(self) -> Optional['Vehicle']:
        """Get vehicle controlled by this driver"""
        pass


class IDMDriver(DriverInterface):
    """
    Intelligent Driver Model (IDM) implementation
    Based on the car-following model by Treiber et al.
    """
    
    def __init__(self, driver_id: int, driver_type: DriverType = DriverType.IDM):
        self.id = driver_id
        self.type = driver_type
        self.vehicle: Optional['Vehicle'] = None
        self.route: Optional[Route] = None
        
        # IDM parameters (can be adjusted based on driver type)
        self.desired_speed = 33.33  # Desired speed [m/s] (~120 km/h)
        self.time_headway = 1.5     # Safe time headway [s]
        self.min_spacing = 2.0      # Minimum spacing [m]
        self.max_acceleration = 2.0  # Maximum acceleration [m/s²]
        self.comfortable_deceleration = 3.0  # Comfortable deceleration [m/s²]
        self.acceleration_exponent = 4  # Acceleration exponent
        
        # Lane changing parameters
        self.politeness = 0.5       # Politeness factor [0-1]
        self.lane_change_threshold = 0.2  # Acceleration advantage threshold
        self.min_lane_change_gap = 10.0   # Minimum gap for lane change [m]
        
        # Adjust parameters based on driver type
        self._adjust_parameters_for_type()
    
    def _adjust_parameters_for_type(self):
        """Adjust driving parameters based on driver type"""
        if self.type == DriverType.AGGRESSIVE:
            self.time_headway = 1.0
            self.min_spacing = 1.5
            self.max_acceleration = 2.5
            self.comfortable_deceleration = 4.0
            self.politeness = 0.2
            self.desired_speed *= 1.1
        elif self.type == DriverType.CAUTIOUS:
            self.time_headway = 2.5
            self.min_spacing = 3.0
            self.max_acceleration = 1.5
            self.comfortable_deceleration = 2.0
            self.politeness = 0.8
            self.desired_speed *= 0.9
        elif self.type == DriverType.NORMAL:
            # Use default parameters
            pass
    
    def get_id(self) -> int:
        return self.id
    
    def get_route(self) -> Optional[Route]:
        return self.route
    
    def set_route(self, route: Route):
        self.route = route
    
    def set_vehicle(self, vehicle: 'Vehicle'):
        self.vehicle = vehicle
        vehicle.driver = self
    
    def get_vehicle(self) -> Optional['Vehicle']:
        return self.vehicle
    
    def drive(self):
        """Execute driving behavior for current time step"""
        if not self.vehicle or self.vehicle.state.crashed:
            return
        
        # Car following behavior
        acceleration = self._calculate_acceleration()
        self.vehicle.set_acceleration(acceleration)
        
        # Lane changing behavior
        self._consider_lane_change()
    
    def _calculate_acceleration(self) -> float:
        """Calculate acceleration using IDM formula"""
        if not self.vehicle:
            return 0.0
        
        v = self.vehicle.get_velocity()
        leader = self.vehicle.get_vehicle(self.vehicle.surrounding['FRONT'] 
                                         if 'FRONT' in self.vehicle.surrounding else None)
        
        # Free flow acceleration
        free_acceleration = self.max_acceleration * (
            1 - (v / self.desired_speed) ** self.acceleration_exponent
        )
        
        if leader is None:
            # No leader, use free flow acceleration
            return free_acceleration
        
        # Calculate desired gap
        gap = self.vehicle.get_gap(leader)
        leader_velocity = leader.get_velocity()
        velocity_diff = v - leader_velocity
        
        desired_gap = (self.min_spacing + 
                      self.time_headway * v + 
                      (v * velocity_diff) / (2 * math.sqrt(self.max_acceleration * 
                                                         self.comfortable_deceleration)))
        
        # IDM acceleration formula
        interaction_term = (desired_gap / gap) ** 2 if gap > 0 else float('inf')
        acceleration = self.max_acceleration * (1 - (v / self.desired_speed) ** self.acceleration_exponent - 
                                              interaction_term)
        
        return max(acceleration, -self.comfortable_deceleration)
    
    def _consider_lane_change(self):
        """Evaluate and execute lane changes using MOBIL model"""
        if not self.vehicle or self.vehicle.is_changing_lane():
            return
        
        lane = self.vehicle.get_lane()
        
        # Consider left lane change
        if lane.get_left_lane() and self._should_change_lane(lane.get_left_lane()):
            if lane.is_safe_lane_change(self.vehicle, lane.get_left_lane()):
                from .vehicle import LatDirection
                self.vehicle.start_lane_change(LatDirection.LEFT)
                return
        
        # Consider right lane change
        if lane.get_right_lane() and self._should_change_lane(lane.get_right_lane()):
            if lane.is_safe_lane_change(self.vehicle, lane.get_right_lane()):
                from .vehicle import LatDirection
                self.vehicle.start_lane_change(LatDirection.RIGHT)
                return
    
    def _should_change_lane(self, target_lane: 'Lane') -> bool:
        """Determine if lane change is beneficial using MOBIL criteria"""
        if not self.vehicle:
            return False
        
        # Calculate current acceleration
        current_accel = self._calculate_acceleration()
        
        # Calculate acceleration in target lane (simplified)
        # This would need more sophisticated implementation for full MOBIL
        target_leader = target_lane.get_leading_vehicle(self.vehicle.get_x())
        
        if target_leader is None:
            target_accel = self.max_acceleration
        else:
            # Simplified calculation - assume same gap behavior
            gap = target_leader.get_x() - self.vehicle.get_x() - self.vehicle.length
            if gap <= 0:
                return False
            
            v = self.vehicle.get_velocity()
            leader_velocity = target_leader.get_velocity()
            velocity_diff = v - leader_velocity
            
            desired_gap = (self.min_spacing + 
                          self.time_headway * v + 
                          (v * velocity_diff) / (2 * math.sqrt(self.max_acceleration * 
                                                             self.comfortable_deceleration)))
            
            interaction_term = (desired_gap / gap) ** 2 if gap > 0 else float('inf')
            target_accel = self.max_acceleration * (1 - (v / self.desired_speed) ** self.acceleration_exponent - 
                                                  interaction_term)
        
        # Lane change if target acceleration is significantly better
        advantage = target_accel - current_accel
        return advantage > self.lane_change_threshold
    
    def get_safe_speed(self, distance: float, stopping_distance: float, 
                      safe_time_headway: float) -> float:
        """Calculate safe speed for given conditions"""
        if distance <= stopping_distance:
            return 0.0
        
        # Simple safe speed calculation
        safe_speed = (distance - stopping_distance) / safe_time_headway
        return max(0.0, min(safe_speed, self.desired_speed))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert driver to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'type': self.type.value,
            'vehicle_id': self.vehicle.id if self.vehicle else None,
            'route_id': self.route.id if self.route else None,
            'parameters': {
                'desired_speed': self.desired_speed,
                'time_headway': self.time_headway,
                'min_spacing': self.min_spacing,
                'max_acceleration': self.max_acceleration,
                'comfortable_deceleration': self.comfortable_deceleration,
                'politeness': self.politeness
            }
        }
    
    def __str__(self):
        return f"IDMDriver({self.id}, type={self.type.value})"
    
    def __repr__(self):
        return self.__str__()


class SimpleDriver(DriverInterface):
    """Simple driver implementation for testing"""
    
    def __init__(self, driver_id: int, driver_type: DriverType = DriverType.NORMAL):
        self.id = driver_id
        self.type = driver_type
        self.vehicle: Optional['Vehicle'] = None
        self.route: Optional[Route] = None
        
        # Simple parameters
        self.desired_speed = 30.0  # m/s
        self.reaction_time = 1.0   # s
        self.max_acceleration = 2.0  # m/s²
        self.max_deceleration = 3.0  # m/s²
    
    def get_id(self) -> int:
        return self.id
    
    def get_route(self) -> Optional[Route]:
        return self.route
    
    def set_route(self, route: Route):
        self.route = route
    
    def set_vehicle(self, vehicle: 'Vehicle'):
        self.vehicle = vehicle
        vehicle.driver = self
    
    def get_vehicle(self) -> Optional['Vehicle']:
        return self.vehicle
    
    def drive(self):
        """Simple driving behavior"""
        if not self.vehicle or self.vehicle.state.crashed:
            return
        
        # Simple acceleration based on desired speed
        current_speed = self.vehicle.get_velocity()
        speed_diff = self.desired_speed - current_speed
        
        if speed_diff > 0:
            acceleration = min(self.max_acceleration, speed_diff)
        else:
            acceleration = max(-self.max_deceleration, speed_diff)
        
        self.vehicle.set_acceleration(acceleration)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert driver to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'type': self.type.value,
            'vehicle_id': self.vehicle.id if self.vehicle else None,
            'route_id': self.route.id if self.route else None,
            'desired_speed': self.desired_speed
        }


# Factory function for creating drivers
def create_driver(driver_id: int, driver_type: DriverType = DriverType.IDM) -> DriverInterface:
    """Factory function to create drivers of different types"""
    if driver_type == DriverType.IDM:
        return IDMDriver(driver_id, driver_type)
    else:
        return SimpleDriver(driver_id, driver_type)