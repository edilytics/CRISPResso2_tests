# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

CRISPResso2_tests is the integration test suite for CRISPResso2, a bioinformatics tool for analyzing genome editing outcomes from deep sequencing data. This repository contains test datasets, CLI integration tests, and web UI tests that are too large or private to keep in the main CRISPResso2 repository.

## Key Commands

### Running Tests

```bash
# Install CRISPResso2 from the sibling directory (required before running tests)
make install

# Run all tests
make all

# Run all tests and compare output to expected results
make all test

# Run tests, skip HTML file comparisons
make all test skip_html

# Run a single test
make basic
make params
make batch

# Run a single test with output comparison
make basic test

# Force print output (useful for debugging)
make basic print

# Update expected results interactively
make params update

# Auto-update expected results (review in git afterward)
make params update-all
```

### Web UI Testing (requires Docker + Chrome)

```bash
make web_ui
```

### Adding a New Test

```bash
python test_manager.py add <actual CRISPResso results directory>
```

### Updating Expected Results Manually

```bash
python test_manager.py update <actual_dir> <expected_dir>
```

## Architecture

```
cli_integration_tests/
├── inputs/                 # Test input files (fastq, bam, batch files)
├── expected_results/       # Baseline expected outputs for regression testing
└── CRISPResso_on_*/       # Actual test output directories (generated)

web_tests/
├── CRISPResso_Web_UI_Tests/  # Selenium page objects and locators
├── web_ui_test.py            # Main UI test script
└── web_stress_test.py        # Load testing

diff.py                     # File comparison with normalization
test_manager.py            # CLI for adding/updating tests
Makefile                   # Test orchestration
```

## Test Infrastructure Details

- **File comparison** (`diff.py`) normalizes floats to 3 decimals, timestamps, file paths, and bowtie versions for stable comparisons
- **Ignored files**: `*_RUNNING_LOG.txt`, `fastp_report.html`
- **Performance tracking**: Tests report if runtime changes by >10% from baseline
- **For better diffs**: `pip install ydiff` provides colorized side-by-side output

## Configuration

The `CRISPRESSO2_DIR` variable in `Makefile` points to the CRISPResso2 repository (default: `../CRISPResso2`). Ensure this path is correct before running tests.

## CRISPResso2 Tool Suite

Tests cover these CRISPResso tools:
- **CRISPResso**: Core single-amplicon analysis
- **CRISPRessoBatch**: Multi-condition batch analysis
- **CRISPRessoPooled**: Pooled amplicon analysis
- **CRISPRessoWGS**: Whole-genome sequencing analysis
- **CRISPRessoCompare**: Comparative analysis between samples
- **CRISPRessoAggregate**: Result aggregation
