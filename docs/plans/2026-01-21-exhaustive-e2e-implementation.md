# Exhaustive E2E Testing Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement position-level verification that CRISPResso correctly detects every edit from syn-gen.

**Architecture:** Add `write_alleles_tsv()` to syn-gen that outputs CRISPResso-compatible allele format, then refactor tests to compare alleles with exact matching instead of tolerance ranges.

**Tech Stack:** Python, pytest, CRISPResso2

---

### Task 1: Add `write_alleles_tsv()` to syn-gen

**Files:**
- Modify: `syn-gen/syn_gen.py:831` (after `write_edit_tsv`)

**Step 1: Add the `write_alleles_tsv` function after `write_edit_tsv`**

Add this function at line 833 (after the `write_edit_tsv` function ends):

```python
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
```

**Step 2: Run existing tests to verify no regression**

Run: `cd syn-gen && pytest test_syn_gen.py -v -x`
Expected: All tests PASS

**Step 3: Commit**

```bash
git add syn-gen/syn_gen.py
git commit -m "feat(syn-gen): add write_alleles_tsv for CRISPResso-compatible output"
```

---

### Task 2: Call `write_alleles_tsv` from `generate_synthetic_data`

**Files:**
- Modify: `syn-gen/syn_gen.py:1097-1106` (Write outputs section)

**Step 1: Add alleles file output**

Modify the "Write outputs" section (around line 1097) to add the alleles file:

```python
    # Write outputs
    fastq_path = f'{output_prefix}.fastq'
    tsv_path = f'{output_prefix}_edits.tsv'
    vcf_path = f'{output_prefix}.vcf'
    alleles_path = f'{output_prefix}_alleles.tsv'

    write_fastq(reads, fastq_path)
    write_edit_tsv(reads, tsv_path)
    write_alleles_tsv(reads, alleles_path)

    variants = aggregate_edits_to_variants(reads, amplicon, amplicon_name)
    write_vcf(variants, amplicon_name, amplicon, vcf_path)
```

**Step 2: Update stats dict to include alleles file**

Modify the stats dict (around line 1126) to include the alleles file:

```python
        'output_files': {
            'fastq': fastq_path,
            'tsv': tsv_path,
            'vcf': vcf_path,
            'alleles': alleles_path
        }
```

**Step 3: Update summary output**

Modify the summary output (around line 1155) to include the alleles file:

```python
        print('Output files:')
        print(f'  FASTQ:   {fastq_path}')
        print(f'  TSV:     {tsv_path}')
        print(f'  VCF:     {vcf_path}')
        print(f'  Alleles: {alleles_path}')
```

**Step 4: Run existing tests**

Run: `cd syn-gen && pytest test_syn_gen.py -v -x`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add syn-gen/syn_gen.py
git commit -m "feat(syn-gen): output alleles.tsv from generate_synthetic_data"
```

---

### Task 3: Add `compare_alleles` function to test_e2e.py

**Files:**
- Modify: `syn-gen/test_e2e.py:177` (after `parse_edits_tsv`)

**Step 1: Add helper to parse syn-gen alleles file**

Add after `parse_edits_tsv` function (around line 177):

```python
def parse_syngen_alleles(alleles_path: str) -> dict[str, dict]:
    """
    Parse syn-gen's *_alleles.tsv file.

    Returns:
        Dict mapping sequence -> allele info dict
    """
    alleles = {}
    with open(alleles_path) as f:
        lines = f.read().strip().split('\n')
        if len(lines) < 2:
            return alleles

        header = lines[0].split('\t')
        for line in lines[1:]:
            values = line.split('\t')
            allele = dict(zip(header, values))
            seq = allele['Aligned_Sequence']
            alleles[seq] = allele

    return alleles


