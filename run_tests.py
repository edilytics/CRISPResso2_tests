#!/usr/bin/env python3
"""Thin wrapper that invokes pytest for CRISPResso2 integration tests.

Usage:
    python run_tests.py                  # run all tests
    python run_tests.py -k basic         # run a single test
    python run_tests.py -m vcf           # run by marker
    python run_tests.py --with-coverage  # measure CRISPResso2 coverage
"""
import subprocess
import sys

sys.exit(subprocess.call(['pytest', 'test_cli.py'] + sys.argv[1:]))
