# Ignored nodeTypes :
# 1. IdentifierPath

from efsm_framework import *
import xml.etree.ElementTree as ET
from wmodify import *
import copy

current_function_name = str()


def ntype(node):
    return node['nodeType']

def handleMemberAccess(node):
    assert ntype(node) == 'MemberAccess', "Node not MemberAccess"

    name = str()
    memberName = node['memberName'] # transfer
    #name = lookup_table[ntype(node['expression'])](node['expression']) # name = {'ntype': 'FunctionCall', 'name' : name, 'args' : 'msg.sender'} or name = wager

    if ntype(node['expression']) == 'FunctionCall' and node['expression']['kind'] == 'typeConversion':
        name_node  = node['expression']['arguments'][0]
        if 'name' in name_node: # name = sender
            name = name_node['name']
            #print('Sender found here---------', name)
            #print(asdf)
        elif 'memberName' in name_node:
            name = name_node['memberName']
            #print('MemberName found here---------', name)
            #print(asdf)


    else:
        name = lookup_table[ntype(node['expression'])](node['expression'])

    for members in VariableComponent['StructVariables'].values():
        if memberName in members:
            #print('Struct variable found:', memberName)
            #print(asdf)
            return name + "_" + memberName


    if isinstance(name, dict):
        return name['args'] + "." + memberName
        # example:
        #return memberName
    elif name == 'sender':
        #print('Sender found:', name)
        if memberName == 'transfer':
 # Building on the assumption that the function call is msg.sender.transfer()
 # get the list of all declared addresses
            sender_dict = VariableComponent['AddressVariables']
            sender_list = list(sender_dict.keys())
            #print('Sender list:', sender_list)
            return {'name': name, 'type': 'mapping_transfer', 'sender_list': sender_list}
 # {'name': 'sender', 'type': 'transfer', 'sender_list': ['operator', 'player']}
            asdf

    else:
        #return str(name + '.' + memberName)
        if memberName == 'transfer':
            return {'name':name + memberName , 'type': 'transfer'}
        else:
            return memberName

def handleIdentifier(node):
    assert ntype(node) == 'Identifier', "Node not Identifier"
    name = node['name']
    return name

def handleVariableDeclaration(node):
    assert ntype(node) == 'VariableDeclaration', " Node not VariableDeclaration"
    name = node['name']
    var_type = lookup_table[ntype(node['typeName'])](node['typeName'])
    initial_value = str()
    if var_type == 'bool':
        if 'value' in node and node['value'] is not None:
            #print('Boolean variable found:', name)
            initial_value = lookup_table[ntype(node['value'])](node['value'])
            #print('Initial value:', initial_value)


    # checking if var_type is already defined as a struct
    #print('Variable name:', name)
    #print('Variable type:', var_type)
    if not isinstance(var_type, dict):
        if var_type in VariableComponent['StructVariables'] :
            #print('Struct found', var_type)
            #print(VariableComponent['StructVariables'][var_type])
            struct_var_attributes = VariableComponent['StructVariables'][var_type]

            # Now generating the names for object of the struct
            for attr in struct_var_attributes:
                var_struct = name + "_" + attr
                #print('Struct variable:', var_struct)
                # Now adding the struct variable to the VariableComponent with value as the attribute of the struct

                # replace the attr with var_struct
                base_attr_xml = copy.deepcopy(VariableComponent[attr])
                base_attr_xml_updated = replace_identifier(base_attr_xml, attr, var_struct)

                VariableComponent[var_struct] = base_attr_xml_updated
                #print('Struct variable added to VariableComponent:', VariableComponent[var_struct])



    #return str(var_type + " : " + name)
    if isinstance(var_type, dict):
        if var_type['ntype'] == 'Mapping':
            # print("Mapping found")
            # print(var_type['key_value'])
            packet = {'name': name, 'type': var_type['ntype'], 'key_value': var_type['key_value']}

            #print(packet)


    else:
        packet = {'name': name, 'type': var_type}
    #print(packet)

    if superVariableDeclaration(packet, initial_value = initial_value):
        return  True
    return(name)

def handleElementaryTypeName(node):
    assert ntype(node) == 'ElementaryTypeName', "Node not ElementaryTypeName"
    name = node['name']
    return name

def handleUserDefinedTypeName(node):
    assert ntype(node) == 'UserDefinedTypeName', "Node not UserDefinedTypeName"
    name = node['pathNode']['name']
    return name

def handleEnumValue(node):
    assert ntype(node) == 'EnumValue', "Node not EnumValue"
    name = node['name']
    return  name

def handleEnumDefinition(node):
    assert ntype(node) == 'EnumDefinition', "Node not EnumDefinition"
    name = node['name']
    members = []
    for m_node in node['members']:
        m_name = lookup_table[ntype(m_node)](m_node)
        members.append(m_name)
    packet = {'name': name, 'members': members}
    superEnumDefinition(packet)
    #return str ( name + " : " + str(members))

def handleIdentifier(node):
    assert ntype(node) == 'Identifier', "Node not Identifier"
    name = node['name']
    return name

def handleBinaryOperation(node):
    assert ntype(node) == 'BinaryOperation', "Node not BinaryOperation"
    lhs = lookup_table[ntype(node['leftExpression'])](node['leftExpression'])
    op = node['operator']
    rhs = lookup_table[ntype(node['rightExpression'])](node['rightExpression'])

    # if op == "||" then convert to "|" and similarly if op == "&&" then convert to "&"
    if op == "||":
        op = "|"
    elif op == "&&":
        op = "&"

    # Case when lhs is a boolean value and used in a binary operation like if(isBuyerIn) then convert to isBuyerIn == true
    if isinstance(lhs, str) and (lhs in VariableComponent['BooleanVariables']) and (rhs != 'true' or rhs != 'false'):
        lhs_name = lhs
        lhs = wmodify_assignment(lhs, "==", "true")

    if isinstance(rhs, str) and (rhs in VariableComponent['BooleanVariables']) and (lhs_name in VariableComponent['BooleanVariables']):
        #print("Both are boolean variables")
        rhs = wmodify_assignment(rhs, "==", "true")

    exp = wmodify_assignment(lhs, op, rhs)

    return exp


def handleFunctionCall(node):
    assert ntype(node) == 'FunctionCall', "Node not FunctionCall"
    name = lookup_table[ntype(node['expression'])](node['expression'])
    kind = str()
    if 'kind' in node:
        kind = node['kind']

    if name == 'keccak256':
        arg = node['arguments'][0]['arguments'][0]['name']
    else:
        if len(node['arguments']) == 0:
            arg = ""
        else:
            arg_list = []
            arg = lookup_table[ntype(node['arguments'][0])](node['arguments'][0])


    if isinstance(name, dict):
        if 'sender_list' in name:
            return_dict = {'ntype': ntype(node), 'name' : name['name'], 'args' : arg, 'type': name['type'], 'sender_list': name['sender_list']}
            #print(return_dict)

            return return_dict
        else:
            return {'ntype': ntype(node), 'name' : name['name'], 'args' : arg, 'type': name['type']}
    else:
        return {'ntype': ntype(node), 'name' : name, 'args' : arg} # args value : msg.sender


def handleExpressionStatement(node):
    assert ntype(node) == 'ExpressionStatement', "Node not ExpressionStatement"
    exp = lookup_table[ntype(node['expression'])](node['expression'])
    return exp

def handlePlaceholderStatement(node):
    assert ntype(node) == 'PlaceholderStatement', "Node not PlaceholderStatement"
    return False

def handleReturn(node):
    assert ntype(node) == 'Return', "Node not Return"
    return False

def handleBlock(node):
    assert ntype(node) == 'Block', "Node not Block"
    statements = []
    for s in node['statements']:
        stmnt = lookup_table[ntype(s)](s)
        statements.append(stmnt)
    return  statements

