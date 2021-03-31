%% clingo 0 spatial.lp union.lp



#script (python)

import sys
import clingo
import dl


class Application:

	program_name = "guess and check"
	version = "1.0"
 
	def __init__(self):
		self.detail_level = 0

	def _read(self, path):

		if path == "-":
			return sys.stdin.read()
		with open(path) as file_:
			return file_.read()

	def main(self, prg, files):

		if not files:
			files = ["-"]

		files = ['safety.lp', 'data.lp', 'timestep.lp']

		dl.PRINT_DETAIL_LEVEL = self.detail_level

		prg.configuration.solve.models = 0

		check = []
		print("\n&&&&&&&&&&& PARSING &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&")
		with prg.builder() as builder:
			trans = dl.Transformer(builder, check)
			for path in files:
				clingo.parse_program(self._read(path), trans.add)
		print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&& PARSING &&&&&&&&&&&\n")

		p = dl.GACPropagator(check)
		prg.register_propagator(p)
		prg.add("base", [], dl.THEORY)

		#prg.ground([("base", [])], context = self)

		prg.ground([("base", [])])
		prg.solve(on_model=p.on_model)


clingo.clingo_main(Application(), sys.argv[1:]) 

#end.

