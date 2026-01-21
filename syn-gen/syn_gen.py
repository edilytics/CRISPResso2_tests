#!/usr/bin/env python3
"""
syn-gen: Synthetic CRISPR editing data generator.

Generates synthetic FASTQ files with realistic edits for testing CRISPResso2.
Supports NHEJ (deletions/insertions), base editing (CBE/ABE), and prime editing.
"""

from __future__ import annotations

import argparse
import gzip
import math
import random
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class FastqRead:
    """A FASTQ read with 4-line format support."""
    name: str
    seq: str
    qual: str

    def __str__(self) -> str:
        return f'@{self.name}\n{self.seq}\n+\n{self.qual}\n'


@dataclass
class Edit:
    """Represents a single edit event (NHEJ, base editing, or prime editing)."""
    edit_type: Literal['deletion', 'insertion', 'substitution', 'prime_edit', 'none']
    position: int | list[int]  # Position(s) in amplicon (0-indexed). List for multi-base edits.
    size: int | list[int]  # Size of edit(s). Always 1 for substitutions.
    original_seq: str | list[str]  # Original sequence(s) at edit site
    edited_seq: str | list[str]  # Resulting sequence(s)


@dataclass
class SequencingError:
    """A sequencing error introduced during simulation."""
    position: int  # 0-indexed position in the read
    original_base: str  # Base before error
    error_base: str  # Base after error


@dataclass
class EditedRead:
    """A read with its associated edit information."""
    read: FastqRead
    edit: Edit
    sequencing_errors: list[SequencingError] = None  # Optional list of sequencing errors

    def __post_init__(self):
        if self.sequencing_errors is None:
            self.sequencing_errors = []


@dataclass
class VcfVariant:
    """A VCF-format variant call."""
    chrom: str  # Amplicon name
    pos: int  # 1-indexed position
    ref: str  # Reference allele
    alt: str  # Alternate allele
    af: float  # Allele frequency


# =============================================================================
# Sequence Utilities
# =============================================================================

COMPLEMENT = str.maketrans('ACGT', 'TGCA')


def reverse_complement(seq: str) -> str:
    """Return reverse complement of DNA sequence."""
    return seq.upper().translate(COMPLEMENT)[::-1]


def generate_random_sequence(length: int) -> str:
    """Generate a random DNA sequence."""
    return ''.join(random.choices('ACGT', k=length))


# =============================================================================
# Guide and Cut Site Functions
# =============================================================================

def find_guide_in_amplicon(amplicon: str, guide: str) -> tuple[int, int, bool]:
    """
    Find guide sequence in amplicon.

    Args:
        amplicon: Reference amplicon sequence
        guide: Guide/sgRNA sequence (without PAM)

    Returns:
        Tuple of (start, end, is_reverse_complement)

    Raises:
        ValueError: If guide not found in amplicon
    """
    amplicon_upper = amplicon.upper()
    guide_upper = guide.upper()

    # Check forward strand
    forward_idx = amplicon_upper.find(guide_upper)
    if forward_idx != -1:
        return (forward_idx, forward_idx + len(guide), False)

    # Check reverse complement
    guide_rc = reverse_complement(guide_upper)
    rc_idx = amplicon_upper.find(guide_rc)
    if rc_idx != -1:
        return (rc_idx, rc_idx + len(guide), True)

    # Not found
    raise ValueError(
        f"Guide sequence not found in amplicon.\n"
        f"Guide: {guide}\n"
        f"Guide RC: {guide_rc}\n"
        f"Amplicon: {amplicon[:50]}...{amplicon[-50:] if len(amplicon) > 100 else ''}\n"
        f"Hint: Ensure guide is provided without PAM sequence."
    )


def calculate_cut_site(
    guide_start: int,
    guide_end: int,
    is_rc: bool,
    cleavage_offset: int = -3
) -> int:
    """
    Calculate cut site position in amplicon coordinates.

    For Cas9, the cut site is 3bp upstream of the PAM-proximal end of the guide.
    - Forward guide: cut is at guide_end + cleavage_offset
    - Reverse complement: cut is at guide_start - cleavage_offset - 1

    Args:
        guide_start: Start position of guide in amplicon (0-indexed)
        guide_end: End position of guide in amplicon (0-indexed, exclusive)
        is_rc: Whether guide is on reverse complement strand
        cleavage_offset: Offset from 3' end of guide (default -3 for Cas9)

    Returns:
        Cut site position (0-indexed)
    """
    if is_rc:
        # For RC guide, PAM-proximal end is at guide_start
        return guide_start - cleavage_offset - 1
    else:
        # For forward guide, PAM-proximal end is at guide_end
        return guide_end + cleavage_offset


# =============================================================================
# Edit Generation
# =============================================================================

def sample_deletion_size(max_size: int = 50) -> int:
    """
    Sample deletion size from realistic distribution.

    Uses geometric distribution with p=0.2 (mean ~5, mode 1).
    """
    # Geometric distribution: mode at 1, long tail
    size = 1
    while random.random() > 0.2 and size < max_size:
        size += 1
    return size


def sample_insertion_size(max_size: int = 10) -> int:
    """
    Sample insertion size from realistic distribution.

    Insertions are typically small (1-3bp).
    """
    size = 1
    while random.random() > 0.5 and size < max_size:
        size += 1
    return size


def generate_edit(
    cut_site: int,
    amplicon: str,
    deletion_weight: float = 0.75
) -> Edit:
    """
    Generate a realistic NHEJ edit at the cut site.

    Args:
        cut_site: Position of cut site in amplicon
        amplicon: Reference amplicon sequence
        deletion_weight: Probability of deletion vs insertion (default 0.75)

    Returns:
        Edit object describing the edit
    """
    # Add position jitter around cut site
    jitter = random.randint(-2, 2)
    position = max(0, min(cut_site + jitter, len(amplicon) - 1))

    if random.random() < deletion_weight:
        # Generate deletion
        size = sample_deletion_size()
        end_pos = min(position + size, len(amplicon))
        actual_size = end_pos - position

        return Edit(
            edit_type='deletion',
            position=position,
            size=actual_size,
            original_seq=amplicon[position:end_pos],
            edited_seq=''
        )
    else:
        # Generate insertion
        size = sample_insertion_size()
        inserted_seq = generate_random_sequence(size)

        return Edit(
            edit_type='insertion',
            position=position,
            size=size,
            original_seq='',
            edited_seq=inserted_seq
        )


