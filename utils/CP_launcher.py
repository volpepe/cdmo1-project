import argparse
import glob
from datetime import timedelta
from typing import Sequence
from minizinc import Instance as SolverInstance, Model, Solver
from problem import ProblemInstance, parse_problem_file
from solution import Circuit, SolutionInstance

def parse_args():
    argpars = argparse.ArgumentParser()
    argpars.add_argument('--model', '-m', 
        type=str, help="Path to the model to execute (.mzn file)",
        default="CP/src/VLSI-model.mzn")
    argpars.add_argument('--solver', '-s',
        type=str, help="Path to the solver to use (solver file or 'gecode'/'chuffed')",
        default="gecode")
    argpars.add_argument("--problems", "-p", type=str,
        help="Pattern to gather all instances to be solved",
        default="utils/samples/ins-sample.txt")
    argpars.add_argument("--output_dir", '-odir', type=str,
        help="Where to create the sequence of output files",
        default="utils/samples")
    return argpars.parse_args()

def load_model(model_path:str) -> Model:
    return Model(model_path)

def load_solver(solver_path:str) -> Solver:
    return Solver.lookup(solver_path)

def create_minizinc_instance(solver:Solver, model:Model) -> SolverInstance:
    return SolverInstance(solver, model)

def get_problem_filenames(pattern:str) -> Sequence[str]:
    return [fn for fn in glob.glob(pattern)]

def get_problem_instance(fn:str) -> ProblemInstance:
    return parse_problem_file(fn)

def get_output_filename(input_fn:str) -> str:
    return input_fn.replace("ins", "out")

def solve_instance(mz_instance, filename=None, verbose=False) -> SolutionInstance:
    # Solve
    if verbose:
        print("=========================================================")
        print("Solving problem {}...".format(filename))
        print()
    result = mz_instance.solve(timeout=timedelta(minutes=5))
    if verbose:
        print("h: {}".format(result['h']))
        print("x: {}".format(result['x_positions']))
        print("y: {}".format(result['y_positions']))
        print()
        print("Generating the solution file...")
        print("=========================================================")
    solution = SolutionInstance(problem.wg, int(result['h']), problem.n,
        [Circuit(problem.circuits[i].w, problem.circuits[i].h,
            result['x_positions'][i], result['y_positions'][i]) for i in range(problem.n)])        
    return solution

if __name__ == '__main__':
    args = parse_args()

    print("Loading the model and the instance/s...")
    # Load the VLSI model
    model = load_model(args.model)
    # Find the MiniZinc solver configuration for Gecode
    solver = Solver.lookup(args.solver)
    # Create an instance of the MiniZinc
    mz_instance = create_minizinc_instance(solver, model)
    # Load sample problem instance
    pattern = args.problems
    problem_filenames = get_problem_filenames(pattern)

    # Iterate over instances
    for filename in problem_filenames:
        problem = get_problem_instance(filename)

        # Assign variables
        mz_instance["w"] = problem.wg
        mz_instance["n"] = problem.n
        mz_instance["measures"] = [[circuit.w, circuit.h] for circuit in problem.circuits]

        solution = solve_instance(mz_instance, filename, verbose=True)
        
        out_filename = get_output_filename(filename)
        solution.write_to_file(out_filename)
