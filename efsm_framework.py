import xml.etree.ElementTree as ET
from wmodify import *
from copy import deepcopy
from json_contract import *  # load the list of nodes from the json_contract.py file corresponding to the contract
import  copy

Supremica = {}

modifier_objects_dict = {}

# Events - contains list of all events
Supremica['Events'] = {}
Events = Supremica['Events']

# Components - contains all efsms
Supremica['Components'] = {}
Components = Supremica['Components']

# Variable Component - Contains all variables
Components['VariableComponent'] = {}
VariableComponent = Components['VariableComponent']
VariableComponent['EnumVariables'] = {}
VariableComponent['StructVariables'] = {}

# creating a dictionary to store all generated addresses
VariableComponent['AddressVariables'] = {}
AddressVariables = VariableComponent['AddressVariables']

# creating a dictionary to store all generated boolean variables
VariableComponent['BooleanVariables'] = {}

# creating a dictionary to store Mapping variables
VariableComponent['MappingVariables'] = {}

# creating a dictionary to store TEMP variables
VariableComponent['FunctionVariablesTEMP'] = {}
FunctionVariablesTEMP = VariableComponent['FunctionVariablesTEMP']

# creating a dictionary to store TEMP variables for expressions genearted in solidity_ast_parser
# because function name is unkown
VariableComponent['GeneralVariablesTEMP'] = {}
GeneralVariablesTEMP = VariableComponent['GeneralVariablesTEMP']

# creating a dictionary to store integer variables
VariableComponent['IntegerVariables'] = {}
IntegerVariables = VariableComponent['IntegerVariables']

# declaring address_index to keep track of address variables
address_index = 0

# Initial Node = S0
INITIAL_NODE = 'S0'

# list for transfer efsms
transfer_efsm_list = []


class EFSM:
    def __init__(self,
                 name):  # This is to create the structure for each efsm. Right for modifiers. Later for all functions
        self.params_dict = {}
        #self.guard_transition_template = []
        self.name = name
        self.efsm = {}

        self.efsm['node_list'] = {}
        self.node_list = self.efsm['node_list']

        self.efsm['edge_list'] = {}
        self.edge_list = self.efsm['edge_list']
        self.i = 0

    def addTransition(self, expression):

        transition_type = str()
        source_index = None
        target_index = None
        events = []
        guard_exp = None
        action_exp = None
        evaluate_exp = None
        evaluate_exp = expression  # This should be derived if 'FunctionCall' is require.

        # we have to check the ntype of expression and then add the transition accordingly
        # we should check this by creating a function call and then checking the ntype of the expression
        if expression:  # This is for the placeholder statement


            if expression['ntype'] == 'FunctionCall':
                if expression['name'] == 'require':
                    # assuming that require has only one argument
                    guard_exp = expression['args']
                    transition_type = 'require_true'

                elif 'type' in expression and expression['type'] == 'transfer':
                    transition_type = 'self_loop'
                    events.append(str(expression['name'] + '1'))

                else:
                    transition_type = 'self_loop'
                    events.append(str(expression['name'] + '1'))

            elif expression['ntype'] == 'Simple':
                if 'name' in expression:
                    events.append(expression['name'])
                    if expression['type'] == 'efsm_fail':
                        transition_type = 'efsm_fail'
                        target_index = INITIAL_NODE

                    elif expression['type'] == 'transfer_success':
                        transition_type = 'transfer_success'

                    elif expression['type'] == 'transfer_fail':
                        transition_type = 'transfer_fail'

                    elif expression['type'] == 'transfer_efsm_fail':
                        target_index = INITIAL_NODE

                    elif expression['type'] == 'true_body_last' or expression['type'] == 'false_body_last':
                        transition_type = expression['type']

                    elif expression['type'] == 'function_fail':
                        target_index = INITIAL_NODE

                    elif expression['type'] == 'modifier_guard':
                        transition_type = 'self_loop'
                        guard_exp = expression['guard_exp']

                    elif expression['type'] == 'sender_transfer_initial':
                        transition_type = 'sender_transfer_initial'
                        guard_exp = expression['guard_exp']

                    elif expression['type'] == 'sender_transfer':
                        transition_type = 'sender_transfer'
                        guard_exp = expression['guard_exp']

                    elif expression['type'] == 'sender_transfer_success_initial':
                        transition_type = 'sender_transfer_success_initial'

                    elif expression['type'] == 'sender_transfer_success':
                        transition_type = 'sender_transfer_success'

                    elif expression['type'] == 'require_false':
                        guard_exp = expression['guard_exp']
                        transition_type = expression['type']

                elif 'type' in expression and expression['type'] == 'param_assignment':
                    guard_exp = expression['guard_exp']
                    transition_type = expression['type']
                elif 'type' in expression and (expression['type'] == 'true_body_last' or expression['type'] == 'false_body_last'):
                    transition_type = expression['type']


            elif expression['ntype'] == 'Assignment':
                if expression['kind'] == 'conditional':
                    guard_exp = expression['expression']

                elif expression['kind'] == 'simple':
                    action_exp = expression['exp']

                elif expression['kind'] == 'mapping_assignment_check':
                    #print('Mapping Assignment Check')
                    guard_exp = expression['expression']

                if 'type' in expression:
                    transition_type = expression['type']


            elif expression['ntype'] == 'VariableDeclarationStatement':
                if expression['kind'] == 'conditional':

                    guard_exp = expression['expression']

                elif expression['kind'] == 'mapping_assignment_check':
                    #print('Mapping Assignment Check')
                    guard_exp = expression['expression']
                    #print(asdf)
                elif expression['kind'] == 'address_variable_assignment':
                    action_exp = expression['expression']

                elif expression['kind'] == 'integer_variable_assignment':
                    action_exp = expression['expression']


            elif expression['ntype'] == 'IfStatement':

                if 'kind' in expression and expression['kind'] == 'internal':
                    if expression['condition'] == 'true':
                        guard_exp = expression['guard_exp']
                        transition_type = expression['type']
                #         # guard_exp = ET.tostring(expression['guard_exp'], encoding='unicode', method='xml')
                #         # action_exp = expression['exp']  # Assumption: only one expression in the body
                    elif expression['condition'] == 'false':
                        guard_exp = expression['guard_exp']
                        transition_type = expression['type']
                #         # guard_exp = ET.tostring(expression['guard_exp'], encoding='unicode', method='xml')
                #         # action_exp = expression['exp'] # Assumption: only one expression in the body



        transition = {
            'transition_type': transition_type,
            'source_index': source_index,
            'target_index': target_index,
            'events': events,
            'guard_exp': guard_exp,
            'action_exp': action_exp,
            'evaluate_exp': evaluate_exp
        }

        self.edge_list[f't{self.i}'] = transition
        self.i += 1

    def addModifierInvocation(self, modifiers):
        # Assumption that modifier right now has only one statement, which is the require statement.
        # issue #1 in nishantparekh01/casino_conversion
        for m in modifiers:
            # if m in Components:
            # m['name'] is the name of the modifier

            mod = m['name']

            if 'args' in m:
                mod = modifier_objects_dict[mod]
                event_name = self.name + '1'
                params_dict_key_list = list(mod.params_dict.keys())
                for i, param_value in enumerate(m['args']):
                    mod.params_dict[params_dict_key_list[i]] = param_value
                #print(mod.guard_transition_template[0]) # Why 0 here ? Refer to issue #39 in nishantparekh01/casino_conversion/test1

                replacement_guard = mod.guard_transition_template[0]
                if 'args' in replacement_guard:
                    root = deepcopy(replacement_guard['args'])
                    for si in root.findall('.//SimpleIdentifier'):    # This is to replace the name of the variables in the guard expression with the values passed in the modifier
                        current_name = si.get('Name')
                        if current_name in mod.params_dict:
                            si.set('Name', mod.params_dict[current_name])

                guard_transition = {'ntype': 'Simple', 'name': event_name, 'type': 'modifier_guard', 'guard_exp': root}

                mod.addTransition(guard_transition)

            else:
                Components[mod]['edge_list']['t0']['events'].append(self.name + '1')

    def addModifierParameter(self, parameters):

        for p in parameters:
            self.params_dict[p] = str()

    def add_transfer(self, expression):
        transition_type = 'self_loop'
        events = []
        guard_exp = None
        action_exp = None
        evaluate_exp = None
        evaluate_exp = expression


