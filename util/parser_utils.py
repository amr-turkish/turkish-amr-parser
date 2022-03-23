from aligner import alias
from util import preprocess


def find_idx_by_name(name,InterParseTree_property):
    """
    :param name: word lemma form
    :param graph_property: graph nodes property dictionary.
    :return: boolean

    It finds if  given word name in the interparse tree.
    """

    if name !="_":
        key=[k for k,v in InterParseTree_property.items() if name==v.concept_name]
        if len(key)>0:
            return key[0]
        else:
            return False
    else:
        return False

def reentrancy_check(name,graph,check=True):
    """
    It checks whether token node  is already created.
    :param name: word lemma form
    :param token_text_to_tree_node: tree token text dictionary for amr graph variables
    :param check:
    :return: boolean
    """
    token_text_to_tree_node = [node.concept_name for idx,node in graph.idx2property.items() if idx in graph.idx2parent ]
    if not check:
        return True
    else:
        if name not in token_text_to_tree_node:
            return True
        else:
            return False

def find_represent_char_of_names(idx,idx2property):
    """
    It give the variable name to node based on amr graph variable name rules.
    Variable names become the first letter of the token text. If there are more than token starting with the same letter,
    variable names take number with the first letter of the token text

    :param new_name: word lemma form
    :param token_text_to_tree_node: tree token text dictionary for amr graph variables
    :return:
    """
    new_name=idx2property[idx].concept_name
    new_name= preprocess.to_lower(new_name)
    var_list = {node.node_var_name:idx for idx,node in idx2property.items() if node.node_var_name !=None}


    if len(var_list)==0:
        idx2property[idx].set_node_var_name(new_name[0])

    else:
        i=1
        new_name_version = new_name[0]+str(i)
        if  new_name_version in var_list:
            while new_name_version in var_list:
                i+=1
                new_name_version = new_name[0]+str(i)
            idx2property[idx].set_node_var_name(new_name_version)

        elif new_name[0] in var_list and  new_name_version not in var_list:

            i+=1
            new_name_version = new_name[0]+str(i)
            eidx=var_list[new_name[0]]
            idx2property[eidx].set_node_var_name(new_name[0])
            while new_name_version  in var_list:
                i += 1
                new_name_version = new_name[0] + str(i)
            idx2property[idx].set_node_var_name(new_name_version)
        else:
            idx2property[idx].set_node_var_name(new_name[0])

def find_proper_connecton(idx,parent_idx,relation,InterParseTree_property,edge):

    if parent_idx == 0:
        return -1,relation
    if InterParseTree_property[parent_idx].isFrame:
        if relation== alias.subj:
            if alias.A0 in edge[idx]:
                i = edge[idx].index(alias.A0)
                return i, alias.A0
            elif  alias.AA in edge[idx]:
                i = edge[idx].index(alias.AA)
                return i, alias.A0
            else:
                return 0,edge[idx][0]
        else:
            return 0,edge[idx][0]
    else:
        i = parent_idx-1
        if i in InterParseTree_property:
            if InterParseTree_property[i].dep_par_relation== alias.deriv:
                return 0,edge[idx][0]
            elif InterParseTree_property[parent_idx].dep_par_relation== alias.deriv:
                return 0,edge[idx][0]
            else:
                return -1,relation
        else:
            return -1,relation

def find_names_start_with_char(idx2property,char):
    names=[(k,v.node_var_name) for k,v in idx2property.items() if v.node_var_name[0]==char]
    return names

def find_children_connected_with_given_relation(idx, idx2parent, relation=alias.A0):
    children=[i for i,value in idx2parent.items()
                                   for node,rel in value.items() if (node==idx)and (rel==relation)]
    return children

def find_reentrancy_connected_with_given_relation(idx, graph, relation=alias.A0):
    children=[i for i,value in graph.node2conn.items()
                                   for node,rel in value.items() if (node==idx)and (rel==relation)]
    return children

