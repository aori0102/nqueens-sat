from math import isqrt
from Encoders.nqueens_encoder import NQueensEncoder
from utils import get_amo_pairwise

class ProductEncoder(NQueensEncoder):
    PAIRWISE_CUTOFF = 3
    def encode_amo(
        self,
        variables: list[int],
        next_auxiliary_variable: int
    ) -> tuple[list[list[int]], int]:
        n = len(variables)

        if n <= 1:
            return [], next_auxiliary_variable

        if n <= self.PAIRWISE_CUTOFF:
            return (
                get_amo_pairwise(variables),
                next_auxiliary_variable
            )

        # One-level Product Encoding.
        p = isqrt(n - 1) + 1
        q = (n + p - 1) // p

        rows = list(range(
            next_auxiliary_variable,
            next_auxiliary_variable + p
        ))

        cols = list(range(
            next_auxiliary_variable + p,
            next_auxiliary_variable + p + q
        ))

        next_auxiliary_variable += p + q

        # AMO directly on row and column flags.
        clauses = get_amo_pairwise(rows)
        clauses.extend(get_amo_pairwise(cols))

        # Each original variable implies its row and column flags.
        for k, variable in enumerate(variables):
            i, j = divmod(k, q)
            clauses.append([-variable, rows[i]])
            clauses.append([-variable, cols[j]])

        return clauses, next_auxiliary_variable
