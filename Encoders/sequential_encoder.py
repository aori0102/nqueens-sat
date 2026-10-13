from Encoders.nqueens_encoder import NQueensEncoder

class SequentialEncoder(NQueensEncoder):
    
    def encode_amo(self, variables, auxilary_variable):
        n = len(variables)
        if n <= 1:
            return [], auxilary_variable
    
        s = [auxilary_variable + i for i in range(n - 1)]
        clauses = []
        for i in range(n - 1):
            clauses.append([-variables[i], s[i]])            # set
            clauses.append([-s[i], -variables[i + 1]])       # trip
            if i < n - 2:
                clauses.append([-s[i], s[i + 1]])            # carry
    
        return clauses, auxilary_variable + n - 1