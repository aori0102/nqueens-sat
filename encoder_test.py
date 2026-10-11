from pysat.solvers import Solver
from Encoders.binary_encoder import BinaryEncoder
from Encoders.commander_encoder import CommanderEncoder
from utils import build_nqueens_clauses, validate

encoder = CommanderEncoder()
solver_name = "cadical153"
board_sizes = [4, 8, 9, 16, 25, 27, 36, 49, 64, 81, 100, 125, 216, 343]

if __name__ == "__main__":
    correct_count = 0
    
    for size in board_sizes:
        clauses = build_nqueens_clauses(size, encoder)
        solver = Solver(name=solver_name)
        if solver.solve():
            print(f"Board Size: {size} is SAT")
            model = solver.get_model()
            correct = validate(size, model)
            print(f"Board Size: {size} : {'Correct' if correct else 'Incorrect'}")
            if correct:
                correct_count += 1
        else:
            print(f"Board Size: {size} is UNSAT")
    print(f"Correct solutions: {correct_count}/{len(board_sizes)}")