def apply_edit(amplicon: str, edit: Edit) -> str:
    """
    Apply an edit to the amplicon sequence.

    Args:
        amplicon: Reference amplicon sequence
        edit: Edit to apply

    Returns:
        Edited sequence
    """
    if edit.edit_type == 'none':
        return amplicon
    elif edit.edit_type == 'deletion':
        return amplicon[:edit.position] + amplicon[edit.position + edit.size:]
    elif edit.edit_type == 'insertion':
        return amplicon[:edit.position] + edit.edited_seq + amplicon[edit.position:]
    else:
        raise ValueError(f"Unknown edit type: {edit.edit_type}")


# =============================================================================
# Base Editing Functions
# =============================================================================

def gaussian_probability(position: int, center: int, sigma: float) -> float:
    """
    Calculate Gaussian probability for a position relative to center.

    Args:
        position: Position to evaluate (1-indexed from PAM-distal end)
        center: Center of activity window
        sigma: Standard deviation

    Returns:
        Probability value (0-1, normalized to peak at 1.0)
    """
    return math.exp(-0.5 * ((position - center) / sigma) ** 2)


def find_editable_bases(
    amplicon: str,
    guide_start: int,
    guide_end: int,
    is_rc: bool,
    editor_type: str,
    window_center: int,
    window_sigma: float,
) -> list[tuple[int, float]]:
    """
    Find editable bases in the activity window with their probabilities.

    Args:
        amplicon: Amplicon sequence
        guide_start: Start position of guide in amplicon (0-indexed)
        guide_end: End position of guide in amplicon (0-indexed, exclusive)
        is_rc: True if guide is on reverse complement strand
        editor_type: 'CBE' (C→T) or 'ABE' (A→G)
        window_center: Center of activity window (position from PAM-distal end)
        window_sigma: Spread of activity window

    Returns:
        List of (amplicon_position, probability) tuples for editable bases
    """
    target_base = 'C' if editor_type == 'CBE' else 'A'
    guide_len = guide_end - guide_start

    editable = []

    # Activity window spans roughly center ± 3*sigma
    window_radius = int(3 * window_sigma) + 1
    window_start_pos = max(1, window_center - window_radius)
    window_end_pos = min(guide_len, window_center + window_radius)

    for guide_pos in range(window_start_pos, window_end_pos + 1):
        # Convert guide position (1-indexed from PAM-distal) to amplicon position
        if is_rc:
            # For RC guides, position 1 is at guide_end-1, increasing toward guide_start
            amplicon_pos = guide_end - guide_pos
            # Check complement base (if target is C, look for G on amplicon)
            check_base = {'C': 'G', 'A': 'T'}[target_base]
        else:
            # For forward guides, position 1 is at guide_start
            amplicon_pos = guide_start + guide_pos - 1
            check_base = target_base

        if 0 <= amplicon_pos < len(amplicon):
            if amplicon[amplicon_pos].upper() == check_base:
                prob = gaussian_probability(guide_pos, window_center, window_sigma)
                editable.append((amplicon_pos, prob))

    return editable


def generate_base_edit(
    amplicon: str,
    guide_start: int,
    guide_end: int,
    is_rc: bool,
    editor_type: str,
    window_center: int,
    window_sigma: float,
    base_edit_prob: float,
) -> Edit:
    """
    Generate a base editing event (substitutions in activity window).

    Args:
        amplicon: Amplicon sequence
        guide_start: Start position of guide in amplicon (0-indexed)
        guide_end: End position of guide in amplicon (0-indexed, exclusive)
        is_rc: True if guide is on reverse complement strand
        editor_type: 'CBE' (C→T) or 'ABE' (A→G)
        window_center: Center of activity window
        window_sigma: Spread of activity window
        base_edit_prob: Per-base conversion probability

    Returns:
        Edit object with substitution(s)
    """
    editable_bases = find_editable_bases(
        amplicon, guide_start, guide_end, is_rc, editor_type,
        window_center, window_sigma
    )

    if not editable_bases:
        # No editable bases found - return no edit
        return Edit(
            edit_type='none',
            position=0,
            size=0,
            original_seq='',
            edited_seq=''
        )

    # Determine which bases get edited based on position probability and base_edit_prob
    positions = []
    original_seqs = []
    edited_seqs = []

    conversion = {'CBE': ('C', 'T'), 'ABE': ('A', 'G')}
    from_base, to_base = conversion[editor_type]
    # For RC strand, we edit the complement
    if is_rc:
        from_base = {'C': 'G', 'A': 'T'}[from_base]
        to_base = {'T': 'A', 'G': 'C'}[to_base]

    for amp_pos, pos_prob in editable_bases:
        # Combined probability: position weight * base edit probability
        if random.random() < pos_prob * base_edit_prob:
            positions.append(amp_pos)
            original_seqs.append(amplicon[amp_pos])
            edited_seqs.append(to_base)

    if not positions:
        # Probabilistically, no bases were edited this time
        return Edit(
            edit_type='none',
            position=0,
            size=0,
            original_seq='',
            edited_seq=''
        )

    # Return single or multi-position edit
    if len(positions) == 1:
        return Edit(
            edit_type='substitution',
            position=positions[0],
            size=1,
            original_seq=original_seqs[0],
            edited_seq=edited_seqs[0]
        )
    else:
        return Edit(
            edit_type='substitution',
            position=positions,
            size=[1] * len(positions),
            original_seq=original_seqs,
            edited_seq=edited_seqs
        )


def apply_base_edit(amplicon: str, edit: Edit) -> str:
    """
    Apply base editing substitutions to amplicon.

    Args:
        amplicon: Original amplicon sequence
        edit: Edit object with substitution(s)

    Returns:
        Edited sequence
    """
    if edit.edit_type == 'none':
        return amplicon

    seq = list(amplicon)

    # Handle both single and multi-position edits
    positions = edit.position if isinstance(edit.position, list) else [edit.position]
    edited_seqs = edit.edited_seq if isinstance(edit.edited_seq, list) else [edit.edited_seq]

    for pos, new_base in zip(positions, edited_seqs):
        seq[pos] = new_base

    return ''.join(seq)


