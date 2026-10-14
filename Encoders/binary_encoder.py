from Encoders.nqueens_encoder import NQueensEncoder
from math import ceil, log2

from utils import get_amo_pairwise

class BinaryEncoder(NQueensEncoder):
    
    def encode_amo(self, variables: list[int], auxilary_variable: int) -> tuple[list[list[int]], int]:
        clauses = []
        n = len(variables)
        if n <= 1:
            return [], auxilary_variable
        
        if n <= 3:
            return get_amo_pairwise(variables), auxilary_variable
        
        clauses = []
        k = ceil(log2(n))
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