from Encoders.nqueens_encoder import NQueensEncoder
from math import ceil, log2

class BinaryEncoder(NQueensEncoder):
    
    def encode_amo(self, variables: list[int], auxilary_variable: int) -> tuple[list[list[int]], int]:
        clauses = []
        n = len(variables)
        k = ceil(log2(n))
        if n <= 1:
            return [], auxilary_variable
        
        clauses = []
        auxilaryVariables = [auxilary_variable + i for i in range(k)]
        nextAuxilaryIndex = auxilary_variable + k
        
        for i in range(len(variables)):
            x_i = variables[i]
            
            for bitIndex in range(k):
                y_j = auxilaryVariables[bitIndex]
                isBitSet = (i >> bitIndex) & 1
                
                if isBitSet:    # X_i => y_j
                    clauses.append([-x_i, y_j])
                else:           # X_i => ~y_j
                    clauses.append([-x_i, -y_j])
                    
        return clauses, nextAuxilaryIndex