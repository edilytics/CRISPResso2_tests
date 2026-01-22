"""Unit tests for BWA verification module."""

import pytest


class TestParseCigar:
    """Tests for CIGAR string parsing."""

    def test_parse_simple_match(self):
        from bwa_verify import parse_cigar

        ops = parse_cigar('100M')
        assert ops == [('M', 100)]

    def test_parse_deletion(self):
        from bwa_verify import parse_cigar

        ops = parse_cigar('50M3D47M')
        assert ops == [('M', 50), ('D', 3), ('M', 47)]

    def test_parse_insertion(self):
        from bwa_verify import parse_cigar

        ops = parse_cigar('50M3I47M')
        assert ops == [('M', 50), ('I', 3), ('M', 47)]

    def test_parse_complex(self):
        from bwa_verify import parse_cigar

        ops = parse_cigar('10M2D5M1I30M')
        assert ops == [('M', 10), ('D', 2), ('M', 5), ('I', 1), ('M', 30)]


class TestParseMdTag:
    """Tests for MD tag parsing."""

    def test_parse_all_match(self):
        from bwa_verify import parse_md_tag

        # MD:Z:100 means 100 matching bases
        result = parse_md_tag('100')
        assert result == [('match', 100)]

    def test_parse_substitution(self):
        from bwa_verify import parse_md_tag

        # MD:Z:45A54 means 45 match, sub (ref was A), 54 match
        result = parse_md_tag('45A54')
        assert result == [('match', 45), ('sub', 'A'), ('match', 54)]

    def test_parse_deletion(self):
        from bwa_verify import parse_md_tag

        # MD:Z:45^CGT52 means 45 match, deleted CGT, 52 match
        result = parse_md_tag('45^CGT52')
        assert result == [('match', 45), ('del', 'CGT'), ('match', 52)]

    def test_parse_complex(self):
        from bwa_verify import parse_md_tag

        # Multiple substitutions and deletions
        result = parse_md_tag('10A5^GG20C10')
        assert result == [
            ('match', 10), ('sub', 'A'), ('match', 5),
            ('del', 'GG'), ('match', 20), ('sub', 'C'), ('match', 10)
        ]

    def test_parse_adjacent_substitutions(self):
        from bwa_verify import parse_md_tag

        # MD:Z:10A0C10 means sub at pos 11, sub at pos 12 (0 between means adjacent)
        result = parse_md_tag('10A0C10')
        assert result == [('match', 10), ('sub', 'A'), ('match', 0), ('sub', 'C'), ('match', 10)]


class TestBWAAlignment:
    """Tests for BWAAlignment dataclass and edit extraction."""

    def test_get_deletions_simple(self):
        from bwa_verify import BWAAlignment

        aln = BWAAlignment(
            read_name='read_0',
            ref_start=0,
            cigar='50M3D47M',
            md_tag='50^ACG47',
            read_seq='A' * 97,  # 100 - 3 deleted = 97
        )

        deletions = aln.get_deletions()
        assert deletions == [(50, 3, 'ACG')]  # (position, size, deleted_seq)

    def test_get_deletions_multiple(self):
        from bwa_verify import BWAAlignment

        aln = BWAAlignment(
            read_name='read_0',
            ref_start=0,
            cigar='20M2D30M1D47M',
            md_tag='20^AT30^G47',
            read_seq='A' * 97,
        )

        deletions = aln.get_deletions()
        assert deletions == [(20, 2, 'AT'), (52, 1, 'G')]

    def test_get_insertions_simple(self):
        from bwa_verify import BWAAlignment

        aln = BWAAlignment(
            read_name='read_0',
            ref_start=0,
            cigar='50M3I47M',
            md_tag='97',  # MD doesn't show insertions
            read_seq='A' * 50 + 'GGG' + 'A' * 47,
        )

        insertions = aln.get_insertions()
        assert insertions == [(50, 'GGG')]  # (position, inserted_seq)

    def test_get_substitutions_simple(self):
        from bwa_verify import BWAAlignment

        aln = BWAAlignment(
            read_name='read_0',
            ref_start=0,
            cigar='100M',
            md_tag='45A54',  # Substitution at position 45
            read_seq='A' * 45 + 'T' + 'A' * 54,
        )

        subs = aln.get_substitutions()
        # (position, ref_base, read_base)
        assert subs == [(45, 'A', 'T')]

    def test_get_substitutions_multiple(self):
        from bwa_verify import BWAAlignment

        aln = BWAAlignment(
            read_name='read_0',
            ref_start=0,
            cigar='100M',
            md_tag='10A20C67',
            read_seq='A' * 10 + 'T' + 'A' * 20 + 'G' + 'A' * 67,
        )

        subs = aln.get_substitutions()
        assert subs == [(10, 'A', 'T'), (31, 'C', 'G')]


