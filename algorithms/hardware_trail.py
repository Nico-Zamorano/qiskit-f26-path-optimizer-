# Takes angles trained on the simulator, runs ONE sampling job on a real IBM device,
# and decodes the bitstrings back into routes. Does not train anything.

from qiskit.circuit.library import QAOAAnsatz
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
from qiskit_optimization.converters import QuadraticProgramToQubo


def run_on_hardware(qp, optimal_point, reps, shots=4000):
    qubo_prob = QuadraticProgramToQubo().convert(qp)
    hamiltonian, _offset = qubo_prob.to_ising()

    circuit = QAOAAnsatz(hamiltonian, reps=reps)
    circuit.measure_all()
    circuit = circuit.assign_parameters(optimal_point)

    service = QiskitRuntimeService()  # assumes you've saved your API key
    backend = service.least_busy(operational=True, simulator=False,
                                 min_num_qubits=circuit.num_qubits)

    pm = generate_preset_pass_manager(backend=backend, optimization_level=3)
    isa_circuit = pm.run(circuit)  # rewrites to native gates + chip connectivity
    print("Backend:", backend.name, "| 2-qubit gates:", isa_circuit.count_ops())

    job = SamplerV2(mode=backend).run([isa_circuit], shots=shots)
    counts = job.result()[0].data.meas.get_counts()
    return counts, backend.name


def decode_counts(counts, qp, arcs, start, end, best_x):
    """Return (best valid path, P(valid), P(optimal))."""
    import qubo
    total = sum(counts.values())
    p_valid = p_opt = 0
    best_path, best_cost = None, float("inf")
    for bitstr, n in counts.items():
        x = [int(b) for b in reversed(bitstr)]  # Qiskit prints qubit 0 on the RIGHT
        if not qp.get_feasibility_info(x)[0]:
            continue
        p_valid += n / total
        if x == list(best_x):
            p_opt += n / total
        cost = qp.objective.evaluate(x)
        if cost < best_cost:
            best_cost, best_path = cost, qubo.decode_path(x, arcs, start, end)
    return best_path, p_valid, p_opt