def parse_crispresso_alleles(crispresso_output_dir: str) -> dict[str, dict]:
    """
    Parse CRISPResso's Alleles_frequency_table.zip with detailed columns.

    Returns:
        Dict mapping sequence -> allele info dict
    """
    # Find the CRISPResso output folder
    output_folders = [
        d for d in os.listdir(crispresso_output_dir)
        if d.startswith("CRISPResso_on_")
    ]
    if not output_folders:
        raise FileNotFoundError(f"No CRISPResso output folder in {crispresso_output_dir}")

    crispresso_folder = os.path.join(crispresso_output_dir, output_folders[0])
    zip_path = os.path.join(crispresso_folder, "Alleles_frequency_table.zip")

    if not os.path.exists(zip_path):
        raise FileNotFoundError(f"Alleles_frequency_table.zip not found in {crispresso_folder}")

    alleles = {}
    with zipfile.ZipFile(zip_path, 'r') as zf:
        tsv_files = [f for f in zf.namelist() if f.endswith('.txt')]
        if not tsv_files:
            raise FileNotFoundError("No .txt file in Alleles_frequency_table.zip")

        with zf.open(tsv_files[0]) as f:
            lines = f.read().decode('utf-8').strip().split('\n')
            if len(lines) < 2:
                return alleles

            header = lines[0].split('\t')
            for line in lines[1:]:
                values = line.split('\t')
                allele = dict(zip(header, values))
                # Remove gaps from aligned sequence for comparison
                seq = allele['Aligned_Sequence'].replace('-', '')
                alleles[seq] = allele

    return alleles


def compare_alleles(syngen_alleles_path: str, crispresso_output_dir: str) -> list[str]:
    """
    Compare syn-gen ground truth against CRISPResso output.

    Args:
        syngen_alleles_path: Path to syn-gen's _alleles.tsv
        crispresso_output_dir: Path to CRISPResso output directory

    Returns:
        List of discrepancy messages (empty = all match)
    """
    syngen = parse_syngen_alleles(syngen_alleles_path)
    crispresso = parse_crispresso_alleles(crispresso_output_dir)

    discrepancies = []

    # Check for missing alleles (in syn-gen but not CRISPResso)
    for seq, sg_allele in syngen.items():
        if seq not in crispresso:
            count = sg_allele['#Reads']
            short_seq = seq[:20] + '...' + seq[-20:] if len(seq) > 50 else seq
            discrepancies.append(f"MISSING allele {short_seq} ({count} reads) - not found in CRISPResso")
            continue

        cr_allele = crispresso[seq]

        # Compare read counts
        sg_count = int(sg_allele['#Reads'])
        cr_count = int(cr_allele['#Reads'])
        if sg_count != cr_count:
            short_seq = seq[:20] + '...' + seq[-20:] if len(seq) > 50 else seq
            discrepancies.append(
                f"COUNT mismatch for {short_seq}: expected {sg_count}, got {cr_count}"
            )

        # Compare deletion positions
        sg_del = sg_allele.get('all_deletion_positions', '[]')
        cr_del = cr_allele.get('all_deletion_positions', '[]')
        if sg_del != cr_del:
            short_seq = seq[:20] + '...' + seq[-20:] if len(seq) > 50 else seq
            discrepancies.append(
                f"DELETION positions mismatch for {short_seq}: expected {sg_del}, got {cr_del}"
            )

        # Compare insertion positions
        sg_ins = sg_allele.get('all_insertion_positions', '[]')
        cr_ins = cr_allele.get('all_insertion_positions', '[]')
        if sg_ins != cr_ins:
            short_seq = seq[:20] + '...' + seq[-20:] if len(seq) > 50 else seq
            discrepancies.append(
                f"INSERTION positions mismatch for {short_seq}: expected {sg_ins}, got {cr_ins}"
            )

        # Compare substitution positions
        sg_sub = sg_allele.get('all_substitution_positions', '[]')
        cr_sub = cr_allele.get('all_substitution_positions', '[]')
        if sg_sub != cr_sub:
            short_seq = seq[:20] + '...' + seq[-20:] if len(seq) > 50 else seq
            discrepancies.append(
                f"SUBSTITUTION positions mismatch for {short_seq}: expected {sg_sub}, got {cr_sub}"
            )

    # Check for extra alleles (in CRISPResso but not syn-gen)
    for seq, cr_allele in crispresso.items():
        if seq not in syngen:
            count = cr_allele['#Reads']
            short_seq = seq[:20] + '...' + seq[-20:] if len(seq) > 50 else seq
            discrepancies.append(f"EXTRA allele {short_seq} ({count} reads) - unexpected in CRISPResso")

    return discrepancies
