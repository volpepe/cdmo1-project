from typing import Sequence
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.cm import get_cmap
from matplotlib.ticker import MultipleLocator
import numpy as np
from problem import IncompleteCircuit, ProblemInstance

class Circuit(IncompleteCircuit):

    def __init__(self,
                w:int,
                h:int,
                x:int,
                y:int) -> None:
        self.w = w
        self.h = h
        self.x0 = x
        self.y0 = y
        self.x1 = self.x0 + self.w
        self.y1 = self.y0 + self.h

    def __str__(self) -> str:
        return "{}x{} circuit at ({}, {})".format(self.w, self.h, self.x0, self.y0)

class SolutionInstance(ProblemInstance):

    def __init__(self, wg:int, hg:int,
        n:int, circuits:Sequence[Circuit]=None) -> None:
        self.wg = wg
        self.hg = hg
        self.n = n
        self.circuits = [] if circuits is None else circuits

    def add_circuit(self, circuit:Circuit):
        self.circuits.append(circuit)

    def draw(self, out=None):
        assert self.n == len(self.circuits), \
            "The number of circuits to draw does not correspond to the instanced circuits."
        plt.figure(figsize=(8,8))
        ax = plt.gca()
        cmap = get_cmap('rainbow')
        colors_idxs = np.linspace(0.0, 1.0, num=self.n)
        for i in range(self.n):
            circuit:Circuit = self.circuits[i]
            rect = patches.Rectangle((circuit.x0, circuit.y0), circuit.w, circuit.h, 
                linewidth=2, edgecolor='black', facecolor=cmap(colors_idxs[i]), fill=True)
            print("Adding {}".format(circuit))
            ax.add_patch(rect)
        ax.set_xlim(0, self.wg)
        ax.set_ylim(0, self.hg)
        ax.xaxis.set_major_locator(MultipleLocator(1))
        ax.yaxis.set_major_locator(MultipleLocator(1))
        ax.grid(which='major', linestyle='--')
        ax.set_aspect('equal', adjustable='box')
        if out is None:
            plt.show()
        else:
            plt.savefig(out)
    
    def write_to_file(self, filename):
        with open(filename, 'w') as f:
            f.write("{} {}\n".format(self.wg, self.hg))
            f.write("{}\n".format(self.n))
            f.writelines(["{} {} {} {}\n".format(c.w, c.h, c.x0, c.y0)
                for c in self.circuits])


class RotatingSolutionInstance(SolutionInstance):
    
    # This class allows for rotation of circuits: therefore before
    # calling draw or printing a solution we should fix heights and
    # widths of the circuits.
    def fix_circuits_rotation(self, widths, heights):
        for i, circuit in enumerate(self.circuits):
            circuit.h = heights[i]
            circuit.w = widths[i]


def parse_solutions_file(filename):
    with open(filename, 'r') as f:
        lines = [x.rstrip() for x in f.readlines()]
    # First line (wgrid and hgrid)
    wg, hg = [int(v) for v in lines[0].split(' ')]
    # Second line (n of instances)
    n = int(lines[1])
    # Other lines (instances, w, h, x, y)
    instance = SolutionInstance(wg, hg, n)
    for inst in lines[2:]:
        w, h, x, y = [int(v) for v in inst.split(' ')]
        instance.add_circuit(Circuit(w, h, x, y))
    return instance
