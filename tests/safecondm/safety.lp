

%%%%%%%%%% TIMESTEPS %%%%%%%%%%%%




#show .


%%%%%%%%%% MODEL PROPERTIES %%%%%%%%%%%%


product(T, X) :-
	is_a(product(X), T), type(T), timestep(X, Te), time_now(T0), Te <= T0.

on(S, X) :-
	containedIn(product(X), storey(S)), timestep(X, Te), time_now(T0), Te <= T0.

type(slab; wall; opening; column).
storey(S) :- product(slab, X), on(S, X).

#show storey/1.
#show time_now/1.

&union{Id : product(T, Id), on(S, Id)} = union(T, S) :- 
	type(T), storey(S).

&buffer{union(slab, S), "0.01"} = buffer(union(slab, S)) :-
	storey(S), &union{Id : product(slab, Id), on(S, Id)} = union(slab, S).

&buffer{union(wall, S), "0.01"} = buffer(union(wall, S)) :-
	storey(S), &union{Id : product(wall, Id), on(S, Id)} = union(wall, S).

&buffer{union(column, S), "0.02"} = buffer(union(column, S)) :-
	storey(S), &union{Id : product(column, Id), on(S, Id)} = union(column, S).

&diff{buffer(union(slab, S)) - buffer(union(column, S))} = walkable_surface(S) :- 
	storey(S), &buffer{union(wall, S), "0.01"} = buffer(union(wall, S)),
	&buffer{union(column, S), "0.02"} = buffer(union(column, S)).

&intersect{buffer(union(wall, S)); union(opening, S)} = transition_space(S) :- 
	storey(S), &buffer{union(wall, S), "0.01"} = buffer(union(wall, S)),
	&union{Id : product(opening, Id), on(S, Id)} = union(opening, S).

&union{buffer(union(slab, S)); buffer(union(wall, S))} = constructed_surface(S) :- 
	storey(S),	
	&buffer{union(slab, S), "0.01"} = buffer(union(slab, S)),
	&buffer{union(wall, S), "0.01"} = buffer(union(wall, S)).

&union{constructed_surface(S) : storey(S)} = union(constructed_surface) :-
	storey(S), &union{buffer(union(slab, S)); buffer(union(wall, S))} = constructed_surface(S).

&buffer{union(constructed_surface), "10.0"} = site :-
	storey(S), &union{constructed_surface(S) : storey(S)} = union(constructed_surface).

&diff{site - constructed_surface(S)} = fall_space(S) :-
	storey(S), &buffer{union(constructed_surface), "10.0"} = site,
	&union{buffer(union(slab, S)); buffer(union(wall, S))} = constructed_surface(S).

&buffer{fall_space(S), "0.05"} = buffer(fall_space(S)) :-
	storey(S), &diff{site - constructed_surface(S)} = fall_space(S).

&union{walkable_surface(S); transition_space(S)} = movement_space(S) :- 
	storey(S),
	&diff{buffer(union(slab, S)) - buffer(union(column, S))} = walkable_surface(S),
	&intersect{buffer(union(wall, S)); union(opening, S)} = transition_space(S).

&intersect{movement_space(S); buffer(fall_space(S))} = hazard_space(S) :-
	storey(S), 
	&union{walkable_surface(S); transition_space(S)} = movement_space(S), 
	&buffer{fall_space(S), "0.05"} = buffer(fall_space(S)).



#program guess. 

%#const t0 = 97.
1{time_now(1..122)}1.
%time_now(200).


%#program check.
%:- 2{time_now(150..200)}.




%*
&draw{buffer(union(slab, S)); union(slab, S)} :- 
	&union{Id : product(slab, Id), on(S, Id)} = union(slab, S), storey(S),
	&buffer{union(slab, S), "0.01"} = buffer(union(slab, S)).

&draw{buffer(union(wall, S)); union(wall, S)} :- 
	&union{Id : product(wall, Id), on(S, Id)} = union(wall, S), storey(S),
	&buffer{union(wall, S), "0.01"} = buffer(union(wall, S)).

&draw{buffer(union(column, S)); union(column, S)} :- 
	&union{Id : product(column, Id), on(S, Id)} = union(column, S), storey(S),
	&buffer{union(column, S), "0.01"} = buffer(union(column, S)).

&draw{walkable_surface(S)} :- 
	storey(S), &diff{buffer(union(slab, S)) - buffer(union(column, S))} = walkable_surface(S).

&draw{transition_space(S)} :- 
	storey(S), &intersect{buffer(union(wall, S)); union(opening, S)} = transition_space(S).

&draw{constructed_surface(S)} :- 
	storey(S), &union{buffer(union(slab, S)); buffer(union(wall, S))} = constructed_surface(S).

&draw{movement_space(S); buffer(fall_space(S)); hazard_space(S)} :- 
	storey(S),
	&union{walkable_surface(S); transition_space(S)} = movement_space(S), 
	&buffer{fall_space(S), "0.05"} = buffer(fall_space(S)), storey(S),
	&intersect{movement_space(S); buffer(fall_space(S))} = hazard_space(S).
*%

