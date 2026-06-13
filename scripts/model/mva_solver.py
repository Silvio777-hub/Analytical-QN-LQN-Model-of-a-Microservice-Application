"""
Open Queueing Network - Mean Value Analysis (MVA) Solver

Implements the MVA algorithm for open queueing networks where each
service centre is modelled as an M/M/1 or M/M/c queue.

Theory:
  For an open network with K service centres:
    - External arrival rate: λ₀
    - Routing matrix: P[i][j] = probability of going from centre i to j
    - Service demand at centre i: D_i = V_i * S_i
      where V_i = visit ratio, S_i = mean service time
    - Utilization: ρ_i = λ_i * S_i  (for M/M/1)
    - Mean response time: R_i = S_i / (1 - ρ_i)  (for M/M/1)
    - Mean number in system: N_i = ρ_i / (1 - ρ_i)  (Little's Law)

References:
  - Lazowska et al., "Quantitative System Performance", 1984
  - Bolch et al., "Queueing Networks and Markov Chains", 2006
"""

import math
import numpy as np
from dataclasses import dataclass


@dataclass
class ServiceCentre:
    """Represents a single service centre (queueing station) in the network."""
    name: str
    service_time: float      # Mean service time S_i (seconds)
    num_servers: int = 1     # Number of parallel servers (c_i), 1 = M/M/1
    scheduling: str = "FCFS" # Scheduling discipline

    def __post_init__(self):
        if self.num_servers < 1:
            raise ValueError(f"ServiceCentre '{self.name}' must have at least 1 server (num_servers={self.num_servers}).")


@dataclass
class MVAResults:
    """Results from solving an open queueing network."""
    service_names: list
    arrival_rates: np.ndarray        # λ_i at each centre
    visit_ratios: np.ndarray         # V_i at each centre
    utilizations: np.ndarray         # ρ_i at each centre
    mean_response_times: np.ndarray  # R_i at each centre
    mean_queue_lengths: np.ndarray   # N_i at each centre
    mean_num_in_service: np.ndarray  # Number being served
    throughputs: np.ndarray          # X_i at each centre
    system_throughput: float         # Overall system throughput
    system_response_time: float      # End-to-end response time

    def summary(self) -> str:
        """Return a formatted summary table of results."""
        lines = []
        lines.append("=" * 90)
        lines.append(f"{'Service Centre':<25} {'Arr.Rate':>8} {'Util':>8} {'R_i (ms)':>10} "
                      f"{'N_i':>8} {'X_i':>8} {'V_i':>8}")
        lines.append("-" * 90)
        for i, name in enumerate(self.service_names):
            lines.append(
                f"{name:<25} "
                f"{self.arrival_rates[i]:>8.3f} "
                f"{self.utilizations[i]:>8.4f} "
                f"{self.mean_response_times[i]*1000:>10.2f} "
                f"{self.mean_queue_lengths[i]:>8.4f} "
                f"{self.throughputs[i]:>8.3f} "
                f"{self.visit_ratios[i]:>8.3f}"
            )
        lines.append("-" * 90)
        lines.append(f"System throughput:     {self.system_throughput:.4f} req/s")
        lines.append(f"System response time:  {self.system_response_time*1000:.2f} ms")
        lines.append("=" * 90)
        return "\n".join(lines)


