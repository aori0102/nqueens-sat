from Encoders.nqueens_encoder import NQueensEncoder
from math import ceil, log2
from utils import coord_to_index

class BinaryEncoder(NQueensEncoder):
    
    def generateAmo(self, variables : list[int],k : int, startAuxilaryIndex : int) -> list[list[int]]:
        n = len(variables)
        if n <= 1:
            return [], startAuxilaryIndex
        
        clauses = []
        auxilaryVariables = [startAuxilaryIndex + i for i in range(k)]
        nextAuxilaryIndex = startAuxilaryIndex + k
        
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
            
    
    def encode(self) -> list[list[int]]:
        clauses = []
        auxilary_index = self.board_size * self.board_size + 1
        k = ceil(log2(self.board_size))
        
        # ALO + AMO for each row
        for row in range(self.board_size):
            variables = [coord_to_index(self.board_size, row, col) for col in range(self.board_size)]
            amo_clauses, auxilary_index = self.generateAmo(variables, k, auxilary_index)
            clauses.append(variables)  # ALO clause
            clauses.extend(amo_clauses)
            
        # AMO for each column
        for col in range(self.board_size):
            variables = [coord_to_index(self.board_size, row, col) for row in range(self.board_size)]
            amo_clauses, auxilary_index = self.generateAmo(variables, k, auxilary_index)
            clauses.extend(amo_clauses)
            
        # AMO for each main diagonal
        for d in range(-(self.board_size - 1), self.board_size):
            main_diag_vars = [coord_to_index(self.board_size, row, col) for row in range(self.board_size) for col in range(self.board_size) if row - col == d]
            
            if len(main_diag_vars) > 1:
                amo_clauses, auxilary_index = self.generateAmo(main_diag_vars, k, auxilary_index)
                
            clauses.extend(amo_clauses)
            
        # AMO for each anti diagonal
        for d in range(1, 2 * self.board_size - 2):
            anti_diag_vars = [coord_to_index(self.board_size, row, col) for row in range(self.board_size) for col in range(self.board_size) if row + col == d]
            
            if len(anti_diag_vars) > 1:
                amo_clauses, auxilary_index = self.generateAmo(anti_diag_vars, k, auxilary_index)
                
            clauses.extend(amo_clauses)

        return clauses