"""CLI integration tests for CRISPResso2, migrated from the Makefile."""
import re
from dataclasses import dataclass, field
from typing import List

import pytest


COMMON_FLAGS = [
    '--place_report_in_output_folder',
    '--halt_on_plot_fail',
    '--debug',
]


@dataclass
class CLITestCase:
    id: str
    cmd: List[str]
    output_dir: str
    marks: List[str] = field(default_factory=list)
    xdist_group: str = ''

    @property
    def full_cmd(self) -> str:
        return ' '.join(self.cmd + COMMON_FLAGS)


TESTS = [
    # ── Core CRISPResso ──────────────────────────────────────────────
    CLITestCase(
        id='basic',
        cmd=[
            'CRISPResso',
            '-r1 inputs/FANC.Cas9.fastq',
            '-a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG',
            '-g GGAATCCCTTCTGCAGCACC',
        ],
        output_dir='CRISPResso_on_FANC.Cas9',
        marks=['core'],
    ),
    CLITestCase(
        id='params',
        cmd=[
            'CRISPResso',
            '-r1 inputs/FANC.Cas9.fastq',
            '-a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG',
            '-g GGAATCCCTTCTGCAGCACC',
            '-e CGGCCGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCTGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG',
            '-c GGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTT',
            '--dump',
            '-qwc 20-30_45-50',
            '-q 30',
            '--default_min_aln_score 80',
            '-an FANC',
            '-n params',
            '--base_editor_output',
            '-fg AGCCTTGCAGTGGGCGCGCTA,CCCACTGAAGGCCC',
            '--dsODN GCTAGATTTCCCAAGAAGA',
            '-gn hi',
            '-fgn dear',
            '-p max',
            '--base_editor_consider_changes_outside_qw',
        ],
        output_dir='CRISPResso_on_params',
        marks=['core'],
    ),
    CLITestCase(
        id='params_deletions',
        cmd=[
            'CRISPResso',
            '-r1 inputs/FANC.Cas9.deletions.fastq',
            '-a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG',
            '-g GGAATCCCTTCTGCAGCACC',
            '-e CGGCCGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCTGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG',
            '-c GGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTT',
            '--dump',
            '-qwc 20-30_45-50',
            '-q 30',
            '--default_min_aln_score 80',
            '-an FANC',
            '-n params-deletions',
            '--base_editor_output',
            '-fg AGCCTTGCAGTGGGCGCGCTA,CCCACTGAAGGCCC',
            '--dsODN GCTAGATTTCCCAAGAAGA',
            '-gn hi',
            '-fgn dear',
            '-p max',
            '--base_editor_consider_changes_outside_qw',
        ],
        output_dir='CRISPResso_on_params-deletions',
        marks=['core'],
    ),
    CLITestCase(
        id='nhej_native_merge',
        cmd=[
            'CRISPResso',
            '-r1 inputs/nhej.r1.fastq.gz',
            '-r2 inputs/nhej.r2.fastq.gz',
            '-a AATGTCCCCCAATGGGAAGTTCATCTGGCACTGCCCACAGGTGAGGAGGTCATGATCCCCTTCTGGAGCTCCCAACGGGCCGTGGTCTGGTTCATCATCTGTAAGAATGGCTTCAAGAGGCTCGGCTGTGGTT',
            '-n nhej_native_merge',
            '--crispresso_merge',
        ],
        output_dir='CRISPResso_on_nhej_native_merge',
        marks=['core'],
    ),
    CLITestCase(
        id='prime_editor',
        cmd=[
            'CRISPResso',
            '--fastq_r1 inputs/prime_editor.fastq.gz',
            '--amplicon_seq ACGTCTCATATGCCCCTTGGCAGTCATCTTAGTCATTACCTGAGGTGTTCGTTGTAACTCATATAAACTGAGTTCCCATGTTTTGCTTAATGGTTGAGTTCCGTTTGTCTGCACAGCCTGAGACATTGCTGGAAATAAAGAAGAGAGAAAAACAATTTTAGTATTTGGAAGGGAAGTGCTATGGTCTGAATGTATGTGTCCCACCAAAATTCCTACGT',
            '--prime_editing_pegRNA_spacer_seq GTCATCTTAGTCATTACCTG',
            '--prime_editing_pegRNA_extension_seq AACGAACACCTCATGTAATGACTAAGATG',
            '--prime_editing_nicking_guide_seq CTCAACCATTAAGCAAAACAT',
            '--prime_editing_pegRNA_scaffold_seq GTTTTAGAGCTAGAAATAGCAAGTTAAAATAAGGCTAGTCCGTTATCAACTTGAAAAAGTGGCACCGAGTCGGTGC',
            '--write_cleaned_report',
        ],
        output_dir='CRISPResso_on_prime_editor',
        marks=['editor'],
    ),
    CLITestCase(
        id='base_editor',
        cmd=[
            'CRISPResso',
            '-r1 inputs/FANC.Cas9.fastq',
            '-a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG',
            '-g GGAATCCCTTCTGCAGCACC',
            '-e CGGCCGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCTGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG',
            '-c GGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTT',
            '--dump',
            '-q 30',
            '--default_min_aln_score 80',
            '-an FANC',
            '-n base_editor',
            '--base_editor_output',
            '-fg AGCCTTGCAGTGGGCGCGCTA,CCCACTGAAGGCCC',
            '--dsODN GCTAGATTTCCCAAGAAGA',
            '-gn hi',
            '-fgn dear',
            '-p max',
        ],
        output_dir='CRISPResso_on_base_editor',
        marks=['editor'],
    ),
    # ── Parallel / process variants ──────────────────────────────────
    CLITestCase(
        id='basic_parallel',
        cmd=[
            'CRISPResso',
            '-r1 inputs/FANC.Cas9.fastq',
            '-a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG',
            '-g GGAATCCCTTCTGCAGCACC',
            '-p 2',
            '-n basic-parallel',
        ],
        output_dir='CRISPResso_on_basic-parallel',
        marks=['core'],
    ),
    # ── Asymmetric ───────────────────────────────────────────────────
    CLITestCase(
        id='asym_both',
        cmd=[
            'CRISPResso',
            '-r1 inputs/asym.fastq',
            '-a GACATACATACA',
            '-g GACATACATACA',
            '--exclude_bp_from_left 0',
            '--exclude_bp_from_right 0',
            '-n asym_both',
        ],
        output_dir='CRISPResso_on_asym_both',
        marks=['asym'],
    ),
    CLITestCase(
        id='asym_left',
        cmd=[
            'CRISPResso',
            '-r1 inputs/FANC.Cas9.fastq',
            '-a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG',
            '-g CGGATGTTCCAATCAGTACG',
            '--exclude_bp_from_left 0',
            '-n asym_left',
        ],
        output_dir='CRISPResso_on_asym_left',
        marks=['asym'],
    ),
    CLITestCase(
        id='asym_right',
        cmd=[
            'CRISPResso',
            '-r1 inputs/FANC.Cas9.fastq',
            '-a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG',
            '-g TCCATCGGCGCTTTGGTCGG',
            '--exclude_bp_from_right 0',
            '-n asym_right',
        ],
        output_dir='CRISPResso_on_asym_right',
        marks=['asym'],
    ),
    # ── BAM input ────────────────────────────────────────────────────
    CLITestCase(
        id='bam',
        cmd=[
            'CRISPResso',
            '--bam_input inputs/Both.Cas9.fastq.smallGenome.bam',
            '--bam_chr_loc chr9',
            '--auto',
            '--name bam',
            '--n_processes 2',
        ],
        output_dir='CRISPResso_on_bam',
        marks=['bam'],
    ),
    CLITestCase(
        id='bam_single',
        cmd=[
            'CRISPResso',
            '--bam_input inputs/Both.Cas9.fastq.smallGenome.bam',
            '--bam_chr_loc chr9',
            '--auto',
            '--n_processes 1',
            '-n bam-single',
        ],
        output_dir='CRISPResso_on_bam-single',
        marks=['bam'],
    ),
    # ── BAM output ───────────────────────────────────────────────────
    CLITestCase(
        id='bam_out',
        cmd=[
            'CRISPResso',
            '-r1 inputs/bam_test.fq',
            '-a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTC,GGAAACGCCCATGCAATTAGTCTATTTCTGCTGCAAGTAAGCATGCATTTGTAGGCTTGATGCTTTTTTTCTGCTTCTCCAGCCCT',
            '--bam_output',
            '-n bam-out',
        ],
        output_dir='CRISPResso_on_bam-out',
        marks=['bam'],
    ),
    CLITestCase(
        id='bam_out_genome',
        cmd=[
            'CRISPResso',
            '-r1 inputs/bam_test.fq',
            '-a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTC,GGAAACGCCCATGCAATTAGTCTATTTCTGCTGCAAGTAAGCATGCATTTGTAGGCTTGATGCTTTTTTTCTGCTTCTCCAGCCCT',
            '--bam_output',
            '-n bam-out-genome',
            '-x inputs/small_genome/smallGenome',
        ],
        output_dir='CRISPResso_on_bam-out-genome',
        marks=['bam'],
    ),
    CLITestCase(
        id='bam_out_parallel',
        cmd=[
            'CRISPResso',
            '-r1 inputs/bam_test.fq',
            '-a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTC,GGAAACGCCCATGCAATTAGTCTATTTCTGCTGCAAGTAAGCATGCATTTGTAGGCTTGATGCTTTTTTTCTGCTTCTCCAGCCCT',
            '--bam_output',
            '-n bam-out-parallel',
            '--n_processes max',
        ],
        output_dir='CRISPResso_on_bam-out-parallel',
        marks=['bam'],
    ),
    CLITestCase(
        id='basic_write_bam_out',
        cmd=[
            'CRISPResso',
            '-r1 inputs/FANC.Cas9.fastq',
            '-a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG',
            '-g GGAATCCCTTCTGCAGCACC',
            '--bam_output',
            '-n basic-write-bam-out',
        ],
        output_dir='CRISPResso_on_basic-write-bam-out',
        marks=['bam'],
    ),
    CLITestCase(
        id='basic_write_bam_out_parallel',
        cmd=[
            'CRISPResso',
            '-r1 inputs/FANC.Cas9.fastq',
            '-a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG',
            '-g GGAATCCCTTCTGCAGCACC',
            '--bam_output',
            '--n_processes 2',
            '-n basic-write-bam-out-parallel',
        ],
        output_dir='CRISPResso_on_basic-write-bam-out-parallel',
        marks=['bam'],
    ),
    # ── Batch ────────────────────────────────────────────────────────
    CLITestCase(
        id='batch',
        cmd=[
            'CRISPRessoBatch',
            '-bs inputs/FANC.batch',
            '-a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG',
            '-g GGAATCCCTTCTGCAGCACC',
            '--base_editor_output',
        ],
        output_dir='CRISPRessoBatch_on_FANC',
        marks=['batch'],
        xdist_group='batch_deps',
    ),
    # ── Pooled ───────────────────────────────────────────────────────
    CLITestCase(
        id='pooled',
        cmd=[
            'CRISPRessoPooled',
            '-r1 inputs/Both.Cas9.fastq',
            '-f inputs/Cas9.amplicons.txt',
            '--keep_intermediate',
            '--min_reads_to_use_region 100',
            '-p 4',
        ],
        output_dir='CRISPRessoPooled_on_Both.Cas9',
        marks=['pooled'],
    ),
    CLITestCase(
        id='pooled_paired_sim',
        cmd=[
            'CRISPRessoPooled',
            '-r1 inputs/simulated.trim_reqd.r1.fq',
            '-r2 inputs/simulated.trim_reqd.r2.fq',
            '-f inputs/simulated.amplicons.txt',
            '--min_reads_to_use_region 10',
            '--trim_sequences',
            '--keep_intermediate',
            '-n pooled-paired-sim',
        ],
        output_dir='CRISPRessoPooled_on_pooled-paired-sim',
        marks=['pooled'],
    ),
    CLITestCase(
        id='pooled_mixed_mode',
        cmd=[
            'CRISPRessoPooled',
            '-r1 inputs/Both.Cas9.genome.fastq',
            '-x inputs/small_genome/smallGenome',
            '-f inputs/Cas9.amplicons.genome.txt',
            '--keep_intermediate',
            '--min_reads_to_use_region 100',
            '-n pooled-mixed-mode',
        ],
        output_dir='CRISPRessoPooled_on_pooled-mixed-mode',
        marks=['pooled'],
    ),
    CLITestCase(
        id='pooled_mixed_mode_genome_demux',
        cmd=[
            'CRISPRessoPooled',
            '-r1 inputs/Both.Cas9.genome.fastq',
            '-x inputs/small_genome/smallGenome',
            '-f inputs/Cas9.amplicons.genome.txt',
            '--keep_intermediate',
            '--min_reads_to_use_region 100',
            '-n pooled-mixed-mode-genome-demux',
            '--demultiplex_genome_wide',
        ],
        output_dir='CRISPRessoPooled_on_pooled-mixed-mode-genome-demux',
        marks=['pooled'],
    ),
    # ── WGS ──────────────────────────────────────────────────────────
    CLITestCase(
        id='wgs',
        cmd=[
            'CRISPRessoWGS',
            '-b inputs/Both.Cas9.fastq.smallGenome.bam',
            '-r inputs/small_genome/smallGenome.fa',
            '-f inputs/Cas9.regions.txt',
        ],
        output_dir='CRISPRessoWGS_on_Both.Cas9.fastq.smallGenome',
        marks=['wgs'],
    ),
    # ── VCF ──────────────────────────────────────────────────────────
    CLITestCase(
        id='vcf_basic',
        cmd=[
            'CRISPResso',
            '-r1 inputs/vcf_basic.fastq',
            '-a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG',
            '-g GGAATCCCTTCTGCAGCACC',
            '--quantification_window_coordinates 89-95',
            '--vcf_output',
            '--amplicon_coordinates FANC:1',
            '-n vcf-basic',
        ],
        output_dir='CRISPResso_on_vcf-basic',
        marks=['vcf'],
    ),
    CLITestCase(
        id='vcf_deletions_only',
        cmd=[
            'CRISPResso',
            '-r1 inputs/vcf_deletions.fastq',
            '-a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG',
            '-g GGAATCCCTTCTGCAGCACC',
            '--vcf_output',
            '--amplicon_coordinates FANC:1',
            '--quantification_window_coordinates 89-94',
            '-n vcf-deletions-only',
        ],
        output_dir='CRISPResso_on_vcf-deletions-only',
        marks=['vcf'],
    ),
    CLITestCase(
        id='vcf_insertions_only',
        cmd=[
            'CRISPResso',
            '-r1 inputs/vcf_insertions.fastq',
            '-a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG',
            '-g GGAATCCCTTCTGCAGCACC',
            '--quantification_window_coordinates 89-95',
            '--vcf_output',
            '--amplicon_coordinates FANC:1',
            '-n vcf-insertions-only',
        ],
        output_dir='CRISPResso_on_vcf-insertions-only',
        marks=['vcf'],
    ),
    CLITestCase(
        id='vcf_no_edits',
        cmd=[
            'CRISPResso',
            '-r1 inputs/vcf_no_edits.fastq',
            '-a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG',
            '-g GGAATCCCTTCTGCAGCACC',
            '--vcf_output',
            '--amplicon_coordinates FANC:1',
            '-n vcf-no-edits',
        ],
        output_dir='CRISPResso_on_vcf-no-edits',
        marks=['vcf'],
    ),
    CLITestCase(
        id='vcf_multi_amplicon',
        cmd=[
            'CRISPResso',
            '-r1 inputs/vcf_multi_amplicon.fastq',
            '-a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG,TACGGGTATTACCCGCGTTTAGTGGCTAGCGACTCGTGGACTTGCTGTACTGTCTACGGGCGTCAACTTGATAATCCCAAAAAAGCTTGGCCCCGCACAACTCGTTGAGCAATTCTTAAAAAGATGGTGTACGTCCCTCATACTTCGTATTCAATAAACCCGGTTAGACCATTGGGTGCGTGATGCTGCATTGCCTTGCA',
            '-an AMP1,AMP2',
            '-g GGAATCCCTTCTGCAGCACC,CCCCGCACAACTCGTTGAGC',
            '--vcf_output',
            '--quantification_window_coordinates 89-95,104-109',
            '--amplicon_coordinates chr1:1000,chr2:5000',
            '-n vcf-multi-amplicon',
        ],
        output_dir='CRISPResso_on_vcf-multi-amplicon',
        marks=['vcf'],
    ),
    CLITestCase(
        id='vcf_base_edit_cbe',
        cmd=[
            'CRISPResso',
            '-r1 inputs/vcf_base_edit_cbe.fastq',
            '-a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG',
            '-g GGAATCCCTTCTGCAGCACC',
            '--vcf_output',
            '--amplicon_coordinates FANC:1',
            '--quantification_window_coordinates 76-96',
            '-n vcf-base-edit-cbe',
        ],
        output_dir='CRISPResso_on_vcf-base-edit-cbe',
        marks=['vcf'],
    ),
    CLITestCase(
        id='vcf_base_edit_abe',
        cmd=[
            'CRISPResso',
            '-r1 inputs/vcf_base_edit_abe.fastq',
            '-a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG',
            '-g GGAATCCCTTCTGCAGCACC',
            '--vcf_output',
            '--amplicon_coordinates FANC:1',
            '--quantification_window_coordinates 76-96',
            '-n vcf-base-edit-abe',
        ],
        output_dir='CRISPResso_on_vcf-base-edit-abe',
        marks=['vcf'],
    ),
    CLITestCase(
        id='vcf_prime_edit_basic',
        cmd=[
            'CRISPResso',
            '-r1 inputs/vcf_prime_edit_basic.fastq',
            '-a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG',
            '-g GGAATCCCTTCTGCAGCACC',
            '--prime_editing_pegRNA_spacer_seq GGAATCCCTTCTGCAGCACC',
            '--prime_editing_pegRNA_extension_seq ATCTGGATCGGCTGCAGAAGGGA',
            '--vcf_output',
            '--amplicon_coordinates FANC:1,FANC_PE:1',
            '-n vcf-prime-edit-basic',
        ],
        output_dir='CRISPResso_on_vcf-prime-edit-basic',
        marks=['vcf'],
    ),
]