# =============================================================================
# Prime Editing Functions
# =============================================================================

@dataclass
class PrimeEditIntent:
    """Represents the intended edit from a pegRNA."""
    edit_type: Literal['substitution', 'insertion', 'deletion', 'complex']
    position: int  # Position in amplicon where edit starts (0-indexed)
    original_seq: str  # Original sequence at edit site
    edited_seq: str  # Intended edited sequence
    pbs_start: int  # Start of PBS binding region
    pbs_end: int  # End of PBS binding region
    rt_template: str  # RT template portion of extension


def parse_peg_extension(
    amplicon: str,
    cut_site: int,
    peg_extension: str,
    pbs_length: int = 13,
) -> PrimeEditIntent:
    """
    Parse pegRNA extension to identify the intended edit.

    The pegRNA extension consists of:
    - RT template (5' portion): specifies the edit
    - PBS (3' portion): binds to the nicked strand

    The PBS binds upstream of the nick site (on the nicked strand).
    The RT template specifies the sequence to be installed.

    IMPORTANT: The RT template on the pegRNA is reverse complemented when
    incorporated into the target strand. This matches CRISPResso2's behavior.

    Args:
        amplicon: Reference amplicon sequence
        cut_site: Position of the nick (0-indexed)
        peg_extension: 3' extension sequence (RT template + PBS)
        pbs_length: Length of primer binding site (default 13bp)

    Returns:
        PrimeEditIntent describing the intended edit
    """
    # The extension is provided 5' to 3' as: RT_template + PBS
    # PBS binds to the nicked strand upstream of the nick
    # PBS is reverse complement of the genomic sequence upstream of nick

    # Extract PBS (last pbs_length bases of extension)
    pbs = peg_extension[-pbs_length:]
    rt_template = peg_extension[:-pbs_length]

    if len(rt_template) == 0:
        raise ValueError("RT template is empty - peg_extension too short for given PBS length")

    # PBS binds upstream of the nick site
    # The PBS is complementary to positions [cut_site - pbs_length : cut_site] on the target strand
    pbs_start = cut_site - pbs_length
    pbs_end = cut_site

    # The RT template will replace sequence starting at the cut site
    # CRITICAL: The RT template must be reverse complemented to get the
    # sequence that appears on the target strand (this matches CRISPResso2)
    rt_template_rc = reverse_complement(rt_template)

    # Get the reference sequence that would be replaced
    # RT template length determines how much reference to compare
    rt_len = len(rt_template_rc)
    ref_seq = amplicon[cut_site:cut_site + rt_len]

    # Compare to find differences
    if rt_template_rc == ref_seq:
        # No edit - this shouldn't happen with a real pegRNA but handle it
        return PrimeEditIntent(
            edit_type='substitution',
            position=cut_site,
            original_seq=ref_seq,
            edited_seq=rt_template_rc,
            pbs_start=pbs_start,
            pbs_end=pbs_end,
            rt_template=rt_template_rc,
        )

    # Determine edit type by comparing lengths and content
    if len(rt_template_rc) == len(ref_seq):
        # Same length - substitution(s)
        edit_type = 'substitution'
    elif len(rt_template_rc) > len(ref_seq):
        # RT template longer - insertion
        edit_type = 'insertion'
    else:
        # RT template shorter - deletion
        edit_type = 'deletion'

    return PrimeEditIntent(
        edit_type=edit_type,
        position=cut_site,
        original_seq=ref_seq,
        edited_seq=rt_template_rc,
        pbs_start=pbs_start,
        pbs_end=pbs_end,
        rt_template=rt_template_rc,
    )


def generate_prime_edit(
    amplicon: str,
    intent: PrimeEditIntent,
    outcome_type: str,
    scaffold: str = '',
) -> Edit:
    """
    Generate a prime editing Edit based on outcome type.

    Args:
        amplicon: Reference amplicon sequence
        intent: The intended edit from the pegRNA
        outcome_type: Type of outcome ('perfect', 'partial', 'indel', 'scaffold', 'flap_indel')
        scaffold: pegRNA scaffold sequence (for scaffold incorporation)

    Returns:
        Edit object representing the outcome
    """
    if outcome_type == 'perfect':
        # Perfect edit - exact RT template incorporation
        return Edit(
            edit_type='prime_edit',
            position=intent.position,
            size=len(intent.edited_seq) - len(intent.original_seq),
            original_seq=intent.original_seq,
            edited_seq=intent.edited_seq,
        )

    elif outcome_type == 'partial':
        # Partial edit - truncated RT template (random truncation point)
        if len(intent.rt_template) <= 2:
            # Too short to truncate meaningfully
            truncation = len(intent.rt_template)
        else:
            truncation = random.randint(2, len(intent.rt_template) - 1)

        truncated_template = intent.rt_template[:truncation]
        truncated_ref = intent.original_seq[:truncation] if truncation <= len(intent.original_seq) else intent.original_seq

        return Edit(
            edit_type='prime_edit',
            position=intent.position,
            size=len(truncated_template) - len(truncated_ref),
            original_seq=truncated_ref,
            edited_seq=truncated_template,
        )

    elif outcome_type == 'indel':
        # NHEJ-like indel at nick site
        indel_size = random.choice([-3, -2, -1, 1, 2, 3])
        if indel_size < 0:
            # Deletion
            del_size = abs(indel_size)
            return Edit(
                edit_type='deletion',
                position=intent.position,
                size=del_size,
                original_seq=amplicon[intent.position:intent.position + del_size],
                edited_seq='',
            )
        else:
            # Insertion
            insert_seq = generate_random_sequence(indel_size)
            return Edit(
                edit_type='insertion',
                position=intent.position,
                size=indel_size,
                original_seq='',
                edited_seq=insert_seq,
            )

    elif outcome_type == 'scaffold':
        # Scaffold incorporation - part of scaffold sequence included
        scaffold_len = random.randint(5, min(20, len(scaffold))) if len(scaffold) > 5 else len(scaffold)
        scaffold_fragment = scaffold[:scaffold_len]

        # Scaffold gets incorporated at the edit site
        edited_seq = intent.edited_seq + scaffold_fragment

        return Edit(
            edit_type='prime_edit',
            position=intent.position,
            size=len(edited_seq) - len(intent.original_seq),
            original_seq=intent.original_seq,
            edited_seq=edited_seq,
        )

    elif outcome_type == 'flap_indel':
        # Small indel at the 3' flap junction
        # This occurs at the boundary between the RT template and downstream sequence
        flap_indel = random.choice([-2, -1, 1, 2])
        if flap_indel < 0:
            # Small deletion at the junction
            del_size = abs(flap_indel)
            # Apply the intended edit but with a small deletion at the end
            edited_seq = intent.edited_seq[:-del_size] if len(intent.edited_seq) > del_size else ''
            return Edit(
                edit_type='prime_edit',
                position=intent.position,
                size=len(edited_seq) - len(intent.original_seq),
                original_seq=intent.original_seq,
                edited_seq=edited_seq,
            )
        else:
            # Small insertion at the junction
            insert_seq = generate_random_sequence(flap_indel)
            edited_seq = intent.edited_seq + insert_seq
            return Edit(
                edit_type='prime_edit',
                position=intent.position,
                size=len(edited_seq) - len(intent.original_seq),
                original_seq=intent.original_seq,
                edited_seq=edited_seq,
            )

    else:
        raise ValueError(f"Unknown outcome type: {outcome_type}")


