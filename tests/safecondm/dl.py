
# python app.py guess_check.lp 0 --quiet


import clingo, heapq
import clingo.ast
import time
import geomdb
import ast
import Polygon, Polygon.IO
import pyclipper

THEORY = """
#theory spatial {
	constant  { - : 1, unary };
	variable  { - : 1, unary };
	spatial_term {
		- : 3 , unary ;
		** : 2 , binary, right ;
		* : 1 , binary, left ;
		/ : 1 , binary , left ; 
		\\ : 1 , binary , left ;
		+ : 0 , binary, left ; 
		- : 0 , binary, left };
	&topology/1 : spatial_term, any;
	&union/1 : spatial_term, {=}, constant, any;
	&diff/1 : spatial_term, {=}, constant, any ;
	&buffer/1 : spatial_term, {=}, constant, any ;
	&intersect/1 : spatial_term, {=}, constant, any ;
	&draw/1 : spatial_term, any
}.
"""


theory_atom_names = ["union", "intersect", "diff", "buffer", "topology", "draw"]
spatial_function_names = ["union", "intersect", "diff", "buffer"]
spatial_relation_names = ["topology"]

spatial_artefact_names = ["constructed_surface", "walkable_surface", "transition_space", "site", "fall_space", "movement_space"]

repr = geomdb.repr

def addPolygon(p):
	res = p[0]
	for i in range(1, len(p)):
		res = res + p[i]
	return res

def inflate(c, th):
	delta = th / 4
	coordinates = tuple(c)
	pco = pyclipper.PyclipperOffset(delta)
	coordinates_scaled = pyclipper.scale_to_clipper(coordinates, 1000)
	pco.AddPath(coordinates_scaled, pyclipper.JT_MITER, pyclipper.ET_CLOSEDPOLYGON)
	th_ = int(th*1000)
	new_coordinates = pco.Execute(th_)
	new_coordinates_scaled = pyclipper.scale_from_clipper(new_coordinates, 1000)
	c_ = [tuple(new_coordinates_scaled[i]) for i in range(len(new_coordinates_scaled))]
	return c_

def deflate(c, th):
	delta = th / 4
	coordinates = tuple(c)
	pco = pyclipper.PyclipperOffset(delta)
	coordinates_scaled = pyclipper.scale_to_clipper(coordinates, 1000)
	pco.AddPath(coordinates_scaled, pyclipper.JT_MITER, pyclipper.ET_CLOSEDPOLYGON)
	th_ = int(th*1000)
	new_coordinates = pco.Execute(-th_)
	new_coordinates_scaled = pyclipper.scale_from_clipper(new_coordinates, 1000)
	c_ = [tuple(new_coordinates_scaled[i]) for i in range(len(new_coordinates_scaled))]
	return c_

def buffer_(l, th):
	c = l[0]
	newc = inflate(c, th)
	p = Polygon.Polygon(newc[0])
	for i in range(1, len(newc)):
		p.addContour(newc[i], 0)
	for j in range(1, len(l)):
		h = l[j]
		newc = deflate(h, th)
		for k in range(len(newc)):
			p.addContour(newc[k], 1)
	return p

def _buffer(p, th):
	lp = []
	for i in range(len(p)):
		if not p.isHole(i):
			l = [p[i]]
			pc = Polygon.Polygon(p[i])
			temp = 0
			area = 0
			for j in range(len(p)):
				if p.isHole(j):
					ph = Polygon.Polygon(p[j])
					if pc.covers(ph):
						if ph.area() > area:
							temp = p[j]
							area = ph.area()
			if temp != 0:
				l.append(temp)
			pi = buffer_(l, th)
			lp.append(pi)
	res = addPolygon(lp)
	return res

def _create_geom(c):
	c = ast.literal_eval(c)
	b, h = c[0], c[1]
	p = Polygon.Polygon(b[0])
	for i in range(len(b)-1):
		p.addContour(b[i], 0)
	if len(h) == 0:
		return p
	else:
		p.addContour(h[0], 1)
		for i in range(len(h)-1):
			p.addContour(h[i], 1)
		return p

