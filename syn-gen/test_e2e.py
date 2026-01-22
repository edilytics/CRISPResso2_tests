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


def parse_syngen_alleles(alleles_path: str) -> dict[str, dict]:
    """
    Parse syn-gen's *_alleles.tsv file.

    Returns:
        Dict mapping sequence -> allele info dict
    """
    alleles = {}
    with open(alleles_path) as f:
        lines = f.read().strip().split('\n')
        if len(lines) < 2:
            return alleles

        header = lines[0].split('\t')
        for line in lines[1:]:
            values = line.split('\t')
            allele = dict(zip(header, values))
            seq = allele['Aligned_Sequence']
            alleles[seq] = allele

    return alleles


def parse_crispresso_alleles(crispresso_output_dir: str) -> dict[str, dict]:
    """
    Parse CRISPResso's Alleles_frequency_table.zip with detailed columns.

    Returns:
        Dict mapping sequence -> allele info dict
    """
    # Find the CRISPResso output folder
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

    alleles = {}
    with zipfile.ZipFile(zip_path, 'r') as zf:
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
                # Remove gaps from aligned sequence for comparison
                seq = allele['Aligned_Sequence'].replace('-', '')
                alleles[seq] = allele

    return alleles


def compare_alleles(syngen_alleles_path: str, crispresso_output_dir: str) -> list[str]:
    """
    Compare syn-gen ground truth against CRISPResso output.

    Args:
        syngen_alleles_path: Path to syn-gen's _alleles.tsv
        crispresso_output_dir: Path to CRISPResso output directory

    Returns:
        List of discrepancy messages (empty = all match)
    """
    syngen = parse_syngen_alleles(syngen_alleles_path)
    crispresso = parse_crispresso_alleles(crispresso_output_dir)

    discrepancies = []

    # Check for missing alleles (in syn-gen but not CRISPResso)
    for seq, sg_allele in syngen.items():
        if seq not in crispresso:
            count = sg_allele['#Reads']
            short_seq = seq[:20] + '...' + seq[-20:] if len(seq) > 50 else seq
            discrepancies.append(f"MISSING allele {short_seq} ({count} reads) - not found in CRISPResso")
            continue

        cr_allele = crispresso[seq]

        # Compare read counts
        sg_count = int(sg_allele['#Reads'])
        cr_count = int(cr_allele['#Reads'])
        if sg_count != cr_count:
            short_seq = seq[:20] + '...' + seq[-20:] if len(seq) > 50 else seq
            discrepancies.append(
                f"COUNT mismatch for {short_seq}: expected {sg_count}, got {cr_count}"
            )

        # Compare deletion positions
        sg_del = sg_allele.get('all_deletion_positions', '[]')
        cr_del = cr_allele.get('all_deletion_positions', '[]')
        if sg_del != cr_del:
            short_seq = seq[:20] + '...' + seq[-20:] if len(seq) > 50 else seq
            discrepancies.append(
                f"DELETION positions mismatch for {short_seq}: expected {sg_del}, got {cr_del}"
            )

        # Compare insertion positions
        sg_ins = sg_allele.get('all_insertion_positions', '[]')
        cr_ins = cr_allele.get('all_insertion_positions', '[]')
        if sg_ins != cr_ins:
            short_seq = seq[:20] + '...' + seq[-20:] if len(seq) > 50 else seq
            discrepancies.append(
                f"INSERTION positions mismatch for {short_seq}: expected {sg_ins}, got {cr_ins}"
            )

        # Compare substitution positions
        sg_sub = sg_allele.get('all_substitution_positions', '[]')
        cr_sub = cr_allele.get('all_substitution_positions', '[]')
        if sg_sub != cr_sub:
            short_seq = seq[:20] + '...' + seq[-20:] if len(seq) > 50 else seq
            discrepancies.append(
                f"SUBSTITUTION positions mismatch for {short_seq}: expected {sg_sub}, got {cr_sub}"
            )

    # Check for extra alleles (in CRISPResso but not syn-gen)
    for seq, cr_allele in crispresso.items():
        if seq not in syngen:
            count = cr_allele['#Reads']
            short_seq = seq[:20] + '...' + seq[-20:] if len(seq) > 50 else seq
            discrepancies.append(f"EXTRA allele {short_seq} ({count} reads) - unexpected in CRISPResso")

    return discrepancies


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
        alleles_path = f"{output_prefix}_alleles.tsv"

        result = run_crispresso(
            fastq_path=fastq_path,
            output_dir=temp_dir,
            amplicon=TEST_AMPLICON,
            guide=TEST_GUIDE,
        )

        assert result.returncode == 0, f"CRISPResso failed: {result.stderr}"

        discrepancies = compare_alleles(alleles_path, temp_dir)

        assert len(discrepancies) == 0, (
            f"Allele comparison failed with {len(discrepancies)} discrepancies:\n"
            + "\n".join(discrepancies[:10])
            + (f"\n... and {len(discrepancies) - 10} more" if len(discrepancies) > 10 else "")
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
        alleles_path = f"{output_prefix}_alleles.tsv"

        result = run_crispresso(
            fastq_path=fastq_path,
            output_dir=temp_dir,
            amplicon=TEST_AMPLICON,
            guide=TEST_GUIDE,
        )

        assert result.returncode == 0, f"CRISPResso failed: {result.stderr}"

        discrepancies = compare_alleles(alleles_path, temp_dir)

        assert len(discrepancies) == 0, (
            f"Allele comparison failed with {len(discrepancies)} discrepancies:\n"
            + "\n".join(discrepancies[:10])
            + (f"\n... and {len(discrepancies) - 10} more" if len(discrepancies) > 10 else "")
        )


class TestBaseEditingEndToEnd:
    """End-to-end tests for base editing mode (CBE and ABE)."""

    def test_cbe_basic(self, temp_dir, random_seed, crispresso_available):
        """
        Test that CRISPResso correctly detects CBE edits (C->T conversions).
        """
        random.seed(random_seed)

        output_prefix = os.path.join(temp_dir, "cbe_test")
        stats = generate_synthetic_data(
            amplicon=TEST_AMPLICON,
            guide=TEST_GUIDE,
            num_reads=1000,
            edit_rate=0.5,
            error_rate=0.0,
            output_prefix=output_prefix,
            seed=random_seed,
            quiet=True,
            mode='base-edit',
            base_editor='CBE',
            window_center=6,
            window_sigma=1.5,
            base_edit_prob=0.8,  # High conversion probability
        )

        fastq_path = f"{output_prefix}.fastq"
        alleles_path = f"{output_prefix}_alleles.tsv"

        result = run_crispresso(
            fastq_path=fastq_path,
            output_dir=temp_dir,
            amplicon=TEST_AMPLICON,
            guide=TEST_GUIDE,
            extra_args=["--base_editor_output"],
        )

        assert result.returncode == 0, f"CRISPResso failed: {result.stderr}"

        discrepancies = compare_alleles(alleles_path, temp_dir)

        assert len(discrepancies) == 0, (
            f"Allele comparison failed with {len(discrepancies)} discrepancies:\n"
            + "\n".join(discrepancies[:10])
            + (f"\n... and {len(discrepancies) - 10} more" if len(discrepancies) > 10 else "")
        )

    def test_abe_basic(self, temp_dir, random_seed, crispresso_available):
        """
        Test that CRISPResso correctly detects ABE edits (A->G conversions).
        """
        random.seed(random_seed)

        output_prefix = os.path.join(temp_dir, "abe_test")
        stats = generate_synthetic_data(
            amplicon=TEST_AMPLICON,
            guide=TEST_GUIDE,
            num_reads=1000,
            edit_rate=0.5,
            error_rate=0.0,
            output_prefix=output_prefix,
            seed=random_seed,
            quiet=True,
            mode='base-edit',
            base_editor='ABE',
            window_center=6,
            window_sigma=1.5,
            base_edit_prob=0.8,
        )

        fastq_path = f"{output_prefix}.fastq"
        alleles_path = f"{output_prefix}_alleles.tsv"

        result = run_crispresso(
            fastq_path=fastq_path,
            output_dir=temp_dir,
            amplicon=TEST_AMPLICON,
            guide=TEST_GUIDE,
            extra_args=["--base_editor_output"],
        )

        assert result.returncode == 0, f"CRISPResso failed: {result.stderr}"

        discrepancies = compare_alleles(alleles_path, temp_dir)

        assert len(discrepancies) == 0, (
            f"Allele comparison failed with {len(discrepancies)} discrepancies:\n"
            + "\n".join(discrepancies[:10])
            + (f"\n... and {len(discrepancies) - 10} more" if len(discrepancies) > 10 else "")
        )


class TestPrimeEditingEndToEnd:
    """End-to-end tests for prime editing mode."""

    def test_prime_edit_basic(self, temp_dir, random_seed, crispresso_available):
        """
        Test that CRISPResso correctly detects prime editing outcomes.

        In prime editing mode, CRISPResso creates multiple reference sequences:
        - Reference: the original amplicon
        - Prime-edited: the expected edited amplicon
        - Scaffold-incorporated: variant with scaffold sequence

        Reads are assigned to the best-matching reference. We verify that:
        1. Unedited reads match the "Reference" amplicon
        2. Edited reads match the "Prime-edited" amplicon
        """
        random.seed(random_seed)

        output_prefix = os.path.join(temp_dir, "pe_test")
        stats = generate_synthetic_data(
            amplicon=TEST_AMPLICON,
            guide=TEST_GUIDE,
            num_reads=1000,
            edit_rate=0.5,
            error_rate=0.0,
            output_prefix=output_prefix,
            seed=random_seed,
            quiet=True,
            mode='prime-edit',
            peg_extension=PE_EXTENSION,
            peg_scaffold=PE_SCAFFOLD,
            perfect_edit_fraction=0.8,  # Mostly perfect edits for cleaner validation
            partial_edit_fraction=0.1,
            pe_indel_fraction=0.1,
            scaffold_incorporation_fraction=0.0,
            flap_indel_fraction=0.0,
        )

        fastq_path = f"{output_prefix}.fastq"
        alleles_path = f"{output_prefix}_alleles.tsv"

        result = run_crispresso(
            fastq_path=fastq_path,
            output_dir=temp_dir,
            amplicon=TEST_AMPLICON,
            guide=TEST_GUIDE,
            extra_args=[
                "--prime_editing_pegRNA_spacer_seq", TEST_GUIDE,
                "--prime_editing_pegRNA_extension_seq", PE_EXTENSION,
                "--prime_editing_pegRNA_scaffold_seq", PE_SCAFFOLD,
            ],
        )

        assert result.returncode == 0, f"CRISPResso failed: {result.stderr}"

        discrepancies = compare_alleles(alleles_path, temp_dir)

        assert len(discrepancies) == 0, (
            f"Allele comparison failed with {len(discrepancies)} discrepancies:\n"
            + "\n".join(discrepancies[:10])
            + (f"\n... and {len(discrepancies) - 10} more" if len(discrepancies) > 10 else "")
        )

    def test_prime_edit_perfect_edits(self, temp_dir, random_seed, crispresso_available):
        """Test that perfect prime edits are detected with correct sequence."""
        random.seed(random_seed)

        output_prefix = os.path.join(temp_dir, "pe_perfect_test")
        stats = generate_synthetic_data(
            amplicon=TEST_AMPLICON,
            guide=TEST_GUIDE,
            num_reads=500,
            edit_rate=1.0,  # All reads edited
            error_rate=0.0,
            output_prefix=output_prefix,
            seed=random_seed,
            quiet=True,
            mode='prime-edit',
            peg_extension=PE_EXTENSION,
            peg_scaffold=PE_SCAFFOLD,
            perfect_edit_fraction=1.0,  # All perfect edits
            partial_edit_fraction=0.0,
            pe_indel_fraction=0.0,
            scaffold_incorporation_fraction=0.0,
            flap_indel_fraction=0.0,
        )

        fastq_path = f"{output_prefix}.fastq"
        alleles_path = f"{output_prefix}_alleles.tsv"

        result = run_crispresso(
            fastq_path=fastq_path,
            output_dir=temp_dir,
            amplicon=TEST_AMPLICON,
            guide=TEST_GUIDE,
            extra_args=[
                "--prime_editing_pegRNA_spacer_seq", TEST_GUIDE,
                "--prime_editing_pegRNA_extension_seq", PE_EXTENSION,
                "--prime_editing_pegRNA_scaffold_seq", PE_SCAFFOLD,
            ],
        )

        assert result.returncode == 0, f"CRISPResso failed: {result.stderr}"

        discrepancies = compare_alleles(alleles_path, temp_dir)

        assert len(discrepancies) == 0, (
            f"Allele comparison failed with {len(discrepancies)} discrepancies:\n"
            + "\n".join(discrepancies[:10])
            + (f"\n... and {len(discrepancies) - 10} more" if len(discrepancies) > 10 else "")
        )

    def test_syn_gen_crispresso_deletion_coordinates_match(
        self, temp_dir, random_seed, crispresso_available
    ):
        """E2E test: verify syn-gen and CRISPResso report same deletion coordinates."""
        import pandas as pd

        output_prefix = os.path.join(temp_dir, "del_coord_test")

        # Generate synthetic data with deletions only (NHEJ mode)
        stats = generate_synthetic_data(
            amplicon=TEST_AMPLICON,
            guide=TEST_GUIDE,
            num_reads=50,
            edit_rate=1.0,
            error_rate=0,
            output_prefix=output_prefix,
            seed=random_seed,
            mode='nhej',
            quiet=True,
        )

        fastq_path = f"{output_prefix}.fastq"
        alleles_path = f"{output_prefix}_alleles.tsv"

        # Run CRISPResso
        result = run_crispresso(
            fastq_path=fastq_path,
            output_dir=temp_dir,
            amplicon=TEST_AMPLICON,
            guide=TEST_GUIDE,
        )

        assert result.returncode == 0, f"CRISPResso failed: {result.stderr}"

        # Read syn-gen output
        syngen_df = pd.read_csv(alleles_path, sep='\t')

        # Read CRISPResso output
        crispresso_alleles = parse_crispresso_alleles(temp_dir)

        # Compare: for each syn-gen allele, find matching CRISPResso allele
        mismatches = []
        for _, syngen_row in syngen_df.iterrows():
            syngen_seq_no_gaps = syngen_row['Aligned_Sequence'].replace('-', '')

            # Find matching CRISPResso row by sequence
            if syngen_seq_no_gaps in crispresso_alleles:
                crisp_allele = crispresso_alleles[syngen_seq_no_gaps]

                # Compare deletion positions
                syngen_del = str(syngen_row['all_deletion_positions'])
                crisp_del = str(crisp_allele.get('all_deletion_positions', '[]'))

                if syngen_del != crisp_del:
                    mismatches.append(
                        f"Deletion mismatch: syn-gen={syngen_del}, CRISPResso={crisp_del}"
                    )

        assert len(mismatches) == 0, (
            f"Found {len(mismatches)} deletion coordinate mismatches:\n"
            + "\n".join(mismatches[:10])
        )
