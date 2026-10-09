from abc import ABC, abstractmethod

class NQueensEncoder(ABC):
    def __init__(self, board_size : int):
        self.board_size = board_size
    
    @abstractmethod
    def encode(self) -> list[list[int]]:
        pass