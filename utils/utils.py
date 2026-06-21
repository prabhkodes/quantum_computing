def real_f(input_string):
    if isinstance(input_string, str):
        if len(input_string) == 5 and all(bit in '01' for bit in input_string):
            return 1
        else:
            raise ValueError("Input must be a string with exactly 5 bits (e.g. '01101').")
    else:
        raise ValueError("Input must be a string with exactly 5 bit (e.g. '01101').")

def f(input_string):
    try:
        return real_f(input_string)
    except ValueError as e:
        print("Error:", e) 

from qiskit import QuantumCircuit
import numpy as np

def Uf(num_qubits,seed):
    """
    Create a random Deutsch-Jozsa function.
    """
    np.random.seed(seed)
    qc = QuantumCircuit(num_qubits + 1)
    if np.random.randint(0, 2):
        # Flip output qubit with 50% chance
        qc.x(num_qubits)
    if np.random.randint(0, 2):
        # return constant circuit with 50% chance
        return qc

    # next, choose half the possible input states
    on_states = np.random.choice(
        range(2**num_qubits),  # numbers to sample from
        2**num_qubits // 2,  # number of samples
        replace=False,  # makes sure states are only sampled once
    )

    def add_cx(qc, bit_string):
        for qubit, bit in enumerate(reversed(bit_string)):
            if bit == "1":
                qc.x(qubit)
        return qc

    for state in on_states:
        qc.barrier()  # Barriers are added to help visualize how the functions are created. They can safely be removed.
        qc = add_cx(qc, f"{state:0b}")
        qc.mcx(list(range(num_qubits)), num_qubits)
        qc = add_cx(qc, f"{state:0b}")

    qc.barrier()

    return qc

from scipy.optimize import OptimizeResult

def parameter_shift_rule(circuit, theta):
    num_params = len(theta)
    grad = np.zeros(num_params)
    shift = np.pi / 2
    
    for i in range(num_params):
        shifted_up = theta.copy()
        shifted_down = theta.copy()
        
        shifted_up[i] += shift
        shifted_down[i] -= shift
        
        # Evaluate the circuit with shifted parameters
        expectation_up = circuit(shifted_up)  # Replace with actual function call
        expectation_down = circuit(shifted_down)  # Replace with actual function call
        
        grad[i] = 0.5 * (expectation_up - expectation_down)

    return grad

def adam(fun,x0,jac,args=(),learning_rate=0.1,
            beta1=0.9,
            beta2=0.999,
            eps=1e-8,
            startiter=0,
            maxiter=1000,
            callback=None,
            **kwargs
        ):
                x = x0
                m = np.zeros_like(x)
                v = np.zeros_like(x)

                for i in range(startiter, startiter + maxiter):
                    g = jac(fun,x)

                    if callback and callback(x):
                        break

                    m = (1 - beta1) * g + beta1 * m  # first  moment estimate.
                    v = (1 - beta2) * (g**2) + beta2 * v  # second moment estimate.
                    mhat = m / (1 - beta1**(i + 1))  # bias correction.
                    vhat = v / (1 - beta2**(i + 1))
                    x = x - learning_rate * mhat / (np.sqrt(vhat) + eps)
                return OptimizeResult(x=x, fun=fun(x), jac=g, nit=i, nfev=i, success=True)