def vertical_array(l, c):
	s = "%-" + str(c) + "s "  	
	n = 1
	i = 0
	while i < len(l)-1:
		l.insert(i+1, '|')
		i += (n+1)
		s += "%s %-" + str(c) + "s "
	#print(s)
	#print(l)
	return s % tuple(l)


def print_msg(s, detail_level):
	if detail_level <= PRINT_DETAIL_LEVEL:
		print(s)



################################ CHECKER() ################################


class Checker:
	
	def __init__(self):
		self._ctl = clingo.Control()
		self._map = []

	def backend(self):
		return self._ctl.backend()
	
	def add(self, guess_lit, check_lit):
		self._map.append((guess_lit, check_lit))
		
	def ground(self, check):
		with self._ctl.builder() as builder:
			for stm in check:
				print_msg(stm, 1)
				builder.add(stm)
		self._ctl.ground([("base", [])])

	def pcheck(self, control, assume):
		s, l = 15, 4
		assignment = control.assignment
		assumptions = []

		labels = ["guess lit", "check_lit", "guess truth", "state"]
		inputs = vertical_array(labels, s)
		print_msg(inputs, l)

		for guess_lit, check_lit in self._map:
			guess_truth = assignment.value(guess_lit)
			values = [guess_lit, check_lit, guess_truth]

			if check_lit in assume:
				values.append("assuming")
				outputs = vertical_array(values, s)
				print_msg(outputs, l)
				assumptions.append(check_lit)

			elif guess_truth != None:
				if guess_truth:
					values.append("assigning")
					outputs = vertical_array(values, s)
					print_msg(outputs, l)
					assumptions.append(check_lit)
				else:
					assumptions.append(-check_lit)

		ret = self._ctl.solve(assumptions)
		if ret.satisfiable is not None:
			return ret.satisfiable

		raise RuntimeError("search interrupted")



################################ GACPropagator(check) ################################



