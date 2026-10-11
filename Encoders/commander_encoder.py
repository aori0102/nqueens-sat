from Encoders.nqueens_encoder import NQueensEncoder
from utils import coord_to_index

group_size = 4

class CommanderEncoder(NQueensEncoder):
    def generateAmo(self, variables : list[int], startAuxilaryIndex : int) -> tuple[list[list[int]], int]:
        n = len(variables)
        if n <= 1:
            return [], startAuxilaryIndex
        
        clauses = []
        commanders = []
        nextAuxilaryIndex = startAuxilaryIndex
        
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
                
        return clauses, nextAuxilaryIndex
    
    def encode(self) -> list[list[int]]:
        clauses = []
        auxilary_index = self.board_size * self.board_size + 1
        
        for row in range(self.board_size):
            variables = [coord_to_index(self.board_size, row, col) for col in range(self.board_size)]
            
            # ALO for each row
            clauses.append(variables)
            
            # AMO for each row
            row_amo_clauses, auxilary_index = self.generateAmo(variables, auxilary_index)
            clauses.extend(row_amo_clauses)
            
        for col in range(self.board_size):
            variables = [coord_to_index(self.board_size, row, col) for row in range(self.board_size)]
            
            # AMO for each column
            col_amo_clauses, auxilary_index = self.generateAmo(variables, auxilary_index)
            clauses.extend(col_amo_clauses)
            
        for d in range(-(self.board_size - 1), self.board_size):
            main_diag_vars = [coord_to_index(self.board_size, row, col) for row in range(self.board_size) for col in range(self.board_size) if row - col == d]
            
            if len(main_diag_vars) > 1:
                main_diag_amo_clauses, auxilary_index = self.generateAmo(main_diag_vars, auxilary_index)
                clauses.extend(main_diag_amo_clauses)
                
        for d in range(1, 2 * self.board_size - 2):
            anti_diag_vars = [coord_to_index(self.board_size, row, col) for row in range(self.board_size) for col in range(self.board_size) if row + col == d]
            
            if len(anti_diag_vars) > 1:
                anti_diag_amo_clauses, auxilary_index = self.generateAmo(anti_diag_vars, auxilary_index)
                clauses.extend(anti_diag_amo_clauses)
                
        return clauses