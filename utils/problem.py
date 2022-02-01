from typing import List, Sequence

class IncompleteCircuit():

    def __init__(self, w:int, h:int) -> None:
        self.w = w
        self.h = h

    def __str__(self) -> str:
        return "{}x{} circuit at unknown position".format(self.w, self.h)

class ProblemInstance():
    
    def __init__(self, wg:int, n:int, 
            circuits:Sequence[IncompleteCircuit]=None) -> None:
        self.wg = wg
        self.n = n
        self.circuits = [] if circuits is None else circuits

    def add_circuit(self, circuit:IncompleteCircuit):
        self.circuits.append(circuit)

    def format_for_dzn(self) -> str:
        txt = 'w = {};\nn = {};\nmeasures = [|'.format(self.wg, self.n)
        for circuit in self.circuits:
            txt += '{}, {},\n|'.format(circuit.w, circuit.h)
        txt += '];'
        return txt

    def write_to_dzn(self, filename:str, 
                     initial_solution=None):
        txt = self.format_for_dzn()
        if initial_solution is not None:
            txt += '\ninitial_x = {};\ninitial_y = {};'.format(
                [c.x0 for c in initial_solution.circuits],
                [c.y0 for c in initial_solution.circuits]
            )
        with open(filename, 'w') as f:
            f.write(txt)


def order_by_area(circuits):
    # Returns circuits sorted by their area (largest first)
    return sorted(circuits, key=lambda c:c.h*c.w, reverse=True)

def parse_problem_file(filename:str) -> ProblemInstance:
    with open(filename, 'r') as f:
        lines = [x.rstrip() for x in f.readlines()]
    # First line (wgrid and hgrid)
    wg = int(lines[0])
    # Second line (n of instances)
    n = int(lines[1])
    # Other lines (instances, w, h, x, y)
    instance = ProblemInstance(wg, n)
    for inst in lines[2:]:
        w, h = [int(v) for v in inst.split(' ')]
        instance.add_circuit(IncompleteCircuit(w, h))
    # Sort instance circuits by their areas
    instance.circuits = order_by_area(instance.circuits)
    return instance