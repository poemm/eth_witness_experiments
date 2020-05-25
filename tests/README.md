# Introduction

`filled/` contains all tests. It may contain tests generated from `fillers/`, and also hand-written tests when convenient.

`fillers/` contains files used to generate ("fill") tests. These files are more general than a text format for witnesses, since they can define error cases. The format of these files is nested lists and key-value pairs. To make tests as pleasant as possible to write -- the test filler format is a concise yaml format (with some json where convenient), since pure json would be less concise. The syntax and semantics of this text format is only specified in the tools used to process them. One can create other filler format if it is convenient.

`testtool.py` has tools for processing test files and executing tests. See example uses below.

# How to use.

Generate ("fill") a test from `fillers/` as follows.
```
python3 testtool.py fillers/hash_node.yaml
```

Fill all tests and put the results in `filled/`.
```
#!/bin/bash
for filename in fillers/*.yaml; do
  python3 testtool.py filler2test $filename > filled/$(basename ${filename} .yaml).json
done
```

It may be useful to visualize a json test as an s-expression.
```
python3 test_tools.py test2sexpr branch_node.json
```