def handleParameterList(node):
    assert ntype(node) == 'ParameterList', "Node not ParameterList"
    parameters = {}
    for p in node['parameters']:
        param_name = lookup_table[ntype(p)](p) # name of the parameter
        param_type = lookup_table[ntype(p['typeName'])](p['typeName']) # type of the parameter
        parameters[param_name] = param_type # add the parameter to the dictionary

    # need to return the parameters as a dictionary
    #params = ', '.join(parameters)
    return parameters

def handleModifierDefinition(node):
    assert ntype(node) == 'ModifierDefinition', "Node not ModifierDefinition"
    packet = {}
    packet['body'] = lookup_table[ntype(node['body'])](node['body'])

    packet['params'] = lookup_table[ntype(node['parameters'])](node['parameters'])
    packet['name'] = node['name']
    super_struct = superModifierDefinition(packet)
    return super_struct

def handleFunctionDefinition(node):
    assert ntype(node) == 'FunctionDefinition', "Node not FunctionDefinition"
    global current_function_name

    kind = node.get('kind', 'function')
    if kind == 'constructor':
        return
    if kind == 'receive':
        current_function_name = 'receive'
    elif node['name']:
        current_function_name = node['name']

    packet = {}
    packet['body'] = lookup_table[ntype(node['body'])](node['body'])
    packet['params'] = lookup_table[ntype(node['parameters'])](node['parameters'])
    packet['name'] = node['name']

    if packet['name'] == '' and kind != 'receive':
        return
    if kind == 'receive':
        packet['name'] = 'receive'

    current_function_name = packet['name']
    packet['modifiers'] = [lookup_table[ntype(m)](m) for m in node['modifiers']]
    super_struct = superFunctionDefinition(packet)
    return super_struct