```

**Step 2: Run existing tests to verify no syntax errors**

Run: `cd syn-gen && python -c "import test_e2e; print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add syn-gen/test_e2e.py
git commit -m "feat(test): add compare_alleles for strict allele verification"
```

---

### Task 4: Refactor `test_nhej_basic` to use strict comparison

**Files:**
- Modify: `syn-gen/test_e2e.py:187-259` (TestNHEJEndToEnd.test_nhej_basic)

**Step 1: Replace the test implementation**

Replace the entire `test_nhej_basic` method with:

```python
    def test_nhej_basic(self, temp_dir, random_seed, crispresso_available):
        """
        Test that CRISPResso correctly detects NHEJ edits (deletions/insertions).

        Uses strict allele-level comparison - every allele sequence and edit
        position must match exactly between syn-gen ground truth and CRISPResso.
        """
        random.seed(random_seed)

        # Generate synthetic data
        output_prefix = os.path.join(temp_dir, "nhej_test")
        stats = generate_synthetic_data(
            amplicon=TEST_AMPLICON,
            guide=TEST_GUIDE,
            num_reads=1000,
            edit_rate=0.5,
            error_rate=0.0,  # No sequencing errors for clean comparison
            output_prefix=output_prefix,
            seed=random_seed,
            quiet=True,
            mode='nhej',
        )

        fastq_path = f"{output_prefix}.fastq"
        alleles_path = f"{output_prefix}_alleles.tsv"

        # Run CRISPResso with detailed allele output
        result = run_crispresso(
            fastq_path=fastq_path,
            output_dir=temp_dir,
            amplicon=TEST_AMPLICON,
            guide=TEST_GUIDE,
        )

        # Check CRISPResso ran successfully
        assert result.returncode == 0, f"CRISPResso failed: {result.stderr}"

        # Strict comparison
        discrepancies = compare_alleles(alleles_path, temp_dir)

        assert len(discrepancies) == 0, (
            f"Allele comparison failed with {len(discrepancies)} discrepancies:\n"
            + "\n".join(discrepancies[:10])  # Show first 10
            + (f"\n... and {len(discrepancies) - 10} more" if len(discrepancies) > 10 else "")
        )
```

**Step 2: Run the refactored test**

Run: `cd syn-gen && pytest test_e2e.py::TestNHEJEndToEnd::test_nhej_basic -v`
Expected: Test runs (may pass or fail depending on format matching)

**Step 3: Commit**

```bash
git add syn-gen/test_e2e.py
git commit -m "refactor(test): use strict comparison in test_nhej_basic"
```

---

### Task 5: Refactor `test_nhej_deletions_detected` to use strict comparison

**Files:**
- Modify: `syn-gen/test_e2e.py:261-307` (TestNHEJEndToEnd.test_nhej_deletions_detected)

**Step 1: Replace the test implementation**

Replace the entire `test_nhej_deletions_detected` method with:

```python
    def test_nhej_deletions_detected(self, temp_dir, random_seed, crispresso_available):
        """Test that deletions are correctly detected by CRISPResso with exact positions."""
        random.seed(random_seed)

        output_prefix = os.path.join(temp_dir, "nhej_del_test")
        stats = generate_synthetic_data(
            amplicon=TEST_AMPLICON,
            guide=TEST_GUIDE,
            num_reads=500,
            edit_rate=1.0,  # All reads edited
            error_rate=0.0,
            output_prefix=output_prefix,
            seed=random_seed,
            quiet=True,
            mode='nhej',
        )

        fastq_path = f"{output_prefix}.fastq"
        alleles_path = f"{output_prefix}_alleles.tsv"

        result = run_crispresso(
            fastq_path=fastq_path,
            output_dir=temp_dir,
            amplicon=TEST_AMPLICON,
            guide=TEST_GUIDE,
        )

        assert result.returncode == 0, f"CRISPResso failed: {result.stderr}"

        discrepancies = compare_alleles(alleles_path, temp_dir)

        assert len(discrepancies) == 0, (
            f"Allele comparison failed with {len(discrepancies)} discrepancies:\n"
            + "\n".join(discrepancies[:10])
            + (f"\n... and {len(discrepancies) - 10} more" if len(discrepancies) > 10 else "")
        )
