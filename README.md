**Retromorphic Testing of Quantum Compiler Passes**

RetroQ is a testing framework for automatically validating quantum compiler passes. 
It uses retromorphic testing and the principles of the Hadamard test to detect semantic and structural errors in compiler transformations without 
requiring developers to manually calculate the expected output of the transformed quantum circuit.

**Key Features**
- Compiler-pass testing
- Black-box verification
- Semantic verification
- Detect transformations that fail to preserve the behavior of the original circuit.
- Two-stage verification
- No manually derived circuit oracle
- PennyLane and Qiskit support

**What It Test**

- Semantic Properties:
  - Whether the compiler pass preserves the expected expectation value.
- Structural Properties
  - Whether the compiler pass peforms the expected changes to circuit metric, gate count
  
  - For example, let F be a target program and F' be the result of applying a compiler pass, C, on F (F' = C(F)):
    - gate_count(F') < gate_count(F)
    - gate_count(F') = gate_count(F)
    - gate_count(F') > gate_count(F)
      
**Supported Frameworks**
| Framework | Status |
| -------- | -------- |
| PennyLane | Supported |
| Qiskit | Supported | 



**Evaluation**
RetroQ was evaluated against compiler passes in PennyLane and Qiskit and was able to detect several compiler defects. These can be seen in bugs.ipynb.

**Installation**:
  - git clone https://github.com/QSAR-UBC/RetroQ.git
  - cd RetroQ
  - pip install -r requirements.txt

**Usage**
  Define a target circuit, compiler pass, and expected behavior:
  
  ```import pennylane as qp
  from retroq import RetroQ, Expectation
  
  def target_function():
      qp.Hadamard(wires=0)
      qp.RZ(0.1, wires=0)
  
  exp = Expectation(gate_count="unchanged")
  
  rq = RetroQ(
      target_function,
      compiler_pass=qp.transforms.single_qubit_fusion,
      compiler_pass_kwargs={
          "exclude_gates": ["Hadamard"]
      },
      expectation=exp,
      framework="pennylane"
  )
  
  results = rq.run()
  print(results)
  ```
  Here, RetroQ tests the single_qubit_fusion compiler pass and verifies that the expected gate-count behavior is preserved.

**Testing**

To run all tests from the project root:
```python3 -m pytest tests```
