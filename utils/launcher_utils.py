import os
import glob
from typing import Sequence
from problem import ProblemInstance, parse_problem_file

# General utils for all launchers

class SubOptimalException(Exception):
    pass

def get_problem_filenames(pattern:str) -> Sequence[str]:
    return [fn for fn in glob.glob(pattern)]

def get_problem_instance(fn:str) -> ProblemInstance:
    return parse_problem_file(fn)

def get_output_filename(output_path: str, input_fn:str, rot:bool) -> str:
    return os.path.join(output_path, input_fn.split(os.sep)[-1].replace(
        "ins", "out" if not rot else "out-rot")
    )