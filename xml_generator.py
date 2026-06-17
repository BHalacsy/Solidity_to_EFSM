from add_events_nodes import *
import xml.etree.ElementTree as ET
from datetime import datetime
import os
import copy

# pre_supremica is imported from add_events_nodes.py
# pre_supremica is in the form of a dictionary

#print(pre_supremica)

contract_module_name = os.path.splitext(os.path.basename(contract_file))[0]
Module = ET.Element("Module", Name = contract_module_name)

# Adding the EventDeclList to the Module
xml_EventDecl = pre_supremica['Events']
Module.append(xml_EventDecl)

# Adding event Name = ":accepting", kind = "PROPOSITION" to the EventDeclList
EventDecl_accepting = ET.SubElement(xml_EventDecl, "EventDecl", Kind = "PROPOSITION", Name = ":accepting")

ComponentList = ET.SubElement(Module, "ComponentList")

# Here we are specifying the xmlns attribute that we have to add
xmlns_uris = {"":"http://waters.sourceforge.net/xsd/module",
    ':B':"http://waters.sourceforge.net/xsd/base"}


# Constants used:
ONE = "1"
EVENT_END = "X"
EVENT_FAIL = "Fail"
# This is a function to add the xmlns attribute to the root node which is "Module"
def add_XMLNS_attributes(tree, xmlns_uris_dict):
    if not ET.iselement(tree):
        tree = tree.getroot()
    for prefix, uri in xmlns_uris_dict.items():
        tree.attrib['xmlns' + prefix] = uri

add_XMLNS_attributes(Module, xmlns_uris)

# Collect variable names that appear in at least one EFSM transition action.
# Supremica treats VariableComponents with no events as isolated automata and warns.
# Only outputting variables actually written avoids this.
def vars_referenced_in_efsm(data):
    referenced = set()
    for efsm_name, details in data.get('Components', {}).items():
        if efsm_name == 'VariableComponent' or not isinstance(details, dict):
            continue
        edge_list_xml = details.get('edge_list')
        if not ET.iselement(edge_list_xml):
            continue
        for gab in edge_list_xml.iter('GuardActionBlock'):
            for si in gab.iter('SimpleIdentifier'):
                name = si.get('Name')
                if name:
                    referenced.add(name)
    return referenced

written_vars = vars_referenced_in_efsm(Supremica)

# Loop to add VariableComponent
declared_vars = set()
for var, val in pre_supremica['Components']['VariableComponent'].items():
    #VariableComponent = ET.SubElement(ComponentList, "VariableComponent",  Name = var)
    #print(var)
    #print('-----------------')
    if not isinstance(val, dict):
        if var not in written_vars:
            continue
        xml_VariableComponent = pre_supremica['Components']['VariableComponent'][var]
        #print(str(xml_VariableComponent))
        ComponentList.append(xml_VariableComponent)
        declared_vars.add(var)

enum_values = {
    member
    for members in VariableComponent['EnumVariables'].values()
    for member in members
}

# Add integer [0,1] VariableComponents for any referenced variable not already declared.
# This handles cases where the pipeline generates a mapping variable name that doesn't
# match a declared address variable (e.g. a withdrawable_<address> slot).
# Exclude enum members and address symbols — they are values, not variables.
addr_sym_set = set(VariableComponent['AddressVariables'].values())
for var in sorted(written_vars - declared_vars - {'sender', 'value'} - enum_values - addr_sym_set):
    vc = ET.Element("VariableComponent", Name=var)
    vr = ET.SubElement(vc, "VariableRange")
    vr.append(wmodify_assignment("0", "..", "1"))
    vi = ET.SubElement(vc, "VariableInitial")
    vi.append(wmodify_assignment(var, "==", "0"))
    ComponentList.append(vc)

#############################################################################################################

# Adding variable 'value' to the VariableComponent

VariableComponent_value = ET.Element("VariableComponent",  Name = "value")

VariableRange_value = ET.SubElement(VariableComponent_value, "VariableRange")
BinaryExpression_value = wmodify_assignment("0", "..", "1")
VariableRange_value.append(BinaryExpression_value)


VariableInitial_value = ET.SubElement(VariableComponent_value, "VariableInitial")
BinaryExpression_value_init = wmodify_assignment("value", "==", "0")
VariableInitial_value.append(BinaryExpression_value_init)

ComponentList.append(VariableComponent_value)

