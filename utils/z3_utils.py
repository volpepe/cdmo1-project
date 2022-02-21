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