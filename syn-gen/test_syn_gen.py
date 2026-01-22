#!/usr/bin/env python3
"""Unit tests for syn-gen."""

import os
import tempfile
import pytest
from hypothesis import given, strategies as st, settings, assume

from syn_gen import (
    FastqRead,
    Edit,
    EditedRead,
    VcfVariant,
    PrimeEditIntent,
    SequencingError,
    reverse_complement,
    generate_random_sequence,
    find_guide_in_amplicon,
    calculate_cut_site,
    apply_edit,
    apply_prime_edit,
    add_sequencing_errors,
    generate_quality_string,
    aggregate_edits_to_variants,
    generate_synthetic_data,
    validate_inputs,
    sample_deletion_size,
    sample_insertion_size,
    generate_edit,
    parse_peg_extension,
    generate_prime_edit,
)


# =============================================================================
# Hypothesis Strategies for DNA sequences
# =============================================================================

# Strategy for generating valid DNA bases
dna_base = st.sampled_from('ACGT')

# Strategy for generating DNA sequences of various lengths
dna_sequence = st.text(alphabet='ACGT', min_size=1, max_size=500)

# Strategy for short DNA sequences (guides are typically 17-23bp)
guide_sequence = st.text(alphabet='ACGT', min_size=15, max_size=25)

# Strategy for amplicon-sized sequences
amplicon_sequence = st.text(alphabet='ACGT', min_size=50, max_size=300)

# Strategy for valid rate parameters (0.0 to 1.0)
rate = st.floats(min_value=0.0, max_value=1.0, allow_nan=False)

# Strategy for positive integers
positive_int = st.integers(min_value=1, max_value=1000)


class TestFastqRead:
    def test_str_format(self):
        read = FastqRead(name='test_read', seq='ACGT', qual='IIII')
        expected = '@test_read\nACGT\n+\nIIII\n'
        assert str(read) == expected

    def test_with_long_sequence(self):
        seq = 'ACGT' * 50
        qual = 'I' * 200
        read = FastqRead(name='long_read', seq=seq, qual=qual)
        assert len(read.seq) == 200
        assert len(read.qual) == 200


class TestReverseComplement:
    def test_simple(self):
        assert reverse_complement('ACGT') == 'ACGT'

    def test_all_bases(self):
        assert reverse_complement('AAAA') == 'TTTT'
        assert reverse_complement('CCCC') == 'GGGG'
        assert reverse_complement('GGGG') == 'CCCC'
        assert reverse_complement('TTTT') == 'AAAA'

    def test_mixed(self):
        assert reverse_complement('AACG') == 'CGTT'

    def test_lowercase(self):
        assert reverse_complement('acgt') == 'ACGT'


class TestGenerateRandomSequence:
    def test_length(self):
        seq = generate_random_sequence(100)
        assert len(seq) == 100

    def test_valid_bases(self):
        seq = generate_random_sequence(1000)
        assert set(seq).issubset({'A', 'C', 'G', 'T'})


class TestFindGuideInAmplicon:
    def test_forward_match(self):
        amplicon = 'AAACCCGGAATCCCTTCTGCAGCACCGGGAAA'
        guide = 'GGAATCCCTTCTGCAGCACC'
        start, end, is_rc = find_guide_in_amplicon(amplicon, guide)
        assert start == 6  # 'AAACCC' is 6 chars, guide starts at index 6
        assert end == 26
        assert is_rc is False

    def test_reverse_complement_match(self):
        guide = 'GGAATCCCTTCTGCAGCACC'
        guide_rc = reverse_complement(guide)
        amplicon = f'AAACCC{guide_rc}GGGAAA'
        start, end, is_rc = find_guide_in_amplicon(amplicon, guide)
        assert is_rc is True
        assert amplicon[start:end] == guide_rc

    def test_not_found(self):
        amplicon = 'AAACCCGGGAAATTTCCC'
        guide = 'GGAATCCCTTCTGCAGCACC'
        with pytest.raises(ValueError, match='Guide sequence not found'):
            find_guide_in_amplicon(amplicon, guide)

    def test_case_insensitive(self):
        amplicon = 'aaacccGGAATCCCTTCTGCAGCACCgggaaa'
        guide = 'ggaatcccttctgcagcacc'
        start, end, is_rc = find_guide_in_amplicon(amplicon, guide)
        assert start == 6
        assert end == 26


class TestCalculateCutSite:
    def test_forward_default_offset(self):
        # Guide at 10-30, cleavage_offset=-3
        # Cut site = 30 + (-3) = 27
        cut = calculate_cut_site(10, 30, is_rc=False, cleavage_offset=-3)
        assert cut == 27

    def test_reverse_complement_default_offset(self):
        # For RC guide at 10-30, PAM-proximal end is at start
        # Cut site = 10 - (-3) - 1 = 12
        cut = calculate_cut_site(10, 30, is_rc=True, cleavage_offset=-3)
        assert cut == 12

    def test_custom_offset(self):
        cut = calculate_cut_site(10, 30, is_rc=False, cleavage_offset=-5)
        assert cut == 25


class TestApplyEdit:
    def test_no_edit(self):
        amplicon = 'AAAAACCCCCGGGGGTTTT'
        edit = Edit('none', 0, 0, '', '')
        result = apply_edit(amplicon, edit)
        assert result == amplicon

    def test_deletion(self):
        amplicon = 'AAAAACCCCCGGGGGTTTT'
        edit = Edit('deletion', 5, 5, 'CCCCC', '')
        result = apply_edit(amplicon, edit)
        assert result == 'AAAAAGGGGGTTTT'
        assert len(result) == len(amplicon) - 5

    def test_deletion_at_start(self):
        amplicon = 'AAAAACCCCC'
        edit = Edit('deletion', 0, 3, 'AAA', '')
        result = apply_edit(amplicon, edit)
        assert result == 'AACCCCC'

    def test_deletion_at_end(self):
        amplicon = 'AAAAACCCCC'
        # Position 7, size 3 deletes indices 7,8,9 (the last 3 C's)
        edit = Edit('deletion', 7, 3, 'CCC', '')
        result = apply_edit(amplicon, edit)
        assert result == 'AAAAACC'  # 5 A's + 2 C's (positions 5,6)

    def test_insertion(self):
        amplicon = 'AAAAAGGGGG'
        edit = Edit('insertion', 5, 3, '', 'TTT')
        result = apply_edit(amplicon, edit)
        assert result == 'AAAAATTTGGGGG'
        assert len(result) == len(amplicon) + 3

    def test_insertion_at_start(self):
        amplicon = 'AAAAAGGGGG'
        edit = Edit('insertion', 0, 2, '', 'CC')
        result = apply_edit(amplicon, edit)
        assert result == 'CCAAAAAGGGGG'

    def test_insertion_at_end(self):
        amplicon = 'AAAAAGGGGG'
        edit = Edit('insertion', 10, 2, '', 'TT')
        result = apply_edit(amplicon, edit)
        assert result == 'AAAAAGGGGGTT'


class TestAddSequencingErrors:
    def test_zero_error_rate(self):
        seq = 'ACGTACGTACGT'
        result, errors = add_sequencing_errors(seq, 0.0)
        assert result == seq
        assert errors == []

    def test_full_error_rate(self):
        seq = 'AAAA'
        result, errors = add_sequencing_errors(seq, 1.0)
        # All bases should be changed
        assert 'A' not in result
        assert len(errors) == 4

    def test_preserves_length(self):
        seq = 'ACGT' * 100
        result, errors = add_sequencing_errors(seq, 0.01)
        assert len(result) == len(seq)

    def test_errors_recorded_correctly(self):
        """Sequencing errors should be recorded with correct positions and bases."""
        seq = 'AAAA'
        result, errors = add_sequencing_errors(seq, 1.0)
        # Check that each error is valid
        for error in errors:
            assert error.original_base == 'A'
            assert error.error_base in 'CGT'
            assert 0 <= error.position < 4
            # Verify the error was applied at the recorded position
            assert result[error.position] == error.error_base


class TestGenerateQualityString:
    def test_default_quality(self):
        qual = generate_quality_string(10)
        assert qual == 'I' * 10

    def test_custom_quality(self):
        qual = generate_quality_string(5, 'H')
        assert qual == 'HHHHH'


class TestAggregateEditsToVariants:
    def test_single_deletion(self):
        amplicon = 'AAAAACCCCCGGGGG'
        reads = [
            EditedRead(
                read=FastqRead('r1', 'AAAAAGGGGG', 'IIIIIIIIII'),
                edit=Edit('deletion', 5, 5, 'CCCCC', '')
            )
        ]
        variants = aggregate_edits_to_variants(reads, amplicon, 'TEST')
        assert len(variants) == 1
        assert variants[0].af == 1.0
        assert variants[0].chrom == 'TEST'

    def test_no_edits(self):
        amplicon = 'AAAAACCCCC'
        reads = [
            EditedRead(
                read=FastqRead('r1', 'AAAAACCCCC', 'IIIIIIIIII'),
                edit=Edit('none', 0, 0, '', '')
            )
        ]
        variants = aggregate_edits_to_variants(reads, amplicon, 'TEST')
        assert len(variants) == 0

    def test_multiple_same_edit(self):
        amplicon = 'AAAAACCCCCGGGGG'
        edit = Edit('deletion', 5, 3, 'CCC', '')
        reads = [
            EditedRead(FastqRead('r1', '', ''), edit),
            EditedRead(FastqRead('r2', '', ''), edit),
            EditedRead(FastqRead('r3', '', ''), Edit('none', 0, 0, '', '')),
        ]
        variants = aggregate_edits_to_variants(reads, amplicon, 'TEST')
        assert len(variants) == 1
        assert abs(variants[0].af - 2/3) < 0.001


class TestValidateInputs:
    def test_valid_inputs(self):
        # Should not raise
        validate_inputs('ACGTACGT', 'ACGT', 0.5, 0.001)

    def test_invalid_amplicon(self):
        with pytest.raises(ValueError, match='Amplicon contains invalid'):
            validate_inputs('ACGTXYZ', 'ACGT', 0.5, 0.001)

    def test_invalid_guide(self):
        with pytest.raises(ValueError, match='Guide contains invalid'):
            validate_inputs('ACGT', 'ACGN', 0.5, 0.001)

    def test_edit_rate_too_high(self):
        with pytest.raises(ValueError, match='edit_rate must be between'):
            validate_inputs('ACGT', 'ACGT', 1.5, 0.001)

    def test_edit_rate_negative(self):
        with pytest.raises(ValueError, match='edit_rate must be between'):
            validate_inputs('ACGT', 'ACGT', -0.1, 0.001)

    def test_error_rate_too_high(self):
        with pytest.raises(ValueError, match='error_rate must be between'):
            validate_inputs('ACGT', 'ACGT', 0.5, 2.0)