#############################################################################################################

# Adding variable 'sender' to the VariableComponent

VariableComponent_sender = ET.Element("VariableComponent",  Name = "sender")
VariableRange_sender = ET.SubElement(VariableComponent_sender, "VariableRange")
EnumSetExpression_sender = ET.SubElement(VariableRange_sender, "EnumSetExpression")

sender_list = VariableComponent ['AddressVariables']
# sender_list is a dictionary of address variables
# {'operator': 'x0001', 'player': 'x0002'}

# Scan the constructor for address variables assigned msg.sender
constructor_addr_inits = {}
for n in sol_list:
    if n.get('nodeType') != 'FunctionDefinition' or n.get('kind') != 'constructor':
        continue
    for stmt in n.get('body', {}).get('statements', []):
        expr = stmt.get('expression', {})
        if expr.get('nodeType') != 'Assignment':
            continue
        lhs = expr.get('leftHandSide', {})
        rhs = expr.get('rightHandSide', {})
        is_msg_sender = (
            rhs.get('nodeType') == 'MemberAccess'
            and rhs.get('memberName') == 'sender'
            and rhs.get('expression', {}).get('name') == 'msg'
        )
        if lhs.get('name') and is_msg_sender and lhs['name'] in AddressVariables:
            constructor_addr_inits[lhs['name']] = 'x0001'
print('Constructor address inits:', constructor_addr_inits)

# Address padding when needed
addr_syms = list(set(sender_list.values()))
constructor_aliases = (
    len(constructor_addr_inits) >= 2
    and len(set(constructor_addr_inits.values())) < len(constructor_addr_inits)
)
if constructor_aliases:
    max_sym = max((int(a[4:]) for a in addr_syms if len(a) == 5 and a.startswith('x000')), default=0)
    while len(addr_syms) < 3:
        max_sym += 1
        addr_syms.append(f'x000{max_sym}')

for address in addr_syms:
    EnumSetExpression_sender.append(ET.Element("SimpleIdentifier", Name = address))

# adding initial value to 'sender'
# Ideally this value should be the one which is assigned in the constructor of the contract
VariableInitial_sender = ET.SubElement(VariableComponent_sender, "VariableInitial")
BinaryExpression_sender_init = wmodify_assignment("sender", "==", "x0001")
VariableInitial_sender.append(BinaryExpression_sender_init)

ComponentList.append(VariableComponent_sender)

#############################################################################################################

# Replacing address domain for all address variables
# Do we have an address list ?:
print(AddressVariables)

for address_name, address_value in VariableComponent['AddressVariables'].items():
    if address_name in VariableComponent:
        #print(f'Updating address: {address_name}')

        # Get the VariableComponent for the address
        xml_VariableComponent = VariableComponent[address_name]

        # Remove existing VariableRange (if required)
        existing_ranges = xml_VariableComponent.findall("VariableRange")
        for existing_range in existing_ranges:
            xml_VariableComponent.remove(existing_range)

        # Remove existing VariableInitial (to ensure correct order when re-adding)
        existing_initial = xml_VariableComponent.find("VariableInitial")
        if existing_initial is not None:
            xml_VariableComponent.remove(existing_initial)

        # Add VariableRange first
        xml_variableRange = ET.SubElement(xml_VariableComponent, "VariableRange")
        xml_EnumSetExpression = ET.SubElement(xml_variableRange, "EnumSetExpression")

        # Copy the EnumSetExpression from sender
        for child in EnumSetExpression_sender:
            xml_EnumSetExpression.append(ET.Element("SimpleIdentifier", Name=child.attrib["Name"]))

        # Add VariableInitial second — prefer constructor-derived value over declaration order
        init_val = constructor_addr_inits.get(address_name, address_value)
        xml_VariableInitial = ET.SubElement(xml_VariableComponent, "VariableInitial")
        xml_VariableInitial.append(wmodify_assignment(address_name, "==", init_val))

