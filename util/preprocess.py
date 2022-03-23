import pandas as pd


def to_lower(text):
    text=text.replace("İ","i")
    text=text.replace("I","ı")
    return text.lower()


def get_sentence_dfs(treebank,sentence_start_index):
    sentence_df_list=[]
    for start in range(len(sentence_start_index)):
        if start==len(sentence_start_index)-1:
            sentence_df_list.append(treebank[sentence_start_index[start]:])
        else:
            sentence_df_list.append(treebank[sentence_start_index[start]:sentence_start_index[start+1]])
    return sentence_df_list

def tag_sentences(treebank,sentence_start_index):
    for i,start in enumerate(range(len(sentence_start_index))):
        if start==len(sentence_start_index)-1:
            for imm in range(int(sentence_start_index[start]),len(treebank)-1):
                treebank.at[imm,"Sentence"]=i
        else:
            for imm in range(int(sentence_start_index[start]),int(sentence_start_index[start+1])):
                treebank.at[imm,"Sentence"]=i
    return treebank

def get_particular_sentence(treebank,sentence_number):
    return treebank[treebank["Sentence"]==sentence_number]


def get_unique_values_of_colums_in_contion(treebank,column,condition_column,condition):
    return treebank[treebank[condition_column] == condition][column].unique()


