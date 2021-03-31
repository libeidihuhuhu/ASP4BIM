

timestep(X, Te) :-
	is_a(product(X), _), 
	belongsTo(product(X), task(L)),
	construct(task(L), Ts), 
	resource(task(L), Td), 
	Te = Ts + Td.

timestep(Y, Te) :-
	is_a(product(Y), _), 
	voids(product(Y), product(X)),
	belongsTo(product(X), task(L)),
	construct(task(L), Ts), 
	resource(task(L), Td), 
	Te = Ts + Td.

%#show timestep/2.