def handleAssignment(node):
    assert ntype(node) == 'Assignment', "Node not Assignment"
    lhs = lookup_table[ntype(node['leftHandSide'])](node['leftHandSide'])  # lhs can be indexAccess returning this  {'operator': 'withdrawable_operator', 'player': 'withdrawable_player'}

    if isinstance(lhs, str):
        mapping_vars = {v for inner in VariableComponent['MappingVariables'].values()
                        for v in inner.values()}
        if lhs in mapping_vars:
            return {'ntype': ntype(node), 'kind': 'simple', 'exp': wmodify_assignment(lhs, '=', '1')}

    op = node['operator']
    rhs = lookup_table[ntype(node['rightHandSide'])](node['rightHandSide'])
    #print('RRHHSS ----', rhs)
    node_rhs = node['rightHandSide']
    kind = 'simple'

    if isinstance(lhs,dict):
        #print('lhs is dict:', lhs)
        if ntype(node['leftHandSide']) == 'IndexAccess':
            #print('lhs is IndexAccess')

            index_node = node['leftHandSide']
            index_node_expression = lookup_table[ntype(index_node['indexExpression'])](index_node['indexExpression'])

            if index_node_expression == 'sender':
                #print('RRHHSS ----', rhs)
                #print('LHSSSS------', lhs)

                lhs_TEMP = {}
                for address, mapping_address_variable in lhs.items():
                    mapping_address_variable_TEMP = mapping_address_variable + 'TEMP'
                    lhs_TEMP[address]  = mapping_address_variable_TEMP

                    if mapping_address_variable_TEMP not in VariableComponent:
                        print('MAPPING VARIABLE ABSENT', mapping_address_variable_TEMP)

                        lhs_variable_definition = VariableComponent[mapping_address_variable]
                        mapping_address_variable_TEMP_definition  = copy.deepcopy(lhs_variable_definition)
                        lhs_variable_temp_definition = replace_with_temp(mapping_address_variable_TEMP_definition, mapping_address_variable,
                                                                         mapping_address_variable_TEMP)

                        VariableComponent[mapping_address_variable_TEMP] = lhs_variable_temp_definition

    # Add the variable - variableTEMP pair to GeneralVariableTEMP
                    global current_function_name
                    #print('FUNCTION NAME-----', current_function_name)
                    if current_function_name not in FunctionVariablesTEMP:
                        FunctionVariablesTEMP[current_function_name] = {}
                    FunctionVariablesTEMP[current_function_name][mapping_address_variable] = mapping_address_variable_TEMP

                exp = generate_mapping_assignment_expression(lhs_TEMP, 'sender', rhs)
                #print('Mapping expression:', exp)
                #print(asdf)

                return {'ntype': ntype(node), 'kind': 'mapping_assignment_check', 'expression': exp}

    if isinstance(rhs, dict):
        if rhs['ntype'] == 'FunctionCall' and node_rhs['kind'] != 'structConstructorCall':
            #rhs = str(rhs['name'] + "(" + rhs['args'] + ")")
            #exp = str(lhs + " " +op + " " + rhs['name'] + "(" + rhs['args'] + ")")
            exp = wmodify_assignment(lhs, op, rhs)

        elif rhs['ntype'] == 'FunctionCall' and node_rhs['kind'] == 'structConstructorCall':
            var_name = lhs # wager
            exp = []
            for index, attr_name in enumerate(node_rhs['names']):
                struct_var = var_name + "_" + attr_name
                node_rhs_arg_value  = lookup_table[ntype(node_rhs['arguments'][index])](node_rhs['arguments'][index])
                #print(struct_var + " = " + node_rhs_arg_value)
                exp.append(wmodify_assignment(struct_var, "=", node_rhs_arg_value))

            return {'ntype': ntype(node), 'kind' : 'structConstructorCall', 'exp' : exp}


        elif rhs['ntype'] == 'Conditional':
            kind = 'conditional'
            #print(ntype(node))
            exp = wmodify_assignment(lhs,"==", rhs['true_exp'], **{'ntype': ntype(node), 'kind': 'conditional', 'name' : lhs, 'condition': rhs['condition'], 'true_exp': rhs['true_exp'], 'false_exp': rhs['false_exp']})
            #print('Expression conditional:',exp)
            return {'ntype': ntype(node), 'kind' : 'conditional', 'expression' : exp}

            #return {'ntype': ntype(node), 'kind' : kind, 'lhs' : lhs, 'op' : op, 'condition' : rhs['condition'], 'true_exp' : rhs['true_exp'], 'false_exp' : rhs['false_exp']}
    elif isinstance(rhs, ET.Element) or isinstance(rhs, str):
        exp = wmodify_assignment(lhs, op, rhs)



    #exp = wmodify_assignment(lhs, op, rhs)
    return  {'ntype': ntype(node), 'kind' : kind, 'exp' : exp}

def handleModifierInvocation(node):
    assert ntype(node) == 'ModifierInvocation', "Node not ModifierInvocation"
    name = lookup_table[ntype(node['modifierName'])](node['modifierName'])
    if 'arguments' in node:
        args = [lookup_table[ntype(a)](a) for a in node['arguments']]
        return {'name':name, 'args': args}
    else:
        return {'name':name}

def handleIdentifierPath(node):
    assert ntype(node) == 'IdentifierPath', "Node not IdentifierPath"
    name = node['name']
    return name

def handleLiteral(node):
    assert ntype(node) == 'Literal', "Node not Literal"
    value = node['value']
    return value

def handleElementaryTypeNameExpression(node):
    assert ntype(node) == 'ElementaryTypeNameExpression', "Node not ElementaryTypeNameExpression"
    return ""

