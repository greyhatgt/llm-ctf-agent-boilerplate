#!/usr/bin/env python3

import os
import re
import sys
from pwn import *
import threading
import time

ROOT = os.path.abspath(os.path.dirname(__file__))

# Adjust to the correct path for remote_chall.py
bin = os.path.join(ROOT, "../docker/remote_chall.py")
print(bin)






from typing import Optional
from z3 import *
import base64
import time
import json
from pprint import pprint

NUM_VARS = 28
NUM_CLAUSES = 32

wires = [
    None,
    {'isHorizontal': True, 'length': 1, 'x': 25, 'y': 3},
    {'isHorizontal': True, 'length': 6, 'x': 25, 'y': 4},
    {'isHorizontal': True, 'length': 1, 'x': 25, 'y': 5},
    {'isHorizontal': True, 'length': 6, 'x': 25, 'y': 6},
    {'isHorizontal': True, 'length': 1, 'x': 25, 'y': 7},
    {'isHorizontal': True, 'length': 6, 'x': 25, 'y': 8},
    {'isHorizontal': True, 'length': 1, 'x': 25, 'y': 9},
    {'isHorizontal': True, 'length': 6, 'x': 25, 'y': 10},
    {'isHorizontal': True, 'length': 1, 'x': 25, 'y': 11},
    {'isHorizontal': True, 'length': 6, 'x': 25, 'y': 12},
    {'isHorizontal': True, 'length': 1, 'x': 25, 'y': 13},
    {'isHorizontal': True, 'length': 6, 'x': 25, 'y': 14},
    {'isHorizontal': True, 'length': 1, 'x': 25, 'y': 15},
    {'isHorizontal': True, 'length': 6, 'x': 25, 'y': 16},
    {'isHorizontal': True, 'length': 1, 'x': 25, 'y': 18},
    {'isHorizontal': True, 'length': 6, 'x': 25, 'y': 19},
    {'isHorizontal': True, 'length': 1, 'x': 25, 'y': 20},
    {'isHorizontal': True, 'length': 6, 'x': 25, 'y': 21},
    {'isHorizontal': True, 'length': 1, 'x': 25, 'y': 22},
    {'isHorizontal': True, 'length': 6, 'x': 25, 'y': 23},
    {'isHorizontal': True, 'length': 1, 'x': 25, 'y': 24},
    {'isHorizontal': True, 'length': 6, 'x': 25, 'y': 25},
    {'isHorizontal': True, 'length': 1, 'x': 25, 'y': 26},
    {'isHorizontal': True, 'length': 6, 'x': 25, 'y': 27},
    {'isHorizontal': True, 'length': 1, 'x': 25, 'y': 28},
    {'isHorizontal': True, 'length': 6, 'x': 25, 'y': 29},
    {'isHorizontal': True, 'length': 1, 'x': 25, 'y': 30},
    {'isHorizontal': True, 'length': 6, 'x': 25, 'y': 31}
]

wire_locs = {
    (25, 3): 1,
    (25, 4): 2,
    (25, 5): 3,
    (25, 6): 4,
    (25, 7): 5,
    (25, 8): 6,
    (25, 9): 7,
    (25, 10): 8,
    (25, 11): 9,
    (25, 12): 10,
    (25, 13): 11,
    (25, 14): 12,
    (25, 15): 13,
    (25, 16): 14,
    (25, 18): 15,
    (25, 19): 16,
    (25, 20): 17,
    (25, 21): 18,
    (25, 22): 19,
    (25, 23): 20,
    (25, 24): 21,
    (25, 25): 22,
    (25, 26): 23,
    (25, 27): 24,
    (25, 28): 25,
    (25, 29): 26,
    (25, 30): 27,
    (25, 31): 28
}



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


def extract_constraints_from_subcircuit(subcircuit: dict) -> list[int]:
    literals_in_component = []
    for wire in subcircuit['wires']:
        # print(wire)
        if (int(wire['x']), int(wire['y'])) in wire_locs.keys():
            literals_in_component.append(wire_locs[(int(wire['x']), int(wire['y']))])
    # print(literals_in_component)

    or_negations = []
    or_gate: Optional[dict] = None
    # find or gate
    for component in subcircuit['components']:
        if component['name'] == 'com.ra4king.circuitsim.gui.peers.gates.OrGatePeer':
            or_gate = component
            break
    if not or_gate:
        print('ERROR: No OR gate found in subcircuit')
        return []
    # print('or gate:')
    # pprint(or_gate)
    for property in or_gate['properties'].keys():
        if 'Negate ' in property:
            # print(property, or_gate['properties'][property])
            target_literal = int(property.split(' ')[1]) + 1
            # print(or_gate['properties'][property])
            if or_gate['properties'][property] == 'Yes':
                or_negations.append(target_literal)
    # print('or negs', or_negations)

    dimacs_literals = []

    for literal in literals_in_component:
        if literal in or_negations:
            dimacs_literals.append(-literal)
        else:
            dimacs_literals.append(literal)

    return dimacs_literals





