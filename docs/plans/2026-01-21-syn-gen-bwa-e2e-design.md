# syn-gen BWA End-to-End Testing Design

## Overview

End-to-end test suite that verifies syn-gen's synthetic read generation at base-pair precision using BWA alignment. Instead of comparing with CRISPResso output, we use BWA as an independent verifier to confirm that synthetic reads contain exactly the edits syn-gen claims to have applied.

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌──────────────┐
│  syn-gen    │ ──► │  BWA align  │ ──► │  Verify per  │
│  generate   │     │  to amplicon│     │  read match  │
└─────────────┘     └─────────────┘     └──────────────┘
      │                   │                    │
      ▼                   ▼                    ▼
 _edits.tsv          output.sam          PASS/FAIL
 (ground truth)     (alignments)         + discrepancy report
```

**Inputs:**
- Amplicon sequence (reference)
- Guide sequence
- Test parameters (num_reads, edit_rate, error_rate, mode)

**Outputs from syn-gen:**
- `.fastq` - synthetic reads
- `_edits.tsv` - ground truth per read (edit type, position, size, sequencing errors)

**BWA processing:**
- Index amplicon as a mini reference genome
- Align reads with `bwa mem`
- Parse SAM: CIGAR string (indels) + MD tag (substitutions)

**Verification:**
- For each read, compare BWA's detected edits against syn-gen's ground truth
- Report exact match or detailed mismatch

## BWA Output Parsing

BWA produces SAM format with two key fields for edit detection:

**CIGAR string** - describes alignment structure:
- `M` = match/mismatch (need MD tag to distinguish)
- `D` = deletion from reference
- `I` = insertion to reference
- Example: `50M3D47M` = 50 bases aligned, 3bp deletion, 47 bases aligned

**MD tag** - describes mismatches within M blocks:
- Numbers = matching bases
- Letters = reference base that was substituted
- `^` = deleted bases
- Example: `MD:Z:45A4^CGT47` = match 45, sub at 46 (ref was A), match 4, deleted CGT, match 47

**Parsing implementation:**

```python
@dataclass
class BWAAlignment:
    read_name: str
    ref_start: int  # 0-indexed position on amplicon
    cigar: str
    md_tag: str
    read_seq: str

    def get_deletions(self) -> list[tuple[int, int]]:
        """Return [(position, size), ...] from CIGAR D operations."""

    def get_insertions(self) -> list[tuple[int, str]]:
        """Return [(position, inserted_seq), ...] from CIGAR I + read sequence."""

    def get_substitutions(self) -> list[tuple[int, str, str]]:
        """Return [(position, ref_base, read_base), ...] from MD tag."""
```

Position calculations must account for CIGAR operations shifting coordinates as we walk through the alignment.

## Verification Logic

For each read, compare syn-gen's ground truth against BWA's detected edits:

**Ground truth from `_edits.tsv`:**
```
read_name | edit_type | edit_position | edit_size | original_seq | edited_seq | seq_error_positions | ...
```

**Verification per edit type:**

| Edit Type | syn-gen fields | BWA check |
|-----------|---------------|-----------|
| `deletion` | position, size | CIGAR has `{size}D` at position |
| `insertion` | position, edited_seq | CIGAR has `{len}I` at position, inserted bases match |
| `substitution` | position(s), edited_seq | MD tag shows mismatch at position(s), bases match |
| `prime_edit` | position, original_seq, edited_seq | Combination of above depending on length difference |
| `none` | - | No indels, no mismatches (except seq errors) |

**Sequencing errors** (from `seq_error_positions`, `seq_error_new`):
- Appear as additional substitutions in MD tag
- Must match positions and new bases exactly

**Verification result per read:**

```python
@dataclass
class ReadVerification:
    read_name: str
    passed: bool
    expected_edit: Edit
    expected_seq_errors: list[SequencingError]
    bwa_deletions: list[tuple[int, int]]
    bwa_insertions: list[tuple[int, str]]
    bwa_substitutions: list[tuple[int, str, str]]
    mismatches: list[str]  # Human-readable discrepancy descriptions
```

## Test Interface

**Main verification function:**

```python
def verify_reads_with_bwa(
    amplicon: str,
    fastq_path: str,
    edits_tsv_path: str,
    temp_dir: str,
) -> VerificationResult:
    """
    Align reads with BWA and verify each against ground truth.

    Returns VerificationResult with pass/fail and detailed discrepancies.
    """
```

**VerificationResult:**

```python
@dataclass
class VerificationResult:
    total_reads: int
    passed_reads: int
    failed_reads: int
    failures: list[ReadVerification]  # Only failed reads, with details

    @property
    def all_passed(self) -> bool:
        return self.failed_reads == 0
```

**Failure output example:**
```
FAILED: read_42
  Expected: deletion at pos=92, size=3
  BWA found: deletion at pos=92, size=2
  Mismatch: deletion size differs (expected 3, got 2)
```

## File Organization

```
syn-gen/
├── syn_gen.py          # Existing generator
├── test_syn_gen.py     # Existing unit tests
├── test_e2e.py         # Existing CRISPResso tests
├── test_bwa_e2e.py     # NEW: BWA-based e2e tests
└── bwa_verify.py       # NEW: BWA parsing and verification logic
```

## Dependencies

| Dependency | Purpose | Notes |
|------------|---------|-------|
| `bwa` | Read alignment | Available in conda crispresso environment |
| `pytest` | Test framework | Already present |

Manual CIGAR + MD tag parsing (no pysam dependency).

**BWA availability check:**

```python
@pytest.fixture
def bwa_available():
    result = subprocess.run(["which", "bwa"], capture_output=True)
    if result.returncode != 0:
        pytest.skip("BWA not available in PATH")
```

## Test Coverage

| Test | Purpose |
|------|---------|
| `test_nhej_deletions` | Verify deletions detected correctly |
| `test_nhej_insertions` | Verify insertions detected correctly |
| `test_base_editing_cbe` | Verify C→T substitutions |
| `test_base_editing_abe` | Verify A→G substitutions |
| `test_prime_editing` | Verify complex edits (indels + substitutions) |
| `test_with_sequencing_errors` | Verify errors detected alongside edits |

## Implementation Plan

1. Create `bwa_verify.py` with:
   - `BWAAlignment` dataclass and SAM parser
   - CIGAR parser for deletions/insertions
   - MD tag parser for substitutions
   - `verify_reads_with_bwa()` main function
   - `VerificationResult` and `ReadVerification` dataclasses

2. Create `test_bwa_e2e.py` with:
   - Fixtures for temp directory and BWA availability
   - Test cases for each edit mode
   - Helper to format failure messages

3. Run tests and iterate on edge cases
