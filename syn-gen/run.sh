#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

# Use the first amplicon record from gene.fna. The file contains two copies
# of this reference sequence, so stop at the next FASTA header.
amplicon="$(awk 'NR == 2 { sub(/>.*/, ""); print }' gene.fna)"

echo "Running CRISPResso on long_read_big_del.fastq"
CRISPResso \
  -r1 long_read_big_del.fastq \
  -a "$amplicon" \
  -g TACCGGGCGCCCGGGGCCG \
  -n long_read_big_del_analysis \
  --place_report_in_output_folder \
  --default_min_aln_score 0
