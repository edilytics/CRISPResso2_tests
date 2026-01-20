#!/usr/bin/env python3
"""
syn-gen: Synthetic CRISPR NHEJ editing data generator.

Generates synthetic FASTQ files with realistic NHEJ edits for testing CRISPResso2.
"""

import argparse
import gzip
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
    """Represents a single NHEJ edit event."""
    edit_type: Literal['deletion', 'insertion', 'none']
    position: int  # Position in amplicon (0-indexed)
    size: int  # Size of deletion or insertion
    original_seq: str  # Original sequence at edit site
    edited_seq: str  # Resulting sequence (empty for deletion, inserted for insertion)


@dataclass
class EditedRead:
    """A read with its associated edit information."""
    read: FastqRead
    edit: Edit


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
# Sequencing Simulation
# =============================================================================

def add_sequencing_errors(seq: str, error_rate: float) -> str:
    """
    Add random substitution errors to simulate sequencing noise.

    Args:
        seq: Input sequence
        error_rate: Per-base error rate

    Returns:
        Sequence with errors introduced
    """
    if error_rate == 0:
        return seq

    bases = list(seq)
    for i in range(len(bases)):
        if random.random() < error_rate:
            # Substitute with a different base
            current = bases[i]
            alternatives = [b for b in 'ACGT' if b != current.upper()]
            bases[i] = random.choice(alternatives)

    return ''.join(bases)


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
    """Write per-read edit information to TSV."""
    with open(filepath, 'w') as fh:
        # Header
        fh.write('read_name\tedit_type\tedit_position\tedit_size\toriginal_seq\tedited_seq\n')

        for edited_read in reads:
            edit = edited_read.edit
            fh.write(f'{edited_read.read.name}\t{edit.edit_type}\t{edit.position}\t'
                     f'{edit.size}\t{edit.original_seq}\t{edit.edited_seq}\n')


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
    """
    total_reads = len(reads)
    edit_counts: Counter[tuple] = Counter()

    for edited_read in reads:
        edit = edited_read.edit
        if edit.edit_type == 'none':
            continue

        # Create a hashable key for the edit
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
        else:  # insertion
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
    deletion_weight: float = 0.75,
    quiet: bool = False,
) -> dict:
    """
    Main entry point for synthetic data generation.

    Returns dict with summary statistics.
    """
    # Set random seed if provided
    if seed is not None:
        random.seed(seed)

    # Find guide and calculate cut site
    guide_start, guide_end, is_rc = find_guide_in_amplicon(amplicon, guide)
    cut_site = calculate_cut_site(guide_start, guide_end, is_rc, cleavage_offset)

    # Determine read length
    actual_read_length = read_length if read_length else len(amplicon)
    if actual_read_length > len(amplicon):
        actual_read_length = len(amplicon)

    # Generate reads
    reads: list[EditedRead] = []
    deletion_count = 0
    insertion_count = 0

    for i in range(num_reads):
        is_edited = random.random() < edit_rate

        if is_edited:
            edit = generate_edit(cut_site, amplicon, deletion_weight)
            seq = apply_edit(amplicon, edit)
            if edit.edit_type == 'deletion':
                deletion_count += 1
            else:
                insertion_count += 1
        else:
            edit = Edit(edit_type='none', position=0, size=0, original_seq='', edited_seq='')
            seq = amplicon

        # Add sequencing errors
        seq = add_sequencing_errors(seq, error_rate)

        # Create FASTQ read
        qual = generate_quality_string(len(seq))
        fastq_read = FastqRead(name=f'read_{i}', seq=seq, qual=qual)

        reads.append(EditedRead(read=fastq_read, edit=edit))

    # Write outputs
    fastq_path = f'{output_prefix}.fastq'
    tsv_path = f'{output_prefix}_edits.tsv'
    vcf_path = f'{output_prefix}.vcf'

    write_fastq(reads, fastq_path)
    write_edit_tsv(reads, tsv_path)

    variants = aggregate_edits_to_variants(reads, amplicon, amplicon_name)
    write_vcf(variants, amplicon_name, amplicon, vcf_path)

    # Calculate statistics
    edited_count = deletion_count + insertion_count
    unedited_count = num_reads - edited_count

    stats = {
        'total_reads': num_reads,
        'edited_reads': edited_count,
        'unedited_reads': unedited_count,
        'edit_rate_actual': edited_count / num_reads if num_reads > 0 else 0,
        'deletions': deletion_count,
        'insertions': insertion_count,
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
        print(f'Amplicon length: {len(amplicon)} bp')
        print(f'Guide position:  {guide_start}-{guide_end} ({"RC" if is_rc else "FWD"})')
        print(f'Cut site:        {cut_site}')
        print()
        print(f'Total reads:     {num_reads}')
        print(f'Edited reads:    {edited_count} ({100 * edited_count / num_reads:.2f}%)')
        print(f'Unedited reads:  {unedited_count} ({100 * unedited_count / num_reads:.2f}%)')
        if edited_count > 0:
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
        description='Generate synthetic CRISPR NHEJ editing data for testing.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
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
        '--deletion-weight',
        type=float,
        default=0.75,
        help='Probability of deletion vs insertion for edits (0.0=insertions only, 1.0=deletions only)'
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
            deletion_weight=args.deletion_weight,
            quiet=args.quiet,
        )
    except ValueError as e:
        print(f'Error: {e}', file=sys.stderr)
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
