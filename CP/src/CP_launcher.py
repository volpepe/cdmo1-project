import argparse
import pathlib
import os
from datetime import datetime, timedelta
from minizinc import Instance as SolverInstance, \
    MiniZincError, Model, Solver, Status
import sys
sys.path.append(os.path.join(os.getcwd(), 'utils'))

from launcher_utils import get_problem_instance,\
    get_problem_filenames, get_output_filename, SubOptimalException
from solution import Circuit, SolutionInstance, RotatingSolutionInstance
from initial_solution import construct_initial_solution
from summary_writer import Summary

def parse_args():
    argpars = argparse.ArgumentParser()
    argpars.add_argument('--model', '-m', 
        type=str, help="Path to the model to execute (.mzn file)",
        default=os.path.join("CP", "src", "VLSI-model.mzn"))
    argpars.add_argument('--solver', '-s',
        type=str, help="Path to the solver to use (solver config file (.msc) or 'gecode'/'chuffed')",
        default='gecode')
    argpars.add_argument("--problems", "-p", type=str,
        help="Pattern to gather all instances to be solved",
        default=os.path.join("instances", "ins-*.txt"))
    argpars.add_argument("--output_dir", '-odir', type=str,
        help="Where to create the sequence of output files",
        default=os.path.join("CP", "out"))
    argpars.add_argument("--show", action="store_true",
        help="Use this flag to show the solution after each solved problem")
    argpars.add_argument("--no_use_initial_solution", action='store_true',
        help="Whether the model requires an initial solution for search")
    argpars.add_argument("--output_log", "-log", type=str,
        help="Path to log file", default=os.path.join("CP","out","log.txt"))
    argpars.add_argument("--rotation_allowed", "-rot", action="store_true",
        help="Whether the problem should also allow rotation of circuits.")
    return argpars.parse_args()

def load_model(model_path:str) -> Model:
    return Model(model_path)

def load_solver(solver_path:str) -> Solver:
    if not os.path.exists(solver_path):
        return Solver.lookup(solver_path)
    else:
        return Solver.load(pathlib.Path(solver_path))

def create_minizinc_instance(solver:Solver, model:Model) -> SolverInstance:
    return SolverInstance(solver, model)

def solve_instance(mz_instance:SolverInstance, 
                   summary_writer:Summary, filename=None, 
                   verbose=False, return_raw_result=False) -> SolutionInstance:
    # Solve
    if verbose:
        print("=========================================================")
        print("Solving problem {}...".format(filename))
        print()
    start_time = datetime.now()
    try:
        result = mz_instance.solve(random_seed=42, 
            timeout=timedelta(minutes=5),
            processes=4 if 'chuffed' not in mz_instance._solver.name.lower() else None,                        
            intermediate_solutions=True)  # Also return all intermediate solutions
    except MiniZincError as e:
        print("Problem could not be solved: {}".format(e))
        raise SubOptimalException()
    end_time = datetime.now()
    duration = end_time - start_time
    duration = duration.seconds + duration.microseconds*1e-6
    if result.status == Status.OPTIMAL_SOLUTION or result.status == Status.SATISFIED:
        # Get the solutions
        intermediate_solutions = result.solution[:-1]
        last_solution = result.solution[-1]
        if verbose:
            for interm_solution in intermediate_solutions:
                print(interm_solution._output_item)
            print("FOUND SOLUTION ({}):".format(result.status))
            print("h: {}".format(last_solution.h))
            print("x: {}".format(last_solution.x_positions))
            print("y: {}".format(last_solution.y_positions))
            print("Solving took {} s".format(duration))
            print()
            print("Generating the solution file...")
            print("=========================================================")
        solution = SolutionInstance(
            mz_instance['w'], int(last_solution.h), mz_instance['n'],
            [ Circuit(mz_instance["measures"][i][0], mz_instance["measures"][i][1],
                    last_solution.x_positions[i], last_solution.y_positions[i]) 
                    for i in range(mz_instance["n"]) ]
        )
        if duration < 5*60:
            summary_writer.write_final_solution(solution, duration)    
            return solution if not return_raw_result else (solution, result)
        else:
            # We have found a sub-optimal solution
            summary_writer.write_best_found_solution(solution, duration)
            raise SubOptimalException
    # Otherwise:
    else:
        raise SubOptimalException()

def solve_instance_plus_rotation(mz_instance:SolverInstance,
                                 summary_writer:Summary, filename=None,
                                 verbose=False) -> RotatingSolutionInstance:
    solution, result = solve_instance(mz_instance, summary_writer, filename, verbose, return_raw_result=True)
    solution = RotatingSolutionInstance(solution.wg, solution.hg, solution.n,
        solution.circuits)
    solution.fix_circuits_rotation(result.solution[-1].current_widths, result.solution[-1].current_heights)
    return solution

if __name__ == '__main__':
    args = parse_args()

    print("Loading the model and the instance/s...")
    # Load the VLSI model
    model = load_model(args.model)
    # Find the MiniZinc solver configuration for Gecode
    solver = load_solver(args.solver)
    # Load sample problem instance
    pattern = args.problems
    problem_filenames = get_problem_filenames(pattern)
    num_problems = len(problem_filenames)
    solved_problems = 0
    # Initialize log writer
    summary_writer = Summary(args.output_log)

    # Iterate over instances
    for filename in problem_filenames:
        # Create an instance of the MiniZinc and the problem
        mz_instance = create_minizinc_instance(solver, model)
        # Get instance of the problem (with sorted circuits order)
        problem = get_problem_instance(filename) 
        # Write on log writer
        summary_writer.init_problem(filename, problem)

        # Assign variables
        mz_instance["w"] = problem.wg
        mz_instance["n"] = problem.n
        mz_instance["measures"] = [[circuit.w, circuit.h] for circuit in problem.circuits]

        if not args.no_use_initial_solution:
            st = datetime.now()
            initial_solution = construct_initial_solution(problem)
            mz_instance["initial_x"] = [ c.x0 for c in initial_solution.circuits ]
            mz_instance["initial_y"] = [ c.y0 for c in initial_solution.circuits ]
            end = datetime.now()
            duration = end - st
            duration = duration.seconds + duration.microseconds*1e-6
            summary_writer.write_initial_solution(initial_solution, duration)

        try: 
            if args.rotation_allowed:
                solution = solve_instance_plus_rotation(mz_instance, summary_writer, filename, verbose=True)
            else:
                solution = solve_instance(mz_instance, summary_writer, filename, verbose=True)
            solved_problems += 1

            out_filename = get_output_filename(args.output_dir, filename, rot=args.rotation_allowed)
            solution.write_to_file(out_filename)

            if args.show:
                solution.draw()
        except SubOptimalException:
            pass

    # Close log file
    summary_writer.close()

    print("Solved {} problems out of {}".format(solved_problems, num_problems))
