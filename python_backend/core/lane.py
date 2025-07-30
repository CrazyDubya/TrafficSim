"""
Lane module - Python equivalent of Java jLane class
Manages a single lane of traffic and vehicle interactions
"""
from typing import List, Optional, Dict, Tuple, Any
from enum import Enum
import math
from dataclasses import dataclass


class LaneType(Enum):
    """Type of lane"""
    NORMAL = "NORMAL"
    ACCELERATION = "ACCELERATION"
    DECELERATION = "DECELERATION"
    EXIT = "EXIT"
    ENTRANCE = "ENTRANCE"


@dataclass
class Coordinate:
    """2D coordinate point"""
    x: float
    y: float


class Lane:
    """Main lane implementation - Python equivalent of Java jLane class"""
    
    def __init__(self, lane_id: int, lane_type: LaneType = LaneType.NORMAL, 
                 length: float = 1000.0, coordinates: Optional[List[Coordinate]] = None):
        self.id = lane_id
        self.type = lane_type
        self.length = length  # Lane length [m]
        
        # Lane geometry
        if coordinates:
            self.coordinates = coordinates
        else:
            # Default straight lane
            self.coordinates = [
                Coordinate(0.0, 0.0),
                Coordinate(length, 0.0)
            ]
        
        # Lane connections
        self.upstream_lane: Optional['Lane'] = None
        self.downstream_lane: Optional['Lane'] = None
        self.left_lane: Optional['Lane'] = None
        self.right_lane: Optional['Lane'] = None
        self.taper_lane: Optional['Lane'] = None
        
        # Vehicles on this lane
        self.vehicles: List['Vehicle'] = []
        
        # Traffic generators
        self.generators: List['TrafficGenerator'] = []
        
        # Road-side units (detectors, traffic lights, etc.)
        self.rsus: List['RSU'] = []
        
        # Observers
        self.observers: List['Observer'] = []
        
        # Speed limit [m/s]
        self.speed_limit = 33.33  # ~120 km/h default
        
        # Lane properties
        self.width = 3.5  # Standard lane width [m]
        
    def add_vehicle(self, vehicle: 'Vehicle'):
        """Add vehicle to this lane"""
        if vehicle not in self.vehicles:
            self.vehicles.append(vehicle)
            # Sort vehicles by position for efficient neighbor finding
            self.vehicles.sort(key=lambda v: v.get_x())
            
            # Update vehicle's lane reference
            vehicle.lane = self
            
            # Notify observers
            for observer in self.observers:
                observer.observe_vehicle_added(self, vehicle)
    
    def remove_vehicle(self, vehicle: 'Vehicle'):
        """Remove vehicle from this lane"""
        if vehicle in self.vehicles:
            self.vehicles.remove(vehicle)
            
            # Notify observers
            for observer in self.observers:
                observer.observe_vehicle_removed(self, vehicle)
    
    def get_vehicles(self) -> List['Vehicle']:
        """Get all vehicles on this lane"""
        return self.vehicles.copy()
    
    def get_vehicle_count(self) -> int:
        """Get number of vehicles on this lane"""
        return len(self.vehicles)
    
    def get_leading_vehicle(self, position: float) -> Optional['Vehicle']:
        """Get the vehicle ahead of given position"""
        candidates = [v for v in self.vehicles if v.get_x() > position]
        if candidates:
            return min(candidates, key=lambda v: v.get_x())
        return None
    
    def get_following_vehicle(self, position: float) -> Optional['Vehicle']:
        """Get the vehicle behind given position"""
        candidates = [v for v in self.vehicles if v.get_x() < position]
        if candidates:
            return max(candidates, key=lambda v: v.get_x())
        return None
    
    def get_neighbors(self, vehicle: 'Vehicle') -> Dict[str, Optional['Vehicle']]:
        """Get neighboring vehicles for a given vehicle"""
        position = vehicle.get_x()
        
        neighbors = {
            'leader': self.get_leading_vehicle(position),
            'follower': self.get_following_vehicle(position)
        }
        
        # Add lateral neighbors if adjacent lanes exist
        if self.left_lane:
            neighbors['left_leader'] = self.left_lane.get_leading_vehicle(position)
            neighbors['left_follower'] = self.left_lane.get_following_vehicle(position)
        
        if self.right_lane:
            neighbors['right_leader'] = self.right_lane.get_leading_vehicle(position)
            neighbors['right_follower'] = self.right_lane.get_following_vehicle(position)
        
        return neighbors
    
    def update_vehicle_surroundings(self):
        """Update surrounding vehicle information for all vehicles on this lane"""
        from .vehicle import Enclosure
        
        for vehicle in self.vehicles:
            neighbors = self.get_neighbors(vehicle)
            
            # Update enclosure mapping
            vehicle.update_surrounding(Enclosure.FRONT, neighbors.get('leader'))
            vehicle.update_surrounding(Enclosure.BACK, neighbors.get('follower'))
            vehicle.update_surrounding(Enclosure.LEFT_FRONT, neighbors.get('left_leader'))
            vehicle.update_surrounding(Enclosure.LEFT_BACK, neighbors.get('left_follower'))
            vehicle.update_surrounding(Enclosure.RIGHT_FRONT, neighbors.get('right_leader'))
            vehicle.update_surrounding(Enclosure.RIGHT_BACK, neighbors.get('right_follower'))
    
    def get_density(self) -> float:
        """Calculate traffic density [vehicles/km]"""
        if self.length <= 0:
            return 0.0
        return (len(self.vehicles) / self.length) * 1000.0
    
    def get_flow(self) -> float:
        """Calculate traffic flow [vehicles/hour] - simplified calculation"""
        if not self.vehicles:
            return 0.0
        
        avg_speed = sum(v.get_velocity() for v in self.vehicles) / len(self.vehicles)
        density = self.get_density()
        
        # Flow = density * speed (converted to vehicles/hour)
        return density * avg_speed * 3.6
    
    def get_average_speed(self) -> float:
        """Get average speed of vehicles on this lane [m/s]"""
        if not self.vehicles:
            return 0.0
        return sum(v.get_velocity() for v in self.vehicles) / len(self.vehicles)
    
    def is_safe_lane_change(self, vehicle: 'Vehicle', target_lane: 'Lane', 
                           min_gap: float = 10.0) -> bool:
        """Check if lane change is safe"""
        if target_lane is None:
            return False
        
        position = vehicle.get_x()
        
        # Check gap with leader in target lane
        leader = target_lane.get_leading_vehicle(position)
        if leader:
            gap_leader = leader.get_x() - position - vehicle.length
            if gap_leader < min_gap:
                return False
        
        # Check gap with follower in target lane
        follower = target_lane.get_following_vehicle(position)
        if follower:
            gap_follower = position - follower.get_x() - follower.length
            if gap_follower < min_gap:
                return False
        
        return True
    
    def get_coordinate_at_distance(self, distance: float) -> Coordinate:
        """Get coordinate at given distance along the lane"""
        if distance <= 0:
            return self.coordinates[0]
        if distance >= self.length:
            return self.coordinates[-1]
        
        # Simple linear interpolation for now
        # In a more sophisticated implementation, this would handle curves
        ratio = distance / self.length
        start = self.coordinates[0]
        end = self.coordinates[-1]
        
        return Coordinate(
            start.x + ratio * (end.x - start.x),
            start.y + ratio * (end.y - start.y)
        )
    
    def get_heading_at_distance(self, distance: float) -> float:
        """Get lane heading (angle) at given distance"""
        # Simplified: assume straight lane
        if len(self.coordinates) < 2:
            return 0.0
        
        start = self.coordinates[0]
        end = self.coordinates[-1]
        
        return math.atan2(end.y - start.y, end.x - start.x)
    
    # Lane connection methods
    def set_upstream_lane(self, lane: 'Lane'):
        """Set upstream (feeding) lane"""
        self.upstream_lane = lane
        if lane:
            lane.downstream_lane = self
    
    def set_downstream_lane(self, lane: 'Lane'):
        """Set downstream (receiving) lane"""
        self.downstream_lane = lane
        if lane:
            lane.upstream_lane = self
    
    def set_left_lane(self, lane: 'Lane'):
        """Set left adjacent lane"""
        self.left_lane = lane
        if lane:
            lane.right_lane = self
    
    def set_right_lane(self, lane: 'Lane'):
        """Set right adjacent lane"""
        self.right_lane = lane
        if lane:
            lane.left_lane = self
    
    def get_left_lane(self) -> Optional['Lane']:
        """Get left adjacent lane"""
        return self.left_lane
    
    def get_right_lane(self) -> Optional['Lane']:
        """Get right adjacent lane"""
        return self.right_lane
    
    def get_upstream_lane(self) -> Optional['Lane']:
        """Get upstream lane"""
        return self.upstream_lane
    
    def get_downstream_lane(self) -> Optional['Lane']:
        """Get downstream lane"""
        return self.downstream_lane
    
    # RSU (Road Side Unit) management
    def add_rsu(self, rsu: 'RSU'):
        """Add road-side unit (detector, traffic light, etc.)"""
        if rsu not in self.rsus:
            self.rsus.append(rsu)
            rsu.set_lane(self)
    
    def remove_rsu(self, rsu: 'RSU'):
        """Remove road-side unit"""
        if rsu in self.rsus:
            self.rsus.remove(rsu)
    
    def get_rsus(self) -> List['RSU']:
        """Get all road-side units on this lane"""
        return self.rsus.copy()
    
    # Observer pattern
    def add_observer(self, observer: 'Observer'):
        """Add observer for lane events"""
        if observer not in self.observers:
            self.observers.append(observer)
    
    def remove_observer(self, observer: 'Observer'):
        """Remove observer"""
        if observer in self.observers:
            self.observers.remove(observer)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert lane to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'type': self.type.value,
            'length': self.length,
            'width': self.width,
            'speed_limit': self.speed_limit,
            'vehicle_count': len(self.vehicles),
            'density': self.get_density(),
            'average_speed': self.get_average_speed(),
            'coordinates': [{'x': c.x, 'y': c.y} for c in self.coordinates],
            'connections': {
                'upstream': self.upstream_lane.id if self.upstream_lane else None,
                'downstream': self.downstream_lane.id if self.downstream_lane else None,
                'left': self.left_lane.id if self.left_lane else None,
                'right': self.right_lane.id if self.right_lane else None
            }
        }
    
    def __str__(self):
        return f"Lane({self.id}, type={self.type.value}, vehicles={len(self.vehicles)})"
    
    def __repr__(self):
        return self.__str__()


# Observer interface for lane events
class Observer:
    """Observer interface for monitoring lane changes"""
    
    def observe_vehicle_added(self, lane: Lane, vehicle: 'Vehicle'):
        """Called when vehicle is added to lane"""
        pass
    
    def observe_vehicle_removed(self, lane: Lane, vehicle: 'Vehicle'):
        """Called when vehicle is removed from lane"""
        pass