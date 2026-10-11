import unittest
import os
import json
import csv
import sys
import numpy as np

# Add project root and scripts dirs to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "scripts", "model"))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "scripts", "validation"))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "scripts", "data_collection"))

from mva_solver import OpenNetworkMVASolver, ServiceCentre
from queueing_network import build_model, get_default_service_times, get_default_routing_matrix, SERVICE_NAMES
from compare import compute_errors


class TestEndToEndPipeline(unittest.TestCase):
    """End-to-End Pipeline Integration Test Suite."""

    def test_01_raw_data_fixture_integrity(self):
        """Test raw trace fixture data integrity for all 11 services."""
        fixture_path = os.path.join(PROJECT_ROOT, "data", "raw", "sample_jaeger_traces.json")
        self.assertTrue(os.path.exists(fixture_path), "sample_jaeger_traces.json fixture missing")

        with open(fixture_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIn("service_demands", data)
        demands = data["service_demands"]
        self.assertEqual(len(demands), 11, "Must contain all 11 microservices")

        for svc in SERVICE_NAMES:
            self.assertIn(svc, demands, f"Service {svc} missing from fixture")
            self.assertGreater(demands[svc]["mean_service_time"], 0.0)

    def test_02_empirical_measurements_csv(self):
        """Test empirical_measurements.csv contains all 11 services including Redis."""
        csv_path = os.path.join(PROJECT_ROOT, "data", "processed", "empirical_measurements.csv")
        self.assertTrue(os.path.exists(csv_path), "empirical_measurements.csv missing")

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))

        svcs = [r["service"] for r in reader]
        self.assertEqual(len(svcs), 11, "CSV must contain 11 microservices")
        self.assertIn("Redis", svcs, "Redis must be present in empirical_measurements.csv")

    def test_03_mva_solver_execution(self):
        """Test MVA solver builds and solves correctly for Online Boutique topology."""
        service_times = get_default_service_times()
        routing_matrix = get_default_routing_matrix()
        arrival_rate = 10.0

        solver = build_model(service_times, routing_matrix, arrival_rate)
        results = solver.solve()

        self.assertEqual(len(results.service_names), 11)
        self.assertAlmostEqual(results.system_throughput, 10.0, places=4)
        # Frontend utilization at lambda=10, S=0.08 should be 0.8
        self.assertAlmostEqual(results.utilizations[0], 0.8, places=4)
        # End-to-end response time should be ~405 ms
        self.assertAlmostEqual(results.system_response_time * 1000, 405.018, delta=1.0)

    def test_04_validation_error_metrics(self):
        """Test compare error computation (RMSE, MAE, WMAPE)."""
        pred = np.array([400.0, 5.09, 3.02, 4.02, 7.55, 5.83, 14.58, 3.81, 9.51, 11.51, 2.01])
        meas = np.array([295.0, 5.00, 3.00, 4.00, 7.50, 5.80, 14.50, 3.80, 9.50, 11.50, 2.00])

        errors = compute_errors(pred, meas)
        self.assertIn("RMSE", errors)
        self.assertIn("MAE", errors)
        self.assertIn("MAPE_%", errors)
        self.assertGreater(errors["RMSE"], 0.0)
        self.assertLess(errors["MAPE_%"], 50.0)


if __name__ == "__main__":
    unittest.main()