class GACPropagator:
	
	def __init__(self, check):
		self._check = check
		self._checkers = []
		self.sleep = .1

		self._h2l = {} # head theory atoms to solver literals
		self._b2l = {} # head body atoms to solver literals
		self._h2b = {}
		self._b2h = {}

		self._literals = []  ## program literals
		self._lit = []  ## solver literals
		self._p2t = {}  ## program literals of theory atoms
		self._l2t = {}  ## solver literals of theory atoms
		self._s2p = {} ## symbolic atoms to program literals

		#self._geoms = {"x":13, "y":24, "p":52, "q":8, "i":134, "j":68}
		self._geoms = {}
		self._rel = {}  ## spatial relations
		self._assigns = {}

	def _eval(self, t):
		#print(t.type)
		if t.type == clingo.TheoryTermType.Symbol:
			#return t.name
			return t
		if t.type == clingo.TheoryTermType.Number:
			return t.number
		if t.type == clingo.TheoryTermType.Function:
			return str(t)


	def init(self, init):
		
		for _ in range(init.number_of_threads):
			start_msg = "\n+++++++++++PropagateInit++++++++++++++++++++++++++++++++++++++++++++++++++++++"
			print_msg(start_msg, 3)
			char1 = "number of threads : " + str(init.number_of_threads)
			print_msg(char1, 1)
			char2 = "check mode : " + str(init.check_mode)
			print_msg(char2, 1)

			checker = Checker()
			self._checkers.append(checker)

			with checker.backend() as backend:
				labels = ["program lit", "solver lit", "symbolic atom"]
				inputs = vertical_array(labels, 15)
				print_msg(inputs, 2)

				for atom in init.symbolic_atoms:

					prg_lit = atom.literal
					guess_lit = init.solver_literal(prg_lit)
					init.add_watch(guess_lit)

					literals = self._literals
					lits = self._lit
					if prg_lit not in literals:
						literals.append(prg_lit)
					if guess_lit not in lits:
						lits.append(guess_lit)

					guess_truth = init.assignment.value(guess_lit)
		
					if guess_truth is False:
						print(False)
						continue

					check_lit = backend.add_atom(atom.symbol)

					#print('%-10s %s %-10s %s %-10s' % (atom.literal, '|', guess_lit, "|", atom.symbol))
					#print('%-10s %s %-10s %s %-10s' % (check_lit, '|', guess_lit, "|", atom.symbol))

					values = [prg_lit, guess_lit, atom.symbol]
					outputs = vertical_array(values, 15)
					print_msg(outputs, 2)
				
					if guess_truth is True:
						print_msg(True, 5)
						backend.add_rule([check_lit], [])

					else:   
						print_msg(None, 5)
						backend.add_rule([check_lit], [], True)
						checker.add(guess_lit, check_lit)

					if atom.symbol.name in spatial_relation_names:
						self._s2p.setdefault(atom.symbol, check_lit)				

				labels = ["program lit", "solver lit", "theory atom"]
				inputs = vertical_array(labels, 15)
				print_msg("\n" + inputs, 2)


				print_msg('%-80s %s %-10s' % ("geometry ID", '|', "object ID"), 3)

				for atom in init.theory_atoms:

					literal = atom.literal
					lit = init.solver_literal(literal)
					literals = self._literals
					lits = self._lit
					if literal not in literals:
						literals.append(literal)
					if lit not in lits:
						lits.append(lit)

					term = atom.term
					op = term.name
					loc = term.arguments[0].name

					values = [literal, lit, atom]
					outputs = vertical_array(values, 15)
					print_msg(outputs, 2)



					if op == "topology" and len(term.arguments) == 1:

						x = str(atom.elements[0].terms[0])
						y = str(atom.elements[0].terms[1])

						self._p2t.setdefault(atom.literal, []).append((op, loc, x, y))
						self._l2t.setdefault(lit, []).append((op, loc, x, y))

						if term.arguments[0].name == "head":
							h2l = self._h2l
							if (x, y) not in h2l.keys():
								h2l.setdefault((x, y), []).append(lit)

						if term.arguments[0].name == "body":
							b2l = self._b2l
							if (x, y) not in b2l.keys():
								b2l.setdefault((x, y), []).append(lit)

					if op == "union" and len(term.arguments) == 1:

						ids = sorted([self._eval(elt.terms[0]) for elt in atom.elements])
						#print(ids)
						new_id = str(ids)
						res = str(atom.guard[1])

						print_msg('%-80s %s %-10s' % (new_id, '|', res), 3)

						self._p2t.setdefault(atom.literal, []).append((op, loc, new_id, res))
						self._l2t.setdefault(lit, []).append((op, loc, new_id, res))

						if loc == "head":
							h2l = self._h2l
							if (new_id, res) not in h2l.keys():
								h2l.setdefault((new_id, res), []).append(lit)
							#init.add_watch(lit, 1)

						if loc == "body":
							b2l = self._b2l
							if (new_id, res) not in b2l.keys():
								b2l.setdefault((new_id, res), []).append(lit)
							#init.add_watch(lit, 1)

					if op == "intersect" and len(term.arguments) == 1:

						ids = sorted([self._eval(elt.terms[0]) for elt in atom.elements])
						#print(ids)
						new_id = str(ids)
						res = str(atom.guard[1])

						print_msg('%-80s %s %-10s' % (new_id, '|', res), 3)

						self._p2t.setdefault(atom.literal, []).append((op, loc, new_id, res))
						self._l2t.setdefault(lit, []).append((op, loc, new_id, res))

						if loc == "head":
							h2l = self._h2l
							if (new_id, res) not in h2l.keys():
								h2l.setdefault((new_id, res), []).append(lit)
							#init.add_watch(lit, 1)

						if loc == "body":
							b2l = self._b2l
							if (new_id, res) not in b2l.keys():
								b2l.setdefault((new_id, res), []).append(lit)
							#init.add_watch(lit, 1)

					if op == "diff" and len(term.arguments) == 1:

						x = str(atom.elements[0].terms[0].arguments[0])
						y = str(atom.elements[0].terms[0].arguments[1])
						#print(x, y)
						new_id = str([x, y])
						res = str(atom.guard[1])

						self._p2t.setdefault(atom.literal, []).append((op, loc, new_id, res))
						self._l2t.setdefault(lit, []).append((op, loc, new_id, res))

						if loc == "head":
							h2l = self._h2l
							if (new_id, res) not in h2l.keys():
								h2l.setdefault((new_id, res), []).append(lit)
							#init.add_watch(lit, 1)

						if loc == "body":
							b2l = self._b2l
							if (new_id, res) not in b2l.keys():
								b2l.setdefault((new_id, res), []).append(lit)
							#init.add_watch(lit, 1)

					if op == "buffer" and len(term.arguments) == 1:

						id = str(atom.elements[0].terms[0])
						cons = atom.elements[0].terms[1]
						#print(id, cons)

						new_id = str([id, cons])
						res = str(atom.guard[1])

						print_msg('%-80s %s %-10s' % (new_id, '|', res), 3)

						self._p2t.setdefault(atom.literal, []).append((op, loc, new_id, res))
						self._l2t.setdefault(lit, []).append((op, loc, new_id, res))

						if loc == "head":
							h2l = self._h2l
							if (new_id, res) not in h2l.keys():
								h2l.setdefault((new_id, res), []).append(lit)
							#init.add_watch(lit, 1)

						if loc == "body":
							b2l = self._b2l
							if (new_id, res) not in b2l.keys():
								b2l.setdefault((new_id, res), []).append(lit)
							#init.add_watch(lit, 1)

					if term.name == "draw" and len(term.arguments) == 1:

						#print(atom)
						ids_ = [self._eval(elt.terms[0]) for elt in atom.elements]
						ids = sorted(ids_)

						new_id = str(ids)
						#print(new_id)

						self._p2t.setdefault(atom.literal, []).append((op, loc, new_id))
						self._l2t.setdefault(lit, []).append((op, loc, new_id))

						if loc == "head":
							h2l = self._h2l
							if new_id not in h2l.keys():
								h2l.setdefault(new_id, []).append(lit)
							#init.add_watch(lit, 1)

						if loc == "body":
							b2l = self._b2l
							if new_id not in b2l.keys():
								b2l.setdefault(new_id, []).append(lit)
							#init.add_watch(lit, 1)

						#print(ids)
						#geom_ids = [self._eval.get(id) for id in ids]

						#print(geom_ids)

						#s = ids[0].split("(")[1].split(")")[0]

						#self._draw(geom_ids, s)


			h2l = self._h2l
			b2l = self._b2l
			heads = set(h2l)
			bodies = set(b2l)
			h2b = self._h2b
			b2h = self._b2h

			#print(heads)
			#print(bodies)
			#print(heads.intersection(bodies))

			for t in heads.intersection(bodies):
				head = h2l[t][0]
				body = b2l[t][0]
				if head not in h2b:
					h2b.setdefault(head, []).append(body)
				if body not in b2h:
					b2h.setdefault(body, []).append(head)

			print_msg("head to body : " + str(h2b), 5)
			print_msg("body to head : " + str(b2h), 5)

			for body in b2h.keys():
				heads = b2h.get(body)
				for head in heads:
					#print(head, body)
					print_msg("body : " + str(body) + "head : " + str(head), 5)
					init.add_clause([-body, head])
					init.add_clause([body, -head])

			print_msg("++++++++++++++++++++++++++++++++++++++++++++++++++++++PropagateInit+++++++++++\n", 3)

			print_msg("\n***************Grounding******************************************************",1)
			checker.ground(self._check)
			print_msg("******************************************************Grounding***************\n",1)


	def print_assignment(self, assignment):
		lits = self._lit
		literals = list(filter(lambda x : assignment.value(x) != None, lits))
		truth_values = [lit if assignment.value(lit) else -lit for lit in literals]
		decision_levels = [assignment.level(lit) for lit in literals]
		print_msg("truth_values : " + str(truth_values), 4)
		print_msg("decision_levels : " + str(decision_levels), 4)
		return


	def inspect_assignment(self, assignment):

		print("decision level : ", assignment.decision_level)
		print("has_conflict : ", assignment.has_conflict)
		print("is_total : ", assignment.is_total)
		print("max_size : ", assignment.max_size)
		print("root_level : ", assignment.root_level)
		print("size : ", assignment.size)
		return


	def propagate(self, control, changes):

		print_msg("\n------------------------------------------------------Propagate---------------", 2)
		print_msg("active thread : " + str(control.thread_id), 2)
		print_msg("changes : " + str(changes), 3)

		assignment = control.assignment
		self.print_assignment(assignment)

		#self.check_partial(control)
		self.check_simple(control)
			
		print_msg("------------------------------------------------------Propagate---------------\n", 2)


	def undo(self, thread_id, assignment, changes):

		print_msg("\n::::::::::::::::::::::::::::::::::::::::::::::::::::::Undo::::::::::::::::::::", 2)
		print_msg("active thread : " + str(thread_id), 2)
		print_msg("undo : " + str(changes), 3)

		print_msg("::::::::::::::::::::Undo::::::::::::::::::::::::::::::::::::::::::::::::::::::\n", 2)


	def _head_atoms(self, literals, map):

		head_atoms = []
		body_atoms = []

		for l in literals:
			if l in map.keys():
				atoms = map.get(l)
				for atom in atoms:
					if atom[1] == "head":
						if atom[0] not in spatial_relation_names:
							head_atoms.append(atom)
						else:
							body_atoms.append(atom)

		return head_atoms, body_atoms


	def _spatial_propagate(self, literals, map):

		eval, rel, assigns = self._geoms, self._rel, self._assigns
		print_msg("old eval : " + str(eval), 5)
		print_msg("old rel : " + str(rel), 5)

		reasoner = QSTR(eval, rel, assigns)
		head_atoms, body_atoms = self._head_atoms(literals, map)

		#print("propagate")
		#print(literals)
		#print(head_atoms)
		reasoner._evaluate(head_atoms)
		#reasoner._compute(body_atoms)
		assign = reasoner.get_assignment()
		relations = reasoner.get_rel()

		eval, rel, assigns = self._geoms, self._rel, self._assigns
		print_msg("new eval : " + str(eval), 5)
		print_msg("new rel : " + str(rel), 5)
		print_msg("new assign : " + str(assigns), 5)

		return assign, relations


	def get_assumptions(self, relations):

		assume = []
		s2p = self._s2p

		for p in relations.keys():
			r = relations.get(p)
			x, y = p[0], p[1]
			f = lambda s: clingo.Function(s, [])
			ext = clingo.Function("topology", [f(r), f(x), f(y)])
			print_msg("assumptions : " + str(ext), 3)
			if ext in s2p.keys():
				literal = s2p.get(ext)
				assume.append(literal)

		return assume

	def check_total(self, control):   ## check method as defined in clingo API

		#time.sleep(self.sleep)

		print_msg("\n;;;;;;;;;;;;;;;;Checking;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;", 2)

		print_msg("active thread : " + str(control.thread_id), 2)
		checker = self._checkers[control.thread_id]

		assignment = control.assignment
		self.print_assignment(assignment)

		if not checker.pcheck(control, []):
			conflict = []
			print_msg("(UNSATISFIABLE)", 2)
			print_msg('%-10s %s %-10s' % ("level", "|" , "decision lit"), 4)

			for level in range(1, assignment.decision_level+1):
				print_msg('%-10s %s %-10s' % (level, "|", assignment.decision(level)), 4)
				conflict.append(assignment.decision(level))
			print_msg("conflicts : " + str(conflict), 3)
			if conflict != []:
				control.add_nogood(conflict) and control.propagate()
				return

		literals = list(filter(lambda x : assignment.value(x)==True, self._lit))
		assign, relations = self._spatial_propagate(literals, self._l2t)
		print_msg("assign :" + " ".join(["{}={}".format(n, v) for n, v in assign.items()]), 5)
		assume = self.get_assumptions(relations)

		if not checker.pcheck(control, assume):
			conflict = []
			print_msg("(UNSATISFIABLE)", 2)
			print_msg('%-10s %s %-10s' % ("level", "|" , "decision lit"), 4)

			for level in range(1, assignment.decision_level+1):
				print_msg('%-10s %s %-10s' % (level, "|", assignment.decision(level)), 4)
				conflict.append(assignment.decision(level))
			print_msg("conflicts : " + str(conflict), 3)
			if conflict != []:
				control.add_nogood(conflict) and control.propagate()

			print_msg(";;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;Checking;;;;;;;;;;;;;;;;\n",2)
			return

		else:

			print_msg("(SATISFIABLE)", 2)
			print_msg(";;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;Checking;;;;;;;;;;;;;;;;\n", 2)
			return


	def check_partial(self, control):

		#time.sleep(self.sleep)

		print_msg("\n;;;;;;;;;;;;;;;;Checking;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;", 2)

		print_msg("active thread : " + str(control.thread_id), 2)
		checker = self._checkers[control.thread_id]

		assignment = control.assignment
		self.print_assignment(assignment)

		if not checker.pcheck(control, []):
			conflict = []
			print_msg("(UNSATISFIABLE)", 2)
			print_msg('%-10s %s %-10s' % ("level", "|" , "decision lit"), 4)

			for level in range(1, assignment.decision_level+1):
				print_msg('%-10s %s %-10s' % (level, "|", assignment.decision(level)), 4)
				conflict.append(assignment.decision(level))
			print_msg("conflicts : " + str(conflict), 3)
			if conflict != []:
				control.add_nogood(conflict) and control.propagate()
				return

		literals = list(filter(lambda x : assignment.value(x)==True, self._lit))
		assign, relations = self._spatial_propagate(literals, self._l2t)
		print_msg("assign :" + " ".join(["{}={}".format(n, v) for n, v in assign.items()]), 5)
		assume = self.get_assumptions(relations)

		if not checker.pcheck(control, assume):
			conflict = []
			print_msg("(UNSATISFIABLE)", 2)
			print_msg('%-10s %s %-10s' % ("level", "|" , "decision lit"), 4)

			for level in range(1, assignment.decision_level+1):
				print_msg('%-10s %s %-10s' % (level, "|", assignment.decision(level)), 4)
				conflict.append(assignment.decision(level))
			print_msg("conflicts : " + str(conflict), 3)
			if conflict != []:
				control.add_nogood(conflict) and control.propagate()

			print_msg(";;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;Checking;;;;;;;;;;;;;;;;\n",2)
			return

		else:

			print_msg("(SATISFIABLE)", 2)
			print_msg(";;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;Checking;;;;;;;;;;;;;;;;\n", 2)
			return


	def check_simple(self, control):

		#time.sleep(self.sleep)

		print_msg("\n;;;;;;;;;;;;;;;;Checking;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;", 2)

		print_msg("active thread : " + str(control.thread_id), 2)
		checker = self._checkers[control.thread_id]

		assignment = control.assignment
		#self.print_assignment(assignment)

		literals = list(filter(lambda x : assignment.value(x)==True, self._lit))
		assign, relations = self._spatial_propagate(literals, self._l2t)
		print_msg("assign :" + " ".join(["{}={}".format(n, v) for n, v in assign.items()]), 5)
		#assume = self.get_assumptions(relations)

		return


	def on_model(self, model):

		print_msg("\n================OnModel=======================================================", 2)
		print_msg("model thread : " + str(model.thread_id), 2)
		literals = list(filter(lambda x : model.is_true(x), self._literals))
		#head_atoms, body_atoms = self._head_atoms(literals, self._p2t)

		assignment, relations = self._spatial_propagate(literals, self._p2t)

		#print("assignment :", " ".join(["{}={}".format(n, v) for n, v in assignment.items()]))

		#print("Answer: {}".format(model))
		#model.extend(clingo.Function("spatial", [var, value]) for var, value in assignment.items())
		print_msg("=======================================================OnModel================\n", 2)



