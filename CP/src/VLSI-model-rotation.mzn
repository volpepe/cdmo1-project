% IMPORTS
include "alldifferent.mzn";
include "cumulative.mzn";
include "count.mzn";
include "diffn.mzn";
include "lex_lesseq.mzn";

% INPUTS AND VARIABLES
% ASSUMPTION: circuits have been ordered by largest circuit to smallest
int: w;       % Width of the plate.
int: n;       % Number of circuits to place on the plate.
set of int: CIRCUITS = 1..n;
array[CIRCUITS,1..2] of int: measures;  % The width and height of every circuit to place. They are interchangeable in this case.
int: max_measure = max(measures);       % We give a name to the maximum element in the measures array
% Initial solutions. 
array[CIRCUITS] of int: initial_x;
array[CIRCUITS] of int: initial_y;

% Heights and widths are vars in this case. We can give upper bounds using the maximum measure found before
array[CIRCUITS] of var 1..max_measure: current_heights;
array[CIRCUITS] of var if max_measure < w then 1..max_measure else 1..w endif: current_widths;
% The constraint for these arrays is that one of the measures is the height, while the other is width
constraint forall (c in CIRCUITS) ( (current_heights[c] in { measures[c,1], measures[c,2] }) /\
                                    (current_widths[c]  in { measures[c,1], measures[c,2] }) /\
                                    (current_heights[c] = measures[c,1] <-> current_widths[c] = measures[c,2] ) /\
                                    (current_heights[c] = measures[c,2] <-> current_widths[c] = measures[c,1] ))::domain;

% Intermediate variable: the maximum height reached by the initial solution (we use the original height)
int: max_h = max([ initial_y[c] + measures[c,2] | c in CIRCUITS ]);
% We can also obtain a lower bound for the height of the board in the solution
% which is given by dividing the sum of the areas of the circuits by W.
% This lower bound corresponds to the real optimal height when no empty spaces
% are present between the circuits, otherwise it's always <= than the real height
int: low_h = floor(sum([ col(measures,1)[c] * col(measures,2)[c] | c in CIRCUITS ]) / w);

% VARIABLES
% Height of the plate. 
% The height is between low_h and max_h, which provides a worst case scenario).
var low_h..max_h: h;
% Positions of the circuits
% The x coordinate is necessarily between 0 and w.
% The y coordinate is necessarily between 0 and max_h.
set of int: POSSIBLE_X = 0..w;
set of int: POSSIBLE_Y = 0..max_h;
array[CIRCUITS] of var POSSIBLE_X: x_positions;
array[CIRCUITS] of var POSSIBLE_Y: y_positions;

% CONSTRAINTS

% - REDUNDANT
% Post an upper-bound constraint on y_positions after the declaration because h is a var
constraint forall (c in CIRCUITS)(
    y_positions[c] + current_heights[c] <= h
)::domain;
% To keep all circuits within the width boundary, we constrain x_positions + widths.
constraint forall (c in CIRCUITS)(
    x_positions[c] + current_widths[c] <= w
)::domain;

% - NORMAL 
% To avoid overlaps between circuits, we can use the diffn global constraint.
% diffn is a global constraint that "constrains rectangles i, given by their origins 
% (x[i], y[i]) and sizes (dx[i], dy[i]), to be non-overlapping. 
constraint diffn(x_positions, y_positions, current_widths, current_heights)::domain; 

% We can use the "cumulative" global constraint to create solutions where the 
% circuits are placed so that they never occupy more than a certain amount of space.
% The cumulative global constraint is used to constrain the usage of a shared resource.
% Usually, the main agents at play with this constraint are tasks with a starting time,
% a duration and a resource requirement to be placed in a resource with a certain capacity.
% We can make the following analogy:
% - tasks are circuits
% - the width of the plate is our capacity
% - the starting time of the task is the assigned y_position (we look at the "rotated" circuit)
% - the duration is the height of the circuit
% - the resource requirement of the task is the width of the circuit
% Basically, this means that at any height, the circuits are constrained to be placed within
% the w columns.
constraint cumulative(y_positions, [ current_heights[c] | c in CIRCUITS ], 
                      [ current_widths[c] | c in CIRCUITS ], w)::domain;
% The same can be told for the x axis. In this case:
% - The height of the circuit is our capacity
% - The starting time of the task is the assigned x_position
% - The duration is the width of the circuit
% - The resource requirement is the height of the circuit
% So, circuits are also constrained to be within height h
constraint cumulative(x_positions, [ current_widths[c] | c in CIRCUITS ],
                      [current_heights[c] | c in CIRCUITS ], h)::domain;
                      
