# Sends ONE sampling job to a real IBM device using angles trained in qaoa.py,
# then decodes the returned bitstrings into a route. Prints the job ID so you can find it on the dashboard.

import json
import os

from qiskit.circuit.library import QAOAAnsatz
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
from qiskit_optimization.converters import QuadraticProgramToQubo

import graph
import qubo
import classical

# ---------------- TEMPORARY ACCOUNT INFO ----------------
IBM_TOKEN = ""
IBM_INSTANCE = ""  
IBM_CHANNEL = "ibm_quantum_platform"
# --------------------------------------------------------

HERE = os.path.dirname(os.path.abspath(__file__))

REPS = 1
SHOTS = 100          # connection test first; raise to ~4000 later
INSTANCE = None      # paste your instance CRN here ("crn:v1:...") if you have more than one


def run_on_hardware(qp, optimal_point, reps, shots):
    qubo_prob = QuadraticProgramToQubo().convert(qp)
    hamiltonian, _offset = qubo_prob.to_ising()

    circuit = QAOAAnsatz(hamiltonian, reps=reps)
    circuit.measure_all()
    circuit = circuit.assign_parameters(optimal_point)

    print("1. Connecting to IBM...")
    service = QiskitRuntimeService(channel=IBM_CHANNEL, token=IBM_TOKEN, instance=IBM_INSTANCE)
    backend = service.least_busy(operational=True, simulator=False,
                                 min_num_qubits=circuit.num_qubits)
    print("2. Backend chosen:", backend.name)

    pm = generate_preset_pass_manager(
    backend=backend,
    optimization_level=3,
    translation_method="translator",
)
    isa_circuit = pm.run(circuit)
    print("3. Transpiled. Gate counts:", dict(isa_circuit.count_ops()))

    sampler = SamplerV2(mode=backend)
    job = sampler.run([isa_circuit], shots=shots)
    print("4. SUBMITTED. Job ID:", job.job_id())
    print("   Waiting for the queue (this can take minutes)...")

    result = job.result()
    print("5. Job finished.")
    counts = result[0].data.meas.get_counts()
    return counts, backend.name, job.job_id()


def decode_counts(counts, qp, arcs, start, end, best_x):
    total = sum(counts.values())
    p_valid = p_opt = 0
    best_path, best_cost = None, float("inf")
    for bitstr, n in counts.items():
        x = [int(b) for b in reversed(bitstr)]  # Qiskit prints qubit 0 on the RIGHT
        if not qp.get_feasibility_info(x)[0]:
            continue
        p_valid += n / total
        if x == [int(v) for v in best_x]:
            p_opt += n / total
        cost = qp.objective.evaluate(x)
        if cost < best_cost:
            best_cost, best_path = cost, qubo.decode_path(x, arcs, start, end)
    return best_path, p_valid, p_opt


if __name__ == "__main__":
    start, end = graph.example_map.nodes[0].name, graph.example_map.nodes[-1].name
    qp, arcs = qubo.build_qubo(graph.example_map, start, end)
    best_x, _, best_path = classical.brute_force(qp, arcs, start, end)

    with open(os.path.join(HERE, f"angles_reps{REPS}.json")) as f:
        optimal_point = json.load(f)

    counts, backend_name, job_id = run_on_hardware(qp, optimal_point, REPS, SHOTS)

    with open(os.path.join(HERE, f"counts_reps{REPS}_{backend_name}.json"), "w") as f:
        json.dump(counts, f)

    path, p_valid, p_opt = decode_counts(counts, qp, arcs, start, end, best_x)
    print("Best valid route (from hardware samples):", " -> ".join(path) if path else "none found")
    print(f"P(valid) = {p_valid:.4f} | P(optimal) = {p_opt:.4f}")
