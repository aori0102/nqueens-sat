import multiprocessing
import time
import traceback

import gurobipy as gp
from gurobipy import GRB
from multiprocessing import Queue

from utils import ResultIndex, SolveReport

class GurobiMIP:
    def __init__(self, board_size : int):
        self.board_size = board_size
    
    def solve(self, result_queue : Queue):
        try:
            start_time = time.time()
            n = self.board_size
            self.model = gp.Model(f"nqueens_{n}")
            self.model.Params.OutputFlag = 0
            self.queens = self.model.addVars(n, n, vtype=GRB.BINARY, name="x")   # queens[i, j] = 1 -> queen at (i, j)
            
            # exactly one queen per row
            self.model.addConstrs(gp.quicksum(self.queens[i, j] for j in range(n)) == 1 for i in range(n))
            # at most one queen per column
            self.model.addConstrs(gp.quicksum(self.queens[i, j] for i in range(n)) <= 1 for j in range(n))
            # at most one queen per diagonal (i - j = d)
            for d in range(-(n - 1), n):
                cells = [(i, i - d) for i in range(max(0, d), min(n, n + d))]
                if len(cells) > 1:
                    self.model.addConstr(gp.quicksum(self.queens[i, j] for i, j in cells) <= 1)
            # at most one queen per anti-diagonal (i + j = s)
            for s in range(2 * n - 1):
                cells = [(i, s - i) for i in range(max(0, s - n + 1), min(n, s + 1))]
                if len(cells) > 1:
                    self.model.addConstr(gp.quicksum(self.queens[i, j] for i, j in cells) <= 1)
            
            self.model.optimize()
            result_queue.put(SolveReport(
                method_name="GUROBI_MIP",
                board_size=self.board_size,
                result_index=ResultIndex.SOLVED if self.model.SolCount > 0 else ResultIndex.UNSOLVED,
                clause_build_time=None,
                solve_time=time.time() - start_time,
                num_clauses=None,
                num_variables=None
            ))
        except Exception as e:
            print(f"Error during solving: {e}")
            traceback.print_exc()
            result_queue.put(SolveReport(
                method_name="GUROBI_MIP",
                board_size=self.board_size,
                result_index=ResultIndex.ERROR,
                clause_build_time=0,
                solve_time=0,
                num_clauses=0,
                num_variables=0
            ))

def solve_gurobi_with_timeout(board_sizes, timeout_second: float) -> dict[int, SolveReport]:
    result_queue = multiprocessing.Queue()
    results = {}
    
    for size in board_sizes:
        print(f"Running Gurobi MIP Solver for board size: {size}")
        process = multiprocessing.Process(target=GurobiMIP(size).solve, args=(result_queue,))
        process.start()
        process.join(timeout_second)
        
        if process.is_alive():
            process.terminate()
            process.join()
            result_queue.put(SolveReport(
                method_name="GUROBI_MIP",
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