class OpenNetworkMVASolver:
    """
    Solves an open queueing network using Mean Value Analysis.

    An open network has external arrivals and departures. Each service centre
    is modelled as either M/M/1 or M/M/c depending on the number of servers.
    """

    def __init__(self, centres: list[ServiceCentre], routing_matrix: np.ndarray,
                 external_arrivals: np.ndarray):
        """
        Initialize the solver.

        Args:
            centres: List of ServiceCentre objects.
            routing_matrix: K×K matrix where P[i][j] = probability of routing
                           from centre i to centre j after service.
            external_arrivals: K-length vector where λ₀_i = external arrival
                              rate to centre i (typically only the frontend
                              has non-zero external arrivals).
        """
        self.centres = centres
        self.K = len(centres)
        self.P = np.array(routing_matrix, dtype=float)
        self.lambda_ext = np.array(external_arrivals, dtype=float)

        if self.P.shape != (self.K, self.K):
            raise ValueError(f"Routing matrix must be {self.K}x{self.K}")
        if self.lambda_ext.shape != (self.K,):
            raise ValueError(f"External arrivals must have {self.K} elements")

    def compute_visit_ratios(self) -> tuple[np.ndarray, np.ndarray]:
        """
        Compute visit ratios V_i by solving the traffic equations:
            λ_i = λ₀_i + Σ_j λ_j * P[j][i]

        The visit ratio V_i = λ_i / λ_total where λ_total = Σ λ₀_i

        Returns:
            Tuple of (lambdas, visit_ratios) as length K vectors.
        """
        # Solve: λ = λ₀ + P^T · λ  =>  (I - P^T) · λ = λ₀
        identity_matrix = np.eye(self.K)
        A = identity_matrix - self.P.T
        try:
            lambdas = np.linalg.solve(A, self.lambda_ext)
        except np.linalg.LinAlgError:
            raise ValueError(
                "Traffic equations are unsolvable — fully closed network detected. "
                "Routing matrix rows must not sum to 1.0 for all service centres."
            )

        total_external = np.sum(self.lambda_ext)
        if total_external > 0:
            visit_ratios = lambdas / total_external
        else:
            visit_ratios = lambdas

        return lambdas, visit_ratios

    def _response_time_mm1(self, service_time: float, utilization: float) -> float:
        """Mean response time for M/M/1: R = S / (1 - ρ)"""
        if utilization >= 1.0:
            return float('inf')
        return service_time / (1.0 - utilization)

    def _response_time_mmc(self, service_time: float, utilization: float,
                            c: int) -> float:
        """
        Mean response time for M/M/c queue.
        Uses Erlang-C formula for the probability of queueing.
        """
        if c == 1:
            return self._response_time_mm1(service_time, utilization)

        rho = utilization  # total utilization = λ*S
        rho_per_server = rho / c

        if rho_per_server >= 1.0:
            return float('inf')

        # Erlang-C formula: P(queueing)
        # C(c, a) where a = λ * S = ρ (offered load)
        a = rho
        sum_terms = sum((a ** k) / math.factorial(k) for k in range(c))
        last_term = (a ** c) / math.factorial(c) * (1.0 / (1.0 - rho_per_server))
        prob_queue = last_term / (sum_terms + last_term)

        # Mean response time for M/M/c
        mean_wait = prob_queue * service_time / (c * (1.0 - rho_per_server))
        return service_time + mean_wait

    def solve(self) -> MVAResults:
        """
        Solve the open queueing network.

        Returns:
            MVAResults object containing all performance metrics.

        Raises:
            ValueError: If any service centre is saturated (ρ >= 1).
        """
        # Step 1: Compute arrival rates and visit ratios
        lambdas, visit_ratios = self.compute_visit_ratios()

        # Step 2: Compute per-centre metrics
        utilizations = np.zeros(self.K)
        response_times = np.zeros(self.K)
        queue_lengths = np.zeros(self.K)
        num_in_service = np.zeros(self.K)

        for i in range(self.K):
            S_i = self.centres[i].service_time
            c_i = self.centres[i].num_servers
            lambda_i = lambdas[i]

            # Utilization
            rho_i = lambda_i * S_i  # Total offered load
            utilizations[i] = rho_i

            if c_i == 1:
                # M/M/1 queue
                if rho_i >= 1.0:
                    raise ValueError(
                        f"Service centre '{self.centres[i].name}' is saturated: "
                        f"ρ = {rho_i:.4f} >= 1.0. Reduce arrival rate or "
                        f"increase service rate."
                    )
                response_times[i] = self._response_time_mm1(S_i, rho_i)
                queue_lengths[i] = rho_i / (1.0 - rho_i)
                num_in_service[i] = rho_i
            else:
                # M/M/c queue
                rho_per_server = rho_i / c_i
                if rho_per_server >= 1.0:
                    raise ValueError(
                        f"Service centre '{self.centres[i].name}' is saturated: "
                        f"ρ/c = {rho_per_server:.4f} >= 1.0."
                    )
                response_times[i] = self._response_time_mmc(S_i, rho_i, c_i)
                # Mean number in system via Little's Law
                queue_lengths[i] = lambda_i * response_times[i]
                num_in_service[i] = rho_i

        # Step 3: System-level metrics
        throughputs = lambdas.copy()
        system_throughput = np.sum(self.lambda_ext)
        # End-to-end response time = sum of R_i * V_i
        system_response_time = np.sum(response_times * visit_ratios)

        return MVAResults(
            service_names=[c.name for c in self.centres],
            arrival_rates=lambdas,
            visit_ratios=visit_ratios,
            utilizations=utilizations,
            mean_response_times=response_times,
            mean_queue_lengths=queue_lengths,
            mean_num_in_service=num_in_service,
            throughputs=throughputs,
            system_throughput=system_throughput,
            system_response_time=system_response_time,
        )


