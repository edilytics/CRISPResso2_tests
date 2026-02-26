# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

CRISPResso2_tests is the integration test suite for CRISPResso2, a bioinformatics tool for analyzing genome editing outcomes from deep sequencing data. This repository contains test datasets, CLI integration tests, and web UI tests that are too large or private to keep in the main CRISPResso2 repository.

## Prerequisites

Tests run inside the **pixi test environment** defined in the sibling `CRISPResso2` repository (`../CRISPResso2/pixi.toml`). You need:

1. **[pixi](https://pixi.sh)** installed and on your `PATH`
2. The **CRISPResso2** repo checked out at `../CRISPResso2` (or set `CRISPRESSO2_DIR`)

The Makefile automatically activates the pixi environment — no manual `conda activate` or `pixi shell` needed. CRISPResso2 is installed (and re-installed when source changes) via the `.install_sentinel` mechanism.

You can also run from the CRISPResso2 repo:
```bash
# Run all integration tests
pixi run -e test integration

# Run specific tests
ARGS="basic test" pixi run -e test integration
```

## Key Commands

### Running Tests

```bash
# Run all tests
make all

# Run all tests and compare output to expected results
make all test

# Run tests, skip HTML file comparisons
make all test skip_html

# Run tests with plot comparison (PDF text diff + PNG approximate RMSE)
make all test diff-plots

# Combine flags
make all test skip_html diff-plots

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
- **Plot comparison** (`--diff-plots` / `make ... diff-plots`) compares plots in two ways: (1) extracts drawing streams from PDFs and diffs them as text, showing exact changes to labels, data values, and drawing coordinates; (2) compares PNGs using downscaled grayscale RMSE, tolerant of anti-aliasing/font rendering differences across matplotlib versions.
- **Ignored files**: `*_RUNNING_LOG.txt`, `fastp_report.html`
- **Performance tracking**: Tests report if runtime changes by >10% from baseline
- **Better diffs**: `ydiff` is included in the pixi test environment for colorized side-by-side output

## Configuration

- **`CRISPRESSO2_DIR`** — path to the CRISPResso2 repo (default: `../CRISPResso2`). The Makefile reads `pixi.toml` from this location.
- **Pixi auto-activation** — the Makefile checks `PIXI_ENVIRONMENT_NAME`. If not already inside pixi's `test` environment, every command is prefixed with `pixi run --manifest-path .../pixi.toml -e test --`. If already inside (e.g., via `pixi shell -e test`), commands run directly with zero overhead.

## CRISPResso2 Tool Suite

Tests cover these CRISPResso tools:
- **CRISPResso**: Core single-amplicon analysis
- **CRISPRessoBatch**: Multi-condition batch analysis
- **CRISPRessoPooled**: Pooled amplicon analysis
- **CRISPRessoWGS**: Whole-genome sequencing analysis
- **CRISPRessoCompare**: Comparative analysis between samples
- **CRISPRessoAggregate**: Result aggregation