# Widen TEMP variables for address-typed state variables to the full address domain.
for fn_temps in FunctionVariablesTEMP.values():
    for orig_var, temp_var in fn_temps.items():
        if orig_var in VariableComponent['AddressVariables'] and temp_var in VariableComponent:
            xml_vc = VariableComponent[temp_var]
            for er in xml_vc.findall("VariableRange"):
                xml_vc.remove(er)
            ei = xml_vc.find("VariableInitial")
            if ei is not None:
                xml_vc.remove(ei)
            xml_vr = ET.SubElement(xml_vc, "VariableRange")
            xml_ese = ET.SubElement(xml_vr, "EnumSetExpression")
            for child in EnumSetExpression_sender:
                xml_ese.append(ET.Element("SimpleIdentifier", Name=child.attrib["Name"]))
            xml_vi = ET.SubElement(xml_vc, "VariableInitial")
            xml_vi.append(wmodify_assignment(temp_var, "==", VariableComponent['AddressVariables'][orig_var]))

#############################################################################################################

for efsm in pre_supremica['Components']:
    SimpleComponent = None
    if efsm != 'VariableComponent':
        if efsm == "":
            efsm = ""
            #global SimpleComponent
            SimpleComponent = ET.SubElement(ComponentList, "SimpleComponent",  Kind = "PLANT",Name = efsm)
        else:
            #global SimpleComponent
            SimpleComponent = ET.SubElement(ComponentList, "SimpleComponent",  Kind = "PLANT", Name = efsm)

        Graph = ET.SubElement(SimpleComponent, "Graph")

        xml_NodeList = pre_supremica['Components'][efsm]['node_list']
        xml_EdgeList = pre_supremica['Components'][efsm]['edge_list']

        Graph.append(xml_NodeList)
        Graph.append(xml_EdgeList)

#############################################################################################################

# Expand the range (and optionally set initial value) of an integer VariableComponent.
def override_variable_range(var_name, lo, hi, initial=None):
    xml_vc = VariableComponent.get(var_name)
    if xml_vc is None or not ET.iselement(xml_vc):
        # Fall back to scanning ComponentList for auto-declared variables
        for child in ComponentList:
            if child.get('Name') == var_name and child.tag == 'VariableComponent':
                xml_vc = child
                break
    if xml_vc is None:
        print(f'[warn] override_variable_range: {var_name} not found')
        return

    for vr in xml_vc.findall('VariableRange'):
        xml_vc.remove(vr)
    for vi in xml_vc.findall('VariableInitial'):
        xml_vc.remove(vi)

    new_vr = ET.SubElement(xml_vc, 'VariableRange')
    new_vr.append(wmodify_assignment(str(lo), '..', str(hi)))

    init_val = str(initial) if initial is not None else str(lo)
    new_vi = ET.SubElement(xml_vc, 'VariableInitial')
    new_vi.append(wmodify_assignment(var_name, '==', init_val))

    if 'IntegerVariables' in VariableComponent:
        VariableComponent['IntegerVariables'][var_name] = [lo, hi]

    print(f'[fix] {var_name} range overridden to [{lo},{hi}], initial={init_val}')

# Parse a (sender == addr) & (primedVar' == rhs) leaf.
# Returns a list with one (addr_name, primed_var_name, rhs_element) triple,
# or an empty list if the node doesn't match the expected pattern.
def parse_primed_and_leaf(and_node):
    children = list(and_node)
    if len(children) != 2:
        return []
    addr_name = primed_var = rhs_el = None
    for child in children:
        if child.tag != 'BinaryExpression' or child.get('Operator') != '==':
            continue
        cc = list(child)
        if len(cc) != 2:
            continue
        if (cc[0].tag == 'SimpleIdentifier' and cc[0].get('Name') == 'sender'
                and cc[1].tag == 'SimpleIdentifier'):
            addr_name = cc[1].get('Name')
        elif (cc[0].tag == 'UnaryExpression' and cc[0].get('Operator') == "'"
              and list(cc[0]) and list(cc[0])[0].tag == 'SimpleIdentifier'):
            primed_var = list(cc[0])[0].get('Name')
            rhs_el = cc[1]
    if addr_name and primed_var and rhs_el is not None:
        return [(addr_name, primed_var, rhs_el)]
    return []

# Recursively walk a guard tree of | nodes and collect all (addr, primed_var, rhs) triples.
def parse_primed_or_tree(node):
    if node.tag == 'BinaryExpression' and node.get('Operator') == '|':
        result = []
        for child in node:
            result.extend(parse_primed_or_tree(child))
        return result
    if node.tag == 'BinaryExpression' and node.get('Operator') == '&':
        return parse_primed_and_leaf(node)
    return []

