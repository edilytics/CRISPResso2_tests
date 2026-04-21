# syn-gen CRISPResso-Compatible Output Format Design

## Overview

Refactor syn-gen's allele output to match CRISPResso's detailed alleles table format. This enables direct comparison between syn-gen's ground truth and CRISPResso's detected edits for end-to-end testing.

## Background

syn-gen generates synthetic CRISPR editing data with known edits. CRISPResso analyzes sequencing data and reports detected edits. For e2e testing, we need to verify CRISPResso correctly detects the edits syn-gen applied.

**Current problem:** syn-gen and CRISPResso output different formats:
- syn-gen: final sequences without gaps, custom column names
- CRISPResso: aligned sequences with gaps, specific coordinate formats

**Solution:** Refactor syn-gen to output in CRISPResso's format for direct comparison.

## Coordinate System

Both tools use **0-indexed reference positions**. Verified by experiment:
- syn-gen deletion at position 92, size 2 → `all_deletion_positions: [92, 93]`
- CRISPResso detects same → `all_deletion_positions: [92, 93]`

## Aligned Sequence Representation

### Deletions

Read gets gaps where bases were deleted:

```
Reference: CAGCACCTG
Read:      CAGC--CTG  (2bp deletion at positions 92-93)
```

**Computation:**
```python
def create_aligned_deletion(amplicon: str, position: int, size: int) -> tuple[str, str]:
    edited_seq = amplicon[:position] + amplicon[position + size:]
    aligned_read = edited_seq[:position] + '-' * size + edited_seq[position:]
    aligned_ref = amplicon
    return aligned_read, aligned_ref
```

### Insertions

Reference gets gaps where bases were inserted:

```
Reference: CAGC---ACCTG  (3bp insertion between positions 91-92)
Read:      CAGCGGGACCTG
```

**Computation:**
```python
def create_aligned_insertion(amplicon: str, position: int, inserted_seq: str) -> tuple[str, str]:
    size = len(inserted_seq)
    aligned_read = amplicon[:position] + inserted_seq + amplicon[position:]
    aligned_ref = amplicon[:position] + '-' * size + amplicon[position:]
    return aligned_read, aligned_ref
```

### Substitutions

No gaps - same length sequences:

```
Reference: ACGCACG
Read:      ATGTATG  (C→T substitutions)
```

**Computation:**
```python
def create_aligned_substitution(amplicon: str, positions: list[int], new_bases: list[str]) -> tuple[str, str]:
    seq = list(amplicon)
    for pos, base in zip(positions, new_bases):
        seq[pos] = base
    aligned_read = ''.join(seq)
    aligned_ref = amplicon
    return aligned_read, aligned_ref
```

### Prime Edits

Prime edits replace `original_seq` with `edited_seq` at the cut site. Alignment depends on length difference:

| Scenario | Length diff | Gaps in |
|----------|-------------|---------|
| Substitution only | 0 | Neither |
| Net insertion | > 0 | Reference |
| Net deletion | < 0 | Read |

**Computation:**
```python
def create_aligned_prime_edit(amplicon: str, position: int, original: str, edited: str) -> tuple[str, str]:
    len_diff = len(edited) - len(original)

    if len_diff == 0:
        # Pure substitution - no gaps
        aligned_read = amplicon[:position] + edited + amplicon[position + len(original):]
        aligned_ref = amplicon
    elif len_diff > 0:
        # Net insertion - reference gets gaps
        aligned_read = amplicon[:position] + edited + amplicon[position + len(original):]
        aligned_ref = amplicon[:position] + original + '-' * len_diff + amplicon[position + len(original):]
    else:
        # Net deletion - read gets gaps
        gap_size = abs(len_diff)
        edited_padded = edited + '-' * gap_size
        aligned_read = amplicon[:position] + edited_padded + amplicon[position + len(original):]
        aligned_ref = amplicon

    return aligned_read, aligned_ref
```

## Output Columns

### Deletion Columns

| Column | Example | Computation |
|--------|---------|-------------|
| `all_deletion_positions` | `[92, 93]` | `list(range(position, position + size))` |
| `deletion_coordinates` | `[(92, 94)]` | `[(position, position + size)]` |
| `deletion_sizes` | `[2]` | `[size]` |

### Insertion Columns

| Column | Example | Computation |
|--------|---------|-------------|
| `all_insertion_positions` | `[91, 92]` | `[position - 1, position]` (flanking positions) |
| `all_insertion_left_positions` | `[91]` | `[position - 1]` |
| `insertion_coordinates` | `[(91, 92)]` | `[(position - 1, position)]` |
| `insertion_sizes` | `[3]` | `[len(inserted_seq)]` |

### Substitution Columns

| Column | Example | Computation |
|--------|---------|-------------|
| `all_substitution_positions` | `[85, 87, 89]` | List of substituted positions |
| `substitution_values` | `['T', 'T', 'T']` | List of new bases |

## Sequencing Errors

Sequencing errors are substitutions applied after the edit. Their positions must be converted from edited-read coordinates to reference coordinates:

```python
def seq_error_to_ref_position(error_pos: int, edit: Edit) -> int:
    if edit.edit_type == 'deletion':
        if error_pos >= edit.position:
            return error_pos + edit.size
        return error_pos
    elif edit.edit_type == 'insertion':
        if error_pos >= edit.position + len(edit.edited_seq):
            return error_pos - len(edit.edited_seq)
        elif error_pos >= edit.position:
            return edit.position  # Error in inserted bases
        return error_pos
    else:
        return error_pos
```

Sequencing errors appear as additional entries in `all_substitution_positions` and `substitution_values`.

## Output File Format

**File:** `{output_prefix}_alleles.tsv`

**Columns (matching CRISPResso):**

```
#Reads
Aligned_Sequence
Reference_Sequence
n_inserted
n_deleted
n_mutated
Read_Status
ref_positions
all_insertion_positions
all_insertion_left_positions
insertion_coordinates
insertion_sizes
all_deletion_positions
deletion_coordinates
deletion_sizes
all_substitution_positions
substitution_values
```

**Grouping:** Reads grouped by identical `Aligned_Sequence`.

**Read_Status:**
- `MODIFIED`: Any edit or sequencing error
- `UNMODIFIED`: No changes from reference

## Comparison Strategy

For e2e testing, compare syn-gen and CRISPResso outputs by:

1. Match alleles by `Aligned_Sequence` (with gaps removed for matching)
2. Compare `#Reads` counts
3. Compare coordinate arrays: `all_deletion_positions`, `all_insertion_positions`, `all_substitution_positions`
4. Verify `deletion_sizes`, `insertion_sizes` match

## Implementation Plan

1. Add `create_aligned_*` functions for each edit type
2. Add coordinate computation functions
3. Refactor `write_alleles_tsv()` to output CRISPResso-compatible format
4. Update `EditedRead` to store aligned sequences
5. Add tests comparing syn-gen output to CRISPResso output

## Files to Modify

| File | Changes |
|------|---------|
| `syn-gen/syn_gen.py` | Add alignment functions, refactor output |
| `syn-gen/test_e2e.py` | Add comparison tests |
