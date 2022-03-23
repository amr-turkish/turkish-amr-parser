from util import parser_utils as utils


class Actions():

    def __init__(self):
        print("")

    @staticmethod
    def connect_up_node_and_remove(graph,idx,amr_remove=True):
        parent_idx_list = list(graph.idx2parent[idx].keys())
        parent_idx = parent_idx_list[0]

        Actions.connect_to_parent(graph,idx)
        Actions.__remove_node(graph,idx, amr_remove=amr_remove)
        graph.moved[idx] = parent_idx

    @staticmethod
    def connect_to_parent(graph,idx):
        parent_idx_list = list(graph.idx2parent[idx].keys())
        parent_idx = parent_idx_list[0]
        if idx in graph.idx2edges:
            try:
                graph.idx2edges[parent_idx].append(graph.idx2edges[idx])
            except:
                if type(graph.idx2edges[idx]) == list:
                    graph.idx2edges[parent_idx] = graph.idx2edges[idx]
                else:
                    graph.idx2edges[parent_idx] = [graph.idx2edges[idx]]

        for key, value in graph.idx2parent.items():
            if idx in value:
                relation = value[idx]
                del graph.idx2parent[key][idx]
                graph.idx2parent[key].update({parent_idx: relation})

    @staticmethod
    def __remove_node(graph,idx, init=False, amr_remove=True):
        while idx in graph.idx_sequence:
            graph.idx_sequence.remove(idx)

            # idx_sequence=[i for i in idx_sequence if i!=idx]

        if idx in graph.idx2edges:
            del graph.idx2edges[idx]

        if not init:
            del graph.idx2parent[idx]
            del graph.node2conn[idx]
            rep_var = graph.idx2property[idx].node_var_name
            # if amr_remove:
            #    del amr[idx2property[idx][5]]

            names_with_idx = utils.find_names_start_with_char(graph.idx2property,rep_var[0])
            print(names_with_idx)
            if len(names_with_idx) >= 1:
                if len(names_with_idx) > 1:
                    for ni, (idx_,name) in enumerate(names_with_idx):
                        graph.idx2property[idx_].set_node_var_name(name[0] + str(ni + 1))
                else:
                    graph.idx2property[idx].set_node_var_name(names_with_idx[0][1])
        del graph.idx2property[idx]

    @staticmethod
    def replace_node(graph,idx, new_idx):
        parent_idx, parent_rel = utils.find_proper_parent(idx,graph)
        graph.idx2parent[new_idx] = {parent_idx: parent_rel}
        # del idx2parent[idx]

        children = utils.find_parent_connections(idx,graph)
        for child in children:
            rel = graph.idx2parent[child][idx]
            del graph.idx2parent[child]
            graph.idx2parent[child] = {new_idx: rel}

        re_ent = utils.find_reentrancy_connections(idx,graph)
        for re in re_ent:
            rel = graph.idx2parent[re][idx]
            del graph.idx2parent[re]
            graph.idx2parent[re] = {new_idx: rel}

        Actions.__remove_node(graph,idx)

    @staticmethod
    def merge(graph,idx, parent_idx):
        graph.idx2property[parent_idx].isFrame = graph.idx2property[idx].isFrame \
            if graph.idx2property[idx].isFrame else graph.idx2property[parent_idx].isFrame
        graph.idx2property[parent_idx].inflections = "|".join([graph.idx2property[idx].inflections,
                                                               graph.idx2property[parent_idx].inflections])
        graph.idx2property[parent_idx].node_name = "".join([graph.idx2property[idx].node_name,
                                                            graph.idx2property[parent_idx].node_name])
        graph.idx2property[parent_idx].concept_name = "".join([graph.idx2property[idx].concept_name,
                                                               graph.idx2property[parent_idx].concept_name])
        utils.find_represent_char_of_names(parent_idx, graph.idx2property)

        Actions.connect_up_node_and_remove(graph,idx)



        return parent_idx