def give_new_idx(idx2property,moved):
    cand_id_1 = max(idx2property, key=int)
    if len(moved)>0:
        cand_id_2=max(moved, key=int)
    else:
        cand_id_2=0
    new_id=max(cand_id_1,cand_id_2)+1
    return new_id

def find_reentrancy_connections(idx,graph):
    """
    Find reentrancy connections of given idx
    """
    reentrancy_connections = [key for key,value in graph.node2conn.items() for node,node_rel in value.items() if node==idx]
    return reentrancy_connections

def move(idx,moved_idx,tree):
    """

    :param idx:
    :param moved_idx:
    :param tree:
    :return:
    """

    for key,value in tree.idx2parent.items():
         for node,node_rel in value.items():
            if node==idx:
                tree.idx2parent[key]={moved_idx:node_rel}

    for key,value in tree.node2conn.items():
         for node,node_rel in value.items():
            if node==idx:
                del tree.node2conn[key][idx]
                tree.node2conn[key].update({moved_idx:node_rel})

def find_proper_parent(idx,graph):
    if idx != 0:
        word = graph.idx2property[idx].node_name
        # print("\ncurrent word",word,idx,idx2property[idx][5])
        parent_idx = list(graph.idx2parent[idx].keys())[0]
        parent_rel = list(graph.idx2parent[idx].values())[0]
        if parent_idx == 0:
            return parent_idx, parent_rel

        parent_word = graph.idx2property[parent_idx].node_name
        agg = idx
        #  print("parent word",parent_word,parent_idx)
        if word == parent_word and graph.idx2property[parent_idx].dep_par_head == agg:
            while word == parent_word and graph.idx2property[parent_idx].dep_par_head == agg:
                #      print("1 word == parent word case parent word",parent_word,parent_idx,idx2property[parent_idx][5])
                parent_idx_ = parent_idx
                parent_idx = list(graph.idx2parent[parent_idx_].keys())[0]
                parent_rel = list(graph.idx2parent[parent_idx_].values())[0]
                if parent_idx == 0:
                    break
                parent_word = graph.idx2property[parent_idx].node_name

                #  print("2 parent word",parent_word,parent_idx)
            return parent_idx, parent_rel
        else:
            # print("3 word != parent word case parent word",parent_word,parent_idx,idx2property[parent_idx][5])
            ### Eğer parent word ile current word eşit değilse; parent node complex node mu
            #  print("parent_idx",parent_idx)
            parent_of_parent_idx = list(graph.idx2parent[parent_idx].keys())[0]
            parent_of_parent_rel = list(graph.idx2parent[parent_idx].values())[0]

            ### Parent of parent root ise parent root node ve complex node değil.
            if parent_of_parent_idx == 0:
                return parent_idx, parent_rel

            parent_of_parent_word = graph.idx2property[parent_of_parent_idx].node_name
            # print("parent pf parent word",parent_of_parent_word,parent_word,parent_of_parent_idx,idx2property[parent_of_parent_idx][5])
            # print("4 parent word == parent of parent case ",parent_word,parent_of_parent_word,idx2property[idx][0])
            ### Parent complex ise
            parent_of_parent_idx_ = parent_of_parent_idx
            agg = parent_idx
            # print("ara chect dx2property[parent_of_parent_idx_][7],agg ",idx2property[parent_of_parent_idx_][5],idx2property[parent_of_parent_idx_][7],agg)
            while parent_of_parent_word == parent_word and graph.idx2property[parent_of_parent_idx_].dep_par_head == agg:
                #   print("cont2")
                parent_of_parent_idx_ = parent_of_parent_idx
                parent_of_parent_idx = list(graph.idx2parent[parent_of_parent_idx_].keys())[0]

                if parent_of_parent_idx == 0:
                    parent_of_parent_idx_ = parent_of_parent_idx
                    break
                parent_of_parent_word = graph.idx2property[parent_of_parent_idx].node_name
                #  print("5 parent of parent node",parent_of_parent_word,"5 parent of parent node",parent_word,parent_of_parent_idx)
                parent_idx = parent_of_parent_idx_
                parent_rel = list(graph.idx2parent[parent_idx].values())[0]

            # print(idx2parent)
            # print("6 parent word",parent_word,parent_idx,parent_rel)
            return parent_idx, parent_rel

    else:
        # print("8 parent word",parent_word,parent_idx,idx)
        return idx, alias.pred

