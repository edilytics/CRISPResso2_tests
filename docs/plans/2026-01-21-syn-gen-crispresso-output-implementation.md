# syn-gen CRISPResso-Compatible Output Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refactor syn-gen's allele output to match CRISPResso's detailed alleles table format for direct comparison in e2e testing.

**Architecture:** Add alignment functions that compute aligned sequences with gaps from ground truth edits. Refactor `write_alleles_tsv()` to output CRISPResso-compatible columns. Store aligned sequences in a new `AlignedAllele` dataclass.

**Tech Stack:** Python 3.10+, pytest, no new dependencies

**Reference:** See `docs/plans/2026-01-21-syn-gen-crispresso-output-format-design.md` for detailed design.

---

### Task 1: Add AlignedAllele Dataclass

**Files:**
- Modify: `syn-gen/syn_gen.py:55-64` (after EditedRead class)
- Test: `syn-gen/test_syn_gen.py`

**Step 1: Write the failing test**

Add to `syn-gen/test_syn_gen.py`:

```python
# =============================================================================
# AlignedAllele Tests
# =============================================================================

def test_aligned_allele_dataclass():
    """Test AlignedAllele stores all required fields."""
    from syn_gen import AlignedAllele

    allele = AlignedAllele(
        aligned_sequence='CAGC--CTG',
        reference_sequence='CAGCACCTG',
        all_deletion_positions=[92, 93],
        deletion_coordinates=[(92, 94)],
        deletion_sizes=[2],
        all_insertion_positions=[],
        all_insertion_left_positions=[],
        insertion_coordinates=[],
        insertion_sizes=[],
        all_substitution_positions=[],
        substitution_values=[],
        n_deleted=2,
        n_inserted=0,
        n_mutated=0,
    )

    assert allele.aligned_sequence == 'CAGC--CTG'
    assert allele.n_deleted == 2
    assert allele.read_status == 'MODIFIED'


def test_aligned_allele_unmodified():
    """Test AlignedAllele read_status for unmodified reads."""
    from syn_gen import AlignedAllele

    allele = AlignedAllele(
        aligned_sequence='CAGCACCTG',
        reference_sequence='CAGCACCTG',
        all_deletion_positions=[],
        deletion_coordinates=[],
        deletion_sizes=[],
        all_insertion_positions=[],
        all_insertion_left_positions=[],
        insertion_coordinates=[],
        insertion_sizes=[],
        all_substitution_positions=[],
        substitution_values=[],
        n_deleted=0,
        n_inserted=0,
        n_mutated=0,
    )

    assert allele.read_status == 'UNMODIFIED'
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/cole/code/edilytics/CRISPResso2_tests/.worktrees/syn-gen-e2e/syn-gen && pytest test_syn_gen.py::test_aligned_allele_dataclass -v
```

Expected: FAIL with "cannot import name 'AlignedAllele'"

**Step 3: Write minimal implementation**

Add to `syn-gen/syn_gen.py` after line 64 (after EditedRead class):

```python
@dataclass
class AlignedAllele:
    """Allele with CRISPResso-compatible alignment information."""
    aligned_sequence: str
    reference_sequence: str
    all_deletion_positions: list[int]
    deletion_coordinates: list[tuple[int, int]]
    deletion_sizes: list[int]
    all_insertion_positions: list[int]
    all_insertion_left_positions: list[int]
    insertion_coordinates: list[tuple[int, int]]
    insertion_sizes: list[int]
    all_substitution_positions: list[int]
    substitution_values: list[str]
    n_deleted: int
    n_inserted: int
    n_mutated: int

    @property
    def read_status(self) -> str:
        """Return MODIFIED or UNMODIFIED based on edit counts."""
        if self.n_deleted > 0 or self.n_inserted > 0 or self.n_mutated > 0:
            return 'MODIFIED'
        return 'UNMODIFIED'
```

**Step 4: Run test to verify it passes**

```bash
cd /Users/cole/code/edilytics/CRISPResso2_tests/.worktrees/syn-gen-e2e/syn-gen && pytest test_syn_gen.py::test_aligned_allele_dataclass test_syn_gen.py::test_aligned_allele_unmodified -v
```

Expected: PASS

**Step 5: Commit**

```bash
cd /Users/cole/code/edilytics/CRISPResso2_tests/.worktrees/syn-gen-e2e && git add syn-gen/syn_gen.py syn-gen/test_syn_gen.py && git commit -m "feat(syn-gen): add AlignedAllele dataclass for CRISPResso-compatible output"
```

---

### Task 2: Add create_aligned_deletion Function

