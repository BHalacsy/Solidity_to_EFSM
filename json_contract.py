import subprocess
import json
import os

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# ############### Function to clean the JSON file by removing the extra string ###############

def clean_json_content(json_content):
    # Locate the starting point of the JSON data
    start_index = json_content.find('{')  # Find the first '{' to start the JSON
    if start_index != -1:
        json_content_cleaned = json_content[start_index:]  # Remove anything before the first '{'

        try:
            # Parse the cleaned JSON content
            json_data = json.loads(json_content_cleaned)
            return json_data
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            return None
    else:
        print("No valid JSON content found.")
        return None

def select_solc(contract_file):
    SOLC_MAP = {
        5: "/home/balint/bin/solc-0.5.17",
    }
    try:
        with open(contract_file) as f:
            content = f.read()
        import re
        m = re.search(r'pragma solidity\s+[\^~]?(\d+)\.(\d+)', content)
        if m and int(m.group(1)) == 0:
            minor = int(m.group(2))
            if minor in SOLC_MAP:
                return SOLC_MAP[minor]
    except OSError:
        pass
    return "/home/balint/bin/solc"  # default: 0.8.x

############### Function to compile the contract and return AST JSON in memory ###############
def compile_contract_to_ast_in_memory(contract_file):
    # Command to generate the AST in compact JSON format using solc
    command = [select_solc(contract_file), "--ast-compact-json", contract_file]

    # Run the command and capture the output in memory
    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Error compiling contract: {result.stderr}")
        return None
    else:
        #print(f"AST JSON generated successfully", result.stdout)
        result_json  = result.stdout
        #print(result_json)
        #print("type of output is: ", type(result.stdout))
    return  result_json


############### Main logic ###################################
def process_contract_in_memory(contract_file, target_contract=None):
    # Compile the contract and get the AST JSON data in memory
    raw_json_data = compile_contract_to_ast_in_memory(contract_file)

    clean_json = clean_json_content(raw_json_data)

    # Proceed if the JSON data was successfully generated and loaded
    if clean_json:
        # Extract the relevant nodes
        print(json.dumps(clean_json))
        top_nodes = clean_json['nodes']

        if target_contract:
            for node in top_nodes:
                if node.get('nodeType') == 'ContractDefinition' and node.get('name') == target_contract:
                    return node['nodes']
            print(f"Warning: contract '{target_contract}' not found; falling back to nodes[1]")

        return top_nodes[1]['nodes']
    return None

final_sol_list = []
contract_file = os.path.join(PROJECT_DIR, 'smart_contracts', 'AkuAuction_simplified.sol')
try:
    final_sol_list = process_contract_in_memory(contract_file)
except Exception as e:
    print(f"Error processing contract: {e}")

print(len(final_sol_list))