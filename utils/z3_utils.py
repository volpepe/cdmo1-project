from itertools import combinations
from z3 import *

# Define complex constraints
def at_least_one(bool_vars):
    return Or(bool_vars)

def at_most_one(bool_vars):
    return [Not(And(pair[0], pair[1])) for pair in combinations(bool_vars, 2)]

def exactly_one(solver, bool_vars):
    solver.add(at_most_one(bool_vars))
    solver.add(at_least_one(bool_vars))

def index_orders(var, c1, c2):
    if c1 == c2:
        raise ValueError
    if c2 > c1:
        return var[c1][c2-1]
    else:
        return var[c1][c2]

def max_z3(vars):
    Max = vars[0]
    for v in vars[1:]:
        Max = If(v > Max, v, Max)
    return Max

def cumulative_z3(start_times, durations, res_requirements, bound):
    '''
    Cumulative constraint for Z3: we iterate over all possible times within bound
    and for each time we check which tasks are involved by considering the start and
    end times for each task. For all involved tasks, we sum their resource requirements
    and constraint it to be below the fixed bound.
    '''
    return [Sum([           # Sum over times in bound
                If(And(start_times[i] <= t, t < start_times[i] + durations[i]), res_requirements[i], 0) 
                for i in range(len(start_times))]) <= bound
            for t in res_requirements]

def lex_lessex_z3(vars1, vars2):
    constraints = [vars1[0] <= vars2[0]]
    for i in range(1, len(vars1)-1):
        constraints.append(Implies(vars1[i] == vars2[i], vars1[i+1] <= vars2[i+1]))
    return And(constraints)