#!/usr/bin/env python3
"""Unit tests for syn-gen."""

import os
import tempfile
import pytest

from syn_gen import (
    FastqRead,
    Edit,
    EditedRead,
    VcfVariant,
    reverse_complement,
    generate_random_sequence,
    find_guide_in_amplicon,
    calculate_cut_site,
    apply_edit,
    add_sequencing_errors,
    generate_quality_string,
    aggregate_edits_to_variants,
    generate_synthetic_data,
    validate_inputs,
)


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
        result = add_sequencing_errors(seq, 0.0)
        assert result == seq

    def test_full_error_rate(self):
        seq = 'AAAA'
        result = add_sequencing_errors(seq, 1.0)
        # All bases should be changed
        assert 'A' not in result

    def test_preserves_length(self):
        seq = 'ACGT' * 100
        result = add_sequencing_errors(seq, 0.01)
        assert len(result) == len(seq)


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


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