def superEnumDefinition(packet):
    global VariableComponent
    name = packet['name']
    members = packet['members']

    VariableComponent['EnumVariables'][name] = members
    return True


def superStructDefinition(packet):
    global VariableComponent
    name = packet['name']
    members = packet['members']

    VariableComponent['StructVariables'][name] = members
    return True


def get_address_index():
    global address_index
    address_index += 1
    return address_index


def superVariableDeclaration(packet, **kwargs):
    global VariableComponent
    name = packet['name']
    type = packet['type']

    initial_value =  kwargs.get('initial_value', None )

    if type in VariableComponent['EnumVariables']:
        members = VariableComponent['EnumVariables'][type]

        xml_VariableComponent = ET.Element("VariableComponent", Name=name)
        xml_variableRange = ET.SubElement(xml_VariableComponent, "VariableRange")
        xml_EnumSetExpression = ET.SubElement(xml_variableRange, "EnumSetExpression")
        for mem in members:
            ET.SubElement(xml_EnumSetExpression, "SimpleIdentifier", Name=mem)

        xml_VariableInitial = ET.SubElement(xml_VariableComponent, "VariableInitial")
        xml_initialValue = wmodify_assignment(name, "==", members[0])
        xml_VariableInitial.append(xml_initialValue)
        VariableComponent[name] = xml_VariableComponent


    elif type == 'uint' or type == 'uint256' or type == 'bytes32':

        VariableComponent['IntegerVariables'][name] = [0, 1]

        xml_VariableComponent = ET.Element("VariableComponent", Name=name)
        xml_variableRange = ET.SubElement(xml_VariableComponent, "VariableRange")
        xml_NumericRangeExpression = wmodify_assignment("0", "..", "1")
        xml_variableRange.append(xml_NumericRangeExpression)

        xml_VariableInitial = ET.SubElement(xml_VariableComponent, "VariableInitial")
        xml_initialValue = wmodify_assignment(name, "==", "0")
        xml_VariableInitial.append(xml_initialValue)
        VariableComponent[name] = xml_VariableComponent


    elif type == 'address':

        # name has the name and type has value 'address'
        # set address index to 0 and increment it for each address
        # append the address index to the address name

        address_index = get_address_index()
        address_name = 'x000' + str(address_index)

        # Add this to the dictionary AddressVariables
        VariableComponent['AddressVariables'][name] = address_name

        # create the xml element for the address
        xml_VariableComponent = ET.Element("VariableComponent", Name=name)
        xml_variableRange = ET.SubElement(xml_VariableComponent, "VariableRange")
        xml_EnumSetExpression = ET.SubElement(xml_variableRange, "EnumSetExpression")

        ET.SubElement(xml_EnumSetExpression, "SimpleIdentifier", Name=address_name)

        xml_VariableInitial = ET.SubElement(xml_VariableComponent, "VariableInitial")
        xml_initialValue = wmodify_assignment(name, "==", address_name)
        xml_VariableInitial.append(xml_initialValue)
        VariableComponent[name] = xml_VariableComponent # store the xml element in VariableComponent dictionary

    elif type == 'Mapping':
        #print(packet)
        #{'name': 'withdrawable', 'type': 'Mapping', 'key_value': 'address_uint'}
        mapping_name = packet['name']
        mapping_key_value  = packet['key_value']
        if mapping_key_value == 'address_uint':
            AddressVariables = VariableComponent['AddressVariables']
            # generate variable names combining address and mapping name

            # Store the generated mapping variables in the dictionary MappingVariables with mapping variable name as the key
            VariableComponent['MappingVariables'][mapping_name] = {}
            for declared_address in AddressVariables.keys():
                #print(mapping_name + '_'+ declared_address)
                mapping_variable = mapping_name + '_'+ declared_address
                VariableComponent['MappingVariables'][mapping_name][declared_address] = mapping_variable
                #print(VariableComponent['MappingVariables'])

                # what to declare here ? withdrawable_player, withdrawable_operator
                mapping_variable_packet = {'name':mapping_variable, 'type': 'uint'}
                superVariableDeclaration(mapping_variable_packet)



    elif type == 'bool':
        members =['false', 'true']

        xml_VariableComponent = ET.Element("VariableComponent", Name=name)
        xml_variableRange = ET.SubElement(xml_VariableComponent, "VariableRange")
        xml_EnumSetExpression = ET.SubElement(xml_variableRange, "EnumSetExpression")
        for mem in members:
            ET.SubElement(xml_EnumSetExpression, "SimpleIdentifier", Name=mem)

        xml_VariableInitial = ET.SubElement(xml_VariableComponent, "VariableInitial")
        if not initial_value:
            initial_value = members[0]
        #print('initial value', initial_value, name, type)


        xml_initialValue = wmodify_assignment(name, "==",initial_value)
        xml_VariableInitial.append(xml_initialValue)
        VariableComponent[name] = xml_VariableComponent
        #print('bool variable added', name)

        # Add this to the dictionary AddressVariables
        VariableComponent['BooleanVariables'][name] = members
        #print('Boolean Variables: ', VariableComponent['BooleanVariables'])

