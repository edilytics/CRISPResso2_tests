# Extending syn-gen for Base Editing and Prime Editing

## Overview

Extend syn-gen to support base editing (CBE/ABE) and prime editing synthetic data generation, enabling comprehensive VCF output testing for CRISPResso2's `--vcf_output` feature.

**Current state:** syn-gen supports NHEJ edits (deletions and insertions)

**Goal:** Add support for:
- Base editing (C→T for CBE, A→G for ABE) with realistic activity windows
- Prime editing with pegRNA template specification and realistic outcome distribution

## Command-Line Interface

### New `--mode` flag

```bash
# NHEJ mode (existing, default)
python syn_gen.py --mode nhej -a AMPLICON -g GUIDE ...

# Base editing mode
python syn_gen.py --mode base-edit -a AMPLICON -g GUIDE \
    --base-editor CBE \          # or ABE
    --window-center 6 \          # position from PAM-distal end
    --window-sigma 1.5 \         # spread of activity (std dev)
    ...

# Prime editing mode
python syn_gen.py --mode prime-edit -a AMPLICON -g GUIDE \
    --peg-spacer SPACER_SEQ \
    --peg-extension RT_TEMPLATE \
    --peg-scaffold SCAFFOLD_SEQ \
    --nick-guide NICK_GUIDE \    # optional PE3
    ...
```

Shared parameters work across all modes:
- `--edit-rate` - Fraction of reads with any edit
- `--error-rate` - Sequencing error rate
- `--seed` - Reproducibility

## Base Editing Implementation

### Edit generation for CBE/ABE

1. **Find target bases** - Scan the activity window for editable bases (C for CBE, A for ABE)
2. **Position-weighted selection** - Each target base gets a probability based on Gaussian distribution centered at `window-center` with spread `window-sigma`
3. **Multi-base editing** - Real base editors often edit multiple Cs/As in the window. Model this with a per-base edit probability

### Activity window model

Example for CBE with window center=6, sigma=1.5:
```
Guide:     5'-NNNNNNNNNNNNNNNNNNNN-3' (PAM at 3' end)
Position:     1 2 3 4 5 6 7 8 9 10...
Probability:  .05 .15 .35 .60 .80 1.0 .80 .60 .35 .15
                        ↑ center
```

### New parameters

- `--base-editor {CBE,ABE}` - Editor type
- `--window-center` (default: 6) - Peak activity position
- `--window-sigma` (default: 1.5) - Activity spread
- `--base-edit-prob` (default: 0.5) - Per-eligible-base conversion probability

## Prime Editing Implementation

### Outcome distribution

Based on real PE experiments, edited reads fall into several categories:

| Outcome | Description | Default % of edits |
|---------|-------------|-------------------|
| Perfect edit | Exact RT template incorporation | 60% |
| Partial edit | Incomplete RT (truncated) | 15% |
| Indels at nick | NHEJ at nicking site | 15% |
| Scaffold incorporation | Part of pegRNA scaffold in read | 5% |
| Flap indels | Small indels at 3' flap | 5% |

### Implementation approach

1. **Parse pegRNA** - Extract spacer, RT template, scaffold sequences
2. **Identify edit** - Compare RT template to reference to determine intended changes
3. **Generate outcomes** - Weighted random selection from outcome types above
4. **Apply edit** - Modify amplicon according to selected outcome

### New parameters

- `--peg-spacer` - pegRNA spacer sequence (required for prime-edit mode)
- `--peg-extension` - RT template sequence (required)
- `--peg-scaffold` - Scaffold sequence (default: standard scaffold)
- `--nick-guide` - PE3 nicking guide (optional)
- `--perfect-edit-fraction` (default: 0.6) - Tune outcome distribution

## VCF Output

### Substitution representation

Base editing creates substitutions which need different VCF handling than indels:

```vcf
# Single substitution (C→T at position 85)
AMPLICON  85  .  C  T  .  PASS  AF=0.25

# Multiple substitutions in same read become separate VCF records
AMPLICON  85  .  C  T  .  PASS  AF=0.20
AMPLICON  87  .  C  T  .  PASS  AF=0.15
```

### Prime editing VCF

Perfect prime edits may include multiple change types in one read:

```vcf
# Prime edit: substitution + small insertion
AMPLICON  95  .  A  G      .  PASS  AF=0.30  # substitution from RT
AMPLICON  98  .  C  CTTA   .  PASS  AF=0.30  # insertion from RT
```

### Edit tracking in TSV

Extend the edits TSV to capture multiple edits per read:

```
read_name  edit_type     positions    original    edited
read_1     substitution  85,87        C,C         T,T
read_2     prime_edit    95,98        A,C         G,CTTA
```

## Code Structure

### File organization

Keep everything in syn_gen.py (single file, no external dependencies). New sections:

```python
# =============================================================================
# Base Editing Functions
# =============================================================================
def calculate_window_probabilities(guide_len, center, sigma): ...
def find_editable_bases(seq, start, end, editor_type): ...
def generate_base_edit(amplicon, guide_start, guide_end, editor_type, ...): ...

# =============================================================================
# Prime Editing Functions
# =============================================================================
def parse_peg_rna(spacer, extension, scaffold): ...
def identify_intended_edit(amplicon, peg_extension, cut_site): ...
def generate_prime_edit_outcome(amplicon, intended_edit, outcome_weights): ...
def apply_partial_rt(amplicon, intended_edit, truncation_point): ...
```

### Edit dataclass update

```python
@dataclass
class Edit:
    edit_type: Literal['deletion', 'insertion', 'substitution', 'prime_edit', 'none']
    position: int | list[int]  # Support multiple positions for base editing
    size: int | list[int]
    original_seq: str | list[str]
    edited_seq: str | list[str]
```

## Implementation Steps

### Phase 1: Base editing

1. Add `--mode` flag and `base-edit` option to argument parser
2. Add `substitution` to Edit dataclass
3. Implement `generate_base_edit()` with Gaussian window model
4. Update VCF writer to handle substitutions
5. Update TSV writer for multi-position edits
6. Add integration tests: `vcf-base-edit-cbe`, `vcf-base-edit-abe`

### Phase 2: Prime editing

1. Add `prime-edit` mode and pegRNA parameters
2. Implement pegRNA parsing and intended edit identification
3. Implement outcome distribution (perfect, partial, indels, scaffold)
4. Add `prime_edit` type to Edit dataclass
5. Add integration tests: `vcf-prime-edit-basic`, `vcf-prime-edit-pe3`

### Backwards compatibility

- Default `--mode nhej` preserves existing behavior
- All existing tests continue to pass unchanged