class TestGenerateSyntheticData:
    def test_basic_generation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            prefix = os.path.join(tmpdir, 'test')
            amplicon = 'AAACCCGGAATCCCTTCTGCAGCACCGGGAAATTT'
            guide = 'GGAATCCCTTCTGCAGCACC'

            stats = generate_synthetic_data(
                amplicon=amplicon,
                guide=guide,
                num_reads=100,
                edit_rate=0.3,
                error_rate=0.0,
                output_prefix=prefix,
                seed=42,
                quiet=True,
            )

            assert stats['total_reads'] == 100
            assert stats['edited_reads'] + stats['unedited_reads'] == 100
            assert os.path.exists(f'{prefix}.fastq')
            assert os.path.exists(f'{prefix}_edits.tsv')
            assert os.path.exists(f'{prefix}.vcf')

    def test_reproducibility(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            amplicon = 'AAACCCGGAATCCCTTCTGCAGCACCGGGAAATTT'
            guide = 'GGAATCCCTTCTGCAGCACC'

            stats1 = generate_synthetic_data(
                amplicon=amplicon,
                guide=guide,
                num_reads=100,
                edit_rate=0.3,
                error_rate=0.001,
                output_prefix=os.path.join(tmpdir, 'test1'),
                seed=42,
                quiet=True,
            )

            stats2 = generate_synthetic_data(
                amplicon=amplicon,
                guide=guide,
                num_reads=100,
                edit_rate=0.3,
                error_rate=0.001,
                output_prefix=os.path.join(tmpdir, 'test2'),
                seed=42,
                quiet=True,
            )

            assert stats1['edited_reads'] == stats2['edited_reads']
            assert stats1['deletions'] == stats2['deletions']
            assert stats1['insertions'] == stats2['insertions']

    def test_zero_edit_rate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            prefix = os.path.join(tmpdir, 'test')
            amplicon = 'AAACCCGGAATCCCTTCTGCAGCACCGGGAAATTT'
            guide = 'GGAATCCCTTCTGCAGCACC'

            stats = generate_synthetic_data(
                amplicon=amplicon,
                guide=guide,
                num_reads=100,
                edit_rate=0.0,
                error_rate=0.0,
                output_prefix=prefix,
                quiet=True,
            )

            assert stats['edited_reads'] == 0
            assert stats['unedited_reads'] == 100

    def test_full_edit_rate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            prefix = os.path.join(tmpdir, 'test')
            amplicon = 'AAACCCGGAATCCCTTCTGCAGCACCGGGAAATTT'
            guide = 'GGAATCCCTTCTGCAGCACC'

            stats = generate_synthetic_data(
                amplicon=amplicon,
                guide=guide,
                num_reads=100,
                edit_rate=1.0,
                error_rate=0.0,
                output_prefix=prefix,
                quiet=True,
            )

            assert stats['edited_reads'] == 100
            assert stats['unedited_reads'] == 0


# =============================================================================
# Hypothesis Property-Based Tests
# =============================================================================

class TestReverseComplementProperties:
    """Property-based tests for reverse_complement function."""

    @given(seq=dna_sequence)
    def test_involution(self, seq):
        """Applying reverse complement twice returns the original sequence."""
        assert reverse_complement(reverse_complement(seq)) == seq.upper()

    @given(seq=dna_sequence)
    def test_preserves_length(self, seq):
        """Reverse complement preserves sequence length."""
        assert len(reverse_complement(seq)) == len(seq)

    @given(seq=dna_sequence)
    def test_only_valid_bases(self, seq):
        """Reverse complement only produces valid DNA bases."""
        result = reverse_complement(seq)
        assert set(result).issubset({'A', 'C', 'G', 'T'})

    @given(seq=dna_sequence)
    def test_base_counts_preserved(self, seq):
        """A↔T and C↔G counts are swapped correctly."""
        seq_upper = seq.upper()
        result = reverse_complement(seq)
        assert seq_upper.count('A') == result.count('T')
        assert seq_upper.count('T') == result.count('A')
        assert seq_upper.count('C') == result.count('G')
        assert seq_upper.count('G') == result.count('C')


class TestGenerateRandomSequenceProperties:
    """Property-based tests for generate_random_sequence function."""

    @given(length=st.integers(min_value=0, max_value=1000))
    def test_correct_length(self, length):
        """Generated sequence has the requested length."""
        seq = generate_random_sequence(length)
        assert len(seq) == length

    @given(length=st.integers(min_value=1, max_value=1000))
    def test_only_valid_bases(self, length):
        """Generated sequence only contains valid DNA bases."""
        seq = generate_random_sequence(length)
        assert set(seq).issubset({'A', 'C', 'G', 'T'})


class TestApplyEditProperties:
    """Property-based tests for apply_edit function."""

    @given(amplicon=amplicon_sequence)
    def test_no_edit_identity(self, amplicon):
        """Applying no edit returns the original sequence."""
        edit = Edit('none', 0, 0, '', '')
        result = apply_edit(amplicon, edit)
        assert result == amplicon

    @given(
        amplicon=amplicon_sequence,
        position=st.integers(min_value=0, max_value=49),
        size=st.integers(min_value=1, max_value=10)
    )
    def test_deletion_shortens_sequence(self, amplicon, position, size):
        """Deletion reduces sequence length by the deletion size."""
        assume(len(amplicon) >= 50)  # Ensure amplicon is long enough
        assume(position + size <= len(amplicon))  # Ensure deletion is valid

        original_seq = amplicon[position:position + size]
        edit = Edit('deletion', position, size, original_seq, '')
        result = apply_edit(amplicon, edit)

        assert len(result) == len(amplicon) - size

    @given(
        amplicon=amplicon_sequence,
        position=st.integers(min_value=0, max_value=49),
        insertion=st.text(alphabet='ACGT', min_size=1, max_size=10)
    )
    def test_insertion_lengthens_sequence(self, amplicon, position, insertion):
        """Insertion increases sequence length by the insertion size."""
        assume(len(amplicon) >= 50)  # Ensure amplicon is long enough
        assume(position <= len(amplicon))

        edit = Edit('insertion', position, len(insertion), '', insertion)
        result = apply_edit(amplicon, edit)

        assert len(result) == len(amplicon) + len(insertion)

    @given(
        amplicon=amplicon_sequence,
        position=st.integers(min_value=0, max_value=49),
        insertion=st.text(alphabet='ACGT', min_size=1, max_size=10)
    )
    def test_insertion_contains_inserted_sequence(self, amplicon, position, insertion):
        """Insertion places the inserted sequence at the correct position."""
        assume(len(amplicon) >= 50)
        assume(position <= len(amplicon))

        edit = Edit('insertion', position, len(insertion), '', insertion)
        result = apply_edit(amplicon, edit)

        assert insertion in result
        assert result[position:position + len(insertion)] == insertion


class TestAddSequencingErrorsProperties:
    """Property-based tests for add_sequencing_errors function."""

    @given(seq=dna_sequence)
    def test_zero_error_rate_preserves_sequence(self, seq):
        """Zero error rate returns the original sequence."""
        result, errors = add_sequencing_errors(seq, 0.0)
        assert result == seq
        assert errors == []

    @given(seq=dna_sequence, error_rate=rate)
    def test_preserves_length(self, seq, error_rate):
        """Error introduction preserves sequence length."""
        result, errors = add_sequencing_errors(seq, error_rate)
        assert len(result) == len(seq)

    @given(seq=dna_sequence, error_rate=rate)
    def test_only_valid_bases(self, seq, error_rate):
        """Errors only introduce valid DNA bases."""
        result, errors = add_sequencing_errors(seq, error_rate)
        assert set(result).issubset({'A', 'C', 'G', 'T'})

    @given(seq=dna_sequence, error_rate=rate)
    def test_error_count_matches_list(self, seq, error_rate):
        """Number of errors recorded matches changes made."""
        result, errors = add_sequencing_errors(seq, error_rate)
        # Each error should correspond to a change
        for error in errors:
            assert result[error.position] == error.error_base
            assert seq[error.position].upper() == error.original_base


class TestGenerateQualityStringProperties:
    """Property-based tests for generate_quality_string function."""

    @given(length=st.integers(min_value=0, max_value=1000))
    def test_correct_length(self, length):
        """Quality string has the requested length."""
        qual = generate_quality_string(length)
        assert len(qual) == length

    @given(
        length=st.integers(min_value=1, max_value=100),
        char=st.characters(whitelist_categories=['L', 'N'], min_codepoint=33, max_codepoint=126)
    )
    def test_uniform_quality(self, length, char):
        """Quality string uses the specified character uniformly."""
        qual = generate_quality_string(length, char)
        assert all(c == char for c in qual)


class TestFindGuideInAmpliconProperties:
    """Property-based tests for find_guide_in_amplicon function."""

    @given(
        prefix=st.text(alphabet='ACGT', min_size=10, max_size=50),
        guide=guide_sequence,
        suffix=st.text(alphabet='ACGT', min_size=10, max_size=50)
    )
    def test_embedded_guide_found_forward(self, prefix, guide, suffix):
        """Guide embedded in amplicon is always found (forward strand)."""
        amplicon = prefix + guide + suffix
        start, end, is_rc = find_guide_in_amplicon(amplicon, guide)

        assert is_rc is False
        assert amplicon[start:end].upper() == guide.upper()

    @given(
        prefix=st.text(alphabet='ACGT', min_size=10, max_size=50),
        guide=guide_sequence,
        suffix=st.text(alphabet='ACGT', min_size=10, max_size=50)
    )
    def test_embedded_guide_found_reverse(self, prefix, guide, suffix):
        """Guide embedded as reverse complement is found."""
        guide_rc = reverse_complement(guide)
        # Skip palindromes where forward and RC are the same
        assume(guide.upper() != guide_rc)
        # Ensure the guide doesn't appear in prefix/suffix in forward orientation
        assume(guide.upper() not in prefix.upper())
        assume(guide.upper() not in suffix.upper())

        amplicon = prefix + guide_rc + suffix
        start, end, is_rc = find_guide_in_amplicon(amplicon, guide)

        assert is_rc is True
        assert amplicon[start:end].upper() == guide_rc.upper()

    @given(
        prefix=st.text(alphabet='ACGT', min_size=10, max_size=50),
        guide=guide_sequence,
        suffix=st.text(alphabet='ACGT', min_size=10, max_size=50)
    )
    def test_guide_position_correct(self, prefix, guide, suffix):
        """Found guide position matches expected position."""
        amplicon = prefix + guide + suffix
        # Ensure the first occurrence of the guide is at the expected position
        # (not earlier due to overlap with prefix)
        assume(amplicon.upper().find(guide.upper()) == len(prefix))

        start, end, is_rc = find_guide_in_amplicon(amplicon, guide)

        assert start == len(prefix)
        assert end == len(prefix) + len(guide)


class TestCalculateCutSiteProperties:
    """Property-based tests for calculate_cut_site function."""

    @given(
        guide_start=st.integers(min_value=0, max_value=100),
        guide_length=st.integers(min_value=15, max_value=25),
        offset=st.integers(min_value=-10, max_value=0)
    )
    def test_forward_cut_site_within_expected_range(self, guide_start, guide_length, offset):
        """Forward strand cut site is near the 3' end of the guide."""
        guide_end = guide_start + guide_length
        cut = calculate_cut_site(guide_start, guide_end, is_rc=False, cleavage_offset=offset)

        # Cut should be near the end of the guide (within offset range)
        assert guide_end + offset == cut

    @given(
        guide_start=st.integers(min_value=10, max_value=100),
        guide_length=st.integers(min_value=15, max_value=25),
        offset=st.integers(min_value=-10, max_value=0)
    )
    def test_rc_cut_site_within_expected_range(self, guide_start, guide_length, offset):
        """Reverse complement cut site is near the 5' end of the guide."""
        guide_end = guide_start + guide_length
        cut = calculate_cut_site(guide_start, guide_end, is_rc=True, cleavage_offset=offset)

        # Cut should be near the start of the guide (within offset range)
        assert guide_start - offset - 1 == cut


class TestSampleEditSizeProperties:
    """Property-based tests for edit size sampling functions."""

    @given(st.randoms())
    @settings(max_examples=200)
    def test_deletion_size_positive(self, _):
        """Deletion size is always positive."""
        size = sample_deletion_size()
        assert size >= 1

    @given(st.randoms())
    @settings(max_examples=200)
    def test_deletion_size_bounded(self, _):
        """Deletion size respects maximum bound."""
        max_size = 50
        size = sample_deletion_size(max_size=max_size)
        assert size <= max_size

    @given(st.randoms())
    @settings(max_examples=200)
    def test_insertion_size_positive(self, _):
        """Insertion size is always positive."""
        size = sample_insertion_size()
        assert size >= 1

    @given(st.randoms())
    @settings(max_examples=200)
    def test_insertion_size_bounded(self, _):
        """Insertion size respects maximum bound."""
        max_size = 10
        size = sample_insertion_size(max_size=max_size)
        assert size <= max_size


class TestGenerateEditProperties:
    """Property-based tests for generate_edit function."""

    @given(
        cut_site=st.integers(min_value=20, max_value=80),
        amplicon=amplicon_sequence
    )
    @settings(max_examples=100)
    def test_edit_near_cut_site(self, cut_site, amplicon):
        """Generated edits are near the cut site."""
        assume(len(amplicon) >= 100)
        assume(cut_site < len(amplicon) - 10)

        edit = generate_edit(cut_site, amplicon)

        # Edit position should be within jitter range of cut site
        assert abs(edit.position - cut_site) <= 2

    @given(
        cut_site=st.integers(min_value=20, max_value=80),
        amplicon=amplicon_sequence
    )
    @settings(max_examples=100)
    def test_edit_type_valid(self, cut_site, amplicon):
        """Generated edit has valid type."""
        assume(len(amplicon) >= 100)
        assume(cut_site < len(amplicon) - 10)

        edit = generate_edit(cut_site, amplicon)

        assert edit.edit_type in ('deletion', 'insertion')

    @given(
        cut_site=st.integers(min_value=20, max_value=80),
        amplicon=amplicon_sequence
    )
    @settings(max_examples=100)
    def test_deletion_has_original_seq(self, cut_site, amplicon):
        """Deletion edits have correct original sequence."""
        assume(len(amplicon) >= 100)
        assume(cut_site < len(amplicon) - 10)

        edit = generate_edit(cut_site, amplicon, deletion_weight=1.0)  # Force deletion

        assert edit.edit_type == 'deletion'
        assert edit.original_seq == amplicon[edit.position:edit.position + edit.size]
        assert edit.edited_seq == ''

    @given(
        cut_site=st.integers(min_value=20, max_value=80),
        amplicon=amplicon_sequence
    )
    @settings(max_examples=100)
    def test_insertion_has_valid_sequence(self, cut_site, amplicon):
        """Insertion edits have valid inserted sequence."""
        assume(len(amplicon) >= 100)
        assume(cut_site < len(amplicon) - 10)

        edit = generate_edit(cut_site, amplicon, deletion_weight=0.0)  # Force insertion

        assert edit.edit_type == 'insertion'
        assert edit.original_seq == ''
        assert len(edit.edited_seq) == edit.size
        assert set(edit.edited_seq).issubset({'A', 'C', 'G', 'T'})


class TestGenerateSyntheticDataProperties:
    """Property-based tests for the main generation function."""

    @given(
        num_reads=st.integers(min_value=10, max_value=500),
        edit_rate=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        seed=st.integers(min_value=0, max_value=2**31)
    )
    @settings(max_examples=20, deadline=None)
    def test_total_reads_correct(self, num_reads, edit_rate, seed):
        """Total reads equals requested number."""
        with tempfile.TemporaryDirectory() as tmpdir:
            prefix = os.path.join(tmpdir, 'test')
            amplicon = 'AAACCCGGAATCCCTTCTGCAGCACCGGGAAATTT'
            guide = 'GGAATCCCTTCTGCAGCACC'

            stats = generate_synthetic_data(
                amplicon=amplicon,
                guide=guide,
                num_reads=num_reads,
                edit_rate=edit_rate,
                error_rate=0.0,
                output_prefix=prefix,
                seed=seed,
                quiet=True,
            )

            assert stats['total_reads'] == num_reads

    @given(
        num_reads=st.integers(min_value=10, max_value=500),
        edit_rate=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        seed=st.integers(min_value=0, max_value=2**31)
    )
    @settings(max_examples=20, deadline=None)
    def test_edit_counts_sum_correctly(self, num_reads, edit_rate, seed):
        """Edited + unedited = total reads."""
        with tempfile.TemporaryDirectory() as tmpdir:
            prefix = os.path.join(tmpdir, 'test')
            amplicon = 'AAACCCGGAATCCCTTCTGCAGCACCGGGAAATTT'
            guide = 'GGAATCCCTTCTGCAGCACC'

            stats = generate_synthetic_data(
                amplicon=amplicon,
                guide=guide,
                num_reads=num_reads,
                edit_rate=edit_rate,
                error_rate=0.0,
                output_prefix=prefix,
                seed=seed,
                quiet=True,
            )

            assert stats['edited_reads'] + stats['unedited_reads'] == stats['total_reads']

    @given(
        num_reads=st.integers(min_value=10, max_value=500),
        edit_rate=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        seed=st.integers(min_value=0, max_value=2**31)
    )
    @settings(max_examples=20, deadline=None)
    def test_deletion_insertion_sum_to_edited(self, num_reads, edit_rate, seed):
        """Deletions + insertions = edited reads."""
        with tempfile.TemporaryDirectory() as tmpdir:
            prefix = os.path.join(tmpdir, 'test')
            amplicon = 'AAACCCGGAATCCCTTCTGCAGCACCGGGAAATTT'
            guide = 'GGAATCCCTTCTGCAGCACC'

            stats = generate_synthetic_data(
                amplicon=amplicon,
                guide=guide,
                num_reads=num_reads,
                edit_rate=edit_rate,
                error_rate=0.0,
                output_prefix=prefix,
                seed=seed,
                quiet=True,
            )

            assert stats['deletions'] + stats['insertions'] == stats['edited_reads']

    @given(seed=st.integers(min_value=0, max_value=2**31))
    @settings(max_examples=10, deadline=None)
    def test_zero_edit_rate_no_edits(self, seed):
        """Zero edit rate produces no edited reads."""
        with tempfile.TemporaryDirectory() as tmpdir:
            prefix = os.path.join(tmpdir, 'test')
            amplicon = 'AAACCCGGAATCCCTTCTGCAGCACCGGGAAATTT'
            guide = 'GGAATCCCTTCTGCAGCACC'

            stats = generate_synthetic_data(
                amplicon=amplicon,
                guide=guide,
                num_reads=100,
                edit_rate=0.0,
                error_rate=0.0,
                output_prefix=prefix,
                seed=seed,
                quiet=True,
            )

            assert stats['edited_reads'] == 0
            assert stats['deletions'] == 0
            assert stats['insertions'] == 0

    @given(seed=st.integers(min_value=0, max_value=2**31))
    @settings(max_examples=10, deadline=None)
    def test_full_edit_rate_all_edited(self, seed):
        """100% edit rate produces all edited reads."""
        with tempfile.TemporaryDirectory() as tmpdir:
            prefix = os.path.join(tmpdir, 'test')
            amplicon = 'AAACCCGGAATCCCTTCTGCAGCACCGGGAAATTT'
            guide = 'GGAATCCCTTCTGCAGCACC'

            stats = generate_synthetic_data(
                amplicon=amplicon,
                guide=guide,
                num_reads=100,
                edit_rate=1.0,
                error_rate=0.0,
                output_prefix=prefix,
                seed=seed,
                quiet=True,
            )

            assert stats['edited_reads'] == 100
            assert stats['unedited_reads'] == 0

    @given(
        num_reads=st.integers(min_value=100, max_value=500),
        seed=st.integers(min_value=0, max_value=2**31)
    )
    @settings(max_examples=10, deadline=None)
    def test_edit_rate_approximately_correct(self, num_reads, seed):
        """Actual edit rate is approximately the requested rate (within statistical bounds)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            prefix = os.path.join(tmpdir, 'test')
            amplicon = 'AAACCCGGAATCCCTTCTGCAGCACCGGGAAATTT'
            guide = 'GGAATCCCTTCTGCAGCACC'
            edit_rate = 0.3

            stats = generate_synthetic_data(
                amplicon=amplicon,
                guide=guide,
                num_reads=num_reads,
                edit_rate=edit_rate,
                error_rate=0.0,
                output_prefix=prefix,
                seed=seed,
                quiet=True,
            )

            actual_rate = stats['edited_reads'] / stats['total_reads']
            # Allow 15% relative tolerance for statistical variation
            assert abs(actual_rate - edit_rate) < 0.15

    @given(
        num_reads=st.integers(min_value=100, max_value=500),
        seed=st.integers(min_value=0, max_value=2**31)
    )
    @settings(max_examples=10, deadline=None)
    def test_output_files_created(self, num_reads, seed):
        """All output files are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            prefix = os.path.join(tmpdir, 'test')
            amplicon = 'AAACCCGGAATCCCTTCTGCAGCACCGGGAAATTT'
            guide = 'GGAATCCCTTCTGCAGCACC'

            stats = generate_synthetic_data(
                amplicon=amplicon,
                guide=guide,
                num_reads=num_reads,
                edit_rate=0.3,
                error_rate=0.0,
                output_prefix=prefix,
                seed=seed,
                quiet=True,
            )

            assert os.path.exists(stats['output_files']['fastq'])
            assert os.path.exists(stats['output_files']['tsv'])
            assert os.path.exists(stats['output_files']['vcf'])


class TestVcfVariantProperties:
    """Property-based tests for VCF variant aggregation."""

    @given(
        num_reads=st.integers(min_value=10, max_value=100),
        seed=st.integers(min_value=0, max_value=2**31)
    )
    @settings(max_examples=20, deadline=None)
    def test_variant_frequencies_sum_correctly(self, num_reads, seed):
        """VCF variant frequencies don't exceed 1.0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            prefix = os.path.join(tmpdir, 'test')
            amplicon = 'AAACCCGGAATCCCTTCTGCAGCACCGGGAAATTT'
            guide = 'GGAATCCCTTCTGCAGCACC'

            generate_synthetic_data(
                amplicon=amplicon,
                guide=guide,
                num_reads=num_reads,
                edit_rate=0.5,
                error_rate=0.0,
                output_prefix=prefix,
                seed=seed,
                quiet=True,
            )

            # Read VCF and check all AFs are valid
            vcf_path = f'{prefix}.vcf'
            with open(vcf_path) as f:
                for line in f:
                    if line.startswith('#'):
                        continue
                    parts = line.strip().split('\t')
                    info = parts[7]
                    af = float(info.split('=')[1])
                    assert 0.0 < af <= 1.0


# =============================================================================
# Prime Editing Tests
# =============================================================================

class TestParsePegExtension:
    """Tests for parse_peg_extension function."""

    # Standard test amplicon and guide from CRISPResso tests
    AMPLICON = 'CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG'
    GUIDE = 'GGAATCCCTTCTGCAGCACC'
    CUT_SITE = 92  # Guide at 75-95, cut site = 95 - 3 = 92

    def test_rt_template_is_reverse_complemented(self):
        """RT template should be reverse complemented to match CRISPResso behavior."""
        peg_extension = 'ATCTGGATCGGCTGCAGAAGGGA'  # RT template + PBS

        intent = parse_peg_extension(
            amplicon=self.AMPLICON,
            cut_site=self.CUT_SITE,
            peg_extension=peg_extension,
            pbs_length=13,
        )

        # RT template is first 10 bp: ATCTGGATCG
        # RC of RT template: CGATCCAGAT
        assert intent.edited_seq == 'CGATCCAGAT'
        assert intent.original_seq == 'ACCTGGATCG'  # Reference at position 92-102

    def test_edit_type_substitution(self):
        """Same length RT template = substitution."""
        peg_extension = 'ATCTGGATCGGCTGCAGAAGGGA'

        intent = parse_peg_extension(
            amplicon=self.AMPLICON,
            cut_site=self.CUT_SITE,
            peg_extension=peg_extension,
            pbs_length=13,
        )

        assert intent.edit_type == 'substitution'
        assert len(intent.edited_seq) == len(intent.original_seq)

    def test_edit_position(self):
        """Edit should be at the cut site."""
        peg_extension = 'ATCTGGATCGGCTGCAGAAGGGA'

        intent = parse_peg_extension(
            amplicon=self.AMPLICON,
            cut_site=self.CUT_SITE,
            peg_extension=peg_extension,
            pbs_length=13,
        )

        assert intent.position == self.CUT_SITE

    def test_pbs_boundaries(self):
        """PBS should span cut_site - pbs_length to cut_site."""
        peg_extension = 'ATCTGGATCGGCTGCAGAAGGGA'

        intent = parse_peg_extension(
            amplicon=self.AMPLICON,
            cut_site=self.CUT_SITE,
            peg_extension=peg_extension,
            pbs_length=13,
        )

        assert intent.pbs_start == self.CUT_SITE - 13
        assert intent.pbs_end == self.CUT_SITE

    def test_empty_rt_template_raises(self):
        """Should raise if pbs_length >= len(peg_extension)."""
        peg_extension = 'GCTGCAGAAGGGA'  # 13 bp, all PBS

        with pytest.raises(ValueError, match="RT template is empty"):
            parse_peg_extension(
                amplicon=self.AMPLICON,
                cut_site=self.CUT_SITE,
                peg_extension=peg_extension,
                pbs_length=13,
            )


class TestGeneratePrimeEdit:
    """Tests for generate_prime_edit function."""

    def test_perfect_edit(self):
        """Perfect edit should exactly match the intent."""
        intent = PrimeEditIntent(
            edit_type='substitution',
            position=92,
            original_seq='ACCTGGATCG',
            edited_seq='CGATCCAGAT',
            pbs_start=79,
            pbs_end=92,
            rt_template='CGATCCAGAT',
        )

        edit = generate_prime_edit(
            amplicon='A' * 223,  # Dummy amplicon
            intent=intent,
            outcome_type='perfect',
        )

        assert edit.edit_type == 'prime_edit'
        assert edit.original_seq == 'ACCTGGATCG'
        assert edit.edited_seq == 'CGATCCAGAT'
        assert edit.position == 92

    def test_indel_outcome(self):
        """Indel outcome should generate deletion or insertion."""
        intent = PrimeEditIntent(
            edit_type='substitution',
            position=92,
            original_seq='ACCTGGATCG',
            edited_seq='CGATCCAGAT',
            pbs_start=79,
            pbs_end=92,
            rt_template='CGATCCAGAT',
        )

        amplicon = 'A' * 100 + 'ACCTGGATCG' + 'A' * 113

        edit = generate_prime_edit(
            amplicon=amplicon,
            intent=intent,
            outcome_type='indel',
        )

        assert edit.edit_type in ('deletion', 'insertion')


class TestApplyPrimeEdit:
    """Tests for apply_prime_edit function."""

    AMPLICON = 'CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG'

    def test_substitution_edit(self):
        """Substitution edit should replace sequence at position."""
        edit = Edit(
            edit_type='prime_edit',
            position=92,
            size=0,
            original_seq='ACCTGGATCG',
            edited_seq='CGATCCAGAT',
        )

        result = apply_prime_edit(self.AMPLICON, edit)

        # Check the edit was applied correctly
        assert result[92:102] == 'CGATCCAGAT'
        # Check flanking regions are unchanged
        assert result[:92] == self.AMPLICON[:92]
        assert result[102:] == self.AMPLICON[102:]

    def test_no_edit(self):
        """No edit should return original amplicon."""
        edit = Edit(
            edit_type='none',
            position=0,
            size=0,
            original_seq='',
            edited_seq='',
        )

        result = apply_prime_edit(self.AMPLICON, edit)
        assert result == self.AMPLICON

    def test_matches_crispresso_expectation(self):
        """Generated sequence should match what CRISPResso expects."""
        # This is the critical test - verify syn-gen output matches CRISPResso's
        # Prime-edited reference sequence

        edit = Edit(
            edit_type='prime_edit',
            position=92,
            size=0,
            original_seq='ACCTGGATCG',
            edited_seq='CGATCCAGAT',
        )

        result = apply_prime_edit(self.AMPLICON, edit)

        # CRISPResso Prime-edited reference at position 85-105:
        # CTGCAGCCGATCCAGATCTT
        assert result[85:105] == 'CTGCAGCCGATCCAGATCTT'


class TestPrimeEditingIntegration:
    """Integration tests for prime editing data generation."""

    AMPLICON = 'CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG'
    GUIDE = 'GGAATCCCTTCTGCAGCACC'
    PEG_EXTENSION = 'ATCTGGATCGGCTGCAGAAGGGA'

    def test_prime_edit_mode_generates_correct_sequences(self):
        """Prime edit mode should generate sequences matching CRISPResso expectations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            prefix = os.path.join(tmpdir, 'test')

            stats = generate_synthetic_data(
                amplicon=self.AMPLICON,
                guide=self.GUIDE,
                num_reads=50,
                edit_rate=0.5,
                error_rate=0.0,
                output_prefix=prefix,
                mode='prime-edit',
                peg_extension=self.PEG_EXTENSION,
                seed=42,
                quiet=True,
            )

            # Read the TSV to check edit details
            with open(f'{prefix}_edits.tsv') as f:
                lines = f.readlines()[1:]  # Skip header

            # Find a perfect prime edit
            for line in lines:
                parts = line.strip().split('\t')
                if parts[1] == 'prime_edit' and parts[4] == 'ACCTGGATCG':
                    # Should have RC of RT template as edited_seq
                    assert parts[5] == 'CGATCCAGAT'
                    break
            else:
                pytest.fail("No perfect prime edit found in output")

    def test_prime_edit_read_sequences_correct(self):
        """Prime edited reads should have correct sequence at edit site."""
        with tempfile.TemporaryDirectory() as tmpdir:
            prefix = os.path.join(tmpdir, 'test')

            generate_synthetic_data(
                amplicon=self.AMPLICON,
                guide=self.GUIDE,
                num_reads=100,
                edit_rate=1.0,  # All reads edited
                error_rate=0.0,
                output_prefix=prefix,
                mode='prime-edit',
                peg_extension=self.PEG_EXTENSION,
                perfect_edit_fraction=1.0,  # All perfect edits
                partial_edit_fraction=0.0,
                pe_indel_fraction=0.0,
                scaffold_incorporation_fraction=0.0,
                flap_indel_fraction=0.0,
                seed=42,
                quiet=True,
            )

            # Read FASTQ and check sequences
            with open(f'{prefix}.fastq') as f:
                lines = f.readlines()

            # Check first read has correct edit
            seq = lines[1].strip()  # Second line is sequence
            # Should have CGATCCAGAT at position 92-102
            assert seq[92:102] == 'CGATCCAGAT'
            # Should match CRISPResso expectation at 85-105
            assert seq[85:105] == 'CTGCAGCCGATCCAGATCTT'


# =============================================================================
# AlignedAllele Tests
# =============================================================================

def test_aligned_allele_dataclass():
    """Test AlignedAllele stores all required fields."""
    from syn_gen import AlignedAllele

    allele = AlignedAllele(
        aligned_sequence='CAGC--CTG',
        reference_sequence='CAGCACCTG',
        all_deletion_positions=[92, 93],
        deletion_coordinates=[(92, 94)],
        deletion_sizes=[2],
        all_insertion_positions=[],
        all_insertion_left_positions=[],
        insertion_coordinates=[],
        insertion_sizes=[],
        all_substitution_positions=[],
        substitution_values=[],
        n_deleted=2,
        n_inserted=0,
        n_mutated=0,
    )

    assert allele.aligned_sequence == 'CAGC--CTG'
    assert allele.n_deleted == 2
    assert allele.read_status == 'MODIFIED'


def test_aligned_allele_unmodified():
    """Test AlignedAllele read_status for unmodified reads."""
    from syn_gen import AlignedAllele

    allele = AlignedAllele(
        aligned_sequence='CAGCACCTG',
        reference_sequence='CAGCACCTG',
        all_deletion_positions=[],
        deletion_coordinates=[],
        deletion_sizes=[],
        all_insertion_positions=[],
        all_insertion_left_positions=[],
        insertion_coordinates=[],
        insertion_sizes=[],
        all_substitution_positions=[],
        substitution_values=[],
        n_deleted=0,
        n_inserted=0,
        n_mutated=0,
    )

    assert allele.read_status == 'UNMODIFIED'


# =============================================================================
# Alignment Function Tests
# =============================================================================

def test_create_aligned_deletion_simple():
    """Test aligned sequences for a simple deletion."""
    from syn_gen import create_aligned_deletion

    amplicon = 'CAGCACCTGGATCGC'
    position = 4  # Delete 'AC' at positions 4-5
    size = 2

    aligned_read, aligned_ref = create_aligned_deletion(amplicon, position, size)

    assert aligned_ref == amplicon
    assert aligned_read == 'CAGC--CTGGATCGC'
    assert len(aligned_read) == len(aligned_ref)


def test_create_aligned_deletion_at_start():
    """Test deletion at the start of sequence."""
    from syn_gen import create_aligned_deletion

    amplicon = 'ACGTACGT'
    position = 0
    size = 2

    aligned_read, aligned_ref = create_aligned_deletion(amplicon, position, size)

    assert aligned_ref == amplicon
    assert aligned_read == '--GTACGT'


def test_create_aligned_deletion_at_end():
    """Test deletion at the end of sequence."""
    from syn_gen import create_aligned_deletion

    amplicon = 'ACGTACGT'
    position = 6
    size = 2

    aligned_read, aligned_ref = create_aligned_deletion(amplicon, position, size)

    assert aligned_ref == amplicon
    assert aligned_read == 'ACGTAC--'


def test_create_aligned_insertion_simple():
    """Test aligned sequences for a simple insertion."""
    from syn_gen import create_aligned_insertion

    amplicon = 'CAGCACCTG'
    position = 4  # Insert 'GGG' at position 4
    inserted_seq = 'GGG'

    aligned_read, aligned_ref = create_aligned_insertion(amplicon, position, inserted_seq)

    assert aligned_read == 'CAGCGGGACCTG'
    assert aligned_ref == 'CAGC---ACCTG'
    assert len(aligned_read) == len(aligned_ref)


def test_create_aligned_insertion_at_start():
    """Test insertion at the start of sequence."""
    from syn_gen import create_aligned_insertion

    amplicon = 'ACGTACGT'
    position = 0
    inserted_seq = 'TTT'

    aligned_read, aligned_ref = create_aligned_insertion(amplicon, position, inserted_seq)

    assert aligned_read == 'TTTACGTACGT'
    assert aligned_ref == '---ACGTACGT'


def test_create_aligned_insertion_single_base():
    """Test single base insertion."""
    from syn_gen import create_aligned_insertion

    amplicon = 'CAGCACCTG'
    position = 4
    inserted_seq = 'A'

    aligned_read, aligned_ref = create_aligned_insertion(amplicon, position, inserted_seq)

    assert aligned_read == 'CAGCAACCTG'
    assert aligned_ref == 'CAGC-ACCTG'


def test_create_aligned_substitution_single():
    """Test aligned sequences for a single substitution."""
    from syn_gen import create_aligned_substitution

    amplicon = 'ACGTACGT'
    positions = [2]
    new_bases = ['T']

    aligned_read, aligned_ref = create_aligned_substitution(amplicon, positions, new_bases)

    assert aligned_read == 'ACTTACGT'
    assert aligned_ref == amplicon
    assert len(aligned_read) == len(aligned_ref)


def test_create_aligned_substitution_multiple():
    """Test aligned sequences for multiple substitutions."""
    from syn_gen import create_aligned_substitution

    amplicon = 'ACGTACGT'
    positions = [0, 4]
    new_bases = ['T', 'T']

    aligned_read, aligned_ref = create_aligned_substitution(amplicon, positions, new_bases)

    assert aligned_read == 'TCGTTCGT'
    assert aligned_ref == amplicon


def test_create_aligned_prime_edit_substitution():
    """Test prime edit with same-length replacement (substitution)."""
    from syn_gen import create_aligned_prime_edit

    amplicon = 'ACGTACGTACGT'
    position = 4
    original = 'ACG'
    edited = 'TTT'

    aligned_read, aligned_ref = create_aligned_prime_edit(amplicon, position, original, edited)

    # 'ACGT' + 'TTT' + 'TACGT' = 'ACGTTTTTACGT' (replacing ACG at pos 4-6 with TTT)
    assert aligned_read == 'ACGTTTTTACGT'
    assert aligned_ref == amplicon
    assert len(aligned_read) == len(aligned_ref)


def test_create_aligned_prime_edit_insertion():
    """Test prime edit with net insertion (edited longer than original)."""
    from syn_gen import create_aligned_prime_edit

    amplicon = 'ACGTACGTACGT'
    position = 4
    original = 'ACG'
    edited = 'TTTTT'  # 2 more bases

    aligned_read, aligned_ref = create_aligned_prime_edit(amplicon, position, original, edited)

    # 'ACGT' + 'TTTTT' + 'TACGT' = 'ACGTTTTTTTACGT' (14 chars)
    # Reference gets gaps: 'ACGT' + 'ACG--' + 'TACGT' = 'ACGTACG--TACGT' (14 chars)
    assert aligned_read == 'ACGTTTTTTTACGT'
    assert aligned_ref == 'ACGTACG--TACGT'
    assert len(aligned_read) == len(aligned_ref)


def test_create_aligned_prime_edit_deletion():
    """Test prime edit with net deletion (edited shorter than original)."""
    from syn_gen import create_aligned_prime_edit

    amplicon = 'ACGTACGTACGT'
    position = 4
    original = 'ACGT'
    edited = 'TT'  # 2 fewer bases

    aligned_read, aligned_ref = create_aligned_prime_edit(amplicon, position, original, edited)

    # 'ACGT' + 'TT--' + 'ACGT' = 'ACGTTT--ACGT' (12 chars with gaps)
    assert aligned_read == 'ACGTTT--ACGT'
    assert aligned_ref == amplicon
    assert len(aligned_read) == len(aligned_ref)


# =============================================================================
# edit_to_aligned_allele Tests
# =============================================================================

def test_edit_to_aligned_allele_deletion():
    """Test converting a deletion Edit to AlignedAllele."""
    from syn_gen import edit_to_aligned_allele, Edit, AlignedAllele

    amplicon = 'ACGTACGTACGT'
    edit = Edit(
        edit_type='deletion',
        position=4,
        size=2,
        original_seq='AC',
        edited_seq='',
    )

    allele = edit_to_aligned_allele(amplicon, edit, sequencing_errors=[])

    assert allele.aligned_sequence == 'ACGT--GTACGT'
    assert allele.reference_sequence == amplicon
    assert allele.all_deletion_positions == [4, 5]
    assert allele.deletion_coordinates == [(4, 6)]
    assert allele.deletion_sizes == [2]
    assert allele.n_deleted == 2
    assert allele.n_inserted == 0
    assert allele.read_status == 'MODIFIED'


def test_edit_to_aligned_allele_insertion():
    """Test converting an insertion Edit to AlignedAllele."""
    from syn_gen import edit_to_aligned_allele, Edit

    amplicon = 'ACGTACGT'
    edit = Edit(
        edit_type='insertion',
        position=4,
        size=3,
        original_seq='',
        edited_seq='GGG',
    )

    allele = edit_to_aligned_allele(amplicon, edit, sequencing_errors=[])

    assert allele.aligned_sequence == 'ACGTGGGACGT'
    assert allele.reference_sequence == 'ACGT---ACGT'
    assert allele.all_insertion_positions == [3, 4]
    assert allele.all_insertion_left_positions == [3]
    assert allele.insertion_coordinates == [(3, 4)]
    assert allele.insertion_sizes == [3]
    assert allele.n_inserted == 3


def test_edit_to_aligned_allele_none():
    """Test converting a 'none' Edit to AlignedAllele."""
    from syn_gen import edit_to_aligned_allele, Edit

    amplicon = 'ACGTACGT'
    edit = Edit(
        edit_type='none',
        position=0,
        size=0,
        original_seq='',
        edited_seq='',
    )

    allele = edit_to_aligned_allele(amplicon, edit, sequencing_errors=[])

    assert allele.aligned_sequence == amplicon
    assert allele.reference_sequence == amplicon
    assert allele.all_deletion_positions == []
    assert allele.all_insertion_positions == []
    assert allele.read_status == 'UNMODIFIED'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