```

**Step 2: Run the test**

Run: `cd syn-gen && pytest test_e2e.py::TestNHEJEndToEnd::test_nhej_deletions_detected -v`
Expected: Test runs

**Step 3: Commit**

```bash
git add syn-gen/test_e2e.py
git commit -m "refactor(test): use strict comparison in test_nhej_deletions_detected"
```

---

### Task 6: Refactor `test_cbe_basic` to use strict comparison

**Files:**
- Modify: `syn-gen/test_e2e.py:313-366` (TestBaseEditingEndToEnd.test_cbe_basic)

**Step 1: Replace the test implementation**

Replace the entire `test_cbe_basic` method with:

```python
    def test_cbe_basic(self, temp_dir, random_seed, crispresso_available):
        """
        Test that CRISPResso correctly detects CBE edits (C→T conversions).
        """
        random.seed(random_seed)

        output_prefix = os.path.join(temp_dir, "cbe_test")
        stats = generate_synthetic_data(
            amplicon=TEST_AMPLICON,
            guide=TEST_GUIDE,
            num_reads=1000,
            edit_rate=0.5,
            error_rate=0.0,
            output_prefix=output_prefix,
            seed=random_seed,
            quiet=True,
            mode='base-edit',
            base_editor='CBE',
            window_center=6,
            window_sigma=1.5,
            base_edit_prob=0.8,
        )

        fastq_path = f"{output_prefix}.fastq"
        alleles_path = f"{output_prefix}_alleles.tsv"

        result = run_crispresso(
            fastq_path=fastq_path,
            output_dir=temp_dir,
            amplicon=TEST_AMPLICON,
            guide=TEST_GUIDE,
            extra_args=["--base_editor_output"],
        )

        assert result.returncode == 0, f"CRISPResso failed: {result.stderr}"

        discrepancies = compare_alleles(alleles_path, temp_dir)

        assert len(discrepancies) == 0, (
            f"Allele comparison failed with {len(discrepancies)} discrepancies:\n"
            + "\n".join(discrepancies[:10])
            + (f"\n... and {len(discrepancies) - 10} more" if len(discrepancies) > 10 else "")
        )
```

**Step 2: Run the test**

Run: `cd syn-gen && pytest test_e2e.py::TestBaseEditingEndToEnd::test_cbe_basic -v`
Expected: Test runs

**Step 3: Commit**

```bash
git add syn-gen/test_e2e.py
git commit -m "refactor(test): use strict comparison in test_cbe_basic"
```

---

### Task 7: Refactor `test_abe_basic` to use strict comparison

**Files:**
- Modify: `syn-gen/test_e2e.py:368-418` (TestBaseEditingEndToEnd.test_abe_basic)

**Step 1: Replace the test implementation**

Replace the entire `test_abe_basic` method with:

```python
    def test_abe_basic(self, temp_dir, random_seed, crispresso_available):
        """
        Test that CRISPResso correctly detects ABE edits (A→G conversions).
        """
        random.seed(random_seed)

        output_prefix = os.path.join(temp_dir, "abe_test")
        stats = generate_synthetic_data(
            amplicon=TEST_AMPLICON,
            guide=TEST_GUIDE,
            num_reads=1000,
            edit_rate=0.5,
            error_rate=0.0,
            output_prefix=output_prefix,
            seed=random_seed,
            quiet=True,
            mode='base-edit',
            base_editor='ABE',
            window_center=6,
            window_sigma=1.5,
            base_edit_prob=0.8,
        )

        fastq_path = f"{output_prefix}.fastq"
        alleles_path = f"{output_prefix}_alleles.tsv"

        result = run_crispresso(
            fastq_path=fastq_path,
            output_dir=temp_dir,
            amplicon=TEST_AMPLICON,
            guide=TEST_GUIDE,
            extra_args=["--base_editor_output"],
        )

        assert result.returncode == 0, f"CRISPResso failed: {result.stderr}"

        discrepancies = compare_alleles(alleles_path, temp_dir)

        assert len(discrepancies) == 0, (
            f"Allele comparison failed with {len(discrepancies)} discrepancies:\n"
            + "\n".join(discrepancies[:10])
            + (f"\n... and {len(discrepancies) - 10} more" if len(discrepancies) > 10 else "")
        )
