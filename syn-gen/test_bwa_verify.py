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
