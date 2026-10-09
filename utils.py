from enum import Enum, auto

class ResultIndex(Enum):
    SAT = auto()
    UNSAT = auto()
    ERROR = auto()
    TIMEOUT = auto()
    
class ProcessInfo:
    def __init__(self, encoder_name: str, board_size: int, ):
        self.encoder_name = encoder_name
        self.board_size = board_size

class SolveReport:
    def __init__(self,
                 encoder_name: str,
                 board_size: int,
                 result_index: ResultIndex,
                 clause_build_time: float,
                 solve_time : float,
                 num_clauses: int,
                 num_variables: int):
        self.encoder_name = encoder_name
        self.board_size = board_size
        self.result_index = result_index
        self.clause_build_time = clause_build_time
        self.solve_time = solve_time
        self.num_clauses = num_clauses
        self.num_variables = num_variables

    def to_dict(self):
        return {
            "encoder_name": self.encoder_name,
            "board_size": self.board_size,
            "result_index": self.result_index.name,
            "clause_build_time": self.clause_build_time,
            "solve_time": self.solve_time,
            "num_clauses": self.num_clauses,
            "num_variables": self.num_variables
        }

def coord_to_index(board_size : int, row : int, column : int) -> int:
    return row * board_size + column + 1

def index_to_coord(board_size : int, index : int) -> tuple[int, int]:
    return (index - 1) // board_size, (index - 1) % board_size

def print_board(board_size : int, result : list[int]):
    board = [['.' for _ in range(board_size)] for _ in range(board_size)]
    
    for var in result:
        if var > 0 and var <= board_size * board_size:
            row, col = index_to_coord(board_size, var)
            board[row][col] = 'Q'
    
    for row in board:
        print(' '.join(row))
        
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