```

**Step 2: Run the test**

Run: `cd syn-gen && pytest test_e2e.py::TestBaseEditingEndToEnd::test_abe_basic -v`
Expected: Test runs

**Step 3: Commit**

```bash
git add syn-gen/test_e2e.py
git commit -m "refactor(test): use strict comparison in test_abe_basic"
```

---

### Task 8: Refactor prime editing tests to use strict comparison

**Files:**
- Modify: `syn-gen/test_e2e.py:424-576` (TestPrimeEditingEndToEnd)

**Step 1: Replace `test_prime_edit_basic`**

Replace with:

```python
    def test_prime_edit_basic(self, temp_dir, random_seed, crispresso_available):
        """
        Test that CRISPResso correctly detects prime editing outcomes.
        """
        random.seed(random_seed)

        output_prefix = os.path.join(temp_dir, "pe_test")
        stats = generate_synthetic_data(
            amplicon=TEST_AMPLICON,
            guide=TEST_GUIDE,
            num_reads=1000,
            edit_rate=0.5,
            error_rate=0.0,
            output_prefix=output_prefix,
            seed=random_seed,
            quiet=True,
            mode='prime-edit',
            peg_extension=PE_EXTENSION,
            peg_scaffold=PE_SCAFFOLD,
            perfect_edit_fraction=0.8,
            partial_edit_fraction=0.1,
            pe_indel_fraction=0.1,
            scaffold_incorporation_fraction=0.0,
            flap_indel_fraction=0.0,
        )

        fastq_path = f"{output_prefix}.fastq"
        alleles_path = f"{output_prefix}_alleles.tsv"

        result = run_crispresso(
            fastq_path=fastq_path,
            output_dir=temp_dir,
            amplicon=TEST_AMPLICON,
            guide=TEST_GUIDE,
            extra_args=[
                "--prime_editing_pegRNA_spacer_seq", TEST_GUIDE,
                "--prime_editing_pegRNA_extension_seq", PE_EXTENSION,
                "--prime_editing_pegRNA_scaffold_seq", PE_SCAFFOLD,
            ],
        )

        assert result.returncode == 0, f"CRISPResso failed: {result.stderr}"

        discrepancies = compare_alleles(alleles_path, temp_dir)

        assert len(discrepancies) == 0, (
            f"Allele comparison failed with {len(discrepancies)} discrepancies:\n"
            + "\n".join(discrepancies[:10])
            + (f"\n... and {len(discrepancies) - 10} more" if len(discrepancies) > 10 else "")
        )
```

**Step 2: Replace `test_prime_edit_perfect_edits`**

Replace with:

```python
    def test_prime_edit_perfect_edits(self, temp_dir, random_seed, crispresso_available):
        """Test that perfect prime edits are detected with correct sequence."""
        random.seed(random_seed)

        output_prefix = os.path.join(temp_dir, "pe_perfect_test")
        stats = generate_synthetic_data(
            amplicon=TEST_AMPLICON,
            guide=TEST_GUIDE,
            num_reads=500,
            edit_rate=1.0,  # All reads edited
            error_rate=0.0,
            output_prefix=output_prefix,
            seed=random_seed,
            quiet=True,
            mode='prime-edit',
            peg_extension=PE_EXTENSION,
            peg_scaffold=PE_SCAFFOLD,
            perfect_edit_fraction=1.0,  # All perfect edits
            partial_edit_fraction=0.0,
            pe_indel_fraction=0.0,
            scaffold_incorporation_fraction=0.0,
            flap_indel_fraction=0.0,
        )

        fastq_path = f"{output_prefix}.fastq"
        alleles_path = f"{output_prefix}_alleles.tsv"

        result = run_crispresso(
            fastq_path=fastq_path,
            output_dir=temp_dir,
            amplicon=TEST_AMPLICON,
            guide=TEST_GUIDE,
            extra_args=[
                "--prime_editing_pegRNA_spacer_seq", TEST_GUIDE,
                "--prime_editing_pegRNA_extension_seq", PE_EXTENSION,
                "--prime_editing_pegRNA_scaffold_seq", PE_SCAFFOLD,
            ],
        )

        assert result.returncode == 0, f"CRISPResso failed: {result.stderr}"

        discrepancies = compare_alleles(alleles_path, temp_dir)

        assert len(discrepancies) == 0, (
            f"Allele comparison failed with {len(discrepancies)} discrepancies:\n"
            + "\n".join(discrepancies[:10])
            + (f"\n... and {len(discrepancies) - 10} more" if len(discrepancies) > 10 else "")
        )
