from qiskit_ibm_runtime import QiskitRuntimeService
QiskitRuntimeService.save_account(
    token="ApiKey-c8b311e7-8d43-461b-853c-c7ec10372402",
    channel="ibm_quantum_platform",
    instance="crn:v1:bluemix:public:quantum-computing:us-east:a/6c36eeab611d4a1783e67a7d1af8b674:5ac4719a-f941-432a-b713-2ff6c44b14a4::",   # the long crn:v1:... string from your dashboard
    overwrite=True,
    set_as_default=True,
)