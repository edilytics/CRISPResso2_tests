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


@pytest.fixture
def random_seed():
    """Provide a consistent random seed for reproducible tests."""
    return 42


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

    def test_nhej_basic(self, temp_dir, random_seed, crispresso_available):
        """
        Test that CRISPResso correctly detects NHEJ edits (deletions/insertions).

        Generates synthetic data with 50% edit rate, runs CRISPResso,
        and verifies the detected edit counts match the ground truth.
        """
        random.seed(random_seed)

        # Generate synthetic data
        output_prefix = os.path.join(temp_dir, "nhej_test")
        stats = generate_synthetic_data(
            amplicon=TEST_AMPLICON,
            guide=TEST_GUIDE,
            num_reads=1000,
            edit_rate=0.5,
            error_rate=0.0,  # No sequencing errors for exact matching
            output_prefix=output_prefix,
            seed=random_seed,
            quiet=True,
            mode='nhej',
        )

        fastq_path = f"{output_prefix}.fastq"
        edits_path = f"{output_prefix}_edits.tsv"

        # Run CRISPResso
        result = run_crispresso(
            fastq_path=fastq_path,
            output_dir=temp_dir,
            amplicon=TEST_AMPLICON,
            guide=TEST_GUIDE,
        )

        # Check CRISPResso ran successfully
        assert result.returncode == 0, f"CRISPResso failed: {result.stderr}"

        # Parse results
        ground_truth = parse_edits_tsv(edits_path)
        alleles = parse_alleles_table(temp_dir)

        # Count edits in ground truth
        gt_edited = sum(1 for e in ground_truth if e['edit_type'] != 'none')
        gt_unedited = sum(1 for e in ground_truth if e['edit_type'] == 'none')

        # Count total reads in CRISPResso output
        total_crispresso_reads = sum(int(a.get('#Reads', a.get('Reads', 0))) for a in alleles)

        # Verify total read count matches
        assert total_crispresso_reads == 1000, (
            f"Read count mismatch: CRISPResso={total_crispresso_reads}, expected=1000"
        )

        # Find reference allele (unedited) in CRISPResso output
        ref_reads = 0
        for allele in alleles:
            n_deleted = int(allele.get('n_deleted', 0))
            n_inserted = int(allele.get('n_inserted', 0))
            n_mutated = int(allele.get('n_mutated', 0))
            if n_deleted == 0 and n_inserted == 0 and n_mutated == 0:
                ref_reads += int(allele.get('#Reads', allele.get('Reads', 0)))

        # Verify unedited count is close to ground truth (allow 5% tolerance)
        tolerance = 0.05 * 1000
        assert abs(ref_reads - gt_unedited) <= tolerance, (
            f"Unedited count mismatch: CRISPResso={ref_reads}, ground_truth={gt_unedited}"
        )

        # Verify edited count
        edited_reads = total_crispresso_reads - ref_reads
        assert abs(edited_reads - gt_edited) <= tolerance, (
            f"Edited count mismatch: CRISPResso={edited_reads}, ground_truth={gt_edited}"
        )

    def test_nhej_deletions_detected(self, temp_dir, random_seed, crispresso_available):
        """Test that deletions are correctly detected by CRISPResso."""
        random.seed(random_seed)

        output_prefix = os.path.join(temp_dir, "nhej_del_test")
        stats = generate_synthetic_data(
            amplicon=TEST_AMPLICON,
            guide=TEST_GUIDE,
            num_reads=500,
            edit_rate=1.0,  # All reads edited
            error_rate=0.0,
            output_prefix=output_prefix,
            seed=random_seed,
            quiet=True,
            mode='nhej',
        )

        fastq_path = f"{output_prefix}.fastq"
        edits_path = f"{output_prefix}_edits.tsv"

        result = run_crispresso(
            fastq_path=fastq_path,
            output_dir=temp_dir,
            amplicon=TEST_AMPLICON,
            guide=TEST_GUIDE,
        )

        assert result.returncode == 0, f"CRISPResso failed: {result.stderr}"

        ground_truth = parse_edits_tsv(edits_path)
        alleles = parse_alleles_table(temp_dir)

        # Count deletions in ground truth
        gt_deletions = sum(1 for e in ground_truth if e['edit_type'] == 'deletion')

        # Count reads with deletions in CRISPResso
        crispresso_deletions = sum(
            int(a.get('#Reads', a.get('Reads', 0)))
            for a in alleles
            if int(a.get('n_deleted', 0)) > 0
        )

        # Verify deletion detection (allow 10% tolerance due to alignment differences)
        tolerance = 0.10 * 500
        assert abs(crispresso_deletions - gt_deletions) <= tolerance, (
            f"Deletion count mismatch: CRISPResso={crispresso_deletions}, ground_truth={gt_deletions}"
        )


class TestBaseEditingEndToEnd:
    """End-to-end tests for base editing mode."""
    pass


class TestPrimeEditingEndToEnd:
    """End-to-end tests for prime editing mode."""
    pass