def handleVariableDeclarationStatement(node):
    assert ntype(node) == 'VariableDeclarationStatement', "Node not VariableDeclarationStatement"

    # assumption - there is only one variable declaration here
    name = lookup_table[ntype(node['declarations'][0])](node['declarations'][0]) # has oldBidder
    init_value = lookup_table[ntype(node['initialValue'])](node['initialValue']) # nodeType == 'IndexAccess' value = {'operator': 'withdrawable_operator', 'player': 'withdrawable_player'} # currentBidde

    if isinstance(init_value, dict):
        #print('Dict found:', init_value)
        if 'ntype' in init_value and init_value['ntype'] == 'Conditional':

            exp = wmodify_assignment(name,"==", init_value['true_exp'], **{'ntype': ntype(node), 'kind': 'conditional', 'name' : name, 'condition': init_value['condition'], 'true_exp': init_value['true_exp'], 'false_exp': init_value['false_exp']})


            return {'ntype': ntype(node), 'kind' : 'conditional', 'expression' : exp}

        elif ntype(node['initialValue']) == 'IndexAccess':
            index_node = node['initialValue']
            index_node_expression = lookup_table[ntype(index_node['indexExpression'])](index_node['indexExpression'])
# trialzone 6-------
            if index_node_expression == 'sender':
                #print('INITTTTT---------', init_value)

                exp = generate_mapping_expression(init_value, 'sender', name)
                print('NAMEEEEE-------------', name)
                return {'ntype': ntype(node), 'kind': 'mapping_assignment_check', 'expression': exp}

    elif isinstance(init_value, list):
        #print('List found:', init_value)
        exp = wmodify_assignment(name, "==", init_value)


        #print(asdf)
    elif init_value in AddressVariables:
        #print('Address variable found:', init_value)
        #print('Value for address variable:', AddressVariables[init_value])
        #print(VariableComponent)

        address_variable_value = init_value
        exp = wmodify_assignment(name, "=", address_variable_value)
        return {'ntype': ntype(node), 'kind': 'address_variable_assignment', 'expression': exp}


    elif init_value in IntegerVariables:
        print('Integer variable found:', init_value)
        init_value = str(init_value)
        exp = wmodify_assignment(name, "=", init_value)
        return {'ntype': ntype(node), 'kind': 'integer_variable_assignment', 'expression': exp}


    else:
        return False

def handleConditional(node):
    assert ntype(node) == 'Conditional', "Node not conditional"
    condition = lookup_table[ntype(node['condition'])](node['condition'])
    false_exp = lookup_table[ntype(node['falseExpression'])](node['falseExpression'])
    true_exp = lookup_table[ntype(node['trueExpression'])](node['trueExpression'])
    #return  str("(" + condition + ")" + "? " + true_exp + " : " + false_exp + ";")
    #print('true_exp:', true_exp)
    #print('false_exp:', false_exp)
    return {'ntype': ntype(node), 'condition' : condition, 'true_exp' : true_exp, 'false_exp' : false_exp}


def handleTupleExpression(node):
    assert ntype(node)  == 'TupleExpression', "Node not TupleExpression"
        # assumption - there is only expression here
    comp = lookup_table[ntype(node['components'][0])](node['components'][0])
    #print(comp)
    return comp

def handleIfStatement(node):
    assert ntype(node) == 'IfStatement', "Node not IfStatement"
    true_condition = lookup_table[ntype(node['condition'])](node['condition'])
    if isinstance(true_condition, str): # if the condition is a string then check if it is a boolean variable. Example: if(isBuyerIn)
        if true_condition in VariableComponent['BooleanVariables']:
            true_condition = wmodify_assignment(true_condition, "==", "true")

    false_condition = ET.Element("UnaryExpression", Operator = "!")
    false_condition.append(true_condition)

    has_false_body = 'falseBody' in node and node['falseBody'] is not None
    if has_false_body:
        false_body = lookup_table[ntype(node['falseBody'])](node['falseBody'])
    #print(false_body)
    true_body = lookup_table[ntype(node['trueBody'])](node['trueBody'])
    #print(true_body)
    #return  str("if" + "( " + condition+" )" + "{\n\t"  + true_body + "\n" + "} " + "else "  + "{\n\t" + false_body + "\n" + "} ")
    if has_false_body:
        return {'ntype': ntype(node), 'true_condition' : true_condition,'false_condition': false_condition, 'true_body' : true_body, 'false_body' : false_body}
    else:
        return {'ntype': ntype(node), 'true_condition' : true_condition,'true_body' : true_body, 'false_condition': false_condition}