# Replace every primed-variable guard in every plant EFSM with per-sender split edges.
def auto_fix_primed_guards():
    for fn_name, details in list(Supremica.get('Components', {}).items()):
        if fn_name == 'VariableComponent' or not isinstance(details, dict):
            continue
        edge_list = details.get('edge_list')
        if edge_list is None or not ET.iselement(edge_list):
            continue

        for edge in list(edge_list):
            gab = edge.find('GuardActionBlock')
            if gab is None:
                continue
            guards_el = gab.find('Guards')
            if guards_el is None or len(guards_el) == 0:
                continue

            guard_root = guards_el[0]
            if guard_root.find(".//UnaryExpression[@Operator=\"'\"]") is None:
                continue

            pairs = parse_primed_or_tree(guard_root)
            if not pairs:
                continue

            src = edge.get('Source')
            tgt = edge.get('Target')
            label_block = edge.find('LabelBlock')
            existing_actions = gab.find('Actions')

            edge_list.remove(edge)

            for addr_name, primed_var, rhs_el in pairs:
                new_edge = ET.Element('Edge', Source=src, Target=tgt)
                new_edge.append(copy.deepcopy(label_block))

                new_gab = ET.SubElement(new_edge, 'GuardActionBlock')

                new_guards = ET.SubElement(new_gab, 'Guards')
                g = ET.SubElement(new_guards, 'BinaryExpression', Operator='==')
                ET.SubElement(g, 'SimpleIdentifier', Name='sender')
                ET.SubElement(g, 'SimpleIdentifier', Name=addr_name)

                new_actions = ET.SubElement(new_gab, 'Actions')
                a = ET.SubElement(new_actions, 'BinaryExpression', Operator='=')
                ET.SubElement(a, 'SimpleIdentifier', Name=primed_var)
                a.append(copy.deepcopy(rhs_el))

                if existing_actions is not None:
                    for act in existing_actions:
                        new_actions.append(copy.deepcopy(act))

                edge_list.append(new_edge)

            event_names = [si.get('Name') for si in label_block.findall('SimpleIdentifier')]
            print(f'[auto-fix primed] {fn_name}: {event_names} → {len(pairs)} per-sender edges')


auto_fix_primed_guards()
override_variable_range('timestamp',    0, 3)
override_variable_range('expiresAt',   0, 3, initial=2)

for v in ('totalBids', 'totalBidsTEMP',
           'bidIndex', 'bidIndexTEMP',
           'refundProgress', 'refundProgressTEMP'):
    override_variable_range(v, 0, 3)
override_variable_range('totalForAuction', 0, 3, initial=3)


# Build AssignMsg component

def count_statements_in_edge_list(supremica_data):
    """
    Identifies functions with `node_list` and `edge_list` where `edge_list` has more than one statement.

    :param supremica_data: The input data structure containing `node_list` and `edge_list`.
    :return: A dictionary with function names as keys and the count of statements in their `edge_list` as values.
    """
    components = supremica_data.get("Components", {})
    functions_with_multiple_statements = {}

    # Iterate through functions in components
    for function_name, details in components.items():
        if isinstance(details, dict) and "node_list" in details and "edge_list" in details:
            # Parse the edge_list XML
            edge_list = details["edge_list"]
            # Simulate parsing <Edge> elements (ensure edge_list is valid XML)
            edge_elements = ET.ElementTree(edge_list).findall("./Edge")
            edge_count = len(edge_elements)  # Count <Edge> elements

            # Check if there is more than one statement
            if edge_count > 1:
                functions_with_multiple_statements[function_name] = edge_count

    return functions_with_multiple_statements


# List of events ending with one for functions with more than on statement in edge_list

def extract_events_ending_with(edge_list, suffix):
    """
    Extracts events from the edge_list that end with the digit 1.

    :param edge_list: The edge_list XML element.
    :return: A list of event names ending with '1'.
    """
    events = set()
    #print(edge_list)
    for edge in ET.ElementTree(edge_list).findall("./Edge/LabelBlock/SimpleIdentifier"):
        event_name = edge.get("Name")
        if event_name and event_name.endswith(suffix):
            if event_name not in events:
                events.add(event_name)
    return events


#############################################################################################################

print('______________________________________________________')
print( Supremica)

#############################################################################################################

# Get list of functions

function_list = []