```

**Step 3: Run the tests**

Run: `cd syn-gen && pytest test_e2e.py::TestPrimeEditingEndToEnd -v`
Expected: Tests run

**Step 4: Commit**

```bash
git add syn-gen/test_e2e.py
git commit -m "refactor(test): use strict comparison in prime editing tests"
```

---

### Task 9: Run full e2e test suite and debug any failures

**Step 1: Run all e2e tests**

Run: `cd syn-gen && pytest test_e2e.py -v`

**Step 2: If failures occur, analyze discrepancies**

Look at the error messages to identify format mismatches between syn-gen and CRISPResso output formats.

**Step 3: Fix any format issues in `write_alleles_tsv` or `compare_alleles`**

Common issues:
- List formatting differences (Python list vs JSON)
- Position indexing (0-based vs 1-based)
- Sequence alignment differences

**Step 4: Commit fixes**

```bash
git add syn-gen/syn_gen.py syn-gen/test_e2e.py
git commit -m "fix: resolve format differences in allele comparison"
```

---

### Task 10: Add test with sequencing errors

**Files:**
- Modify: `syn-gen/test_e2e.py` (add new test)

**Step 1: Add test for sequencing error detection**

Add to `TestNHEJEndToEnd` class:

```python
    def test_nhej_with_sequencing_errors(self, temp_dir, random_seed, crispresso_available):
        """Test that sequencing errors are detected as substitutions."""
        random.seed(random_seed)

        output_prefix = os.path.join(temp_dir, "nhej_errors_test")
        stats = generate_synthetic_data(
            amplicon=TEST_AMPLICON,
            guide=TEST_GUIDE,
            num_reads=500,
            edit_rate=0.5,
            error_rate=0.01,  # 1% sequencing error rate
            output_prefix=output_prefix,
            seed=random_seed,
            quiet=True,
            mode='nhej',
        )

        fastq_path = f"{output_prefix}.fastq"
        alleles_path = f"{output_prefix}_alleles.tsv"

        result = run_crispresso(
            fastq_path=fastq_path,
            output_dir=temp_dir,
            amplicon=TEST_AMPLICON,
            guide=TEST_GUIDE,
        )

        assert result.returncode == 0, f"CRISPResso failed: {result.stderr}"

        discrepancies = compare_alleles(alleles_path, temp_dir)

        assert len(discrepancies) == 0, (
            f"Allele comparison failed with {len(discrepancies)} discrepancies:\n"
            + "\n".join(discrepancies[:10])
            + (f"\n... and {len(discrepancies) - 10} more" if len(discrepancies) > 10 else "")
        )
```

**Step 2: Run the new test**

Run: `cd syn-gen && pytest test_e2e.py::TestNHEJEndToEnd::test_nhej_with_sequencing_errors -v`

**Step 3: Commit**

```bash
git add syn-gen/test_e2e.py
git commit -m "test: add e2e test for sequencing error detection"
```

---

### Task 11: Final validation and push

**Step 1: Run full test suite**

Run: `cd syn-gen && pytest test_syn_gen.py test_e2e.py -v`
Expected: All tests PASS

**Step 2: Push changes**

```bash
git push origin feature/syn-gen-e2e
```

**Step 3: Verify CI passes**

Run: `gh run watch --exit-status`
