
import multiprocessing
import time
import traceback
from queue import Empty

from docplex.mp.model import Model
from multiprocessing import Queue

from utils import ResultIndex, SolveReport


class CPlexMIP:
    def __init__(self, board_size: int):
        self.board_size = board_size

    def solve(self, result_queue: Queue):
        start_time = time.perf_counter()

        try:
            n = self.board_size
            self.model = Model(name=f"nqueens_{n}")

            # x[r, c] = 1 if a queen is placed at (r, c)
            self.queens = self.model.binary_var_matrix(
                keys1=range(n),
                keys2=range(n),
                name="x"
            )

            # Exactly one queen per row and per column
            for i in range(n):
                self.model.add_constraint(
                    self.model.sum(self.queens[i, c] for c in range(n)) == 1
                )
                self.model.add_constraint(
                    self.model.sum(self.queens[r, i] for r in range(n)) == 1
                )

            # At most one queen per diagonal (r - c = k)
            for k in range(-n + 1, n):
                diagonal = [
                    self.queens[r, r - k]
                    for r in range(n)
                    if 0 <= r - k < n
                ]

                if len(diagonal) > 1:
                    self.model.add_constraint(
                        self.model.sum(diagonal) <= 1
                    )

            # At most one queen per anti-diagonal (r + c = k)
            for k in range(2 * n - 1):
                anti_diagonal = [
                    self.queens[r, k - r]
                    for r in range(n)
                    if 0 <= k - r < n
                ]

                if len(anti_diagonal) > 1:
                    self.model.add_constraint(
                        self.model.sum(anti_diagonal) <= 1
                    )

            # Solve the MIP
            solution = self.model.solve()

            result_queue.put(
                SolveReport(
                    method_name="CPLEX_MIP",
                    board_size=n,
                    result_index=(
                        ResultIndex.SOLVED
                        if solution is not None
                        else ResultIndex.UNSOLVED
                    ),
                    clause_build_time=None,
                    solve_time=time.perf_counter() - start_time,
                    num_clauses=None,
                    num_variables=None
                )
            )

        except Exception:
            print(
                f"Error during CPLEX MIP for n={self.board_size}:",
                flush=True
            )
            traceback.print_exc()

            result_queue.put(
                SolveReport(
                    method_name="CPLEX_MIP",
                    board_size=self.board_size,
                    result_index=ResultIndex.ERROR,
                    clause_build_time=None,
                    solve_time=time.perf_counter() - start_time,
                    num_clauses=None,
                    num_variables=None
                )
            )


def solve_cplex_mip_with_timeout(
    board_sizes,
    timeout_second: float
) -> dict[int, SolveReport]:

    results = {}

    for size in board_sizes:
        print(f"Running CPLEX MIP Solver for board size: {size}")

        # Use a separate queue for each process
        result_queue = multiprocessing.Queue()

        process = multiprocessing.Process(
            target=CPlexMIP(size).solve,
            args=(result_queue,)
        )

        process.start()
        process.join(timeout_second)

        if process.is_alive():
            process.terminate()
            process.join()

            results[size] = SolveReport(
                method_name="CPLEX_MIP",
                board_size=size,
                result_index=ResultIndex.TIMEOUT,
                clause_build_time=None,
                solve_time=timeout_second,
                num_clauses=None,
                num_variables=None
            )

        else:
            try:
                result = result_queue.get(timeout=2.0)
                results[size] = result

            except Empty:
                # The worker exited without returning a report
                results[size] = SolveReport(
                    method_name="CPLEX_MIP",
                    board_size=size,
                    result_index=ResultIndex.ERROR,
                    clause_build_time=None,
                    solve_time=0,
                    num_clauses=None,
                    num_variables=None
                )

        result_queue.close()
        result_queue.join_thread()

    return results
