"""End-to-end tests for syn-gen + CRISPResso integration."""

import os
import random
import subprocess
import tempfile
import zipfile
from pathlib import Path

import pytest

from syn_gen import generate_synthetic_data


# =============================================================================
# Constants
# =============================================================================

# Standard test amplicon (from existing CRISPResso tests)
TEST_AMPLICON = (
    "CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCAT"
    "GGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTG"
    "GGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG"
)

TEST_GUIDE = "GGAATCCCTTCTGCAGCACC"

# Prime editing parameters (from existing tests)
PE_EXTENSION = "ATCTGGATCGGCTGCAGAAGGGA"
PE_SCAFFOLD = "GTTTTAGAGCTAGAAATAGCAAGTTAAAATAAGGCTAGTCCGTTATCAACTTGAAAAAGTGGCACCGAGTCGGTGC"


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def crispresso_available():
    """Check if CRISPResso is available in PATH."""
    result = subprocess.run(
        ["which", "CRISPResso"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.skip("CRISPResso not available in PATH")
    return True


# =============================================================================
# Helper Functions
# =============================================================================

def run_crispresso(
    fastq_path: str,
    output_dir: str,
    amplicon: str,
    guide: str,
    extra_args: list[str] = None,
) -> subprocess.CompletedProcess:
    """
    Run CRISPResso on the given FASTQ file.

    Args:
        fastq_path: Path to input FASTQ file
        output_dir: Directory for CRISPResso output
        amplicon: Amplicon sequence
        guide: Guide sequence
        extra_args: Additional CRISPResso arguments

    Returns:
        CompletedProcess with stdout/stderr
    """
    cmd = [
        "CRISPResso",
        "-r1", fastq_path,
        "-a", amplicon,
        "-g", guide,
        "-o", output_dir,
        "--write_detailed_allele_table",
        "--place_report_in_output_folder",
        "-w", "20",  # quantification window size
        "-q", "0",   # no quality filtering (synthetic data is perfect)
    ]
    if extra_args:
        cmd.extend(extra_args)

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=300,  # 5 minute timeout
    )
    return result


def parse_alleles_table(crispresso_output_dir: str) -> list[dict]:
    """
    Parse Alleles_frequency_table.zip from CRISPResso output.

    Args:
        crispresso_output_dir: Path to CRISPResso output directory

    Returns:
        List of dicts with allele information
    """
    # Find the CRISPResso output folder (named CRISPResso_on_*)
    output_folders = [
        d for d in os.listdir(crispresso_output_dir)
        if d.startswith("CRISPResso_on_")
    ]
    if not output_folders:
        raise FileNotFoundError(f"No CRISPResso output folder in {crispresso_output_dir}")

    crispresso_folder = os.path.join(crispresso_output_dir, output_folders[0])
    zip_path = os.path.join(crispresso_folder, "Alleles_frequency_table.zip")

    if not os.path.exists(zip_path):
        raise FileNotFoundError(f"Alleles_frequency_table.zip not found in {crispresso_folder}")

    alleles = []
    with zipfile.ZipFile(zip_path, 'r') as zf:
        # Find the TSV file inside the zip
        tsv_files = [f for f in zf.namelist() if f.endswith('.txt')]
        if not tsv_files:
            raise FileNotFoundError("No .txt file in Alleles_frequency_table.zip")

        with zf.open(tsv_files[0]) as f:
            lines = f.read().decode('utf-8').strip().split('\n')
            if len(lines) < 2:
                return alleles

            header = lines[0].split('\t')
            for line in lines[1:]:
                values = line.split('\t')
                allele = dict(zip(header, values))
                alleles.append(allele)

    return alleles


def parse_edits_tsv(tsv_path: str) -> list[dict]:
    """
    Parse syn-gen's *_edits.tsv ground truth file.

    Args:
        tsv_path: Path to edits TSV file

    Returns:
        List of dicts with edit information per read
    """
    edits = []
    with open(tsv_path) as f:
        lines = f.read().strip().split('\n')
        if len(lines) < 2:
            return edits

        header = lines[0].split('\t')
        for line in lines[1:]:
            values = line.split('\t')
            edit = dict(zip(header, values))
            edits.append(edit)

    return edits


# =============================================================================
# Test Classes (placeholders for subsequent tasks)
# =============================================================================

class TestNHEJEndToEnd:
    """End-to-end tests for NHEJ editing mode."""
    pass


class TestBaseEditingEndToEnd:
    """End-to-end tests for base editing mode."""
    pass


class TestPrimeEditingEndToEnd:
    """End-to-end tests for prime editing mode."""
    pass
