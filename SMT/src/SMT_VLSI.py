from itertools import combinations
import time
import re
import math
import random
from tracemalloc import start
from z3 import *

from typing import Tuple, Dict

import sys
BASE_PATH = os.path.join(sys.path[0].split('cdmo1-project')[0], 'cdmo1-project')
sys.path.append(os.path.join(BASE_PATH, 'utils'))
from problem import ProblemInstance, parse_problem_file
from solution import SolutionInstance, Circuit
from initial_solution import construct_initial_solution
from z3_utils import exactly_one, cumulative_z3, lex_lessex_z3, max_z3

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
        self.cx = [Int(f'x_{circ}') for circ in range(self.n)]
        self.cy = [Int(f'y_{circ}') for circ in range(self.n)]
        self.cw = [self.get_cw(circ) for circ in range(self.n)]
        self.ch = [self.get_ch(circ) for circ in range(self.n)]
        self.transl_pos = [Int(f'tr_{circ}') for circ in range(self.n)]
        self.h = Int(f'h')
        # Variable to keep all kinds of times into check
        self.durations = {
            'duration_initial_solution': end_init_sol - start_init_sol,
            'duration_check': 0.0,
            'duration_model': 0.0,
            'duration_solution_creation': 0.0
        }
        # Solver for the problem
        self.opt = Optimize()
        self.add_main_constraints()
        self.opt.minimize(self.h)

    def add_main_constraints(self):
        # For each circuit, there must be at least a px and a py variable
        # that is true such that the circuit is not placed out of bounds. 
        # Furthermore, we must pose the ordering integrity constraint
        for circ in range(self.n):
            self.opt.add(And(0 <= self.cx[circ], self.cx[circ] <= self.W - self.cw[circ]))
            self.opt.add(And(0 <= self.cy[circ], self.cy[circ] <= self.h - self.ch[circ]))
            self.opt.add(And(self.low_h <= self.h, self.h <= self.max_h))
            self.opt.add(self.transl_pos[circ] == self.cy[circ] * self.W + self.cx[circ])

        # All translated positions must be different
        self.opt.add(Distinct(self.transl_pos))
        # One circuit must be at 0
        exactly_one(self.opt, [self.transl_pos[circ] == 0 for circ in range(self.n)])

        # Constraints on pairs of circuits
        for ci, cj in combinations(range(self.n), 2):
            # Bidimensional No-Overlap
            self.opt.add(Or(
                self.cx[ci] + self.cw[ci] <= self.cx[cj],
                self.cx[cj] + self.cw[cj] <= self.cx[ci],
                self.cy[ci] + self.ch[ci] <= self.cy[cj],
                self.cy[cj] + self.ch[cj] <= self.cy[ci]
            ))

        # Cumulative constraint
        self.opt.add(cumulative_z3(self.cy, self.ch, self.cw, self.W))
        self.opt.add(cumulative_z3(self.cx, self.cw, self.ch, self.h))
        
        ## Symmetry breaking
        self.opt.add([
            lex_lessex_z3(self.transl_pos, [self.cy[c]*self.W+
                                           (self.W-self.cx[c]-self.cw[c]) 
                                           for c in range(self.n)]),
            lex_lessex_z3(self.transl_pos, [(self.h-self.cy[c]*self.ch[c])*self.W+
                                            self.cx[c] 
                                            for c in range(self.n)]),
            lex_lessex_z3(self.transl_pos, [(self.h-self.cy[c]-self.ch[c])*self.W+
                                            (self.W-self.cx[c]-self.cw[c]) 
                                            for c in range(self.n)])
        ])

        ## Definition of the height variable
        self.opt.add(self.h == max_z3([self.cy[circ] + self.ch[circ] for circ in range(self.n)]))


    def obtain_solution(self, verbose=False):
        # Check if SAT
        start_check = time.time()
        check = self.opt.check()
        self.durations['duration_check'] = time.time() - start_check
        if check == sat:
            # If SAT, obtain the variable values and construct the solution object
            start_model = time.time()
            sol = self.opt.model()
            self.durations['duration_model'] = time.time() - start_model
            if verbose:
                print(sol)
            assignments_x = [int(sol[var].as_long()) 
                for circ in range(self.n)
                for var in sol if re.match(f'x_{circ}$', str(var)) ]
            assignments_y = [int(sol[var].as_long()) 
                for circ in range(self.n)
                for var in sol if re.match(f'y_{circ}$', str(var)) ]
            sol_h = [int(sol[var].as_long()) 
                for var in sol 
                if re.match(f'h$', str(var))][0]
            if verbose:
                print(assignments_x, assignments_y)
                print("Solution h: {}".format(sol_h))
            solution = SolutionInstance(
                self.W, sol_h, self.n,
                [ Circuit(self.get_cw(i), self.get_ch(i), assignments_x[i], assignments_y[i]) 
                    for i in range(self.n) ]
            )
            return check, solution
        else:
            return check, None

    def out_of_time(self, max_time:float):
        return self.durations['duration_check'] + self.durations['duration_model'] > max_time

    def solve(self, max_sol_time:int=60*5, draw_best=False):
        # Set solver timeout
        self.opt.set(timeout=max_sol_time*1000)
        start_sol_time = time.time()
        status, solution = self.obtain_solution(verbose=False)
        self.durations['duration_solution_creation'] = time.time() - start_sol_time
        # If it's SAT, we have an optimal solution
        if status == sat:
            if draw_best:
                solution.draw()
            return solution
        else:
            print(f"Failed to solve")
            return None

    def get_cw(self, circ:int):
        return self.inst.circuits[circ].w

    def get_ch(self, circ:int):
        return self.inst.circuits[circ].h

if __name__ == '__main__':    
    INSTANCE_NUMS = range(1,20)

    for INSTANCE_NUM in INSTANCE_NUMS:
        print(f"Solving instance {INSTANCE_NUM}")
        inst = parse_problem_file(f'instances/ins-{INSTANCE_NUM}.txt')
        problem = OptimalVLSI(inst)
        solution = problem.solve(draw_best=True)
        if solution is not None:
            print("Durations for solving:")
            print(problem.durations)
            print("Total solving time (algorithm overhead not counted): {} seconds".\
                format(problem.durations['duration_check'] + problem.durations['duration_solution_creation']))
            print("=======================")
        else:
            print("Failed to solve within the time limits.")