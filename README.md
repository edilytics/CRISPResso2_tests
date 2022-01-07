# CRISPResso2_tests

A repository for testing that is too large (or too private) to be kept in their respective repositories.

## `CRISPResso2` Thorough Integeration Tests

To run the integration tests for `CRISPResso2` make sure that the `CRISPRESSO2_DIR` variable in the `Makefile` is set to the correct directory where the `CRISPResso2` repository is (by default it is set to `../CRISPResso2`).
Then to run only the integration tests you can issue `make test_cli_integration` and it will run the tests and compare the output.

Furthermore, the running times of each integration test will be checked and if there is a difference > 10% in the two times, it will be reported.