for node in sol_list:
    if node['nodeType'] != 'FunctionDefinition':
        continue
    kind = node.get('kind', 'function')
    vis = node.get('visibility', '')
    if kind == 'constructor':
        continue
    if vis in ('public', 'external'):
        # receive/fallback have empty name; use kind as the EFSM name
        fn_name = node['name'] if node['name'] else kind
        if fn_name in pre_supremica['Components']:
            function_list.append(fn_name)

print(function_list)


def find_events_with_s0(supremica_data, function_names):

    components = supremica_data.get("Components", {})
    source_s0_events = set()  # Use set to ensure uniqueness
    target_s0_events = set()  # Use set to ensure uniqueness

    # Iterate through the provided function names
    for function_name in function_names:
        # Check if the function exists in Supremica components
        if function_name in components:
            details = components[function_name]
            if isinstance(details, dict) and "edge_list" in details:
                # Parse the edge_list XML
                edge_list = details["edge_list"]
                edges = list(ET.ElementTree(edge_list).findall("./Edge"))

                # Skip functions with one or zero edges
                if len(edges) <= 1:
                    continue

                # Process edges
                for edge in edges:
                    # Check if the edge has Source='S0'
                    if edge.get("Source") == "S0":
                        for event in edge.findall("./LabelBlock/SimpleIdentifier"):
                            source_s0_events.add(event.get("Name"))

                    # Check if the edge has Target='S0'
                    if edge.get("Target") == "S0":
                        for event in edge.findall("./LabelBlock/SimpleIdentifier"):
                            target_s0_events.add(event.get("Name"))

    return list(source_s0_events), list(target_s0_events)

source_s0, target_s0 = find_events_with_s0(Supremica, function_list)
print("Events with source 'S0':", source_s0)
print("Events with target 'S0':", target_s0)

#############################################################################################################

# Generate the XML structure for assignMsg component
def generate_address_xml(address_list):

    if not address_list:
        raise ValueError("Address list cannot be empty.")

    address_list  = list(set(address_list))

    # Start with the first address as the initial root of the expression
    current = ET.Element("BinaryExpression", {"Operator": "=="})

    # Add sender' == first_address
    unary_expression = ET.SubElement(current, "UnaryExpression", {"Operator": "'"})
    ET.SubElement(unary_expression, "SimpleIdentifier", {"Name": "sender"})
    ET.SubElement(current, "SimpleIdentifier", {"Name": address_list[0]})

    # For each subsequent address, create a new BinaryExpression with an OR ('|') operator
    for address in address_list[1:]:
        new_root = ET.Element("BinaryExpression", {"Operator": "|"})
        new_root.append(current)

        right_expression = ET.SubElement(new_root, "BinaryExpression", {"Operator": "=="})
        unary_expression = ET.SubElement(right_expression, "UnaryExpression", {"Operator": "'"})
        ET.SubElement(unary_expression, "SimpleIdentifier", {"Name": "sender"})
        ET.SubElement(right_expression, "SimpleIdentifier", {"Name": address})

        # Update the current root
        current = new_root

    # Return the generated tree as a string
    return    current
address_xml = generate_address_xml(list(sender_list.values()))

