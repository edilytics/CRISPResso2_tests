# syn-gen End-to-End Testing Design

## Overview

Add automated end-to-end tests for the syn-gen package that verify CRISPResso correctly detects the synthetic edits. Tests will run in GitHub Actions on each push.

## Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   syn-gen   │───▶│ CRISPResso  │───▶│   Verify    │
│  (generate) │    │   (run)     │    │  (compare)  │
└─────────────┘    └─────────────┘    └─────────────┘
     │                   │                   │
     ▼                   ▼                   ▼
  FASTQ +            Output dir         Assert edits
  ground truth       with allele        match ground
  TSV                tables             truth
```

### Test File Location

`syn-gen/test_e2e.py`

### Test Classes

- `TestNHEJEndToEnd` - deletions and insertions
- `TestBaseEditingEndToEnd` - CBE/ABE substitutions
- `TestPrimeEditingEndToEnd` - pegRNA-templated edits

## Validation Strategy

### Data Source

Parse `Alleles_frequency_table.zip` from CRISPResso output. This contains full sequences and all identified edits.

### Comparison Against Ground Truth

Compare CRISPResso's detected edits against syn-gen's `*_edits.tsv` file which contains the exact edits applied to each read.

### Mode-Specific Validation

**NHEJ (deletions/insertions):**
- Extract each read's aligned sequence from allele table
- Verify deletion positions/sizes and insertion sequences match ground truth
- Key columns: `Aligned_Sequence`, `Reference_Sequence`, `n_deleted`, `n_inserted`

**Base Editing (CBE/ABE):**
- Look for substitutions at expected positions in the quantification window
- Verify the substitution pattern matches (C→T for CBE, A→G for ABE)
- Account for multi-base edits within the activity window

**Prime Editing:**
- Use CRISPResso's prime editing mode with `--prime_editing_pegRNA_*` flags
- Verify RT template incorporation is detected correctly
- Check perfect edits show the expected sequence change at cut site

### Error Handling

- Set `error_rate=0` in syn-gen to eliminate sequencing noise
- Use random seeds (logged for reproducibility) to catch edge cases over time

## Test Parameters

| Mode | Reads | Edit Rate | Key CRISPResso Flags |
|------|-------|-----------|---------------------|
| NHEJ | 1000 | 50% | `--quantification_window_size 20`, `--write_detailed_allele_table` |
| Base Edit (CBE) | 1000 | 50% | `--base_editor_output`, `-w 20`, `--write_detailed_allele_table` |
| Base Edit (ABE) | 1000 | 50% | `--base_editor_output`, `-w 20`, `--write_detailed_allele_table` |
| Prime Edit | 1000 | 50% | `--prime_editing_pegRNA_*`, `--write_detailed_allele_table` |

### Shared Test Amplicon

```
CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG
```

### Guide Sequence

`GGAATCCCTTCTGCAGCACC`

## Test Cases

Each mode will have:

1. `test_basic_<mode>` - Standard case, verify edits detected
2. `test_unedited_reads` - Verify unedited reads classified correctly
3. `test_edit_positions` - Verify edit locations match ground truth

### Validation Assertions

- Total read count matches
- Edited vs unedited classification accuracy > 95%
- For edited reads: edit type and position match ground truth

## Random Seed Handling

```python
@pytest.fixture
def random_seed(request):
    """Generate random seed, log it for reproducibility."""
    seed = request.config.getoption("--seed", default=None)
    if seed is None:
        seed = random.randint(0, 2**31)
    print(f"\n=== Test seed: {seed} ===")
    return seed
```

- Random seeds provide broader coverage over many CI runs
- Seeds are logged in pytest output for reproducibility
- Failed tests can be reproduced with `pytest --seed=<failed_seed>`

## GitHub Actions Workflow

### File

`.github/workflows/syn-gen-tests.yml`

### Workflow

```yaml
name: syn-gen tests
on:
  push:
    branches: [master, main]
  pull_request:
    branches: [master, main]

jobs:
  test:
    runs-on: ubuntu-latest
    defaults:
      run:
        shell: bash -l {0}

    steps:
      - uses: actions/checkout@v4

      - name: Setup Miniconda
        uses: conda-incubator/setup-miniconda@v3
        with:
          auto-update-conda: true
          python-version: "3.10"
          channels: bioconda,conda-forge,defaults

      - name: Install CRISPResso2
        run: conda install -c bioconda crispresso2

      - name: Install test dependencies
        run: pip install pytest hypothesis

      - name: Run unit tests
        run: cd syn-gen && pytest test_syn_gen.py -v

      - name: Run e2e tests
        run: cd syn-gen && pytest test_e2e.py -v
```

### Configuration

- **Conda caching**: Cache conda environment for faster runs
- **Timeout**: 30 minutes (CRISPResso can be slow)
- **Python version**: 3.10 (compatible with bioconda CRISPResso2)
- **Artifact upload**: Save test outputs on failure for debugging

### Estimated Runtime

- Conda setup + CRISPResso install: ~3-5 min
- Unit tests: ~1-2 min
- E2E tests (3 modes × 1000 reads each): ~5-8 min
- **Total**: ~10-15 minutes

## Implementation Plan

1. Create `syn-gen/test_e2e.py` with pytest fixtures and test classes
2. Implement NHEJ e2e tests first (simplest validation)
3. Add base editing e2e tests (CBE and ABE)
4. Add prime editing e2e tests
5. Create `.github/workflows/syn-gen-tests.yml`
6. Test locally, then push to verify CI works

## Files to Create/Modify

| File | Action |
|------|--------|
| `syn-gen/test_e2e.py` | Create - e2e test implementation |
| `.github/workflows/syn-gen-tests.yml` | Create - CI workflow |
| `syn-gen/conftest.py` | Create - pytest fixtures and `--seed` option |