def select_prime_edit_outcome(
    perfect_frac: float = 0.6,
    partial_frac: float = 0.15,
    indel_frac: float = 0.15,
    scaffold_frac: float = 0.05,
    flap_indel_frac: float = 0.05,
) -> str:
    """
    Randomly select a prime editing outcome type based on distribution.

    Returns:
        Outcome type string
    """
    outcomes = ['perfect', 'partial', 'indel', 'scaffold', 'flap_indel']
    weights = [perfect_frac, partial_frac, indel_frac, scaffold_frac, flap_indel_frac]

    # Normalize weights
    total = sum(weights)
    weights = [w / total for w in weights]

    return random.choices(outcomes, weights=weights, k=1)[0]


def apply_prime_edit(amplicon: str, edit: Edit) -> str:
    """
    Apply prime edit to amplicon.

    Handles substitutions, insertions, deletions, and complex edits.

    Args:
        amplicon: Original amplicon sequence
        edit: Edit object

    Returns:
        Edited sequence
    """
    if edit.edit_type == 'none':
        return amplicon

    pos = edit.position
    original = edit.original_seq
    edited = edit.edited_seq

    # Replace the original sequence with the edited sequence
    return amplicon[:pos] + edited + amplicon[pos + len(original):]


# =============================================================================
# Sequencing Simulation
# =============================================================================

def add_sequencing_errors(
    seq: str,
    error_rate: float,
) -> tuple[str, list[SequencingError]]:
    """
    Add random substitution errors to simulate sequencing noise.

    Args:
        seq: Input sequence
        error_rate: Per-base error rate

    Returns:
        Tuple of (sequence with errors, list of SequencingError objects)
    """
    errors: list[SequencingError] = []

    if error_rate == 0:
        return seq, errors

    bases = list(seq)
    for i in range(len(bases)):
        if random.random() < error_rate:
            # Substitute with a different base
            current = bases[i]
            alternatives = [b for b in 'ACGT' if b != current.upper()]
            new_base = random.choice(alternatives)
            errors.append(SequencingError(
                position=i,
                original_base=current.upper(),
                error_base=new_base,
            ))
            bases[i] = new_base

    return ''.join(bases), errors


def generate_quality_string(length: int, quality_char: str = 'I') -> str:
    """
    Generate quality string for FASTQ.

    Args:
        length: Length of quality string
        quality_char: Character to use (default 'I' = Q40 in Phred+33)

    Returns:
        Quality string
    """
    return quality_char * length


# =============================================================================
# Output Writers
# =============================================================================

def write_fastq(reads: list[EditedRead], filepath: str) -> None:
    """Write reads to FASTQ file (gzip if .gz extension)."""
    open_func = gzip.open if filepath.endswith('.gz') else open
    mode = 'wt' if filepath.endswith('.gz') else 'w'

    with open_func(filepath, mode) as fh:
        for edited_read in reads:
            fh.write(str(edited_read.read))


def write_edit_tsv(reads: list[EditedRead], filepath: str) -> None:
    """Write per-read edit information to TSV.

    Handles both single edits (NHEJ) and multi-position edits (base editing).
    Multi-position edits have list values which are formatted as comma-separated.
    Also includes sequencing error information.
    """
    with open(filepath, 'w') as fh:
        # Header - includes sequencing error columns
        fh.write('read_name\tedit_type\tedit_position\tedit_size\toriginal_seq\tedited_seq\t'
                 'seq_error_count\tseq_error_positions\tseq_error_original\tseq_error_new\n')

        for edited_read in reads:
            edit = edited_read.edit

            # Format values - handle both single values and lists (for multi-position edits)
            if isinstance(edit.position, list):
                pos_str = ','.join(str(p) for p in edit.position)
                size_str = ','.join(str(s) for s in edit.size)
                orig_str = ','.join(edit.original_seq)
                edit_str = ','.join(edit.edited_seq)
            else:
                pos_str = str(edit.position)
                size_str = str(edit.size)
                orig_str = edit.original_seq
                edit_str = edit.edited_seq

            # Format sequencing errors
            seq_errors = edited_read.sequencing_errors
            error_count = len(seq_errors)
            if error_count > 0:
                error_positions = ','.join(str(e.position) for e in seq_errors)
                error_original = ','.join(e.original_base for e in seq_errors)
                error_new = ','.join(e.error_base for e in seq_errors)
            else:
                error_positions = ''
                error_original = ''
                error_new = ''

            fh.write(f'{edited_read.read.name}\t{edit.edit_type}\t{pos_str}\t'
                     f'{size_str}\t{orig_str}\t{edit_str}\t'
                     f'{error_count}\t{error_positions}\t{error_original}\t{error_new}\n')


