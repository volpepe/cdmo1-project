import argparse
import os
from typing import Union

import sys
sys.path.append(os.path.join(os.getcwd(), 'utils'))
from solution import SolutionInstance, RotatingSolutionInstance
from summary_writer import Summary
from launcher_utils import SubOptimalException, get_problem_filenames,\
    get_problem_instance, get_output_filename
from SAT_VLSI import OptimalVLSI
from SAT_VLSI_rotation import OptimalVLSI as OptimalVLSIRotation

def parse_args():
    argpars = argparse.ArgumentParser()
    argpars.add_argument("--problems", "-p", type=str,
        help="Pattern to gather all instances to be solved",
        default=os.path.join("instances", "ins-1.txt"))
    argpars.add_argument("--output_dir", '-odir', type=str,
        help="Where to create the sequence of output files",
        default=os.path.join("SAT", "out"))
    argpars.add_argument("--show", action="store_true",
        help="Use this flag to show the solution after each solved problem")
    argpars.add_argument("--output_log", "-log", type=str,
        help="Path to log file", default=os.path.join("SAT","out","log.txt"))
    argpars.add_argument("--rotation_allowed", "-rot", action="store_true",
        help="Whether the problem should also allow rotation of circuits.")
    return argpars.parse_args()


def solve_instance(problem, 
    summary_writer:Summary, filename=None, 
    verbose=False) -> Union[SolutionInstance,RotatingSolutionInstance]:
    # Solve
    if verbose:
        print("=========================================================")
        print("Solving problem {}...".format(filename))
        print()
    solution = problem.solve_optimally_no_assumptions(draw_best=False)
    duration = problem.durations['duration_check'] + \
               problem.durations['duration_model']
    if verbose:
        print("FOUND SOLUTION ({}):".format('OPTIMAL' if not problem.out_of_time(5*60) else 'SUB-OPTIMAL'))
        if not problem.out_of_time(5*60):
            print("h: {}".format(solution.hg))
            print("x: {}".format([solution.circuits[c].x0 for c in range(len(solution.circuits))]))
            print("y: {}".format([solution.circuits[c].y0 for c in range(len(solution.circuits))]))
        print("Durations for solving:")
        print(problem.durations)
        print("Total solving time (algorithm overhead not counted): {} seconds".\
            format(duration))
        print()
        print("Generating the solution file...")
        print("=========================================================")
    if not problem.out_of_time(5*60):
        summary_writer.write_final_solution(solution, duration)
        return solution
    else:
        # We have found a sub-optimal solution
        summary_writer.write_best_found_solution(solution, duration)
        raise SubOptimalException


if __name__ == '__main__':
    args = parse_args()

    print("Loading the model and the instance/s...")
    # Load sample problem instance
    pattern = args.problems
    problem_filenames = get_problem_filenames(pattern)
    num_problems = len(problem_filenames)
    solved_problems = 0
    # Initialize log writer
    summary_writer = Summary(args.output_log)

    # Iterate over instances
    for filename in problem_filenames:
        # Get instance of the problem (with sorted circuits order)
        problem = get_problem_instance(filename) 
        # Initialize the problem
        vlsi_instance = OptimalVLSI(problem) if not args.rotation_allowed else OptimalVLSIRotation(problem)
        # Write on log writer
        summary_writer.init_problem(filename, problem)
        summary_writer.write_initial_solution(vlsi_instance.init_inst, 
            vlsi_instance.durations['duration_initial_solution'])
        try: 
            solution = solve_instance(vlsi_instance, summary_writer, 
                filename, verbose=True)
            solved_problems += 1
            out_filename = get_output_filename(args.output_dir, filename, rot=args.rotation_allowed)
            solution.write_to_file(out_filename)
            if args.show:
                solution.draw()
        except SubOptimalException:
            # If suboptimal, ignore instance
            pass

    # Close log file
    summary_writer.close()

    print("Solved {} problems out of {}".format(solved_problems, num_problems))
