# Runs QAOA on the QUBO from qubo.py at several depths (reps), decodes the results back into routes,
# and reports how often the optimal route shows up. Uses the ideal (noise-free) simulator.

import json
import os

import numpy as np
from qiskit.primitives import Sampler
from qiskit_algorithms import QAOA
from qiskit_algorithms.optimizers import COBYLA
from qiskit_algorithms.utils import algorithm_globals
from qiskit_optimization.algorithms import MinimumEigenOptimizer

import classical
import graph
import qubo

HERE = os.path.dirname(os.path.abspath(__file__))


def run_qaoa(qp, reps=1, maxiter=100, seed=42):
    algorithm_globals.random_seed = seed  # makes runs repeatable for the demo
    qaoa = QAOA(sampler=Sampler(), optimizer=COBYLA(maxiter=maxiter), reps=reps)
    return MinimumEigenOptimizer(qaoa).solve(qp)


def save_angles(result, reps):
    point = [float(a) for a in result.min_eigen_solver_result.optimal_point]
    out_path = os.path.join(HERE, f"angles_reps{reps}.json")
    with open(out_path, "w") as f:
        json.dump(point, f)
    print(f"  Saved {len(point)} angles to {out_path}")


def summarize(result, arcs, start, end, best_x):
    """Pull out the headline numbers from a QAOA result."""
    p_optimal = sum(s.probability for s in result.samples if np.array_equal(np.round(s.x), best_x))
    p_valid = sum(s.probability for s in result.samples if s.status.name == "SUCCESS")
    path = qubo.decode_path(result.x, arcs, start, end)
    return path, p_optimal, p_valid  # <- this line was missing


if __name__ == "__main__":  # <- this whole block was missing
    start, end = graph.example_map.nodes[0].name, graph.example_map.nodes[-1].name
    qp, arcs = qubo.build_qubo(graph.example_map, start, end)

    best_x, best_cost, best_path = classical.brute_force(qp, arcs, start, end)
    print("Classical optimum:", " -> ".join(best_path))

    for reps in (1, 2, 3):
        result = run_qaoa(qp, reps=reps)
        save_angles(result, reps)
        path, p_opt, p_valid = summarize(result, arcs, start, end, best_x)
        print(f"\nreps={reps}")
        print("  QAOA route:           ", " -> ".join(path) if path else "invalid")
        print(f"  P(optimal route):      {p_opt:.4f}")
        print(f"  P(any valid route):    {p_valid:.4f}")
        print(f"  Random-guess baseline: {1 / 2**len(arcs):.5f}")