class TestParseSam:
    """Tests for SAM file parsing."""

    def test_parse_single_alignment(self):
        from bwa_verify import parse_sam

        sam_content = """\
@HD\tVN:1.6\tSO:unsorted
@SQ\tSN:AMPLICON\tLN:200
read_0\t0\tAMPLICON\t1\t60\t100M\t*\t0\t0\tACGT\tIIII\tMD:Z:100
"""
        alignments = parse_sam(sam_content)

        assert len(alignments) == 1
        assert alignments['read_0'].read_name == 'read_0'
        assert alignments['read_0'].ref_start == 0  # SAM is 1-based, we convert to 0-based
        assert alignments['read_0'].cigar == '100M'
        assert alignments['read_0'].md_tag == '100'

    def test_parse_multiple_alignments(self):
        from bwa_verify import parse_sam

        sam_content = """\
@HD\tVN:1.6
@SQ\tSN:AMPLICON\tLN:200
read_0\t0\tAMPLICON\t1\t60\t100M\t*\t0\t0\tACGT\tIIII\tMD:Z:100
read_1\t0\tAMPLICON\t1\t60\t50M3D47M\t*\t0\t0\tACGT\tIIII\tMD:Z:50^ACG47
"""
        alignments = parse_sam(sam_content)

        assert len(alignments) == 2
        assert 'read_0' in alignments
        assert 'read_1' in alignments
        assert alignments['read_1'].cigar == '50M3D47M'

    def test_skip_unmapped(self):
        from bwa_verify import parse_sam

        sam_content = """\
@HD\tVN:1.6
@SQ\tSN:AMPLICON\tLN:200
read_0\t4\t*\t0\t0\t*\t*\t0\t0\tACGT\tIIII
read_1\t0\tAMPLICON\t1\t60\t100M\t*\t0\t0\tACGT\tIIII\tMD:Z:100
"""
        alignments = parse_sam(sam_content)

        assert len(alignments) == 1
        assert 'read_1' in alignments


class TestVerificationTypes:
    """Tests for verification result dataclasses."""

    def test_read_verification_passed(self):
        from bwa_verify import ReadVerification

        rv = ReadVerification(
            read_name='read_0',
            passed=True,
            mismatches=[],
        )

        assert rv.passed is True
        assert rv.mismatches == []

    def test_read_verification_failed(self):
        from bwa_verify import ReadVerification

        rv = ReadVerification(
            read_name='read_0',
            passed=False,
            mismatches=['Deletion size mismatch: expected 3, got 2'],
        )

        assert rv.passed is False
        assert len(rv.mismatches) == 1

    def test_verification_result_all_passed(self):
        from bwa_verify import VerificationResult, ReadVerification

        result = VerificationResult(
            total_reads=10,
            passed_reads=10,
            failed_reads=0,
            failures=[],
        )

        assert result.all_passed is True

    def test_verification_result_some_failed(self):
        from bwa_verify import VerificationResult, ReadVerification

        failure = ReadVerification(
            read_name='read_5',
            passed=False,
            mismatches=['Position mismatch'],
        )

        result = VerificationResult(
            total_reads=10,
            passed_reads=9,
            failed_reads=1,
            failures=[failure],
        )

        assert result.all_passed is False
        assert result.failed_reads == 1
