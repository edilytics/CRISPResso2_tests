"""CLI integration tests for CRISPResso2, migrated from the Makefile."""
from dataclasses import dataclass, field
from typing import List

import pytest


@dataclass
class CLITestCase:
    id: str
    cmd: str
    output_dir: str
    marks: List[str] = field(default_factory=list)


TESTS = [
    # ── Core CRISPResso ──────────────────────────────────────────────
    CLITestCase(
        id='basic',
        cmd=(
            'CRISPResso -r1 inputs/FANC.Cas9.fastq'
            ' -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG'
            ' -g GGAATCCCTTCTGCAGCACC'
            ' --place_report_in_output_folder --halt_on_plot_fail --debug'
        ),
        output_dir='CRISPResso_on_FANC.Cas9',
        marks=['crispresso'],
    ),
    CLITestCase(
        id='params',
        cmd=(
            'CRISPResso -r1 inputs/FANC.Cas9.fastq'
            ' -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG'
            ' -g GGAATCCCTTCTGCAGCACC'
            ' -e CGGCCGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCTGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG'
            ' -c GGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTT'
            ' --dump -qwc 20-30_45-50 -q 30 --default_min_aln_score 80'
            ' -an FANC -n params --base_editor_output'
            ' -fg AGCCTTGCAGTGGGCGCGCTA,CCCACTGAAGGCCC'
            ' --dsODN GCTAGATTTCCCAAGAAGA -gn hi -fgn dear -p max'
            ' --place_report_in_output_folder'
            ' --base_editor_consider_changes_outside_qw'
            ' --halt_on_plot_fail --debug'
        ),
        output_dir='CRISPResso_on_params',
        marks=['crispresso'],
    ),
    CLITestCase(
        id='nhej_native_merge',
        cmd=(
            'CRISPResso -r1 inputs/nhej.r1.fastq.gz -r2 inputs/nhej.r2.fastq.gz'
            ' -a AATGTCCCCCAATGGGAAGTTCATCTGGCACTGCCCACAGGTGAGGAGGTCATGATCCCCTTCTGGAGCTCCCAACGGGCCGTGGTCTGGTTCATCATCTGTAAGAATGGCTTCAAGAGGCTCGGCTGTGGTT'
            ' -n nhej_native_merge --crispresso_merge'
            ' --place_report_in_output_folder --halt_on_plot_fail --debug'
        ),
        output_dir='CRISPResso_on_nhej_native_merge',
        marks=['crispresso'],
    ),
    CLITestCase(
        id='prime_editor',
        cmd=(
            'CRISPResso --fastq_r1 inputs/prime_editor.fastq.gz'
            ' --amplicon_seq ACGTCTCATATGCCCCTTGGCAGTCATCTTAGTCATTACCTGAGGTGTTCGTTGTAACTCATATAAACTGAGTTCCCATGTTTTGCTTAATGGTTGAGTTCCGTTTGTCTGCACAGCCTGAGACATTGCTGGAAATAAAGAAGAGAGAAAAACAATTTTAGTATTTGGAAGGGAAGTGCTATGGTCTGAATGTATGTGTCCCACCAAAATTCCTACGT'
            ' --prime_editing_pegRNA_spacer_seq GTCATCTTAGTCATTACCTG'
            ' --prime_editing_pegRNA_extension_seq AACGAACACCTCATGTAATGACTAAGATG'
            ' --prime_editing_nicking_guide_seq CTCAACCATTAAGCAAAACAT'
            ' --prime_editing_pegRNA_scaffold_seq GTTTTAGAGCTAGAAATAGCAAGTTAAAATAAGGCTAGTCCGTTATCAACTTGAAAAAGTGGCACCGAGTCGGTGC'
            ' --write_cleaned_report'
            ' --place_report_in_output_folder --halt_on_plot_fail --debug'
        ),
        output_dir='CRISPResso_on_prime_editor',
        marks=['crispresso'],
    ),
    CLITestCase(
        id='base_editor',
        cmd=(
            'CRISPResso -r1 inputs/FANC.Cas9.fastq'
            ' -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG'
            ' -g GGAATCCCTTCTGCAGCACC'
            ' -e CGGCCGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCTGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG'
            ' -c GGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTT'
            ' --dump -q 30 --default_min_aln_score 80'
            ' -an FANC -n base_editor --base_editor_output'
            ' -fg AGCCTTGCAGTGGGCGCGCTA,CCCACTGAAGGCCC'
            ' --dsODN GCTAGATTTCCCAAGAAGA -gn hi -fgn dear -p max'
            ' --place_report_in_output_folder --halt_on_plot_fail --debug'
        ),
        output_dir='CRISPResso_on_base_editor',
        marks=['crispresso'],
    ),
    # ── Parallel / process variants ──────────────────────────────────
    CLITestCase(
        id='basic_parallel',
        cmd=(
            'CRISPResso -r1 inputs/FANC.Cas9.fastq'
            ' -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG'
            ' -g GGAATCCCTTCTGCAGCACC'
            ' --place_report_in_output_folder --debug -p 2 -n basic-parallel'
            ' --halt_on_plot_fail'
        ),
        output_dir='CRISPResso_on_basic-parallel',
        marks=['crispresso'],
    ),
    # ── Asymmetric ───────────────────────────────────────────────────
    CLITestCase(
        id='asym_both',
        cmd=(
            'CRISPResso -r1 inputs/asym.fastq'
            ' -a GACATACATACA -g GACATACATACA'
            ' --exclude_bp_from_left 0 --exclude_bp_from_right 0'
            ' -n asym_both'
            ' --place_report_in_output_folder --halt_on_plot_fail --debug'
        ),
        output_dir='CRISPResso_on_asym_both',
        marks=['crispresso'],
    ),
    CLITestCase(
        id='asym_left',
        cmd=(
            'CRISPResso -r1 inputs/FANC.Cas9.fastq'
            ' -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG'
            ' -g CGGATGTTCCAATCAGTACG --exclude_bp_from_left 0'
            ' -n asym_left'
            ' --place_report_in_output_folder --halt_on_plot_fail --debug'
        ),
        output_dir='CRISPResso_on_asym_left',
        marks=['crispresso'],
    ),
    CLITestCase(
        id='asym_right',
        cmd=(
            'CRISPResso -r1 inputs/FANC.Cas9.fastq'
            ' -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG'
            ' -g TCCATCGGCGCTTTGGTCGG --exclude_bp_from_right 0'
            ' -n asym_right'
            ' --place_report_in_output_folder --halt_on_plot_fail --debug'
        ),
        output_dir='CRISPResso_on_asym_right',
        marks=['crispresso'],
    ),
    # ── BAM input ────────────────────────────────────────────────────
    CLITestCase(
        id='bam',
        cmd=(
            'CRISPResso --bam_input inputs/Both.Cas9.fastq.smallGenome.bam'
            ' --bam_chr_loc chr9 --auto --name bam --n_processes 2'
            ' --place_report_in_output_folder --halt_on_plot_fail --debug'
        ),
        output_dir='CRISPResso_on_bam',
        marks=['bam'],
    ),
    CLITestCase(
        id='bam_single',
        cmd=(
            'CRISPResso --bam_input inputs/Both.Cas9.fastq.smallGenome.bam'
            ' --bam_chr_loc chr9 --auto --n_processes 1'
            ' --place_report_in_output_folder --debug -n bam-single'
            ' --halt_on_plot_fail'
        ),
        output_dir='CRISPResso_on_bam-single',
        marks=['bam'],
    ),
    # ── BAM output ───────────────────────────────────────────────────
    CLITestCase(
        id='bam_out',
        cmd=(
            'CRISPResso -r1 inputs/bam_test.fq'
            ' -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTC,GGAAACGCCCATGCAATTAGTCTATTTCTGCTGCAAGTAAGCATGCATTTGTAGGCTTGATGCTTTTTTTCTGCTTCTCCAGCCCT'
            ' --bam_output --halt_on_plot_fail --debug -n bam-out'
            ' --place_report_in_output_folder'
        ),
        output_dir='CRISPResso_on_bam-out',
        marks=['bam'],
    ),
    CLITestCase(
        id='bam_out_genome',
        cmd=(
            'CRISPResso -r1 inputs/bam_test.fq'
            ' -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTC,GGAAACGCCCATGCAATTAGTCTATTTCTGCTGCAAGTAAGCATGCATTTGTAGGCTTGATGCTTTTTTTCTGCTTCTCCAGCCCT'
            ' --bam_output --debug -n bam-out-genome'
            ' -x inputs/small_genome/smallGenome'
            ' --place_report_in_output_folder --halt_on_plot_fail'
        ),
        output_dir='CRISPResso_on_bam-out-genome',
        marks=['bam'],
    ),
    CLITestCase(
        id='bam_out_parallel',
        cmd=(
            'CRISPResso -r1 inputs/bam_test.fq'
            ' -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTC,GGAAACGCCCATGCAATTAGTCTATTTCTGCTGCAAGTAAGCATGCATTTGTAGGCTTGATGCTTTTTTTCTGCTTCTCCAGCCCT'
            ' --bam_output --debug -n bam-out-parallel --n_processes max'
            ' --place_report_in_output_folder --halt_on_plot_fail'
        ),
        output_dir='CRISPResso_on_bam-out-parallel',
        marks=['bam'],
    ),
    CLITestCase(
        id='basic_write_bam_out',
        cmd=(
            'CRISPResso -r1 inputs/FANC.Cas9.fastq'
            ' -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG'
            ' -g GGAATCCCTTCTGCAGCACC'
            ' --place_report_in_output_folder --debug --bam_output'
            ' -n basic-write-bam-out --halt_on_plot_fail'
        ),
        output_dir='CRISPResso_on_basic-write-bam-out',
        marks=['bam'],
    ),
    CLITestCase(
        id='basic_write_bam_out_parallel',
        cmd=(
            'CRISPResso -r1 inputs/FANC.Cas9.fastq'
            ' -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG'
            ' -g GGAATCCCTTCTGCAGCACC'
            ' --place_report_in_output_folder --debug --bam_output'
            ' --n_processes 2 -n basic-write-bam-out-parallel'
            ' --halt_on_plot_fail'
        ),
        output_dir='CRISPResso_on_basic-write-bam-out-parallel',
        marks=['bam'],
    ),
    # ── Batch ────────────────────────────────────────────────────────
    CLITestCase(
        id='batch',
        cmd=(
            'CRISPRessoBatch -bs inputs/FANC.batch'
            ' -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG'
            ' -g GGAATCCCTTCTGCAGCACC'
            ' --halt_on_plot_fail --debug'
            ' --place_report_in_output_folder --base_editor_output'
        ),
        output_dir='CRISPRessoBatch_on_FANC',
        marks=['batch'],
    ),
    CLITestCase(
        id='batch_failing',
        cmd=(
            'CRISPRessoBatch -bs inputs/FANC_failing.batch'
            ' -n batch-failing'
            ' -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG'
            ' -g GGAATCCCTTCTGCAGCACC'
            ' --debug --place_report_in_output_folder'
            ' --base_editor_output --skip_failed --halt_on_plot_fail'
        ),
        output_dir='CRISPRessoBatch_on_batch-failing',
        marks=['batch'],
    ),
    # ── Pooled ───────────────────────────────────────────────────────
    CLITestCase(
        id='pooled',
        cmd=(
            'CRISPRessoPooled -r1 inputs/Both.Cas9.fastq'
            ' -f inputs/Cas9.amplicons.txt'
            ' --keep_intermediate --min_reads_to_use_region 100 -p 4'
            ' --place_report_in_output_folder --halt_on_plot_fail --debug'
        ),
        output_dir='CRISPRessoPooled_on_Both.Cas9',
        marks=['pooled'],
    ),
    CLITestCase(
        id='pooled_paired_sim',
        cmd=(
            'CRISPRessoPooled -r1 inputs/simulated.trim_reqd.r1.fq'
            ' -r2 inputs/simulated.trim_reqd.r2.fq'
            ' -f inputs/simulated.amplicons.txt'
            ' --place_report_in_output_folder --debug'
            ' --min_reads_to_use_region 10 --trim_sequences --keep_intermediate'
            ' -n pooled-paired-sim --halt_on_plot_fail'
        ),
        output_dir='CRISPRessoPooled_on_pooled-paired-sim',
        marks=['pooled'],
    ),
    CLITestCase(
        id='pooled_mixed_mode',
        cmd=(
            'CRISPRessoPooled -r1 inputs/Both.Cas9.genome.fastq'
            ' -x inputs/small_genome/smallGenome'
            ' -f inputs/Cas9.amplicons.genome.txt'
            ' --keep_intermediate --min_reads_to_use_region 100'
            ' --halt_on_plot_fail --debug -n pooled-mixed-mode'
            ' --place_report_in_output_folder'
        ),
        output_dir='CRISPRessoPooled_on_pooled-mixed-mode',
        marks=['pooled'],
    ),
    CLITestCase(
        id='pooled_mixed_mode_genome_demux',
        cmd=(
            'CRISPRessoPooled -r1 inputs/Both.Cas9.genome.fastq'
            ' -x inputs/small_genome/smallGenome'
            ' -f inputs/Cas9.amplicons.genome.txt'
            ' --keep_intermediate --min_reads_to_use_region 100'
            ' --debug -n pooled-mixed-mode-genome-demux'
            ' --place_report_in_output_folder --demultiplex_genome_wide'
            ' --halt_on_plot_fail'
        ),
        output_dir='CRISPRessoPooled_on_pooled-mixed-mode-genome-demux',
        marks=['pooled'],
    ),
    # ── WGS ──────────────────────────────────────────────────────────
    CLITestCase(
        id='wgs',
        cmd=(
            'CRISPRessoWGS -b inputs/Both.Cas9.fastq.smallGenome.bam'
            ' -r inputs/small_genome/smallGenome.fa'
            ' -f inputs/Cas9.regions.txt'
            ' --place_report_in_output_folder --halt_on_plot_fail --debug'
        ),
        output_dir='CRISPRessoWGS_on_Both.Cas9.fastq.smallGenome',
        marks=['wgs'],
    ),
    # ── VCF ──────────────────────────────────────────────────────────
    CLITestCase(
        id='vcf_basic',
        cmd=(
            'CRISPResso -r1 inputs/vcf_basic.fastq'
            ' -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG'
            ' -g GGAATCCCTTCTGCAGCACC'
            ' --quantification_window_coordinates 89-95'
            ' --vcf_output --amplicon_coordinates FANC:1'
            ' -n vcf-basic'
            ' --place_report_in_output_folder --debug'
        ),
        output_dir='CRISPResso_on_vcf-basic',
        marks=['vcf'],
    ),
    CLITestCase(
        id='vcf_deletions_only',
        cmd=(
            'CRISPResso -r1 inputs/vcf_deletions.fastq'
            ' -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG'
            ' -g GGAATCCCTTCTGCAGCACC'
            ' --vcf_output --amplicon_coordinates FANC:1'
            ' --quantification_window_coordinates 89-94'
            ' -n vcf-deletions-only'
            ' --place_report_in_output_folder --debug'
        ),
        output_dir='CRISPResso_on_vcf-deletions-only',
        marks=['vcf'],
    ),
    CLITestCase(
        id='vcf_insertions_only',
        cmd=(
            'CRISPResso -r1 inputs/vcf_insertions.fastq'
            ' -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG'
            ' -g GGAATCCCTTCTGCAGCACC'
            ' --quantification_window_coordinates 89-95'
            ' --vcf_output --amplicon_coordinates FANC:1'
            ' -n vcf-insertions-only'
            ' --place_report_in_output_folder --debug'
        ),
        output_dir='CRISPResso_on_vcf-insertions-only',
        marks=['vcf'],
    ),
    CLITestCase(
        id='vcf_no_edits',
        cmd=(
            'CRISPResso -r1 inputs/vcf_no_edits.fastq'
            ' -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG'
            ' -g GGAATCCCTTCTGCAGCACC'
            ' --vcf_output --amplicon_coordinates FANC:1'
            ' -n vcf-no-edits'
            ' --place_report_in_output_folder --debug'
        ),
        output_dir='CRISPResso_on_vcf-no-edits',
        marks=['vcf'],
    ),
    CLITestCase(
        id='vcf_multi_amplicon',
        cmd=(
            'CRISPResso -r1 inputs/vcf_multi_amplicon.fastq'
            ' -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG,TACGGGTATTACCCGCGTTTAGTGGCTAGCGACTCGTGGACTTGCTGTACTGTCTACGGGCGTCAACTTGATAATCCCAAAAAAGCTTGGCCCCGCACAACTCGTTGAGCAATTCTTAAAAAGATGGTGTACGTCCCTCATACTTCGTATTCAATAAACCCGGTTAGACCATTGGGTGCGTGATGCTGCATTGCCTTGCA'
            ' -an AMP1,AMP2'
            ' -g GGAATCCCTTCTGCAGCACC,CCCCGCACAACTCGTTGAGC'
            ' --vcf_output --quantification_window_coordinates 89-95,104-109'
            ' --amplicon_coordinates chr1:1000,chr2:5000'
            ' -n vcf-multi-amplicon'
            ' --place_report_in_output_folder --debug'
        ),
        output_dir='CRISPResso_on_vcf-multi-amplicon',
        marks=['vcf'],
    ),
    CLITestCase(
        id='vcf_base_edit_cbe',
        cmd=(
            'CRISPResso -r1 inputs/vcf_base_edit_cbe.fastq'
            ' -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG'
            ' -g GGAATCCCTTCTGCAGCACC'
            ' --vcf_output --amplicon_coordinates FANC:1'
            ' --quantification_window_coordinates 76-96'
            ' -n vcf-base-edit-cbe'
            ' --place_report_in_output_folder --debug'
        ),
        output_dir='CRISPResso_on_vcf-base-edit-cbe',
        marks=['vcf'],
    ),
    CLITestCase(
        id='vcf_base_edit_abe',
        cmd=(
            'CRISPResso -r1 inputs/vcf_base_edit_abe.fastq'
            ' -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG'
            ' -g GGAATCCCTTCTGCAGCACC'
            ' --vcf_output --amplicon_coordinates FANC:1'
            ' --quantification_window_coordinates 76-96'
            ' -n vcf-base-edit-abe'
            ' --place_report_in_output_folder --debug'
        ),
        output_dir='CRISPResso_on_vcf-base-edit-abe',
        marks=['vcf'],
    ),
    CLITestCase(
        id='vcf_prime_edit_basic',
        cmd=(
            'CRISPResso -r1 inputs/vcf_prime_edit_basic.fastq'
            ' -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG'
            ' -g GGAATCCCTTCTGCAGCACC'
            ' --prime_editing_pegRNA_spacer_seq GGAATCCCTTCTGCAGCACC'
            ' --prime_editing_pegRNA_extension_seq ATCTGGATCGGCTGCAGAAGGGA'
            ' --vcf_output --amplicon_coordinates FANC:1,FANC_PE:1'
            ' -n vcf-prime-edit-basic'
            ' --place_report_in_output_folder --debug'
        ),
        output_dir='CRISPResso_on_vcf-prime-edit-basic',
        marks=['vcf'],
    ),
]


def _make_params():
    """Build pytest.param list with proper markers from CLITestCase instances."""
    mark_map = {
        'crispresso': pytest.mark.crispresso,
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
        params.append(pytest.param(tc, id=tc.id, marks=marks))
    return params


@pytest.mark.parametrize('test_case', _make_params())
def test_crispresso_cli(test_case, run_crispresso, assert_no_diff, cli_test_dir):
    result = run_crispresso(test_case.cmd)
    assert result.returncode == 0, (
        f'{test_case.id} command failed (exit code {result.returncode}):\n'
        f'{result.stderr}'
    )
    actual = cli_test_dir / test_case.output_dir
    assert_no_diff(actual)


@pytest.mark.compare
def test_compare(run_crispresso, assert_no_diff, cli_test_dir):
    """CRISPRessoCompare — requires batch output from test_crispresso_cli[batch]."""
    batch_dir = cli_test_dir / 'CRISPRessoBatch_on_FANC'
    if not batch_dir.exists():
        pytest.skip('Batch output not found; run batch test first')
    result = run_crispresso(
        'CRISPRessoCompare'
        ' CRISPRessoBatch_on_FANC/CRISPResso_on_Cas9/'
        ' CRISPRessoBatch_on_FANC/CRISPResso_on_Untreated/'
        ' --place_report_in_output_folder --halt_on_plot_fail --debug'
    )
    assert result.returncode == 0, (
        f'compare command failed (exit code {result.returncode}):\n'
        f'{result.stderr}'
    )
    assert_no_diff(cli_test_dir / 'CRISPRessoCompare_on_Cas9_VS_Untreated')


@pytest.mark.aggregate
def test_aggregate(run_crispresso, assert_no_diff, cli_test_dir):
    """CRISPRessoAggregate — requires batch output from test_crispresso_cli[batch]."""
    batch_dir = cli_test_dir / 'CRISPRessoBatch_on_FANC'
    if not batch_dir.exists():
        pytest.skip('Batch output not found; run batch test first')
    result = run_crispresso(
        'CRISPRessoAggregate'
        ' -p CRISPRessoBatch_on_FANC/CRISPResso_on_'
        ' -n aggregate --debug'
        ' --place_report_in_output_folder --halt_on_plot_fail'
    )
    assert result.returncode == 0, (
        f'aggregate command failed (exit code {result.returncode}):\n'
        f'{result.stderr}'
    )
    assert_no_diff(cli_test_dir / 'CRISPRessoAggregate_on_aggregate')