def find_connections_of_a_nodes(idx,graph):
    parent_connections = find_parent_connections(idx,graph)
    reentrancy_connections = find_reentrancy_connections(idx,graph)
    return parent_connections+reentrancy_connections

def find_parent_connections(idx,graph):
    parent_connections = [key for key, value in graph.idx2parent.items() for node, node_rel in value.items() if node == idx]
    return parent_connections

def find_connnection_names(frames,frames_connections,graph):
    connection_names={}
    for f,c in zip(frames,frames_connections):
        for ci in c:
            #print("f",f,"ci",ci,"c",c)
            try:
                if f in graph.idx2parent[ci]:
                    connection_names[f]+=[graph.idx2parent[ci][f]]
                else:
                    connection_names[f]+=[graph.node2conn[ci][f]]
            except:
                if f in graph.idx2parent[ci]:
                    connection_names[f]=[graph.idx2parent[ci][f]]
                else:
                    connection_names[f]=[graph.node2conn[ci][f]]
    return connection_names

def is_compound_idx(idx,graph):
    parent_idx = list(graph.idx2parent[idx].keys())[0]
    if parent_idx == 0:
        return idx
    if graph.idx2property[parent_idx].concept_name in [alias.ve, alias.ol17, alias.possible]:  ##### if node is compound
        idx = parent_idx

    return idx

def find_parent_with_given_post_tag(idx, graph, postag=alias.noun, participant=4):

    parent_idx, _ = find_proper_parent(idx,graph)

    the_first_parent_idx = parent_idx
    while parent_idx != 0:
        #  print(postag ,"parent is searching",parent_idx)
        parent_type = graph.idx2property[parent_idx].pos_tag if participant == 4 \
                                            else graph.idx2property[parent_idx].lemma_pos_tag
        if parent_type == postag:
            return parent_idx
        else:
            parent_idx, _ = find_proper_parent(parent_idx,graph)
    return the_first_parent_idx

def is_proper_child(idx,graph):
    """Finds whether  given node is compound . Returns tops and bottom nodes if its compound"""
    while graph.idx2property[idx].concept_name in [alias.ve, alias.ol17, alias.possible, alias.or_]:  ##### if node is compound
        idx = find_parent_connections(idx,graph)[0]
    return idx

def find_parent_idx_with_given_relation(idx, graph, relation=alias.coord):
    '''verilen id nin üst node larına çıkar,
    relation olmayan node da durur ve
    son relation olan nodu parent yapar'''

    # print("find "+relation+" parent sequence for",idx)
    parent_idx, rel = find_proper_parent(idx,graph)
    # print(parent_idx)
    sequence = [parent_idx]
    pre_rel = rel
    pre_parent = parent_idx
    i = 0
    # print(idx2parent)
    while rel == relation:
        #   print(" in the while parent_idx",parent_idx,"rel",rel)
        sequence.append(parent_idx)
        pre_rel = rel
        pre_parent = parent_idx
        parent_idx, rel = find_proper_parent(parent_idx,graph)
        #  print("next parent idx",parent_idx,rel,sequence)

    sequence = list(set(sequence))
    # print(relation+" sequence",sequence,pre_parent,pre_rel)
    return pre_parent, pre_rel, sequence

def make_parent_to_sibling(graph,left_node_idx, right_node_idx, parent_idx, left_rel, right_rel):
    graph.idx2parent[left_node_idx] = {parent_idx: left_rel}
    graph.idx2parent[right_node_idx] = {parent_idx: right_rel}




