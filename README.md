# CRISPResso2_tests

A repository for testing that is too large (or too private) to be kept in their respective repositories.

## `CRISPResso2` Thorough Integeration Tests

To run the integration tests for `CRISPResso2` make sure that the `CRISPRESSO2_DIR` variable in the `Makefile` is set to the correct directory where the `CRISPResso2` repository is (by default it is set to `../CRISPResso2`).
Then to run only the integration tests you can issue `make test_cli_integration` and it will run the tests and compare the output.

Furthermore, the running times of each integration test will be checked and if there is a difference > 10% in the two times, it will be reported.


### `Selenium Testing`

In order to test the web UI using Selenium there are several pre-requisites:

+ You must have Docker installed
+ Use Docker to build the C2Web Docker image with the name `crispresso2web`
  + e.g. `docker build -t crispresso2web .`
+ You must also have Google Chrome installed, the most recently version is best.
+ In the environment you are using the following libraries must be installed (followed by conda examples).
  + Selenium `conda install -c conda-forge selenium`
  + webdriver_manager `conda install webdriver-manager`

The test can be run using `make web_ui`

**Warning:** The tests will fail if the pages fail to load within a buffer period.