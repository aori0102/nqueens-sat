from Encoders.nqueens_encoder import NQueensEncoder

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
            
            # No two variables in the group can be true at the same time
            for a in range(m):
                for b in range(a + 1, m):
                    clauses.append([-group[a], -group[b]])
                    
            # If any variable in the group is true, then the commander must be true
            for var in group:
                clauses.append([-var, commander_index])

        # At most one commander can be true across all groups.
        commander_clauses, nextAuxilaryIndex = self.encode_amo(
            commanders, nextAuxilaryIndex
        )
        clauses.extend(commander_clauses)

        return clauses, nextAuxilaryIndex