# CRISPResso2_tests

A repository for testing that is too large (or too private) to be kept in their respective repositories.

## `CRISPResso2` Thorough Integration Tests

To run the integration tests for `CRISPResso2` make sure that the `CRISPRESSO2_DIR` variable in the `Makefile` is set to the correct directory where the `CRISPResso2` repository is (by default it is set to `../CRISPResso2`).
Then to run only the integration tests you can issue `make all test` and it will run the tests and compare the output.

Furthermore, the running times of each integration test will be checked and if there is a difference > 10% in the two times, it will be reported.

For improved diff output, run `pip install ydiff` and the diffs will be colorized and side by side.

### How can I run a test?

As explained above, to run all of the tests and check all of the files for differences run:

``` shell
make all
```

To run all the tests and check all files for differences use the `test` option:

```shell
make all test
```

You can also select a single command to run, like this:

``` shell
make basic
```

**Note:** this will only run the CRISPResso command, it will not check the output files for differences.

If you want to run a single command *and* check it for differences, use the `test` option, like this:

``` shell
make basic test
```

By default, tests will only print command output in the case of an error. To force print output for any test use the `print` option, like this:

``` shell
make basic print
```

### How can I update the expected results for a test?

If you run a test and there are differences, you can run the command:

```shell
python test_manager.py update <actual CRISPResso results directory> <expected CRISPResso results directory>

```

This will show you what is different in the files, and then you can select whether you want them copied over or not.

### How can I add a test?

If you want to add a test, you can run the command:

``` shell
python test_manager.py add <actual CRISPResso results directory>
```

This will get the command that you used to run and add it to the Makefile, it will also copy over the files into the `cli_integration_tests/expected_results` directory and (try) to copy over the input files into the appropriate places.
As with all semi-automated tools, you should most definitely check the work of the program before committing it.

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
