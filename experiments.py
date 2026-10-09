from pysat.solvers import Solver
from Encoders.binary_encoder import BinaryEncoder
from Encoders.nqueens_encoder import NQueensEncoder
from utils import print_board, validate, SolveReport, ResultIndex
import time
import multiprocessing

board_sizes = [4, 8, 9, 16, 25, 27, 36, 49, 64, 81, 100, 125, 216, 343, 512, 729, 1000, 1331]
solver_name = "cadical153"
timeout_seconds = 20

def solve(encoder_name : str, encoder : NQueensEncoder, result_queue : multiprocessing.Queue):
    try:
        start_time = time.time()
        clauses = encoder.encode()
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
            encoder_name=encoder_name,
            board_size=encoder.board_size,
            result_index=ResultIndex.SAT if is_sat else ResultIndex.UNSAT,
            clause_build_time=clause_build_time,
            solve_time=solve_time,
            num_clauses=number_of_clauses,
            num_variables=number_of_variable
        ))
        
        solver.delete()
    except Exception as e:
        print(f"Error during solving: {e}")
        result_queue.put(SolveReport(
            encoder_name=encoder_name,
            board_size=encoder.board_size,
            result_index=ResultIndex.ERROR,
            clause_build_time=0,
            solve_time=0,
            num_clauses=0,
            num_variables=0
        ))

def solve_with_timeout(encoders, board_sizes, timeout_second: float) -> dict[str, dict[int, SolveReport]]:
    result_queue = multiprocessing.Queue()
    processes = []
    results = {}

    # Create a process for each encoder and board size
    for encoder_name, encoder_class in encoders:
        results[encoder_name] = {}
        for size in board_sizes:
            encoder = encoder_class(size)
            results[encoder_name][size] = None
            p = multiprocessing.Process(target=solve, args=(encoder_name, encoder, result_queue))
            processes.append((p, encoder_name, size))
            p.start()

    start_time = time.time()
    while True:
        elapsed = time.time() - start_time
        all_finished = all(not p.is_alive() for p, _, _ in processes)
        
        if all_finished or elapsed >= timeout_second:
            break
            
        time.sleep(0.1)

    # Clear timeout processes
    for p, encoder_name, size in processes:
        if p.is_alive():
            p.terminate()
            p.join()
            results[encoder_name][size] = SolveReport(
                encoder_name=encoder_name,
                board_size=size,
                result_index=ResultIndex.TIMEOUT,
                clause_build_time=0,
                solve_time=0,
                num_clauses=0,
                num_variables=0
            )

    # Fetch results
    while not result_queue.empty():
        result = result_queue.get()
        results[result.encoder_name][result.board_size] = result

    return results

if __name__ == "__main__":
    Encoders = {
        "Binary": BinaryEncoder
    }
    
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