def addAutomata(efsm):
    global Components
    Components[efsm.name] = efsm.efsm


def superModifierDefinition(packet):
    # must return a dictionary
    global Supremica

    name = packet['name']  # name of modifier
    # fill the name here. Create a new efsm
    # To create the ast, for each level we need a function

    params = packet['params']
    # Use parameters in whichever way
    body = packet['body']  # list of expressions
    # Generate transitions using expressions here.

    # Create modifier object
    modifier = EFSM(name)

    if params:
        modifier.addModifierParameter(params)
        modifier.guard_transition_template = body
    else:
        for exp in body:
            #modifier.addTransition(exp)
            #print(exp)
            if exp != False:
             process_in_ignore_list(exp, 'args', ignore_list, modifier)

    # Add modifier to the global dictionary
    modifier_objects_dict[name] = modifier

    addAutomata(modifier)
    return Supremica

def add_transfer_efsm(efsm_name):
    #efsm_name = efsm_name
    #print('ADding efsm-----------', efsm_name)
    transfer_efsm_name = efsm_name  # operatortransfer
    if  transfer_efsm_name not in transfer_efsm_list:


        transfer_efsm = EFSM(transfer_efsm_name)
        transfer_efsm_list.append(transfer_efsm_name)

        # transition for transfer event
        transfer_event = {'ntype': 'Simple', 'name': efsm_name  + '1', 'type': 'transfer_event'}
        transfer_efsm.addTransition(transfer_event)

        # transition for transfer fail
        transfer_fail = {'ntype': 'Simple', 'name': efsm_name + 'Fail', 'type': 'transfer_efsm_fail'}
        transfer_efsm.addTransition(transfer_fail)

        # transition for transfer success
        transfer_success = {'ntype': 'Simple', 'name': efsm_name + 'X', 'type': 'transfer_efsm_success'}
        transfer_efsm.addTransition(transfer_success)

        addAutomata(transfer_efsm)


def check_require_in_function(body):
    for exp in body:
        if not isinstance(exp, dict):
            continue
        if 'ntype' in exp and exp['ntype'] == 'FunctionCall':
            if exp['name'] == 'require':
                return True
    return False


def check_parameter_in_require( body, search_string):
    # check for all parameter if they are present in any require statement
    # Check if the search string is in the element's text
    for exp in body:
        if not isinstance(exp, dict):
            continue
        if 'ntype' in exp and exp['ntype'] == 'FunctionCall':
            if exp['name'] == 'require':
                element = exp['args']

                if element.text and search_string in element.text:
                    return True

                # Check if the search string is in the element's tail text
                if element.tail and search_string in element.tail:
                    return True

                # Check if the search string is in any of the element's attributes
                for attribute in element.attrib.values():
                    if search_string in attribute:
                        return True

                # Recursively check all child elements
                for child in element:
                    if in_ignore_list(child, search_string):
                        return True

                # If none of the conditions are met
                return False

        return False




