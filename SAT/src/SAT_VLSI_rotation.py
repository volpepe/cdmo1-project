from itertools import combinations
import time
import re
import math
import random
from z3 import *

import sys
sys.path.append(os.path.join(os.getcwd(), 'utils'))
from problem import ProblemInstance, parse_problem_file
from solution import RotatingSolutionInstance, Circuit
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
        #####
        # ROTATION
        # Add variables for each circuit telling if it is rotated or not
        self.rot = [Bool(f"rot_{c}") for c in range(self.n)]
        #####
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

    def can_rotate(self, circuit):
        # Checks if a circuit can be rotated or not
        return (self.get_ch(circuit) <= self.W) and (self.get_cw(circuit) <= self.max_h)

    def add_main_constraints(self):
        # For each circuit, there must be at least a px and a py variable
        # that is true such that the circuit is not placed out of bounds. 
        # Furthermore, we must pose the ordering integrity constraint
        for circ in range(self.n):
            # The circuit should be placed somewhere within the possible positions
            self.s.add(Implies(Not(self.rot[circ]), at_least_one([self.px[circ][e] 
                for e in range(self.W-self.get_cw(circ)+1)])))
            self.s.add(Implies(Not(self.rot[circ]), at_least_one([self.py[circ][f] 
                for f in range(self.max_h-self.get_ch(circ)+1)])))
            #### ROTATION
            self.s.add(Implies(self.rot[circ], at_least_one([self.px[circ][e] 
                for e in range(self.W-self.get_ch(circ)+1)])))
            self.s.add(Implies(self.rot[circ], at_least_one([self.py[circ][f] 
                for f in range(self.max_h-self.get_cw(circ)+1)])))
            #####
            # The ordering integrity conditions
            self.s.add(Implies(Not(self.rot[circ]), And([Or(Not(self.px[circ][e]), self.px[circ][e+1]) 
                for e in range(self.W-self.get_cw(circ))])))
            self.s.add(Implies(Not(self.rot[circ]), And([Or(Not(self.py[circ][f]), self.py[circ][f+1]) 
                for f in range(self.max_h-self.get_ch(circ))])))
            #### ROTATION
            self.s.add(Implies(self.rot[circ], And([Or(Not(self.px[circ][e]), self.px[circ][e+1]) 
                for e in range(self.W-self.get_ch(circ))])))
            self.s.add(Implies(self.rot[circ], And([Or(Not(self.py[circ][f]), self.py[circ][f+1]) 
                for f in range(self.max_h-self.get_cw(circ))])))
            #####

            ##### ROTATION
            # Circuits whose height is greater than W or whose width is greater than maxh
            # cannot be rotated
            if not self.can_rotate(circ):
                self.s.add(Not(self.rot[circ]))
            # Rotating a circuit whose height is equal to its width is pointless
            if self.get_ch(circ) == self.get_cw(circ):
                self.s.add(Not(self.rot[circ]))

        # There is exactly one circuit placed at (0,0)
        exactly_one(self.s, [
            And(self.px[circ][0], self.py[circ][0]) for circ in range(self.n)
        ])

        rectangle_pairs = combinations(range(self.n), 2)
        # Decide a random pair for activating the one-pair fixed ordering reduction that breaks
        # symmetry
        random_pair_for_reduction = random.randrange(0, 
            sum(1 for _,_ in combinations(range(self.n), 2)))
        counter = 0

        # Constraints on pairs of circuits
        for ci, cj in rectangle_pairs:

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

            # ONE PAIR OF RECTANGLES
            # We impose an ordering between a pair of rectangles. In this
            # way, all total flippings are broken because the ordering 
            # must be respected.
            if counter == random_pair_for_reduction:
                self.s.add(Not(index_orders(self.lr, cj, ci)))
                self.s.add(Not(index_orders(self.ud, cj, ci)))
            
            counter += 1

            # The rotation makes it impossible to apply the large rectangle reduction
            # because we don't know how are circuits rotated and thus what is their 
            # current width            

            #### HORIZONTAL ####
            # If i is before j, then px[cj] cannot be before ci_w or ci_h if it is rotated
            self.s.add(Implies(Not(self.rot[ci]), And([Or(
                Not(index_orders(self.lr, ci, cj)),
                Not(self.px[cj][e])
            ) for e in range(self.get_cw(ci))])))
            # Then, we pose the full constraint
            self.s.add(Implies(Not(self.rot[ci]), And([Or(
                Not(index_orders(self.lr, ci, cj)), 
                self.px[ci][e],
                Not(self.px[cj][e+self.get_cw(ci)])
            ) for e in range(self.W-self.get_cw(ci))])))

            if self.can_rotate(ci):
                self.s.add(Implies(self.rot[ci], And([Or(
                    Not(index_orders(self.lr, ci, cj)),
                    Not(self.px[cj][e])
                ) for e in range(self.get_ch(ci))])))
                self.s.add(Implies(self.rot[ci], And([Or(
                    Not(index_orders(self.lr, ci, cj)), 
                    self.px[ci][e],
                    Not(self.px[cj][e+self.get_ch(ci)])
                ) for e in range(self.W-self.get_ch(ci))])))

            # If j is before i, then px[ci] cannot be before cj_w
            self.s.add(Implies(Not(self.rot[cj]), And([Or(
                Not(index_orders(self.lr, cj, ci)),
                Not(self.px[ci][e])
            ) for e in range(self.get_cw(cj))])))
            # Then, we pose the full constraint
            self.s.add(Implies(Not(self.rot[cj]), And([Or(
                Not(index_orders(self.lr, cj, ci)), 
                self.px[cj][e],
                Not(self.px[ci][e+self.get_cw(cj)])
            ) for e in range(self.W-self.get_cw(cj))])))
            
            if self.can_rotate(cj):
                self.s.add(Implies(self.rot[cj], And([Or(
                    Not(index_orders(self.lr, cj, ci)),
                    Not(self.px[ci][e])
                ) for e in range(self.get_ch(cj))])))
                self.s.add(Implies(self.rot[cj], And([Or(
                    Not(index_orders(self.lr, cj, ci)), 
                    self.px[cj][e],
                    Not(self.px[ci][e+self.get_ch(cj)])
                ) for e in range(self.W-self.get_ch(cj))])))

            #### VERTICAL ####
            # If i is above j, then px[cj] cannot be before ci_w
            self.s.add(Implies(Not(self.rot[ci]), And([Or(
                Not(index_orders(self.ud, ci, cj)),
                Not(self.py[cj][f])
            ) for f in range(self.get_ch(ci))])))
            # Then, we pose the full constraint
            self.s.add(Implies(Not(self.rot[ci]), And([Or(
                Not(index_orders(self.ud, ci, cj)), 
                self.py[ci][f],
                Not(self.py[cj][f+self.get_ch(ci)])
            ) for f in range(self.max_h-self.get_ch(ci))])))

            if self.can_rotate(ci):
                self.s.add(Implies(self.rot[ci], And([Or(
                    Not(index_orders(self.ud, ci, cj)),
                    Not(self.py[cj][f])
                ) for f in range(self.get_cw(ci))])))
                self.s.add(Implies(self.rot[ci], And([Or(
                    Not(index_orders(self.ud, ci, cj)), 
                    self.py[ci][f],
                    Not(self.py[cj][f+self.get_cw(ci)])
                ) for f in range(self.max_h-self.get_cw(ci))])))

            # If j is before i, then px[ci] cannot be before cj_w
            self.s.add(Implies(Not(self.rot[cj]), And([Or(
                Not(index_orders(self.ud, cj, ci)),
                Not(self.py[ci][f])
            ) for f in range(self.get_ch(cj))])))
            # Then, we pose the full constraint
            self.s.add(Implies(Not(self.rot[cj]), And([Or(
                Not(index_orders(self.ud, cj, ci)), 
                self.py[cj][f],
                Not(self.py[ci][f+self.get_ch(cj)])
            ) for f in range(self.max_h-self.get_ch(cj))])))
        
            if self.can_rotate(cj):
                self.s.add(Implies(self.rot[cj], And([Or(
                    Not(index_orders(self.ud, cj, ci)),
                    Not(self.py[ci][f])
                ) for f in range(self.get_cw(cj))])))
                self.s.add(Implies(self.rot[cj], And([Or(
                    Not(index_orders(self.ud, cj, ci)), 
                    self.py[cj][f],
                    Not(self.py[ci][f+self.get_cw(cj)])
                ) for f in range(self.max_h-self.get_cw(cj))])))

        # At any level, ph,i true means that all circuits must be
        # placed before i - h_c (or i - w_c if rotated). 
        # Furthermore, we also have the ordering integrity constraint.
        for o in self.ph:
            self.s.add([Implies(Not(self.rot[ci]), Or(
                Not(self.ph[o]),
                self.py[ci][o-self.get_ch(ci)]
            )) for ci in range(self.n)])
            self.s.add([Implies(self.rot[ci], Or(
                Not(self.ph[o]),
                self.py[ci][o-self.get_cw(ci)]
            )) for ci in range(self.n)])
            if o < self.max_h:
                self.s.add(Or(Not(self.ph[o]), self.ph[o+1]))

    def add_initial_solution(self):
        # We have obtained the upper bound for height using the initial solution,
        # so ph at the maximum height is definitely true
        self.s.add(self.ph[self.max_h])


    def obtain_solution(self, verbose=False):
        # If SAT, construct the solution
        start_get_true_vars = time.time()
        m = self.s.model()
        end_get_true_vars = time.time()
        duration_true_vars = end_get_true_vars - start_get_true_vars
        assignments = self.s.model()
        true_vars = [var for var in assignments if is_true(m[var])]
        if verbose:
            print(true_vars)
        # Get the variable with the smallest index out of those referring
        # to the same circuit.
        assignments_x = [min([int(str(var).split('_')[-1])
                for var in true_vars 
                if re.match(f'px_{circ}_', str(var))]
            ) for circ in range(self.n)]
        assignments_y = [min([int(str(var).split('_')[-1])
                for var in true_vars 
                if re.match(f'py_{circ}_', str(var))]
            ) for circ in range(self.n)]
        rotations = [int(str(var).split('_')[1]) for var in true_vars 
            if 'rot' in str(var)]
        sol_h = min([int(str(phvar).split('_')[-1])
            for phvar in true_vars
            if re.match(f'ph_*', str(phvar))])
        if verbose:
            print(assignments_x, assignments_y, rotations)
            print("Solution h: {}".format(sol_h))
        # Instantiate a solution object
        solution = RotatingSolutionInstance(
            self.inst.wg, sol_h, self.n,
            [ Circuit(self.get_cw(i), self.get_ch(i), assignments_x[i], assignments_y[i]) 
                for i in range(self.n) ]
        )
        # Fix rotated widths and heights 
        solution.fix_circuits_rotation(
            widths=[self.get_cw(circ) if not circ in rotations
                else self.get_ch(circ) 
                for circ in range(self.n)], 
            heights=[self.get_ch(circ) if not circ in rotations
                else self.get_cw(circ) 
                for circ in range(self.n)])
        print("ROTATED CIRCUITS: {}".format(rotations))
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

    def solve_optimally_fast(self, max_sol_time:int=60*5, draw_best=False):
        # We solve the problem faster by assuming that the initial height is the lowh 
        # (because it's true for all(?) provided instances, but not true in general)
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

    def get_cw(self, circ:int) -> int:
        # Returns width of a circuit according to the one defined
        # in the instance of the problem
        return self.inst.circuits[circ].w

    def get_ch(self, circ:int) -> int:
        # Returns height of a circuit according to the one defined
        # in the instance of the problem
        return self.inst.circuits[circ].h


if __name__ == '__main__':
    for i in range(1, 20):
        print(f"Solving instance {i}")
        inst = parse_problem_file(f'instances/ins-{i}.txt')
        problem = OptimalVLSI(inst)
        solution = problem.solve_optimally(draw_best=True)
        print("Durations for solving:")
        print(problem.durations)
        print("Total solving time (algorithm overhead not counted): {} seconds".\
            format(problem.durations['duration_check'] + problem.durations['duration_solution_creation']))
        print("=======================")