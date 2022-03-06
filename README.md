# cdmo1-project

This repository contains the code for the **Combinatorial Optimization and Decision Making - Module 1** exam for the *Artificial Intelligence* master course @UniBo. The project is developed by **Federico Cichetti**.

The project's description can be found in the [CDMO_Project_2021.pdf](CDMO_Project_2021.pdf) document.

## Structure of the project

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