**Files:**
- Modify: `syn-gen/syn_gen.py` (add new function in Output Writers section ~line 775)
- Test: `syn-gen/test_syn_gen.py`

**Step 1: Write the failing test**

Add to `syn-gen/test_syn_gen.py`:

```python
# =============================================================================
# Alignment Function Tests
# =============================================================================

def test_create_aligned_deletion_simple():
    """Test aligned sequences for a simple deletion."""
    from syn_gen import create_aligned_deletion

    amplicon = 'CAGCACCTGGATCGC'
    position = 4  # Delete 'AC' at positions 4-5
    size = 2

    aligned_read, aligned_ref = create_aligned_deletion(amplicon, position, size)

    assert aligned_ref == amplicon
    assert aligned_read == 'CAGC--CTGGATCGC'
    assert len(aligned_read) == len(aligned_ref)


def test_create_aligned_deletion_at_start():
    """Test deletion at the start of sequence."""
    from syn_gen import create_aligned_deletion

    amplicon = 'ACGTACGT'
    position = 0
    size = 2

    aligned_read, aligned_ref = create_aligned_deletion(amplicon, position, size)

    assert aligned_ref == amplicon
    assert aligned_read == '--GTACGT'


def test_create_aligned_deletion_at_end():
    """Test deletion at the end of sequence."""
    from syn_gen import create_aligned_deletion

    amplicon = 'ACGTACGT'
    position = 6
    size = 2

    aligned_read, aligned_ref = create_aligned_deletion(amplicon, position, size)

    assert aligned_ref == amplicon
    assert aligned_read == 'ACGTAC--'
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/cole/code/edilytics/CRISPResso2_tests/.worktrees/syn-gen-e2e/syn-gen && pytest test_syn_gen.py::test_create_aligned_deletion_simple -v
```

Expected: FAIL with "cannot import name 'create_aligned_deletion'"

**Step 3: Write minimal implementation**

Add to `syn-gen/syn_gen.py` before `write_fastq` function (~line 778):

```python
# =============================================================================
# Alignment Functions
# =============================================================================

def create_aligned_deletion(amplicon: str, position: int, size: int) -> tuple[str, str]:
    """Create aligned read and reference sequences for a deletion.

    Args:
        amplicon: Reference amplicon sequence
        position: Start position of deletion (0-indexed)
        size: Number of bases deleted

    Returns:
        Tuple of (aligned_read, aligned_reference) with gaps in read
    """
    # The edited sequence has the deletion applied
    edited_seq = amplicon[:position] + amplicon[position + size:]
    # Insert gaps at the deletion site to match reference length
    aligned_read = edited_seq[:position] + '-' * size + edited_seq[position:]
    aligned_ref = amplicon
    return aligned_read, aligned_ref
```

**Step 4: Run test to verify it passes**

```bash
cd /Users/cole/code/edilytics/CRISPResso2_tests/.worktrees/syn-gen-e2e/syn-gen && pytest test_syn_gen.py::test_create_aligned_deletion_simple test_syn_gen.py::test_create_aligned_deletion_at_start test_syn_gen.py::test_create_aligned_deletion_at_end -v
```

Expected: PASS

**Step 5: Commit**

```bash
cd /Users/cole/code/edilytics/CRISPResso2_tests/.worktrees/syn-gen-e2e && git add syn-gen/syn_gen.py syn-gen/test_syn_gen.py && git commit -m "feat(syn-gen): add create_aligned_deletion function"
```

---

### Task 3: Add create_aligned_insertion Function

**Files:**
- Modify: `syn-gen/syn_gen.py`
- Test: `syn-gen/test_syn_gen.py`

**Step 1: Write the failing test**

Add to `syn-gen/test_syn_gen.py`:

```python
def test_create_aligned_insertion_simple():
    """Test aligned sequences for a simple insertion."""
    from syn_gen import create_aligned_insertion

    amplicon = 'CAGCACCTG'
    position = 4  # Insert 'GGG' at position 4
    inserted_seq = 'GGG'

    aligned_read, aligned_ref = create_aligned_insertion(amplicon, position, inserted_seq)

    assert aligned_read == 'CAGCGGGACCTG'
    assert aligned_ref == 'CAGC---ACCTG'
    assert len(aligned_read) == len(aligned_ref)


def test_create_aligned_insertion_at_start():
    """Test insertion at the start of sequence."""
    from syn_gen import create_aligned_insertion

    amplicon = 'ACGTACGT'
    position = 0
    inserted_seq = 'TTT'

    aligned_read, aligned_ref = create_aligned_insertion(amplicon, position, inserted_seq)

    assert aligned_read == 'TTTACGTACGT'
    assert aligned_ref == '---ACGTACGT'


def test_create_aligned_insertion_single_base():
    """Test single base insertion."""
    from syn_gen import create_aligned_insertion

    amplicon = 'CAGCACCTG'
    position = 4
    inserted_seq = 'A'

    aligned_read, aligned_ref = create_aligned_insertion(amplicon, position, inserted_seq)

    assert aligned_read == 'CAGCAACCTG'
    assert aligned_ref == 'CAGC-ACCTG'
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/cole/code/edilytics/CRISPResso2_tests/.worktrees/syn-gen-e2e/syn-gen && pytest test_syn_gen.py::test_create_aligned_insertion_simple -v
```

