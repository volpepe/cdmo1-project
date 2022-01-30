import argparse
import os
from tqdm import tqdm
from initial_solution import construct_initial_solution
from CP_launcher import get_problem_filenames, get_problem_instance

def parse_args():
    argpars = argparse.ArgumentParser()
    argpars.add_argument("--problems", "-p", type=str,
        help="Pattern to gather all instances to be solved",
        default=os.path.join("instances","ins-*.txt"))
    argpars.add_argument("--output_dir", '-odir', type=str,
        help="Where to create the sequence of output files",
        default=os.path.join("CP","datafiles"))
    argpars.add_argument("--add_initial_solution", action="store_true",
        help="Whether to add an initial solution to the file")
    return argpars.parse_args()

if __name__ == '__main__':
    args = parse_args()

    # Load sample problem instance
    pattern = args.problems
    problem_filenames = get_problem_filenames(pattern)
    num_problems = len(problem_filenames)

    # Iterate over instances
    print("Converting files...")
    os.makedirs(args.output_dir, exist_ok=True)
    for filename in tqdm(problem_filenames):
        problem = get_problem_instance(filename)
        initial_solution = construct_initial_solution(problem) if args.add_initial_solution else None
        problem.write_to_dzn(os.path.join(
            args.output_dir, 
            filename.split(os.sep)[-1].replace('txt', 'dzn')),
            initial_solution
        )
