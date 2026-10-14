from pysat.solvers import Solver
from ConstraintProgramming.cplex_cp import solve_cplex_cp_with_timeout
from Encoders.binary_encoder import BinaryEncoder
from Encoders.commander_encoder import CommanderEncoder
from Encoders.nqueens_encoder import NQueensEncoder
from Encoders.product_encoder import ProductEncoder
from Encoders.sequential_encoder import SequentialEncoder
from utils import build_nqueens_clauses, SolveReport, ResultIndex, export_reports_to_csv, print_board, validate
import time
import multiprocessing
import traceback
import argparse

board_sizes = [4, 8, 9, 16, 25, 27, 36, 49, 64, 81]#, 100, 125, 216, 343, 512, 729, 1000, 1331]
solver_name = "cadical153"
timeout_seconds = 100
Encoders = {
    "Binary": BinaryEncoder,
    "Commander" : CommanderEncoder,
    "Sequential" : SequentialEncoder,
    "Product" : ProductEncoder
}
solve_results = []

def solve(encoder_name : str, encoder : NQueensEncoder, board_size : int, result_queue : multiprocessing.Queue):
    try:
        start_time = time.time()
        clauses = build_nqueens_clauses(board_size, encoder)
        clause_build_time = time.time() - start_time
        
        number_of_variable = 0
        number_of_clauses = len(clauses)
        for clause in clauses:
            for literal in clause:
                number_of_variable = max(number_of_variable, abs(literal))
        
        solver = Solver(name=solver_name, bootstrap_with=clauses)
        start_time = time.time()
        is_sat = solver.solve()
        solve_time = time.time() - start_time
        
        result_queue.put(SolveReport(
            method_name=encoder_name,
            board_size=board_size,
            result_index=ResultIndex.SAT if is_sat else ResultIndex.UNSAT,
            clause_build_time=clause_build_time,
            solve_time=solve_time,
            num_clauses=number_of_clauses,
            num_variables=number_of_variable
        ))
        
        solver.delete()
    except Exception as e:
        print(f"Error during solving: {e}")
        traceback.print_exc()
        result_queue.put(SolveReport(
            method_name=encoder_name,
            board_size=board_size,
            result_index=ResultIndex.ERROR,
            clause_build_time=0,
            solve_time=0,
            num_clauses=0,
            num_variables=0
        ))

def solve_with_timeout(encoders, board_sizes, timeout_second: float) -> dict[str, dict[int, SolveReport]]:
    result_queue = multiprocessing.Queue()
    results = {}

    # Create a process for each encoder and board size
    for encoder_name, encoder_class in encoders:
        for size in board_sizes:
            print(f"Running {encoder_name} Encoder for board size: {size}")
            encoder = encoder_class()
            process = multiprocessing.Process(target=solve, args=(encoder_name, encoder, size, result_queue))
            process.start()
            process.join(timeout_second)
            
            if process.is_alive():
                process.terminate()
                process.join()
                result_queue.put(SolveReport(
                    method_name=encoder_name,
                    board_size=size,
                    result_index=ResultIndex.TIMEOUT,
                    clause_build_time=0,
                    solve_time=0,
                    num_clauses=0,
                    num_variables=0
                ))

    while not result_queue.empty():
        result = result_queue.get()
        if result.method_name not in results:
            results[result.method_name] = {}
        results[result.method_name][result.board_size] = result
    
    return results

def run_sat_solvers():
    print("Running SAT Solvers...")
    
    results = solve_with_timeout(Encoders.items(), board_sizes, timeout_seconds)
    for encoder_name, encoder_results in results.items():
        print("*" * 70)
        print(f"Results for {encoder_name} Encoder:")
        for board_size, report in encoder_results.items():
            print(f">>> Size: {board_size}")
            print(f"Result: {report.result_index.name}")
            if report.result_index is not ResultIndex.TIMEOUT and report.result_index is not ResultIndex.ERROR:
                print(f"Clause Build Time: {report.clause_build_time:.6f}s")
                print(f"Num Variables: {report.num_variables}")
                print(f"Num Clauses: {report.num_clauses}")
                print(f"Solve Time: {report.solve_time:.6f}s")
                print(f"Total Time: {report.solve_time + report.clause_build_time:.6f}s")
                
            solve_results.append(report)
                
def run_cplex_cp_solver():
    print("Running CPLEX CP Solver...")
    
    results = solve_cplex_cp_with_timeout(board_sizes, timeout_seconds)
    print("*" * 70)
    print(f"Results for CPLEX CP Solver:")
    for board_size, report in results.items():
        print(f">>> Size: {board_size}")
        print(f"Result: {report.result_index.name}")
        if report.result_index is not ResultIndex.TIMEOUT and report.result_index is not ResultIndex.ERROR:
            print(f"Solve Time: {report.solve_time:.6f}s")
            
        solve_results.append(report)

if __name__ == "__main__":
    run_sat_solvers()
    run_cplex_cp_solver()
    
    export_reports_to_csv(solve_results)