def superFunctionDefinition(packet):
    global false_body
    name = packet['name']
    params = packet['params']
    #print('params', params)
    global param_assigned
    param_assigned = False
    body = packet['body']
    modifiers = packet['modifiers']
    global initial_statement_added
    initial_statement_added = False


    # Create EFSM instance of function
    function = EFSM(name)

    require_in_function = check_require_in_function(body)
    if require_in_function:
        #print('Require in function', name)

        for param, param_type in params.items():
            # check if the parameter is present in the require statement
            if check_parameter_in_require(body, param):
                # Add parameter to the function
                #print('Parameter present in require statement', param, param_type)

                if param_type in VariableComponent['EnumVariables']:
                    # generate xml expression where param = param_type[0] | param_type[1] | param_type[2] | ...
                    guard_exp = wmodify_assignment(param, "==", VariableComponent['EnumVariables'][param_type],
                                                   **{'ntype': 'ParameterDeclarationStatement',
                                                      'kind': 'AssignmentCheck'})
                    # print(ET.tostring(guard_exp, encoding='unicode', method='xml'))
                    param_assignment = {'ntype': 'Simple', 'guard_exp': guard_exp, 'type': 'param_assignment'}
                    function.addTransition(param_assignment)
                    param_assigned = True
                    initial_statement_added = True

                elif param_type == 'uint' or param_type == 'uint256' or param_type == 'bytes32':
                    rhs_list = ['0', '1']
                    guard_exp = wmodify_assignment(param, "==", rhs_list, **{'ntype': 'ParameterDeclarationStatement',
                                                                             'kind': 'AssignmentCheck'})
                    param_assignment = {'ntype': 'Simple', 'guard_exp': guard_exp, 'type': 'param_assignment'}
                    function.addTransition(param_assignment)
                    param_assigned = True
                    initial_statement_added = True
    else:
        # add parameters to the function
        for param, param_type in params.items():
            # print(param, param_type, 'param and param_type')
            if param_type in VariableComponent['EnumVariables']:
                # generate xml expression where param = param_type[0] | param_type[1] | param_type[2] | ...
                guard_exp = wmodify_assignment(param, "==", VariableComponent['EnumVariables'][param_type],
                                               **{'ntype': 'ParameterDeclarationStatement',
                                                  'kind': 'AssignmentCheck'})
                # print(ET.tostring(guard_exp, encoding='unicode', method='xml'))
                param_assignment = {'ntype': 'Simple', 'guard_exp': guard_exp, 'type': 'param_assignment'}
                function.addTransition(param_assignment)
                param_assigned = True

            elif param_type == 'uint' or param_type == 'uint256' or param_type == 'bytes32':
                rhs_list  = ['0','1']
                guard_exp = wmodify_assignment(param, "==", rhs_list, **{'ntype': 'ParameterDeclarationStatement',
                                                                  'kind': 'AssignmentCheck'})
                param_assignment = {'ntype': 'Simple', 'guard_exp': guard_exp, 'type': 'param_assignment'}
                function.addTransition(param_assignment)
                param_assigned = True

    # Add function name to invoked modifiers
    if modifiers:
        function.addModifierInvocation(modifiers)

    # Add transitions to the function based on parameters and its respective values

    for exp_index, exp in enumerate(body):
        #print(exp_index)
        if not isinstance(exp, dict):
            continue
        if 'type' in exp and exp['type'] == 'transfer':
            transfer_in_function_name = str()

            if exp_index == 0:
                first_transition = {'ntype': 'Simple', 'name': name + '1', 'type': 'first_transition'}
                function.addTransition(first_transition)
                transfer_in_function_name = name + exp['name']
                add_transfer_efsm(transfer_in_function_name)

            else:
                transfer_in_function_name = name + exp['name']
                add_transfer_efsm(transfer_in_function_name)


            exp['name'] = name + exp['name'] # transfer name is now function name + transfer name to distinguish between same address transfers in different functions
            function.addTransition(exp)

            transfer_success = transfer_in_function_name + 'X'
            transfer_fail = transfer_in_function_name + 'Fail'

            transfer_success_exp = {'ntype': 'Simple', 'name': transfer_success, 'type': 'transfer_success'}
            transfer_fail_exp = {'ntype': 'Simple', 'name': transfer_fail, 'type': 'transfer_fail'}
            next_statement = {'ntype': 'Simple'}
            efsm_fail = {'ntype': 'Simple', 'name': name + 'Fail', 'type': 'efsm_fail'}

            function.addTransition(transfer_fail_exp)
            function.addTransition(efsm_fail)
            function.addTransition(transfer_success_exp)
            function.addTransition(next_statement)

        elif 'type' in exp and exp['type'] == 'mapping_transfer': # check issue #49 in nishantparekh01/test
            #print('Mapping Transfer reached in superFunctionDefinition')
            #print(exp)
            sender_list = exp['sender_list']
            #print('SENDER LIST-----', sender_list)
            #print(AddressVariables)

            #print(sender_list)
            #asdf



            if exp_index == 0:
                first_transition = {'ntype': 'Simple', 'name': name + '1', 'type': 'first_transition'}
                function.addTransition(first_transition)
                for sender_address in sender_list: # add transfer_efsm for each address if it is not already present
                    if sender_address not in any(list(FunctionVariablesTEMP.values())):
                        #print('Check SENDER Address', sender_address)
                        sender_address_check = name +sender_address + 'transfer'
                        add_transfer_efsm(sender_address_check)



            else:
                for sender_address in sender_list: # add transfer_efsm for each address if it is not already present
                    # trialzone4------------------------------
                    if not check_address_in_TEMP(sender_address):
                        sender_address_check = name + sender_address + 'transfer'
                        add_transfer_efsm(sender_address_check)

            for sender_id, sender_address in enumerate(sender_list):
                if not check_address_in_TEMP(sender_address):
                    transfer_event = name +sender_address + 'transfer'
                    transfer_event_initial = transfer_event + '1'
                    transfer_event_fail = transfer_event + 'Fail'
                    transfer_event_success = transfer_event + 'X'
                    #print('sender id ====', sender_id)

                    sender_guard = get_sender_guard(sender_address)

                    if sender_id == 0:
                        transfer_attempt_type = 'sender_transfer_initial'

                        transfer_attempt = {'ntype': 'Simple', 'name': transfer_event_initial, 'sender_index' : sender_id, 'guard_exp': sender_guard ,'type' : transfer_attempt_type}
                        function.addTransition(transfer_attempt)

                        transfer_fail_exp = {'ntype': 'Simple', 'name': transfer_event_fail, 'type': 'transfer_fail'}
                        efsm_fail = {'ntype': 'Simple', 'name': name + 'Fail', 'type': 'efsm_fail'}
                        function.addTransition(transfer_fail_exp)
                        function.addTransition(efsm_fail)

                        transfer_success_type = 'sender_transfer_success_initial'
                        transfer_success_exp = {'ntype': 'Simple', 'name': transfer_event_success, 'type': transfer_success_type}
                        function.addTransition(transfer_success_exp)


                    else:
                        transfer_attempt_type = 'sender_transfer'

                        transfer_attempt = {'ntype': 'Simple', 'name': transfer_event_initial,
                                            'sender_index': sender_id, 'guard_exp': sender_guard , 'type': transfer_attempt_type}
                        function.addTransition(transfer_attempt)

                        transfer_fail_exp = {'ntype': 'Simple', 'name': transfer_event_fail, 'type': 'transfer_fail'}
                        efsm_fail = {'ntype': 'Simple', 'name': name + 'Fail', 'type': 'efsm_fail'}
                        function.addTransition(transfer_fail_exp)
                        function.addTransition(efsm_fail)

                        transfer_success_exp = {'ntype': 'Simple', 'name': transfer_event_success,
                                                'type': 'sender_transfer_success'}
                        print('TRANSFER SUCCESS',sender_address,transfer_success_exp)
                        function.addTransition(transfer_success_exp)

                        if exp_index == len(body) - 1 and sender_id == len(sender_list) - 1:
                            #function_complete = {'ntype': 'Simple', 'name': name + 'X', 'type': 'function_complete'}
                            extra_transition = {'ntype': 'Simple'}
                            function.addTransition(extra_transition)



        elif exp['ntype'] == 'IfStatement':
            true_condition = exp['true_condition']
            false_condition = exp['false_condition']

            true_body = exp['true_body']

            if 'false_body' in exp:
                false_body = exp['false_body']
            true_exp_transition = {'ntype': 'IfStatement', 'kind': 'internal', 'condition': 'true',
                                   'guard_exp': true_condition, 'type': 'true_body_start'}

            if 'false_body' in exp and len(exp['false_body']) > 0:
                false_exp_transition = {'ntype': 'IfStatement', 'kind': 'internal', 'condition': 'false',
                                    'guard_exp': false_condition, 'type': 'false_body_start'}
            else:
                false_exp_transition = {'ntype': 'IfStatement', 'kind': 'internal', 'condition': 'false','guard_exp': false_condition, 'type': 'false_body_absent'}

            function.addTransition(true_exp_transition)
            for index, stmnt in enumerate(true_body): # add transitions for each statement in the true body
                if not isinstance(stmnt, dict):
                    continue
                if index == len(true_body) - 1: # if it is the only statement / last statement in true body

                    #print('true body last statement', stmnt)
                    if 'type' in stmnt and stmnt['type'] == 'transfer':
                        transfer_in_function_name = str()
                        print('Transfer in function name', transfer_in_function_name)


                        if exp_index == 0:
                            first_transition = {'ntype': 'Simple', 'name': name + '1', 'type': 'first_transition'}
                            function.addTransition(first_transition)
                            transfer_in_function_name = name + stmnt['name']
                            add_transfer_efsm(transfer_in_function_name)


                        else:
                            transfer_in_function_name = name + stmnt['name']
                            add_transfer_efsm(transfer_in_function_name)


                        stmnt['name'] = name + stmnt[
                            'name']  # transfer name is now function name + transfer name to distinguish between same address transfers in different functions
                        function.addTransition(stmnt)

                        transfer_success = transfer_in_function_name + 'X'
                        transfer_fail = transfer_in_function_name + 'Fail'

                        transfer_success_exp = {'ntype': 'Simple', 'name': transfer_success, 'type': 'transfer_success'}
                        transfer_fail_exp = {'ntype': 'Simple', 'name': transfer_fail, 'type': 'transfer_fail'}
                        next_statement = {'ntype': 'Simple', 'type': 'true_body_last'}
                        efsm_fail = {'ntype': 'Simple', 'name': name + 'Fail', 'type': 'efsm_fail'}

                        function.addTransition(transfer_fail_exp)
                        function.addTransition(efsm_fail)
                        function.addTransition(transfer_success_exp)
                        function.addTransition(next_statement)
                    else:
                        stmnt['type'] = 'true_body_last'
                        if name not in FunctionVariablesTEMP:
                            FunctionVariablesTEMP[name] = {}
                        if 'exp' in stmnt:
                            assignment_xml = stmnt['exp']
                            # print('Assignment XML', assignment_xml)

                            # if exp_index != len(body) -1 :
                            lhs_variable = get_lhs_variable(assignment_xml)
                            if lhs_variable in VariableComponent:
                                # print('Variable Component', VariableComponent[lhs_variable])
                                lhs_variable_temp = lhs_variable + 'TEMP'

                                # Add the lhs_variable to the FunctionVariablesTEMP dictionary
                                FunctionVariablesTEMP[name][lhs_variable] = lhs_variable_temp

                                # Replace and declare the lhs_variable with lhs_variable_temp
                                variable_temp_xml_expression = replace_with_temp(assignment_xml, lhs_variable,
                                                                                 lhs_variable_temp)
                                # print('Variable Temp XML', variable_temp_xml_expression)

                                # replace var with varTEMP in the expression if it is not the last expression

                                exp['exp'] = variable_temp_xml_expression

                                # Add variableTEMP to VariableComponent - replace VariableComponent with FunctionVariablesTEMP
                                lhs_variable_definition = VariableComponent[lhs_variable]
                                lhs_variable_temp_definition = copy.deepcopy(lhs_variable_definition)
                                lhs_variable_temp_definition = replace_with_temp(lhs_variable_temp_definition, lhs_variable,
                                                                                 lhs_variable_temp)

                                # Add the lhs_variable_temp to the VariableComponent
                                VariableComponent[lhs_variable_temp] = lhs_variable_temp_definition
                        function.addTransition(stmnt)
                else: # transfer not added here, can be added later
                    if 'exp' or 'expression' in stmnt:
                        if 'exp' in exp:

                            process_in_ignore_list(stmnt, 'exp', ignore_list, function)

                        elif 'expression' in exp:

                            process_in_ignore_list(stmnt, 'expression', ignore_list, function)

                if stmnt['ntype'] == 'FunctionCall':
                    if stmnt['type'] == 'transfer':
                        #print('-----------------Transfer in function call-----------------')

                        continue
                    elif index == len(true_body) - 1: # flag the last statement in the true body, if statement is a function call

                        function_complete = {'ntype': 'Simple', 'name': stmnt['name'] + 'X', 'type': 'true_body_last'}
                        function_call_name = stmnt['name']
                        if check_transfer_in_function(function_call_name):
                            function_fail = {'ntype': 'Simple', 'name': stmnt['name'] + 'Fail', 'type': 'function_fail'}
                            function.addTransition(function_fail)
                        function.addTransition(function_complete)
                    else:
                        function_complete = {'ntype': 'Simple', 'name': stmnt['name'] + 'X', 'type': 'function_complete'}
                        function_fail = {'ntype': 'Simple', 'name': stmnt['name'] + 'Fail', 'type': 'function_fail'}
                        #function.addTransition(function_fail)
                        if check_transfer_in_function(stmnt['name']):
                            function_fail = {'ntype': 'Simple', 'name': stmnt['name'] + 'Fail', 'type': 'function_fail'}
                            function.addTransition(function_fail)

                        function.addTransition(function_complete)


            function.addTransition(false_exp_transition) # add transition for false condition. For both cases when false body is present/absent


            if 'false_body' in exp: # if false body is present
                for index, stmnt in enumerate(false_body): # add transitions for each statement in the false body
                    if not isinstance(stmnt, dict):
                        continue
                    if index == len(false_body) - 1:  # if it is the last statement in the false body
                        stmnt['type'] = 'false_body_last'
                        function.addTransition(stmnt)
                    #     if exp_index == len(body) - 1: # and if it is the last transition in the body
                    #         function_complete = {'ntype': 'Simple','name': name + 'X', 'type': 'function_complete'}
                    #         function.addTransition(function_complete)
                    #
                    # else:
                    #     pass
                        #function.addTransition(stmnt)
                    if stmnt['ntype'] == 'FunctionCall':
                        if index == len(false_body) - 1: # flag the last statement in the false body, if statement is a function call
                            function_complete = {'ntype': 'Simple', 'name': stmnt['name'] + 'X', 'type': 'false_body_last'}
                            function_call_name = stmnt['name']
                            if check_transfer_in_function(function_call_name):
                                function_fail = {'ntype': 'Simple', 'name': stmnt['name'] + 'Fail', 'type': 'function_fail'}
                                function.addTransition(function_fail)
                            # else:
                            # function_fail = {'ntype': 'Simple', 'name': stmnt['name'] + 'Fail', 'type': 'function_fail'}
                            # function.addTransition(function_fail)
                            function.addTransition(function_complete)

                        else:
                            function_complete = {'ntype': 'Simple', 'name': stmnt['name'] + 'X', 'type': 'function_complete'}
                            function_fail = {'ntype': 'Simple', 'name': stmnt['name'] + 'Fail', 'type': 'function_fail'}
                            function.addTransition(function_fail)
                            function.addTransition(function_complete)
            else:
                # if false body is absent and it was the last transition
                if exp_index == len(body) - 1:
                    function_complete = {'ntype': 'Simple', 'name': name + 'X', 'type': 'function_complete'}
                    function.addTransition(function_complete)

        elif exp['ntype'] == 'FunctionCall' and exp['name'] == 'require':

            if isinstance(exp['args'], str): # case where require statement has a single variable of boolean type, example: require(auctionOpen)
                    if exp['args'] in VariableComponent['BooleanVariables']:
                        exp['args'] = wmodify_assignment(exp['args'], "==", "true")



            process_in_ignore_list(exp, 'args', ignore_list, function, transition_type = 'require_true', efsm_name = name)
            if exp_index == 0:
                initial_statement_added = True



            # else:
            #     process_in_ignore_list(exp, 'args', ignore_list, function)
            #function.addTransition(exp)

            # Parameter assignment place here so that it is called after the require statement if any require statement is present
            if param_assigned == False:
                for param, param_type in params.items():
                    #print(param, param_type, 'param and param_type')
                    if param_type in VariableComponent['EnumVariables']:
                        # generate xml expression where param = param_type[0] | param_type[1] | param_type[2] | ...
                        guard_exp = wmodify_assignment(param, "==", VariableComponent['EnumVariables'][param_type],
                                                       **{'ntype': 'ParameterDeclarationStatement',
                                                          'kind': 'AssignmentCheck'})
                       # print(ET.tostring(guard_exp, encoding='unicode', method='xml'))
                        param_assignment = {'ntype': 'Simple', 'guard_exp': guard_exp, 'type': 'param_assignment'}
                        function.addTransition(param_assignment)

                    # work on this part later
                    elif param_type == 'uint' or param_type == 'uint256' or param_type == 'bytes32':
                        rhs_list  = ['0','1']
                        guard_exp = wmodify_assignment(param, "==", rhs_list, **{'ntype': 'ParameterDeclarationStatement',
                                                                          'kind': 'AssignmentCheck'})
                        param_assignment = {'ntype': 'Simple', 'guard_exp': guard_exp, 'type': 'param_assignment'}
                        function.addTransition(param_assignment)
                    param_assigned = True


        elif exp['ntype'] == 'Assignment' and exp['kind'] == 'structConstructorCall':
            #print('Struct Constructor Call')
            for attr_assignments in exp['exp']:
                #function.addTransition(attr_assignments)
                #print(exp)
                #print(attr_assignments)
                # trialzone ------------------------
                if name not in FunctionVariablesTEMP:
                    FunctionVariablesTEMP[name] = {}
                assignment_xml = attr_assignments
                # print('Assignment XML', assignment_xml)

                # if exp_index != len(body) -1 :
                lhs_variable = get_lhs_variable(assignment_xml)
                if lhs_variable in VariableComponent:
                    # print('Variable Component', VariableComponent[lhs_variable])
                    lhs_variable_temp = lhs_variable + 'TEMP'

                    # Add the lhs_variable to the FunctionVariablesTEMP dictionary
                    FunctionVariablesTEMP[name][lhs_variable] = lhs_variable_temp

                    # Replace and declare the lhs_variable with lhs_variable_temp
                    variable_temp_xml_expression = replace_with_temp(assignment_xml, lhs_variable, lhs_variable_temp)
                    # print('Variable Temp XML', variable_temp_xml_expression)
                    # VariableComponent[lhs_variable_temp] = variable_temp_xml

                    # replace var with varTEMP in the expression if it is not the last expression

                    attr_assignments = variable_temp_xml_expression

                    # Add variableTEMP to VariableComponent - replace VariableComponent with FunctionVariablesTEMP
                    lhs_variable_definition = VariableComponent[lhs_variable]
                    lhs_variable_temp_definition = copy.deepcopy(lhs_variable_definition)
                    lhs_variable_temp_definition = replace_with_temp(lhs_variable_temp_definition, lhs_variable,
                                                                     lhs_variable_temp)

                    # Add the lhs_variable_temp to the VariableComponent
                    VariableComponent[lhs_variable_temp] = lhs_variable_temp_definition

                exp = {'ntype': 'Assignment', 'kind': 'simple', 'exp': attr_assignments}
                #print(exp)
                process_in_ignore_list(    exp, 'exp', ignore_list, function)
                #function.addTransition(exp)
                #print('assignment added')
            #print(asdf)

        else:
            if 'exp' in exp or 'expression' in exp:
                #print('Expression in here', exp)