Expected: FAIL with "cannot import name 'create_aligned_insertion'"

**Step 3: Write minimal implementation**

Add to `syn-gen/syn_gen.py` after `create_aligned_deletion`:

```python
def create_aligned_insertion(amplicon: str, position: int, inserted_seq: str) -> tuple[str, str]:
    """Create aligned read and reference sequences for an insertion.

    Args:
        amplicon: Reference amplicon sequence
        position: Position where insertion occurs (0-indexed)
        inserted_seq: The inserted sequence

    Returns:
        Tuple of (aligned_read, aligned_reference) with gaps in reference
    """
    size = len(inserted_seq)
    # Read has the insertion
    aligned_read = amplicon[:position] + inserted_seq + amplicon[position:]
    # Reference has gaps where insertion occurred
    aligned_ref = amplicon[:position] + '-' * size + amplicon[position:]
    return aligned_read, aligned_ref
```

**Step 4: Run test to verify it passes**

```bash
cd /Users/cole/code/edilytics/CRISPResso2_tests/.worktrees/syn-gen-e2e/syn-gen && pytest test_syn_gen.py::test_create_aligned_insertion_simple test_syn_gen.py::test_create_aligned_insertion_at_start test_syn_gen.py::test_create_aligned_insertion_single_base -v
```

Expected: PASS

**Step 5: Commit**

```bash
cd /Users/cole/code/edilytics/CRISPResso2_tests/.worktrees/syn-gen-e2e && git add syn-gen/syn_gen.py syn-gen/test_syn_gen.py && git commit -m "feat(syn-gen): add create_aligned_insertion function"
```

---

### Task 4: Add create_aligned_substitution Function

**Files:**
- Modify: `syn-gen/syn_gen.py`
- Test: `syn-gen/test_syn_gen.py`

**Step 1: Write the failing test**

Add to `syn-gen/test_syn_gen.py`:

```python
def test_create_aligned_substitution_single():
    """Test aligned sequences for a single substitution."""
    from syn_gen import create_aligned_substitution

    amplicon = 'ACGTACGT'
    positions = [2]
    new_bases = ['T']

    aligned_read, aligned_ref = create_aligned_substitution(amplicon, positions, new_bases)

    assert aligned_read == 'ACTTACGT'
    assert aligned_ref == amplicon
    assert len(aligned_read) == len(aligned_ref)


def test_create_aligned_substitution_multiple():
    """Test aligned sequences for multiple substitutions."""
    from syn_gen import create_aligned_substitution

    amplicon = 'ACGTACGT'
    positions = [0, 4]
    new_bases = ['T', 'T']

    aligned_read, aligned_ref = create_aligned_substitution(amplicon, positions, new_bases)

    assert aligned_read == 'TCGTTCGT'
    assert aligned_ref == amplicon
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/cole/code/edilytics/CRISPResso2_tests/.worktrees/syn-gen-e2e/syn-gen && pytest test_syn_gen.py::test_create_aligned_substitution_single -v
```

Expected: FAIL with "cannot import name 'create_aligned_substitution'"

**Step 3: Write minimal implementation**

Add to `syn-gen/syn_gen.py` after `create_aligned_insertion`:

```python
def create_aligned_substitution(amplicon: str, positions: list[int], new_bases: list[str]) -> tuple[str, str]:
    """Create aligned read and reference sequences for substitution(s).

    Args:
        amplicon: Reference amplicon sequence
        positions: List of positions with substitutions (0-indexed)
        new_bases: List of new bases at those positions

    Returns:
        Tuple of (aligned_read, aligned_reference) - no gaps, same length
    """
    seq = list(amplicon)
    for pos, base in zip(positions, new_bases):
        seq[pos] = base
    aligned_read = ''.join(seq)
    aligned_ref = amplicon
    return aligned_read, aligned_ref
```

**Step 4: Run test to verify it passes**

