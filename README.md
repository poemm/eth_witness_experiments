The goal of this work-in-progress repository is to share experiments related to [the stateless ethereum witness spec](https://github.com/ethereum/stateless-ethereum-specs/blob/master/witness.md).

Files:
* `parse_generate_spec.py` implements the spec closely -- each spec rule corresponds to a function. This may be naively slow.
* `parse_alternative_implementations.py` gives alternative implementations of the spec, with aggressive optimizations, possibly introducing bugs.
* `test.py` includes many hand-written tests for the above files.

To run tests on a specific implementation:
```
# Choose which implementation to test by editting tops of files test.py and parse_alternative_implementations.py
#  (see instructions starting with "PLEASE COMMENT").
python3 test.py
```