# do some processing here where lhs is replaced with lhsTEMP

                #exp_string = ET.tostring(exp['exp'], encoding='unicode', method='xml')
                if 'exp' in exp:
                    #print('Expression in here', exp)
                    #do some processing here where lhs is replaced with lhsTEMP
                    if name not in FunctionVariablesTEMP:
                        FunctionVariablesTEMP[name] = {}
                    assignment_xml = exp['exp']
                    #print('Assignment XML', assignment_xml)

                    #if exp_index != len(body) -1 :
                    lhs_variable = get_lhs_variable(assignment_xml)
                    if lhs_variable in VariableComponent:
                                #print('Variable Component', VariableComponent[lhs_variable])
                                lhs_variable_temp = lhs_variable + 'TEMP'

                                # Add the lhs_variable to the FunctionVariablesTEMP dictionary
                                FunctionVariablesTEMP[name][lhs_variable] = lhs_variable_temp

                                # Replace and declare the lhs_variable with lhs_variable_temp
                                variable_temp_xml_expression = replace_with_temp(assignment_xml, lhs_variable, lhs_variable_temp)
                                #print('Variable Temp XML', variable_temp_xml_expression)
                                #VariableComponent[lhs_variable_temp] = variable_temp_xml



                                # replace var with varTEMP in the expression if it is not the last expression

                                exp['exp'] = variable_temp_xml_expression

                                 # Add variableTEMP to VariableComponent - replace VariableComponent with FunctionVariablesTEMP
                                lhs_variable_definition = VariableComponent[lhs_variable]
                                lhs_variable_temp_definition = copy.deepcopy(lhs_variable_definition)
                                lhs_variable_temp_definition = replace_with_temp(lhs_variable_temp_definition, lhs_variable, lhs_variable_temp)

                                    # Add the lhs_variable_temp to the VariableComponent
                                VariableComponent[lhs_variable_temp] = lhs_variable_temp_definition


                    else:
                        pass

                    process_in_ignore_list(exp, 'exp', ignore_list, function)
                    initial_statement_added = True

                elif 'expression' in exp:

                    process_in_ignore_list(exp, 'expression', ignore_list, function)
                    initial_statement_added = True


    efsm_edge_list = function.edge_list
    if not efsm_edge_list:
        return Supremica
    last_key, last_element = next(reversed(efsm_edge_list.items()))

    variable_temp_dict = {}
    if name in FunctionVariablesTEMP and len(list(FunctionVariablesTEMP[name].keys())) != 0:
        variable_temp_dict = FunctionVariablesTEMP[name]


    reassignment_variable_xml = None
    if variable_temp_dict != {}:
        reassignment_variable_xml = get_variable_reassignment(variable_temp_dict)

    # case1 : reassigning variabes only if there is no action expression present
    if last_element['action_exp'] == None:
        last_element['action_exp'] = reassignment_variable_xml

        last_element['transition_type'] = 'final_transition'
        last_element['guard_exp'] = None
    else:
        last_transition = {'ntype': 'Simple', 'type': 'final_transition'}
        function.addTransition(last_transition)

        efsm_edge_list = function.edge_list
        last_key, last_element = next(reversed(efsm_edge_list.items()))
        last_element['action_exp'] = reassignment_variable_xml

    # reassign_lhs_xml =
    #print(function.edge_list)
    addAutomata(function)
    return Supremica

