from Encoders.nqueens_encoder import NQueensEncoder
from utils import get_amo_pairwise

group_size = 4

class CommanderEncoder(NQueensEncoder):
    def encode_amo(self, variables: list[int], auxilary_variable: int) -> tuple[list[list[int]], int]:
        n = len(variables)

        if n <= 1:
            return [], auxilary_variable

        clauses = []
        commanders = []
        nextAuxilaryIndex = auxilary_variable

        for i in range(0, n, group_size):
            group = variables[i : i + group_size]
            m = len(group)

            if m == 1:
                commanders.append(group[0])
                continue

            commander_index = nextAuxilaryIndex
            commanders.append(commander_index)
            nextAuxilaryIndex += 1

            # At most one variable can be true in this group.
            clauses.extend(get_amo_pairwise(group))

            # If any variable is true, the commander must be true.
            for var in group:
                clauses.append([-var, commander_index])

            # If the commander is true, some variable must be true.
            clauses.append([-commander_index] + group)

        commander_clauses, nextAuxilaryIndex = self.encode_amo(
            commanders, nextAuxilaryIndex
        )
        clauses.extend(commander_clauses)

        return clauses, nextAuxilaryIndex
