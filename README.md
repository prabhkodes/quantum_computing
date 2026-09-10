# quantum_computing

![Qiskit](https://img.shields.io/badge/Qiskit-6929C4?style=flat-square&logo=qiskit&logoColor=white)
![Cirq](https://img.shields.io/badge/Cirq-4285F4?style=flat-square&logo=google&logoColor=white)
![D-Wave Ocean](https://img.shields.io/badge/D--Wave%20Ocean-008CD7?style=flat-square&logoColor=white)
![PyQUBO](https://img.shields.io/badge/PyQUBO-FF6200?style=flat-square&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)

Two ways of computing with quantum hardware, and they have almost nothing in common: **gate-model
circuits**, where you build a unitary out of gates, and **quantum annealing**, where you encode a
combinatorial problem as an energy landscape and let the hardware relax into its minimum.

| Track | What it covers | Runs on |
|---|---|---|
| [`notebooks/gate-model/`](notebooks/gate-model/) | Circuits, entanglement, and the textbook oracle algorithms | Qiskit and Cirq simulators |
| [`notebooks/qubo-annealing/`](notebooks/qubo-annealing/) | Real optimisation problems reduced to QUBO | Classical annealer (`neal`) **and D-Wave QPU** |

---

## Annealing: everything is one equation

A quantum annealer solves exactly one problem — minimise a quadratic form over binary variables:

```
minimise   E(x) = Σᵢ Qᵢᵢ xᵢ  +  Σᵢ<ⱼ Qᵢⱼ xᵢxⱼ        xᵢ ∈ {0,1}
```

So all the work is *reduction*: getting your problem into that shape. These notebooks build up the
techniques one constraint type at a time.

### Antenna placement — a progression

Place antennas to **maximise coverage while minimising interference**. Each candidate position *i* has
coverage `Aᵢ = πRᵢ²`; two antennas interfere when `Rᵢ + Rⱼ > d(i,j)`. That makes an interference graph,
and the problem becomes **maximum weighted independent set** on it.

| Notebook | Technique |
|---|---|
| [`qubo_antenna_placement`](notebooks/qubo-annealing/qubo_antenna_placement.ipynb) | The base formulation — reward coverage, penalise interfering pairs |
| [`qubo_antenna_equal_constraint`](notebooks/qubo-annealing/qubo_antenna_equal_constraint.ipynb) | Equality constraints via a squared penalty `λ(Σxᵢ − k)²` |
| [`qubo_antenna_linear_constraint`](notebooks/qubo-annealing/qubo_antenna_linear_constraint.ipynb) | General linear constraints |
| [`qubo_antenna_leq_constraint`](notebooks/qubo-annealing/qubo_antenna_leq_constraint.ipynb) | Inequalities — the hard case, needing slack variables |
| [`qubo_antenna_higher_order`](notebooks/qubo-annealing/qubo_antenna_higher_order.ipynb) | Cubic and higher terms, reduced to quadratic |

→ **Inequalities are the interesting one.** A QUBO has no `≤`. You introduce a slack variable and encode
it in binary — `m = ⌈log₂(B+1)⌉` auxiliary bits — so `Σcᵢxᵢ + Σ2ʲyⱼ = B` enforces `Σcᵢxᵢ ≤ B` exactly.
Logarithmic rather than one-hot, so a budget of 100 costs 7 extra qubits instead of 100.
See [`utils/cost.py`](utils/cost.py).

→ **Higher-order terms have to go.** The hardware is quadratic by construction, so a cubic term
`x₁x₂x₃` is replaced by an auxiliary variable plus a penalty that forces `y = x₁x₂`. Every reduction
costs qubits, which is why formulation quality matters more than solver choice.

### Other reductions

| Notebook | Problem |
|---|---|
| [`pyqubo_intro`](notebooks/qubo-annealing/pyqubo_intro.ipynb) | Building and compiling QUBOs symbolically |
| [`game_of_switches`](notebooks/qubo-annealing/game_of_switches.ipynb) | A combinatorial switch puzzle as an energy minimum |
| [`budget_optimisation`](notebooks/qubo-annealing/budget_optimisation.ipynb) | Knapsack — maximise value under a budget, using the slack encoding above |

### Classical and quantum, same QUBO

Each problem is solved twice:

```python
neal.SimulatedAnnealingSampler()              # classical, runs anywhere
EmbeddingComposite(DWaveSampler())            # real D-Wave QPU
```

`EmbeddingComposite` handles **minor-embedding** — mapping logical variables onto the QPU's physical
qubit graph, where a single logical variable often becomes a *chain* of physical qubits because the
hardware topology isn't fully connected.

→ **The QUBO is hardware-agnostic; only the sampler changes.** That's the practical argument for the
formulation work: it outlives whichever annealer you point it at.

## Gate model

| Notebook | Contents |
|---|---|
| [`qiskit_entanglement`](notebooks/gate-model/qiskit_entanglement.ipynb) | Circuits, superposition, Bell states, measurement statistics |
| [`quantum_algorithms`](notebooks/gate-model/quantum_algorithms.ipynb) | Deutsch–Jozsa, Bernstein–Vazirani, quantum phase estimation |
| [`grovers_cirq`](notebooks/gate-model/grovers_cirq.ipynb) | Grover's search in Cirq |

Deutsch–Jozsa and Bernstein–Vazirani are the two cleanest demonstrations that quantum parallelism buys
something: both decide in **one** oracle query what classically needs many. Phase estimation is the more
consequential one — it's the subroutine underneath Shor's algorithm and quantum chemistry.

[`utils/utils.py`](utils/utils.py) has the oracle construction (`Uf`) plus a **parameter-shift rule**
and a hand-written **Adam** optimiser — the machinery for variational circuits, where gradients are
obtained by evaluating the circuit at shifted parameter values rather than by backpropagation.

## Running

```bash
pip install qiskit qiskit-aer cirq pyqubo dwave-ocean-sdk neal networkx matplotlib
jupyter lab
```

The classical sampler runs anywhere. The D-Wave cells need a
[Leap](https://cloud.dwavesys.com/leap/) API token:

```bash
dwave config create
```

## Caveats

| Caveat | Detail |
|---|---|
| **The five antenna notebooks have no stored outputs** | They need re-running to render on GitHub. The gate-model ones do have outputs |
| **Penalty weights are hand-tuned** | Set λ too low and constraints are violated; too high and the objective is swamped. No systematic sweep here |
| **Small problems** | Tens of variables — enough to show the encodings, far below where annealing versus classical solvers becomes an interesting question |
| **No claim of quantum advantage** | Simulated annealing solves all of these fine. The point is the reduction technique, not the speedup |

## Where this came from

| | |
|---|---|
| Course | *P2.5 — Quantum Computing*, Master's in High Performance Computing, ICTP &amp; SISSA, Trieste, 2025–26 |
| Related | [`federated-learning-nextflow`](https://github.com/prabhkodes/federated-learning-nextflow) — the other "unusual accelerator" project on this profile |
