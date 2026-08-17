# syn-gen

Synthetic CRISPR NHEJ editing data generator for testing CRISPResso2.

## Installation

No installation required. Just run the script directly:

```bash
python syn_gen.py --help
```

Dependencies: Python 3.10+ (uses dataclasses and type hints). No external packages required.

## Usage

### With custom amplicon and guide

```bash
python syn_gen.py \
    --amplicon CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG \
    --guide GGAATCCCTTCTGCAGCACC \
    --amplicon-name FANC \
    --num-reads 10000 \
    --edit-rate 0.3 \
    --output-prefix fanc_synthetic
```

### Random amplicon generation

For quick testing, omit `--amplicon` to generate a random 200bp amplicon with embedded guide:

```bash
python syn_gen.py \
    --num-reads 1000 \
    --edit-rate 0.5 \
    --seed 42 \
    --output-prefix random_test
```

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `-a, --amplicon` | random | Amplicon sequence (generates random 200bp if not provided) |
| `-g, --guide` | required* | Guide/sgRNA sequence without PAM (*required if amplicon provided) |
| `--amplicon-name` | AMPLICON | Name for output files (VCF CHROM field) |
| `-n, --num-reads` | 10000 | Number of reads to generate |
| `-e, --edit-rate` | 0.3 | Fraction of reads with edits (0.0-1.0) |
| `--deletion-weight` | 0.75 | Probability of deletion vs insertion in NHEJ mode |
| `--deletion-min-size` | 1 | Minimum deletion size in NHEJ mode |
| `--deletion-max-size` | 50 | Maximum deletion size in NHEJ mode |
| `--insertion-min-size` | 1 | Minimum insertion size in NHEJ mode |
| `--insertion-max-size` | 10 | Maximum insertion size in NHEJ mode |
| `--error-rate` | 0.001 | Per-base sequencing error rate |
| `--read-length` | full | Read length (default: full amplicon) |
| `--cleavage-offset` | -3 | Cut site offset from 3' end of guide |
| `-o, --output-prefix` | synthetic | Prefix for output files |
| `--seed` | None | Random seed for reproducibility |
| `-q, --quiet` | False | Suppress summary output |

## Output Files

1. **`{prefix}.fastq`** - FASTQ file with synthetic reads
2. **`{prefix}_edits.tsv`** - Per-read edit information
3. **`{prefix}.vcf`** - CRISPResso2-compatible VCF with variants

### TSV Format

```
read_name    edit_type    edit_position    edit_size    original_seq    edited_seq
read_0       none         0                0
read_1       deletion     87               3            GCA
read_2       insertion    88               1                            T
```

### VCF Format

Standard VCF 4.5 format with allele frequencies:

```
##fileformat=VCFv4.5
##source=syn-gen
#CHROM  POS  ID  REF   ALT  QUAL  FILTER  INFO      FORMAT  Reference
FANC    87   .   AGCA  A    .     PASS    AF=0.150  GT      .
```

## Edit Distribution

NHEJ edits follow a realistic distribution:
- **75% deletions**, 25% insertions by default
- Deletion sizes: shifted geometric distribution (default 1-50bp, configurable with `--deletion-min-size/--deletion-max-size`)
- Insertion sizes: shifted geometric distribution (default 1-10bp, configurable with `--insertion-min-size/--insertion-max-size`)
- Position: centered at cut site ±2bp jitter

### Large deletion example

For long-read simulations with 100-1000bp deletions:

```bash
python syn_gen.py \
    --amplicon <LONG_AMPLICON> \
    --guide <GUIDE> \
    --num-reads 1000 \
    --edit-rate 0.5 \
    --deletion-weight 1.0 \
    --deletion-min-size 100 \
    --deletion-max-size 1000 \
    --seed 42 \
    --output-prefix long_read_large_del
```

## Testing

Run unit tests:

```bash
pytest test_syn_gen.py -v
```

Verify with CRISPResso2:

```bash
# Generate synthetic data
python syn_gen.py -a <AMPLICON> -g <GUIDE> -e 0.3 -o test

# Run CRISPResso2
CRISPResso -r1 test.fastq -a <AMPLICON> -g <GUIDE> --place_report_in_output_folder

# Check that CRISPResso2 reports ~30% modified reads
```
