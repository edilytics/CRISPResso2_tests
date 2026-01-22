# syn-gen BWA End-to-End Testing Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Verify syn-gen's synthetic read generation at base-pair precision using BWA alignment.

**Architecture:** Generate synthetic reads with syn-gen, align with BWA, parse SAM output (CIGAR + MD tag), verify each read's detected edits match ground truth from `_edits.tsv`.

**Tech Stack:** Python 3, pytest, BWA (conda crispresso environment), manual SAM parsing

---

## Task 1: Create bwa_verify.py with SAM Parsing

**Files:**
- Create: `syn-gen/bwa_verify.py`
- Test: `syn-gen/test_bwa_verify.py`

**Step 1: Write failing test for CIGAR parsing**

Create `syn-gen/test_bwa_verify.py`:

```python
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
```

**Step 2: Run test to verify it fails**

Run: `cd syn-gen && python -m pytest test_bwa_verify.py::TestParseCigar -v`
Expected: FAIL with "No module named 'bwa_verify'"

**Step 3: Write minimal implementation**

Create `syn-gen/bwa_verify.py`:

```python
"""BWA alignment verification for syn-gen synthetic reads."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


def parse_cigar(cigar: str) -> list[tuple[str, int]]:
    """
    Parse CIGAR string into list of (operation, length) tuples.

    Args:
        cigar: CIGAR string like '50M3D47M'

    Returns:
        List of tuples like [('M', 50), ('D', 3), ('M', 47)]
    """
    pattern = re.compile(r'(\d+)([MIDNSHP=X])')
    return [(op, int(length)) for length, op in pattern.findall(cigar)]
```

**Step 4: Run test to verify it passes**

Run: `cd syn-gen && python -m pytest test_bwa_verify.py::TestParseCigar -v`
Expected: PASS

**Step 5: Commit**

```bash
git add syn-gen/bwa_verify.py syn-gen/test_bwa_verify.py
git commit -m "feat(syn-gen): add CIGAR parsing for BWA verification"
```

---

## Task 2: Add MD Tag Parsing

**Files:**
- Modify: `syn-gen/bwa_verify.py`
- Modify: `syn-gen/test_bwa_verify.py`

**Step 1: Write failing test for MD tag parsing**

Add to `syn-gen/test_bwa_verify.py`:

```python
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
```

**Step 2: Run test to verify it fails**

Run: `cd syn-gen && python -m pytest test_bwa_verify.py::TestParseMdTag -v`
Expected: FAIL with "cannot import name 'parse_md_tag'"

**Step 3: Write implementation**

Add to `syn-gen/bwa_verify.py`:

```python
def parse_md_tag(md: str) -> list[tuple[str, str | int]]:
    """
    Parse MD tag into list of operations.

    Args:
        md: MD tag string like '45A54' or '45^CGT52'

    Returns:
        List of tuples:
        - ('match', count) for matching bases
        - ('sub', ref_base) for substitution (ref base that was replaced)
        - ('del', ref_seq) for deletion (ref bases that were deleted)
    """
    result = []
    i = 0

    while i < len(md):
        # Check for deletion (^SEQ)
        if md[i] == '^':
            i += 1
            del_seq = ''
            while i < len(md) and md[i].isalpha():
                del_seq += md[i]
                i += 1
            result.append(('del', del_seq))
        # Check for number (match count)
        elif md[i].isdigit():
            num_str = ''
            while i < len(md) and md[i].isdigit():
                num_str += md[i]
                i += 1
            result.append(('match', int(num_str)))
        # Must be a substitution (single base)
        elif md[i].isalpha():
            result.append(('sub', md[i]))
            i += 1
        else:
            i += 1  # Skip unknown characters

    return result
```

**Step 4: Run test to verify it passes**

Run: `cd syn-gen && python -m pytest test_bwa_verify.py::TestParseMdTag -v`
Expected: PASS

**Step 5: Commit**

```bash
git add syn-gen/bwa_verify.py syn-gen/test_bwa_verify.py
git commit -m "feat(syn-gen): add MD tag parsing for substitution detection"
```

