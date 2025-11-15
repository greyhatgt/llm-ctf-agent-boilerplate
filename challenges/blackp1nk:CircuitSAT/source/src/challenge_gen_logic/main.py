from circuitsim_file_gen import generate_full_file
from constraints_gen import generate_unique_sat
import base64

NUM_VARS = 28
NUM_CLAUSES = 32


def generate_challenge(debug = False) -> tuple[str, list[bool]]:
    """
    Generates a challenge for the user to solve

    First return is the base64 encoded circuit file
    
    Second return is the T/F list answer key
    """
    answer_key, clauses = generate_unique_sat(NUM_VARS, NUM_CLAUSES)
    print(clauses)
    circuit_file = generate_full_file(clauses)
    encoded_circuit_file = base64.b64encode(circuit_file.encode('utf-8')).decode('utf-8')
    if debug:
        print('Clauses:', clauses)
        print('Answer Key:', answer_key)

    return encoded_circuit_file, answer_key


if __name__ == "__main__":
    b64_circuit_file, answer_key = generate_challenge(debug=True)
    print('Circuit File:')
    print(b64_circuit_file)