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

% The constraint for these arrays is that one of the measures is the height, while the other is width
constraint forall (c in CIRCUITS) ( (current_heights[c] in { measures[c,1], measures[c,2] }) /\
                                    (current_widths[c]  in { measures[c,1], measures[c,2] }) /\
                                    (current_heights[c] = measures[c,1] <-> current_widths[c] = measures[c,2] ) /\
                                    (current_heights[c] = measures[c,2] <-> current_widths[c] = measures[c,1] ))::domain;

% Intermediate variable: the maximum height reached by the initial solution (we use the original height)
int: max_h = max([ initial_y[c] + measures[c,2] | c in CIRCUITS ]);

% VARIABLES
% Height of the plate. 
% The height is between 0 (no circuits on the plate) and the sum of all
% heights of all circuits (the case where all circuits are stacked one on top
% of the other, which provides a worst case scenario).
var 0..max_h: h;
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


% OTHER IDEAS AND TODOs

% Another constraint we can post is that along the border of a circuit there must be another circuit
% (except at the borders of the boards).
% To facilitate posting this constraint, we should construct another dual view of the model:
% a matrix of integers, each integer representing a circuit and the number -1 representing
% the absence of circuits.
%set of int : OPTIONAL_CIRCUITS = -1..n;
%array[POSSIBLE_X, POSSIBLE_Y] of var OPTIONAL_CIRCUITS : M;
% channeling constraints to link the two models
%constraint forall(c in CIRCUITS) (
    % Mark for each circuit the positions it occupies
%    forall( i in x_positions[c]..min(w, x_positions[c]+measures[c,1]),
%            j in y_positions[c]..min(max_h, y_positions[c]+measures[c,2]) )
%    ( M[i,j] = c )
%);
% The unoccupied positions should be marked with -1
%constraint forall (i in POSSIBLE_X, j in POSSIBLE_Y) (forall(c in CIRCUITS)
    % For all positions of the matrix, we check that it does not overlap with any circuit.
    % Instead of using 
    % not exists(c in CIRCUITS) ( p(c) )
    % we use the equivalent
    % forall (c in CIRCUITS) ( not(p(c)) )
    % It probably does not change anything, but I'm highly suspicious of existential quantifiers
    % because poor implementations may lead to posting disjunctions, while forall is certainly
    % a sequence of conjunctions
%    (not ( i >= x_positions[c] /\ i < x_positions[c]+measures[c,1] /\
%           j >= y_positions[c] /\ j < y_positions[c]+measures[c,2] ) )
%      <-> M[i,j] = -1
%);
% These two constraints should be able to fill the whole matrix.

% TODO: for the cost function, think about how we can penalize empty spaces
% An idea could be using a cost function like: h*w + whitespaces, so the model
% will try to reduce h since the effect will be stronger

% What is the value of h? It's the maximum between the values of y_positions + h of 
% circuits
constraint h = max([y_positions[c] + current_heights[c] | c in CIRCUITS])::domain;
constraint h >= 0::domain;

% Also, another measure of quality is how many blank spaces are present in the model. 
% If we have w*h possible spaces and the area of each circuit is given by its wc and hc,
% we can say that the number of blank spaces is:
var int: blanks;
constraint blanks = w*h - sum([current_widths[c]*current_heights[c] | c in CIRCUITS])::domain;
constraint blanks >= 0::domain;

% SEARCH
ann : search_ann = seq_search([
    int_search(current_heights, input_order, indomain),       % Fix rotations
    int_search(x_positions, input_order, indomain_min),       % First assign the min values to x_positions, so to have a compact representation
    int_search(y_positions, input_order, indomain_min),       % Finally, try to assign the y_positions, assigning the minimum values to the largest circuits because we need to minimize height
]);


include "chuffed.mzn";
solve :: search_ann :: 
         restart_luby(200)                      % Apply Luby restarting
         minimize blanks;

output ["x_pos=\(x_positions)\ty_pos=\(y_positions)\th=\(h)\ntransl_pos=\(transl_pos)\ncurrent_heights=\(current_heights)\ncurrent_widths=\(current_widths)\n"];