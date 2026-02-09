#!/usr/bin/env bash
# Generate synthetic VCF test data using syn-gen
# Run from the repository root directory.
set -euo pipefail

SYNGEN="python syn-gen/syn_gen.py"
OUTDIR="cli_integration_tests/inputs"

FANC_AMP="CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG"
FANC_GUIDE="GGAATCCCTTCTGCAGCACC"

# Shorter amplicon used for ABE test (no TGGATCGCTTTTCCGAGCTTCTGGCGG segment)
ABE_AMP="CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG"

# Second amplicon for multi-amplicon test
AMP2="TACGGGTATTACCCGCGTTTAGTGGCTAGCGACTCGTGGACTTGCTGTACTGTCTACGGGCGTCAACTTGATAATCCCAAAAAAGCTTGGCCCCGCACAACTCGTTGAGCAATTCTTAAAAAGATGGTGTACGTCCCTCATACTTCGTATTCAATAAACCCGGTTAGACCATTGGGTGCGTGATGCTGCATTGCCTTGCA"
AMP2_GUIDE="CCCCGCACAACTCGTTGAGC"

SEED=42
READS=100

echo "=== Generating VCF test data ==="

# 1. vcf_basic: mixed deletions/insertions (default 75/25 split)
echo "1/8: vcf_basic"
$SYNGEN -a "$FANC_AMP" -g "$FANC_GUIDE" --amplicon-name FANC \
    -n $READS -e 0.3 --seed $SEED \
    -o "$OUTDIR/vcf_basic" -q

# 2. vcf_deletions: deletions only
echo "2/8: vcf_deletions"
$SYNGEN -a "$FANC_AMP" -g "$FANC_GUIDE" --amplicon-name FANC \
    -n $READS -e 0.3 --deletion-weight 1.0 --seed $SEED \
    -o "$OUTDIR/vcf_deletions" -q

# 3. vcf_insertions: insertions only
echo "3/8: vcf_insertions"
$SYNGEN -a "$FANC_AMP" -g "$FANC_GUIDE" --amplicon-name FANC \
    -n $READS -e 0.3 --deletion-weight 0.0 --seed $SEED \
    -o "$OUTDIR/vcf_insertions" -q

# 4. vcf_no_edits: no edits at all
echo "4/8: vcf_no_edits"
$SYNGEN -a "$FANC_AMP" -g "$FANC_GUIDE" --amplicon-name FANC \
    -n $READS -e 0.0 --seed $SEED \
    -o "$OUTDIR/vcf_no_edits" -q

# 5. vcf_multi_amplicon: two amplicons, 50 reads each, combined
echo "5/8: vcf_multi_amplicon"
$SYNGEN -a "$FANC_AMP" -g "$FANC_GUIDE" --amplicon-name AMP1 \
    -n 50 -e 0.3 --seed $SEED \
    -o "$OUTDIR/vcf_multi_amp1" -q
$SYNGEN -a "$AMP2" -g "$AMP2_GUIDE" --amplicon-name AMP2 \
    -n 50 -e 0.3 --seed 43 \
    -o "$OUTDIR/vcf_multi_amp2" -q
# Combine FASTQ files
cat "$OUTDIR/vcf_multi_amp1.fastq" "$OUTDIR/vcf_multi_amp2.fastq" > "$OUTDIR/vcf_multi_amplicon.fastq"
# Clean up temp files (keep the combined one)
rm -f "$OUTDIR/vcf_multi_amp1.fastq"
rm -f "$OUTDIR/vcf_multi_amp2.fastq"

# 6. vcf_base_edit_cbe: cytosine base editor (C→T)
echo "6/8: vcf_base_edit_cbe"
$SYNGEN --mode base-edit -a "$FANC_AMP" -g "$FANC_GUIDE" --amplicon-name FANC \
    --base-editor CBE -n $READS -e 0.3 --seed $SEED \
    -o "$OUTDIR/vcf_base_edit_cbe" -q

# 7. vcf_base_edit_abe: adenine base editor (A→G)
echo "7/8: vcf_base_edit_abe"
$SYNGEN --mode base-edit -a "$ABE_AMP" -g "$FANC_GUIDE" --amplicon-name FANC \
    --base-editor ABE -n $READS -e 0.3 --seed $SEED \
    -o "$OUTDIR/vcf_base_edit_abe" -q

# 8. vcf_prime_edit_basic: prime editing
echo "8/8: vcf_prime_edit_basic"
$SYNGEN --mode prime-edit -a "$FANC_AMP" -g "$FANC_GUIDE" \
    --peg-extension ATCTGGATCGGCTGCAGAAGGGA \
    -n $READS -e 0.3 --seed $SEED \
    -o "$OUTDIR/vcf_prime_edit_basic" -q

echo "=== Done ==="