def _make_params():
    """Build pytest.param list with proper markers from CLITestCase instances."""
    mark_map = {
        'core': pytest.mark.core,
        'editor': pytest.mark.editor,
        'asym': pytest.mark.asym,
        'batch': pytest.mark.batch,
        'pooled': pytest.mark.pooled,
        'wgs': pytest.mark.wgs,
        'vcf': pytest.mark.vcf,
        'bam': pytest.mark.bam,
        'pro_only': pytest.mark.pro_only,
    }
    params = []
    for tc in TESTS:
        marks = [mark_map[m] for m in tc.marks if m in mark_map]
        if tc.xdist_group:
            marks.append(pytest.mark.xdist_group(tc.xdist_group))
        params.append(pytest.param(tc, id=tc.id, marks=marks))
    return params


@pytest.mark.parametrize('test_case', _make_params())
def test_crispresso_cli(test_case, run_crispresso, check_diffs, assert_no_diff, cli_test_dir):
    result = run_crispresso(test_case.full_cmd)
    assert result.returncode == 0, (
        f'{test_case.id} command failed (exit code {result.returncode}):\n'
        f'{result.stderr}'
    )
    if check_diffs:
        actual = cli_test_dir / test_case.output_dir
        assert_no_diff(actual)


@pytest.mark.compare
@pytest.mark.xdist_group('batch_deps')
def test_compare(run_crispresso, check_diffs, assert_no_diff, cli_test_dir):
    """CRISPRessoCompare — requires batch output from test_crispresso_cli[batch]."""
    batch_dir = cli_test_dir / 'CRISPRessoBatch_on_FANC'
    if not batch_dir.exists():
        pytest.skip('Batch output not found; run batch test first')
    result = run_crispresso(' '.join([
        'CRISPRessoCompare',
        'CRISPRessoBatch_on_FANC/CRISPResso_on_Cas9/',
        'CRISPRessoBatch_on_FANC/CRISPResso_on_Untreated/',
    ] + COMMON_FLAGS))
    assert result.returncode == 0, (
        f'compare command failed (exit code {result.returncode}):\n'
        f'{result.stderr}'
    )
    if check_diffs:
        assert_no_diff(cli_test_dir / 'CRISPRessoCompare_on_Cas9_VS_Untreated')


