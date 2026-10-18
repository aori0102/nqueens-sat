from enum import Enum, auto
from Encoders.nqueens_encoder import NQueensEncoder

class ResultIndex(Enum):
    SAT = auto()
    UNSAT = auto()
    ERROR = auto()
    TIMEOUT = auto()
    SOLVED = auto()
    UNSOLVED = auto()
    
class ProcessInfo:
    def __init__(self, encoder_name: str, board_size: int, ):
        self.encoder_name = encoder_name
        self.board_size = board_size

class SolveReport:
    def __init__(self,
                 method_name: str,
                 board_size: int,
                 result_index: ResultIndex,
                 clause_build_time: float,
                 solve_time : float,
                 num_clauses: int,
                 num_variables: int):
        self.method_name = method_name if method_name is not None else "Unknown"
        self.board_size = board_size if board_size is not None else 0
        self.result_index = result_index if result_index is not None else ResultIndex.ERROR
        self.clause_build_time = clause_build_time if clause_build_time is not None else 0
        self.solve_time = solve_time if solve_time is not None else 0
        self.num_clauses = num_clauses if num_clauses is not None else 0
        self.num_variables = num_variables if num_variables is not None else 0

    def to_dict(self):
        return {
            "Method Name": self.method_name,
            "Board Size": self.board_size,
            "Result": self.result_index.name,
            "Clause Build Time": self.clause_build_time,
            "Solve Time": self.solve_time,
            "Num Clauses": self.num_clauses,
            "Num Variables": self.num_variables,
            "Total Time": self.clause_build_time + self.solve_time
        }

def coord_to_index(board_size : int, row : int, column : int) -> int:
    return row * board_size + column + 1

def index_to_coord(board_size : int, index : int) -> tuple[int, int]:
    return (index - 1) // board_size, (index - 1) % board_size

def get_amo_pairwise(variables: list[int]) -> list[list[int]]:
    clauses = []
    n = len(variables)
    for i in range(n):
        for j in range(i + 1, n):
            clauses.append([-variables[i], -variables[j]])
    return clauses

def print_board(board_size : int, result : list[int]):
    board = [['.' for _ in range(board_size)] for _ in range(board_size)]
    
    for var in result:
        if var > 0 and var <= board_size * board_size:
            row, col = index_to_coord(board_size, var)
            board[row][col] = 'Q'
    
    for row in board:
        print(' '.join(row))
        
def build_nqueens_clauses(board_size : int, encoder : NQueensEncoder) -> list[list[int]]:
    clauses = []
    auxilary_variable = board_size * board_size + 1
    for row in range(board_size):
        # ALO for each row
        variables = [coord_to_index(board_size, row, col) for col in range(board_size)]
        clauses.append(variables)
        
        # AMO for each row
        amo_clauses, auxilary_variable = encoder.encode_amo(variables, auxilary_variable)
        clauses.extend(amo_clauses)
        
    for col in range(board_size):
        # ALO for each column
        variables = [coord_to_index(board_size, row, col) for row in range(board_size)]
        clauses.append(variables)
        
        # AMO for each column
        amo_clauses, auxilary_variable = encoder.encode_amo(variables, auxilary_variable)
        clauses.extend(amo_clauses)
        
    for d in range(-(board_size - 1), board_size):
        # AMO for each main diagonal
        variables = [coord_to_index(board_size, row, row - d) for row in range(board_size) if 0 <= row - d < board_size]
        if len(variables) > 1:
            amo_clauses, auxilary_variable = encoder.encode_amo(variables, auxilary_variable)
            clauses.extend(amo_clauses)

    for d in range(2 * board_size - 1):
        # AMO for each anti-diagonal
        variables = [coord_to_index(board_size, row, d - row) for row in range(board_size) if 0 <= d - row < board_size]
        if len(variables) > 1:
            amo_clauses, auxilary_variable = encoder.encode_amo(variables, auxilary_variable)
            clauses.extend(amo_clauses)

    return clauses

def validate(board_size : int, result : list[int]) -> bool:
    queens = []
    
    board_size_sqr = board_size * board_size
    for var in result:
        if var > 0 and var <= board_size_sqr:
            row, col = index_to_coord(board_size, var)
            queens.append((row, col))
    
    for i in range(len(queens)):
        for j in range(i + 1, len(queens)):
            r1, c1 = queens[i]
            r2, c2 = queens[j]
            
            if r1 == r2 or c1 == c2 or abs(r1 - r2) == abs(c1 - c2):
                return False
    
    return True