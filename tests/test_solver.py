import sys
import os
import pytest
import numpy as np

# Add the scripts/model directory to the python path to import the solver
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts', 'model')))

from mva_solver import OpenNetworkMVASolver, ServiceCentre

def test_mm1_single_node():
    """Test a basic M/M/1 queue with known analytical results."""
    # Arrival rate = 10 req/s, Service time = 0.05 s
    # Utilization rho = 10 * 0.05 = 0.5
    # Response time R = 0.05 / (1 - 0.5) = 0.1 s
    centres = [ServiceCentre("NodeA", service_time=0.05, num_servers=1)]
    routing = np.array([[0.0]])
    arrivals = np.array([10.0])
    
    solver = OpenNetworkMVASolver(centres, routing, arrivals)
    results = solver.solve()
    
    assert np.isclose(results.utilizations[0], 0.5), "Utilization calculation failed"
    assert np.isclose(results.mean_response_times[0], 0.1), "Response time calculation failed"
    assert np.isclose(results.system_throughput, 10.0), "Throughput calculation failed"

def test_mmc_multi_server_stability():
    """Test M/M/c Erlang-C solver with large number of servers to ensure it does not overflow."""
    # Arrival rate = 100, Service time = 0.5 -> Offered load (rho) = 50
    # Servers c = 100
    # An unstable math.factorial implementation would crash here.
    centres = [ServiceCentre("NodeA", service_time=0.5, num_servers=100)]
    routing = np.array([[0.0]])
    arrivals = np.array([100.0])
    
    solver = OpenNetworkMVASolver(centres, routing, arrivals)
    results = solver.solve()
    
    # Total utilization (offered load) = 50.0
    assert np.isclose(results.utilizations[0], 50.0)
    
    # Since c=100 and rho=50, the probability of queueing is extremely small,
    # so the response time should essentially be equal to the pure service time.
    assert np.isclose(results.mean_response_times[0], 0.5, atol=0.01)

def test_closed_loop_detection():
    """Test that a fully closed routing loop with no exits raises a ValueError."""
    centres = [
        ServiceCentre("NodeA", service_time=0.1),
        ServiceCentre("NodeB", service_time=0.1)
    ]
    routing = np.array([
        [0.0, 1.0],  # NodeA routes 100% to NodeB
        [1.0, 0.0]   # NodeB routes 100% to NodeA
    ])
    arrivals = np.array([10.0, 0.0])
    
    solver = OpenNetworkMVASolver(centres, routing, arrivals)
    
    with pytest.raises(ValueError, match="fully closed network"):
        solver.solve()

def test_textbook_example_visit_ratios():
    """Test visit ratio and arrival rate formulations against known textbook mathematics."""
    centres = [
        ServiceCentre("N0", 0.04),
        ServiceCentre("N1", 0.06),
        ServiceCentre("N2", 0.03),
    ]
    routing = np.array([
        [0.0, 0.5, 0.0],   # N0 -> N1 (50%), Exit (50%)
        [0.0, 0.0, 0.8],   # N1 -> N2 (80%), Exit (20%)
        [0.3, 0.0, 0.0]    # N2 -> N0 (30%), Exit (70%)
    ])
    external = np.array([5.0, 0.0, 0.0])  # 5 req/s enter N0
    
    solver = OpenNetworkMVASolver(centres, routing, external)
    results = solver.solve()
    
    # Expected analytical arrival rates
    expected_lambda0 = 5.0 / 0.88
    expected_lambda1 = 0.5 * expected_lambda0
    expected_lambda2 = 0.4 * expected_lambda0
    
    assert np.isclose(results.arrival_rates[0], expected_lambda0)
    assert np.isclose(results.arrival_rates[1], expected_lambda1)
    assert np.isclose(results.arrival_rates[2], expected_lambda2)
