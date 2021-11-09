 % 1. Importing global constraints:

include "alldifferent.mzn";
include "cumulative.mzn";
include "among.mzn";

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

% We can avoid overlapping circuits posting constraints on the dual view (transl_pos array).
% We need to consider each pair of circuits.
% Then, we consider an index hc over the height of the first of the two circuits
% The constraint is that the translated positions of the first row of the second circuit must not
% be in the set that is determined by the blocks occupied by c1. 
% If hc is the index on the height level of c1 and w is the width of the plate, 
% we can express the positions on one level of height with the range hc*w..hc*(w+1). 
% To correct this range, we add the y position of the circuit.
% We then use x(c1) (the x position of c1) as an offset from the initial element of the line (hc*w)
% and we can express the positions occupied by the block in that line as hc*w+x(c1)..hc*w+x(c1)+w(c1)
% (w(c1) being the width of the block c1). The translated position of c2 must simply not be in this range.
constraint forall (c1, c2 in CIRCUITS where c1!=c2) (
    forall (hc in y_positions[c1]-measures[c2,2]+1..y_positions[c1]+measures[c1,2]-1) (
        forall (c2_pos in transl_pos[c2]..transl_pos[c2]+measures[c1,1]-1) (
            not (c2_pos in 
            (hc*w+x_positions[c1])..(hc*w+x_positions[c1]+measures[c1,1]-1))
        )
    )
);

% TODO: THINK OF A MORE "GLOBAL" CONSTRAINT

% TODO: for the cost function, think about how we can penalize white spaces

% We can try to reduce waste of space (as well as reduce the search space)
% by constraining at least one circuit to be in the origin position.
constraint among(1, transl_pos, 0..0); % Requires that exactly one of the positions is (0,0)

%%%%%%%%%%%%%%% DEBATE: DOES THIS MAKE SENSE? %%%%%%%%%%%%%%%%%%%%%
% We can use the "cumulative" global constraint to create solutions where the 
% circuits are placed so that they never occupy more than a certain amount of space.
% The cumulative global constraint is used to constrain the usage of a shared resource.
% Usually, the main agents at play with this constraint are tasks with a starting time,
% a duration and a resource requirement to be placed in a resource with a certain capacity.
% We can make the following analogy:
% - tasks are circuits
% - the width of the plate as our capacity
% - the starting time of the task is the assigned x_position
% - the resource requirement of the task is the fixed width of the circuit
% - the duration is the fixed height of the circuit
% Basically, this means that at any height, the width is constrained to be within w.
%constraint cumulative(x_positions, col(measures, 2), col(measures, 1), w);
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% To keep all circuits within the width boundary, constrain x_positions + widths
constraint forall (c in CIRCUITS)(x_positions[c] + measures[c,1] <= w);

% What is the value of h? It's the maximum between the values of y_positions + h of 
% circuits
constraint h = max([y_positions[c] + measures[c,2] | c in CIRCUITS]);

% 5. Search

ann : search_ann = seq_search([
            int_search(y_positions, dom_w_deg, indomain_min),     % Try to assign the y_positions with first_fail, 
                                                                  % assigning the minimum values first because we need
                                                                  % to minimize height
            int_search(x_positions, dom_w_deg, indomain_min),  % Then assign randomically the values to x_positions
            restart_luby(500)
]);

solve :: search_ann
   minimize h;

output ["x_pos=\(x_positions)\ty_pos=\(y_positions)\th=\(h)\n"];