################################ Transformer(builder, check) ################################



class Transformer:
	
	def __init__(self, builder, check):
		self._builder = builder
		self._state = "guess"
		self._check = check

	def add(self, stm):
		#print(stm)
		if stm.type == clingo.ast.ASTType.Program:
			print('%-10s : %s' % ("directive", stm))
			if stm.name == "check" and not stm.parameters:
				stm.name = "check"
				self._state = "check"
			elif stm.name in ("base", "guess") and not stm.parameters:
				self._state = "guess"
			else:
				raise RuntimeError("unexpected program part")

		else:
			if self._state == "guess":
				#print('%-10s : %s' % ("guess", self.visit(stm)))
				self._builder.add(self.visit(stm))
			else:
				#print('%-10s : %s' % ("check", self.visit(stm)))
				self._check.append(self.visit(stm))

	def visit(self, stm):
		if stm.type == clingo.ast.ASTType.Rule:
			head = stm.head
			body = stm.body
			loc = stm.location
			if head.type == clingo.ast.ASTType.TheoryAtom:
				head = self.visit_TheoryAtom(head, "head")
			for lit in body:
				if lit.atom.type == clingo.ast.ASTType.TheoryAtom:
					lit = self.visit_TheoryAtom(lit.atom, "body")
			stm = clingo.ast.Rule(loc, head, body)
		return stm


	def visit_TheoryAtom(self, atom, loc):
		term = atom.term
		if term.name in theory_atom_names and not term.arguments:
			atom.term = clingo.ast.Function(term.location, term.name, [clingo.ast.Function(term.location, loc, [], False)], False)
		return atom