def write_alleles_tsv(reads: list[EditedRead], filepath: str) -> None:
    """Write per-allele aggregated edit info matching CRISPResso format.

    Groups reads by sequence, aggregates edit metadata into CRISPResso-compatible
    columns for direct comparison with Alleles_frequency_table output.
    """
    from collections import defaultdict

    # Group reads by sequence
    allele_groups: dict[str, list[EditedRead]] = defaultdict(list)
    for edited_read in reads:
        allele_groups[edited_read.read.seq].append(edited_read)

    with open(filepath, 'w') as fh:
        # Header matching CRISPResso's detailed allele table columns
        fh.write('#Reads\tAligned_Sequence\t'
                 'all_deletion_positions\tall_deletion_sizes\t'
                 'all_insertion_positions\tall_insertion_sizes\t'
                 'all_substitution_positions\tall_substitution_values\n')

        for seq, group in sorted(allele_groups.items(), key=lambda x: -len(x[1])):
            count = len(group)

            # Aggregate edits from first read (all reads with same seq have same edits)
            # Note: sequencing errors may differ, but final sequence is the same
            first_read = group[0]
            edit = first_read.edit

            del_positions = []
            del_sizes = []
            ins_positions = []
            ins_sizes = []
            sub_positions = []
            sub_values = []

            # Process intentional edits
            if edit.edit_type == 'deletion':
                if isinstance(edit.position, list):
                    del_positions.extend(edit.position)
                    del_sizes.extend(edit.size)
                else:
                    del_positions.append(edit.position)
                    del_sizes.append(edit.size)

            elif edit.edit_type == 'insertion':
                if isinstance(edit.position, list):
                    ins_positions.extend(edit.position)
                    ins_sizes.extend(edit.size)
                else:
                    ins_positions.append(edit.position)
                    ins_sizes.append(edit.size)

            elif edit.edit_type == 'substitution':
                if isinstance(edit.position, list):
                    for i, pos in enumerate(edit.position):
                        sub_positions.append(pos)
                        orig = edit.original_seq[i]
                        edited = edit.edited_seq[i]
                        sub_values.append(f'{orig}>{edited}')
                else:
                    sub_positions.append(edit.position)
                    sub_values.append(f'{edit.original_seq}>{edit.edited_seq}')

            elif edit.edit_type == 'prime_edit':
                # Prime edits can have mixed edit types - check the sequences
                # For now, treat as substitutions if sizes match, else deletion/insertion
                if isinstance(edit.position, list):
                    for i, pos in enumerate(edit.position):
                        orig = edit.original_seq[i] if isinstance(edit.original_seq, list) else edit.original_seq
                        edited = edit.edited_seq[i] if isinstance(edit.edited_seq, list) else edit.edited_seq
                        size = edit.size[i] if isinstance(edit.size, list) else edit.size
                        if len(orig) == len(edited) == 1:
                            sub_positions.append(pos)
                            sub_values.append(f'{orig}>{edited}')
                        elif len(edited) < len(orig):
                            del_positions.append(pos)
                            del_sizes.append(len(orig) - len(edited))
                        else:
                            ins_positions.append(pos)
                            ins_sizes.append(len(edited) - len(orig))
                else:
                    orig = edit.original_seq
                    edited = edit.edited_seq
                    if len(orig) == len(edited):
                        for i, (o, e) in enumerate(zip(orig, edited)):
                            if o != e:
                                sub_positions.append(edit.position + i)
                                sub_values.append(f'{o}>{e}')
                    elif len(edited) < len(orig):
                        del_positions.append(edit.position)
                        del_sizes.append(len(orig) - len(edited))
                    else:
                        ins_positions.append(edit.position)
                        ins_sizes.append(len(edited) - len(orig))

            # Add sequencing errors as substitutions
            for seq_error in first_read.sequencing_errors:
                sub_positions.append(seq_error.position)
                sub_values.append(f'{seq_error.original_base}>{seq_error.error_base}')

            # Sort positions for consistent output
            if del_positions:
                del_positions, del_sizes = zip(*sorted(zip(del_positions, del_sizes)))
                del_positions, del_sizes = list(del_positions), list(del_sizes)
            if ins_positions:
                ins_positions, ins_sizes = zip(*sorted(zip(ins_positions, ins_sizes)))
                ins_positions, ins_sizes = list(ins_positions), list(ins_sizes)
            if sub_positions:
                sub_positions, sub_values = zip(*sorted(zip(sub_positions, sub_values)))
                sub_positions, sub_values = list(sub_positions), list(sub_values)

            # Format as Python lists (matching CRISPResso format)
            fh.write(f'{count}\t{seq}\t'
                     f'{del_positions}\t{del_sizes}\t'
                     f'{ins_positions}\t{ins_sizes}\t'
                     f'{sub_positions}\t{sub_values}\n')


def write_vcf(
    variants: list[VcfVariant],
    amplicon_name: str,
    amplicon_seq: str,
    filepath: str
) -> None:
    """Write VCF file in CRISPResso2-compatible format."""
    with open(filepath, 'w') as fh:
        # Header
        fh.write('##fileformat=VCFv4.5\n')
        fh.write('##source=syn-gen\n')
        fh.write(f'##contig=<ID={amplicon_name},length={len(amplicon_seq)}>\n')
        fh.write('##INFO=<ID=AF,Number=A,Type=Float,Description="Allele Frequency">\n')
        fh.write('#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tReference\n')

        # Variants
        for var in variants:
            fh.write(f'{var.chrom}\t{var.pos}\t.\t{var.ref}\t{var.alt}\t.\tPASS\t'
                     f'AF={var.af:.3f}\tGT\t.\n')


