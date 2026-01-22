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
