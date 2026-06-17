import json

from ast_restructure import *

# Now I need a way to add events to the transitions. So I add events, source and target nodes to the transitions.
# And also create a separate structure for storing variables.

pre_supremica = final_result

# Creating the EventDecl xml here
EventDeclList = ET.Element("EventDeclList")

event_list = []

# Initial Node - S0
INITIAL_NODE = 'S0'


# Create a separate eventdecl for this
# <EventDecl Kind="PROPOSITION" Name=":accepting"/>

# Need to write a function for adding generated events to xml eventdecl
def add_events_to_xml(event):  # event is a string
    global EventDeclList
    global event_list

    if event not in event_list:
        event_list.append(event)
        ET.SubElement(EventDeclList, "EventDecl", Kind="CONTROLLABLE", Name=event)
    else:
        return


# Creating a list to add all the nodes for a specific efsm

def add_node_to_efsm_node_list(source_node, target_node):
    if source_node not in efsm_node_list:
        efsm_node_list.append(source_node)

    if target_node not in efsm_node_list:
        efsm_node_list.append(target_node)



node_id = 0

node_list = []


def check_node_already_created(node):
    global node_list
    if node in node_list:
        return True
    else:
        return False


def get_new_node(type):
    global node_id
    if type == 'source':
        s_node = 'S' + str(node_id)
        return s_node
    elif type == 'source_reduced':
        node_id = node_id - 1
        s_node = 'S' + str(node_id)
        node_id = node_id + 1
        return s_node
    elif type == 'target':
        node_id += 1
        t_node = 'S' + str(node_id)
        if check_node_already_created(t_node):
            t_node = get_new_node('target')
            node_list.append(t_node)
        else:
            node_list.append(t_node)

        return t_node


    # Add node to node_list and check if it is already present
    # if is present, then return next node

for efsm in pre_supremica['Components']:
    # print(efsm)

    node_id = 0
    efsm_node_list = []
    node_list = []
    temporary_source_node = ""
    if efsm != 'VariableComponent':
        if 'edge_list' in pre_supremica['Components'][efsm]:

            n_transitions = len(pre_supremica['Components'][efsm]['edge_list'])
            EdgeList = ET.Element("EdgeList")

            if n_transitions == 1: # if there is only one transition
                source_node = INITIAL_NODE
                target_node = source_node
                processing_transition = pre_supremica['Components'][efsm]['edge_list']['t0']
                processing_transition['source_index'] = source_node
                processing_transition['target_index'] = target_node
                add_node_to_efsm_node_list(source_node, target_node)

                # adding events only if the events list is empty
                if not pre_supremica['Components'][efsm]['edge_list']['t0']['events']:
                    event_name = str(efsm + '1')
                    pre_supremica['Components'][efsm]['edge_list']['t0']['event'] = event_name
                    add_events_to_xml(event_name)
                else:
                    event_names = pre_supremica['Components'][efsm]['edge_list']['t0']['events']
                    for event_name in event_names:
                        add_events_to_xml(event_name)
                    

                transition_xml = add_transition_to_xml(processing_transition)
                EdgeList.append(transition_xml)
            else:
                condition_node = str()
                true_last_node = str()
                sender_transfer_node = str()
                transfer_success_source_node = str()
                sender_transfer_merge_node = str()
                temporary_source_node = str()
                require_node = str()
                for i in range(n_transitions): # if there are multiple transitions
                    #print('========',condition_node, true_last_node)
                    processing_transition = pre_supremica['Components'][efsm]['edge_list'][f't{i}']