ignore_list = ['pot']
#ignore_list = []

def superVariableDeclarationStatement(packet):
    pass

################ Adding framework behaviour ################################################

################ Adding in_ignore_list ################################################

def in_ignore_list(element, search_string):
    # Check if the search string is in the element's text
    if element.text and search_string in element.text:
        return True

    # Check if the search string is in the element's tail text
    if element.tail and search_string in element.tail:
        return True

    # Check if the search string is in any of the element's attributes
    for attribute in element.attrib.values():
        if search_string in attribute:
            return True

    # Recursively check all child elements
    for child in element:
        if in_ignore_list(child, search_string):
            return True

    # If none of the conditions are met
    return False

################ Processing if in in_ignore_list ################################################

def process_in_ignore_list(exp, exp_key, ignore_list, function, **kwargs):
    transition_type = kwargs.get('transition_type', None)
    efsm_name = kwargs.get('efsm_name', None)

    false_exp = {}
    #print('Expression:--',exp)
    #print(exp)
    if exp_key not in exp:
        function.addTransition(exp)
        return
    #print(exp[exp_key])
    exp_node = exp[exp_key]
    #print('Exp Node---', exp_node)

    for ignore_var in ignore_list:
        if in_ignore_list(exp_node, ignore_var):
            #print('Im hereeee')
            exp[exp_key] = None
            break

    if transition_type  and initial_statement_added == True and exp[exp_key] != None:
            exp['type'] = transition_type
            #print('Transition Type-----------', transition_type)
            require_condition = exp['args']
            require_condition_false = ET.Element("UnaryExpression", Operator="!")
            require_condition_false.append(require_condition)
            function_fail = efsm_name + 'Fail'
            false_exp = {'ntype': 'Simple','name':function_fail, 'guard_exp': require_condition_false, 'type': 'require_false' }


    function.addTransition(exp)
    if false_exp != {}:
        #print("False Exp", false_exp)
        function.addTransition(false_exp)