def aggregate_edits_to_variants(
    reads: list[EditedRead],
    amplicon: str,
    amplicon_name: str
) -> list[VcfVariant]:
    """
    Convert per-read edits to VCF variant calls with allele frequencies.

    Groups identical edits and calculates AF = count / total_reads.
    Handles single-position and multi-position edits (e.g., base editing).
    """
    total_reads = len(reads)
    # Key: (edit_type, position, original_seq, edited_seq) -> count
    # For multi-position edits, we expand to individual positions
    edit_counts: Counter[tuple] = Counter()

    for edited_read in reads:
        edit = edited_read.edit
        if edit.edit_type == 'none':
            continue

        # Handle multi-position edits (e.g., multiple substitutions)
        if isinstance(edit.position, list):
            # Expand multi-position edit into individual position counts
            for i, pos in enumerate(edit.position):
                orig = edit.original_seq[i] if isinstance(edit.original_seq, list) else edit.original_seq
                edited = edit.edited_seq[i] if isinstance(edit.edited_seq, list) else edit.edited_seq
                size = edit.size[i] if isinstance(edit.size, list) else edit.size
                key = (edit.edit_type, pos, size, orig, edited)
                edit_counts[key] += 1
        else:
            # Single-position edit
            key = (edit.edit_type, edit.position, edit.size, edit.original_seq, edit.edited_seq)
            edit_counts[key] += 1

    variants = []
    for (edit_type, position, size, original_seq, edited_seq), count in edit_counts.items():
        af = count / total_reads

        if edit_type == 'deletion':
            # For VCF, include the base before the deletion
            if position > 0:
                ref = amplicon[position - 1:position + size]
                alt = amplicon[position - 1]
                vcf_pos = position  # 1-indexed
            else:
                # Deletion at start - include base after
                ref = amplicon[position:position + size + 1]
                alt = amplicon[position + size]
                vcf_pos = 1
        elif edit_type == 'insertion':
            # For VCF, include the base before the insertion
            if position > 0:
                ref = amplicon[position - 1]
                alt = amplicon[position - 1] + edited_seq
                vcf_pos = position  # 1-indexed
            else:
                # Insertion at start
                ref = amplicon[0]
                alt = edited_seq + amplicon[0]
                vcf_pos = 1
        elif edit_type == 'substitution':
            # Simple: REF is original base, ALT is new base
            ref = original_seq
            alt = edited_seq
            vcf_pos = position + 1  # Convert 0-indexed to 1-indexed
        elif edit_type == 'prime_edit':
            # Prime edits: complex variants with original_seq -> edited_seq
            # Include anchor base before the edit for VCF compliance
            if position > 0:
                anchor = amplicon[position - 1]
                ref = anchor + original_seq
                alt = anchor + edited_seq
                vcf_pos = position  # 1-indexed (anchor position)
            else:
                # Edit at start - use first base as anchor after
                if len(original_seq) > 0:
                    ref = original_seq
                    alt = edited_seq if edited_seq else '.'
                else:
                    ref = amplicon[0]
                    alt = edited_seq + amplicon[0] if edited_seq else amplicon[0]
                vcf_pos = 1
        else:
            continue  # Skip unknown edit types

        variants.append(VcfVariant(
            chrom=amplicon_name,
            pos=vcf_pos,
            ref=ref,
            alt=alt,
            af=af
        ))

    # Sort by position
    variants.sort(key=lambda v: v.pos)
    return variants


# =============================================================================
# Main Generator
# =============================================================================

