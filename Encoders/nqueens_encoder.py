from abc import ABC, abstractmethod

class NQueensEncoder(ABC):
    @abstractmethod
    def encode_amo(self, variables: list[int], auxilary_variable : int) -> tuple[list[list[int]], int]:
        pass