# generate next_transition_type
                    if i != n_transitions - 1:
                        next_transition_type = pre_supremica['Components'][efsm]['edge_list'][f't{i+1}']['transition_type']


                    if i == 0: # if it is the first transition
                        source_node = get_new_node('source')
                        if processing_transition['transition_type'] == 'self_loop':
                            target_node = source_node

                        elif processing_transition['transition_type'] == 'true_body_start':
                            #print('found some true body start here+++++++++++++++++++++++++++++')
                            #print(efsm, processing_transition)
                            source_node = get_new_node('source')
                            condition_node = source_node
                            target_node = get_new_node('target')
                            if next_transition_type ==  'false_body_start' or next_transition_type == 'false_body_absent':
                                true_last_node = target_node
                                #print('true last node: ', true_last_node)
                            processing_transition['source_index'] = source_node
                            processing_transition['target_index'] = target_node
                            add_node_to_efsm_node_list(source_node, target_node)

                        elif processing_transition['transition_type'] == 'true_body_last':
                            #print('found some true last here')
                            if source_node == "S0":
                                source_node = get_new_node('source')
                                condition_node = source_node
                                #print('condition node: ', condition_node)
                            target_node = get_new_node('target')
                            true_last_node = target_node
                            #print('transition number, source node, true_last node: ', i, source_node, true_last_node)

                            processing_transition['source_index'] = source_node
                            processing_transition['target_index'] = target_node
                            add_node_to_efsm_node_list(source_node, target_node)

                        elif processing_transition['transition_type'] == 'false_body_last':
                            #print('found some false last here')
                            target_node = true_last_node
                            node_id = int(target_node[-1])
                            processing_transition['source_index'] = source_node
                            processing_transition['target_index'] = target_node
                            add_node_to_efsm_node_list(condition_node, target_node)
                            #print(asdf)

                        elif processing_transition['transition_type'] == 'false_body_start':
                            # print('found some false body start here')
                            source_node = condition_node

                            target_node = get_new_node('target')
                            processing_transition['source_index'] = source_node
                            processing_transition['target_index'] = target_node
                            add_node_to_efsm_node_list(source_node, target_node)

                        elif processing_transition['transition_type'] == 'false_body_absent':
                            #print('found some false body start here at i = 0')
                            #print(efsm, processing_transition)
                            #print('source node: ', condition_node)
                            #print('target node: ', true_last_node)
                            #print(asdf)
                            source_node = condition_node

                            target_node = true_last_node if true_last_node else INITIAL_NODE
                            processing_transition['source_index'] = source_node
                            processing_transition['target_index'] = target_node
                            add_node_to_efsm_node_list(source_node, target_node)

                        else:
                            # target_node = get_new_node('target')
                            target_node = get_new_node('target') if not processing_transition['target_index'] else \
                            processing_transition['target_index']
                        processing_transition['source_index'] = source_node
                        processing_transition['target_index'] = target_node
                        add_node_to_efsm_node_list(source_node, target_node)

                        # adding events only if the events list is empty
                        if not pre_supremica['Components'][efsm]['edge_list'][f't{i}']['events']:
                            event_name = str(efsm + '1')
                            pre_supremica['Components'][efsm]['edge_list'][f't{i}']['event'] = event_name
                            add_events_to_xml(event_name)
                        else:
                            event_names = pre_supremica['Components'][efsm]['edge_list'][f't{i}']['events']
                            for event_name in event_names:
                                add_events_to_xml(event_name)



                    elif i == n_transitions - 1: # if it is the last transition
                        if temporary_source_node != "":
                            source_node = temporary_source_node
                        else:
                            source_node = get_new_node('source')
                        if processing_transition['transition_type'] == 'self_loop':
                            target_node = source_node

                        elif processing_transition['transition_type'] == 'transfer_success':
                            #print('found some transfer success here')
                            #node_id = node_id - 1
                            source_node = get_new_node('source_reduced')
                            target_node = get_new_node('target')
                            processing_transition['source_index'] = source_node
                            processing_transition['target_index'] = target_node
                            add_node_to_efsm_node_list(source_node, target_node)

                        elif processing_transition['transition_type'] == 'true_body_start':
                            #print('found some true body start here')
                            source_node = get_new_node('source')
                            condition_node = source_node
                            target_node = get_new_node('target')
                            processing_transition['source_index'] = source_node
                            processing_transition['target_index'] = target_node
                            add_node_to_efsm_node_list(source_node, target_node)

                        elif processing_transition['transition_type'] == 'false_body_start':
                            #print('found some false body start here')
                            source_node = condition_node

                            target_node = get_new_node('target')
                            processing_transition['source_index'] = source_node
                            processing_transition['target_index'] = target_node
                            add_node_to_efsm_node_list(source_node, target_node)

                        elif processing_transition['transition_type'] == 'false_body_last':
                            #print('found some false last here')
                            target_node = true_last_node
                            node_id = int(target_node[-1])
                            processing_transition['source_index'] = source_node
                            processing_transition['target_index'] = target_node
                            add_node_to_efsm_node_list(condition_node, target_node)

                        elif processing_transition['transition_type'] == 'false_body_absent':
                            #print('found some false_absent body here, last transition')
                            #print(efsm, processing_transition)
                            #print('source node: ', condition_node)
                            #print('target node: ', true_last_node)
                            # print(asdf)
                            source_node = condition_node

                            target_node = true_last_node if true_last_node else INITIAL_NODE
                            processing_transition['source_index'] = source_node
                            processing_transition['target_index'] = target_node
                            add_node_to_efsm_node_list(source_node, target_node)

                        elif processing_transition['transition_type'] == 'sender_transfer_initial':

                            #print('sender transfer found in add_events_nodes.py')
                            source_node = get_new_node('source')
                            sender_transfer_node = source_node
                            target_node = get_new_node('target')
                            #print('sender transfer node : ',sender_transfer_node)
                            processing_transition['source_index'] = source_node
                            processing_transition['target_index'] = target_node
                            add_node_to_efsm_node_list(source_node, target_node)

                        elif processing_transition['transition_type'] == 'sender_transfer':
                            #print('sender transfer found in add_events_nodes.py-----')
                            source_node = sender_transfer_node
                            target_node = get_new_node('target')
                            #print('source node: ', source_node)
                            #print('target node: ', target_node)
                            processing_transition['source_index'] = source_node
                            processing_transition['target_index'] = target_node
                            add_node_to_efsm_node_list(source_node, target_node)

                        elif processing_transition['transition_type'] == 'sender_transfer_success':
                            #print('sender transfer found in add_events_nodes.py-----')
                            source_node = transfer_success_source_node
                            #target_node = get_new_node('target')
                            target_node = sender_transfer_merge_node
                            #print('source node: ', source_node)
                            #print('target node: ', target_node)
                            processing_transition['source_index'] = source_node
                            processing_transition['target_index'] = target_node
                            add_node_to_efsm_node_list(source_node, target_node)

                        else:
                            target_node = INITIAL_NODE
                        processing_transition['source_index'] = source_node
                        processing_transition['target_index'] = target_node
                        add_node_to_efsm_node_list(source_node, target_node)

                        # adding events only if the events list is empty
                        if not processing_transition['events']:
                            event_name = str(efsm + 'X')
                            pre_supremica['Components'][efsm]['edge_list'][f't{i}']['event'] = event_name
                            add_events_to_xml(event_name)
                        else:
                            event_names = pre_supremica['Components'][efsm]['edge_list'][f't{i}']['events']
                            for event_name in event_names:
                                add_events_to_xml(event_name)

                    else: # if it is neither the first nor the last transition
                        source_node = get_new_node('source') #s6 #s6 #s5
                        if temporary_source_node != "" and processing_transition['transition_type'] == '':
                            source_node = temporary_source_node
                            target_node = get_new_node('target')
                            processing_transition['source_index'] = source_node
                            processing_transition['target_index'] = target_node
                            add_node_to_efsm_node_list(source_node, target_node)
                            temporary_source_node = target_node
                        elif processing_transition['transition_type'] == 'self_loop':
                            target_node = source_node #s6

                        elif processing_transition['transition_type'] == 'transfer_success':
                            #print('found some transfer success here')

                            source_node = get_new_node('source_reduced')
                            target_node = get_new_node('target')
                            processing_transition['source_index'] = source_node
                            processing_transition['target_index'] = target_node
                            add_node_to_efsm_node_list(source_node, target_node)

                        elif processing_transition['transition_type'] == 'true_body_start':
                            #print('found some true body start here----------------------------------')
                            #print(efsm, processing_transition)
                            source_node = get_new_node('source')
                            condition_node = source_node
                            target_node = get_new_node('target')
                            if next_transition_type ==  'false_body_start' or next_transition_type == 'false_body_absent':
                                true_last_node = target_node
                            processing_transition['source_index'] = source_node
                            processing_transition['target_index'] = target_node
                            add_node_to_efsm_node_list(source_node, target_node)

                        elif processing_transition['transition_type'] == 'true_body_last':
                            #print('found some true last here, transaction not first not last')
                            #print(efsm, processing_transition)
                            target_node = get_new_node('target')
                            true_last_node = target_node
                            #print('true last node: ', true_last_node)
                            processing_transition['source_index'] = source_node
                            processing_transition['target_index'] = target_node
                            add_node_to_efsm_node_list(source_node, target_node)

                        elif processing_transition['transition_type'] == 'false_body_last':
                            #print('found some false last here')
                            target_node = true_last_node  #s5
                            node_id = int(target_node[-1])
                            processing_transition['source_index'] = source_node
                            processing_transition['target_index'] = target_node
                            add_node_to_efsm_node_list(condition_node, target_node)
                            #print(asdf)

                        elif processing_transition['transition_type'] == 'false_body_start':
                            #print('found some false body start here ------', processing_transition)

                            source_node = condition_node #s3 #trueLastNode = s5

                            target_node = get_new_node('target') #s6
                            #print(efsm, processing_transition)
                            processing_transition['source_index'] = source_node
                            processing_transition['target_index'] = target_node
                            add_node_to_efsm_node_list(source_node, target_node)

                        elif processing_transition['transition_type'] == 'false_body_absent':
                            #print('found some false_absent body here')
                            #print(efsm, processing_transition)
                            #print('source node: ', condition_node)
                            #print('target node: ', true_last_node)
                            #print(asdf)
                            source_node = condition_node

                            target_node = true_last_node if true_last_node else get_new_node('source')
                            processing_transition['source_index'] = source_node
                            processing_transition['target_index'] = target_node
                            add_node_to_efsm_node_list(source_node, target_node)

                        elif processing_transition['transition_type'] == 'sender_transfer_initial':

                            #print('sender transfer found in add_events_nodes.py')
                            source_node = get_new_node('source')
                            sender_transfer_node = source_node
                            target_node = get_new_node('target')
                            transfer_success_source_node = target_node
                            #print('sender transfer node : ', sender_transfer_node)
                            processing_transition['source_index'] = source_node
                            processing_transition['target_index'] = target_node
                            add_node_to_efsm_node_list(source_node, target_node)

                        elif processing_transition['transition_type'] == 'sender_transfer':
                            #print('sender transfer found in add_events_nodes.py-----')
                            source_node = sender_transfer_node
                            target_node = get_new_node('target')
                            transfer_success_source_node = target_node #s6
                            #print('source node: ', source_node)
                            #print('target node: ', target_node)
                            processing_transition['source_index'] = source_node
                            processing_transition['target_index'] = target_node
                            add_node_to_efsm_node_list(source_node, target_node)

                        elif processing_transition['transition_type'] == 'sender_transfer_success_initial':
                            #print('sender transfer found in add_events_nodes.py-----')
                            source_node = transfer_success_source_node
                            target_node = get_new_node('target')
                            sender_transfer_merge_node = target_node
                            temporary_source_node = sender_transfer_merge_node
                            #print('source node: ', source_node)
                            #print('target node: ', target_node)
                            processing_transition['source_index'] = source_node
                            processing_transition['target_index'] = target_node
                            add_node_to_efsm_node_list(source_node, target_node)

                        elif processing_transition['transition_type'] == 'sender_transfer_success':
                            #print('sender transfer found in add_events_nodes.py-----')
                            source_node = transfer_success_source_node
                            target_node = sender_transfer_merge_node
                            #print('source node: ', source_node)
                            #print('target node: ', target_node)
                            processing_transition['source_index'] = source_node
                            processing_transition['target_index'] = target_node
                            add_node_to_efsm_node_list(source_node, target_node)
                        elif processing_transition['transition_type'] == 'require_true':
                            source_node = get_new_node('source')
                            target_node = get_new_node('target')
                            require_node = source_node

                            processing_transition['source_index'] = source_node
                            processing_transition['target_index'] = target_node
                            add_node_to_efsm_node_list(source_node, target_node)

                        elif processing_transition['transition_type'] == 'require_false':
                            source_node = require_node
                            target_node = INITIAL_NODE
                            processing_transition['source_index'] = source_node
                            processing_transition['target_index'] = target_node
                            add_node_to_efsm_node_list(source_node, target_node)

                        else:

                            target_node = get_new_node('target') if not processing_transition['target_index'] else processing_transition['target_index']
                            #print('TARGET NODE IN EFSN', efsm, target_node) # get_new_node = s6

                        processing_transition['source_index'] = source_node
                        processing_transition['target_index'] = target_node
                        add_node_to_efsm_node_list(source_node, target_node)

                        # adding events only if the events list is empty
                        if not processing_transition['events']:
                            event_name = str(efsm + str(i + 1))
                            pre_supremica['Components'][efsm]['edge_list'][f't{i}']['event'] = event_name
                            add_events_to_xml(event_name)
                        else:
                            event_names = pre_supremica['Components'][efsm]['edge_list'][f't{i}']['events']
                            for event_name in event_names:
                                add_events_to_xml(event_name)

                    transition_xml = add_transition_to_xml(processing_transition)
                    EdgeList.append(transition_xml)

            # Adding the transition_xml to EdgeList

            # pre_supremica['Components'][efsm]['edge_list'] = ET.tostring(EdgeList, encoding='unicode', method='xml')
            pre_supremica['Components'][efsm]['edge_list'] = EdgeList

        # Adding the node_list to pre_supremica
        nodes_xml = add_nodes_to_xml(efsm_node_list)
        # pre_supremica['Components'][efsm]['node_list'] = ET.tostring(nodes_xml, encoding='unicode', method='xml')
        pre_supremica['Components'][efsm]['node_list'] = nodes_xml

# Adding all the events to pre_supremica
# pre_supremica['Events']['EventDeclList'] = ET.tostring(EventDeclList, encoding='unicode', method='xml')
pre_supremica['Events'] = EventDeclList

# pre_supremica is in the form of a dictionary
# print(json.dumps(str(pre_supremica)))
# print(pre_supremica)
