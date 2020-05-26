# Introduction

`filled/` contains all tests. It may contain tests generated from `fillers/`, and also hand-written tests when convenient. The olly test format specification, instead but it is meant to be intuitive.

`fillers/` contains files used to generate ("fill") tests. These files are more general than a text format for witnesses, since they can define error cases. The format of these files is nested lists and key-value pairs. To make tests as pleasant as possible to write -- the test filler format is a concise yaml format (with some json where convenient), since pure json would be less concise. The syntax and semantics of this text format is only specified in the tools used to process them. One can create other filler format if it is convenient.

`testtool.py` is for processing test files and executing tests. See example uses below.


# How to use

Make sure you are in this `tests/` directory of this repo.

Generate ("fill") a test from `fillers/` as follows.
```
python3 testtool.py fill fillers/hash_node.yaml
```

Fill all tests and put the results in `filled/`.
```
#!/bin/bash
for filename in fillers/*.yaml; do
  python3 testtool.py fill $filename > filled/$(basename ${filename} .yaml).json
done
```

Execute a test.
```
python3 testtool.py test filled/hash_node.json
```

Execute all tests.
```
#!/bin/bash
for filename in filled/*.json; do
  python3 testtool.py test $filename
done
```

Optionally, it may be useful to visualize a json test as an s-expression.
```
python3 testtool.py test2sexpr filled/branch_node.json
```

