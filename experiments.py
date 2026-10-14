from pysat.solvers import Solver
from ConstraintProgramming.cp_sat import solve_cpsat_with_timeout
from ConstraintProgramming.cplex_cp import solve_cplex_cp_with_timeout
from Encoders.binary_encoder import BinaryEncoder
from Encoders.commander_encoder import CommanderEncoder
from Encoders.nqueens_encoder import NQueensEncoder
from Encoders.product_encoder import ProductEncoder
from Encoders.sequential_encoder import SequentialEncoder
from IntegerLinearProgramming.cplex_mip import solve_cplex_mip_with_timeout
from IntegerLinearProgramming.gurobi_mip import solve_gurobi_with_timeout
from utils import build_nqueens_clauses, SolveReport, ResultIndex, combine_csv_reports, export_reports_to_csv, print_board, validate
import time
import multiprocessing
import traceback
import argparse

board_sizes = [4, 8, 9, 16, 25, 27, 36, 49, 64, 81, 100, 125, 216, 343, 512, 729, 1000, 1331]
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
        
def run_cplex_mip_solver():
    print("Running CPLEX MIP Solver...")
    
    results = solve_cplex_mip_with_timeout(board_sizes, timeout_seconds)
    print("*" * 70)
    print(f"Results for CPLEX MIP Solver:")
    for board_size, report in results.items():
        print(f">>> Size: {board_size}")
        print(f"Result: {report.result_index.name}")
        if report.result_index is not ResultIndex.TIMEOUT and report.result_index is not ResultIndex.ERROR:
            print(f"Solve Time: {report.solve_time:.6f}s")
            
        solve_results.append(report)
        
def run_cpsat_solver():
    print("Running CP-SAT Solver...")
    
    results = solve_cpsat_with_timeout(board_sizes, timeout_seconds)
    print("*" * 70)
    print(f"Results for CP-SAT Solver:")
    for board_size, report in results.items():
        print(f">>> Size: {board_size}")
        print(f"Result: {report.result_index.name}")
        if report.result_index is not ResultIndex.TIMEOUT and report.result_index is not ResultIndex.ERROR:
            print(f"Solve Time: {report.solve_time:.6f}s")
            
        solve_results.append(report)
        
def run_gurobi_mip_solver():
    print("Running Gurobi MIP Solver...")
    
    results = solve_gurobi_with_timeout(board_sizes, timeout_seconds)
    print("*" * 70)
    print(f"Results for Gurobi MIP Solver:")
    for board_size, report in results.items():
        print(f">>> Size: {board_size}")
        print(f"Result: {report.result_index.name}")
        if report.result_index is not ResultIndex.TIMEOUT and report.result_index is not ResultIndex.ERROR:
            print(f"Solve Time: {report.solve_time:.6f}s")
            
        solve_results.append(report)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run N-Queens Solvers")
    parser.add_argument("--sat-binary", action="store_true", help="Run SAT solver with Binary encoding")
    parser.add_argument("--sat-commander", action="store_true", help="Run SAT solver with Commander encoding")
    parser.add_argument("--sat-sequential", action="store_true", help="Run SAT solver with Sequential encoding")
    parser.add_argument("--sat-product", action="store_true", help="Run SAT solver with Product encoding")
    parser.add_argument("--cplex-cp", action="store_true", help="Run CPLEX CP solver")
    parser.add_argument("--cplex-mip", action="store_true", help="Run CPLEX MIP solver")
    parser.add_argument("--cpsat", action="store_true", help="Run CP-SAT solver")
    parser.add_argument("--gurobi-mip", action="store_true", help="Run Gurobi MIP solver")
    parser.add_argument("--combine-reports", action="store_true", help="Combine all reports into a single CSV file")

    args = parser.parse_args()
    benchmark_file = "benchmark_results.csv"
    
    if args.combine_reports:
        combine_csv_reports([
            "benchmark_results_binary.csv",
            "benchmark_results_commander.csv",
            "benchmark_results_sequential.csv",
            "benchmark_results_product.csv",
            "benchmark_results_cplex_cp.csv",
            "benchmark_results_cplex_mip.csv",
            "benchmark_results_cpsat.csv",
            "benchmark_results_gurobi_mip.csv"
        ], "benchmark_results_combined.csv")
        exit(0)
    
    if args.sat_binary:
        Encoders = {"Binary": BinaryEncoder}
        benchmark_file = "benchmark_results_binary.csv"
        run_sat_solvers()
    elif args.sat_commander:
        Encoders = {"Commander": CommanderEncoder}
        benchmark_file = "benchmark_results_commander.csv"
        run_sat_solvers()
    elif args.sat_sequential:
        Encoders = {"Sequential": SequentialEncoder}
        benchmark_file = "benchmark_results_sequential.csv"
        run_sat_solvers()
    elif args.sat_product:
        Encoders = {"Product": ProductEncoder}
        benchmark_file = "benchmark_results_product.csv"
        run_sat_solvers()
    elif args.cplex_cp:
        benchmark_file = "benchmark_results_cplex_cp.csv"
        run_cplex_cp_solver()
    elif args.cplex_mip:
        benchmark_file = "benchmark_results_cplex_mip.csv"
        run_cplex_mip_solver()
    elif args.cpsat:
        benchmark_file = "benchmark_results_cpsat.csv"
        run_cpsat_solver()
    elif args.gurobi_mip:
        benchmark_file = "benchmark_results_gurobi_mip.csv"
        run_gurobi_mip_solver()
    
    export_reports_to_csv(solve_results, benchmark_file)