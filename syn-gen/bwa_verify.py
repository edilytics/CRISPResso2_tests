"""BWA alignment verification for syn-gen synthetic reads."""

from __future__ import annotations

import os
import re
import subprocess
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
            if op == 'S':
                # Soft-clip: doesn't affect reference position or MD tag
                pass
            elif op == 'M' or op == '=' or op == 'X':
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
            if op == 'S':
                # Soft-clip: advances read position but not reference
                read_pos += length
            elif op == 'M' or op == '=' or op == 'X':
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
            if op == 'S':
                # Soft-clip: advances read position but not reference
                read_pos += length
            elif op == 'M' or op == '=' or op == 'X':
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
    warnings: list[str] = field(default_factory=list)  # Soft-clipped seq errors
    expected_deletions: list[tuple[int, int]] = field(default_factory=list)
    expected_insertions: list[tuple[int, str]] = field(default_factory=list)
    expected_substitutions: list[tuple[int, str, str]] = field(default_factory=list)
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


def adjust_seq_error_position_to_ref(
    seq_error_pos: int,
    ground_truth: dict,
) -> int:
    """
    Translate a sequencing error position from edited-read coordinates
    to reference coordinates, accounting for indels.

    Args:
        seq_error_pos: Position in the edited read (0-indexed)
        ground_truth: Edit info from syn-gen's _edits.tsv

    Returns:
        Reference position (0-indexed), or -1 if inside an insertion
    """
    edit_type = ground_truth['edit_type']
    edit_pos = ground_truth.get('edit_position', 0)
    if isinstance(edit_pos, list):
        edit_pos = edit_pos[0]  # Use first position for multi-position edits
    edit_size = ground_truth.get('edit_size', 0)
    if isinstance(edit_size, list):
        edit_size = edit_size[0]

    if edit_type == 'deletion':
        # Deletion: the read is shorter than ref after edit_pos
        # Read positions >= edit_pos map to ref_pos + deletion_size
        if seq_error_pos >= edit_pos:
            return seq_error_pos + edit_size
        return seq_error_pos
    elif edit_type == 'insertion':
        # Insertion: positions in the inserted region have no ref coordinate
        # Positions after insertion shift right in read relative to ref
        if seq_error_pos < edit_pos:
            return seq_error_pos
        elif seq_error_pos >= edit_pos + edit_size:
            return seq_error_pos - edit_size
        else:
            return -1  # Inside insertion, no ref position
    else:
        # none, substitution, prime_edit (length-preserving)
        return seq_error_pos


def _ref_region_to_read_region(ref_start: int, ref_end: int, alignment: BWAAlignment) -> int:
    """
    Find the read start position for a reference region, including any insertions.

    For prime edits, the edited region in the read may include insertions that
    occur at the start of the reference region. This function finds the read
    position where the edited content starts.

    Args:
        ref_start: Start of reference region (0-indexed, inclusive)
        ref_end: End of reference region (0-indexed, exclusive)
        alignment: Parsed BWA alignment

    Returns:
        Read position where the region starts, or -1 if unmappable
    """
    cigar_ops = parse_cigar(alignment.cigar)

    current_ref = alignment.ref_start
    current_read = 0

    # Walk through CIGAR, track where we enter the region
    for op, length in cigar_ops:
        if op == 'S':
            current_read += length
        elif op in ('M', '=', 'X'):
            # Check if we've entered or passed the region
            if current_ref + length > ref_start:
                # We're at or past the start of the region
                if current_ref <= ref_start:
                    # The region starts within this M block
                    offset = ref_start - current_ref
                    return current_read + offset
                else:
                    # We've passed the start (shouldn't happen in normal flow)
                    return current_read
            current_ref += length
            current_read += length
        elif op == 'D':
            if current_ref + length > ref_start >= current_ref:
                # Region starts in a deleted area
                return -1
            current_ref += length
        elif op == 'I':
            # Insertion: if it's at the start of our region, include it
            if current_ref == ref_start:
                # The insertion is right at the region start - include it
                return current_read
            current_read += length

    return -1


def _ref_pos_to_read_pos(ref_pos: int, alignment: BWAAlignment) -> int:
    """
    Convert a reference position to read position, accounting for CIGAR ops.

    Args:
        ref_pos: Reference position (0-indexed)
        alignment: Parsed BWA alignment

    Returns:
        Read position (0-indexed), or -1 if position is outside aligned region
    """
    cigar_ops = parse_cigar(alignment.cigar)

    current_ref = alignment.ref_start
    current_read = 0

    # First, skip leading soft-clips
    for op, length in cigar_ops:
        if op == 'S':
            current_read += length
        else:
            break

    # Check if ref_pos is before alignment start
    if ref_pos < current_ref:
        return -1

    # Walk through CIGAR operations
    for op, length in cigar_ops:
        if op == 'S':
            # Skip soft-clips (already handled above for leading ones)
            current_read += length
        elif op in ('M', '=', 'X'):
            # Match/mismatch: both advance
            if current_ref <= ref_pos < current_ref + length:
                # Found it - ref_pos is within this M block
                offset = ref_pos - current_ref
                return current_read + offset
            current_ref += length
            current_read += length
        elif op == 'D':
            # Deletion: ref advances, read doesn't
            if current_ref <= ref_pos < current_ref + length:
                # ref_pos is within deleted region - no corresponding read position
                return -1
            current_ref += length
        elif op == 'I':
            # Insertion: read advances, ref doesn't
            current_read += length
        elif op == 'N':
            # Skipped region: ref advances
            current_ref += length

    # Position is after alignment
    return -1