################################ QSTR(eval, rel) ################################



class QSTR:

	def __init__(self, geoms, rel, assigns):
		self._geoms = geoms
		self._rel = rel
		self._assigns = assigns

	def create_geom(self, r):
		return _create_geom(r)
		#return Polygon.Polygon(repr[0])

	def add_geom(self, obj_id, r):
		geom_id = len(self._geoms) + 1
		self._assigns.setdefault(obj_id, geom_id)
		self._geoms.setdefault(geom_id, self.create_geom(r))
		return geom_id

	def get_geom_(self, id) :
		if id in repr.keys():
			r = repr[id]
			return self.add_geom(id, r)
		else:
			return self._geoms[id]

	def get_geom(self, id) :

		assigns = self._assigns
		#print(assigns)
		if id in assigns.keys():
			geom_id = assigns.get(id)
			return geom_id
		else:
			if id in repr.keys():
				#print("repr")
				r = repr[id]
				return self.add_geom(id, r)
			else:
				raise RuntimeError("geometric data not available")

	def union_(self, shapes):
		if len(shapes) == 0:
			res = "void"
		#print("union")
		res = shapes[0]
		if len(shapes) > 1:
			res += self.union_(shapes[1:])
		return res

	def union(self, l):
		if len(l) == 0:
			return "void"
		shapes_ = [self._geoms.get(elt) for elt in l]
		shapes = [shape for shape in shapes_ if shape != "void"]
		return self.union_(shapes)

	def diff(self, geom_id1, geom_id2):
		shape1 = self._geoms.get(geom_id1)
		shape2 = self._geoms.get(geom_id2)
		if shape1 == "void":
			new_shape = "void"
		elif shape2 == "void":
			new_shape = shape1
		else:
			#print("diff")
			new_shape = shape1 - shape2
		#Polygon.IO.writeSVG("t.svg", (shape1, shape2, new_shape))
		return new_shape

	def buffer(self, geom_id, value):
		shape = self._geoms.get(geom_id)
		if shape == "void":
			new_shape = "void"
		else:
			#print("buffer")
			new_shape = _buffer(shape, value)
		return new_shape

	def intersect_(self, shapes):
		if len(shapes) == 0:
			return "void"
		#print("intersect")
		res = shapes[0]
		if len(shapes) > 1:
			res &= self.intersect_(shapes[1:])
		return res

	def intersect(self, l):
		if len(l) == 0:
			return "void"
		shapes = [self._geoms.get(elt) for elt in l]
		if "void" in shapes:
			return "void"
		else:
			return self.intersect_(shapes)

	def _draw(self, l, s):
		shapes = [self._geoms.get(elt) for elt in l]
		s1, s2, s3 = shapes[0], shapes[1], shapes[2]
		n1, n2, n3 = './pics/' + s + '_f.svg', './pics/' + s + '_h.svg', './pics/' + s + '_m.svg'
		n = './pics/' + s + '.svg'
		if s1 != "void" and s2 != "void" and s3 != "void":
			Polygon.IO.writeSVG(n1, (s1,))
			Polygon.IO.writeSVG(n2, (s2,))
			Polygon.IO.writeSVG(n3, (s3, ))
			Polygon.IO.writeSVG(n, (s3, s1, s2))

	def _in(self, h, heads):
		for head in heads:
			if head in h:
				#print(h)
				return True
		return False

	def _category(self, id):
		for name in spatial_function_names + spatial_artefact_names:
			if id.startswith(name):
				return id
		try:
			return float(id)
		except:
			return '"'+ id + '"'


	def _conv(self, id):
		if id.startswith('"'):
			return id[1:-1]
		else:
			return id

	def _convert_draw(self, id):

		#print(id)
		ids = ast.literal_eval(id)
		ids = [self._category(id) for id in ids]
		ids = [self._conv(id) for id in ids]
		geom_ids = [self.get_geom(id) for id in ids]
		return geom_ids

	def _convert(self, id):

		#print("id", id)
		ids = ast.literal_eval(id)
		ids = [self._category(id) for id in ids]
		#print("ids", ids)
		geom_ids = [self.get_geom(id) for id in ids]
		return geom_ids

	def _convert_buffer(self, id):

		#print(id)
		ids = ast.literal_eval(id)
		ids = [self._category(id) for id in ids]
		geom_id = self.get_geom(ids[0])
		return geom_id, ids[1]

	def _convert_diff(self, id):

		#print(id)
		ids = ast.literal_eval(id)
		ids = [self._category(id) for id in ids]
		geom_ids = [self.get_geom(id) for id in ids]
		return geom_ids

	def _evaluate(self, head_atoms):

		#print("evaluate")
		#print(len(head_atoms))
		if len(head_atoms) == 0:
			return
		heads = [t[3] for t in head_atoms if len(t) > 3]
		head_atoms_ = []
		for h in head_atoms:
			if not self._in(h[2], heads): 

				#print(h)
				if h[0] == "diff":
					#print(h[0], h[2])
					res = h[3]
					if res not in self._assigns.keys():
						geom_ids = self._convert_diff(h[2])
						#print(geom_ids)
						new_id = 'diff(' + ','.join([str(id) for id in geom_ids]) + ')'
						#print(new_id)
						new_shape = self.diff(geom_ids[0], geom_ids[1])
						self._geoms.setdefault(new_id, new_shape)
						self._assigns.setdefault(res, new_id)
						self._geoms.setdefault(res, new_shape)

				if h[0] == "union":
					#print(h[0], h[2])
					res = h[3]
					if res not in self._assigns.keys():
						geom_ids = self._convert(h[2])
						new_id = 'union(' + ','.join([str(id) for id in geom_ids]) + ')'
						new_shape = self.union(geom_ids)
						self._geoms.setdefault(new_id, new_shape)
						self._assigns.setdefault(res, new_id)

				if h[0] == "intersect":
					#print(h[0], h[2])
					res = h[3]
					if res not in self._assigns.keys():
						geom_ids = self._convert(h[2])
						new_id = 'intersect(' + ','.join([str(id) for id in geom_ids]) + ')'
						new_shape = self.intersect(geom_ids)
						self._geoms.setdefault(new_id, new_shape)
						self._assigns.setdefault(res, new_id)

				if h[0] == "buffer":
					#print(h[0], h[2])
					res = h[3]
					if res not in self._assigns.keys():
						geom_id, val = self._convert_buffer(h[2])
						#print(geom_id, val)
						new_id = 'buffer(' + ','.join([geom_id, str(val)]) + ')'
						new_shape = self.buffer(geom_id, val)
						self._geoms.setdefault(new_id, new_shape)
						self._assigns.setdefault(res, new_id)

				if h[0] == "draw":
					#print(h[0], h[2])
					geom_ids = self._convert_draw(h[2])
					shapes = [self._geoms.get(geom_id) for geom_id in geom_ids]
					shapes = [shape for shape in shapes if shape != "void"]
					if len(shapes) > 0:
						file_name = './pics/' + h[2][2:-2] + '.svg'
						Polygon.IO.writeSVG(file_name, shapes)
			else:
				#print(2, h)
				head_atoms_.append(h)
		return self._evaluate(head_atoms_)

	def topology(self, x, y):
		print_msg("Heuristics : TOPOLOGICAL", 1)
		if x < y:
			return "part_of"
		else:
			return "overlaps"

	def _compute(self, body_atoms):
		if len(body_atoms) == 0:
			return
		for b in body_atoms:
			if b[0] in spatial_relation_names:
				r1, r2 = b[2], b[3]
				x, y = self._geoms.get(r1), self._geoms.get(r2)
				if (r1, r2) not in self._rel.keys():
					self._rel.setdefault((r1, r2), self.topology(x, y))
		return 

	def get_assignment(self):
		return self._geoms

	def get_rel(self):
		return self._rel

	def get_repr(self):
		return self._assigns



