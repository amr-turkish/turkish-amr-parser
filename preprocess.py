import pandas as pd
import numpy as np
import argparse
import logging



def remove(tag_list):
    if tag_list is not None:
        while '' in tag_list:
            tag_list.remove('')
    return tag_list

def get_propbank_label(row, n):
    line = row.split("\t")

    tree_fields = line[:n]
    prop_tags = line[n:]

    tags = [t for t in prop_tags if t not in ["_"]]

    tree_fields.append(tags if len(tags) > 0 else None)
    return tree_fields

def convert_propbank(propbank,args):

    propbank["probank_tags"] = np.nan
    propbank["probank_tags"] = propbank[0].apply(lambda x: get_propbank_label(x,n=args.n))
    treebank = pd.DataFrame(propbank['probank_tags'].values.tolist(), columns=[i for i in range(args.n+1)])

    treebank[args.n] = treebank[args.n].apply(lambda x: remove(x))
    return treebank


def read_file(filepath):
    assert filepath.endswith('.conll'),'input file has to be in CONLL format'
    propbank = pd.read_csv(filepath, sep="\n", header=None)

    return propbank


if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-f',"--filepath", type=str, help="Input file. It has to be in CONLL format")
    parser.add_argument("--out", type=str, help="Output path")
    parser.add_argument('--numberOfColumns',type=int,default=12, dest='n',help='Number of colums the Propbank has except semantic layer')

    args = parser.parse_args()

    logging.info('File processing started.')
    propbank=read_file(args.filepath)

    treebank=convert_propbank(propbank,args)

    from os import path,mkdir

    if not path.exists(args.out):
        mkdir(args.out)

    outfile=path.join(args.out,'propbank.out')

    treebank.to_csv(outfile, index=False)
    logging.info('File processing ended.')






