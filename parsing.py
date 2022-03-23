import numpy as np
import pandas as pd

from parser import parse
from util import preprocess
import argparse


def __prepare_sentence_format(treebank):

    treebank["Sentence"] = np.nan
    sentence_start_index = list(treebank[treebank[0] == 1].index)
    treebank = preprocess.tag_sentences(treebank, sentence_start_index)
    treebank["rel_str"] = treebank[12]
    treebank["rel_str"].fillna("nope", inplace=True)
    sentences = preprocess.get_sentence_dfs(treebank, sentence_start_index)
    return sentences

def main(treebank,path):
    print("Start input formating...")
    sentences=__prepare_sentence_format(treebank)

#    total_lenght = sum([len(s) for s in sentences])

    if path is None:
        path ="./"


    print("Start parsing...")
    parse.parse_sentence_list(sentences, path=path)
    print("Parsing is done")


    print("Parsing outputs are written in ",path+"output.out")
    print("Parser could not parse sentence written in ", path + "exception.out")

def parse_one_sent(treebank):
    print("Start input formating...")
    sentences = __prepare_sentence_format(treebank)
    print(sentences[0],len(sentences[0]))
    parse.parse_sentence(sentences[0])




if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', "--filepath", type=str, help="Input file. It has to be in CONLL format")
    parser.add_argument("--out", type=str, help="Output path")
    parser.add_argument('--numberOfColumns', type=int, default=13, dest='n',
                        help='Number of colums the Propbank has except semantic layer')

    parser.add_argument('-only-one', type=bool, default=False, dest='one_sentence',
                        help='Number of colums the Propbank has except semantic layer')

    args = parser.parse_args()

    treebank = pd.read_csv(args.filepath, names=[i for i in range(args.n)]).reset_index().drop(["index"],axis=1)

    if args.one_sentence:
        parse_one_sent(treebank)
    else:
        main(treebank, args.out)




