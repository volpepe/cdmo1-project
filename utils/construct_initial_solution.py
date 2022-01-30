import os
import argparse
import random
from solution import SolutionInstance, Circuit
from CP_launcher import get_problem_filenames, get_problem_instance
from problem import ProblemInstance

def parse_args():
    argpars = argparse.ArgumentParser()
    argpars.add_argument("--problem", "-p", type=str,
        help="Path to the problem for which we want to construct an initial solution.",
        default=os.path.join("utils","samples","ins-sample.txt"))
    argpars.add_argument("--show", action="store_true",
        help="Use this flag to show the solution after each solved problem")
    return argpars.parse_args()

def update_current_y(current_y, circuits, xs, ys):
    # Iterate over x positions
    for i in range(len(current_y)):
        heights_for_i = []
        # For each x position, iterate over all circuits
        for c in range(len(xs)):
            # If column i overlaps the circuit, add the reached
            # height of the circuit in heights_for_i
            if xs[c] <= i < xs[c] + circuits[c].w:
                heights_for_i.append(ys[c] + circuits[c].h)
        # The current height at column i will be the max of the 
        # heights of the circuits that overlap it
        current_y[i] = max(heights_for_i) if len(heights_for_i) else 0
    return current_y

def construct_initial_solution(problem: ProblemInstance) -> SolutionInstance:
    # Get the circuits and shuffle them randomly
    circuits = problem.circuits
    random.shuffle(circuits)
    # The first circuit will be at 0,0
    xs, ys = [0], [0]
    # We keep track of what the next y should be by keeping a list of the 
    # current height in each of the xs
    current_y = update_current_y([ 0 for _ in range(problem.wg) ], circuits, xs, ys)
    # The other circuits should be placed based on the placement of the previous
    for i in range(1, problem.n):
        # The next x will theoretically be placed at the position of the last
        # circuit + its width
        new_theory_x = xs[i-1] + circuits[i-1].w
        # Then, we check if placing that circuit on that x overflows the
        # board's width
        row_adder = new_theory_x + circuits[i].w > problem.wg
        # If it does, we move it on the row above, using the array current_y 
        # to understand what the proper height at that row is
        if row_adder:
            x = 0
            y = max(current_y)
        else:
            # Otherwise, we keep it on the same row
            x = new_theory_x
            y = ys[i-1]
        xs.append(x)
        ys.append(y)
        current_y = update_current_y(current_y, circuits, xs, ys)
    # We construct the solution instance and return it
    return SolutionInstance(
        wg=problem.wg, 
        hg=max([ ys[i] + circuits[i].h for i in range(problem.n) ]), 
        n=problem.n,
        circuits=[ Circuit(circuits[i].w, circuits[i].h,
                             xs[i],        ys[i]) for i in range(problem.n) ])


if __name__ == '__main__':
    args = parse_args()
    # Load problem instance
    filename = get_problem_filenames(args.problem)[0]
    problem = get_problem_instance(filename)
    initial_solution = construct_initial_solution(problem)
    initial_solution.draw()