@pytest.mark.aggregate
@pytest.mark.xdist_group('batch_deps')
def test_aggregate(run_crispresso, check_diffs, assert_no_diff, cli_test_dir):
    """CRISPRessoAggregate — requires batch output from test_crispresso_cli[batch]."""
    batch_dir = cli_test_dir / 'CRISPRessoBatch_on_FANC'
    if not batch_dir.exists():
        pytest.skip('Batch output not found; run batch test first')
    result = run_crispresso(' '.join([
        'CRISPRessoAggregate',
        '-p CRISPRessoBatch_on_FANC/CRISPResso_on_',
        '-n aggregate',
    ] + COMMON_FLAGS))
    assert result.returncode == 0, (
        f'aggregate command failed (exit code {result.returncode}):\n'
        f'{result.stderr}'
    )
    if check_diffs:
        assert_no_diff(cli_test_dir / 'CRISPRessoAggregate_on_aggregate')


@pytest.mark.pro_only
def test_pro_smoke_single_plot(run_crispresso, cli_test_dir):
    """Smoke test: config_file with plots key containing only read_barplot.

    Verifies that the Pro report pipeline respects the plots config by
    checking that the generated HTML contains exactly one <img> tag,
    and it's the read barplot.
    """
    cmd = ' '.join([
        'CRISPResso',
        '-r1 inputs/FANC.Cas9.fastq',
        '-a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG',
        '-g GGAATCCCTTCTGCAGCACC',
        '-n pro-smoke-single-plot',
        '--config_file inputs/smoke_single_plot_config.json',
        '--use_matplotlib',
    ] + COMMON_FLAGS)

    result = run_crispresso(cmd)
    assert result.returncode == 0, (
        f'pro-smoke-single-plot command failed (exit code {result.returncode}):\n'
        f'{result.stderr}'
    )

    # Read the generated report HTML
    report_path = cli_test_dir / 'CRISPResso_on_pro-smoke-single-plot' / 'CRISPResso2_report.html'
    assert report_path.exists(), f'Report not found at {report_path}'
    html = report_path.read_text(encoding='utf-8')

    # Find all <img src="..."> tags
    img_tags = re.findall(r'<img\s+src="([^"]+)"', html)
    assert len(img_tags) == 1, (
        f'Expected exactly 1 <img> tag, found {len(img_tags)}: {img_tags}'
    )
    assert '1a.Read_barplot.png' in img_tags[0], (
        f'Expected read barplot image, got: {img_tags[0]}'
    )


