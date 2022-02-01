% INPUTS AND VARIABLES
int: w;       % Width of the plate.
int: n;       % Number of circuits to place on the plate.
set of int: CIRCUITS = 1..n;
array[CIRCUITS,1..2] of int: measures;  % The width and height of every circuit to place.
array[CIRCUITS] of int: widths = col(measures, 1);  % Just a renaming of the above columns for convenience
array[CIRCUITS] of int: heights = col(measures, 2);
% Initial solutions
array[CIRCUITS] of int: initial_x;
array[CIRCUITS] of int: initial_y;

array[CIRCUITS, 1..2] of int: testarr = array2d(CIRCUITS, 1..2, [ if j mod 2 = 0 then widths[c] else heights[c] endif | c in CIRCUITS, j in 1..2 ]);

solve satisfy;

output ["testarr=\(testarr)\n"];
