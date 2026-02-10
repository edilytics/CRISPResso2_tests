"""End-to-end tests using BWA alignment verification."""

import os
import subprocess
import tempfile

import pytest

from syn_gen import generate_synthetic_data
from bwa_verify import verify_reads_with_bwa


# Standard test amplicon
TEST_AMPLICON = (
    "CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCAT"
    "GGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTG"
    "GGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG"
)
TEST_GUIDE = "GGAATCCCTTCTGCAGCACC"

# Prime editing parameters
PE_EXTENSION = "ATCTGGATCGGCTGCAGAAGGGA"


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def bwa_available():
    """Check if BWA is available."""
    import shutil
    if shutil.which("bwa") is None:
        pytest.skip("BWA not available in PATH")


class TestNHEJVerification:
    """BWA verification tests for NHEJ editing."""

    def test_nhej_deletions(self, temp_dir, bwa_available):
        """Verify deletions are correctly detected by BWA."""
        output_prefix = os.path.join(temp_dir, "nhej_del")

        generate_synthetic_data(
            amplicon=TEST_AMPLICON,
            guide=TEST_GUIDE,
            num_reads=100,
            edit_rate=1.0,
            error_rate=0.0,
            output_prefix=output_prefix,
            seed=42,
            quiet=True,
            mode='nhej',
        )

        result = verify_reads_with_bwa(
            amplicon=TEST_AMPLICON,
            fastq_path=f"{output_prefix}.fastq",
            edits_tsv_path=f"{output_prefix}_edits.tsv",
            temp_dir=temp_dir,
        )

        assert result.all_passed, (
            f"Failed {result.failed_reads}/{result.total_reads} reads:\n"
            + "\n".join(f"  {f.read_name}: {f.mismatches}" for f in result.failures[:5])
        )

    def test_nhej_mixed(self, temp_dir, bwa_available):
        """Verify mixed deletions and insertions."""
        output_prefix = os.path.join(temp_dir, "nhej_mixed")

        generate_synthetic_data(
            amplicon=TEST_AMPLICON,
            guide=TEST_GUIDE,
            num_reads=200,
            edit_rate=0.5,
            error_rate=0.0,
            output_prefix=output_prefix,
            seed=123,
            quiet=True,
            mode='nhej',
        )

        result = verify_reads_with_bwa(
            amplicon=TEST_AMPLICON,
            fastq_path=f"{output_prefix}.fastq",
            edits_tsv_path=f"{output_prefix}_edits.tsv",
            temp_dir=temp_dir,
        )

        assert result.all_passed, (
            f"Failed {result.failed_reads}/{result.total_reads} reads:\n"
            + "\n".join(f"  {f.read_name}: {f.mismatches}" for f in result.failures[:5])
        )


class TestBaseEditingVerification:
    """BWA verification tests for base editing."""

    def test_cbe_substitutions(self, temp_dir, bwa_available):
        """Verify CBE C->T substitutions are detected."""
        output_prefix = os.path.join(temp_dir, "cbe")

        generate_synthetic_data(
            amplicon=TEST_AMPLICON,
            guide=TEST_GUIDE,
            num_reads=100,
            edit_rate=1.0,
            error_rate=0.0,
            output_prefix=output_prefix,
            seed=42,
            quiet=True,
            mode='base-edit',
            base_editor='CBE',
            base_edit_prob=0.9,
        )

        result = verify_reads_with_bwa(
            amplicon=TEST_AMPLICON,
            fastq_path=f"{output_prefix}.fastq",
            edits_tsv_path=f"{output_prefix}_edits.tsv",
            temp_dir=temp_dir,
        )

        assert result.all_passed, (
            f"Failed {result.failed_reads}/{result.total_reads} reads:\n"
            + "\n".join(f"  {f.read_name}: {f.mismatches}" for f in result.failures[:5])
        )

    def test_abe_substitutions(self, temp_dir, bwa_available):
        """Verify ABE A->G substitutions are detected."""
        output_prefix = os.path.join(temp_dir, "abe")

        generate_synthetic_data(
            amplicon=TEST_AMPLICON,
            guide=TEST_GUIDE,
            num_reads=100,
            edit_rate=1.0,
            error_rate=0.0,
            output_prefix=output_prefix,
            seed=42,
            quiet=True,
            mode='base-edit',
            base_editor='ABE',
            base_edit_prob=0.9,
        )

        result = verify_reads_with_bwa(
            amplicon=TEST_AMPLICON,
            fastq_path=f"{output_prefix}.fastq",
            edits_tsv_path=f"{output_prefix}_edits.tsv",
            temp_dir=temp_dir,
        )

        assert result.all_passed, (
            f"Failed {result.failed_reads}/{result.total_reads} reads:\n"
            + "\n".join(f"  {f.read_name}: {f.mismatches}" for f in result.failures[:5])
        )


