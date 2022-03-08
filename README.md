# cdmo1-project

This repository contains the code for the **Combinatorial Optimization and Decision Making - Module 1** exam for the *Artificial Intelligence* master course @UniBo. The project was developed by **Federico Cichetti** ([federico.cichetti@studio.unibo.it](mailto:federico.cichetti@studio.unibo.it)).

The problem description can be found in [CDMO_Project_2021.pdf](CDMO_Project_2021.pdf).

## Structure of the project

For this project we implemented 5 models: 2 for constraint programming (normal and rotation), 2 for SAT (normal and rotation) and 1 for SMT (normal). 

SAT and SMT solutions were modelled using the [Z3 solver](https://github.com/Z3Prover/z3) from Microsoft Research (in particular, its Python interface), while the CP solution was built using the [MiniZinc](https://www.minizinc.org/) constraint modelling language. 

The models are grouped by category: the CP models can be found in the `CP` directory, the SAT models are in the `SAT` directory and the SMT model is in the `SMT` directory. Each directory has an `out` folder containing logs of the results of our experiments, and a `src` folder containing the source code. The `src` folders also contain README files with instructions for reproducing our experiments.

The reports for the project can be found in each group's folder: [CP Report](CP/Report_CP.pdf), [SAT Report](SAT/Report_SAT.pdf), [SMT Report](SMT/Report_SMT.pdf).

The full structure tree is shown below:

```
|-CP                                // Implementation of the CP model
    |--- datafiles                      // Instances translated to .dzn files for MiniZinc
        |--- ins-1.dzn
        |--- ...
    |--- out                            // Solutions and logs provided by the CP model
        |--- log.txt                        // Logs for the model that does not allow rotation
        |--- log_rot.txt                    // Logs for the model that allows rotation
        |--- out-1.txt                      // Solution of the first instance blocking rotations
        |--- out-rot-1.txt                  // Solution of the first instance allowing rotations
        |--- ...
    |--- src                            // Source code for the CP model
        |--- solvers                        // Contains the used solver configurations
            |--- gecode_42_5min.mpc
        |--- cdmo1-project-cp.mzp           // The MiniZinc project for the CP model
        |--- CP_launcher.py                 // Python launcher for the CP model
        |--- create_dzns.py                 // Utility script to create .dzn files out of .txt files
        |--- VLSI-model.mzn                 // The MiniZinc model implementation (no rotations)
        |--- VLSI-model-rotation.mzn        // The MiniZinc model implementation (allowing rotations)
    |--- Report_CP.pdf                  // CP model report
|- SAT                              // Implementation of the SAT model
    |--- out                            // Solutions and logs provided by the SAT model
    |--- src                            // Source code for the SAT model
        |--- SAT_launcher.py                // Launcher for solving instances using the SAT model
        |--- SAT_VLSI.py                    // SAT model definition
        |--- SAT_VLSI_rotation.py           // SAT model + rotation definition
    |--- Report_SAT.pdf                 // SAT model report
|- SMT                              // Implementation of the SMT model
    |--- out                            // Solutions and logs provided by the SMT model
    |--- src
        |--- SMT_launcher.py                // Launcher for solving instances using the SMT model
        |--- SMT_VLSI.py                    // SMT model definition
    |--- Report_SMT.pdf                 // The report for the SMT model
|- instances                        // The provided instances of the problem (1 to 40)
    |--- ins-1.txt
    |--- ...
|- utils                            // General utility functions
    |--- initial_solution.py            // Code for constructing the initial solution
    |--- problem.py                     // Class that represents an instance of the problem
    |--- solution.py                    // Class that represents the solution to a problem
    |--- solution_visualizer.py         // Utility functions to visualize a solution
    |--- summary_writer.py              // Log writer
    |--- launcher_utils.py              // General utilities for the launchers
    |--- z3_utils.py                //     General utilities and constraints for Z3
|- CDMO_Project_2021.pdf            // The provided project description
|- README.md                        // This file
|- requirements.txt                 // The pip packages that are required for the code execution
```

## Results

Here, we provide an overview of the results we obtained with our different models. In general, we managed to solve over 30 instances within the 5 minutes mark with all models. Allowing rotations requires a longer search, therefore we can observe a gap in the number of solved instances. 

| Model     | Solved Instances | Average time for solved solutions |
| :---      | :--------------: | :-----------: |
|  CP       |        31        |    8.21 s     |
| CP (rot.) |        20        |    16.13 s    |
|  SAT      |        35        |    7.40 s     |
| SAT (rot.)|        21        |    29.31 s    |
|  SMT      |        33        |    48.14 s    |

The results for each model are detailed at the end of the corresponding reports.

## Citations

The SAT model is an implementation of the paper "[A SAT-based Method for Solving the Two-dimensional Strip Packing Problem](https://www.researchgate.net/publication/220445013_A_SAT-based_Method_for_Solving_the_Two-dimensional_Strip_Packing_Problem)" by Soh et al, although we added some of our own original ideas and designed the rotation extension.