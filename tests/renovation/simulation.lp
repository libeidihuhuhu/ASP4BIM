
%%% RENOVATION SUBJECTS %%%

subject(window; wall).

%%% RENOVATION APPROACHES %%%s

{approach(S, repair)} :- subject(S).
approach(S, replace) :- subject(S).
{approach(wall, remove)} :- subject(wall).

%%% RENOVATION FEATURES %%%s

1{feature(window, replace, glazing); feature(window, replace, width); feature(window, replace, translate)} :- approach(window, replace).
feature(wall, replace, translate) :- approach(wall, replace).

%%% RENOVATION VALUES %%%

glazing(single; double; triple).
window_width(3; 4; 5).
window_translate(-2; -1; 0; 1; 2).
wall_translate(-1; 0; 1).

1{value(window, replace, glazing, G) : glazing(G)}1 :- feature(window, replace, glazing).
1{value(window, replace, width, W) : window_width(W)}1 :- feature(window, replace, width).
1{value(window, replace, translate, T): window_translate(T)}1 :- feature(window, replace, translate).
1{value(wall, replace, translate, T): wall_translate(T)}1 :- feature(wall, replace, translate).

%%% DIMENSIONAL PROPERTIES %%%

width(window, 2).
height(window, 2).
width(wall, 4).
height(wall, 3).

new_width(S, W) :- value(S, replace, width, W).     %% DIMENSIONAL CHANGES
new_width(S, W) :- not value(S, replace, width, _), width(S, W).     %% NO DIMENSIONAL CHANGES
new_perimeter(S, P) :- new_width(S, W), height(S, H), P = 2*W + 2*H.
new_area(S, W*H) :- new_width(S, W), height(S, H).

%%% THERMAL PROPERTIES %%%

insulation(window, 4).
insulation(wall, 2).

u_value(single, 3).
u_value(double, 2).
u_value(triple, 1).

new_insulation(S, V) :- value(S, replace, glazing, G), u_value(G, V).     %% THERMAL CHANGES
new_insulation(S, V) :- not value(S, replace, glazing, _), insulation(S, V).     %% NO THERMAL CHANGES

%%% SPATIAL VIABILITY %%%

footprint(window, (1, 3)).
footprint(wall, (0, 4)).

new_footprint(S, (X + T, X + W + T)) :-     %% POSITIONAL CHANGES
	footprint(S, (X, _)), new_width(S, W), value(S, replace, translate, T).

new_footprint(S, (X, X + W)) :-     %% NO POSITIONAL CHANGES
	footprint(S, (X, _)), new_width(S, W), not value(S, replace, translate, _).

consistent:-
	new_footprint(window, (X1, Y1)), new_footprint(wall, (X2, Y2)),
	X1 > X2, Y1 < Y2.



#show a/6.

&simulation{P1, P2, A1, A2, U1, U2} :- 
	new_perimeter(window, P1),
	new_perimeter(wall, P2),
	new_area(window, A1),
	new_area(wall, A2),
	new_insulation(window, U1),
	new_insulation(wall, U2).


a(P1, P2, A1, A2, U1, U2) :-
	new_perimeter(window, P1),
	new_perimeter(wall, P2),
	new_area(window, A1),
	new_area(wall, A2),
	new_insulation(window, U1),
	new_insulation(wall, U2).

#program check.

:- not consistent.



#show .