@pytest.mark.pro_only
def test_pro_no_plots_key_shows_all_defaults(run_crispresso, cli_test_dir):
    """Config file with no plots key shows all default plots.

    A config_file containing only colors (no plots key) should produce
    a report with all default plots present.
    """
    cmd = ' '.join([
        'CRISPResso',
        '-r1 inputs/FANC.Cas9.fastq',
        '-a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG',
        '-g GGAATCCCTTCTGCAGCACC',
        '-n pro-no-plots-key',
        '--config_file inputs/no_plots_key_config.json',
        '--use_matplotlib',
    ] + COMMON_FLAGS)

    result = run_crispresso(cmd)
    assert result.returncode == 0, (
        f'pro-no-plots-key command failed (exit code {result.returncode}):\n'
        f'{result.stderr}'
    )

    report_path = cli_test_dir / 'CRISPResso_on_pro-no-plots-key' / 'CRISPResso2_report.html'
    assert report_path.exists(), f'Report not found at {report_path}'
    html = report_path.read_text(encoding='utf-8')

    # Should have multiple <img> tags (all default plots)
    img_tags = re.findall(r'<img\s+src="([^"]+)"', html)
    assert len(img_tags) > 5, (
        f'Expected many default plots, found only {len(img_tags)} <img> tags'
    )