################ Checking through final_sol_list ################################################

#print(final_sol_list)

def check_transfer_in_function(function_name):
    for node in final_sol_list:
        if node['nodeType'] != 'FunctionDefinition':
            continue
        node_name = node['name'] or node.get('kind', '')
        if node_name == function_name:
            node_string = str(node)
            return 'transfer' in node_string
    return False



#check_transfer_in_function('operatorWins')

################ Definition for get_lhs_variable ################################################

def get_lhs_variable(root):
    #print(ET.tostring(root, encoding='unicode', method='xml'))

    variable = root.find("./SimpleIdentifier")
    if variable is not None and "Name" in variable.attrib:
        #print(variable.attrib["Name"])
        return variable.attrib["Name"]  # Return the name of the variable
    return None

################ Definition for get_sender_guard ################################################

def get_sender_guard(sender_address):
    sender_guard = wmodify_assignment('sender', "==", sender_address)
    return sender_guard


################ Definition for replace_with_temp ################################################

def replace_with_temp(element, old_variable, new_variable):
    """
    Recursively replaces all occurrences of old_variable with new_variable in an XML element
    and returns the updated XML element.

    :param element: The root XML element to traverse.
    :param old_variable: The variable name to be replaced.
    :param new_variable: The variable name to replace with.
    :return: The updated XML element.
    """
    # Check if the element has a 'Name' attribute and replace it if it matches old_variable
    if element.attrib.get('Name') == old_variable:
        element.set('Name', new_variable)

    # Check the text of the element (if applicable)
    if element.text and old_variable in element.text:
        element.text = element.text.replace(old_variable, new_variable)

    # Recursively process child elements
    for child in element:
        replace_with_temp(child, old_variable, new_variable)

    return element

################ Definition for get_variable_reassignment ################################################


def get_variable_reassignment(variable_dict):


    container = ET.Element("Container")  # Temporary container for grouping elements

    # Iterate over the dictionary to create each BinaryExpression
    for lhs_variable, lhs_variable_temp in variable_dict.items():
        # Create a BinaryExpression element
        if lhs_variable not in ignore_list:
            binary_expression = ET.SubElement(
                container,
                "BinaryExpression",
                {"Operator": "=", "Text": f"{lhs_variable} = {lhs_variable_temp}"}
            )

            # Add SimpleIdentifiers for the left-hand side and right-hand side
            ET.SubElement(binary_expression, "SimpleIdentifier", {"Name": lhs_variable})
            ET.SubElement(binary_expression, "SimpleIdentifier", {"Name": lhs_variable_temp})

    # Return the container as the XML element
    if len(container) != 0:
        return container
    else:
        return None


def check_address_in_TEMP(sender_address):
    for key, value in FunctionVariablesTEMP.items():
        if sender_address in value.values():
            #print('SENDER FOUND', sender_address)
            return True

    return False