```bash
cd /Users/cole/code/edilytics/CRISPResso2_tests/.worktrees/syn-gen-e2e/syn-gen && pytest test_syn_gen.py::test_create_aligned_substitution_single test_syn_gen.py::test_create_aligned_substitution_multiple -v
```

Expected: PASS

**Step 5: Commit**

```bash
cd /Users/cole/code/edilytics/CRISPResso2_tests/.worktrees/syn-gen-e2e && git add syn-gen/syn_gen.py syn-gen/test_syn_gen.py && git commit -m "feat(syn-gen): add create_aligned_substitution function"
```

---

### Task 5: Add create_aligned_prime_edit Function

**Files:**
- Modify: `syn-gen/syn_gen.py`
- Test: `syn-gen/test_syn_gen.py`

**Step 1: Write the failing test**

Add to `syn-gen/test_syn_gen.py`:

```python
def test_create_aligned_prime_edit_substitution():
    """Test prime edit with same-length replacement (substitution)."""
    from syn_gen import create_aligned_prime_edit

    amplicon = 'ACGTACGTACGT'
    position = 4
    original = 'ACG'
    edited = 'TTT'

    aligned_read, aligned_ref = create_aligned_prime_edit(amplicon, position, original, edited)

    assert aligned_read == 'ACGTTTTACGT'
    assert aligned_ref == amplicon
    assert len(aligned_read) == len(aligned_ref)


def test_create_aligned_prime_edit_insertion():
    """Test prime edit with net insertion (edited longer than original)."""
    from syn_gen import create_aligned_prime_edit

    amplicon = 'ACGTACGTACGT'
    position = 4
    original = 'ACG'
    edited = 'TTTTT'  # 2 more bases

    aligned_read, aligned_ref = create_aligned_prime_edit(amplicon, position, original, edited)

    assert aligned_read == 'ACGTTTTTTACGT'
    assert aligned_ref == 'ACGTACG--ACGT'
    assert len(aligned_read) == len(aligned_ref)


def test_create_aligned_prime_edit_deletion():
    """Test prime edit with net deletion (edited shorter than original)."""
    from syn_gen import create_aligned_prime_edit

    amplicon = 'ACGTACGTACGT'
    position = 4
    original = 'ACGT'
    edited = 'TT'  # 2 fewer bases

    aligned_read, aligned_ref = create_aligned_prime_edit(amplicon, position, original, edited)

    assert aligned_read == 'ACGTTT--ACGT'
    assert aligned_ref == amplicon
    assert len(aligned_read) == len(aligned_ref)
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/cole/code/edilytics/CRISPResso2_tests/.worktrees/syn-gen-e2e/syn-gen && pytest test_syn_gen.py::test_create_aligned_prime_edit_substitution -v
```

Expected: FAIL with "cannot import name 'create_aligned_prime_edit'"

**Step 3: Write minimal implementation**

Add to `syn-gen/syn_gen.py` after `create_aligned_substitution`:

```python
def create_aligned_prime_edit(amplicon: str, position: int, original: str, edited: str) -> tuple[str, str]:
    """Create aligned read and reference sequences for a prime edit.

    Args:
        amplicon: Reference amplicon sequence
        position: Position where edit starts (0-indexed)
        original: Original sequence at edit site
        edited: Edited sequence (may differ in length)

    Returns:
        Tuple of (aligned_read, aligned_reference) with appropriate gaps
    """
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

**Step 4: Run test to verify it passes**

```bash
cd /Users/cole/code/edilytics/CRISPResso2_tests/.worktrees/syn-gen-e2e/syn-gen && pytest test_syn_gen.py::test_create_aligned_prime_edit_substitution test_syn_gen.py::test_create_aligned_prime_edit_insertion test_syn_gen.py::test_create_aligned_prime_edit_deletion -v
```

Expected: PASS

**Step 5: Commit**

```bash
cd /Users/cole/code/edilytics/CRISPResso2_tests/.worktrees/syn-gen-e2e && git add syn-gen/syn_gen.py syn-gen/test_syn_gen.py && git commit -m "feat(syn-gen): add create_aligned_prime_edit function"
```

---

### Task 6: Add edit_to_aligned_allele Function

**Files:**
- Modify: `syn-gen/syn_gen.py`
- Test: `syn-gen/test_syn_gen.py`

**Step 1: Write the failing test**

Add to `syn-gen/test_syn_gen.py`:

```python
def test_edit_to_aligned_allele_deletion():
    """Test converting a deletion Edit to AlignedAllele."""
    from syn_gen import edit_to_aligned_allele, Edit, AlignedAllele

    amplicon = 'ACGTACGTACGT'
    edit = Edit(
        edit_type='deletion',
        position=4,
        size=2,
        original_seq='AC',
        edited_seq='',
    )

    allele = edit_to_aligned_allele(amplicon, edit, sequencing_errors=[])

    assert allele.aligned_sequence == 'ACGT--GTACGT'
    assert allele.reference_sequence == amplicon
    assert allele.all_deletion_positions == [4, 5]
    assert allele.deletion_coordinates == [(4, 6)]
    assert allele.deletion_sizes == [2]
    assert allele.n_deleted == 2
    assert allele.n_inserted == 0
    assert allele.read_status == 'MODIFIED'


