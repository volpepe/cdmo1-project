% 1. Importing global constraints:

include "alldifferent.mzn";

% 2. Inputs for the problem:

int: w;       % Width of the plate.
int: n;       % Number of circuits to place on the plate.
set of int: CIRCUITS = 1..n;
array[CIRCUITS,1..2] of int: measures;  % The width and height of every circuit to place.

% Intermediate variable: the sum of all heights to give an upper bound to h
int: max_h = sum(col(measures, 2));

% 3. Variables for the problem:

% Height of the plate. 
% The height is between 0 (no circuits on the plate) and the sum of all
% heights of all circuits (the case where all circuits are stacked one on top
% of the other, which provides a worst case scenario).
var 0..max_h: h;

% Positions of the circuits
% The x coordinate is necessarily between 0 and w.
% The y coordinate is necessarily between 0 and h.
set of int: POSSIBLE_X = 0..w;
set of int: POSSIBLE_Y = 0..max_h;
array[CIRCUITS] of var POSSIBLE_X: x_positions;
array[CIRCUITS] of var POSSIBLE_Y: y_positions;
% Post a clearer upper-bound constraint after the declaration because h is a var
constraint forall (c in CIRCUITS)(y_positions[c] <= h);
% Another obvious constraint is that there shouldn't be two circuits on the same
% position. Instead of checking all pairs of circuits for "same x implying different y" and
% viceversa, we translate all positions of circuits to a single number (row*w+col)
% and check that all circuits are assigned to a different number with the alldifferent
% constraint, which also allows for a better propagation.
set of int: POSSIBLE_TRANSL_POS = 0..(max_h+1)*w;
array[CIRCUITS] of var POSSIBLE_TRANSL_POS: transl_pos;
% Populate the array of translated positions
constraint forall (c in CIRCUITS)(transl_pos[c] = y_positions[c] * w + x_positions[c]);
% Then we can define the actual constraint using alldifferent
constraint alldifferent(transl_pos);

% 4. Actual constraints on the variables

% What is the value of h? It's the maximum between the values of y_positions + h of 
% circuits
constraint h = max([y_positions[c] + measures[c,2] | c in CIRCUITS]);

% TODO: DEFINE A NO-OVERLAP FOR CIRCUITS

% 5. Search

solve minimize h;

output ["measures\(measures)\tmax_h=\(max_h)\th=\(h)\n"];