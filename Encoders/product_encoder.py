from Encoders.nqueens_encoder import NQueensEncoder
from math import isqrt

class ProductEncoder(NQueensEncoder):
    PAIRWISE_CUTOFF = 4  # pairwise is cheaper than product for tiny groups

    def encode_amo(self, variables: list[int], auxilary_variable: int) -> tuple[list[list[int]], int]:
        n = len(variables)
        if n <= 1:
            return [], auxilary_variable
        if n <= self.PAIRWISE_CUTOFF:
            clauses = [[-variables[i], -variables[j]]
                       for i in range(n) for j in range(i + 1, n)]
            return clauses, auxilary_variable

        p = isqrt(n - 1) + 1       # ceil(sqrt(n)) rows
        q = -(-n // p)             # ceil(n / p) cols
        rows = [auxilary_variable + i for i in range(p)]
        cols = [auxilary_variable + p + j for j in range(q)]
        next_var = auxilary_variable + p + q

        clauses = []
        for k, x in enumerate(variables):
            i, j = divmod(k, q)
            clauses.append([-x, rows[i]])   # x -> row flag
            clauses.append([-x, cols[j]])   # x -> col flag

        # AMO over the row flags and col flags, recursively
        row_clauses, next_var = self.encode_amo(rows, next_var)
        col_clauses, next_var = self.encode_amo(cols, next_var)
        clauses += row_clauses + col_clauses

        return clauses, next_var