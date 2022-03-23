from aligner import alignment as align, alias
from parser.actions import Actions
from parser.graph import SpanGraph as Graph
from util import parser_utils as utils, preprocess


class AmrParser():
    def __init__(self):
        super().__init__()
        self.root=None
        self.graph=None

    def parse(self,sentence):
        self.graph=Graph().create_graph(sentence)
        self.__parse()
        return self.graph

    def __parse(self):
        idx = 0
        max_indexed_node = max(self.graph.idx2parent, key=int)
        while idx <= max_indexed_node:
            if idx in self.graph.idx2parent.keys():
                #        print("idx-parent rel",idx,idx2parent[idx])
                if not self.__node_post_process(idx):
                    self.__relation_post_process(idx)


            max_indexed_node = max(self.graph.idx2parent, key=int)
            idx += 1

        self.__transform_left()
        root = self.__find_root()
        self.graph.root = root



    def __node_post_process(self,idx):
        root_name = preprocess.to_lower(self.graph.idx2property[idx].concept_name)
        surface_name = self.graph.idx2property[idx].node_name
        parent_idx, parent_rel = utils.find_proper_parent(idx,self.graph)
        rel_check = False
        mappings = ""

        if root_name in align.key2amr[alias.remove_token_child_up]:
            mappings = alias.remove_token_child_up
        elif root_name in align.key2amr[alias.child_up_parent_down]:
            mappings = alias.child_up_parent_down
        elif root_name in align.key2amr[alias.only_parent_rel]:
            if align.key2amr[alias.only_parent_rel][root_name] == alias.medium:
                rel_check = 1
            mappings = alias.only_parent_rel
        elif root_name in align.key2amr[alias.function_based]:
            mappings = alias.function_based
        elif root_name in align.key2amr[alias.special_cases]:
            mappings = alias.special_cases
        elif root_name in align.quantities:
            mappings = alias.quantity
        elif root_name in align.aproximation:
            mappings = alias.approximation
        elif root_name in align.key2amr[alias.negation]:
            mappings = alias.negation
        elif root_name in align.key2amr[alias.question]:
            mappings = alias.question
        elif root_name in align.key2amr[alias.wh_questions]:
            mappings = alias.wh_questions
        elif root_name in align.key2amr[alias.have_degre]:
            mappings = alias.have_degre
        elif root_name in align.key2amr[alias.have_relation] and self.graph.idx2property[idx].pos_tag==alias.noun:
            mappings = alias.have_relation
        elif root_name in align.time_temporal_words.keys():
            mappings = alias.time_temporal_words
        elif root_name in align.key2amr[alias.det_to_mod]:
            mappings = alias.det_to_mod
        elif root_name in align.key2amr[alias.non_relations]:
            mappings = alias.non_relations
        elif root_name in align.key2amr[alias.locations]:
            mappings = alias.name_entities
        elif root_name in align.key2amr[alias.date_entity]:
            mappings = alias.date_entity
        elif root_name in align.key2amr[alias.nationality]:
            mappings = alias.nationality
        else:
            if surface_name == alias.domain:
                self.graph.add_domain(idx, surface_name)
            if surface_name in align.key2amr[alias.percentage]:
                mappings = alias.percentage
            else:
                return False
                #    print("mapping", mappings,"word:", root_name)
        return self.__add_proper_amr_relation_for_word(idx, root_name, parent_rel, parent_idx, mapping=mappings,
                                                rel_check=rel_check)



    def __relation_post_process(self,idx):

        parent_conn = self.graph.node2conn[idx]
        connection = self.graph.node2conn[idx]

        frame = self.graph.idx2property[idx].concept_name

        parent_idx = list(self.graph.idx2parent[idx].keys())[0]
        parent_rel = list(self.graph.idx2parent[idx].values())[0]
        #   print("relation post process", parent_rel,"\n")

        if parent_rel == alias.conj:
            self.__add_conjunction(idx)

        elif parent_rel == alias.coord:
            self.__handle_coordination(idx)

        elif parent_rel == alias.goal:
            self.__add_beneficiary_or_purpose(idx)

        elif parent_rel == alias.mod and self.graph.idx2property[idx].isFrame:
            #   print("add reification")
            self.__add_reification(idx, parent_idx)
        elif parent_rel in align.number_relations:
            #    print("add pre quant")
            if self.graph.idx2property[idx].pos_tag == alias.adj and \
                            self.graph.idx2property[idx].lemma_pos_tag == alias.num:
                #        print("add quant 1")
                self.__add_quant(idx, relation=parent_rel)
            elif  self.graph.idx2property[idx].pos_tag == alias.noun and \
                            self.graph.idx2property[idx].lemma_pos_tag == alias.num:
                #        print("add quant 2 ")
                self.__add_quant(idx, relation=parent_rel)
            elif parent_rel == alias.det:
                Actions.connect_up_node_and_remove(self.graph,idx)

        elif parent_rel == alias.cau:
            self.__add_cause(idx)

        elif parent_rel == alias.ext:
            root_name = self.graph.idx2property[idx].concept_name
            if root_name == alias.kere:
                self.__add_frequency(idx)

        elif parent_rel == alias.dub :
            self.__add_reduplication(idx, parent_idx)

        elif parent_rel == alias.two :
            self.__add_reduplication(idx, parent_idx,two=True)

        elif parent_rel == alias.mwe_conj:
            self.__handle_temp_expression(idx, parent_idx)

        elif parent_rel == alias.am_neg:
            child = utils.find_children_connected_with_given_relation(parent_idx, self.graph.idx2parent, relation=alias.polarity)
            #     print("am-neg child",child)
            if len(child) == 0:
                self.graph.add_polarity(parent_idx)
            Actions.connect_up_node_and_remove(self.graph,idx)

        elif parent_rel == alias.compound:
            self.__add_topic(idx, parent_idx)

        elif alias.enamex in parent_rel:
            self.__add_named_entity(idx, parent_rel, "")

        elif parent_rel in align.amrtag2rel:
            #       print("transfrer to amr")
            if  self.graph.idx2property[idx].lemma_pos_tag==alias.ip:
                self.graph.idx2parent[idx][parent_idx]=alias.prep_after
            elif self.graph.idx2property[idx].lemma_pos_tag == alias.madan:
                self.graph.idx2parent[idx][parent_idx] = alias.prep_without
            elif self.graph.idx2property[idx].lemma_pos_tag == alias.arak:
                self.graph.idx2parent[idx][parent_idx] = alias.prep_by
            elif self.graph.idx2property[idx].lemma_pos_tag ==alias.ince:
                self.graph.idx2parent[idx][parent_idx] = alias.prep_when
            elif self.graph.idx2property[idx].lemma_pos_tag == alias.ken:
                self.graph.idx2parent[idx][parent_idx] = alias.prep_while
            else:
                self.graph.idx2parent[idx][parent_idx] = align.amrtag2rel[parent_rel]

        elif parent_rel in align.rel2removed:
            Actions.connect_up_node_and_remove(self.graph,idx)



    def __add_topic(self,idx,  parent_idx):
        parent_rel = self.graph.idx2parent[idx][parent_idx]
        if parent_rel == alias.compound:
            self.graph.idx2parent[idx][parent_idx] = alias.topic
        else:
            previous_token = self.graph.idx_sequence[self.graph.idx_sequence.index(idx) - 1]
            if self.graph.idx2property[previous_token].concept_name == alias.ile:
                Actions.connect_up_node_and_remove(self.graph,previous_token)
            parent_idx = list(self.graph.idx2parent[idx].keys())[0]
            children = utils.find_parent_connections(idx,self.graph)
            Actions.connect_up_node_and_remove(self.graph,idx)
            self.graph.idx2parent[children[0]] = {parent_idx: alias.topic}
        return True

    def __handle_temp_expression(self,idx, parent_idx):

        name = self.graph.idx2property[idx].concept_name
        parent_name = self.graph.idx2property[parent_idx].concept_name
        if name == alias.suffix_ya and parent_name == alias.suffix_da:
            Actions.connect_up_node_and_remove(self.graph,idx)
            Actions.connect_up_node_and_remove(self.graph,parent_idx)
        elif name == alias.concept_bu and parent_name == alias.ara:
            Actions.connect_up_node_and_remove(self.graph,idx)
            Actions.connect_up_node_and_remove(self.graph,parent_idx)
        elif name == alias.o and parent_name == alias.zaman:
            Actions.connect_up_node_and_remove(self.graph,idx)
            Actions.connect_up_node_and_remove(self.graph,parent_idx)
        elif name == alias.concept_bu and parent_name == alias.yuz:
            # parent_relation = list(self.graph.idx2parent[parent_idx].values())[0]
            #      print("handle_temp_expression ,parent_relation",parent_relation)
            self.__add_cause(idx)

    def __add_reduplication(self,idx, parent_idx,two=False):
        if two:
            s = self.graph.idx_sequence.index(idx)
            parent_idx = self.graph.idx_sequence[s+1]

        self.graph.idx2parent[idx]={parent_idx:alias.degree}
        self.graph.idx2property[idx].node_name = alias.cok
        self.graph.idx2property[idx].concept_name = alias.cok
        utils.find_represent_char_of_names(idx,self.graph.idx2property)

    def __find_root(self):
        root = [key for key, value in self.graph.idx2parent.items() for node, node_rel in value.items() if node_rel == alias.pred]
        if len(root) == 0:
            root = [key for key, value in self.graph.node2conn.items() for node, node_rel in value.items() if node_rel == alias.pred]
            if len(root) > 0:
                r = root[0]
                if r in self.graph.idx2parent:
                    swp = self.graph.idx2parent[r]
                    self.graph.idx2parent[r] = self.graph.node2conn[r]
                    self.graph.node2conn[r] = swp
                else:
                    self.graph.idx2parent[r] = self.graph.node2conn[r]
                    del self.graph.node2conn[r]

        return root[0]

    def __transform_left(self):
        for idx in self.graph.idx2parent.copy().keys():
            parent_idx = list(self.graph.idx2parent[idx].keys())[0]
            parent_rel = list(self.graph.idx2parent[idx].values())[0]
            root_name = self.graph.idx2property[idx].concept_name

            if parent_rel in align.amrtag2rel:
                if parent_rel[0] == "C":
                    self.__handle_Cs(idx, parent_rel, parent_idx)

                else:
                    #             print("tag rel",idx,parent_idx,amrtag2rel[parent_rel])
                    self.graph.idx2parent[idx][parent_idx] = align.amrtag2rel[parent_rel]
            elif parent_rel in align.special_relations:
                self.__handle_obj_subj(idx, parent_rel, parent_idx)

            if idx in self.graph.node2conn.keys():
                if len(self.graph.node2conn[idx]) > 0:
                    parent_rel = list(self.graph.node2conn[idx].values())[0]
                    parent_idx = list(self.graph.node2conn[idx].keys())[0]
                    #     print(parent_rel)
                    if parent_rel in align.amrtag2rel:
                        if parent_rel[0] == "C":
                            self.__handle_Cs(idx, parent_rel, parent_idx, type_=2)
                        else:
                            #       print("tag rel",idx,parent_idx,amrtag2rel[parent_rel])
                            self.graph.node2conn[idx][parent_idx] = align.amrtag2rel[parent_rel]
            if root_name in align.key2removed:
                #  print(root_name,"key2removed")
                self.__word_removal(idx)

    def __word_removal(self,idx):
        parent_rel = list(self.graph.idx2parent[idx].values())[0]
        parent_idx = list(self.graph.idx2parent[idx].keys())[0]
        #    print(parent_rel)
        if parent_rel[0] == "A":
            if len(parent_rel) == 2:
                child = utils.find_parent_connections(idx,self.graph)
                #            print("child",child)
                if len(child) > 0:
                    child = child[0]
                    Actions.connect_up_node_and_remove(self.graph,idx)
                    self.graph.idx2parent[child] = {parent_idx: parent_rel}
        elif parent_rel in [alias.manner, alias.instrument, alias.mod_rel]:
            child = utils.find_parent_connections(idx,self.graph)
            #        print("child",child)
            if len(child) > 0:
                child = child[0]
                Actions.connect_up_node_and_remove(self.graph,idx)
                self.graph.idx2parent[child] = {parent_idx: parent_rel}

            else:
                Actions.connect_up_node_and_remove(self.graph,idx)

        else:
            Actions.connect_up_node_and_remove(self.graph,idx)

    def __handle_obj_subj(self,idx, parent_rel, parent_idx):
        children = utils.find_children_connected_with_given_relation(parent_idx, self.graph.idx2parent,
                                                                     relation=align.special_relations[parent_rel])
        #  print("handle obj subj",children,special_relations[parent_rel])
        # print(node2conn)
        if len(children) == 0:
            self.graph.idx2parent[idx][parent_idx] = align.special_relations[parent_rel]

        else:
            if len(self.graph.node2conn[idx]) > 0:
                reent_rel = list(self.graph.node2conn[idx].values())[0]
                reent_idx = list(self.graph.node2conn[idx].keys())[0]
                if reent_rel == align.special_relations[parent_rel]:
                    self.graph.node2conn[idx] = {}
                    self.graph.idx2parent[idx] = {reent_idx: alias.A1}
                else:
                    self.graph.idx2edges[idx] = [align.special_relations[parent_rel]]
                    #         print(idx, "idx2edges", idx2edges)
                    self.graph.add_reentrancy_in_an_order()
                    reent_rel = list(self.graph.node2conn[idx].values())[0]
                    reent_idx = list(self.graph.node2conn[idx].keys())[0]
                    self.graph.node2conn[idx] = {}
                    self.graph.idx2parent[idx] = {reent_idx: alias.A1}
            else:
                self.graph.idx2edges[idx] = [align.special_relations[parent_rel]]
                #       print(idx, "idx2edges", idx2edges)
                self.graph.add_reentrancy_in_an_order()
                if len(self.graph.node2conn[idx]) > 0:
                    reent_rel = list(self.graph.node2conn[idx].values())[0]
                    reent_idx = list(self.graph.node2conn[idx].keys())[0]
                    self.graph.node2conn[idx] = {}
                    self.graph.idx2parent[idx] = {reent_idx: alias.A1}
                else:
                    self.graph.idx2parent[idx][parent_idx] = align.special_relations[parent_rel]

    def __handle_Cs(self,idx, parent_rel, parent_idx, type_=1):

        rel = parent_rel.split("-")[0]

        children = utils.find_children_connected_with_given_relation(parent_idx,self.graph,relation=rel) if type_ == 1 \
                else utils.find_reentrancy_connected_with_given_relation(parent_idx, self.graph,relation=rel)

        if len(children) > 0:
            common_parent = self.graph.create_and_add_new_node(parent_idx, rel, name=alias.ve,
                                                               postag=alias.noun, const_name=alias.ve)
            if type_ == 1:
                self.graph.idx2parent[idx] = {parent_idx: alias.op1}
                for e, i in enumerate(children):
                    self.graph.idx2parent[i] = {parent_idx: alias.op + str(e + 2)}
            else:
                self.graph.node2conn[idx] = {parent_idx: alias.op1}
                for e, i in enumerate(children):
                    self.graph.node2conn[i] = {parent_idx: alias.op + str(e + 2)}

    def __add_frequency(self,idx):
        previous_token = self.graph.idx_sequence[self.graph.idx_sequence.index(idx) - 1]
        parent_idx = list(self.graph.idx2parent[idx].keys())[0]
        if parent_idx != previous_token:
            Actions.connect_up_node_and_remove(self.graph,idx)
            self.graph.idx2parent[previous_token] = {parent_idx: alias.frequency}
        else:
            Actions.connect_up_node_and_remove(self.graph,idx)

    def __add_quant(self, idx, relation=alias.numex):
        '''MWE:NUMEX olmayan parent sequence bul. Parent of parent taki kelimenin sayı içerip içermediğine bak.
        İçeriyorsa birleştir.
        '''
        approx = 0
        quantity = 0
        aproximation_idx = None
        quantity_idx = None
        temporal_word = 0

        # print("add quant")
        if self.graph.idx2property[idx].node_name in align.aproximation:
            # print(aproximation[idx2property[idx][5]])
            parent_idx, parent_relation = utils.find_proper_parent(idx,self.graph)
            # print(parent_idx,parent_relation)

            aproximation_idx = self.graph.create_and_add_new_node(parent_idx,parent_relation,
                                                                       name=self.graph.idx2property[idx].node_name,
                                                                       const_name=align.aproximation[self.graph.idx2property[idx].node_name])

            self.graph.idx2property[aproximation_idx].dep_par_head = idx
            approx = 1
        else:

            parent_idx, parent_relation, number_sequence = utils.find_parent_idx_with_given_relation(idx,self.graph, relation=relation)
            # number_sequence+=sequence
            #   print("quant",parent_idx,parent_relation,number_sequence,"\n")
            if self.graph.idx2property[parent_idx].lemma_pos_tag != alias.num:
                number_sequence.remove(parent_idx)
            for i in range(len(number_sequence)):
                idx = Actions.merge(self.graph,idx, number_sequence[i])
                #     print("new idx",idx)

        ##### Quantity########
        parent_idx, parent_relation = utils.find_proper_parent(idx,self.graph)
        if parent_idx != 0:
            if self.graph.idx2property[parent_idx].concept_name in align.quantities:
                quantity_idx = self.__add_quantity(parent_idx)
                quantity = 1

        ##### Before-After########
        parent_of_parent_idx, parent_of_parent_relation = utils.find_proper_parent(parent_idx,self.graph)
        # print("ne acaba",idx2property[parent_of_parent_idx][5])
        if parent_of_parent_idx != 0:
            if self.graph.idx2property[parent_of_parent_idx].concept_name in align.time_temporal_words:
                # print("Before-After")

                temporal_word_idx = self.graph.create_and_add_new_node(parent_of_parent_idx, alias.op1,
                                                                       name=alias.suan,
                                                                       const_name=alias.suan)
                self.graph.idx2property[temporal_word_idx].dep_par_head = parent_of_parent_idx
                temporal_word = 1

        if quantity and approx:
            self.graph.idx2parent[aproximation_idx] = {parent_of_parent_idx: alias.quant}
            self.graph.idx2parent[quantity_idx] = {aproximation_idx: alias.op1}
            self.graph.idx2parent[idx] = {quantity_idx: alias.quant}
            self.graph.idx2parent[parent_idx] = {quantity_idx: alias.unit}

        elif approx:
            self.graph.idx2parent[idx] = {aproximation_idx: alias.op1}
            self.graph.idx2parent[aproximation_idx][parent_idx] = alias.quant

        elif quantity:
            self.graph.idx2parent[parent_idx] = {quantity_idx: alias.unit}
            self.graph.idx2parent[idx] = {quantity_idx: alias.quant}
            if temporal_word:
                self.graph.idx2parent[quantity_idx][parent_of_parent_idx] = alias.quant
        else:
            self.graph.idx2parent[idx][parent_idx] = alias.quant
            if temporal_word:
                self.graph.idx2parent[parent_idx][parent_of_parent_idx] = alias.op1

    def __add_reification(self,idx, parent_idx):
        parent_name = self.graph.idx2property[parent_idx].concept_name
        if parent_name not in align.key2amr[alias.special_cases]:
            children = utils.find_reentrancy_connections(idx,self.graph)
            reified = [utils.is_proper_child(child,self.graph) for child in children]
            if parent_idx in reified:
                rel = self.graph.node2conn[parent_idx][idx]
                new_rel = rel + "-of"
                self.graph.idx2parent[idx] = {parent_idx: new_rel}
                del self.graph.node2conn[parent_idx][idx]

    def __add_proper_amr_relation_for_word(self,idx, root_name, parent_rel, parent_idx, mapping="", rel_check=False):
        rels = [alias.mod, alias.subj]
        if rel_check:
            if parent_rel != rels[rel_check]:
                return False

        if mapping == alias.remove_token_child_up:
            previous_token = self.graph.idx_sequence[self.graph.idx_sequence.index(idx) - 1]
            if previous_token == parent_idx:
                Actions.connect_up_node_and_remove(self.graph,idx)
                return True
            else:
                if previous_token in self.graph.idx2property:
                    Actions.connect_up_node_and_remove(self.graph,idx)
                    self.graph.idx2parent[previous_token] = {parent_idx: align.key2amr[mapping][root_name]}
                    return True
                else:
                    return False
        elif mapping == alias.child_up_parent_down:
            del self.graph.idx2parent[idx]
            self.graph.idx2parent[idx] = {parent_idx: align.key2amr[mapping][root_name]}
            return True
        elif mapping == alias.function_based:
            if align.key2amr[alias.function_based][root_name] == alias.add_topic:
               return  self.__add_topic(idx, parent_idx)
            elif align.key2amr[alias.function_based][root_name] == alias.add_benze_frame:
                return self.__add_benze_frame(idx,root_name)
            elif align.key2amr[alias.function_based][root_name] == alias.handle_modality_words:
                return self.__handle_modality_words(idx, parent_idx)
            elif align.key2amr[alias.function_based][root_name] == alias.change_olarak:
                return self.__change_olarak(idx)

        elif mapping == alias.only_parent_rel:
            next_token = self.graph.idx_sequence[self.graph.idx_sequence.index(idx) + 1]
            if self.graph.idx2property[next_token].concept_name == alias.ki:
                self.graph.idx2property[idx].concept_name = self.graph.idx2property[idx].concept_name \
                                                                 + "-" + self.graph.idx2property[next_token].concept_name
                utils.find_represent_char_of_names(idx,self.graph.idx2property)
                Actions.connect_up_node_and_remove(self.graph,next_token)
            parent_idx = utils.is_compound_idx(parent_idx,self.graph)
            self.graph.idx2parent[idx] = {parent_idx: align.key2amr[mapping][root_name]}
            return True
        elif mapping == alias.special_cases:
            self.__handle_special_cases(idx, root_name)
            return True
        elif mapping == alias.quantity:
            self.__add_quantity(idx, connect=True)
            return True
        elif mapping == alias.approximation:
            self.__add_approximation(idx)
            return True
        elif mapping == alias.question:
            self.__add_questions(idx, root_name)
            return True
        elif mapping == alias.wh_questions:
            return self.__add_wh_questions(idx, root_name, parent_rel, parent_idx)
        elif mapping == alias.domain:
            return self.graph.add_domain(idx, root_name)
        elif mapping == alias.have_degre:
            return self.__add_relative_degree(idx, root_name)
        elif mapping == alias.time_temporal_words:
            self.__handle_time_temporals(idx)
            return False
        elif mapping == alias.det_to_mod:
            if parent_rel == alias.det:
                if self.graph.idx2property[parent_idx].pos_tag == alias.verb:
                    self.graph.idx2parent[idx][parent_idx] = alias.mod
                if self.graph.idx2property[parent_idx].pos_tag== alias.noun:
                    self.graph.idx2parent[idx][parent_idx] = alias.mod
            return False
        elif mapping == alias.non_relations:
            if root_name == alias.icin and parent_rel != alias.cau and parent_rel != alias.goal:
                children = utils.find_parent_connections(idx,self.graph)
                if self.graph.idx2property[children[0]].pos_tag == alias.pron:
                    self.__add_beneficiary_or_purpose(idx)
                else:
                    self.__add_cause(idx)
                return True
        elif mapping == alias.name_entities:
            entity = align.key2amr[alias.locations][root_name]
            self.__add_named_entity(idx, alias.single, root_name)
            return True
        elif mapping == alias.have_relation:
            self.__add_have_rel(idx, root_name, parent_rel, parent_idx)
            return True
        elif mapping == alias.negation:
            return self.__handle_negation_words(idx, root_name, parent_idx, parent_rel)
        elif mapping == alias.date_entity:
            return self.__add_date_entity(idx, root_name, parent_idx, parent_rel)
        elif mapping == alias.nationality:
            return self.__add_nationality(idx, root_name, parent_idx, parent_rel)
        elif mapping == alias.percentage:
            return self.__add_percentage(idx, root_name, parent_idx, parent_rel)
        else:
            return False

    def __add_date_entity(self,idx, root_name, parent_idx, parent_rel):

        date_entity_idx = self.graph.create_and_add_new_node(parent_idx, parent_rel, tag=alias.noun,
                                                             const_name=self.graph.idx2property[idx].node_name,
                                                             name=alias.date_entity)
        self.graph.idx2property[date_entity_idx].dep_par_head = idx
        if parent_idx != 0:
            if (self.graph.idx2property[parent_idx].concept_name == alias.gun) or \
                    (self.graph.idx2property[parent_idx].concept_name == alias.ay):
                #      print("buraya ne düşüyormuş bakalım",idx2property[parent_idx][5],)
                parent_of_parent, parent_rel_of_parent = utils.find_proper_parent(parent_idx,self.graph)

                Actions.connect_up_node_and_remove(self.graph,parent_idx)
                #      print("root name",root_name,parent_of_parent,parent_rel_of_parent )
                self.graph.idx2parent[date_entity_idx] = {parent_of_parent: parent_rel_of_parent}
                self.graph.idx2parent[idx] = {date_entity_idx: align.key2amr[alias.date_entity][root_name]}
            else:
                #       print("parent idx:",parent_idx)
                self.graph.idx2parent[idx] = {date_entity_idx: align.key2amr[alias.date_entity][root_name]}

    def __add_nationality(self,idx, root_name, parent_idx, parent_rel):
        if parent_rel != alias.op1:
            country_idx = self.graph.create_and_add_new_node(parent_idx, parent_rel,
                                                             tag=alias.noun, name=alias.ulke,
                                                             const_name=self.graph.idx2property[idx].node_name,
                                                             check=False,
                                                             verb_frame=False)
            wiki_idx = self.graph.create_and_add_new_node(country_idx, alias.wiki, tag=alias.noun, name="-",
                                                         const_name=self.graph.idx2property[idx].node_name,
                                                         check=False, verb_frame=False)
            name_idx = self.graph.create_and_add_new_node(country_idx, alias.name, tag=alias.noun,
                                                          name=align.key2amr[alias.nationality][root_name],
                                                          const_name=self.graph.idx2property[idx].node_name,
                                                          check=False, verb_frame=False)

            self.graph.idx2property[country_idx].dep_par_head= idx
            self.graph.idx2property[wiki_idx].dep_par_head = idx
            self.graph.idx2property[name_idx].dep_par_head = idx
            Actions.connect_up_node_and_remove(self.graph,idx)
            return True
        else:
            return False

    def __add_percentage(self,idx, root_name, parent_idx, parent_rel):
        #  print("add_percentage")

        if alias.pct in parent_rel:
            parent_of_parent, parent_rel_of_parent = utils.find_proper_parent(parent_idx,self.graph)
            percentage_entity_idx = self.graph.create_and_add_new_node(parent_of_parent, parent_rel_of_parent,
                                                                       tag=alias.noun,
                                                                       const_name=self.graph.idx2property[idx].node_name,
                                                                       name=alias.percentage_entity)
            self.graph.idx2parent[parent_idx] = {percentage_entity_idx: alias.value}
            Actions.connect_up_node_and_remove(self.graph,idx)
            return True
        return False

    def __handle_negation_words(self,idx, root_name, parent_idx, parent_rel):
        #    print("\nhandle_negation_words")
        if parent_idx != 0:
            if self.graph.idx2property[parent_idx].concept_name in align.key2amr[alias.question]:
                child = utils.find_parent_connections(idx,self.graph)
                if len(child) == 0:
                    Actions.connect_up_node_and_remove(self.graph,idx)
                    child =  utils.find_parent_connections(parent_idx,self.graph)

                parent_of_parent, parent_of_parent_rel =  utils.find_proper_parent(parent_idx,self.graph)
                if len(child) == 0:
                    if parent_of_parent_rel == alias.coord:
                        child = [parent_of_parent]
                        parent_of_parent, parent_of_parent_rel =  utils.find_proper_parent(parent_of_parent,self.graph)

                if len(child) > 0:
                    tag_represent_idx = self.graph.create_and_add_new_node(parent_of_parent, parent_of_parent_rel, tag=alias.noun,
                                                                           name=alias.onay_talebi,
                                                                           const_name=self.graph.idx2property[child[0]].node_name)
                    self.graph.idx2property[tag_represent_idx].dep_par_head = child[0]
                    self.graph.idx2parent[child[0]] = {tag_represent_idx: alias.A1}

                    Actions.connect_up_node_and_remove(self.graph,parent_idx)
                    return True
                    # else:

        else:
            child = utils.find_children_connected_with_given_relation(idx, self.graph.idx2parent, relation=alias.A1) + \
                    utils.find_children_connected_with_given_relation(idx, self.graph.idx2parent, relation=alias.obj)
            #       print("değil root. obj child of değil",child)
            if len(child) == 0:
                child = utils.find_children_connected_with_given_relation(idx, self.graph.idx2parent, relation=alias.A0) + \
                        utils.find_children_connected_with_given_relation(idx, self.graph.idx2parent, relation=alias.subj)
            if len(child) > 0:
                self.graph.add_domain(idx, root_name)
                Actions.replace_node(self.graph, idx, child[0])
                self.graph.add_polarity(child[0])
                return True

        return False

    def __add_have_rel(self,idx, root_name, parent_rel, parent_idx):

        if parent_rel == alias.appos:


            have_rel = self.graph.create_and_add_new_node(parent_idx, alias.A0_of, tag=alias.noun,
                                                          name=alias.sahip_ilişki_role_91,
                                                          const_name=self.graph.idx2property[idx].node_name,
                                                          check=False, verb_frame=False)
            self.graph.idx2property[have_rel].dep_par_head = idx


        else:
            person_idx = self.graph.create_and_add_new_node(parent_idx, parent_rel, tag=alias.noun, name=alias.person,
                                                            const_name=self.graph.idx2property[idx].node_name,
                                                            check=False, verb_frame=False)
            self.graph.idx2property[person_idx].dep_par_head= idx
            #
            have_rel = self.graph.create_and_add_new_node(person_idx, alias.A0_of, tag=alias.noun,
                                                          name=alias.sahip_ilişki_role_91,
                                                          const_name= self.graph.idx2property[idx].node_name,
                                                          check=False, verb_frame=False)
            self.graph.idx2property[have_rel].dep_par_head = idx

            self.graph.idx2parent[idx] = {have_rel: alias.A2}
        children = utils.find_parent_connections(idx,self.graph)
        if len(children) > 0:
            self.graph.idx2parent[children[0]] = {have_rel: alias.A1}
        else:
            surface_form = list(set(self.graph.idx2property[idx].inflections.split("|")))
            if surface_form[1] in align.pronouns:
                pronoun_idx = self.graph.create_and_add_new_node(have_rel, alias.A1, tag=alias.noun, name=align.pronouns[surface_form[1]],
                                                      const_name=self.graph.idx2property[idx].node_name,
                                                      check=False, verb_frame=False)
        return True

    def __add_named_entity(self,idx, rel, root_name):

        internal_entity_idx, internal_entity_relation, relation_sequence = utils.find_parent_idx_with_given_relation(idx,self.graph,
                                                                                                               relation=rel)
        if rel == alias.single:
            par = list(self.graph.idx2parent[idx].values())[0]
            if par == alias.name:
                return False

            entity_name = align.key2amr[alias.locations][root_name]

            const_name = self.graph.idx2property[idx].node_name

            person_idx = self.graph.create_and_add_new_node(internal_entity_idx, internal_entity_relation,
                                                            tag=alias.noun, name=entity_name, const_name=const_name, check=False,
                                                            verb_frame=False)
            wiki_idx = self.graph.create_and_add_new_node(person_idx, alias.wiki, tag=alias.noun, name="-", const_name=const_name,
                                                          check=False, verb_frame=False)
            name_idx = self.graph.create_and_add_new_node(person_idx, alias.name, tag=alias.noun, name=alias.isim,
                                                          const_name=const_name, check=False, verb_frame=False)

            self.graph.idx2property[person_idx].dep_par_head = idx
            self.graph.idx2property[wiki_idx].dep_par_head = idx
            self.graph.idx2property[name_idx].dep_par_head = idx

            self.graph.idx2parent[idx] = {name_idx: alias.op1}

        else:

            entity_type = rel.split(":")[2]
            entity_name = ""
            if entity_type == alias.pers:
                entity_name = alias.person
            elif entity_type == alias.org:
                entity_name = alias.organizasyon
            elif entity_type == alias.loc:
                entity_name = alias.ulke

            relation_sequence = [idx] + relation_sequence

            parent_of_interna_entity_idx, parent_of_interna_entity_rel = utils.find_proper_parent(internal_entity_idx,self.graph)

            const_name_id = relation_sequence[len(relation_sequence) - 2]
            const_name = self.graph.idx2property[const_name_id].concept_name

            person_idx = self.graph.create_and_add_new_node(parent_of_interna_entity_idx, parent_of_interna_entity_rel,
                                                            tag=alias.noun, name=entity_name, const_name=const_name, check=False,
                                                            verb_frame=False)
            wiki_idx = self.graph.create_and_add_new_node(person_idx, alias.wiki, tag=alias.noun, name="-", const_name=const_name,
                                                          check=False, verb_frame=False)
            name_idx = self.graph.create_and_add_new_node(person_idx, alias.name, tag=alias.noun, name=alias.isim,
                                                          const_name=const_name, check=False, verb_frame=False)

            self.graph.idx2property[person_idx].dep_par_head = const_name_id
            self.graph.idx2property[wiki_idx].dep_par_head = const_name_id
            self.graph.idx2property[name_idx].dep_par_head = const_name_id

            for i, seq_idx in enumerate(relation_sequence):
                rel_name = alias.op + str(i)
                self.graph.idx2parent[seq_idx] = {name_idx: rel_name}

    def __add_cause(self,idx):
        parent_idx, parent_relation = utils.find_proper_parent(idx,self.graph)
        idx_to_be_parent = idx
        parent_of_ol, parent_rel_ol = utils.find_proper_parent(parent_idx,self.graph)

        if self.graph.idx2property[idx].concept_name == alias.concept_bu:

            parent_of_parent_ol, parent_of_parent_rel_ol = utils.find_proper_parent(parent_of_ol,self.graph)
            cause_idx = self.graph.create_and_add_new_node(parent_of_parent_ol, parent_of_parent_rel_ol,
                                                           tag=alias.verb, name=alias.ol17, const_name=alias.ol17)
            self.graph.idx2property[cause_idx].dep_par_head = idx
            self.graph.idx2parent[idx] = {cause_idx: alias.A0}
            self.graph.idx2parent[parent_of_ol] = {cause_idx: alias.A1}
            Actions.connect_up_node_and_remove(self.graph,parent_idx)


        else:
            ### Eğer sözcük için ise için'i ol.17 ile değiştir ve ol.17'yi parent in parent ına bağla
            if self.graph.idx2property[idx].concept_name == alias.icin:
                self.graph.idx2property[idx].node_name =alias.ol17
                self.graph.idx2property[idx].concept_name = alias.ol17
                self.graph.idx2property[idx].isFrame = True
                self.graph.idx2property[idx].pos_tag = alias.verb
                self.graph.idx2property[idx].lemma_pos_tag = alias.verb


                utils.find_represent_char_of_names(idx,self.graph.idx2property)
                self.graph.idx2parent[idx] = {parent_of_ol: parent_rel_ol}
                child = utils.find_parent_connections(idx,self.graph)[0]

                self.graph.idx2parent[child][idx] = alias.A0
                cause_idx = idx

            else:
                cause_idx=self.graph.create_and_add_new_node(parent_of_ol, parent_rel_ol, tag=alias.verb,
                                                             name=alias.ol17,
                                                             const_name=alias.ol17,
                                                             check=False,
                                                             verb_frame=False)

                self.graph.idx2property[cause_idx].dep_par_head = idx
                self.graph.idx2parent[idx] = {cause_idx: alias.A0}
                # print("ol 17 has been added",idx2parent)
                idx_to_be_parent = cause_idx

            self.graph.idx2parent[parent_idx] = {idx_to_be_parent: alias.A1}
            children = utils.find_parent_connections(idx_to_be_parent,self.graph)
            if parent_rel_ol == alias.coord:
                self.__handle_coordination(cause_idx)
            elif parent_rel_ol == alias.conj:
                self.__add_conjunction(idx)
                # print("2",idx2parent)
                # print("cause ",children)

    def __handle_coordination(self,idx):

        name = self.graph.idx2property[idx].concept_name
        parent_idx, parent_relation, seq = utils.find_parent_idx_with_given_relation(idx,self.graph)
        if name == alias.ve:
            _, parent_of_parent_rel = utils.find_proper_parent(parent_idx,self.graph)
            if alias.op not in parent_of_parent_rel:
                self.__add_ve(idx, seq, parent_idx, parent_relation, punc=False, cjnt=True)
            else:
                Actions.connect_up_node_and_remove(self.graph,idx, amr_remove=False)

        elif name == alias.ile and self.graph.idx2property[idx].pos_tag == alias.cnjc:
            parent_of_parent_idx, parent_of_parent_rel = utils.find_proper_parent(parent_idx,self.graph)
            self.graph.idx2parent[parent_idx][parent_of_parent_idx] = alias.instrument
            Actions.connect_up_node_and_remove(self.graph,idx)
        else:
            if alias.suffix_de in self.graph.idx2property[parent_idx].concept_name:
                children = utils.find_children_connected_with_given_relation(parent_idx, self.graph.idx2parent, relation=alias.A1)
                if len(children) == 0:
                    children = utils.find_reentrancy_connected_with_given_relation(parent_idx, self.graph, relation=alias.A1)
                self.graph.idx2parent[idx] = {parent_idx: alias.A1}
                if len(children) > 0:
                    self.graph.idx2parent[children[0]] = {idx: alias.A1}
                    # if children[0] in node2conn:
                    # del node2conn[children[0]][parent_idx]
            else:
                #    print("bura 3")
                next_id = self.graph.idx_sequence.index(idx) + 1
                if next_id < len(self.graph.idx_sequence):
                    next_token = self.graph.idx_sequence[next_id]
                    next_rel = self.graph.idx2property[next_token].dep_par_relation
                    if next_rel != alias.conj:
                        #          print("bura 1")
                        self.__add_ve(idx, seq, parent_idx, parent_relation)
                    else:
                        self.__add_conjunction(idx)
                else:
                    #     print("bura 2")
                    self.__add_ve(idx, seq, parent_idx, parent_relation)

    def __add_conjunction(self,idx):
        # print("add conj")
        name = preprocess.to_lower(self.graph.idx2property[idx].concept_name)
        pos_tag = self.graph.idx2property[idx].pos_tag
        #   print("hem mi ne mi  ve conj mu acaba ".upper(),name,pos_tag)
        parent_idx, parent_relation, seq = utils.find_parent_idx_with_given_relation(idx,self.graph)

        if name == alias.ama or name == alias.fakat:
            #      print("bu bir contrast")
            self.__add_contrast(idx)
        elif name == alias.ve or name == alias.veya or name == alias.ile or name == alias.suffix_de:
            if name != alias.ve:
                self.graph.idx2property[idx].concept_name = alias.ve
                self.graph.idx2property[idx].node_name = alias.ve
                utils.find_represent_char_of_names(idx,self.graph.idx2property)

            _, parent_of_parent_rel = utils.find_proper_parent(parent_idx,self.graph)
            # print("yep",parent_idx,parent_relation,seq,"parent of parent",parent_of_parent_rel)
            if alias.op not in parent_of_parent_rel:
                self.__add_ve(idx, seq, parent_idx, parent_relation, punc=False, cjnt=True)
            else:
                Actions.connect_up_node_and_remove(self.graph,idx, amr_remove=False)

        elif name == alias.hem and pos_tag == alias.cnjc:
            # print("hem ve conj mu acaba ",name,pos_tag)
            parent_of_parent_idx, parent_of_parent_relation, seq = utils.find_parent_idx_with_given_relation(parent_idx,self.graph)
            Actions.connect_up_node_and_remove(self.graph,idx)
            if "op" not in parent_of_parent_relation:
                # print("op değil başka bişi")
                self.__add_ve(parent_idx, seq, parent_of_parent_idx, parent_of_parent_relation, punc=True)
        elif name == alias.ne and pos_tag == alias.cnjc:
            # print("ne başka bişi")
            parent_of_parent_idx, parent_of_parent_relation, seq = utils.find_parent_idx_with_given_relation(parent_idx,self.graph)
            parent_of_parent_of_parent_idx, parent_of_parent_of_parent_rel = utils.find_proper_parent(parent_of_parent_idx,self.graph)
            Actions.connect_up_node_and_remove(self.graph,idx)
            if alias.op not in parent_of_parent_relation:
                self.__add_ve(parent_idx, seq, parent_of_parent_idx, parent_of_parent_relation, punc=True)
                self.graph.add_polarity(parent_of_parent_of_parent_idx)
        else:
            if pos_tag != alias.cnjc:
                #         print("buraya mı düşer acaba",pos_tag, name,"control",conj)
                if pos_tag == alias.punc:
                    #             print("buraya düşmesi gerekiyor")
                    Actions.connect_up_node_and_remove(self.graph,idx)
                elif name == alias.eger:
                    Actions.connect_up_node_and_remove(self.graph,idx)
                else:
                    parent_idx, parent_relation, seq = utils.find_parent_idx_with_given_relation(idx,self.graph)
                    self.__add_ve(idx, seq, parent_idx, parent_relation, punc=True)
            else:
                #       print("neden buraya düşmüyorsun".upper())
                Actions.connect_up_node_and_remove(self.graph,idx)

    def __add_contrast(self,idx):
        self.graph.idx2property[idx].concept_name = alias.or_
        self.graph.idx2property[idx].node_name = alias.or_[:-3]
        utils.find_represent_char_of_names(idx,self.graph.idx2property)

        optx_idx, _ = utils.find_proper_parent(idx,self.graph)
        # optx_idx=list(idx2parent[idx].keys())[0]
        opty_idx, _ = utils.find_proper_parent(optx_idx,self.graph)
        # opty_idx=list(idx2parent[optx_idx].keys())[0]

        if opty_idx != 0:
            parent_of_opty_idx, parent_of_opty_rel = utils.find_proper_parent(opty_idx,self.graph)
            # parent_of_opty_idx=list(idx2parent[opty_idx].keys())[0]
            # parent_of_opty_rel=list(idx2parent[opty_idx].values())[0]
            self.graph.idx2parent[idx] = {parent_of_opty_idx: parent_of_opty_rel}

            utils.make_parent_to_sibling(self.graph, optx_idx, opty_idx, idx, alias.A1, alias.A2)
        else:
            _, parent_of_optx_rel = utils.find_proper_parent(optx_idx,self.graph)
            # parent_of_optx_rel=list(idx2parent[optx_idx].values())[0]
            self.graph.idx2parent[idx] = {opty_idx: parent_of_optx_rel}

            self.graph.idx2parent[optx_idx] = {idx: alias.A2}

    def __add_ve(self,idx, seq, parent_idx, parent_relation, punc=True, cjnt=False):

        parent_of_parent_idx, parent_of_parent_rel = utils.find_proper_parent(parent_idx,self.graph)
        # print("print(parent_of_parent_idx)",parent_of_parent_idx,"parent_idx",parent_idx)
        if punc:
            and_idx = self.graph.create_and_add_new_node(parent_of_parent_idx, parent_of_parent_rel, tag=alias.cnjc,
                                                         name=alias.ve, const_name=alias.ve)
            self.graph.idx2property[and_idx].dep_par_head =idx
            # idx2property[and_idx][7]=idx
            self.graph.idx2parent[idx] = {and_idx: alias.op1}

            for i, e in enumerate(seq):
                e_ = utils.is_compound_idx(e,self.graph)
                #      print("check ve",e,e_,list(idx2parent[e_].keys())[0],and_idx)
                if list(self.graph.idx2parent[and_idx].keys())[0] == e_:
                    self.graph.idx2parent[e] = {and_idx: alias.op + str(i + 2)}
                else:
                    self.graph.idx2parent[e_] = {and_idx: alias.op + str(i + 2)}
                # print(idx2parent)
        elif cjnt:
            parent_of_parent_of_parent_idx, parent_of_parent_of_parent_rel = utils.find_proper_parent(parent_of_parent_idx,self.graph)
            #    print("print(parent_of_parent_of_parent_idx)",parent_of_parent_of_parent_idx,"parent_of_parent_of_parent_rel",parent_of_parent_of_parent_rel)
            if parent_of_parent_idx == 0:
                self.graph.idx2parent[idx] = {parent_of_parent_idx: parent_of_parent_rel}
                self.graph.idx2parent[parent_idx] = {idx: alias.op1}
            else:
                utils.make_parent_to_sibling(self.graph, parent_idx, parent_of_parent_idx, idx, alias.op1, alias.op2)
                self.graph.idx2parent[idx] = {parent_of_parent_of_parent_idx: parent_of_parent_of_parent_rel}

        else:
            #    print("print(parent_of_parent_idx)",parent_of_parent_idx,"parent_of_parent_rel",parent_of_parent_rel)
            parent_of_parent_of_idx, parent_of_parent_of_rel = utils.find_proper_parent(parent_of_parent_idx,self.graph)

            utils.make_parent_to_sibling(parent_idx, parent_of_parent_idx, idx, alias.op1, alias.op2)
            self.graph.idx2parent[idx] = {parent_of_parent_idx: parent_of_parent_rel}

    def __add_beneficiary_or_purpose(self,idx):
        name = self.graph.idx2property[idx].concept_name

        if name == alias.icin:
            previous_token = self.graph.idx_sequence[self.graph.idx_sequence.index(idx) - 1]
            # print("idx",idx,idx2property[idx][5],"previous token",previous_token)

            if previous_token in self.graph.idx2property:
                # print("previous token",idx2property[previous_token][5])
                child_pos_tag = self.graph.idx2property[previous_token].pres_pos_tag
                parent_idx, parent_relation = utils.find_proper_parent(idx,self.graph)
                # print("parent_idx",parent_idx,idx2property[parent_idx][5])
                Actions.connect_up_node_and_remove(self.graph,idx)
                if child_pos_tag == alias.noun:
                    self.graph.idx2parent[previous_token] = {parent_idx: alias.beneficiary}
                else:
                    self.graph.idx2parent[previous_token] = {parent_idx: alias.purpose}
        else:
            parent_idx, parent_relation = utils.find_proper_parent(idx,self.graph)
            # print("goal case için yok parent ",parent_idx,idx)
            if self.graph.idx2property[idx].pos_tag == alias.pron:
                self.graph.idx2parent[idx] = {parent_idx: alias.beneficiary}
            else:
                self.graph.idx2parent[idx] = {parent_idx: alias.purpose}

    def __handle_time_temporals(self,idx):

        children = utils.find_children_connected_with_given_relation(idx, self.graph.idx2parent, relation=alias.arg) + \
                   utils.find_children_connected_with_given_relation(idx,self.graph.idx2parent,  relation=alias.appos)
        # print("handle_time_temporals",children)
        if len(children) > 0:
            for i in children:
                self.graph.idx2parent[i][idx] = alias.time

    def __add_relative_degree(self,idx, root_name):

        if root_name == alias.kadar:
            parent_idx, parent_rel = utils.find_proper_parent(idx,self.graph)  #### kadar iyi
            parent_of_parent_idx, parent_of_parent_rel = utils.find_proper_parent(parent_idx,self.graph)  #### kadar iyi ev
            children = utils.find_parent_connections(idx,self.graph)
            #        print("add relative degree kadar parent idx",parent_idx,idx2property[parent_idx][0],parent_idx,idx2property[parent_idx][4])
            #        print("\nadd relative degree kadar parent of parent and children",parent_of_parent_idx,children)


            if not self.graph.idx2property[parent_idx].isFrame: #### kadar fiile bağlı değil.

                if parent_of_parent_idx!=0:

                    obj_idx = parent_of_parent_idx
                    #            print("kadar fiile bağlı değil",obj_idx)
                    if self.graph.idx2property[parent_of_parent_idx].isFrame:

                        obj = utils.find_children_connected_with_given_relation(parent_of_parent_idx, self.graph.idx2parent, relation=alias.A0)
                        #               print("parent of parent fiil: obj:",obj)
                        if len(obj) > 0:
                            if obj[0] != parent_idx:
                                obj_idx = obj[0]
                            else:
                                self.graph.idx2parent[idx] = {parent_idx: alias.mod_rel}
                                return True
                        else:
                            self.graph.idx2parent[idx] = {parent_idx: alias.mod}
                            return True
                            #           print("obj idx", obj_idx)
                    have_degree_idx = self.graph.create_and_add_new_node(obj_idx, alias.A1_of, tag=alias.noun,
                                                                         name=align.key2amr[alias.have_degre][root_name],
                                                                         const_name=self.graph.idx2property[obj_idx].node_name, check=False,
                                                                         verb_frame=False)
                    self.graph.idx2property[have_degree_idx].dep_par_head = obj_idx

                    self.graph.idx2property[idx].concept_name = alias.ayni
                    utils.find_represent_char_of_names(idx,self.graph.idx2property)

                    self.graph.idx2property[idx].node_name= self.graph.idx2property[obj_idx].node_name

                    self.graph.idx2property[idx].dep_par_head = obj_idx
                    self.graph.idx2parent[idx] = {have_degree_idx: alias.A3}

                    self.graph.idx2parent[parent_idx] = {have_degree_idx: alias.A2}
                    self.graph.idx2parent[children[0]] = {have_degree_idx: alias.A4}

            else:
                #         print("kadar fiile bağlı")
                if parent_rel == alias.ext:
                    self.graph.idx2parent[idx] = {parent_idx: alias.degree}
                else:
                    obj = utils.find_children_connected_with_given_relation(parent_idx, self.graph.idx2parent, relation=alias.A1) + \
                          utils.find_children_connected_with_given_relation(parent_idx, self.graph.idx2parent, relation=alias.obj)
                    if len(obj) > 0:
                        obj_idx = obj[0]
                        self.graph.idx2parent[idx] = {obj_idx: alias.degree}
                    else:
                        self.graph.idx2parent[idx] = {parent_idx: alias.mod_rel}
                        return True

        else:

            tag = 5 if root_name == alias.en else 4
            parent_idx, parent_rel = utils.find_proper_parent(idx,self.graph)
            parent_of_parent, _ = utils.find_proper_parent(parent_idx,self.graph)

            if self.graph.idx2property[parent_idx].pos_tag == alias.adj:
                if self.graph.idx2property[parent_of_parent].isFrame:
                    self.graph.idx2parent[parent_idx] = {parent_of_parent: alias.mod_rel}
                    self.graph.idx2parent[idx] = {parent_idx: alias.degree}
                    return True

                noun_idx = utils.find_parent_with_given_post_tag(idx,self.graph,participant=tag)

                if noun_idx == parent_idx:
                    return False

                have_degree_idx = self.graph.create_and_add_new_node(noun_idx, alias.A1_of, tag=alias.noun,
                                                                     name=align.key2amr[alias.have_degre][root_name],
                                                                     const_name=align.key2amr[alias.have_degre][root_name],
                                                                     check=False, verb_frame=False)
                self.graph.idx2property[have_degree_idx].dep_par_head= idx

                #           print("superlative ",parent_of_parent,idx2property[parent_of_parent][2],idx2property[parent_of_parent][0])

                if self.graph.idx2property[parent_of_parent].pos_tag == alias.adj:
                    self.graph.idx2parent[parent_of_parent] = {have_degree_idx: alias.A5}

                self.graph.idx2parent[parent_idx] = {have_degree_idx: alias.A2}
                self.graph.node2conn[noun_idx].update({parent_idx: alias.A1})
                self.graph.idx2parent[idx] = {have_degree_idx: alias.A3}

                #            print("have-degree idx",have_degree_idx,"idx2parent",idx2parent,"\n")
            else:
                #            print("en den sonra sıfat gelmiyor")
                if self.graph.idx2property[parent_idx].pos_tag == alias.noun:
                    #               print("en den sonra isim geliyor",idx2property[parent_idx][2])
                    self.graph.idx2parent[idx] = {parent_idx: alias.degree}

        return True

    def __add_wh_questions(self,idx, root_name, parent_rel, parent_idx):
        if root_name in [alias.ne]:
            if parent_rel in [alias.cau]:
                return False
            elif self.graph.idx2property[idx].node_name == alias.neden:

                unknown = self.graph.create_and_add_new_node(parent_idx, align.key2amr[alias.wh_questions][root_name],
                                                             tag=alias.noun, name=alias.amr_unknown, const_name=alias.amr_unknown,
                                                             check=False, verb_frame=False)

                self.graph.idx2parent[unknown] = {parent_idx: align.key2amr[alias.wh_questions][alias.neden]}
                Actions.connect_up_node_and_remove(self.graph,idx)
                return True

        else:
            parent_idx, parent_rel = utils.find_proper_parent(idx,self.graph)
            unknown = self.graph.create_and_add_new_node(parent_idx, align.key2amr[alias.wh_questions][root_name],
                                                         tag=alias.noun, name=alias.amr_unknown, const_name=alias.amr_unknown,
                                                         check=False, verb_frame=False)

            if preprocess.to_lower(self.graph.idx2property[idx].node_name) == alias.nereden:
                self.graph.idx2parent[unknown] = {parent_idx: align.key2amr[alias.wh_questions][alias.nasil]}
            Actions.connect_up_node_and_remove(self.graph,idx)
            return True

    def __add_questions(self,idx, root_name):

        previous_token = self.graph.idx_sequence[self.graph.idx_sequence.index(idx) - 1]

        if previous_token in self.graph.idx2property:
            parent_idx, parent_rel = utils.find_proper_parent(idx,self.graph)
            self.graph.idx2parent[idx] = {previous_token: ""}
            Actions.connect_up_node_and_remove(self.graph,idx)

            self.graph.idx2parent[previous_token] = {parent_idx: parent_rel}
            unknown = self.graph.create_and_add_new_node(previous_token, alias.polarity, tag=alias.noun,
                                                         name=alias.amr_unknown, const_name=alias.amr_unknown, check=False,
                                                         verb_frame=False)
            self.graph.idx2property[unknown].dep_par_head = previous_token
            if (self.graph.idx2property[previous_token].pos_tag == alias.noun) or\
                    (self.graph.idx2property[previous_token].pos_tag == alias.adj):
                self.graph.add_domain(previous_token, root_name)

    def __add_quantity(self,idx, connect=False):
        #  print(quantities[idx2property[idx][5]])
        parent_of_idx, parent_relation = utils.find_proper_parent(idx,self.graph)

        if parent_relation != alias.unit:

            quantity_idx=self.graph.create_and_add_new_node(parent_of_idx, parent_relation, tag=alias.verb,
                                                            name=align.quantities[self.graph.idx2property[idx].concept_name],
                                                            const_name=self.graph.idx2property[idx].node_name,
                                                            verb_frame=False)
            if connect:
                self.graph.idx2parent[idx] = {quantity_idx: alias.unit}
            return quantity_idx

    def __add_approximation(self,idx):

        parent_of_idx, parent_relation = utils.find_proper_parent(idx,self.graph)

        if parent_relation != alias.quant:
            more_than = self.graph.create_and_add_new_node(idx, alias.quant, tag=alias.noun,
                                                           name=align.aproximation[self.graph.idx2property[idx].concept_name],
                                                           const_name=self.graph.idx2property[idx].concept_name)
            op = self.graph.create_and_add_new_node(more_than, alias.op1, tag=alias.noun, name="1", const_name=self.graph.idx2property[idx].node_name)

    def __handle_special_cases(self,idx, root_name):
        if root_name == alias.person:
            #  print("kişi is found")
            parent_connections = utils.find_parent_connections(idx,self.graph)
            reentrancy = utils.find_reentrancy_connections(idx,self.graph)
            reified = [child for child in parent_connections if self.graph.idx2property[child].dep_par_relation in [
                alias.mod]]
            reified += [child for child in reentrancy if self.graph.node2conn[child][idx] == alias.mod]
            reified = [child for child in reified if self.graph.idx2property[child].pres_pos_tag == alias.verb]
            #    print("kişi with mode relations and verbs",reified)
            rel_comming_with_reentrancy = None
            for child in reified:
                if child in self.graph.node2conn[idx]:
                    rel_comming_with_reentrancy = self.graph.node2conn[idx][child]

                if rel_comming_with_reentrancy is not None:
                    new_rel = rel_comming_with_reentrancy + "-of"
                    self.graph.idx2parent[child][idx] = new_rel
                    del self.graph.node2conn[idx][child]
                else:
                    rel = self.graph.idx2parent[child][idx]
                    new_rel = alias.A0_of if self.graph.idx2property[child].dep_par_relation == alias.mod else alias.cause_of
                    self.graph.idx2parent[child] = {idx: new_rel}

        elif root_name == alias.thing:
            parent_connections = utils.find_parent_connections(idx,self.graph)
            reentrancy = utils.find_reentrancy_connections(idx,self.graph)

            reified = [child for child in parent_connections if self.graph.idx2property[child].dep_par_relation in [
                alias.mod]]
            reified += [child for child in reentrancy if self.graph.node2conn[child][idx] == alias.mod]
            reified = [child for child in reified if self.graph.idx2property[child].pres_pos_tag == alias.verb]

            rel_comming_with_reentrancy = None
            #        print("refied",reified,node2conn,idx)

            for child in reified:
                if child in self.graph.node2conn[idx]:
                    rel_comming_with_reentrancy = self.graph.node2conn[idx][child]
                    #                print("rel_comming_with_reentrancy",rel_comming_with_reentrancy)

                if rel_comming_with_reentrancy is not None:
                    new_rel = rel_comming_with_reentrancy + "-of"
                    self.graph.idx2parent[child][idx] = new_rel
                    del self.graph.node2conn[idx][child]
                else:
                    tmp = utils.is_proper_child(child,self.graph)
                    reentrancy_cases = utils.find_reentrancy_connections(tmp,self.graph)
                    rel = alias.A1
                    #                print("reentrancy_cases",reentrancy_cases,tmp,idx,child)
                    if idx in reentrancy_cases:
                        rel = self.graph.node2conn[idx][tmp]
                    new_rel = rel + "-of"
                    self.graph.idx2parent[child] = {idx: new_rel}
                    if tmp in self.graph.node2conn[idx]:
                        del self.graph.node2conn[idx][tmp]


        elif root_name == alias.gibi:
            parent_idx = list(self.graph.idx2parent[idx].keys())[0]
            parent_rel = list(self.graph.idx2parent[idx].values())[0]

            child_list = utils.find_parent_connections(idx,self.graph)
            child = child_list[0] if len(child_list) > 0 else None

            #            print("1 gibi gibi",parent_idx,parent_rel,root_name,child)

            if idx in self.graph.idx2property.keys():

                if self.graph.idx2property[child].lemma_pos_tag== alias.nadj and self.graph.idx2property[parent_idx].pos_tag == alias.noun:
                    parent_of_parent_idx = list(self.graph.idx2parent[parent_idx].keys())[0]
                    self.graph.idx2parent[parent_idx][parent_of_parent_idx] = alias.example


                elif self.graph.idx2property[parent_idx].pos_tag == alias.noun or self.graph.idx2property[parent_idx].pos_tag == alias.verb:
                    #                   print("2 gibi gibi",idx2property[parent_idx][2],idx2property[child][1])
                    if self.graph.idx2property[child].lemma_pos_tag == alias.aor or "Aor" in self.graph.idx2property[child].inflections:
                        #                        print("3 gibi gibi",idx2property[parent_idx][2])
                        Actions.connect_up_node_and_remove(self.graph,idx)
                        self.graph.idx2parent[child][parent_idx] = alias.conj_as_if
                    elif self.graph.idx2property[child].lemma_pos_tag == alias.verb:
                        #                        print("7 gibi gibi",idx2property[parent_idx][2])
                        Actions.connect_up_node_and_remove(self.graph,idx)
                        self.graph.idx2parent[child][parent_idx] = alias.conj_as_if
                    elif not self.__add_benze_frame(idx, root_name):
                        if parent_rel in align.amrtag2rel:
                            self.graph.idx2parent[idx][parent_idx] = align.amrtag2rel[parent_rel]

                elif self.graph.idx2property[child].pos_tag == alias.noun:
                    #                   print("gibi gibi 5")
                    # IGs = idx2property[child][1].split("|")[1]
                    self.__add_benze_frame(idx, root_name)

                else:
                    #                   print("else")
                    if parent_rel in align.amrtag2rel:
                        self.graph.idx2parent[idx][parent_idx] = align.amrtag2rel[parent_rel]

    def __add_benze_frame(self,idx, root_name):
        parent_idx = list(self.graph.idx2parent[idx].keys())[0]
        parent_rel = list(self.graph.idx2parent[idx].values())[0]

        def add_gibi(idx, parent_idx):
            children =  utils.find_parent_connections(idx,self.graph)
            children = list(set(children))
            if  [self.graph.idx_sequence[self.graph.idx_sequence.index(idx) - 1]] not in children:
                children += [self.graph.idx_sequence[self.graph.idx_sequence.index(idx) - 1]]

            for child in children:
                #      print(child,idx2property[child])
                tmp = utils.is_proper_child(child,self.graph)
                #      print("1 proper child gibi",child,idx2property[tmp])
                parent_of_new_node = parent_idx
                if self.graph.idx2property[tmp].pos_tag == alias.noun or self.graph.idx2property[tmp].concept_name ==alias.ve:
                    #         print("2 gibi")
                    if (self.graph.idx2property[parent_idx].pos_tag == alias.verb) or (self.graph.idx2property[parent_idx].lemma_pos_tag == alias.ques):
                        #             print("3 gibi")
                        rel_of_parent = utils.find_children_connected_with_given_relation(parent_idx, self.graph.idx2parent,
                                                                                          relation=alias.A0) + utils.find_children_connected_with_given_relation(
                            parent_idx,self.graph.idx2parent, relation=alias.subj) + \
                                        utils.find_children_connected_with_given_relation(parent_idx, self.graph.idx2parent,
                                                                                          relation=alias.AA)
                        if len(rel_of_parent) > 0:
                            rel_of_parent_idx = rel_of_parent[0]
                            parent_of_new_node = rel_of_parent_idx
                            #        print("4 gibi")
                    new_node_id=self.graph.create_and_add_new_node(parent_of_new_node, alias.A0_of, tag=alias.verb,
                                                                   name=alias.benze, const_name=alias.benze, verb_frame=True)
                    Actions.connect_up_node_and_remove(self.graph,idx)
                    self.graph.idx2parent[child] = {new_node_id: alias.A1}
                    return True

            return False

        def add_oyle(idx, parent_idx,parent_rel, pron=alias.concept_bu):
            #  print("add böyle",idx)
            if  self.graph.idx2property[parent_idx].pos_tag ==alias.noun:
                parent_of_new_node = utils.find_parent_with_given_post_tag(idx,self.graph)
                #   print("parent of new node",parent_of_new_node)
                parent_rel = list(self.graph.idx2parent[parent_of_new_node].values())[0]

                if parent_of_new_node == 0:
                    new_idx =self.graph.create_and_add_new_node(parent_idx, parent_rel, tag="-",
                                                                name=alias.ol14, const_name=alias.ol14, verb_frame=True)

                    doers = utils.find_children_connected_with_given_relation(idx, self.graph.idx2parent,
                                                                              relation=alias.A0) + utils.find_children_connected_with_given_relation(
                        idx,self.graph.idx2parent, relation=alias.subj)

                    parent_of_new_node = doers[0]
                    self.graph.idx2parent[parent_of_new_node] = {new_idx: alias.A0}

                elif self.graph.idx2property[parent_of_new_node].pos_tag == alias.verb:
                    rel_of_parent = utils.find_children_connected_with_given_relation(parent_of_new_node, self.graph.idx2parent,
                                                                                      relation=alias.A0) + utils.find_children_connected_with_given_relation(
                        parent_of_new_node,self.graph.idx2parent, relation=alias.subj) + \
                                    utils.find_children_connected_with_given_relation(
                        parent_of_new_node, self.graph.idx2parent,relation=alias.AA)

                    if len(rel_of_parent)==0:
                        rel_of_parent = utils.find_children_connected_with_given_relation(parent_of_new_node,
                                                                                          self.graph.node2conn,
                                                                                          relation=alias.A0) +  \
                                        utils.find_children_connected_with_given_relation(
                                            parent_of_new_node, self.graph.node2conn, relation=alias.AA)
                    parent_of_new_node = rel_of_parent[0]



                new_node_id = self.graph.create_and_add_new_node(parent_of_new_node, alias.A0_of, tag=alias.verb,
                                                                 name=alias.benze[:-3], const_name=alias.benze,
                                                                 verb_frame=True)

                new_node=self.graph.create_and_add_new_node(new_node_id, alias.A1, tag=alias.adj,
                                                            name=alias.concept_bu, const_name=alias.concept_bu,
                                                            verb_frame=False)

                self.graph.idx2parent[idx] = {new_node_id: ""}
                Actions.connect_up_node_and_remove(self.graph, idx)
                return True

            elif self.graph.idx2property[parent_idx].pos_tag == alias.verb:
                new_node_id = self.graph.create_and_add_new_node(parent_idx, parent_rel, tag=alias.verb,
                                                                 name=alias.benze[:-3], const_name=alias.benze,
                                                                 verb_frame=True)

                _ = self.graph.create_and_add_new_node(new_node_id, alias.A1, tag=alias.adj,
                                                              name=alias.concept_bu, const_name=alias.concept_bu,
                                                              verb_frame=False)

                self.graph.idx2parent[idx] = {new_node_id: ""}
                Actions.connect_up_node_and_remove(self.graph, idx)
                return True

            else:
                self.graph.idx2parent[idx] = {parent_idx: alias.manner}
                return True





        if root_name == alias.gibi:
            return add_gibi(idx, parent_idx)
        #elif (self.graph.idx2property[parent_idx].pos_tag ==alias.noun) :
        if root_name == alias.boyle:
            return add_oyle(idx, parent_idx,parent_rel)
        elif root_name == alias.soyle:
            return add_oyle(idx, parent_idx,parent_rel, pron=alias.concept_su)

    def __handle_modality_words(self,idx, parent_idx):
        self.graph.add_modality(parent_idx)
        Actions.connect_up_node_and_remove(self.graph,idx)
        return True

    def __change_olarak(self,idx):
        self.graph.idx2property[idx].concept_name = alias.ol01
        utils.find_represent_char_of_names(idx,self.graph.idx2property)
        self.graph.idx2property[idx].pos_tag = alias.verb
        self.graph.idx2property[idx].lemma_pos_tag = alias.verb
        children = utils.find_parent_connections(idx,self.graph)
        self.graph.idx2parent[children[0]] = {idx: alias.A1}



    def clear(self):
        del self.graph
        self.graph = None





















