This directory includes some tests for some edge cases.

* `account_node.json`	- tests related to account nodes
* `branch_node.json`	- tests related to branch nodes
* `extension_node.json`	- tests related to extension nodes
* `hash_node.json`	- tests related to hash nodes
* `multiple_trees.json`	- tests related to having multiple chunks as separate trees


These tests are generated ("filled") from corresponding files in `fillers/` with the following commands.
```
python3 test_tools.py yaml2test fillers/extension_node.yaml > extension_node.json
python3 test_tools.py yaml2test fillers/hash_node.yaml > hash_node.json
python3 test_tools.py yaml2test fillers/account_node.yaml > account_node.json
python3 test_tools.py yaml2test fillers/branch_node.yaml > branch_node.json
python3 test_tools.py yaml2test fillers/storage_tree.yaml > storage_tree.json
python3 test_tools.py yaml2test fillers/multiple_trees.yaml > multiple_trees.json
```

Visualize json tests as s-expressions.
```
python3 test_tools.py test2sexpr branch_node.json
python3 test_tools.py test2sexpr account_node.json
python3 test_tools.py test2sexpr hash_node.json
python3 test_tools.py test2sexpr storage_tree.json
python3 test_tools.py test2sexpr multiple_trees.json
python3 test_tools.py test2sexpr extension_node.json
```