@pytest.mark.pro_only
def test_pro_subset_plots_in_order(run_crispresso, cli_test_dir):
    """Config file with a subset of plots shows only those, in order.

    Verifies that exactly the listed plots appear in the report and
    in the order specified.
    """
    cmd = ' '.join([
        'CRISPResso',
        '-r1 inputs/FANC.Cas9.fastq',
        '-a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG',
        '-g GGAATCCCTTCTGCAGCACC',
        '-n pro-subset-plots',
        '--config_file inputs/subset_plots_config.json',
        '--use_matplotlib',
    ] + COMMON_FLAGS)

    result = run_crispresso(cmd)
    assert result.returncode == 0, (
        f'pro-subset-plots command failed (exit code {result.returncode}):\n'
        f'{result.stderr}'
    )

    report_path = cli_test_dir / 'CRISPResso_on_pro-subset-plots' / 'CRISPResso2_report.html'
    assert report_path.exists(), f'Report not found at {report_path}'
    html = report_path.read_text(encoding='utf-8')

    img_tags = re.findall(r'<img\s+src="([^"]+)"', html)
    # Config specifies: indel_size_distribution, read_barplot, alignment_pie_chart
    # (reverse of default order to verify ordering works)
    assert len(img_tags) == 3, (
        f'Expected exactly 3 <img> tags, found {len(img_tags)}: {img_tags}'
    )

    # Verify order: indel_size_distribution (3a) should come before read_barplot (1a)
    img_str = ' '.join(img_tags)
    pos_3a = img_str.find('3a.')
    pos_1a = img_str.find('1a.')
    pos_1b = img_str.find('1b.')
    assert pos_3a < pos_1a < pos_1b, (
        f'Expected indel_size_distribution before read_barplot before '
        f'alignment_pie_chart, got: {img_tags}'
    )