def is_position_soft_clipped(ref_pos: int, alignment: BWAAlignment) -> bool:
    """
    Check if a reference position falls outside the aligned region of the read.

    Args:
        ref_pos: Reference position to check (0-indexed)
        alignment: Parsed BWA alignment

    Returns:
        True if position is outside aligned region (soft-clipped)
    """
    cigar_ops = parse_cigar(alignment.cigar)

    ref_start = alignment.ref_start
    ref_end = ref_start

    for op, length in cigar_ops:
        if op in ('M', 'D', '=', 'X'):
            ref_end += length
        # 'S' (soft-clip), 'I' (insertion), 'H' (hard-clip) don't advance ref

    return ref_pos < ref_start or ref_pos >= ref_end


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


def verify_read(
    read_name: str,
    ground_truth: dict,
    alignment: BWAAlignment,
) -> ReadVerification:
    """
    Verify a single read's BWA alignment against ground truth.

    Performs strict base-pair level verification:
    - Exact position matching for all edit types
    - Exact sequence matching for insertions/deletions
    - Original and new base verification for substitutions
    - Full sequencing error verification (soft-clipped as warnings)

    Args:
        read_name: Name of the read
        ground_truth: Edit info from syn-gen's _edits.tsv
        alignment: Parsed BWA alignment

    Returns:
        ReadVerification with pass/fail and any mismatches
    """
    mismatches = []
    warnings = []

    # Track seq error positions absorbed into deletions (boundary cases)
    absorbed_seq_error_positions = set()

    edit_type = ground_truth['edit_type']
    bwa_deletions = alignment.get_deletions()
    bwa_insertions = alignment.get_insertions()
    bwa_substitutions = alignment.get_substitutions()

    # Track expected values for debugging
    expected_deletions = []
    expected_insertions = []
    expected_substitutions = []

    if edit_type == 'none':
        # Should have no edits (only sequencing errors as substitutions)
        if bwa_deletions:
            mismatches.append(f"Expected no deletions, found {bwa_deletions}")
        if bwa_insertions:
            mismatches.append(f"Expected no insertions, found {bwa_insertions}")

    elif edit_type == 'deletion':
        expected_pos = ground_truth['edit_position']
        expected_size = ground_truth['edit_size']
        expected_seq = ground_truth.get('original_seq', '')
        seq_error_positions = ground_truth.get('seq_error_positions', [])

        expected_deletions.append((expected_pos, expected_size))

        if not bwa_deletions:
            mismatches.append(
                f"Expected deletion at pos={expected_pos}, size={expected_size}, "
                f"seq={expected_seq}; found none"
            )
        else:
            # Must find deletion at exact position with exact size and sequence
            found_match = False
            boundary_error_warning = None

            for bwa_pos, bwa_size, bwa_seq in bwa_deletions:
                if (bwa_pos == expected_pos and
                    bwa_size == expected_size and
                    bwa_seq == expected_seq):
                    found_match = True
                    break

                # Check for boundary seq error case:
                # If sizes match and positions differ by 1, and there's a seq error
                # at the boundary, BWA may have absorbed the error into the deletion
                if bwa_size == expected_size and abs(bwa_pos - expected_pos) == 1:
                    boundary_pos = min(bwa_pos, expected_pos)
                    if boundary_pos in seq_error_positions:
                        boundary_error_warning = (
                            f"Deletion at pos={expected_pos} shifted to {bwa_pos} "
                            f"due to seq error at boundary pos={boundary_pos}"
                        )
                        # Mark this seq error as absorbed
                        absorbed_seq_error_positions.add(boundary_pos)
                        found_match = True
                        break

            if not found_match:
                mismatches.append(
                    f"Deletion mismatch: expected pos={expected_pos}, "
                    f"size={expected_size}, seq={expected_seq}; found {bwa_deletions}"
                )
            elif boundary_error_warning:
                warnings.append(boundary_error_warning)

    elif edit_type == 'insertion':
        expected_pos = ground_truth['edit_position']
        expected_seq = ground_truth['edited_seq']

        expected_insertions.append((expected_pos, expected_seq))

        if not bwa_insertions:
            mismatches.append(
                f"Expected insertion at pos={expected_pos}, seq={expected_seq}; "
                f"found none"
            )
        else:
            # Must find insertion at exact position with exact sequence
            found_match = False
            for bwa_pos, bwa_seq in bwa_insertions:
                if bwa_pos == expected_pos and bwa_seq == expected_seq:
                    found_match = True
                    break

            if not found_match:
                mismatches.append(
                    f"Insertion mismatch: expected pos={expected_pos}, "
                    f"seq={expected_seq}; found {bwa_insertions}"
                )

    elif edit_type == 'substitution':
        positions = ground_truth['edit_position']
        original_bases = ground_truth.get('original_seq', [])
        new_bases = ground_truth['edited_seq']

        # Normalize to lists
        if not isinstance(positions, list):
            positions = [positions]
        if not isinstance(original_bases, list):
            original_bases = [original_bases]
        if not isinstance(new_bases, list):
            new_bases = [new_bases]

        for pos, orig_base, new_base in zip(positions, original_bases, new_bases):
            expected_substitutions.append((pos, orig_base, new_base))

            # Must find substitution with exact position, original base, and new base
            found = any(
                s[0] == pos and s[1] == orig_base and s[2] == new_base
                for s in bwa_substitutions
            )
            if not found:
                mismatches.append(
                    f"Missing substitution at pos {pos}: {orig_base} -> {new_base}"
                )

    elif edit_type == 'prime_edit':
        expected_pos = ground_truth['edit_position']
        original_seq = ground_truth['original_seq']
        edited_seq = ground_truth['edited_seq']

        len_diff = len(edited_seq) - len(original_seq)

        # For prime edits, BWA may represent the same edit differently
        # (e.g., as indel+subs instead of pure subs). Verify by extracting
        # the read region that covers the edit, accounting for any indels.
        #
        # Find the read region that corresponds to the original reference region
        # The edit covers ref positions [expected_pos : expected_pos + len(original_seq)]
        ref_start = expected_pos
        ref_end = expected_pos + len(original_seq)

        # Find where this region maps to in the read
        read_start = _ref_region_to_read_region(ref_start, ref_end, alignment)

        if read_start >= 0:
            # The edited region in the read should have len(edited_seq) bases
            # starting from read_start
            read_end = read_start + len(edited_seq)
            actual_seq = alignment.read_seq[read_start:read_end]

            if actual_seq != edited_seq:
                mismatches.append(
                    f"Prime edit sequence mismatch at pos {expected_pos}: "
                    f"expected '{edited_seq}', found '{actual_seq}'"
                )
        else:
            # Position is in soft-clipped or deleted region
            warnings.append(
                f"Prime edit at pos {expected_pos} cannot be mapped to read"
            )

        # Also verify the net length change is correct
        if len_diff > 0:
            expected_insertions.append((expected_pos, edited_seq))
        elif len_diff < 0:
            expected_deletions.append((expected_pos, abs(len_diff)))

    # Verify sequencing errors as substitutions
    seq_error_positions = ground_truth.get('seq_error_positions', [])
    seq_error_original = ground_truth.get('seq_error_original', [])
    seq_error_new = ground_truth.get('seq_error_new', [])

    for i, pos in enumerate(seq_error_positions):
        orig_base = seq_error_original[i]
        new_base = seq_error_new[i]

        # Skip seq errors that were absorbed into deletion boundary shifts
        if pos in absorbed_seq_error_positions:
            continue

        # Translate position from edited-read coordinates to reference coordinates
        ref_pos = adjust_seq_error_position_to_ref(pos, ground_truth)

        if ref_pos < 0:
            # Error is inside an insertion - can't verify against reference
            warnings.append(
                f"Seq error at read pos {pos} inside insertion: {orig_base} -> {new_base}"
            )
            continue

        found = any(
            s[0] == ref_pos and s[1] == orig_base and s[2] == new_base
            for s in bwa_substitutions
        )
        if not found:
            # Check if position is soft-clipped
            if is_position_soft_clipped(ref_pos, alignment):
                warnings.append(
                    f"Seq error at pos {pos} (ref: {ref_pos}) soft-clipped: "
                    f"{orig_base} -> {new_base}"
                )
            else:
                mismatches.append(
                    f"Missing seq error at pos {pos} (ref: {ref_pos}): "
                    f"{orig_base} -> {new_base}"
                )

    return ReadVerification(
        read_name=read_name,
        passed=len(mismatches) == 0,
        mismatches=mismatches,
        warnings=warnings,
        expected_deletions=expected_deletions,
        expected_insertions=expected_insertions,
        expected_substitutions=expected_substitutions,
        bwa_deletions=bwa_deletions,
        bwa_insertions=bwa_insertions,
        bwa_substitutions=bwa_substitutions,
    )


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