class TestPrimeEditingVerification:
    """BWA verification tests for prime editing."""

    def test_prime_edit_perfect(self, temp_dir, bwa_available):
        """Verify perfect prime edits are detected."""
        output_prefix = os.path.join(temp_dir, "pe_perfect")

        generate_synthetic_data(
            amplicon=TEST_AMPLICON,
            guide=TEST_GUIDE,
            num_reads=100,
            edit_rate=1.0,
            error_rate=0.0,
            output_prefix=output_prefix,
            seed=42,
            quiet=True,
            mode='prime-edit',
            peg_extension=PE_EXTENSION,
            perfect_edit_fraction=1.0,
            partial_edit_fraction=0.0,
            pe_indel_fraction=0.0,
            scaffold_incorporation_fraction=0.0,
            flap_indel_fraction=0.0,
        )

        result = verify_reads_with_bwa(
            amplicon=TEST_AMPLICON,
            fastq_path=f"{output_prefix}.fastq",
            edits_tsv_path=f"{output_prefix}_edits.tsv",
            temp_dir=temp_dir,
        )

        assert result.all_passed, (
            f"Failed {result.failed_reads}/{result.total_reads} reads:\n"
            + "\n".join(f"  {f.read_name}: {f.mismatches}" for f in result.failures[:5])
        )


class TestSequencingErrorVerification:
    """BWA verification tests including sequencing errors."""

    def test_errors_with_no_edit(self, temp_dir, bwa_available):
        """Verify sequencing errors detected on unedited reads."""
        output_prefix = os.path.join(temp_dir, "errors_only")

        generate_synthetic_data(
            amplicon=TEST_AMPLICON,
            guide=TEST_GUIDE,
            num_reads=100,
            edit_rate=0.0,  # No edits
            error_rate=0.01,  # 1% error rate
            output_prefix=output_prefix,
            seed=42,
            quiet=True,
            mode='nhej',
        )

        result = verify_reads_with_bwa(
            amplicon=TEST_AMPLICON,
            fastq_path=f"{output_prefix}.fastq",
            edits_tsv_path=f"{output_prefix}_edits.tsv",
            temp_dir=temp_dir,
        )

        assert result.all_passed, (
            f"Failed {result.failed_reads}/{result.total_reads} reads:\n"
            + "\n".join(f"  {f.read_name}: {f.mismatches}" for f in result.failures[:5])
        )

    def test_errors_with_edits(self, temp_dir, bwa_available):
        """Verify both edits and sequencing errors detected."""
        output_prefix = os.path.join(temp_dir, "errors_and_edits")

        generate_synthetic_data(
            amplicon=TEST_AMPLICON,
            guide=TEST_GUIDE,
            num_reads=100,
            edit_rate=0.5,
            error_rate=0.005,
            output_prefix=output_prefix,
            seed=42,
            quiet=True,
            mode='nhej',
        )

        result = verify_reads_with_bwa(
            amplicon=TEST_AMPLICON,
            fastq_path=f"{output_prefix}.fastq",
            edits_tsv_path=f"{output_prefix}_edits.tsv",
            temp_dir=temp_dir,
        )

        assert result.all_passed, (
            f"Failed {result.failed_reads}/{result.total_reads} reads:\n"
            + "\n".join(f"  {f.read_name}: {f.mismatches}" for f in result.failures[:5])
        )