def handleStructDefinition(node):
    assert ntype(node) == 'StructDefinition', "Node not StructDefinition"
    members = [lookup_table[ntype(m)](m) for m in node['members']]
    #members = "\n".join(members)
    name = node['name']
    packet = {'name': name, 'members': members}
    #print(packet)
    if superStructDefinition(packet):
        return True
    #return str (name + " {\n" + members + "\n}")

def handleMapping(node):
    assert ntype(node) == 'Mapping', "Node not Mapping"
    key = lookup_table[ntype(node['keyType'])](node['keyType'])
    value = lookup_table[ntype(node['valueType'])](node['valueType'])
    key_value = str()
    node_type = 'Mapping'
    # return  str( key + " => "  + value)
    # Currently only handling the key value pair of type address -> uint
    # We assume that all the variable of 'address' type have been declared in the contract before mapping
    if key == 'address' and (value == 'uint' or value == 'uint256'):
        key_value  = 'address_uint'
    packet = {'ntype':node_type, 'key_value': key_value}
    #print(packet)
    return packet




def handleIndexAccess(node):
    assert ntype(node) == 'IndexAccess' , "Node not IndexAccess"
    base = lookup_table[ntype(node['baseExpression'])](node['baseExpression']) # has withdrawable
    if base in VariableComponent['MappingVariables']:
        #print(base + ' : ' ,VariableComponent['MappingVariables'][base])
        #print('Mapping variable found:', base)
        index = lookup_table[ntype(node['indexExpression'])](node['indexExpression'])
        #print('Index:', index)
        if index == 'sender': # Building on the assumption that sender is an address
            mapping_variable_dict = VariableComponent['MappingVariables'][base] # has {'operator': 'withdrawable_operator', 'player': 'withdrawable_player'}
            #for sender_address in mapping_variable_dict.keys():
                #print('Sender Address: ', sender_address)
            return mapping_variable_dict



    return  str( base + "_" + index)


lookup_table = {}

lookup_table['MemberAccess'] = handleMemberAccess
lookup_table['Identifier'] = handleIdentifier
lookup_table['BinaryOperation'] = handleBinaryOperation
lookup_table['ElementaryTypeName'] = handleElementaryTypeName
lookup_table['VariableDeclaration'] = handleVariableDeclaration
lookup_table['UserDefinedTypeName'] = handleUserDefinedTypeName
lookup_table['EnumValue'] = handleEnumValue
lookup_table['EnumDefinition'] = handleEnumDefinition
lookup_table['Identifier'] = handleIdentifier
lookup_table['FunctionCall'] = handleFunctionCall
lookup_table['ExpressionStatement'] = handleExpressionStatement
lookup_table['PlaceholderStatement'] = handlePlaceholderStatement
lookup_table['Block'] = handleBlock
lookup_table['ModifierDefinition'] = handleModifierDefinition
lookup_table['ParameterList'] = handleParameterList
lookup_table['FunctionDefinition'] = handleFunctionDefinition
lookup_table['Assignment'] = handleAssignment
lookup_table['ModifierInvocation'] = handleModifierInvocation
lookup_table['IdentifierPath'] = handleIdentifierPath
lookup_table['Literal'] = handleLiteral
lookup_table['ElementaryTypeNameExpression'] = handleElementaryTypeNameExpression
lookup_table['VariableDeclarationStatement'] = handleVariableDeclarationStatement
lookup_table['Conditional'] = handleConditional
lookup_table['TupleExpression'] = handleTupleExpression
lookup_table['IfStatement'] = handleIfStatement
lookup_table['StructDefinition'] = handleStructDefinition
lookup_table['Mapping'] = handleMapping
lookup_table['IndexAccess'] = handleIndexAccess
lookup_table['Return'] = handleReturn