---

## Task 3: Add BWAAlignment Dataclass with Edit Extraction

**Files:**
- Modify: `syn-gen/bwa_verify.py`
- Modify: `syn-gen/test_bwa_verify.py`

**Step 1: Write failing test for BWAAlignment**

Add to `syn-gen/test_bwa_verify.py`:

```python
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
```

**Step 2: Run test to verify it fails**

Run: `cd syn-gen && python -m pytest test_bwa_verify.py::TestBWAAlignment -v`
Expected: FAIL with "cannot import name 'BWAAlignment'"

**Step 3: Write implementation**

Add to `syn-gen/bwa_verify.py`:

```python
@dataclass
class BWAAlignment:
    """Parsed BWA alignment with edit extraction methods."""

    read_name: str
    ref_start: int  # 0-indexed position on reference
    cigar: str
    md_tag: str
    read_seq: str

    def get_deletions(self) -> list[tuple[int, int, str]]:
        """
        Extract deletions from CIGAR and MD tag.

        Returns:
            List of (ref_position, size, deleted_sequence) tuples
        """
        deletions = []
        cigar_ops = parse_cigar(self.cigar)
        md_ops = parse_md_tag(self.md_tag)

        ref_pos = self.ref_start
        md_idx = 0
        md_offset = 0  # Position within current MD match block

        for op, length in cigar_ops:
            if op == 'M':
                # Advance through MD tag for matches
                remaining = length
                while remaining > 0 and md_idx < len(md_ops):
                    md_op, md_val = md_ops[md_idx]
                    if md_op == 'match':
                        avail = md_val - md_offset
                        if avail <= remaining:
                            remaining -= avail
                            md_offset = 0
                            md_idx += 1
                        else:
                            md_offset += remaining
                            remaining = 0
                    elif md_op == 'sub':
                        md_idx += 1
                        remaining -= 1
                    else:
                        md_idx += 1
                ref_pos += length
            elif op == 'D':
                # Find deletion in MD tag
                while md_idx < len(md_ops):
                    md_op, md_val = md_ops[md_idx]
                    if md_op == 'del':
                        deletions.append((ref_pos, length, md_val))
                        md_idx += 1
                        break
                    elif md_op == 'match' and md_val == 0:
                        md_idx += 1
                    else:
                        md_idx += 1
                ref_pos += length
            elif op == 'I':
                pass  # Insertions don't advance ref position

        return deletions

    def get_insertions(self) -> list[tuple[int, str]]:
        """
        Extract insertions from CIGAR and read sequence.

        Returns:
            List of (ref_position, inserted_sequence) tuples
        """
        insertions = []
        cigar_ops = parse_cigar(self.cigar)

        ref_pos = self.ref_start
        read_pos = 0

        for op, length in cigar_ops:
            if op == 'M':
                ref_pos += length
                read_pos += length
            elif op == 'D':
                ref_pos += length
            elif op == 'I':
                inserted_seq = self.read_seq[read_pos:read_pos + length]
                insertions.append((ref_pos, inserted_seq))
                read_pos += length

        return insertions

    def get_substitutions(self) -> list[tuple[int, str, str]]:
        """
        Extract substitutions from MD tag and read sequence.

        Returns:
            List of (ref_position, ref_base, read_base) tuples
        """
        substitutions = []
        cigar_ops = parse_cigar(self.cigar)
        md_ops = parse_md_tag(self.md_tag)

        ref_pos = self.ref_start
        read_pos = 0
        md_idx = 0

        for op, length in cigar_ops:
            if op == 'M':
                # Walk through this M block, tracking MD ops
                remaining = length
                while remaining > 0 and md_idx < len(md_ops):
                    md_op, md_val = md_ops[md_idx]
                    if md_op == 'match':
                        advance = min(remaining, md_val)
                        ref_pos += advance
                        read_pos += advance
                        remaining -= advance
                        if advance == md_val:
                            md_idx += 1
                        else:
                            # Partially consumed - update in place
                            md_ops[md_idx] = ('match', md_val - advance)
                    elif md_op == 'sub':
                        ref_base = md_val
                        read_base = self.read_seq[read_pos]
                        substitutions.append((ref_pos, ref_base, read_base))
                        ref_pos += 1
                        read_pos += 1
                        remaining -= 1
                        md_idx += 1
                    elif md_op == 'del':
                        md_idx += 1  # Skip deletions in MD during M block
            elif op == 'D':
                # Skip deletion in MD tag
                while md_idx < len(md_ops) and md_ops[md_idx][0] != 'del':
                    md_idx += 1
                if md_idx < len(md_ops):
                    md_idx += 1
                ref_pos += length
            elif op == 'I':
                read_pos += length

        return substitutions
```