def generate_assignMsg_efsm(source_s0, target_s0):

    # Create the root element
    root = ET.Element("SimpleComponent", Kind="PLANT", Name="assignMsg")

    # Create the Graph element
    graph = ET.SubElement(root, "Graph")

    # Create NodeList
    node_list = ET.SubElement(graph, "NodeList")

    # Add SimpleNode S0
    s0_node = ET.SubElement(node_list, "SimpleNode", Initial="true", Name="S0")
    event_list = ET.SubElement(s0_node, "EventList")
    ET.SubElement(event_list, "SimpleIdentifier", Name=":accepting")
    point_geom = ET.SubElement(s0_node, "PointGeometry")
    ET.SubElement(point_geom, "Point", X="208", Y="128")
    label_geom = ET.SubElement(s0_node, "LabelGeometry", Anchor="NW")
    ET.SubElement(label_geom, "Point", X="0", Y="10")

    # Add SimpleNode S1
    s1_node = ET.SubElement(node_list, "SimpleNode", Name="S1")
    event_list = ET.SubElement(s1_node, "EventList")
    ET.SubElement(event_list, "SimpleIdentifier", Name=":accepting")
    point_geom = ET.SubElement(s1_node, "PointGeometry")
    ET.SubElement(point_geom, "Point", X="496", Y="304")
    label_geom = ET.SubElement(s1_node, "LabelGeometry", Anchor="NW")
    ET.SubElement(label_geom, "Point", X="0", Y="10")

    # Create EdgeList
    edge_list = ET.SubElement(graph, "EdgeList")

    # Add edges for source S0 -> S1
    if source_s0:
        edge = ET.SubElement(edge_list, "Edge", Source="S0", Target="S1")
        label_block = ET.SubElement(edge, "LabelBlock")
        for event in source_s0:
            ET.SubElement(label_block, "SimpleIdentifier", Name=event)
        label_geom = ET.SubElement(label_block, "LabelGeometry", Anchor="NW")
        ET.SubElement(label_geom, "Point", X="38", Y="-36")
        spline_geom = ET.SubElement(edge, "SplineGeometry")
        ET.SubElement(spline_geom, "Point", X="380", Y="182")

    # Add edges for target S1 -> S0
    if target_s0:
        edge = ET.SubElement(edge_list, "Edge", Source="S1", Target="S0")
        label_block = ET.SubElement(edge, "LabelBlock")
        for event in target_s0:
            ET.SubElement(label_block, "SimpleIdentifier", Name=event)
        label_geom = ET.SubElement(label_block, "LabelGeometry", Anchor="NW")
        ET.SubElement(label_geom, "Point", X="-57", Y="13")
        spline_geom = ET.SubElement(edge, "SplineGeometry")
        ET.SubElement(spline_geom, "Point", X="315", Y="256")

    # Add one assignSev edge per (sender_address, value) combination using explicit assignments.
    unique_addresses = addr_syms
    for addr in unique_addresses:
        for val in [0, 1]:
            edge = ET.SubElement(edge_list, "Edge", Source="S0", Target="S0")
            label_block = ET.SubElement(edge, "LabelBlock")
            ET.SubElement(label_block, "SimpleIdentifier", Name="assignSev")
            guard_action_block = ET.SubElement(edge, "GuardActionBlock")
            actions = ET.SubElement(guard_action_block, "Actions")
            sender_assign = ET.SubElement(actions, "BinaryExpression", Operator="=")
            ET.SubElement(sender_assign, "SimpleIdentifier", Name="sender")
            ET.SubElement(sender_assign, "SimpleIdentifier", Name=addr)
            value_assign = ET.SubElement(actions, "BinaryExpression", Operator="=")
            ET.SubElement(value_assign, "SimpleIdentifier", Name="value")
            ET.SubElement(value_assign, "IntConstant", Value=str(val))

    return root


#############################################################################################################

# xml testing
address_list = addr_syms

assignMsg_efsm = generate_assignMsg_efsm(source_s0, target_s0)

ComponentList.append(assignMsg_efsm)
add_events_to_xml('assignSev')

############################# TIME-ADVANCE MODELLING ########################################################
# For contracts that use time-gated modifiers, the
# 'now' or 'timestamp' variable must be able to advance non-deterministically.
time_var = ('now' if 'now' in written_vars
             else ('timestamp' if 'timestamp' in written_vars
                   else None))
MODEL_TIME_ADVANCE = time_var is not None

if MODEL_TIME_ADVANCE:
    # Attach advanceTime self-loops directly to the already-built assignMsg element.
    edge_list = assignMsg_efsm.find('.//EdgeList')
    edge = ET.SubElement(edge_list, "Edge", Source="S0", Target="S0")
    lb   = ET.SubElement(edge, "LabelBlock")
    ET.SubElement(lb, "SimpleIdentifier", Name="advanceTime")
    gab  = ET.SubElement(edge, "GuardActionBlock")
    acts = ET.SubElement(gab, "Actions")
    be  = ET.SubElement(acts, "BinaryExpression", Operator="=")
    ET.SubElement(be, "SimpleIdentifier", Name=time_var)
    rhs = ET.SubElement(be, "BinaryExpression", Operator="+")
    ET.SubElement(rhs, "SimpleIdentifier", Name=time_var)
    ET.SubElement(rhs, "IntConstant", Value="1")
    add_events_to_xml('advanceTime')

