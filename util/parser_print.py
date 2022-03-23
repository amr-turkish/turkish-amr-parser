from util import parser_utils as utils
import numpy as np


def write(graph,head, level=0):
    level += 1
    Name = "name"
    children = utils.find_parent_connections(head,graph)
    reentrancy = utils.find_reentrancy_connections(head,graph)
    connections = children + reentrancy
    amr_key = graph.idx2property[head].concept_name

    if len(connections) == 0:
        return f'( {graph.idx2property[head].node_var_name} / {amr_key})'
    else:
        c = ''
        tabs = '\t' * level

        for child in children:
            c += f'\n{tabs}:{graph.idx2parent[child][head]} {write(graph,child, level)}'

        if len(reentrancy) != 0:
            for conn in reentrancy:
                ree = graph.idx2property[conn].node_var_name
                c += f'\n{tabs}:{graph.node2conn[conn][head]} {ree}'
        return f'({graph.idx2property[head].node_var_name} / {amr_key}{c})'

def to_sentence(sentence):
    try:
            l = list(sentence[1].values)
            c =" ".join(l)
            c=c.replace("_","")
    except:
            l = list(sentence[1].values)
            l = [i for i in l if i is not np.nan ]
            print(l)
            c =" ".join(l)
            c=c.replace("_","")
    return c

def to_penman(graph,head, level=0):
    parsed_str = write(graph,head,level=level)
    parsed_str = parsed_str.replace("R-A0", "ARG0")
    parsed_str=parsed_str.replace("A0","ARG0")
    parsed_str = parsed_str.replace("A1", "ARG1")
    parsed_str = parsed_str.replace("A2", "ARG2")
    parsed_str=parsed_str.replace("A3","ARG3")
    parsed_str = parsed_str.replace("A4", "ARG4")
    parsed_str = parsed_str.replace("A5", "ARG5")
    parsed_str = parsed_str.replace("A6", "ARG6")
    parsed_str=parsed_str.replace("A7","ARG7")
    parsed_str = parsed_str.replace("A8", "ARG8")
    parsed_str = parsed_str.replace("A9", "ARG9")
    parsed_str = parsed_str.replace("A10", "ARG10")
    parsed_str = parsed_str.replace("AM-MNR", "manner")
    parsed_str = parsed_str.replace("AM-LOC", "location")
    parsed_str = parsed_str.replace("MWE:", "MWE_")

    return parsed_str