def run_textbook_test():
    """
    Verify the solver with a known textbook example.

    Example: 3-node open network
      - External arrivals: λ₀ = [5, 0, 0] req/s (all arrive at node 0)
      - Service times: S = [0.04, 0.06, 0.03] seconds
      - Routing: node0→node1 (0.5), node0→exit (0.5)
                 node1→node2 (0.8), node1→exit (0.2)
                 node2→node0 (0.3), node2→exit (0.7)
    """
    print("=" * 60)
    print("TEXTBOOK VERIFICATION TEST")
    print("=" * 60)
    print()

    centres = [
        ServiceCentre(name="Node_0", service_time=0.04),
        ServiceCentre(name="Node_1", service_time=0.06),
        ServiceCentre(name="Node_2", service_time=0.03),
    ]

    # Routing matrix P[i][j]
    routing = np.array([
        [0.0, 0.5, 0.0],   # Node 0 → Node 1 (50%), exit (50%)
        [0.0, 0.0, 0.8],   # Node 1 → Node 2 (80%), exit (20%)
        [0.3, 0.0, 0.0],   # Node 2 → Node 0 (30%), exit (70%)
    ])

    external = np.array([5.0, 0.0, 0.0])  # 5 req/s arrive at Node 0

    solver = OpenNetworkMVASolver(centres, routing, external)
    results = solver.solve()
    print(results.summary())
    print()

    # Verify traffic equations manually
    # λ₀ = 5 + 0.3*λ₂
    # λ₁ = 0.5*λ₀
    # λ₂ = 0.8*λ₁
    # λ₂ = 0.8 * 0.5 * λ₀ = 0.4*λ₀
    # λ₀ = 5 + 0.3*0.4*λ₀ = 5 + 0.12*λ₀
    # 0.88*λ₀ = 5 => λ₀ = 5.6818...
    expected_lambda0 = 5.0 / 0.88
    expected_lambda1 = 0.5 * expected_lambda0
    expected_lambda2 = 0.4 * expected_lambda0

    print("Verification of arrival rates:")
    print(f"  L0: computed={results.arrival_rates[0]:.4f}, "
          f"expected={expected_lambda0:.4f}")
    print(f"  L1: computed={results.arrival_rates[1]:.4f}, "
          f"expected={expected_lambda1:.4f}")
    print(f"  L2: computed={results.arrival_rates[2]:.4f}, "
          f"expected={expected_lambda2:.4f}")

    # Check results
    assert abs(results.arrival_rates[0] - expected_lambda0) < 0.001
    assert abs(results.arrival_rates[1] - expected_lambda1) < 0.001
    assert abs(results.arrival_rates[2] - expected_lambda2) < 0.001
    print("\n[OK] All verification checks passed!")


if __name__ == "__main__":
    import sys
    if "--test" in sys.argv:
        run_textbook_test()
    else:
        print("Usage: python mva_solver.py --test")
        print("  --test  Run textbook verification example")
        print()
        print("For Online Boutique model, run: python queueing_network.py")
