# Constraint Programming Model

This folder contains the implementation of the Constraint Programming model we wrote for solving the VLSI problem. To execute the code, be sure to have installed the requirements through a Python package manager like `pip` or `conda`:

```bash
# From the root of the project
python -m venv .env
source .env/bin/activate    # on Windows: .env\Scripts\activate
# ALTERNATIVE WITH CONDA:
# conda create -n cdmo1 python=3.8
# conda activate cdmo1
# Then:
python -m pip install -r requirements.txt
```

The files in this folder are:

- A launcher for running the solver on a set of instances, saving the outputs and optionally showing the results: `CP_launcher.py`. 
    - It can be run from the project root with: 
    ```
    python CP/src/CP_launcher.py -p instances/ins-*.txt -odir CP/out -log CP/out/log.txt -m CP/src/VLSI-model.mzn
    ```
    - Two optional flags can be provided: 
        - `-rot` sets up the launcher to allow rotation in the solver. When used, some of the other flags should be changed too: 
        ```
        python CP/src/CP_launcher.py -p instances/ins-*.txt -odir CP/out -log CP/out/log-rot.txt -m CP/src/VLSI-model-rotation.mzn -rot
        ```
        - `--show` stops the launcher after each instance has been solved to graphically show the solution that has just been produced.
        ```
        python CP/src/CP_launcher.py -p instances/ins-*.txt -odir CP/out -log CP/out/log.txt -m CP/src/VLSI-model.mzn --show
        ```
- The MiniZinc project file (`cdmo1-project-cp.mzp`) and the MiniZinc models (`VLSI-model-rotation.mzn` and `VLSI-model.mzn`)
- A utility script to create `.dzn` files to be used within the MiniZinc IDE: `create_dzns.py`
    - It can be run from the project root with 
    ```
    python CP/src/create_dzns.py -p instances/ins-*.txt -odir CP/datafiles --add_initial_solution
    ```