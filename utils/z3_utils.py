from itertools import combinations
from z3 import *

# This file contains some complex constraints and other utility functions
# for SAT and SMT models.

def index_orders(var, c1, c2):
    # Since in the SAT model, lr does not contain lr[i][j] when i == j,
    # we created this function to make indexing into the lr array
    # more transparent.
    if c1 == c2:
        raise ValueError
    if c2 > c1:
        return var[c1][c2-1]
    else:
        return var[c1][c2]

def at_least_one(bool_vars):
    return Or(bool_vars)

def at_most_one(bool_vars):
    return [Not(And(pair[0], pair[1])) for pair in combinations(bool_vars, 2)]

def exactly_one(solver, bool_vars):
    solver.add(at_most_one(bool_vars))
    solver.add(at_least_one(bool_vars))

def max_z3(vars):
    '''
    Implementation of the max function as a constraint within the Z3 framework
    '''
    Max = vars[0]
    for v in vars[1:]:
        Max = If(v > Max, v, Max)
    return Max

def cumulative_z3(start_times, durations, res_requirements, bound, place_lb, place_ub):
    '''
    Cumulative constraint for Z3: we iterate over all possible times within the provided
    lower and upper bound for the placement of the circuits and for each time we check 
    which tasks are involved by considering the start and end times for each task. 
    For all involved tasks, we sum their resource requirements and constrain their sum to 
    be below the fixed bound.
    '''
    return [Sum([           # Sum over times in bound
                If(And(start_times[i] <= t, t < start_times[i] + durations[i]), res_requirements[i], 0) 
                for i in range(len(start_times))]) <= bound
            for t in range(place_lb, place_ub)]

def lex_leq_z3(vars1, vars2):
    '''
    Simple implementation of the lexicographic <= constraint
    '''
    constraints = [vars1[0] <= vars2[0]]
    for i in range(1, len(vars1)-1):
        constraints.append(Implies(vars1[i] == vars2[i], vars1[i+1] <= vars2[i+1]))
    return And(constraints)