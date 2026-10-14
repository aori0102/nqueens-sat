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


import os
import time
import tempfile
import multiprocessing
import traceback
from pysat.solvers import Solver
from Encoders.nqueens_encoder import NQueensEncoder
from utils import (
    build_nqueens_clauses,
    SolveReport,
    ResultIndex,
)

SOLVER_NAME = "cadical153"

def write_dimacs(clauses, path):
    """Write a CNF clause list to DIMACS format."""
    num_clauses = len(clauses)
    num_variables = max(
        (abs(lit) for clause in clauses for lit in clause),
        default=0,
    )

    with open(path, "w", encoding="ascii") as file:
        file.write(f"p cnf {num_variables} {num_clauses}\n")

        for clause in clauses:
            file.write(" ".join(map(str, clause)))
            file.write(" 0\n")

    return num_variables, num_clauses

def iter_dimacs_clauses(path):
    """Yield clauses one at a time, without loading the whole CNF."""
    with open(path, "r", encoding="ascii") as file:
        for line in file:
            line = line.strip()

            if not line or line.startswith(("c", "p")):
                continue

            literals = [int(token) for token in line.split()]
            if literals and literals[-1] == 0:
                literals.pop()

            yield literals

def build_cnf_worker(
    board_size: int,
    encoder_class: type[NQueensEncoder],
    cnf_path: str,
    result_sender,
):
    """Build clauses and save them to a file in an isolated process."""
    try:
        encoder = encoder_class()

        start = time.perf_counter()
        clauses = build_nqueens_clauses(board_size, encoder)
        build_time = time.perf_counter() - start

        num_variables, num_clauses = write_dimacs(clauses, cnf_path)

        result_sender.send({
            "ok": True,
            "build_time": build_time,
            "num_variables": num_variables,
            "num_clauses": num_clauses,
        })

    except Exception:
        try:
            result_sender.send({
                "ok": False,
                "error": traceback.format_exc(),
            })
        except (BrokenPipeError, EOFError, OSError):
            pass
    finally:
        result_sender.close()

def solve_cnf_worker(
    cnf_path: str,
    solver_name: str,
    result_sender,
):
    """Load the CNF from disk and solve it in an isolated process."""
    solver = None

    try:
        # Loading the CNF is included in the process-level timeout.
        solver = Solver(
            name=solver_name,
            bootstrap_with=iter_dimacs_clauses(cnf_path),
        )

        start = time.perf_counter()
        is_sat = solver.solve()
        solve_time = time.perf_counter() - start

        result_sender.send({
            "ok": True,
            "is_sat": is_sat,
            "solve_time": solve_time,
        })

    except Exception:
        try:
            result_sender.send({
                "ok": False,
                "error": traceback.format_exc(),
            })
        except (BrokenPipeError, EOFError, OSError):
            pass
    finally:
        if solver is not None:
            solver.delete()
        result_sender.close()

def run_isolated_stage(target, args, timeout_seconds):
    """
    Run one stage with its own process and timeout.
    Returns (status, payload).
    """
    receiver, sender = multiprocessing.Pipe(duplex=False)

    process = multiprocessing.Process(
        target=target,
        args=(*args, sender),
    )

    start = time.perf_counter()
    process.start()
    sender.close()

    process.join(timeout_seconds)
    elapsed = time.perf_counter() - start

    if process.is_alive():
        process.terminate()
        process.join()

        # Escalate if the OS has not stopped the process.
        if process.is_alive():
            process.kill()
            process.join()

        receiver.close()
        return "TIMEOUT", {"elapsed": elapsed}

    if receiver.poll(2):
        try:
            payload = receiver.recv()
        except EOFError:
            payload = None
    else:
        payload = None

    receiver.close()

    if payload is None:
        return "ERROR", {
            "error": f"Worker exited with code {process.exitcode} without a result."
        }

    if not payload.get("ok"):
        return "ERROR", payload

    return "OK", payload

def solve_with_timeout(
    encoders,
    board_sizes,
    build_timeout_seconds: float,
    solve_timeout_seconds: float,
):
    results = {}

    for encoder_name, encoder_class in encoders.items():
        results[encoder_name] = {}

        for size in board_sizes:
            print(f"Running {encoder_name} for board size {size}")

            # Each benchmark gets its own temporary CNF file.
            fd, cnf_path = tempfile.mkstemp(suffix=".cnf")
            os.close(fd)

            build_time = 0.0
            solve_time = 0.0
            num_variables = 0
            num_clauses = 0

            try:
                # Stage A: build timeout is independent of solve timeout.
                status, build_result = run_isolated_stage(
                    build_cnf_worker,
                    (size, encoder_class, cnf_path),
                    build_timeout_seconds,
                )

                if status == "TIMEOUT":
                    print(f"Build timeout: {encoder_name}, N={size}")
                    report = SolveReport(
                        method_name=encoder_name,
                        board_size=size,
                        result_index=ResultIndex.TIMEOUT,
                        clause_build_time=build_result["elapsed"],
                        solve_time=0,
                        num_clauses=0,
                        num_variables=0,
                    )

                elif status == "ERROR":
                    print(build_result.get("error", "Unknown build error"))
                    report = SolveReport(
                        method_name=encoder_name,
                        board_size=size,
                        result_index=ResultIndex.ERROR,
                        clause_build_time=0,
                        solve_time=0,
                        num_clauses=0,
                        num_variables=0,
                    )

                else:
                    build_time = build_result["build_time"]
                    num_variables = build_result["num_variables"]
                    num_clauses = build_result["num_clauses"]

                    # Stage B: timeout starts only after build has finished.
                    status, solve_result = run_isolated_stage(
                        solve_cnf_worker,
                        (cnf_path, SOLVER_NAME),
                        solve_timeout_seconds,
                    )

                    if status == "TIMEOUT":
                        print(f"Solve timeout: {encoder_name}, N={size}")
                        report = SolveReport(
                            method_name=encoder_name,
                            board_size=size,
                            result_index=ResultIndex.TIMEOUT,
                            clause_build_time=build_time,
                            solve_time=solve_result["elapsed"],
                            num_clauses=num_clauses,
                            num_variables=num_variables,
                        )

                    elif status == "ERROR":
                        print(solve_result.get("error", "Unknown solve error"))
                        report = SolveReport(
                            method_name=encoder_name,
                            board_size=size,
                            result_index=ResultIndex.ERROR,
                            clause_build_time=build_time,
                            solve_time=0,
                            num_clauses=num_clauses,
                            num_variables=num_variables,
                        )

                    else:
                        solve_time = solve_result["solve_time"]
                        result_index = (
                            ResultIndex.SAT
                            if solve_result["is_sat"]
                            else ResultIndex.UNSAT
                        )

                        report = SolveReport(
                            method_name=encoder_name,
                            board_size=size,
                            result_index=result_index,
                            clause_build_time=build_time,
                            solve_time=solve_time,
                            num_clauses=num_clauses,
                            num_variables=num_variables,
                        )

                results[encoder_name][size] = report

                print(
                    f"Result: {report.result_index.name} | "
                    f"Build: {report.clause_build_time:.2f}s | "
                    f"Solve: {report.solve_time:.2f}s | "
                    f"Clauses: {report.num_clauses}"
                )

            finally:
                try:
                    os.remove(cnf_path)
                except FileNotFoundError:
                    pass

    return results

def run_sat_solvers():
    print("Running SAT Solvers...")
    
    results = solve_with_timeout(Encoders, board_sizes, timeout_seconds, timeout_seconds)
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