# SMT Model

This folder contains the implementation of SMT model we wrote for solving the VLSI problem. To execute the code, be sure to have installed the requirements through a Python package manager like `pip` or `conda`:

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

- A launcher for running the solver on a set of instances, saving the outputs and optionally showing the results: `SMT_launcher.py`. 
    - It can be run from the project root with: 
    ```
    python SMT/src/SMT_launcher.py -p instances/ins-*.txt -odir SMT/out -log SMT/out/log.txt
    ```
    - Only the `--show` optional flags can be provided: it stops the launcher after each instance has been solved to graphically show the solution that has just been produced.
    ```
    python SMT/src/SMT_launcher.py -p instances/ins-*.txt -odir SMT/out -log SMT/out/log.txt --show
    ```
- The file containing the main class, which is where we define all constants, variables and constraint definitions for the problem, as well as the optimal solving algorithm. This file can be run for testing purposes, but it's not a full launcher.

```bash
python SMT/src/SMT_VLSI.py
```