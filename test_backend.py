"""
Simple test script to verify the Python backend works
"""
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from python_backend.core.vehicle import Vehicle, LatDirection
from python_backend.core.lane import Lane, LaneType, Coordinate
from python_backend.core.driver import IDMDriver, DriverType, Route
from python_backend.core.model import TrafficSimulationModel, SimulationSettings


def test_basic_functionality():
    """Test basic simulation functionality"""
    print("Testing Traffic Simulation Python Backend...")
    
    # Test Lane creation
    print("1. Creating lanes...")
    lane1 = Lane(0, LaneType.NORMAL, 1000.0)
    lane2 = Lane(1, LaneType.NORMAL, 1000.0)
    lane3 = Lane(2, LaneType.NORMAL, 1000.0)
    
    # Connect lanes
    lane1.set_right_lane(lane2)
    lane2.set_left_lane(lane1)
    lane2.set_right_lane(lane3)
    lane3.set_left_lane(lane2)
    
    print(f"Created lanes: {lane1}, {lane2}, {lane3}")
    
    # Test Vehicle creation
    print("2. Creating vehicles...")
    vehicle1 = Vehicle(1, lane1, 100.0)
    vehicle2 = Vehicle(2, lane2, 200.0)
    
    # Add vehicles to lanes
    lane1.add_vehicle(vehicle1)
    lane2.add_vehicle(vehicle2)
    
    print(f"Created vehicles: {vehicle1}, {vehicle2}")
    
    # Test Driver creation
    print("3. Creating drivers...")
    driver1 = IDMDriver(1, DriverType.NORMAL)
    driver2 = IDMDriver(2, DriverType.AGGRESSIVE)
    
    # Assign drivers to vehicles
    driver1.set_vehicle(vehicle1)
    driver2.set_vehicle(vehicle2)
    
    print(f"Created drivers: {driver1}, {driver2}")
    
    # Test Simulation Model
    print("4. Setting up simulation...")
    model = TrafficSimulationModel.get_instance()
    model.initialize([lane1, lane2, lane3])
    
    print("5. Running simulation steps...")
    for i in range(5):
        print(f"Step {i+1}:")
        
        # Update vehicle surroundings
        for lane in [lane1, lane2, lane3]:
            lane.update_vehicle_surroundings()
        
        # Execute driver behaviors
        driver1.drive()
        driver2.drive()
        
        # Move vehicles
        vehicle1.move(0.1)
        vehicle2.move(0.1)
        
        # Print vehicle states
        print(f"  Vehicle 1: pos={vehicle1.get_x():.1f}, vel={vehicle1.get_velocity():.1f}, acc={vehicle1.get_acceleration():.2f}")
        print(f"  Vehicle 2: pos={vehicle2.get_x():.1f}, vel={vehicle2.get_velocity():.1f}, acc={vehicle2.get_acceleration():.2f}")
    
    print("6. Testing lane change...")
    vehicle1.start_lane_change(LatDirection.RIGHT)
    print(f"Vehicle 1 starting lane change: {vehicle1.is_changing_lane()}")
    
    # Move a few steps to complete lane change
    for i in range(30):
        vehicle1.move(0.1)
        if not vehicle1.is_changing_lane():
            break
    
    print(f"Vehicle 1 after lane change: lane={vehicle1.get_lane().id}, progress={vehicle1.get_lane_change_progress()}")
    
    # Test serialization
    print("7. Testing data serialization...")
    sim_data = model.get_simulation_data()
    print(f"Simulation data keys: {list(sim_data.keys())}")
    print(f"Number of vehicles: {len(sim_data['vehicles'])}")
    print(f"Number of lanes: {len(sim_data['lanes'])}")
    
    print("\nAll tests completed successfully!")
    return True


if __name__ == '__main__':
    try:
        test_basic_functionality()
        print("✓ Backend test passed!")
    except Exception as e:
        print(f"✗ Backend test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)