def test_edit_to_aligned_allele_insertion():
    """Test converting an insertion Edit to AlignedAllele."""
    from syn_gen import edit_to_aligned_allele, Edit

    amplicon = 'ACGTACGT'
    edit = Edit(
        edit_type='insertion',
        position=4,
        size=3,
        original_seq='',
        edited_seq='GGG',
    )

    allele = edit_to_aligned_allele(amplicon, edit, sequencing_errors=[])

    assert allele.aligned_sequence == 'ACGTGGGACGT'
    assert allele.reference_sequence == 'ACGT---ACGT'
    assert allele.all_insertion_positions == [3, 4]
    assert allele.all_insertion_left_positions == [3]
    assert allele.insertion_coordinates == [(3, 4)]
    assert allele.insertion_sizes == [3]
    assert allele.n_inserted == 3


def test_edit_to_aligned_allele_none():
    """Test converting a 'none' Edit to AlignedAllele."""
    from syn_gen import edit_to_aligned_allele, Edit

    amplicon = 'ACGTACGT'
    edit = Edit(
        edit_type='none',
        position=0,
        size=0,
        original_seq='',
        edited_seq='',
    )

    allele = edit_to_aligned_allele(amplicon, edit, sequencing_errors=[])

    assert allele.aligned_sequence == amplicon
    assert allele.reference_sequence == amplicon
    assert allele.all_deletion_positions == []
    assert allele.all_insertion_positions == []
    assert allele.read_status == 'UNMODIFIED'
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/cole/code/edilytics/CRISPResso2_tests/.worktrees/syn-gen-e2e/syn-gen && pytest test_syn_gen.py::test_edit_to_aligned_allele_deletion -v
```

Expected: FAIL with "cannot import name 'edit_to_aligned_allele'"

**Step 3: Write minimal implementation**

Add to `syn-gen/syn_gen.py` after `create_aligned_prime_edit`:

```python
def edit_to_aligned_allele(
    amplicon: str,
    edit: Edit,
    sequencing_errors: list[SequencingError],
) -> AlignedAllele:
    """Convert an Edit and sequencing errors to an AlignedAllele.

    Args:
        amplicon: Reference amplicon sequence
        edit: The Edit object describing the intentional edit
        sequencing_errors: List of sequencing errors applied after the edit

    Returns:
        AlignedAllele with CRISPResso-compatible alignment and coordinates
    """
    # Initialize coordinate lists
    all_del_positions = []
    del_coordinates = []
    del_sizes = []
    all_ins_positions = []
    all_ins_left_positions = []
    ins_coordinates = []
    ins_sizes = []
    all_sub_positions = []
    sub_values = []

    # Handle the edit based on type
    if edit.edit_type == 'none':
        aligned_read = amplicon
        aligned_ref = amplicon

    elif edit.edit_type == 'deletion':
        pos = edit.position
        size = edit.size
        aligned_read, aligned_ref = create_aligned_deletion(amplicon, pos, size)
        all_del_positions = list(range(pos, pos + size))
        del_coordinates = [(pos, pos + size)]
        del_sizes = [size]

    elif edit.edit_type == 'insertion':
        pos = edit.position
        size = len(edit.edited_seq)
        aligned_read, aligned_ref = create_aligned_insertion(amplicon, pos, edit.edited_seq)
        # CRISPResso uses flanking positions: [left_pos, right_pos]
        left_pos = pos - 1 if pos > 0 else 0
        all_ins_positions = [left_pos, pos]
        all_ins_left_positions = [left_pos]
        ins_coordinates = [(left_pos, pos)]
        ins_sizes = [size]

    elif edit.edit_type == 'substitution':
        # Handle single or multiple substitutions
        if isinstance(edit.position, list):
            positions = edit.position
            new_bases = edit.edited_seq
        else:
            positions = [edit.position]
            new_bases = [edit.edited_seq]

        aligned_read, aligned_ref = create_aligned_substitution(amplicon, positions, new_bases)
        all_sub_positions = positions
        sub_values = new_bases

    elif edit.edit_type == 'prime_edit':
        pos = edit.position
        original = edit.original_seq
        edited = edit.edited_seq
        aligned_read, aligned_ref = create_aligned_prime_edit(amplicon, pos, original, edited)

        len_diff = len(edited) - len(original)
        if len_diff > 0:
            # Net insertion
            left_pos = pos - 1 if pos > 0 else 0
            all_ins_positions = [left_pos, pos]
            all_ins_left_positions = [left_pos]
            ins_coordinates = [(left_pos, pos)]
            ins_sizes = [len_diff]
        elif len_diff < 0:
            # Net deletion
            del_size = abs(len_diff)
            del_start = pos + len(edited)
            all_del_positions = list(range(del_start, del_start + del_size))
            del_coordinates = [(del_start, del_start + del_size)]
            del_sizes = [del_size]

        # Check for substitutions within the edited region
        for i, (o, e) in enumerate(zip(original, edited)):
            if o != e:
                all_sub_positions.append(pos + i)
                sub_values.append(e)

    else:
        raise ValueError(f"Unknown edit type: {edit.edit_type}")

    # Add sequencing errors as substitutions
    # Note: sequencing error positions are in the edited read coordinates
    # For now, we add them directly (coordinate conversion can be added later)
    for seq_error in sequencing_errors:
        all_sub_positions.append(seq_error.position)
        sub_values.append(seq_error.error_base)

    # Calculate totals
    n_deleted = sum(del_sizes)
    n_inserted = sum(ins_sizes)
    n_mutated = len(all_sub_positions)

    return AlignedAllele(
        aligned_sequence=aligned_read,
        reference_sequence=aligned_ref,
        all_deletion_positions=all_del_positions,
        deletion_coordinates=del_coordinates,
        deletion_sizes=del_sizes,
        all_insertion_positions=all_ins_positions,
        all_insertion_left_positions=all_ins_left_positions,
        insertion_coordinates=ins_coordinates,
        insertion_sizes=ins_sizes,
        all_substitution_positions=all_sub_positions,
        substitution_values=sub_values,
        n_deleted=n_deleted,
        n_inserted=n_inserted,
        n_mutated=n_mutated,
    )
