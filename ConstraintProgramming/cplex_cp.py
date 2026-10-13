import multiprocessing
import time
import traceback

from docplex.cp.model import CpoModel
from multiprocessing import Queue

from utils import ResultIndex, SolveReport

class CPlexCP:
    def __init__(self, board_size : int):
        self.board_size = board_size
    
    def solve(self, result_queue : Queue):
        try:
            start_time = time.time()
            self.model = CpoModel()
            self.queens = [self.model.integer_var(min=0, max=self.board_size - 1, name=f"Q{i}") for i in range(self.board_size)]
            self.model.add(self.model.all_diff(self.queens))
            self.model.add(self.model.all_diff([self.queens[i] + i for i in range(self.board_size)]))
            self.model.add(self.model.all_diff([self.queens[i] - i for i in range(self.board_size)]))
            solution = self.model.solve(LogVerbosity='Quiet')
            result_queue.put(SolveReport(
                method_name="CPLEX_CP",
                board_size=self.board_size,
                result_index=ResultIndex.SOLVED if solution is not None else ResultIndex.UNSOLVED,
                clause_build_time=None,
                solve_time=time.time() - start_time,
                num_clauses=None,
                num_variables=None
            ))
        except Exception as e:
            print(f"Error during solving: {e}")
            traceback.print_exc()
            result_queue.put(SolveReport(
                method_name="CPLEX_CP",
                board_size=self.board_size,
                result_index=ResultIndex.ERROR,
                clause_build_time=0,
                solve_time=0,
                num_clauses=0,
                num_variables=0
            ))

def solve_cplex_cp_with_timeout(board_sizes, timeout_second: float) -> dict[int, SolveReport]:
    result_queue = multiprocessing.Queue()
    results = {}
    
    for size in board_sizes:
        print(f"Running CPLEX CP Solver for board size: {size}")
        process = multiprocessing.Process(target=CPlexCP(size).solve, args=(result_queue,))
        process.start()
        process.join(timeout_second)
        
        if process.is_alive():
            process.terminate()
            process.join()
            result_queue.put(SolveReport(
                method_name="CPLEX_CP",
                board_size=size,
                result_index=ResultIndex.TIMEOUT,
                clause_build_time=0,
                solve_time=0,
                num_clauses=0,
                num_variables=0
            ))
            
    while not result_queue.empty():
        result = result_queue.get()
        results[result.board_size] = result
        
    return results