**Step 4: Run test to verify it passes**

Run: `cd syn-gen && python -m pytest test_bwa_verify.py::TestBWAAlignment -v`
Expected: PASS

**Step 5: Commit**

```bash
git add syn-gen/bwa_verify.py syn-gen/test_bwa_verify.py
git commit -m "feat(syn-gen): add BWAAlignment dataclass with edit extraction"
```

---

## Task 4: Add SAM File Parsing

**Files:**
- Modify: `syn-gen/bwa_verify.py`
- Modify: `syn-gen/test_bwa_verify.py`

**Step 1: Write failing test for SAM parsing**

Add to `syn-gen/test_bwa_verify.py`:

```python
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
```

**Step 2: Run test to verify it fails**

Run: `cd syn-gen && python -m pytest test_bwa_verify.py::TestParseSam -v`
Expected: FAIL with "cannot import name 'parse_sam'"

**Step 3: Write implementation**

Add to `syn-gen/bwa_verify.py`:

```python
def parse_sam(sam_content: str) -> dict[str, BWAAlignment]:
    """
    Parse SAM content into dict of BWAAlignment objects.

    Args:
        sam_content: SAM file content as string

    Returns:
        Dict mapping read_name -> BWAAlignment
    """
    alignments = {}

    for line in sam_content.strip().split('\n'):
        if line.startswith('@'):
            continue  # Skip header lines

        fields = line.split('\t')
        if len(fields) < 11:
            continue

        read_name = fields[0]
        flag = int(fields[1])
        ref_name = fields[2]
        pos = int(fields[3])  # 1-based in SAM
        cigar = fields[5]
        seq = fields[9]

        # Skip unmapped reads (flag & 4)
        if flag & 4 or ref_name == '*' or cigar == '*':
            continue

        # Extract MD tag from optional fields
        md_tag = ''
        for field in fields[11:]:
            if field.startswith('MD:Z:'):
                md_tag = field[5:]
                break

        alignments[read_name] = BWAAlignment(
            read_name=read_name,
            ref_start=pos - 1,  # Convert to 0-based
            cigar=cigar,
            md_tag=md_tag,
            read_seq=seq,
        )

    return alignments
```

**Step 4: Run test to verify it passes**

Run: `cd syn-gen && python -m pytest test_bwa_verify.py::TestParseSam -v`
Expected: PASS

**Step 5: Commit**

```bash
git add syn-gen/bwa_verify.py syn-gen/test_bwa_verify.py
git commit -m "feat(syn-gen): add SAM file parsing"
```

---

## Task 5: Add BWA Runner and Verification Result Types

**Files:**
- Modify: `syn-gen/bwa_verify.py`
- Modify: `syn-gen/test_bwa_verify.py`

**Step 1: Write failing test for verification types**

Add to `syn-gen/test_bwa_verify.py`:

```python
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
```

**Step 2: Run test to verify it fails**

Run: `cd syn-gen && python -m pytest test_bwa_verify.py::TestVerificationTypes -v`
Expected: FAIL with "cannot import name 'ReadVerification'"

**Step 3: Write implementation**

Add to `syn-gen/bwa_verify.py`:

```python
@dataclass
class ReadVerification:
    """Verification result for a single read."""

    read_name: str
    passed: bool
    mismatches: list[str] = field(default_factory=list)
    expected_deletions: list[tuple[int, int]] = field(default_factory=list)
    expected_insertions: list[tuple[int, str]] = field(default_factory=list)
    expected_substitutions: list[tuple[int, str]] = field(default_factory=list)
    bwa_deletions: list[tuple[int, int, str]] = field(default_factory=list)
    bwa_insertions: list[tuple[int, str]] = field(default_factory=list)
    bwa_substitutions: list[tuple[int, str, str]] = field(default_factory=list)


@dataclass
class VerificationResult:
    """Overall verification result for a test run."""

    total_reads: int
    passed_reads: int
    failed_reads: int
    failures: list[ReadVerification]

    @property
    def all_passed(self) -> bool:
        return self.failed_reads == 0
```

**Step 4: Run test to verify it passes**

Run: `cd syn-gen && python -m pytest test_bwa_verify.py::TestVerificationTypes -v`
Expected: PASS

**Step 5: Commit**

```bash
git add syn-gen/bwa_verify.py syn-gen/test_bwa_verify.py
git commit -m "feat(syn-gen): add verification result dataclasses"
```

---

## Task 6: Add Ground Truth Parser

**Files:**
- Modify: `syn-gen/bwa_verify.py`
- Modify: `syn-gen/test_bwa_verify.py`

**Step 1: Write failing test for edits TSV parsing**

Add to `syn-gen/test_bwa_verify.py`:

```python
class TestParseEditsTsv:
    """Tests for parsing syn-gen's _edits.tsv ground truth."""

    def test_parse_deletion(self):
        from bwa_verify import parse_edits_tsv

        tsv_content = """\
read_name\tedit_type\tedit_position\tedit_size\toriginal_seq\tedited_seq\tseq_error_count\tseq_error_positions\tseq_error_original\tseq_error_new
read_0\tdeletion\t50\t3\tACG\t\t0\t\t\t
"""
        edits = parse_edits_tsv(tsv_content)

        assert len(edits) == 1
        assert edits['read_0']['edit_type'] == 'deletion'
        assert edits['read_0']['edit_position'] == 50
        assert edits['read_0']['edit_size'] == 3

    def test_parse_insertion(self):
        from bwa_verify import parse_edits_tsv

        tsv_content = """\
read_name\tedit_type\tedit_position\tedit_size\toriginal_seq\tedited_seq\tseq_error_count\tseq_error_positions\tseq_error_original\tseq_error_new
read_0\tinsertion\t50\t3\t\tGGG\t0\t\t\t
"""
        edits = parse_edits_tsv(tsv_content)

        assert edits['read_0']['edit_type'] == 'insertion'
        assert edits['read_0']['edited_seq'] == 'GGG'

    def test_parse_substitution_multi(self):
        from bwa_verify import parse_edits_tsv

        tsv_content = """\
read_name\tedit_type\tedit_position\tedit_size\toriginal_seq\tedited_seq\tseq_error_count\tseq_error_positions\tseq_error_original\tseq_error_new
read_0\tsubstitution\t10,15,20\t1,1,1\tC,C,C\tT,T,T\t0\t\t\t
"""
        edits = parse_edits_tsv(tsv_content)

        assert edits['read_0']['edit_type'] == 'substitution'
        assert edits['read_0']['edit_position'] == [10, 15, 20]
        assert edits['read_0']['edited_seq'] == ['T', 'T', 'T']

    def test_parse_sequencing_errors(self):
        from bwa_verify import parse_edits_tsv

        tsv_content = """\
read_name\tedit_type\tedit_position\tedit_size\toriginal_seq\tedited_seq\tseq_error_count\tseq_error_positions\tseq_error_original\tseq_error_new
read_0\tnone\t0\t0\t\t\t2\t30,60\tA,C\tT,G
"""
        edits = parse_edits_tsv(tsv_content)

        assert edits['read_0']['seq_error_count'] == 2
        assert edits['read_0']['seq_error_positions'] == [30, 60]
        assert edits['read_0']['seq_error_new'] == ['T', 'G']
```

