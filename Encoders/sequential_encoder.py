from Encoders.nqueens_encoder import NQueensEncoder

class SequentialEncoder(NQueensEncoder):
    
    def encode_amo(self, variables: list[int], auxilary_variable: int) -> tuple[list[list[int]], int]:
        n = len(variables)
        if n <= 1:
            return [], auxilary_variable

        auxilary_variables = [auxilary_variable + i for i in range(n - 1)]        
        clauses = []
        for i in range(n - 1):
            clauses.extend([
                [-variables[i], auxilary_variables[i]] if n == 0 else [], # Set
                [-auxilary_variables[i], variables[i + 1]], # Carry
                [-auxilary_variables[i], auxilary_variables[i + 1]] if i < n - 2 else [] # Trip
            ])
        
        return clauses, auxilary_variable