from parser.parser import AmrParser
from util import parser_print as ppx

from os import path, mkdir


def parse_sentence_list(sentences, path_="./"):

    if not path.exists(path_):
        mkdir(path_)

    outfile = path.join(path_, 'output.out')
    exceptionfile = path.join(path_, 'exception.out')

    file_exception = open(exceptionfile, "w", encoding="utf-8")
    out = open(outfile, "w", encoding="utf-8")

    for i,sentence in enumerate(sentences):
        parser = AmrParser()
        try:
            graph = parser.parse(sentence.values)
            parser.clear()
            if i % 10 == 0:
                print("sentence", i, "from_id", i + 1)
            parsed = ppx.to_penman(graph,graph.root)
            sent_str = ppx.to_sentence(sentence)
            out.write("### " + str(i) + " " + sent_str + "\n" + "### by Parser" + "\n"+ parsed + "\n\n")
            parser.clear()

        except Exception as e:
            sent_str = ppx.to_sentence(sentence)
            file_exception.write(str(i) + " " + sent_str + "\n" + " exception " + str(e) + "\n")
            parser.clear()
            continue
    file_exception.close()
    out.close()

def parse_sentence(sentence):
    print(ppx.to_sentence(sentence))
    parser = AmrParser()
    graph = parser.parse(sentence.values)
    print(ppx.to_penman(graph, graph.root, level=0))
    parser.clear()
