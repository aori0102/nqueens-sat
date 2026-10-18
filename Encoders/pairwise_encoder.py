from utils import get_amo_pairwise
from Encoders.nqueens_encoder import NQueensEncoder

class PairwiseEncoder(NQueensEncoder):
    def encode_amo(self, variables: list[int], auxilary_variable: int) -> tuple[list[list[int]], int]:
        clauses = get_amo_pairwise(variables)
        return clauses, auxilary_variable