**Step 2: Run test to verify it fails**

Run: `cd syn-gen && python -m pytest test_bwa_verify.py::TestParseEditsTsv -v`
Expected: FAIL with "cannot import name 'parse_edits_tsv'"

**Step 3: Write implementation**

Add to `syn-gen/bwa_verify.py`:

```python
def parse_edits_tsv(tsv_content: str) -> dict[str, dict]:
    """
    Parse syn-gen's _edits.tsv ground truth file.

    Args:
        tsv_content: TSV file content as string

    Returns:
        Dict mapping read_name -> edit info dict
    """
    edits = {}
    lines = tsv_content.strip().split('\n')

    if len(lines) < 2:
        return edits

    header = lines[0].split('\t')

    for line in lines[1:]:
        values = line.split('\t')
        row = dict(zip(header, values))

        read_name = row['read_name']

        # Parse position (may be comma-separated for multi-position edits)
        pos_str = row['edit_position']
        if ',' in pos_str:
            row['edit_position'] = [int(p) for p in pos_str.split(',')]
        else:
            row['edit_position'] = int(pos_str) if pos_str else 0

        # Parse size
        size_str = row['edit_size']
        if ',' in size_str:
            row['edit_size'] = [int(s) for s in size_str.split(',')]
        else:
            row['edit_size'] = int(size_str) if size_str else 0

        # Parse original_seq and edited_seq (may be comma-separated)
        orig_str = row.get('original_seq', '')
        if ',' in orig_str:
            row['original_seq'] = orig_str.split(',')

        edit_str = row.get('edited_seq', '')
        if ',' in edit_str:
            row['edited_seq'] = edit_str.split(',')

        # Parse sequencing errors
        row['seq_error_count'] = int(row.get('seq_error_count', 0))

        err_pos_str = row.get('seq_error_positions', '')
        if err_pos_str:
            row['seq_error_positions'] = [int(p) for p in err_pos_str.split(',')]
        else:
            row['seq_error_positions'] = []

        err_orig_str = row.get('seq_error_original', '')
        if err_orig_str:
            row['seq_error_original'] = err_orig_str.split(',')
        else:
            row['seq_error_original'] = []

        err_new_str = row.get('seq_error_new', '')
        if err_new_str:
            row['seq_error_new'] = err_new_str.split(',')
        else:
            row['seq_error_new'] = []

        edits[read_name] = row

    return edits
```

**Step 4: Run test to verify it passes**

Run: `cd syn-gen && python -m pytest test_bwa_verify.py::TestParseEditsTsv -v`
Expected: PASS

**Step 5: Commit**

```bash
git add syn-gen/bwa_verify.py syn-gen/test_bwa_verify.py
git commit -m "feat(syn-gen): add ground truth TSV parser"
```

---

## Task 7: Add Read Verification Logic

**Files:**
- Modify: `syn-gen/bwa_verify.py`
- Modify: `syn-gen/test_bwa_verify.py`

**Step 1: Write failing test for single read verification**

Add to `syn-gen/test_bwa_verify.py`:

```python
class TestVerifyRead:
    """Tests for single read verification."""

    def test_verify_deletion_match(self):
        from bwa_verify import verify_read, BWAAlignment

        ground_truth = {
            'edit_type': 'deletion',
            'edit_position': 50,
            'edit_size': 3,
            'original_seq': 'ACG',
            'edited_seq': '',
            'seq_error_count': 0,
            'seq_error_positions': [],
            'seq_error_new': [],
        }

        alignment = BWAAlignment(
            read_name='read_0',
            ref_start=0,
            cigar='50M3D47M',
            md_tag='50^ACG47',
            read_seq='A' * 97,
        )

        result = verify_read('read_0', ground_truth, alignment)

        assert result.passed is True
        assert result.mismatches == []

    def test_verify_deletion_size_mismatch(self):
        from bwa_verify import verify_read, BWAAlignment

        ground_truth = {
            'edit_type': 'deletion',
            'edit_position': 50,
            'edit_size': 5,  # Expected 5
            'original_seq': 'ACGTA',
            'edited_seq': '',
            'seq_error_count': 0,
            'seq_error_positions': [],
            'seq_error_new': [],
        }

        alignment = BWAAlignment(
            read_name='read_0',
            ref_start=0,
            cigar='50M3D47M',  # BWA found 3
            md_tag='50^ACG47',
            read_seq='A' * 97,
        )

        result = verify_read('read_0', ground_truth, alignment)

        assert result.passed is False
        assert any('size' in m.lower() for m in result.mismatches)

    def test_verify_insertion_match(self):
        from bwa_verify import verify_read, BWAAlignment

        ground_truth = {
            'edit_type': 'insertion',
            'edit_position': 50,
            'edit_size': 3,
            'original_seq': '',
            'edited_seq': 'GGG',
            'seq_error_count': 0,
            'seq_error_positions': [],
            'seq_error_new': [],
        }

        alignment = BWAAlignment(
            read_name='read_0',
            ref_start=0,
            cigar='50M3I47M',
            md_tag='97',
            read_seq='A' * 50 + 'GGG' + 'A' * 47,
        )

        result = verify_read('read_0', ground_truth, alignment)

        assert result.passed is True

    def test_verify_no_edit(self):
        from bwa_verify import verify_read, BWAAlignment

        ground_truth = {
            'edit_type': 'none',
            'edit_position': 0,
            'edit_size': 0,
            'original_seq': '',
            'edited_seq': '',
            'seq_error_count': 0,
            'seq_error_positions': [],
            'seq_error_new': [],
        }

        alignment = BWAAlignment(
            read_name='read_0',
            ref_start=0,
            cigar='100M',
            md_tag='100',
            read_seq='A' * 100,
        )

        result = verify_read('read_0', ground_truth, alignment)

        assert result.passed is True
```

**Step 2: Run test to verify it fails**

Run: `cd syn-gen && python -m pytest test_bwa_verify.py::TestVerifyRead -v`
Expected: FAIL with "cannot import name 'verify_read'"

**Step 3: Write implementation**

Add to `syn-gen/bwa_verify.py`:

```python
def verify_read(
    read_name: str,
    ground_truth: dict,
    alignment: BWAAlignment,
) -> ReadVerification:
    """
    Verify a single read's BWA alignment against ground truth.

    Args:
        read_name: Name of the read
        ground_truth: Edit info from syn-gen's _edits.tsv
        alignment: Parsed BWA alignment

    Returns:
        ReadVerification with pass/fail and any mismatches
    """
    mismatches = []

    edit_type = ground_truth['edit_type']
    bwa_deletions = alignment.get_deletions()
    bwa_insertions = alignment.get_insertions()
    bwa_substitutions = alignment.get_substitutions()

    # Collect expected sequencing errors as substitutions
    expected_seq_errors = []
    for i, pos in enumerate(ground_truth.get('seq_error_positions', [])):
        new_base = ground_truth['seq_error_new'][i]
        expected_seq_errors.append((pos, new_base))

    if edit_type == 'none':
        # Should have no edits (only sequencing errors as substitutions)
        if bwa_deletions:
            mismatches.append(f"Expected no deletions, found {len(bwa_deletions)}")
        if bwa_insertions:
            mismatches.append(f"Expected no insertions, found {len(bwa_insertions)}")

        # Check sequencing errors match substitutions
        if expected_seq_errors:
            for pos, new_base in expected_seq_errors:
                found = any(s[0] == pos and s[2] == new_base for s in bwa_substitutions)
                if not found:
                    mismatches.append(f"Missing sequencing error at pos {pos}")

    elif edit_type == 'deletion':
        expected_pos = ground_truth['edit_position']
        expected_size = ground_truth['edit_size']

        if not bwa_deletions:
            mismatches.append(f"Expected deletion at {expected_pos}, found none")
        else:
            # Find matching deletion
            found = False
            for pos, size, seq in bwa_deletions:
                if pos == expected_pos and size == expected_size:
                    found = True
                    break

            if not found:
                bwa_info = [(pos, size) for pos, size, _ in bwa_deletions]
                mismatches.append(
                    f"Deletion mismatch: expected pos={expected_pos} size={expected_size}, "
                    f"found {bwa_info}"
                )

    elif edit_type == 'insertion':
        expected_pos = ground_truth['edit_position']
        expected_seq = ground_truth['edited_seq']

        if not bwa_insertions:
            mismatches.append(f"Expected insertion at {expected_pos}, found none")
        else:
            found = False
            for pos, seq in bwa_insertions:
                if pos == expected_pos and seq == expected_seq:
                    found = True
                    break

            if not found:
                mismatches.append(
                    f"Insertion mismatch: expected pos={expected_pos} seq={expected_seq}, "
                    f"found {bwa_insertions}"
                )

    elif edit_type == 'substitution':
        positions = ground_truth['edit_position']
        new_bases = ground_truth['edited_seq']

        if not isinstance(positions, list):
            positions = [positions]
            new_bases = [new_bases]

        for pos, new_base in zip(positions, new_bases):
            found = any(s[0] == pos and s[2] == new_base for s in bwa_substitutions)
            if not found:
                mismatches.append(f"Missing substitution at pos {pos} -> {new_base}")

    elif edit_type == 'prime_edit':
        # Prime edits may result in insertions, deletions, or substitutions
        # depending on length difference. Verify based on what's expected.
        original = ground_truth['original_seq']
        edited = ground_truth['edited_seq']
        expected_pos = ground_truth['edit_position']

        len_diff = len(edited) - len(original)

        if len_diff > 0:
            # Net insertion expected
            if not bwa_insertions:
                mismatches.append(f"Expected prime edit insertion, found none")
        elif len_diff < 0:
            # Net deletion expected
            if not bwa_deletions:
                mismatches.append(f"Expected prime edit deletion, found none")
        # Substitutions within the edit region are also expected

    # Verify sequencing errors appear as substitutions
    for pos, new_base in expected_seq_errors:
        found = any(s[0] == pos and s[2] == new_base for s in bwa_substitutions)
        if not found:
            mismatches.append(f"Missing sequencing error substitution at pos {pos}")

    return ReadVerification(
        read_name=read_name,
        passed=len(mismatches) == 0,
        mismatches=mismatches,
        bwa_deletions=bwa_deletions,
        bwa_insertions=bwa_insertions,
        bwa_substitutions=bwa_substitutions,
    )
```

**Step 4: Run test to verify it passes**

Run: `cd syn-gen && python -m pytest test_bwa_verify.py::TestVerifyRead -v`
Expected: PASS

**Step 5: Commit**

```bash
git add syn-gen/bwa_verify.py syn-gen/test_bwa_verify.py
git commit -m "feat(syn-gen): add single read verification logic"
```

---

## Task 8: Add Main Verification Function with BWA Runner

**Files:**
- Modify: `syn-gen/bwa_verify.py`

**Step 1: Write the BWA runner and main verification function**

Add to `syn-gen/bwa_verify.py`:

