# Retromorphic Testing of Quantum Compiler Passes
RetroQ allows users to input a compiler pass along with a target quantum function and expected behavior of the compiler pass, enabling automated evaluation of each compiler pass’s behavior without manual derivation of expected output. 

RetroQ uses a two-stage verification process for this: an adjoint identity check and a controlled adjoint identity check. RetroQ first generates baseline quantum circuits for both stages and then compares their semantic and structural information against variants of stage 1 quantum circuits with the compiler pass applied.

- Stage 1 Baseline Circuit:
  
  <img width="400" height="80" alt="Screenshot from 2026-10-06 12-55-50" src="https://github.com/user-attachments/assets/21c8aae9-8e7a-4727-950c-1ce893f9ebfe" />


- Stage 1 Variant Circuits:
  
  <img width="400" height="190" alt="Screenshot from 2026-10-06 12-56-33" src="https://github.com/user-attachments/assets/700ad1f3-a22f-4513-beac-ad49e8fdacd0" />


- Stage 2 Baseline Circuit:
 
  <img width="400" height="120" alt="Screenshot from 2026-10-06 12-57-07" src="https://github.com/user-attachments/assets/450d9fea-747b-4ff3-b2bf-f0b4973c5a6b" />

- Stage 2 Variant Circuits

  <img width="400" height="360" alt="Screenshot from 2026-10-06 12-57-41" src="https://github.com/user-attachments/assets/fb9d4132-0539-4dc6-82ff-2f512a613c0a" />

Here, F is the target quantum circuit and ζ is a compiler pass.

  
```python
import pennylane as qp
  from retroq import RetroQ, Expectation
  
  def target_function():
      qp.Hadamard(wires=0)
      qp.RZ(0.1, wires=0)
  
  exp = Expectation(gate_count="unchanged")
  
  rq = RetroQ(
      target_quantum_circuit,
      compiler_pass=qp.transforms.single_qubit_fusion,
      compiler_pass_kwargs={
          "exclude_gates": ["Hadamard"]
      },
      expectation=exp,
      framework="pennylane"
  )

  rq.run()
```
## Installation
Clone the repository and install the required dependencies:
```
  git clone https://github.com/QSAR-UBC/RetroQ.git
  cd RetroQ
  pip install -r requirements.txt
```
## Usage
The usage of RetroQ requires four components:
- A target quantum circuit
- A compiler pass to test
- An expectation describing the behaviour of the compiler pass
- The quantum computing framework being used

In the example above, RetroQ applies PennyLane's `single_qubit_fusion` compiler pass to the target program and verifies that the resulting circuit satisfies:
- Semantic preservation: the transformed circuit should preserve the behavior of the original circuit.
- Structural behavior: the gate count should remain unchanged.

The expectation object specifies the properties that the compiler pass is expected to satisfy. RetroQ supports expected gate-count relationship, which can be one of the following:
```python
Expectation(gate_count="decreased")
Expectation(gate_count="unchanged")
Expectation(gate_count="increased")
```

RetroQ supports PennyLane and Qiskit.
### Example
Consider the program below. Here, the target program, `target_function`, has two consecutive Hadamard gates on qubit 0. The [`cancel_inverses`](https://docs.pennylane.ai/en/stable/code/api/pennylane.transforms.cancel_inverses.html) compiler pass, which is designed to identify and remove redundant adjoint or self-inverse operations, is being passed to RetroQ with the target function, the expectation that the gate count should decrease and the framework PennyLane. When the `.run()` is called, any deviations from expected results will be captured by failure report that associate each violation with the corresponding circuit description.
```python
import pennylane as qp
from retro_q import RetroQ, Expectation

# 1. Define the target program
def target_function():
    qp.Hadamard(wires=0)
    qp.Hadamard(wires=0)

# 2. Define user expectations for the compiler pass
# We expect the gate count to decrease
exp = Expectation(gate_count='decrease')

# 3. Initialize RetroQ with the pass to test
rq = RetroQ(target_function, compiler_pass=qp.transforms.cancel_inverses, expectation=exp, framework='pennylane')
```
```pycon
>>> rq.run()
{'stage_1_differences': [{
  'detail': 'compiler_pass(adjoint(func))',
  'differences': {
   'gate_count': {'baseline': 4, 'actual': 4, 'ok': False},
   'expectation_value': {
    'baseline': [np.float64(0.9999999999999993)],
    'actual': [np.float64(0.9999999999999993)], 'ok': True
   }}}],
 'stage_2_differences': [{
  'detail': 'control(compiler_pass(adjoint(func))',
  'differences': {
   'gate_count': {'baseline': 6, 'actual': 6, 'ok': False},
   'expectation_value': {
    'baseline': np.float64(0.9999999999999996),
    'actual': np.float64(0.9999999999999993), 'ok': True
   }}}]}}
```
As shown here, the `cancel_inverses` compiler pass did not satisfy the structural property expectation of gate count reduction for both stages.

### Contributing
RetroQ is available open source under the MIT License. Contributions are welcome. Please open an issue if you are interested in contributing, or if you encounter a bug.

### Reference 
The authors acknowledge funding from the Natural Sciences and Engineering Research Council of Canada (NSERC) CREATE in Quantum Computing Program, grant number 543245, and the Four Year Doctoral Fellowship. ODM acknowledges funding from NSERC (RGPIN-2022-04609), the Canada Research Chairs program (CRC-2021-00206), and UBC. The authors thank the PennyLane team for feedback on the identified bugs.

If you use RetroQ as part of your workflow, we would appreciate if you cite it using the BibTex below.

```
@article{khan2026retromorphic,
  title         = {Retromorphic Testing of Quantum Compiler Passes},
  author        = {Khan, Mushahid and Di Matteo, Olivia},
  year          = {2026},
  journal       = {arXiv preprint arXiv:2610.11195},
  eprint        = {2610.11195},
  archivePrefix = {arXiv},
  primaryClass  = {quant-ph},
  url           = {https://arxiv.org/abs/2610.11195}
}

```