% DUAL VIEW
% Another obvious constraint is that there shouldn't be two circuits on the same
% position. It's a redundant constraint because we'll later define some non-overlapping 
% constraints, but we can implement this using a dual viewpoint and a free global constraint,
% so it should help propagation.
% Instead of checking all pairs of circuits for "same x implying different y" and
% viceversa, we translate all positions of circuits to a single number (row*w+col)
% and check that all circuits are assigned to a different number with the alldifferent
% constraint, which also allows for a better propagation.
set of int: POSSIBLE_TRANSL_POS = 0..(max_h+1)*w;
array[CIRCUITS] of var POSSIBLE_TRANSL_POS: transl_pos;
% Channeling constraint between these two viewpoints
constraint forall (c in CIRCUITS)(
  transl_pos[c] = y_positions[c] * w + x_positions[c]
)::domain;
% Then we can define the actual constraint using alldifferent.
constraint alldifferent(transl_pos)::domain;
% With this different point of view, can try to reduce waste of space (as well as reduce the search space)
% by constraining at least one circuit to be in the origin position.
constraint count(i in transl_pos)(i = 0) = 1::domain; % Requires that exactly one of the positions is (0,0)        

% SYMMETRY BREAKING
% Flipping a solution horizontally/vertically or by the diagonals generates another
% viable solution.
% - Not rotations, because we are not always dealing with square circuits.
% Therefore, we must pose some symmetry breaking constraints.
% Given w the total width of the grid, x, y, xw and yh the specific x,y coordinates of a circuit and
% its width and height:
% - In a horizontal rotation, block at position [x,y] becomes a block at position [w-x-xw, y]
% - In a vertical rotation, block at position [x,y] becomes a block at position [x, h-y-yh]
% - When flipping over a diagonal, block at position [x,y] becomes a block at position [w-x-xw, h-y-yh]
% To pose these constraints we actually re-use the 1d "translated" model which contains the starting
% positions of the circuits
constraint symmetry_breaking_constraint(
    % Lexicographic symmetry breaking constraints
    % 1. Horizontal flip: the new "translated array" is constructed by calculating what would be the
    % translated position at [w-x-xw, y], where for all circuits c, y = y_positions[c], x = x_positions[c],
    % xw = widths[c]
    lex_lesseq(transl_pos, [ y_positions[c] * w + ( w - x_positions[c] - current_widths[c] ) | c in CIRCUITS ])
    % 2. Vertical flip: the new "translated array" is constructed by calculating what would be the
    % translated position at [x, h-y-yh], where for all circuits c, y = y_positions[c], x = x_positions[c],
    % yh = heights[c]
/\  lex_lesseq(transl_pos, [ ( h - y_positions[c] - current_heights[c] ) * w + x_positions[c] | c in CIRCUITS ])
    % 3. Diagonal flip: the new "translated array" is constructed by calculating what would be the
    % translated position at [w-x-xw, h-y-yh]
/\  lex_lesseq(transl_pos, [ ( h - y_positions[c] - current_heights[c] ) * w + 
                             ( w - x_positions[c] - current_widths[c]  ) | c in CIRCUITS ])
)::domain;

% What is the value of h? It's the maximum between the values of y_positions + h of 
% circuits
constraint h = max([y_positions[c] + current_heights[c] | c in CIRCUITS])::domain;

% SEARCH
ann : search_ann = seq_search([
    int_search(current_heights, input_order, indomain_random), % Choose a random rotation
    int_search(y_positions, input_order, indomain_min),        % Try to assign the y_positions, assigning the minimum values to the largest circuits first because we need to minimize height
    int_search(x_positions, input_order, indomain_min),        % Then assign the min values to x_positions, so to have a compact representation
]);


include "gecode.mzn";
solve :: search_ann ::
         restart_luby(250) ::                      % Apply Luby restarting
         relax_and_reconstruct(transl_pos, 50,     % For large neighbourhood search if we work with gecode: upon restart keep some of the variables fixed
             [ initial_y[c] * w + initial_x[c] | c in CIRCUITS ]      %   to the previous (good) solutions and explore those neighbourhoods.
         )                                         % Also, start from the initial solution.
         minimize h;

output ["x_pos=\(x_positions)\ty_pos=\(y_positions)\th=\(h)\ntransl_pos=\(transl_pos)\ncurrent_heights=\(current_heights)\ncurrent_widths=\(current_widths)\n"];