```python
import os
import subprocess
import tempfile


def run_bwa(
    amplicon: str,
    amplicon_name: str,
    fastq_path: str,
    temp_dir: str,
) -> str:
    """
    Run BWA alignment and return SAM content.

    Args:
        amplicon: Reference amplicon sequence
        amplicon_name: Name for the reference
        fastq_path: Path to FASTQ file
        temp_dir: Temporary directory for index files

    Returns:
        SAM file content as string
    """
    # Write reference FASTA
    ref_path = os.path.join(temp_dir, 'reference.fa')
    with open(ref_path, 'w') as f:
        f.write(f'>{amplicon_name}\n{amplicon}\n')

    # Index reference
    subprocess.run(
        ['bwa', 'index', ref_path],
        capture_output=True,
        check=True,
    )

    # Run alignment
    result = subprocess.run(
        ['bwa', 'mem', ref_path, fastq_path],
        capture_output=True,
        text=True,
        check=True,
    )

    return result.stdout


def verify_reads_with_bwa(
    amplicon: str,
    fastq_path: str,
    edits_tsv_path: str,
    temp_dir: str,
    amplicon_name: str = 'AMPLICON',
) -> VerificationResult:
    """
    Align reads with BWA and verify each against ground truth.

    Args:
        amplicon: Reference amplicon sequence
        fastq_path: Path to syn-gen FASTQ output
        edits_tsv_path: Path to syn-gen _edits.tsv ground truth
        temp_dir: Temporary directory for BWA files
        amplicon_name: Name for reference sequence

    Returns:
        VerificationResult with pass/fail and detailed discrepancies
    """
    # Read ground truth
    with open(edits_tsv_path) as f:
        ground_truth = parse_edits_tsv(f.read())

    # Run BWA alignment
    sam_content = run_bwa(amplicon, amplicon_name, fastq_path, temp_dir)

    # Parse alignments
    alignments = parse_sam(sam_content)

    # Verify each read
    passed = 0
    failed = 0
    failures = []

    for read_name, edit_info in ground_truth.items():
        if read_name not in alignments:
            failures.append(ReadVerification(
                read_name=read_name,
                passed=False,
                mismatches=[f"Read not found in BWA output (unmapped?)"],
            ))
            failed += 1
            continue

        result = verify_read(read_name, edit_info, alignments[read_name])

        if result.passed:
            passed += 1
        else:
            failed += 1
            failures.append(result)

    return VerificationResult(
        total_reads=len(ground_truth),
        passed_reads=passed,
        failed_reads=failed,
        failures=failures,
    )
```

**Step 2: Commit**

```bash
git add syn-gen/bwa_verify.py
git commit -m "feat(syn-gen): add BWA runner and main verification function"
```

---

## Task 9: Create E2E Test File

**Files:**
- Create: `syn-gen/test_bwa_e2e.py`

**Step 1: Write the e2e test file**

Create `syn-gen/test_bwa_e2e.py`:

```python
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
    result = subprocess.run(["which", "bwa"], capture_output=True)
    if result.returncode != 0:
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
```

**Step 2: Commit**

```bash
git add syn-gen/test_bwa_e2e.py
git commit -m "test(syn-gen): add BWA-based e2e test suite"
```

---

## Task 10: Run Full Test Suite and Fix Issues

**Step 1: Run all unit tests**

Run: `cd syn-gen && python -m pytest test_bwa_verify.py -v`
Expected: All tests pass

**Step 2: Run e2e tests**

Run: `cd syn-gen && python -m pytest test_bwa_e2e.py -v`
Expected: All tests pass (or identify specific failures to fix)

**Step 3: Fix any issues found**

If tests fail, debug by:
1. Adding print statements to show expected vs actual values
2. Checking CIGAR/MD parsing edge cases
3. Verifying position calculations (0-indexed vs 1-indexed)

**Step 4: Final commit**

```bash
git add -A
git commit -m "test(syn-gen): complete BWA e2e verification implementation"
```

---

## Summary

| Task | Description | Files |
|------|-------------|-------|
| 1 | CIGAR parsing | `bwa_verify.py`, `test_bwa_verify.py` |
| 2 | MD tag parsing | `bwa_verify.py`, `test_bwa_verify.py` |
| 3 | BWAAlignment with edit extraction | `bwa_verify.py`, `test_bwa_verify.py` |
| 4 | SAM file parsing | `bwa_verify.py`, `test_bwa_verify.py` |
| 5 | Verification result types | `bwa_verify.py`, `test_bwa_verify.py` |
| 6 | Ground truth TSV parser | `bwa_verify.py`, `test_bwa_verify.py` |
| 7 | Single read verification | `bwa_verify.py`, `test_bwa_verify.py` |
| 8 | BWA runner + main function | `bwa_verify.py` |
| 9 | E2E test suite | `test_bwa_e2e.py` |
| 10 | Run tests and fix issues | All files |
