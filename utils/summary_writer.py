from problem import ProblemInstance
from solution import SolutionInstance


class Summary():
    def __init__(self, filename:str) -> None:
        self.fn = filename
        self.open_file = open(self.fn, 'w', encoding='utf-8')

    def write(self, text, sep='\n'):
        self.open_file.write(text + sep)

    def close(self):
        # Once called, we cannot write on the file anymore
        self.open_file.close()

    def init_problem(self, name:str, problem:ProblemInstance):
        text = """============================
Solving problem {}.
- Max width: {}.
- Circuits: {}.""".format(name, problem.wg, problem.n)
        self.write(text)

    def write_initial_solution(self, solution:SolutionInstance, time):
        text="""- Initial solution found in {} seconds.
- Starting xs: {}
- Starting ys: {}
- Starting h: {}""".format(time,
            [c.x0 for c in solution.circuits],
            [c.y0 for c in solution.circuits],
            solution.hg)
        self.write(text)

    def write_best_found_solution(self, solution:SolutionInstance, time):
        text="""------
Couldn't reach optimal solution in {}.
Best found solution:
- Best xs: {}
- Best ys: {}
- Best h: {}
""".format(
            time, 
            [c.x0 for c in solution.circuits],
            [c.y0 for c in solution.circuits],
            solution.hg
        )
        self.write(text)

    def write_final_solution(self, solution:SolutionInstance, time):
        text="""------
- Final solution found in {} seconds.
- Final xs: {}
- Final ys: {}
- Optimal h: {}
""".format(time,
            [c.x0 for c in solution.circuits],
            [c.y0 for c in solution.circuits],
            solution.hg)
        self.write(text)