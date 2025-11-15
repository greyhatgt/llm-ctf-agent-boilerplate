import random
from itertools import combinations, product
from z3 import *
import time

def generate_unique_sat(num_vars, max_clauses):
    """
    Generate a SAT problem in CNF form with exactly one solution.
    Uses a systematic approach to guarantee uniqueness.
    
    Args:
        num_vars (int): Number of boolean variables
        max_clauses (int): Maximum number of clauses to generate
        
    Returns:
        tuple: (solution, clauses)
    """
    # Generate a random solution
    solution = [random.choice([True, False]) for _ in range(num_vars)]
    clauses = []
    
    # Step 1: Add unit clauses for each variable to force our solution
    for i, val in enumerate(solution):
        clauses.append([i + 1 if val else -(i + 1)])
        
    # Calculate how many additional clauses we can add
    remaining_clauses = max_clauses - num_vars
    if remaining_clauses > 0:
        # Step 2: Add some random redundant clauses to make it more interesting
        # but ensure they don't allow additional solutions
        num_extra = random.randint(min(num_vars // 2, remaining_clauses), 
                                 min(remaining_clauses, num_vars * 2))
        
        for _ in range(num_extra):
            # Pick 2-3 variables randomly
            clause_size = random.randint(2, 3)
            vars_in_clause = random.sample(range(num_vars), clause_size)
            
            clause = []
            # For each variable, add it to the clause with the correct polarity
            # to make the clause true under our solution
            for var in vars_in_clause:
                if solution[var]:
                    clause.append(var + 1)
                else:
                    clause.append(-(var + 1))
                    
            clauses.append(clause)
    
    # Shuffle the clauses to hide the unit clauses
    random.shuffle(clauses)
    
    return solution, clauses

def verify_solution(solution, clauses):
    """
    Verify if a solution satisfies all clauses.
    """
    for clause in clauses:
        clause_satisfied = False
        for literal in clause:
            var_idx = abs(literal) - 1
            var_val = solution[var_idx]
            if literal < 0:
                var_val = not var_val
            if var_val:
                clause_satisfied = True
                break
        if not clause_satisfied:
            return False
    return True

def solve_sat_one(clauses, num_vars):
    """
    Find one solution to the SAT problem using Z3.
    
    Args:
        clauses (list): List of clauses where each clause is a list of integers
        num_vars (int): Number of variables in the problem
        
    Returns:
        tuple: (is_satisfiable, solution, solve_time)
            - is_satisfiable (bool): Whether a solution was found
            - solution (list): List of boolean values or None if unsatisfiable
            - solve_time (float): Time taken to solve in seconds
    """
    # Create Z3 solver
    solver = Solver()
    
    # Create boolean variables
    vars = [Bool(f"x_{i}") for i in range(num_vars)]
    
    # Add clauses to solver
    for clause in clauses:
        z3_clause = []
        for literal in clause:
            var_idx = abs(literal) - 1
            if literal > 0:
                z3_clause.append(vars[var_idx])
            else:
                z3_clause.append(Not(vars[var_idx]))
        solver.add(Or(z3_clause))
    
    # Solve and measure time
    start_time = time.time()
    is_sat = solver.check() == sat
    solve_time = time.time() - start_time
    
    if is_sat:
        model = solver.model()
        solution = [bool(model.evaluate(var)) for var in vars]
        return True, solution, solve_time
    else:
        return False, None, solve_time

def solve_sat_all(clauses, num_vars):
    """
    Find all solutions to the SAT problem using Z3.
    
    Args:
        clauses (list): List of clauses where each clause is a list of integers
        num_vars (int): Number of variables in the problem
        
    Returns:
        tuple: (solutions, solve_time)
            - solutions (list): List of all solutions, where each solution is a list of boolean values
            - solve_time (float): Total time taken to find all solutions
    """
    # Create Z3 solver
    solver = Solver()
    
    # Create boolean variables
    vars = [Bool(f"x_{i}") for i in range(num_vars)]
    
    # Add clauses to solver
    for clause in clauses:
        z3_clause = []
        for literal in clause:
            var_idx = abs(literal) - 1
            if literal > 0:
                z3_clause.append(vars[var_idx])
            else:
                z3_clause.append(Not(vars[var_idx]))
        solver.add(Or(z3_clause))
    
    # Find all solutions
    solutions = []
    start_time = time.time()
    
    while solver.check() == sat:
        model = solver.model()
        solution = [bool(model.evaluate(var)) for var in vars]
        solutions.append(solution)
        
        # Add blocking clause to prevent this solution from being found again
        block = []
        for i, var in enumerate(vars):
            if model[var]:
                block.append(Not(var))
            else:
                block.append(var)
        solver.add(Or(block))
    
    solve_time = time.time() - start_time
    return solutions, solve_time

def count_solutions(clauses, num_vars, max_solutions=1):
    """
    Count solutions to the SAT problem up to max_solutions.
    """
    solutions_found = 0
    for assignment in product([False, True], repeat=num_vars):
        if verify_solution(list(assignment), clauses):
            solutions_found += 1
            if solutions_found >= max_solutions:
                break
    return solutions_found

def format_dimacs(clauses, num_vars):
    """
    Format the problem in DIMACS CNF format.
    """
    lines = [f"p cnf {num_vars} {len(clauses)}"]
    for clause in clauses:
        lines.append(" ".join(map(str, clause + [0])))
    return "\n".join(lines)

if __name__ == "__main__":
    num_vars = 28
    max_clauses = 32
    print("Working with %s variables and %s clauses" % (num_vars, max_clauses))
    
    solution, clauses = generate_unique_sat(num_vars, max_clauses)
    print("Original solution:", solution)
    print("Number of clauses:", len(clauses))
    print("Clauses:", clauses)
    
    # Find one solution
    is_sat, found_solution, one_time = solve_sat_one(clauses, num_vars)
    print("\nFinding one solution:")
    print(f"Satisfiable: {is_sat}")
    print(f"Solution: {found_solution}")
    print(f"Time taken: {one_time:.4f} seconds")
    
    # Find all solutions
    all_solutions, all_time = solve_sat_all(clauses, num_vars)
    print("\nFinding all solutions:")
    print(f"Number of solutions: {len(all_solutions)}")
    print(f"Solutions: {all_solutions}")
    print(f"Time taken: {all_time:.4f} seconds")
    
    # Verify that all solutions are valid
    print("\nVerifying solutions:")
    for sol in all_solutions:
        print(f"Solution {sol} is valid: {verify_solution(sol, clauses)}")

    # brute force
    print("testing brute force")
    start = time.time()
    count_solutions(clauses, num_vars)
    print("brute force time:", time.time() - start)
    