def generate_synthetic_data(
    amplicon: str,
    guide: str,
    num_reads: int,
    edit_rate: float,
    error_rate: float,
    output_prefix: str,
    amplicon_name: str = 'AMPLICON',
    read_length: Optional[int] = None,
    seed: Optional[int] = None,
    cleavage_offset: int = -3,
    quiet: bool = False,
    # Mode and base editing parameters
    mode: str = 'nhej',
    base_editor: str = 'CBE',
    window_center: int = 6,
    window_sigma: float = 1.5,
    base_edit_prob: float = 0.5,
    # Prime editing parameters
    peg_extension: Optional[str] = None,
    peg_scaffold: str = '',
    perfect_edit_fraction: float = 0.6,
    partial_edit_fraction: float = 0.15,
    pe_indel_fraction: float = 0.15,
    scaffold_incorporation_fraction: float = 0.05,
    flap_indel_fraction: float = 0.05,
) -> dict:
    """
    Main entry point for synthetic data generation.

    Args:
        mode: Editing mode - 'nhej' (deletions/insertions), 'base-edit' (CBE/ABE), or 'prime-edit'
        base_editor: Type of base editor ('CBE' or 'ABE') for base-edit mode
        window_center: Center of activity window (position from PAM-distal end)
        window_sigma: Spread of activity window (std dev)
        base_edit_prob: Per-eligible-base conversion probability
        peg_extension: pegRNA 3' extension (RT template + PBS) for prime-edit mode
        peg_scaffold: pegRNA scaffold sequence
        perfect_edit_fraction: Fraction of perfect prime edits
        partial_edit_fraction: Fraction of partial prime edits
        pe_indel_fraction: Fraction of indels at nick site
        scaffold_incorporation_fraction: Fraction with scaffold incorporation
        flap_indel_fraction: Fraction with flap indels

    Returns dict with summary statistics.
    """
    # Set random seed if provided
    if seed is not None:
        random.seed(seed)

    # Validate mode-specific requirements
    if mode == 'prime-edit' and not peg_extension:
        raise ValueError("--peg-extension is required for prime-edit mode")

    # Find guide and calculate cut site
    guide_start, guide_end, is_rc = find_guide_in_amplicon(amplicon, guide)
    cut_site = calculate_cut_site(guide_start, guide_end, is_rc, cleavage_offset)

    # For prime editing, parse the pegRNA extension to get intended edit
    prime_edit_intent = None
    if mode == 'prime-edit':
        prime_edit_intent = parse_peg_extension(amplicon, cut_site, peg_extension)

    # Determine read length
    actual_read_length = read_length if read_length else len(amplicon)
    if actual_read_length > len(amplicon):
        actual_read_length = len(amplicon)

    # Generate reads
    reads: list[EditedRead] = []
    deletion_count = 0
    insertion_count = 0
    substitution_count = 0
    prime_edit_count = 0

    for i in range(num_reads):
        is_edited = random.random() < edit_rate

        if is_edited:
            if mode == 'base-edit':
                # Base editing mode - generate substitutions
                edit = generate_base_edit(
                    amplicon=amplicon,
                    guide_start=guide_start,
                    guide_end=guide_end,
                    is_rc=is_rc,
                    editor_type=base_editor,
                    window_center=window_center,
                    window_sigma=window_sigma,
                    base_edit_prob=base_edit_prob,
                )
                seq = apply_base_edit(amplicon, edit)
                if edit.edit_type == 'substitution':
                    substitution_count += 1

            elif mode == 'prime-edit':
                # Prime editing mode - generate various outcome types
                outcome = select_prime_edit_outcome(
                    perfect_frac=perfect_edit_fraction,
                    partial_frac=partial_edit_fraction,
                    indel_frac=pe_indel_fraction,
                    scaffold_frac=scaffold_incorporation_fraction,
                    flap_indel_frac=flap_indel_fraction,
                )
                edit = generate_prime_edit(
                    amplicon=amplicon,
                    intent=prime_edit_intent,
                    outcome_type=outcome,
                    scaffold=peg_scaffold,
                )
                seq = apply_prime_edit(amplicon, edit)
                if edit.edit_type == 'prime_edit':
                    prime_edit_count += 1
                elif edit.edit_type == 'deletion':
                    deletion_count += 1
                elif edit.edit_type == 'insertion':
                    insertion_count += 1

            else:
                # NHEJ mode (default) - generate deletions/insertions
                edit = generate_edit(cut_site, amplicon)
                seq = apply_edit(amplicon, edit)
                if edit.edit_type == 'deletion':
                    deletion_count += 1
                else:
                    insertion_count += 1
        else:
            edit = Edit(edit_type='none', position=0, size=0, original_seq='', edited_seq='')
            seq = amplicon

        # Add sequencing errors
        seq, seq_errors = add_sequencing_errors(seq, error_rate)

        # Create FASTQ read
        qual = generate_quality_string(len(seq))
        fastq_read = FastqRead(name=f'read_{i}', seq=seq, qual=qual)

        reads.append(EditedRead(read=fastq_read, edit=edit, sequencing_errors=seq_errors))

    # Write outputs
    fastq_path = f'{output_prefix}.fastq'
    tsv_path = f'{output_prefix}_edits.tsv'
    vcf_path = f'{output_prefix}.vcf'

    write_fastq(reads, fastq_path)
    write_edit_tsv(reads, tsv_path)

    variants = aggregate_edits_to_variants(reads, amplicon, amplicon_name)
    write_vcf(variants, amplicon_name, amplicon, vcf_path)

    # Calculate statistics
    edited_count = deletion_count + insertion_count + substitution_count + prime_edit_count
    unedited_count = num_reads - edited_count

    stats = {
        'total_reads': num_reads,
        'edited_reads': edited_count,
        'unedited_reads': unedited_count,
        'edit_rate_actual': edited_count / num_reads if num_reads > 0 else 0,
        'deletions': deletion_count,
        'insertions': insertion_count,
        'substitutions': substitution_count,
        'prime_edits': prime_edit_count,
        'mode': mode,
        'cut_site': cut_site,
        'guide_start': guide_start,
        'guide_end': guide_end,
        'guide_is_rc': is_rc,
        'output_files': {
            'fastq': fastq_path,
            'tsv': tsv_path,
            'vcf': vcf_path
        }
    }

    # Print summary
    if not quiet:
        print('=== syn-gen Summary ===')
        print(f'Mode:            {mode}')
        print(f'Amplicon length: {len(amplicon)} bp')
        print(f'Guide position:  {guide_start}-{guide_end} ({"RC" if is_rc else "FWD"})')
        print(f'Cut site:        {cut_site}')
        print()
        print(f'Total reads:     {num_reads}')
        print(f'Edited reads:    {edited_count} ({100 * edited_count / num_reads:.2f}%)')
        print(f'Unedited reads:  {unedited_count} ({100 * unedited_count / num_reads:.2f}%)')
        if edited_count > 0:
            if mode == 'base-edit':
                print(f'  - Substitutions: {substitution_count} ({100 * substitution_count / edited_count:.2f}% of edits)')
            elif mode == 'prime-edit':
                print(f'  - Prime edits: {prime_edit_count} ({100 * prime_edit_count / edited_count:.2f}% of edits)')
                print(f'  - Indels:      {deletion_count + insertion_count} ({100 * (deletion_count + insertion_count) / edited_count:.2f}% of edits)')
            else:
                print(f'  - Deletions:   {deletion_count} ({100 * deletion_count / edited_count:.2f}% of edits)')
                print(f'  - Insertions:  {insertion_count} ({100 * insertion_count / edited_count:.2f}% of edits)')
        print()
        print('Output files:')
        print(f'  FASTQ: {fastq_path}')
        print(f'  TSV:   {tsv_path}')
        print(f'  VCF:   {vcf_path}')

    return stats


# =============================================================================
# Input Validation
# =============================================================================

def validate_sequence(seq: str, name: str, allowed: str = 'ACGTN') -> None:
    """Validate a DNA sequence."""
    invalid = set(seq.upper()) - set(allowed)
    if invalid:
        raise ValueError(f"{name} contains invalid characters: {invalid} (allowed: {allowed})")


def validate_inputs(
    amplicon: str,
    guide: str,
    edit_rate: float,
    error_rate: float
) -> None:
    """Validate all inputs before generation."""
    validate_sequence(amplicon, 'Amplicon', 'ACGTN')
    validate_sequence(guide, 'Guide', 'ACGT')

    if not 0.0 <= edit_rate <= 1.0:
        raise ValueError(f"edit_rate must be between 0 and 1, got {edit_rate}")

    if not 0.0 <= error_rate <= 1.0:
        raise ValueError(f"error_rate must be between 0 and 1, got {error_rate}")

    if len(guide) < 10:
        import warnings
        warnings.warn(f"Guide length {len(guide)} is unusually short (typical: 17-23bp)")
    elif len(guide) > 25:
        import warnings
        warnings.warn(f"Guide length {len(guide)} is unusually long (typical: 17-23bp)")


# =============================================================================
# CLI
# =============================================================================

