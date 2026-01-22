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
