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
    """End-to-end tests for base editing mode (CBE and ABE)."""

    def test_cbe_basic(self, temp_dir, random_seed, crispresso_available):
        """
        Test that CRISPResso correctly detects CBE edits (C→T conversions).
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
        edits_path = f"{output_prefix}_edits.tsv"

        result = run_crispresso(
            fastq_path=fastq_path,
            output_dir=temp_dir,
            amplicon=TEST_AMPLICON,
            guide=TEST_GUIDE,
            extra_args=["--base_editor_output"],
        )

        assert result.returncode == 0, f"CRISPResso failed: {result.stderr}"

        ground_truth = parse_edits_tsv(edits_path)
        alleles = parse_alleles_table(temp_dir)

        # Count substitutions in ground truth
        gt_substitutions = sum(1 for e in ground_truth if e['edit_type'] == 'substitution')

        # Count reads with mutations in CRISPResso
        crispresso_mutated = sum(
            int(a.get('#Reads', a.get('Reads', 0)))
            for a in alleles
            if int(a.get('n_mutated', 0)) > 0
        )

        # Verify substitution detection (allow 15% tolerance)
        tolerance = 0.15 * 1000
        assert abs(crispresso_mutated - gt_substitutions) <= tolerance, (
            f"Substitution count mismatch: CRISPResso={crispresso_mutated}, ground_truth={gt_substitutions}"
        )

    def test_abe_basic(self, temp_dir, random_seed, crispresso_available):
        """
        Test that CRISPResso correctly detects ABE edits (A→G conversions).
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
        edits_path = f"{output_prefix}_edits.tsv"

        result = run_crispresso(
            fastq_path=fastq_path,
            output_dir=temp_dir,
            amplicon=TEST_AMPLICON,
            guide=TEST_GUIDE,
            extra_args=["--base_editor_output"],
        )

        assert result.returncode == 0, f"CRISPResso failed: {result.stderr}"

        ground_truth = parse_edits_tsv(edits_path)
        alleles = parse_alleles_table(temp_dir)

        gt_substitutions = sum(1 for e in ground_truth if e['edit_type'] == 'substitution')

        crispresso_mutated = sum(
            int(a.get('#Reads', a.get('Reads', 0)))
            for a in alleles
            if int(a.get('n_mutated', 0)) > 0
        )

        tolerance = 0.15 * 1000
        assert abs(crispresso_mutated - gt_substitutions) <= tolerance, (
            f"ABE substitution count mismatch: CRISPResso={crispresso_mutated}, ground_truth={gt_substitutions}"
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
        edits_path = f"{output_prefix}_edits.tsv"

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

        ground_truth = parse_edits_tsv(edits_path)
        alleles = parse_alleles_table(temp_dir)

        # Count prime edits in ground truth
        gt_prime_edits = sum(1 for e in ground_truth if e['edit_type'] == 'prime_edit')
        gt_unedited = sum(1 for e in ground_truth if e['edit_type'] == 'none')

        # Count total reads
        total_crispresso_reads = sum(int(a.get('#Reads', a.get('Reads', 0))) for a in alleles)

        # Verify total read count
        assert total_crispresso_reads == 1000, (
            f"Read count mismatch: CRISPResso={total_crispresso_reads}, expected=1000"
        )

        # In prime editing mode, count reads assigned to each reference
        # Reference_Name column tells us which amplicon the reads aligned to
        reference_reads = 0
        prime_edited_reads = 0
        for allele in alleles:
            reads = int(allele.get('#Reads', allele.get('Reads', 0)))
            ref_name = allele.get('Reference_Name', '')
            if ref_name == 'Reference':
                reference_reads += reads
            elif ref_name == 'Prime-edited':
                prime_edited_reads += reads

        # Verify unedited count (allow 10% tolerance)
        tolerance = 0.10 * 1000
        assert abs(reference_reads - gt_unedited) <= tolerance, (
            f"Reference read count mismatch: CRISPResso={reference_reads}, ground_truth={gt_unedited}"
        )

        # Verify edited reads are detected (prime edits should align to Prime-edited reference)
        # Note: some prime edits with indels may align to Reference with modifications
        assert prime_edited_reads > 0, (
            f"No reads aligned to Prime-edited reference (expected ~{gt_prime_edits})"
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

        alleles = parse_alleles_table(temp_dir)

        # Count reads by reference assignment
        reference_reads = 0
        prime_edited_reads = 0
        for allele in alleles:
            reads = int(allele.get('#Reads', allele.get('Reads', 0)))
            ref_name = allele.get('Reference_Name', '')
            if ref_name == 'Reference':
                reference_reads += reads
            elif ref_name == 'Prime-edited':
                prime_edited_reads += reads

        # With 100% edit rate and perfect edits, all reads should align to Prime-edited
        # Allow small tolerance for alignment edge cases
        assert reference_reads <= 25, (
            f"Too many reads aligned to Reference: {reference_reads} (expected ~0)"
        )
        assert prime_edited_reads >= 475, (
            f"Too few reads aligned to Prime-edited: {prime_edited_reads} (expected ~500)"
        )
