import json
from pprint import pprint
from copy import deepcopy



"""
File template is the base template for the entire file
Just includes the Main circuit w/ none of the subcircuits
"""
file_template = None
with open('./templates/template_min.sim', 'r') as file:
    file_template = json.loads(file.read())

"""
Or gate template is just an or gate in the right location for the subcircuit
"""
or_gate_template = None
with open('./templates/comp_or_gate_template.json', 'r') as file:
    or_gate_template = json.load(file)

"""
Subcircuit template needs to be missing the or gate and horizontal wires by default
"""
subcircuit_template = None
with open('./templates/subcircuit_template.json', 'r') as file:
    subcircuit_template = json.load(file)







# the locations of the tunnels in each circuit
# enable only when working with the literal

# index into wires by the literal you want to enable, 1-indexed
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



# print(or_gate_template['properties']['Negate 8'])

def generate_or_gate_from_input_negations(negation_list: list[int]) -> str:
    """
    Inputs is a list of ints, where each int represents an input to be negated
    """
    output_or_gate = deepcopy(or_gate_template)

    for str_key in output_or_gate['properties'].keys():
        if 'Negate' in str_key:
            num = int(str_key[len('Negate '):])
            # print(num, type(num))
            if num in negation_list:
                output_or_gate['properties'][str_key] = 'Yes'

    # print(or_gate_out)
    # pprint(or_gate_out)
    # print(json.dumps(or_gate_out, indent=4))
    return output_or_gate

            

# generate_or_gate_from_input_negations([1, 5, 6])






def generate_subcircuit(name: str, clause: list[int]) -> dict:
    """
    Generates a subcircuit from a clause
    
    I need to change all of the following from the template:
    - Name
    - Or gate negations
    - Insert wires for the clauses I want to activate

    """
    output_subcircuit = deepcopy(subcircuit_template)
    output_subcircuit['name'] = name

    literals = [abs(literal) for literal in clause]
    for literal in literals:
        output_subcircuit['wires'].append(wires[literal])
        
    # negation list is zero-indexed, and we're only supporting up to 28 literals
    negation_list = [abs(literal)-1 for literal in clause if literal < 0]
    negated_or = generate_or_gate_from_input_negations(negation_list)
    output_subcircuit['components'].append(negated_or)

    # print(json.dumps(output_subcircuit, indent=4))
    # print(name, clause)
    # input()

    return output_subcircuit


def generate_full_file(clauses: list[list[int]]) -> str:
    assert len(clauses) == 32

    output_circuit_file = deepcopy(file_template)
    for idx, clause in enumerate(clauses):
        subcircuit: dict = generate_subcircuit(f'c{idx+1}', clause)
        # pprint(subcircuit)
        # print(idx, clause)
        # input()
        output_circuit_file['circuits'].append(subcircuit)

    return json.dumps(output_circuit_file, indent=4)
    



if __name__ == "__main__":
    ...
    # generate_or_gate_from_input_negations([1, 5, 6])
    # pprint(file_template)
    # pprint(file_template['circuits'][0])

    # input_clauses = [[-19, -9, 2], [4], [-21], [26], [-27], [2], [15], [20], [-23], [18], [14], [28], [25], [-16], [8], [10], [-11], [7], [-19], [12], [-3], [-22], [1], [17], [-11, 20, 14], [-13], [18, -16], [5], [-9], [6], [24], [4, -9]]
    input_clauses = [[4], [-14], [17], [8], [-6], [-24], [21], [10, 3, -14], [3], [13], [-20], [10], [15, 12], [22], [-16], [-26], [-23, 8], [15], [-5], [25], [-9], [19], [28], [18], [7], [-27], [-23], [-11], [12], [2], [-1], [-6, -16]]
    # solution is [False, True, True, True, False, False, True, True, False, True, False, True, True, False, True, False, True, True, True, False, True, True, False, False, True, False, False, True]
    output = generate_full_file(input_clauses)

    with open('./output.sim', 'w') as file:
        file.write(output)





    exit(0)
    # tmp = None
    # with open('./templates/template_min_ref.sim', 'r') as file:
    #     tmp = json.loads(file.read())
    
    # pprint(tmp['circuits'][2]['wires'])
