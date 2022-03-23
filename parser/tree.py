import warnings

import numpy as np

from aligner import alignment, alias
from util import parser_utils as utils, preprocess

warnings.filterwarnings("ignore")

class SpanTree():

    """
       Span is the base for building amr graph. I only holds the nodes and their relations.
    """

    def __init__(self):
        self.idx2property = {}
        self.idx2edges = {}
        self.idx_sequence = []
        self.idx2parent = {}
        self.node2conn = {}
        self.moved = {}

    def create_tree(self,sentence,verbose=True):
        self.__initialize_tokens_as_nodes(sentence,verbose=verbose)
        self.__create_interparsed_tree()
        print("Span Tree has been created.")

    def create_and_add_new_node(self,parent_idx, parent_rel, tag="", name="", const_name="", check=False, verb_frame=False):
        new_idx = utils.give_new_idx(self.idx2property,self.moved)
        frame = ""
        if verb_frame:
            frame = ["Y", name]

        node = [new_idx, const_name, name, "", tag, tag, "", "", parent_idx, "", parent_rel, "", frame, name, 0, False]
        new_idx = self.__create_node(node, check=check)
        new_idx = self.__add_node_in_tree(new_idx, parent_idx, node[10], check=check)
        return new_idx

    def __initialize_tokens_as_nodes(self,sentence,verbose = False):
        """
        :param sentence: list of list
        :return:

        Sentece: list of token.
        token : The list which holds token text and its properties.
        token properties :
            0: token position in list
            1: word
            2: word lemma
            3: word lemma
            4: postag
            5:
            6: word surface form properties
            7: the same with 6
            8: dependency parsing connected node
            9:  the same with 8
            10: dependency relation
            11: the same with 10
            12: propbank verb frame or relation

        """
        for i in range(0, len(sentence)):
            token = sentence[i]
            token[12] = eval(token[12]) if token[12] is not np.nan else []
            _ = self.__create_node(token, check=False)
        if verbose:
            print("Nodes are initiliazed..")

    def __create_node(self, node_properties, check):

        idx = node_properties[0]
        prop_tags = node_properties[12]
        frame = False
        name = preprocess.to_lower(node_properties[1])
        root_name = preprocess.to_lower(node_properties[2])
        root_pos_tag = node_properties[4]
        second_pos_tag = node_properties[5]
        isThere = utils.find_idx_by_name(root_name,self.idx2property) if check else False

        if not isThere:
            if len(prop_tags) > 0 :
                # print("prop tags", prop_tags)
                if 'Y' in prop_tags:
                    index_of_Y = prop_tags.index("Y")
                    root_name = prop_tags[index_of_Y + 1]
                    prop_tags.remove(root_name)
                    prop_tags.remove('Y')
                    frame = True

                    #  print("Prop tags of row",prop_tags,len(prop_tags),idx)
                if len(prop_tags) > 0  and node_properties[8]!=0:
                    # print("Prop tags of row",prop_tags,len(prop_tags),idx)
                    self.idx2edges[idx] = prop_tags
            self.idx2property[idx] = Node(idx)
            self.idx2property[idx].create_node([name, node_properties[6], node_properties[4],
                                                         node_properties[10],frame, root_name, root_pos_tag,
                                                         node_properties[8], second_pos_tag])
            self.idx_sequence.append(idx)
            return idx
        else:
            if len(prop_tags) > 0:
                if 'Y' in prop_tags:
                    index_of_Y = prop_tags.index("Y")
                    root_name = prop_tags[index_of_Y + 1]
                    prop_tags.remove(root_name)
                    prop_tags.remove('Y')
                    frame = True

                    # print("Prop tags of row",prop_tags,len(prop_tags),isThere)
                if len(prop_tags) > 0:
                    # print("Prop tags of row",prop_tags,len(prop_tags),idx)
                    self.idx2edges[isThere] = prop_tags

            self.idx_sequence.append(isThere)
            return isThere

    def __create_interparsed_tree(self):
        for idx, property_ in self.idx2property.copy().items():
            _ = self.__add_node_in_tree(idx, property_.dep_par_head, property_.dep_par_relation, check=False)

    def __add_node_in_tree(self,idx, parent_idx, dep_rel, check=True):

        """
        It adds node in InterParsedTree.
        :param idx: node idx
        :param parent_idx: parent node idx
        :param dep_rel: relation comming from dependency parser
        :param check: check if node is in the InterParseTree
        :return: node idx
        """
        name = self.idx2property[idx].concept_name
        if utils.reentrancy_check(name,self, check=check):

            utils.find_represent_char_of_names(idx,self.idx2property)

            if idx in self.idx2edges.keys():
                rel_index, rel = utils.find_proper_connecton(idx, parent_idx, dep_rel,self.idx2property,self.idx2edges)
                self.idx2parent[idx] = {parent_idx: rel} if parent_idx not in self.moved.keys() \
                                                        else {self.moved[parent_idx]: rel}
                self.node2conn[idx] = {}
                if rel_index != -1:
                    if len(self.idx2edges[idx]) > 1:
                        del self.idx2edges[idx][rel_index]
                    else:
                        del self.idx2edges[idx]
                elif rel != self.idx2edges[idx] and rel!=alias.coord:
                    ed = self.idx2edges[idx][0]
                    if ed in [alias.two, alias.cau,alias.goal,alias.ext,alias.am_neg]:
                        self.idx2parent[idx] = {parent_idx: ed} if parent_idx not in self.moved.keys() \
                            else {self.moved[parent_idx]: ed}
                        self.node2conn[idx] = {}
                        del self.idx2edges[idx][0]

            else:
                self.idx2parent[idx] = {parent_idx: dep_rel} if parent_idx not in self.moved.keys() else {
                    self.moved[parent_idx]: dep_rel}
                self.node2conn[idx] = {}
            return idx
        else:
            new_idx =utils.find_idx_by_name(name,self.idx2property)
            self.node2conn[new_idx] = {} if new_idx not in self.node2conn else self.node2conn[new_idx]
            if idx in self.idx2edges.keys():
                self.node2conn[new_idx].update({parent_idx: self.idx2edges[idx][0]}) \
                                            if parent_idx not in self.moved.keys() \
                                            else {self.moved[parent_idx]: self.idx2edges[idx][0]}
                del self.idx2edges[idx][0]
            else:
                self.node2conn[new_idx].update({parent_idx: dep_rel}) if parent_idx not in self.moved.keys() else {
                    self.moved[parent_idx]: dep_rel}
            self.moved[idx] = new_idx
            utils.move(idx, new_idx,self)

            return new_idx


    def __str__(self):
        return "property "+ str([ v.write() for k,v in self.idx2property.items()]) +"\nedges " +str(self.idx2edges) +\
               "\nparent " +str(self.idx2parent)+"\nvar list "



    # def create_and_add_new_node(self,parent_idx, parent_rel, tag="", name="", const_name="", check=False, verb_frame=False):
    #     new_idx = utils.give_new_idx(self.idx2property,self.moved)
    #     frame = ""
    #     if verb_frame:
    #         frame = ["Y", name]
    #
    #     node = [new_idx, const_name, name, "", tag, tag, "", "", parent_idx, "", parent_rel, "", frame, name, 0, False]
    #     _ = self.__create_nodes(node, check=check)
    #     self.__add_node_in_tree(new_idx, parent_idx, node[10], check=check)
    #     return new_idx
    #
    # def add_null_subject(self,parent_idx):
    #     parent_surface_form = set(self.idx2property[parent_idx][1].split("|"))
    #     pron_type = list(parent_surface_form.intersection(set(list(aligner.subjects.keys()))))
    #     # print(pron_type)
    #     if len(pron_type) > 0:
    #         pronoun = aligner.subjects[pron_type[0]]
    #         # print("pronoun",pronoun)
    #         idx  = utils.give_new_idx(self.idx2property,self.moved)
    #         subject_node = [idx, pronoun, pronoun, "", alias.pron,  alias.pron, "", "", parent_idx, "", alias.subj, "", [alias.A0],
    #                         pronoun, 0, False]
    #         node_idx = self.__create_nodes(subject_node)
    #         self.__add_node_in_tree(node_idx, parent_idx, subject_node[10])

    def add_subject_is_necessary(self):
        for idx, property_ in self.idx2property.copy().items():
            if property_.pres_pos_tag == alias.verb:
                parent_rels = [node_rel for key, value in self.idx2parent.items() for node, node_rel in value.items() if
                               node == idx]
                reentrancy_rels = [node_rel for key, value in self.node2conn.items() for node, node_rel in value.items() if
                                   node == idx]
                relations = parent_rels + reentrancy_rels
                if alias.A0 not in relations:
                    if alias.AA not in relations:
                        _=self.add_null_subject(idx,check=True)

    def add_null_subject(self,parent_idx,check=True):
        parent_surface_form = set(self.idx2property[parent_idx].inflections.split("|"))
        pron_type = list(parent_surface_form.intersection(set(list(alignment.subjects.keys()))))
        print(pron_type)
        if len(pron_type) > 0:
            pronoun = alignment.subjects[pron_type[0]]
            # print("pronoun",pronoun)
            return self.create_and_add_new_node(parent_idx, alias.A0, tag=alias.pron,check=check,name=pronoun, const_name=pronoun)

class Node():
    def __init__(self,idx):
        self.idx = idx
        self.node_name=""
        self.pos_tag=""
        self.pres_pos_tag=""
        self.inflections=""
        self.dep_par_relation=""
        self.dep_par_head=None
        self.isFrame = False
        self.concept_name=""
        self.lemma_pos_tag=""

        self.node_var_name = None


    def create_node(self,node_properties):

        self.node_name=node_properties[0]
        self.inflections = node_properties[1]
        self.pos_tag = node_properties[2]
        self.dep_par_relation = node_properties[3]
        self.isFrame = node_properties[4]
        self.concept_name = node_properties[5]
        self.pres_pos_tag=node_properties[6]
        self.dep_par_head = node_properties[7]
        self.lemma_pos_tag= node_properties[8]

    def set_node_var_name(self,name):
        self.node_var_name =name



    def write(self):
        return str(self.idx)+ " " + self.node_name