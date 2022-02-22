from itertools import combinations
import time
import re
import math
from z3 import *

import sys
sys.path.append(os.path.join(os.getcwd(), 'utils'))
from problem import ProblemInstance, parse_problem_file
from solution import SolutionInstance, Circuit
from initial_solution import construct_initial_solution
from z3_utils import exactly_one, index_orders, at_least_one

class OptimalVLSI():
    def __init__(self, instance:ProblemInstance):
        # Instance-related variables
        self.inst = instance
        self.n = self.inst.n
        self.W = self.inst.wg
        # Initial solution
        start_init_sol = time.time()
        self.init_inst = construct_initial_solution(self.inst)
        end_init_sol = time.time()
        # Upper and lower bounds for height
        self.low_h = math.floor(sum([self.get_ch(circ)*self.get_cw(circ) 
            for circ in range(self.n)]) / self.W)
        self.max_h = max([circ.y0 + circ.h for circ in self.init_inst.circuits])
        # Boolean variables for our problem
        self.px = [[Bool(f"px_{c}_{e}") for e in range(self.W)] for c in range(self.n)]
        self.py = [[Bool(f"py_{c}_{f}") for f in range(self.max_h)] for c in range(self.n)]
        self.lr = [[Bool(f"lr_{i}_{j}") for j in range(self.n) if i != j] for i in range(self.n)]
        self.ud = [[Bool(f"ud_{i}_{j}") for j in range(self.n) if i != j] for i in range(self.n)]
        self.ph = {int(o): Bool(f'ph_{o}') for o in range(self.low_h, self.max_h+1)}
        # Variable to keep all kinds of times into check
        self.durations = {
            'duration_initial_solution': end_init_sol - start_init_sol,
            'duration_check': 0.0,
            'duration_model': 0.0,
            'duration_solution_creation': 0.0
        }
        # Solver for the problem
        self.s = Solver()
        self.add_main_constraints()
        self.add_initial_solution()

    def add_main_constraints(self):
        # For each circuit, there must be at least a px and a py variable
        # that is true such that the circuit is not placed out of bounds. 
        # Furthermore, we must pose the ordering integrity constraint
        for circ in range(self.n):
            # The circuit should be placed somewhere within the possible positions
            self.s.add(at_least_one([self.px[circ][e] 
                for e in range(self.W-self.get_cw(circ)+1)]))
            self.s.add(at_least_one([self.py[circ][f] 
                for f in range(self.max_h-self.get_ch(circ)+1)]))
            # The ordering integrity conditions
            self.s.add([Or(Not(self.px[circ][e]), self.px[circ][e+1]) 
                for e in range(self.W-self.get_cw(circ))])
            self.s.add([Or(Not(self.py[circ][f]), self.py[circ][f+1]) 
                for f in range(self.max_h-self.get_ch(circ))])

        # There is exactly one circuit placed at (0,0)
        exactly_one(self.s, [
            And(self.px[circ][0], self.py[circ][0]) for circ in range(self.n)
        ])

        # Constraints on pairs of circuits
        for ci, cj in combinations(range(self.n), 2):

            # One must be before or above the other in some way
            self.s.add(Or(
                index_orders(self.lr, ci, cj),
                index_orders(self.lr, cj, ci),
                index_orders(self.ud, ci, cj),
                index_orders(self.ud, cj, ci)
            ))

            # SAME RECTANGLES REDUCTION:
            # If two rectangles have the same dimension, we can fix the positional
            # relation between them (eg. programmatically decide that one is on the
            # left - or if it doesn't apply - above the other.
            if  (self.get_ch(ci) == self.get_ch(cj)) and \
                (self.get_cw(ci) == self.get_cw(cj)):
                self.s.add(Not(index_orders(self.lr, cj, ci)))
                self.s.add(Or(
                    index_orders(self.lr, ci, cj), 
                    Not(index_orders(self.ud, cj, ci))
                ))

            # LARGE RECTANGLES REDUCTION:
            # If the width of the two circuits (wi + wj) is greater than 
            # W, then they cannot be placed on the left/right of each other.
            # So, we can assign lr[i,j] and lr[j,i] = False and remove all of
            # the horizontal constraints. The same is true on the vertical axis.
            if self.get_cw(ci) + self.get_cw(cj) > self.W:
                self.s.add(Not(index_orders(self.lr, ci, cj)))
                self.s.add(Not(index_orders(self.lr, cj, ci)))
            else:
                #### HORIZONTAL ####
                # If i is before j, then px[cj] cannot be before ci_w
                for e in range(self.get_cw(ci)):
                    self.s.add(Or(
                        Not(index_orders(self.lr, ci, cj)),
                        Not(self.px[cj][e])
                    ))
                # Then, we pose the full constraint
                for e in range(self.W-self.get_cw(ci)):
                    self.s.add(Or(
                        Not(index_orders(self.lr, ci, cj)), 
                        self.px[ci][e],
                        Not(self.px[cj][e+self.get_cw(ci)])
                    ))
                # If j is before i, then px[ci] cannot be before cj_w
                for e in range(self.get_cw(cj)):
                    self.s.add(Or(
                        Not(index_orders(self.lr, cj, ci)),
                        Not(self.px[ci][e])
                    ))
                # Then, we have the full constraint
                for e in range(self.W-self.get_cw(cj)):
                    self.s.add(Or(
                        Not(index_orders(self.lr, cj, ci)), 
                        self.px[cj][e],
                        Not(self.px[ci][e+self.get_cw(cj)])
                    ))
            if self.get_ch(ci) + self.get_ch(cj) > self.max_h:
                self.s.add(Not(index_orders(self.ud, ci, cj)))
                self.s.add(Not(index_orders(self.ud, cj, ci)))
            else:
                #### VERTICAL ####
                # If i is above j, then px[cj] cannot be before ci_w
                for f in range(self.get_ch(ci)):
                    self.s.add(Or(
                        Not(index_orders(self.ud, ci, cj)),
                        Not(self.py[cj][f])
                    ))
                # Then, we have the full constraint
                for f in range(self.max_h-self.get_ch(ci)):
                    self.s.add(Or(
                        Not(index_orders(self.ud, ci, cj)), 
                        self.py[ci][f],
                        Not(self.py[cj][f+self.get_ch(ci)])
                    ))
                # If j is above i, then py[ci] cannot be before cj_h
                for f in range(self.get_ch(cj)):
                    self.s.add(Or(
                        Not(index_orders(self.ud, cj, ci)),
                        Not(self.py[ci][f])
                    ))
                # Then, we have the full constraint
                for f in range(self.max_h-self.get_ch(cj)):
                    self.s.add(Or(
                        Not(index_orders(self.ud, cj, ci)), 
                        self.py[cj][f],
                        Not(self.py[ci][f+self.get_ch(cj)])
                    ))

        # At any level, ph,i true means that all circuits must be
        # placed before i - h_c. Furthermore, we also have the ordering
        # integrity constraint.
        for o in self.ph:
            self.s.add([Or(
                Not(self.ph[o]),
                self.py[ci][o-self.get_ch(ci)]
            ) for ci in range(self.n)])
            if o < self.max_h:
                self.s.add(Or(Not(self.ph[o]), self.ph[o+1]))

    def add_initial_solution(self):
        # We have obtained the upper bound for height using the initial solution,
        # so ph at the maximum height is definitely true
        self.s.add(self.ph[self.max_h])
        # For each circuit, we add the initial positions. We do this by saying that 
        # when the optimal height is max_h, the solution is the provided one.
        try:
            self.s.add(Implies(And(self.ph[self.max_h], Not(self.ph[self.max_h-1])), 
            And([
                And([self.px[circ][e] for e in range(
                    self.init_inst.circuits[circ].x0, self.W
                )] + [self.py[circ][f] for f in range(
                    self.init_inst.circuits[circ].y0, self.max_h
                )])
                for circ in range(self.n)
            ])))
        except KeyError:
            pass

    def obtain_solution(self, verbose=False):
        # If SAT, construct the solution
        start_get_true_vars = time.time()
        m = self.s.model()
        end_get_true_vars = time.time()
        duration_true_vars = end_get_true_vars - start_get_true_vars
        true_vars = [var for var in self.s.model() if is_true(m[var])]
        if verbose:
            print(true_vars)
        assignments_x = [min([int(str(var).split('_')[-1])
                for var in true_vars 
                if re.match(f'px_{circ}_', str(var))]
            ) for circ in range(self.n)]
        assignments_y = [min([int(str(var).split('_')[-1])
                for var in true_vars 
                if re.match(f'py_{circ}_', str(var))]
            ) for circ in range(self.n)]
        sol_h = max([assignments_y[i] + self.get_ch(i) for i in range(self.n)])
        if verbose:
            print(assignments_x, assignments_y)
            print("Solution h: {}".format(sol_h))
        solution = SolutionInstance(
            self.inst.wg, sol_h, self.n,
            [ Circuit(self.get_cw(i), self.get_ch(i), assignments_x[i], assignments_y[i]) 
                for i in range(self.n) ]
        )
        return solution, duration_true_vars

    def test_solvability_at_h(self, h:int, verbose=True, draw_sol=True):
        # h is out of the lower/higher bounds for the instance: return unsat
        if h in self.ph:
            self.s.push()           # Push the solver state
            self.s.add(self.ph[h])  # Add h as maximum height and check if it can be solved
            # Calculate time for solving
            start_time = time.time()
            # Solve the problem!
            solver_status = self.s.check()
            end_time = time.time()
            self.durations['duration_check'] += end_time - start_time
            # Check status of solution
            if solver_status == sat:
                start_time_sol = time.time()
                solution, duration_get_vars = self.obtain_solution(verbose=verbose)
                end_time_sol = time.time()
                duration_sol = end_time_sol - start_time_sol
                self.durations['duration_model'] += duration_get_vars
                self.durations['duration_solution_creation'] += duration_sol
                if draw_sol:
                    solution.draw()
            else:
                if verbose:
                    print("Failed to solve")
                solution = None
            self.s.pop() # Restore previous solver condition
        else:
            if verbose:
                print(f"h={h} is not within the lower/higher bounds for height")
            solver_status = unknown
            solution = None
        return solver_status, solution

    def out_of_time(self, max_time:float):
        return self.durations['duration_check'] + self.durations['duration_model'] > max_time

    def solve_optimally_no_assumptions(self, max_sol_time:int=60*5, draw_best=False):
        # Same as self.solve_optimally, but we don't try to solve for the lower bound at the beginning,
        # so we have to go through the whole bisection algorithm to reach it.
        # This is mostly to test that the bisection algorithm is working properly.
        max_h = self.max_h
        low_h = self.low_h
        self.s.set(timeout=max_sol_time*1000) # In milliseconds
        h = low_h+(max_h-low_h)//2
        while max_h != low_h:
            print(f"Trying with h={h}")
            solver_status, _ = self.test_solvability_at_h(
                h, verbose=False, draw_sol=False
            )
            if self.out_of_time(max_sol_time):
                print("Unable to solve the problem within the time limit")
                return None
            if solver_status == sat:
                # Move down upper bound
                max_h = h
            else:
                # Move up lower bound
                low_h = h+1 # +1 because h was unsat
            h = low_h+(max_h-low_h)//2
        # When max_h == low_h we get an optimal solution or proved unsat
        solver_status, solution = self.test_solvability_at_h(
            h, verbose=False, draw_sol=False
        )
        if solver_status != sat or self.out_of_time(max_sol_time):
            print("Unable to solve the problem within the time limit")
            return None
        else:
            if draw_best:
                solution.draw()
            return solution

    def solve_optimally(self, max_sol_time:int=60*5, draw_best=False):
        max_h = self.max_h
        low_h = self.low_h
        # In our algorithm we might have to use the solver multiple time, 
        # so we also check for the total time of execution
        # We set a timeout to the solver in case it cannot even find one solution. 
        # Time must be in milliseconds.
        self.s.set(timeout=max_sol_time*1000)
        # We try to solve it with the lower bound
        h = self.low_h
        solver_status, solution = self.test_solvability_at_h(
            h, verbose=False, draw_sol=False
        )
        # If it's sat, we have an optimal solution
        if solver_status == sat:
            if draw_best:
                solution.draw()
            return solution
        else:
            print(f"Failed to solve at h={h}")
            while max_h != low_h:
                h = low_h+(max_h-low_h)//2
                print(f"Retrying with {h}")
                solver_status, _ = self.test_solvability_at_h(
                    h, verbose=False, draw_sol=False
                )
                if self.out_of_time(max_sol_time):
                    print("Unable to solve the problem within the time limit")
                    return None
                if solver_status == sat:
                    # Move down upper bound
                    max_h = h
                else:
                    # Move up lower bound
                    low_h = h+1 # +1 because h was unsat
            # When max_h == low_h we get an optimal solution or proved unsat
            solver_status, solution = self.test_solvability_at_h(
                h, verbose=False, draw_sol=False
            )
            if solver_status != sat or self.out_of_time(max_sol_time):
                print("Unable to solve the problem within the time limit")
                return None
            else:
                if draw_best:
                    solution.draw()
                return solution

    def get_cw(self, circ:int):
        return self.inst.circuits[circ].w

    def get_ch(self, circ:int):
        return self.inst.circuits[circ].h


if __name__ == '__main__':    
    for i in range(10,11):
        print(f"Solving instance {i}")
        inst = parse_problem_file(f'instances/ins-{i}.txt')
        problem = OptimalVLSI(inst)
        solution = problem.solve_optimally(draw_best=True)
        print("Durations for solving:")
        print(problem.durations)
        print("Total solving time (algorithm overhead not counted): {} seconds".\
            format(problem.durations['duration_check'] + problem.durations['duration_solution_creation']))
        print("=======================")