############################# GENERATE PROGRESS SPEC ########################################################
# Taken from automatic_spec branch
def generate_spec(event_name):

    root = ET.Element("SimpleComponent", Kind="SPEC", Name="ProgressSpec")
    graph = ET.SubElement(root, "Graph")

    node_list = ET.SubElement(graph, "NodeList")

    # S0 Node
    s0 = ET.SubElement(node_list, "SimpleNode", Initial="true", Name="S0")
    point_geometry_s0 = ET.SubElement(s0, "PointGeometry")
    ET.SubElement(point_geometry_s0, "Point", X="48", Y="-96")

    label_geometry_s0 = ET.SubElement(s0, "LabelGeometry", Anchor="NW")
    ET.SubElement(label_geometry_s0, "Point", X="0", Y="10")

    # S1 Node
    s1 = ET.SubElement(node_list, "SimpleNode", Name="S1")
    event_list_s1 = ET.SubElement(s1, "EventList")
    ET.SubElement(event_list_s1, "SimpleIdentifier", Name=":accepting")

    point_geometry_s1 = ET.SubElement(s1, "PointGeometry")
    ET.SubElement(point_geometry_s1, "Point", X="192", Y="-96")

    label_geometry_s1 = ET.SubElement(s1, "LabelGeometry", Anchor="NW")
    ET.SubElement(label_geometry_s1, "Point", X="0", Y="10")

    edge_list = ET.SubElement(graph, "EdgeList")

    # S0 -> S1 Edge
    edge_0_1 = ET.SubElement(edge_list, "Edge", Source="S0", Target="S1")
    label_block_0_1 = ET.SubElement(edge_0_1, "LabelBlock")
    ET.SubElement(label_block_0_1, "SimpleIdentifier", Name=event_name)
    label_geometry_0_1 = ET.SubElement(label_block_0_1, "LabelGeometry", Anchor="NW")
    ET.SubElement(label_geometry_0_1, "Point", X="-55", Y="-22")
    spline_geometry_0_1 = ET.SubElement(edge_0_1, "SplineGeometry")
    ET.SubElement(spline_geometry_0_1, "Point", X="120", Y="-112")

    # S1 -> S0 Edge
    edge_1_0 = ET.SubElement(edge_list, "Edge", Source="S1", Target="S0")
    label_block_1_0 = ET.SubElement(edge_1_0, "LabelBlock")
    for event in event_list:
        if event != event_name:
            ET.SubElement(label_block_1_0, "SimpleIdentifier", Name=event)
    label_geometry_1_0 = ET.SubElement(label_block_1_0, "LabelGeometry", Anchor="NW")
    ET.SubElement(label_geometry_1_0, "Point", X="11", Y="0")
    spline_geometry_1_0 = ET.SubElement(edge_1_0, "SplineGeometry")
    ET.SubElement(spline_geometry_1_0, "Point", X="120", Y="-80")

    # S1 -> S1 Edge
    edge_1_1 = ET.SubElement(edge_list, "Edge", Source="S1", Target="S1")
    label_block_1_1 = ET.SubElement(edge_1_1, "LabelBlock")
    ET.SubElement(label_block_1_1, "SimpleIdentifier", Name=event_name)
    label_geometry_1_1 = ET.SubElement(label_block_1_1, "LabelGeometry", Anchor="NW")
    ET.SubElement(label_geometry_1_1, "Point", X="-57", Y="-29")

    # S0 -> S0 Edge
    edge_0_0 = ET.SubElement(edge_list, "Edge", Source="S0", Target="S0")
    label_block_0_0 = ET.SubElement(edge_0_0, "LabelBlock")
    for event in event_list:
        if event != event_name:
            ET.SubElement(label_block_0_0, "SimpleIdentifier", Name=event)
    label_geometry_0_0 = ET.SubElement(label_block_0_0, "LabelGeometry", Anchor="NW")
    ET.SubElement(label_geometry_0_0, "Point", X="-73", Y="-272")
    spline_geometry_0_0 = ET.SubElement(edge_0_0, "SplineGeometry")
    ET.SubElement(spline_geometry_0_0, "Point", X="4", Y="-137")

    return root