```

**Step 4: Run test to verify it passes**

```bash
cd /Users/cole/code/edilytics/CRISPResso2_tests/.worktrees/syn-gen-e2e/syn-gen && pytest test_syn_gen.py::test_edit_to_aligned_allele_deletion test_syn_gen.py::test_edit_to_aligned_allele_insertion test_syn_gen.py::test_edit_to_aligned_allele_none -v
```

Expected: PASS

**Step 5: Commit**

```bash
cd /Users/cole/code/edilytics/CRISPResso2_tests/.worktrees/syn-gen-e2e && git add syn-gen/syn_gen.py syn-gen/test_syn_gen.py && git commit -m "feat(syn-gen): add edit_to_aligned_allele function"
```

---

### Task 7: Refactor write_alleles_tsv to Use New Format

**Files:**
- Modify: `syn-gen/syn_gen.py:834-963` (replace `write_alleles_tsv`)
- Test: `syn-gen/test_syn_gen.py`

**Step 1: Write the failing test**

Add to `syn-gen/test_syn_gen.py`:

```python
import tempfile
import os

def test_write_alleles_tsv_crispresso_format():
    """Test that write_alleles_tsv outputs CRISPResso-compatible format."""
    from syn_gen import write_alleles_tsv, EditedRead, FastqRead, Edit

    amplicon = 'ACGTACGTACGT'
    reads = [
        EditedRead(
            read=FastqRead(name='read_0', seq='ACGT--GTACGT'.replace('-', ''), qual='I' * 10),
            edit=Edit(edit_type='deletion', position=4, size=2, original_seq='AC', edited_seq=''),
        ),
        EditedRead(
            read=FastqRead(name='read_1', seq='ACGT--GTACGT'.replace('-', ''), qual='I' * 10),
            edit=Edit(edit_type='deletion', position=4, size=2, original_seq='AC', edited_seq=''),
        ),
    ]

    with tempfile.NamedTemporaryFile(mode='w', suffix='.tsv', delete=False) as f:
        filepath = f.name

    try:
        write_alleles_tsv(reads, amplicon, filepath)

        with open(filepath) as f:
            lines = f.readlines()

        # Check header
        header = lines[0].strip().split('\t')
        assert '#Reads' in header
        assert 'Aligned_Sequence' in header
        assert 'Reference_Sequence' in header
        assert 'all_deletion_positions' in header
        assert 'deletion_coordinates' in header
        assert 'deletion_sizes' in header
        assert 'n_deleted' in header
        assert 'Read_Status' in header

        # Check data row
        data = lines[1].strip().split('\t')
        assert data[0] == '2'  # 2 reads with same sequence
        assert '--' in data[1]  # Aligned_Sequence has gaps

    finally:
        os.unlink(filepath)
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/cole/code/edilytics/CRISPResso2_tests/.worktrees/syn-gen-e2e/syn-gen && pytest test_syn_gen.py::test_write_alleles_tsv_crispresso_format -v
```

Expected: FAIL (signature mismatch or wrong columns)

**Step 3: Write minimal implementation**

Replace `write_alleles_tsv` in `syn-gen/syn_gen.py` (lines 834-963):

```python
def write_alleles_tsv(reads: list[EditedRead], amplicon: str, filepath: str) -> None:
    """Write per-allele aggregated edit info matching CRISPResso format.

    Groups reads by aligned sequence, aggregates counts, outputs CRISPResso-compatible
    columns for direct comparison with Alleles_frequency_table output.

    Args:
        reads: List of EditedRead objects
        amplicon: Reference amplicon sequence
        filepath: Output file path
    """
    from collections import defaultdict

    # Convert each read to aligned allele and group by aligned sequence
    allele_groups: dict[str, tuple[AlignedAllele, int]] = {}

    for edited_read in reads:
        allele = edit_to_aligned_allele(
            amplicon,
            edited_read.edit,
            edited_read.sequencing_errors,
        )
        key = allele.aligned_sequence
        if key in allele_groups:
            existing_allele, count = allele_groups[key]
            allele_groups[key] = (existing_allele, count + 1)
        else:
            allele_groups[key] = (allele, 1)

    # Sort by count descending
    sorted_alleles = sorted(allele_groups.values(), key=lambda x: -x[1])

    with open(filepath, 'w') as fh:
        # Header matching CRISPResso's detailed allele table columns
        fh.write('#Reads\tAligned_Sequence\tReference_Sequence\t'
                 'n_inserted\tn_deleted\tn_mutated\tRead_Status\t'
                 'all_insertion_positions\tall_insertion_left_positions\t'
                 'insertion_coordinates\tinsertion_sizes\t'
                 'all_deletion_positions\tdeletion_coordinates\tdeletion_sizes\t'
                 'all_substitution_positions\tsubstitution_values\n')

        for allele, count in sorted_alleles:
            fh.write(f'{count}\t'
                     f'{allele.aligned_sequence}\t'
                     f'{allele.reference_sequence}\t'
                     f'{allele.n_inserted}\t'
                     f'{allele.n_deleted}\t'
                     f'{allele.n_mutated}\t'
                     f'{allele.read_status}\t'
                     f'{allele.all_insertion_positions}\t'
                     f'{allele.all_insertion_left_positions}\t'
                     f'{allele.insertion_coordinates}\t'
                     f'{allele.insertion_sizes}\t'
                     f'{allele.all_deletion_positions}\t'
                     f'{allele.deletion_coordinates}\t'
                     f'{allele.deletion_sizes}\t'
                     f'{allele.all_substitution_positions}\t'
                     f'{allele.substitution_values}\n')