def extract_all_clauses(csim_dict: dict) -> list[list[int]]:
    clauses = []
    for subcircuit in csim_dict['circuits']:
        if subcircuit['name'] == 'Main':
            continue
        clauses.append(extract_constraints_from_subcircuit(subcircuit))
    return clauses


def solve_challenge(csim_b64: str) -> list[bool]:
    csim_json = base64.b64decode(csim_b64).decode('utf-8')
    clauses = extract_all_clauses(json.loads(csim_json))
    print('clauses:', clauses)
    is_satisfiable, solution, solve_time = solve_sat_one(clauses, NUM_VARS)
    print('Took {:.2f} seconds to solve'.format(solve_time))
    if not is_satisfiable:
        print("ERROR: FAILED!")
        return []
    return solution






































def solve_round(p: process) -> bytes:
    # ...
    b64 = p.recvline().strip()
    p.recvline()
    # print(p.recvall())

    sol = solve_challenge(b64.decode('utf-8'))
    print(sol)
    print(len(sol))

    if not sol:
        print("Failed to solve challenge.")

    for s in sol:
        print(s)
        p.sendline(b'T' if s else b'F')
        print(p.recvline())
        flag = p.recvline()
        print('b', flag)

    # print(p.recvall())
    # print(p.recvline())

    return flag







def exploit(p: process):
    # Loop to respond correctly to each prompt until the flag is printed or program ends

    # print(p.recvuntil(b"Enter T or F.\n"))
    # print(p.recvall(timeout=3))
    p.recvline()

    flag = None
    try:
        for _ in range(10):
            flag = solve_round(p)
            print(p.recvline())
    except:
        flag = flag.strip().decode('utf-8')
        print("Flag:", flag)


    # flag = p.recvline()


    return flag

    exit()

    b64 = p.recvline().strip()
    p.recvline()
    # print(p.recvall())

    sol = solve_challenge(b64.decode('utf-8'))
    print(sol)
    print(len(sol))

    if not sol:
        print("Failed to solve challenge.")

    for s in sol:
        print(s)
        p.sendline(b'T' if s else b'F')
        print(p.recvline())
        print(p.recvline())

    # print(p.recvall())
    print(p.recvline())
    # print(p.recvline())
    # print(p.recvline())
    # print(p.recvline())
    # print(p.recvline())
    # p.recvline()

    exit()

    # exit()
    score = 0
    while score < 10:
        for j in range(28):
            p.recvuntil(b"Enter T or F.")
            p.sendline(b'T')  # Send 'T' for each variable, based on hardcoded list in encode_and_generate_tf

            # Read response and check if we got "Correct!" or "Challenge fail!"
            response = p.recvline().strip()
            if b"Challenge fail!" in response:
                print("Exploit failed.")
                return None
            elif b"Correct!" in response:
                continue

        # Increment score
        score += 1
        p.recvuntil(b"Score:")
        print(f"Score: {score}")

        # Check if we've reached the score threshold for winning
        if score == 10:
            flag_line = p.recvline().strip()
            return parse_flag(flag_line)

def parse_flag(out):
    m = re.search(b"(tkctf{[^}]+})", out)
    if m is None:
        return None
    return m.groups()[0].decode('utf-8')

if __name__ == '__main__':
    if "REMOTE" in os.environ:
    # if True:
        if not "PORT" in os.environ:
            print("[!] Please specify the port number")
            exit(1)
        p = remote("localhost", int(os.environ["PORT"]))
    else:
        b = os.path.abspath(bin)
        p = process(["python3", b], cwd=os.path.dirname(b))

    flag = exploit(p)
    if flag:
        print("Found: %s" % flag)
        print("OK!")
        exit(0)
    else:
        print("FAILED!")
        exit(1)