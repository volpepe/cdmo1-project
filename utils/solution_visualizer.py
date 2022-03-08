import argparse
from solution import parse_solutions_file

# A simple script for visualizing a given solution on screen.

def parse_args():
    args = argparse.ArgumentParser()
    args.add_argument('--solution', '-s',
        default="utils/samples/solution_sample.txt",
        help="Path to a solution file", 
        type=str
    )
    args.add_argument('--output', '-o',
        default=None,
        help="Path to save the output image",
        type=str
    )
    return args.parse_args()
    
if __name__ == "__main__":
    args = parse_args()
    filename = args.solution
    instance = parse_solutions_file(filename)
    instance.draw(args.output)
    