```

**Step 4: Run test to verify it passes**

```bash
cd /Users/cole/code/edilytics/CRISPResso2_tests/.worktrees/syn-gen-e2e/syn-gen && pytest test_syn_gen.py::test_write_alleles_tsv_crispresso_format -v
```

Expected: PASS

**Step 5: Commit**

```bash
cd /Users/cole/code/edilytics/CRISPResso2_tests/.worktrees/syn-gen-e2e && git add syn-gen/syn_gen.py syn-gen/test_syn_gen.py && git commit -m "refactor(syn-gen): update write_alleles_tsv to CRISPResso-compatible format"
```

---

### Task 8: Update generate_synthetic_data to Pass Amplicon to write_alleles_tsv

**Files:**
- Modify: `syn-gen/syn_gen.py` (find call to `write_alleles_tsv` in `generate_synthetic_data`)
- Test: Run existing tests

**Step 1: Find and update the call**

Search for `write_alleles_tsv` call in `generate_synthetic_data` function and add the `amplicon` argument.

**Step 2: Run existing tests to verify nothing breaks**

```bash
cd /Users/cole/code/edilytics/CRISPResso2_tests/.worktrees/syn-gen-e2e/syn-gen && pytest test_syn_gen.py -v --tb=short
```

Expected: All tests PASS

**Step 3: Commit**

```bash
cd /Users/cole/code/edilytics/CRISPResso2_tests/.worktrees/syn-gen-e2e && git add syn-gen/syn_gen.py && git commit -m "fix(syn-gen): pass amplicon to write_alleles_tsv"
```

---

### Task 9: Add E2E Comparison Test

**Files:**
- Modify: `syn-gen/test_e2e.py`
- Test: Run the e2e test

**Step 1: Write the e2e comparison test**

Add to `syn-gen/test_e2e.py`:

```python
import subprocess
import tempfile
import pandas as pd
from pathlib import Path

