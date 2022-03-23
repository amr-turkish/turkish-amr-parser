# turkish-amr-guidelines

This repository provides the resources introduced within the article:

[Abstract Meaning Representation of Turkish](https://www.cambridge.org/core/journals/natural-language-engineering) accepted for publication in [Natural Language Engineering](https://www.cambridge.org/core/journals/natural-language-engineering), Cambridge Press.


Abstract meaning representation (AMR) is a graph-based sentence-level meaning representation that has become highly popular in recent years. AMR is a knowledge-based meaning representation heavily relying on frame semantics for linking predicate frames and entity knowledge bases such as DBpedia for linking named entity concepts. Although it is originally designed for English, its adaptation to non-English languages is possible by defining language-specific divergences and representations. This article introduces the first AMR representation framework for Turkish, which poses diverse challenges for AMR due to its typological differences compared to English; agglutinative, free constituent order, morphologically highly rich resulting in fewer word surface forms in sentences. The introduced solutions to these peculiarities are expected to guide the studies for other similar languages and speed up the construction of a cross-lingual universal AMR framework. Besides this main contribution, the article also presents the construction of the first AMR corpus of 700 sentences, the first AMR parser (i.e., a tree-to-graph rule-based AMR parser)
used for semi-automatic annotation, and the evaluation of the introduced resources for Turkish. 


Other resources introduced within the same article may be found at the following GitHub repositories:

the first Turkish AMR Guidelines: [turkish-amr-guidelines](https://github.com/amr-turkish/turkish-amr-parser)


the first Turkish AMR Corpus: [turkish-amr-corpus](https://github.com/amr-turkish/turkish-amr-corpus)

## Quick Tour
### Input Format
Turkish AMR parser uses syntactic and semantic features, therefore they should be provided to the parser in CONLL format. 

A sample should have the following columns :

* Token id
* Surface form
* Lemma
* Pos
* PPos
* Morphologic Tags
* Dependency Head
* Dependency Relation
* SRL features
 

An example data sample:
Ama annemin şartları vardı. (*But my mother has her conditions*) 

| ID | Surface| Lemma\*| Pos | PPos | Morp\*  | DepHead ID | DepRel\* | Semantic Layers |
|--- |--------|------|---|----|--------|-----|---|---------|
| 1  | ama | ama  | Conj | Conj | _ | 4 | CONJUNCTION |  _ _ _ |
| 2  | annemin | anne   | Noun | Noun | A3sg\|P1sg\|Gen | 3 | POSSESSOR | _ _ _ |
| 3  | şartları | şart | Noun | Noun | A3pl\|P3sg\|Nom | 4 | SUBJECT | _ _ A1 |
| 4  | vardı | var | Verb | Verb | Pos\|Past\|A3sg | 0 | PREDICATE | Y var.01 _ |
| 5  | . | . | Punc | Punc | _ | 4 | PUNCTUATION | _ _ _ |


\* indicates duplicate columns. The further information about input form is available in [Abstract Meaning Representation of Turkish](https://www.cambridge.org/core/journals/natural-language-engineering)


### Running the Parser
For Prepocessing
`python preprocess.py -f <datafilepath> --out <outputdirectory>`

## Contributing

All contributions welcome!

## How to cite this work

Oral, E., Acar, A., & Eryiğit, G. (2022). Abstract Meaning Representation of Turkish. Natural Language Engineering, 1-33. doi:coming

## Licence Information

Shield: [![CC BY-NC-SA 4.0][cc-by-nc-sa-shield]][cc-by-nc-sa]

This work is licensed under a
[Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License][cc-by-nc-sa].

[![CC BY-NC-SA 4.0][cc-by-nc-sa-image]][cc-by-nc-sa]

[cc-by-nc-sa]: http://creativecommons.org/licenses/by-nc-sa/4.0/
[cc-by-nc-sa-image]: https://licensebuttons.net/l/by-nc-sa/4.0/88x31.png
[cc-by-nc-sa-shield]: https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg
