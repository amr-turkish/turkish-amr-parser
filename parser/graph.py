import warnings

from aligner import alignment, alias
from parser.actions import Actions
from parser.tree import SpanTree
from util import parser_utils as utils, preprocess

from util import parser_print as ppx


warnings.filterwarnings("ignore")

class SpanGraph(SpanTree):

    def __init__(self):
        super().__init__()


    def create_graph(self,sentence):
        self.__create_interparsed_graph(sentence)
        self.root=None
        return self


    def __create_interparsed_graph(self,sentence):
        self.create_tree(sentence)
        for idx, property_ in self.idx2property.copy().items():
            if not self.__graph_re_order(property_, idx):
                if property_.pres_pos_tag == alias.verb:
                    self.node_surface_form(idx)

        self.add_reentrancy_in_an_order()
        self.add_subject_is_necessary()



    def __graph_re_order(self, property_, idx):
        if property_.dep_par_relation == alias.det and list(self.idx2parent[idx].values())[0]==alias.det:
            return self.__remove_determiner(idx)
        elif property_.dep_par_relation == alias.deriv:
            parent_rel = list(self.idx2parent[idx].values())[0]
            # print("Derivs parent relation", parent_rel)
            if parent_rel == alias.deriv:
                self.__merge_derived_verbs_with_root_forms(idx)
            return True

        elif property_.concept_name == alias.ol14:
            self.add_domain(idx, property_.concept_name)
            return True
        else:
            if property_.dep_par_relation == alias.pred:
                pre_token = self.idx_sequence[self.idx_sequence.index(idx) - 1]
                parent_of_pre_token, rel_of_pre_token = utils.find_proper_parent(pre_token,self) ##### isCompound yap
                if parent_of_pre_token == idx and rel_of_pre_token == alias.deriv:
                    if self.idx2property[parent_of_pre_token].isFrame:
                        return False
                    elif (property_.pos_tag == alias.adj) or (property_.pos_tag == alias.pron) or (
                        property_.pos_tag == alias.adv) or (property_.pos_tag == alias.noun):
                        #                    print("domain e girmesi lazım")
                        self.add_domain(idx, property_.concept_name)
                        return True
                else:
                    if (property_.pos_tag == alias.adj) or (property_.pos_tag == alias.pron) or (
                        property_.pos_tag == alias.adv) or (property_.pos_tag == alias.noun):
                        #                    print("domain e girmesi lazım")
                        self.add_domain(idx, property_.concept_name)
                        return True

    def __merge_derived_verbs_with_root_forms(self, idx):

        parent_idx_list = list(self.idx2parent[idx].keys()) if idx in self.idx2parent.keys() else \
        self.node2conn[idx].keys()
        parent_idx = parent_idx_list[0]
        parent_name = self.idx2property[parent_idx].concept_name
        self.idx2property[parent_idx].concept_name = self.idx2property[idx].concept_name \
                                                            if self.idx2property[parent_idx].concept_name== "_" \
                                                            else self.idx2property[parent_idx].concept_name

        self.idx2property[parent_idx].set_node_var_name(self.idx2property[idx].node_var_name)
        self.idx2property[idx].set_node_var_name("*")

        self.idx2property[parent_idx].pres_pos_tag = self.idx2property[idx].pos_tag
        self.idx2property[parent_idx].isFrame = self.idx2property[idx].isFrame if self.idx2property[idx].isFrame \
            else self.idx2property[parent_idx].isFrame
        self.idx2property[parent_idx].inflections = "|".join(
            [self.idx2property[idx].inflections, self.idx2property[parent_idx].inflections])

        # del amr[idx2property[idx][5]]
        Actions.connect_up_node_and_remove(self,idx)
        # moved[idx]=parent_idx

    def add_domain(self,idx, root_name):
        if root_name == alias.ol14:
            parent_idx = list(self.idx2parent[idx].keys())[0]
            parent_rel = list(self.idx2parent[idx].values())[0]

            obj = utils.find_children_connected_with_given_relation(idx, self.idx2parent, relation=alias.A1)
            if len(obj) > 0:
                obj = obj[0]
            else:
                ind = self.idx_sequence.index(idx) - 1
                obj = self.idx_sequence[ind]

            self.idx2property[obj].isFrame = True
            self.idx2property[obj].node_name = alias.domain
            doer = utils.find_children_connected_with_given_relation(idx, self.idx2parent, relation=alias.A0) \
                   + utils.find_children_connected_with_given_relation(idx, self.idx2parent, relation=alias.AA) \
                   + utils.find_children_connected_with_given_relation(idx, self.idx2parent, relation=alias.subj)


            if len(doer) == 0:
                doer = utils.find_children_connected_with_given_relation(obj, self.idx2parent, relation=alias.A0)

            self.idx2parent[obj] = {parent_idx: parent_rel}

            if len(doer) > 0:
                self.idx2parent[doer[0]] = {obj: alias.domain}
            self.idx2parent[idx] = {obj: ""}
            Actions.connect_up_node_and_remove(self, idx)
            #      print("it is domain, idx removed",idx)
            return True

        elif root_name == alias.domain:
            domain = utils.find_children_connected_with_given_relation(idx, self.idx2parent, relation=alias.domain)
            if len(domain) > 0:
                return False

            doer = [i for i in utils.find_reentrancy_connections(idx,self)
                    if self.node2conn[i][idx] == alias.A0]

            if len(doer) > 0:
                self.node2conn[doer[0]] = {idx: alias.domain}
            return False

        else:

            self.idx2property[idx].isFrame = True
            self.idx2property[idx].node_name = alias.domain
            doer =  utils.find_children_connected_with_given_relation(idx, self.idx2parent, relation=alias.A0) \
                   + utils.find_children_connected_with_given_relation(idx, self.idx2parent, relation=alias.AA) \
                   + utils.find_children_connected_with_given_relation(idx, self.idx2parent, relation=alias.subj)

            if len(doer) > 0:
                self.idx2parent[doer[0]] = {idx: alias.domain}
            else:
                self.add_null_subject(idx)
                doer = utils.find_children_connected_with_given_relation(idx, self.idx2parent, relation=alias.A0) \
                   + utils.find_children_connected_with_given_relation(idx, self.idx2parent, relation=alias.subj)

                if len(doer) > 0:
                    self.idx2parent[doer[0]] ={idx: alias.domain}
                else:
                    self.create_and_add_new_node(idx, alias.domain, tag=alias.noun, name=alias.concept_bu,
                                                 const_name=alias.concept_bu)
                    #              print("it  will be considered as well")

                    #        print(root_name,"it is domain")
            return False

    def node_surface_form(self,idx):
        surface_form = set(self.idx2property[idx].inflections.split("|"))
        name = self.idx2property[idx].concept_name

        if alias.able in surface_form:
            self.add_modality(idx)
        if alias.neg in surface_form:
            self.add_polarity(idx)
        if alias.imp in surface_form:
            self.add_imperative(idx)
        if alias.necessity in surface_form:
            self.add_necessary(idx)
        if alias.caus in surface_form:
            self.add_caus(idx)
        if alias.condition in surface_form:
            parent_idx = list(self.idx2parent[idx].keys())[0]
            self.idx2parent[idx][parent_idx] = alias.condition_
            if surface_form in alignment.key2removed:
                Actions.connect_up_node_and_remove(idx,self)

    def add_caus(self,idx):

        parent_idx = list(self.idx2parent[idx].keys())[0]
        parent_rel = list(self.idx2parent[idx].values())[0]

        caus_idx = self.create_and_add_new_node(parent_idx, parent_rel, tag=alias.verb, name=alias.yap_,
                                                    const_name=self.idx2property[idx].node_name)

        self.idx2property[caus_idx].dep_par_head = idx
        self.idx2parent[idx] = {caus_idx: alias.A1}
     #   Actions.connect_to_parent(self,idx)

        inf=""

        for p in self.idx2property[idx].inflections.split("|"):
            if p in alignment.pronouns.keys():
                inf = p.replace("P","A") + "|" + inf
            else:
                inf=p + "|" + inf

        self.idx2property[caus_idx].inflections = inf
        arga=self.add_null_subject(caus_idx, check=False)
     #   self.idx2parent[arga] = {caus_idx: alias.A0}

       # print(ppx.to_penman(self, 8, level=0))


    def add_imperative(self,idx):
        imperative_idx = self.create_and_add_new_node(idx, alias.mod_rel, tag=alias.noun, name=alias.imperative,
                                                      const_name=self.idx2property[idx].node_name)

        self.idx2property[imperative_idx].dep_par_head = idx

    def add_modality(self,idx):
        #  print("add modality")

        parent_idx = list(self.idx2parent[idx].keys())[0]
        parent_rel = list(self.idx2parent[idx].values())[0]

        modality_idx = self.create_and_add_new_node(parent_idx, parent_rel, tag=alias.verb, name=alias.possible,
                                                    const_name=self.idx2property[idx].node_name)
        self.idx2property[modality_idx].dep_par_head = idx
        self.idx2parent[idx] = {modality_idx: alias.A1}

    def __remove_determiner(self,idx):
        if self.idx2property[idx].concept_name in alignment.key2amr[alias.det_to_mod]+[alias.cok]:
            return False
        elif self.idx2property[idx].pos_tag == alias.adj and self.idx2property[idx].lemma_pos_tag == alias.num:
            return False
        elif self.idx2property[idx].pos_tag ==alias.noun and self.idx2property[idx].lemma_pos_tag == alias.num:
            return False
        else:
            Actions.connect_up_node_and_remove(self,idx)
            return True

    def add_necessary(self,idx):

        parent_idx, parent_rel = utils.find_proper_parent(idx,self)

        neces_idx = self.create_and_add_new_node(parent_idx, parent_rel, tag=alias.verb, name="zorla.01",
                                                 const_name=self.idx2property[idx].node_name)
        self.idx2property[neces_idx].dep_par_head = idx
        self.idx2parent[idx] = {neces_idx: alias.A2}

    def add_polarity(self,idx):
        polarity_idx = self.create_and_add_new_node(idx, alias.polarity, tag=alias.noun, name=alias.eksi,
                                                    const_name=self.idx2property[idx].node_name)
        self.idx2property[polarity_idx].dep_par_head = idx

    def add_reentrancy_in_an_order(self):
        frames = [pidx for pidx, property_ in self.idx2property.items() if property_.isFrame]

        noun_adj_verbs = [pidx for key, values in self.idx2parent.items() for pidx, prel in values.items() if
                          prel == alias.domain]
        frames += noun_adj_verbs
        # print("\nFRAMES",frames)
        nodes_having_reentrancy = {idx: value for idx, value in self.idx2edges.items()}

        for idx, value in nodes_having_reentrancy.items():
            if len(value) > 0:
                #       print("REENTRANCY",idx,value)
                frames_connections = [utils.find_connections_of_a_nodes(pidx,self) for pidx in frames]
                connection_names = utils.find_connnection_names(frames, frames_connections,self)
                #      print("Frame connections",frames_connections,"connection_names",connection_names)
                connect = []
                reentrancy = 0
                yap_check = 0

                if alias.A0 in value:
                    value_connections = utils.find_connections_of_a_nodes(idx,self)  #### yapan eden var mı bakılıcak
                    do_con = [con for con in value_connections if alias.yap in self.idx2property[con].concept_name]
                    if len(do_con) > 0:
                        self.node2conn[idx].update({do_con[0]: alias.A0})
                        value.remove(alias.A0)
                        yap_check = 1

                        #  value_connection_names = [find_connnection_names(frames,frames_connections)]

                for f, c in zip(frames, frames_connections):
                    if yap_check:
                        continue
                        # print("frames",f,"frames_connections",c,"reentrancy",reentrancy,"value",value)
                        # if len(value)>reentrancy:
                        #   if "AM-CAU" in value[reentrancy]:
                        #      reentrancy+=1

                    if len(value) > reentrancy:
                        if (idx not in c) and (
                                f not in connection_names or value[reentrancy] not in connection_names[f]):
                            #  print("eklendi",idx,f)
                            idx_ = utils.is_compound_idx(idx,self)
                            if idx != idx_:
                                self.idx2parent[idx_] = {f: value[reentrancy]}
                            else:
                                if idx in noun_adj_verbs:
                                    self.idx2parent[idx] = {f: value[reentrancy]}
                                else:
                                    self.node2conn[idx].update({f: value[reentrancy]})
                                    #    print("hangisi acaba ")
                            reentrancy += 1
                            # print(idx2edges,idx,idx2edges[idx],reentrancy)
                for i in range(0, reentrancy - 1):
                    del self.idx2edges[idx][0]



if __name__ == '__main__':
    import pandas as pd
    import numpy as np

    treebank = pd.read_csv("../resource/deneme.conll", names=[i for i in range(13)])

    treebank["Sentence"] = np.nan
    sentence_start_index = list(treebank[treebank[0] == 1].index)
    first_sent = treebank[sentence_start_index[0]:sentence_start_index[1]]
    treebank = preprocess.tag_sentences(treebank, sentence_start_index)
    treebank["rel_str"] = treebank[12]
    treebank["rel_str"].fillna("nope", inplace=True)
    sentences = preprocess.get_sentence_dfs(treebank, sentence_start_index)


    st = SpanGraph()
    st.create_graph(sentences[0].values)
    print(st.idx2parent)
    print(st.idx2edges)
    print(st.node2conn)

    print([a.write() for k,a in st.idx2property.items()])