def test_syn_gen_crispresso_deletion_coordinates_match():
    """E2E test: verify syn-gen and CRISPResso report same deletion coordinates."""
    amplicon = 'CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG'
    guide = 'GGAATCCCTTCTGCAGCACC'

    with tempfile.TemporaryDirectory() as tmpdir:
        prefix = f'{tmpdir}/test'

        # Generate synthetic data with deletions only
        from syn_gen import generate_synthetic_data
        generate_synthetic_data(
            amplicon=amplicon,
            guide=guide,
            num_reads=50,
            edit_rate=1.0,
            error_rate=0,
            output_prefix=prefix,
            seed=42,
            mode='nhej',
            quiet=True,
        )

        # Run CRISPResso
        result = subprocess.run([
            'CRISPResso',
            '-r1', f'{prefix}.fastq',
            '-a', amplicon,
            '-g', guide,
            '--write_detailed_allele_table',
            '-o', tmpdir,
            '-n', 'crispresso_test',
            '--suppress_plots',
        ], capture_output=True, text=True, timeout=120)

        if result.returncode != 0:
            print(result.stderr)
        assert result.returncode == 0 or 'allele_frequency_files' in result.stderr

        # Read syn-gen output
        syngen_df = pd.read_csv(f'{prefix}_alleles.tsv', sep='\t')

        # Read CRISPResso output
        crispresso_dir = Path(tmpdir) / 'CRISPResso_on_crispresso_test'
        import zipfile
        with zipfile.ZipFile(crispresso_dir / 'Alleles_frequency_table.zip', 'r') as z:
            z.extractall(crispresso_dir)
        crisp_df = pd.read_csv(crispresso_dir / 'Alleles_frequency_table.txt', sep='\t')

        # Compare: for each syn-gen allele, find matching CRISPResso allele
        # Match by sequence (removing gaps from CRISPResso)
        for _, syngen_row in syngen_df.iterrows():
            syngen_seq_no_gaps = syngen_row['Aligned_Sequence'].replace('-', '')

            # Find matching CRISPResso row
            for _, crisp_row in crisp_df.iterrows():
                crisp_seq_no_gaps = crisp_row['Aligned_Sequence'].replace('-', '')
                if crisp_seq_no_gaps == syngen_seq_no_gaps:
                    # Compare deletion positions
                    syngen_del = syngen_row['all_deletion_positions']
                    crisp_del = crisp_row['all_deletion_positions']
                    assert str(syngen_del) == str(crisp_del), \
                        f"Deletion mismatch: syn-gen={syngen_del}, CRISPResso={crisp_del}"
                    break
```

**Step 2: Run the e2e test**

```bash
cd /Users/cole/code/edilytics/CRISPResso2_tests/.worktrees/syn-gen-e2e/syn-gen && pytest test_e2e.py::test_syn_gen_crispresso_deletion_coordinates_match -v --timeout=180
```

Expected: PASS (or identify coordinate mismatches to debug)

**Step 3: Commit**

```bash
cd /Users/cole/code/edilytics/CRISPResso2_tests/.worktrees/syn-gen-e2e && git add syn-gen/test_e2e.py && git commit -m "test(syn-gen): add e2e comparison test for deletion coordinates"
```

---

### Task 10: Final Verification - Run All Tests

**Step 1: Run all syn-gen tests**

```bash
cd /Users/cole/code/edilytics/CRISPResso2_tests/.worktrees/syn-gen-e2e/syn-gen && pytest test_syn_gen.py test_e2e.py -v --tb=short
```

Expected: All PASS

**Step 2: Commit any final fixes**

```bash
cd /Users/cole/code/edilytics/CRISPResso2_tests/.worktrees/syn-gen-e2e && git status
```

**Step 3: Push to remote**

```bash
cd /Users/cole/code/edilytics/CRISPResso2_tests/.worktrees/syn-gen-e2e && git push origin feature/syn-gen-e2e
```
