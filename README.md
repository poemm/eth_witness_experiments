The goal of this work-in-progress repository is to share experiments related to [the stateless ethereum witness spec](https://github.com/ethereum/stateless-ethereum-specs/blob/master/witness.md).

Files:
* `parse_generate_spec.py` implements the witness spec closely -- each spec rule corresponds to a function. This may be naively slow.
* `parse_alternative_implementations.py` gives alternative implementations of the spec, with optimizations, possibly introducing bugs.
* `tests/` includes tests for the above files.