def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Generate synthetic CRISPR editing data for testing (NHEJ, base editing, prime editing).',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    # Mode selection
    parser.add_argument(
        '--mode',
        type=str,
        choices=['nhej', 'base-edit', 'prime-edit'],
        default='nhej',
        help='Editing mode: nhej (deletions/insertions), base-edit (CBE/ABE substitutions), prime-edit (pegRNA templated)'
    )

    # Input sequences
    input_group = parser.add_argument_group('Input sequences')
    input_group.add_argument(
        '-a', '--amplicon',
        type=str,
        help='Amplicon sequence. If not provided, generates random 200bp sequence.'
    )
    input_group.add_argument(
        '-g', '--guide',
        type=str,
        help='Guide/sgRNA sequence (without PAM). Required if --amplicon provided.'
    )
    input_group.add_argument(
        '--amplicon-name',
        type=str,
        default='AMPLICON',
        help='Name for amplicon in output files (used as CHROM in VCF)'
    )

    # Generation parameters
    gen_group = parser.add_argument_group('Generation parameters')
    gen_group.add_argument(
        '-n', '--num-reads',
        type=int,
        default=10000,
        help='Number of reads to generate'
    )
    gen_group.add_argument(
        '-e', '--edit-rate',
        type=float,
        default=0.3,
        help='Fraction of reads with NHEJ edits (0.0-1.0)'
    )
    gen_group.add_argument(
        '--error-rate',
        type=float,
        default=0.001,
        help='Per-base sequencing error rate'
    )
    gen_group.add_argument(
        '--read-length',
        type=int,
        default=None,
        help='Read length. Default: full amplicon length'
    )
    gen_group.add_argument(
        '--cleavage-offset',
        type=int,
        default=-3,
        help="Cut site offset from 3' end of guide (Cas9 default: -3)"
    )

    # Base editing parameters
    base_group = parser.add_argument_group('Base editing parameters (for --mode base-edit)')
    base_group.add_argument(
        '--base-editor',
        type=str,
        choices=['CBE', 'ABE'],
        default='CBE',
        help='Base editor type: CBE (C→T) or ABE (A→G)'
    )
    base_group.add_argument(
        '--window-center',
        type=int,
        default=6,
        help='Activity window center position (from PAM-distal end of guide, 1-indexed)'
    )
    base_group.add_argument(
        '--window-sigma',
        type=float,
        default=1.5,
        help='Activity window spread (standard deviation for Gaussian model)'
    )
    base_group.add_argument(
        '--base-edit-prob',
        type=float,
        default=0.5,
        help='Per-eligible-base conversion probability within the window'
    )

    # Prime editing parameters
    prime_group = parser.add_argument_group('Prime editing parameters (for --mode prime-edit)')
    prime_group.add_argument(
        '--peg-spacer',
        type=str,
        default=None,
        help='pegRNA spacer sequence (defaults to --guide if not specified)'
    )
    prime_group.add_argument(
        '--peg-extension',
        type=str,
        default=None,
        help='pegRNA 3\' extension (RT template + PBS). Required for prime-edit mode.'
    )
    prime_group.add_argument(
        '--peg-scaffold',
        type=str,
        default='GTTTTAGAGCTAGAAATAGCAAGTTAAAATAAGGCTAGTCCGTTATCAACTTGAAAAAGTGGCACCGAGTCGGTGC',
        help='pegRNA scaffold sequence (default: standard SpCas9 scaffold)'
    )
    prime_group.add_argument(
        '--nick-guide',
        type=str,
        default=None,
        help='PE3 nicking guide sequence (optional, for PE3 mode)'
    )
    prime_group.add_argument(
        '--perfect-edit-fraction',
        type=float,
        default=0.6,
        help='Fraction of edits that are perfect RT template incorporation (default: 0.6)'
    )
    prime_group.add_argument(
        '--partial-edit-fraction',
        type=float,
        default=0.15,
        help='Fraction of edits with incomplete/truncated RT template (default: 0.15)'
    )
    prime_group.add_argument(
        '--pe-indel-fraction',
        type=float,
        default=0.15,
        help='Fraction of edits with indels at nick site (default: 0.15)'
    )
    prime_group.add_argument(
        '--scaffold-incorporation-fraction',
        type=float,
        default=0.05,
        help='Fraction of edits with scaffold sequence incorporation (default: 0.05)'
    )
    prime_group.add_argument(
        '--flap-indel-fraction',
        type=float,
        default=0.05,
        help='Fraction of edits with small indels at 3\' flap junction (default: 0.05)'
    )

    # Output options
    output_group = parser.add_argument_group('Output options')
    output_group.add_argument(
        '-o', '--output-prefix',
        type=str,
        default='synthetic',
        help='Prefix for output files'
    )
    output_group.add_argument(
        '--seed',
        type=int,
        default=None,
        help='Random seed for reproducibility'
    )
    output_group.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Suppress summary output to stdout'
    )

    return parser


def main() -> int:
    parser = create_parser()
    args = parser.parse_args()

    # Handle random generation mode
    if args.amplicon is None:
        # Generate random amplicon with embedded guide
        random.seed(args.seed)  # Set seed early for reproducible random generation
        amplicon_length = 200
        guide_length = 20

        # Generate random guide
        guide = generate_random_sequence(guide_length)

        # Generate amplicon with guide embedded near the middle
        prefix_len = (amplicon_length - guide_length) // 2
        suffix_len = amplicon_length - guide_length - prefix_len

        amplicon = (
            generate_random_sequence(prefix_len) +
            guide +
            generate_random_sequence(suffix_len)
        )

        if not args.quiet:
            print(f'Generated random amplicon ({amplicon_length}bp) with embedded guide')
            print(f'Guide: {guide}')
            print()
    else:
        amplicon = args.amplicon
        if args.guide is None:
            parser.error('--guide is required when --amplicon is provided')
        guide = args.guide

    # Validate inputs
    try:
        validate_inputs(amplicon, guide, args.edit_rate, args.error_rate)
    except ValueError as e:
        print(f'Error: {e}', file=sys.stderr)
        return 1

    # Generate data
    try:
        generate_synthetic_data(
            amplicon=amplicon,
            guide=guide,
            num_reads=args.num_reads,
            edit_rate=args.edit_rate,
            error_rate=args.error_rate,
            output_prefix=args.output_prefix,
            amplicon_name=args.amplicon_name,
            read_length=args.read_length,
            seed=args.seed,
            cleavage_offset=args.cleavage_offset,
            quiet=args.quiet,
            # Mode and base editing parameters
            mode=args.mode,
            base_editor=args.base_editor,
            window_center=args.window_center,
            window_sigma=args.window_sigma,
            base_edit_prob=args.base_edit_prob,
            # Prime editing parameters
            peg_extension=args.peg_extension,
            peg_scaffold=args.peg_scaffold,
            perfect_edit_fraction=args.perfect_edit_fraction,
            partial_edit_fraction=args.partial_edit_fraction,
            pe_indel_fraction=args.pe_indel_fraction,
            scaffold_incorporation_fraction=args.scaffold_incorporation_fraction,
            flap_indel_fraction=args.flap_indel_fraction,
        )
    except ValueError as e:
        print(f'Error: {e}', file=sys.stderr)
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