############################# GENERATE ATTACKER MODEL ########################################################
# Taken from automatic_spec branch
def generate_attacker_model(function_name, address_name):
    """Generate an attacker SPEC that permanently blocks a transfer sub-EFSM."""
    root = ET.Element("SimpleComponent", Kind="SPEC", Name="AttackerModel")
    graph = ET.SubElement(root, "Graph")

    node_list = ET.SubElement(graph, "NodeList")

    # S0 Node
    s0 = ET.SubElement(node_list, "SimpleNode", Initial="true", Name="S0")
    event_list_s0 = ET.SubElement(s0, "EventList")
    ET.SubElement(event_list_s0, "SimpleIdentifier", Name=":accepting")

    point_geometry_s0 = ET.SubElement(s0, "PointGeometry")
    ET.SubElement(point_geometry_s0, "Point", X="176", Y="192")

    label_geometry_s0 = ET.SubElement(s0, "LabelGeometry", Anchor="NW")
    ET.SubElement(label_geometry_s0, "Point", X="0", Y="10")

    # S1 Node
    s1 = ET.SubElement(node_list, "SimpleNode", Name="S1")
    event_list_s1 = ET.SubElement(s1, "EventList")
    ET.SubElement(event_list_s1, "SimpleIdentifier", Name=":accepting")

    point_geometry_s1 = ET.SubElement(s1, "PointGeometry")
    ET.SubElement(point_geometry_s1, "Point", X="416", Y="192")

    label_geometry_s1 = ET.SubElement(s1, "LabelGeometry", Anchor="NW")
    ET.SubElement(label_geometry_s1, "Point", X="0", Y="10")

    edge_list = ET.SubElement(graph, "EdgeList")
    fail_event = f"{function_name}{address_name}transferFail"
    success_event = f"{function_name}{address_name}transferX"

    # S0 -> S1 Edge
    edge_0_1 = ET.SubElement(edge_list, "Edge", Source="S0", Target="S1")
    label_block_0_1 = ET.SubElement(edge_0_1, "LabelBlock")
    ET.SubElement(label_block_0_1, "SimpleIdentifier", Name=fail_event)
    label_geometry_0_1 = ET.SubElement(label_block_0_1, "LabelGeometry", Anchor="NW")
    ET.SubElement(label_geometry_0_1, "Point", X="-74", Y="6")

    # S1 -> S1 Edge
    edge_1_1 = ET.SubElement(edge_list, "Edge", Source="S1", Target="S1")
    label_block_1_1 = ET.SubElement(edge_1_1, "LabelBlock")
    ET.SubElement(label_block_1_1, "SimpleIdentifier", Name=fail_event)
    label_geometry_1_1 = ET.SubElement(label_block_1_1, "LabelGeometry", Anchor="NW")
    ET.SubElement(label_geometry_1_1, "Point", X="-121", Y="-30")

    # S0 -> S0 Edge
    edge_0_0 = ET.SubElement(edge_list, "Edge", Source="S0", Target="S0")
    label_block_0_0 = ET.SubElement(edge_0_0, "LabelBlock")
    ET.SubElement(label_block_0_0, "SimpleIdentifier", Name=success_event)
    label_geometry_0_0 = ET.SubElement(label_block_0_0, "LabelGeometry", Anchor="NW")
    ET.SubElement(label_geometry_0_0, "Point", X="-126", Y="-28")

    return root



############################# ATTACKER AND SPEC #############################################################

# *** EDIT THIS SECTION to switch contracts. ***
attacker_model = generate_attacker_model("processRefund", "project")
ComponentList.append(attacker_model)

progress_spec_model = generate_spec("claimProjectFundsX")
ComponentList.append(progress_spec_model)

#############################################################################################################

#print(VariableComponent['AddressVariables'])
#print(transfer_efsm_list)
print(FunctionVariablesTEMP)
#print(GeneralVariablesTEMP)
#print(asdf)

timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M")

# Define the folder where you want to store the output files
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
base_folder = os.path.join(PROJECT_DIR, 'output')

# Create a unique folder name using the current timestamp
output_folder = os.path.join(base_folder, f"output_{timestamp}")

# Create new output folder
os.makedirs(output_folder, exist_ok=True)

# Generate a unique filename using the contract name and current timestamp
filename = os.path.join(output_folder, f"{contract_module_name}_{timestamp}.wmod")

# Text file containing a short summary of changes made
filename_txt = os.path.join(output_folder, f"{contract_module_name}_{timestamp}.txt")

# Open the file and write the output
with open(filename, 'w') as file:
    print(ET.tostring(Module, encoding='utf8').decode('utf8'), file=file)

summary = (""" Adding the eventtransferX and eventtransferFail events to EventDecl list
""")

with open(filename_txt, 'w') as file:
    print(summary, file=file)

print(f"Output written to {output_folder}")

#print(ET.tostring(Module, encoding='utf8').decode('utf8'))