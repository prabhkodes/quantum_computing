# From a submitted problem to quantum hardware

The notebooks in this repo each solve one problem end to end. This note takes the same path and
asks a different question at every step: **what would a service have to do here, if these were
other people's jobs and the QPU were a metered, shared resource?**

Nothing here is a proposal for this repo. It is the operational reading of work that already
exists — written down because the interesting engineering in quantum computing right now is not
the annealing, it is everything around it.

```
  submit          compile              embed                sample            return
    │               │                    │                    │                 │
 problem  ──►  QUBO (PyQUBO)  ──►  minor-embedding  ──►  sampler backend  ──►  results
    │               │                    │                    │                 │
 validate,      deterministic,       topology-specific,   neal (CPU) or     decode, rank,
 quota          cacheable            the expensive step   DWaveSampler      report quality
```

---

## 1. What is actually in a submitted job

Not a circuit, and not a matrix. For an annealing job the payload is **a problem plus the
parameters that decide what it costs**:

| Field | From the notebooks | Why a service cares |
|---|---|---|
| The QUBO or the model | `pyqubo` expression compiled to `Q` | Size drives everything downstream |
| `num_reads` | 10 · 500 · 1000 · 5000 across these notebooks | **The primary cost knob.** Linear in QPU access time |
| Penalty strength | `A` in the constraint terms | Too low → infeasible answers; too high → the objective is swamped |
| Precision scaling | `SCALE = 100`, floats → ints | A float budget of 47.31 becomes 4731; precision costs qubits |
| Constraint encodings | slack bits, `m = ⌈log₂(B+1)⌉` | Silently grows the problem — a budget of 100 adds 7 variables |

**What must be validated before anything reaches hardware**, because past this point it costs:

- **Variable count after reduction, not before.** A user submits 10 decision variables; the
  knapsack in `budget_optimisation` adds 7 slack bits, and a cubic term in `qubo_antenna_higher_order`
  adds one auxiliary variable *per reduced term*. The size that matters is post-reduction.
- **Connectivity.** A dense QUBO on a sparse QPU topology means long chains — see §3. Density is
  knowable before submission and is the best early predictor of a job going badly.
- **`num_reads` against the tenant's remaining budget.** 5000 reads is 500× the cost of 10. This is
  the single field most worth a per-tenant ceiling.
- **Penalty strength sanity.** If `A` is small relative to the objective coefficients, the run will
  return confident, infeasible answers. Cheap to check statically; expensive to discover afterwards.

## 2. Compilation is deterministic, so it caches

`pyqubo`'s `.compile()` → `.to_qubo()` is a pure function of the model. Same expression, same `Q`.
That makes it cacheable on a hash of the model, and it should be — it is pure CPU work that does
not need to sit between the user and the queue.

The useful consequence: **compilation and dispatch are different services**. One is CPU-bound,
horizontally scalable and cheap to retry. The other is gated on a scarce external resource. Putting
them in one process couples a cheap failure to an expensive queue slot.

## 3. Minor-embedding is the expensive step, and the one worth caching hardest

```python
EmbeddingComposite(DWaveSampler())      # this line hides the real work
```

`EmbeddingComposite` finds a mapping from logical variables to **physical qubits**, and because the
hardware graph is not fully connected, one logical variable usually becomes a **chain** of physical
qubits held together by strong couplings.

Three things follow, and all three are platform concerns:

- **It is topology-specific, not problem-specific.** An embedding computed for one QPU's graph is
  worthless on another. The cache key is `(problem hash, topology id)` — not the problem alone.
- **It is the slow part and it is heuristic.** Finding an embedding can take longer than the
  sampling it enables, and the result varies run to run. A service that recomputes it per
  submission is burning CPU to get a *worse* answer than a cached one it already had.
- **Chain length is the quality predictor.** Long chains need strong couplings, strong couplings
  compress the dynamic range available to the actual problem, and the answer degrades. **Chain
  length is knowable at embed time, before any QPU seconds are spent** — which makes it the right
  place to fail a job, warn a user, or route it elsewhere.

## 4. What decides which backend runs it

Every notebook here solves the same QUBO twice:

```python
neal.SimulatedAnnealingSampler()        # classical, runs anywhere, no queue
EmbeddingComposite(DWaveSampler())      # real QPU, metered, queued
```

That is not just a teaching device — it is a **backend abstraction**, and it is the thing that
makes a submission platform possible at all. The QUBO does not know or care which one ran it.

A dispatcher choosing between them has four inputs, all available before dispatch:

1. **Size after reduction** — below some threshold, classical wins outright and costs nothing.
2. **Chain length after embedding** — past a point the QPU answer is worse than the classical one.
   Dispatching anyway is spending money to get a worse result.
3. **Queue depth and the tenant's remaining budget.**
4. **What the user asked for.** Sometimes the answer is "I specifically want QPU results" and the
   platform's job is to price it, not to second-guess it.

**The general point, and the one worth keeping:** the formulation is hardware-agnostic, only the
sampler changes. Every platform decision above lives in the gap between those two lines.

## 5. What to meter

Wall-clock time is the wrong unit — most of it is queue.

| Metric | Why |
|---|---|
| **QPU access time** | What is actually billed. ≈ `num_reads` × anneal time + overhead |
| `num_reads` per job, per tenant | The cost knob users control, so the one to rate-limit |
| **Embedding time and cache hit rate** | Directly converts to CPU saved and latency removed |
| **Chain-break fraction** | Answer quality. High break rates mean the run was wasted |
| Time-to-best-solution, classical vs QPU | The only honest basis for routing decisions |
| Queue depth and wait per backend | What a user actually experiences as slowness |

Chain-break fraction is the interesting one: it is a **quality** metric, not a performance one, and
it has no analogue in ordinary job schedulers. A run can complete successfully, bill fully, and
return answers that mean nothing — and only the break rate reveals it.

---

## Why this is written down

The formulation work in this repo — reducing inequalities with binary-encoded slack, collapsing
higher-order terms to quadratic — is what makes a problem runnable on annealing hardware at all.
The notes above are what would make it runnable *for other people*: validation before spend,
caching the expensive deterministic step, routing on measurable quality signals, and metering the
resource that is actually scarce.

Those are the same problems as any compute platform, with one difference worth stating plainly:
the scarce resource is a physical device with a fixed topology, and the cost of a bad job is paid
before anyone finds out it was bad.
