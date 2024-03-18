.PHONY: all install test test_cli_integration clean clean_cli_integration \
	basic params batch pooled wgs compare

CRISPRESSO2_DIR := ../CRISPResso2
CRISPRESSO2_SOURCES := $(wildcard $(CRISPRESSO2_DIR)/CRISPResso2/*.py*)
TEST_CLI_INTEGRATION_DIRECTORIES := $(addprefix cli_integration_tests/,CRISPResso_on_FANC.Cas9 \
CRISPResso_on_bam CRISPResso_on_params \
CRISPRessoBatch_on_FANC CRISPRessoPooled_on_Both.Cas9 \
CRISPRessoWGS_on_Both.Cas9.fastq.smallGenome \
CRISPResso_on_hdr_insertion \
CRISPResso_on_prime_editor \
CRISPRessoBatch_on_batch-failing \
CRISPRessoPooled_on_pooled-mixed-mode \
CRISPRessoCompare_on_Cas9_VS_Untreated)

all: test

install: $(CRISPRESSO2_SOURCES)
	cd $(CRISPRESSO2_DIR) && output=`pip install -e .` || echo "$$output"

test: clean basic-test params-test prime-editor-test batch-test pooled-test wgs-test compare-test

run: $(TEST_CLI_INTEGRATION_DIRECTORIES)

clean: clean_cli_integration

clean_cli_integration:
	rm -rf cli_integration_tests/CRISPResso_on_FANC.Cas9* \
cli_integration_tests/CRISPResso_on_params* \
cli_integration_tests/CRISPResso_on_bam* \
cli_integration_tests/CRISPRessoBatch_on_FANC* \
cli_integration_tests/CRISPRessoPooled_on_Both.Cas9* \
cli_integration_tests/CRISPRessoWGS_on_Both.Cas9.fastq.smallGenome* \
cli_integration_tests/CRISPRessoCompare_on_Cas9_VS_Untreated* \
cli_integration_tests/CRISPRessoPooled_on_prime.editing* \
cli_integration_tests/CRISPRessoBatch_on_large_batch* \
cli_integration_tests/CRISPResso_on_hdr_insertion* \
cli_integration_tests/CRISPResso_on_prime_editor* \
cli_integration_tests/CRISPRessoBatch_on_batch-failing* \
cli_integration_tests/CRISPRessoPooled_on_pooled-mixed-mode* \
web_tests/stress_test_log.txt \
web_tests/UI_docker_log.txt \
web_tests/UI_selenium_log.txt

basic: cli_integration_tests/CRISPResso_on_FANC.Cas9

basic-test: cli_integration_tests/CRISPResso_on_FANC.Cas9
	python diff.py $^ --expected cli_integration_tests/expected_results/CRISPResso_on_FANC.Cas9

cli_integration_tests/CRISPResso_on_FANC.Cas9: install cli_integration_tests/inputs/FANC.Cas9.fastq
	cd cli_integration_tests && output=`CRISPResso -r1 inputs/FANC.Cas9.fastq -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -g GGAATCCCTTCTGCAGCACC --place_report_in_output_folder --debug 2>&1` || echo "$$output"

bam: cli_integration_tests/CRISPResso_on_bam

bam-test: cli_integration_tests/CRISPResso_on_bam
	python diff.py $^ --expected cli_integration_tests/expected_results/CRISPResso_on_bam

cli_integration_tests/CRISPResso_on_bam: install cli_integration_tests/inputs/Both.Cas9.fastq.smallGenome.bam
	cd cli_integration_tests && output=`CRISPResso --bam_input inputs/Both.Cas9.fastq.smallGenome.bam --bam_chr_loc chr9 --auto --name bam --n_processes max --place_report_in_output_folder --debug 2>&1` || echo "$$output"

params: cli_integration_tests/CRISPResso_on_params

params-test: cli_integration_tests/CRISPResso_on_params
	python diff.py $^ --expected cli_integration_tests/expected_results/CRISPResso_on_params

cli_integration_tests/CRISPResso_on_params: install cli_integration_tests/inputs/FANC.Cas9.fastq
	cd cli_integration_tests && output=`CRISPResso -r1 inputs/FANC.Cas9.fastq -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -g GGAATCCCTTCTGCAGCACC -e CGGCCGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCTGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -c GGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTT --dump -qwc 20-30_45-50 -q 30 --default_min_aln_score 80 -an FANC -n params --base_edit -fg AGCCTTGCAGTGGGCGCGCTA,CCCACTGAAGGCCC --dsODN GCTAGATTTCCCAAGAAGA -gn hi -fgn dear -p max --place_report_in_output_folder --debug 2>&1` || echo "$$output"

nhej: cli_integration_tests/CRISPResso_on_nhej

nhej-test: cli_integration_tests/CRISPResso_on_nhej

cli_integration_tests/CRISPResso_on_nhej: install cli_integration_tests/
	cd cli_integration_tests && CRISPResso -r1 inputs/nhej.r1.fastq.gz -r2 inputs/nhej.r2.fastq.gz -a AATGTCCCCCAATGGGAAGTTCATCTGGCACTGCCCACAGGTGAGGAGGTCATGATCCCCTTCTGGAGCTCCCAACGGGCCGTGGTCTGGTTCATCATCTGTAAGAATGGCTTCAAGAGGCTCGGCTGTGGTT -n nhej --process_paired_fastq --place_report_in_output_folder --debug # || echo "$$output"

batch: cli_integration_tests/CRISPRessoBatch_on_FANC

batch-test: cli_integration_tests/CRISPRessoBatch_on_FANC
	python diff.py $^ --expected cli_integration_tests/expected_results/CRISPRessoBatch_on_FANC

cli_integration_tests/CRISPRessoBatch_on_FANC: install cli_integration_tests/inputs/FANC.batch
	cd cli_integration_tests && output=`CRISPRessoBatch -bs inputs/FANC.batch -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -g GGAATCCCTTCTGCAGCACC --debug --place_report_in_output_folder --base_editor 2>&1` || echo "$$output"

large-batch: cli_integration_tests/CRISPRessoBatch_on_large_batch

cli_integration_tests/CRISPRessoBatch_on_large_batch: install cli_integration_tests/inputs/FANC_large.batch
	cd cli_integration_tests && CRISPRessoBatch -bs inputs/FANC_large.batch -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -g GGAATCCCTTCTGCAGCACC --debug --no_rerun --base_editor -p 4 -n large_batch --place_report_in_output_folder # 2>&1` || echo "$$output"

pooled: cli_integration_tests/CRISPRessoPooled_on_Both.Cas9

pooled-test: cli_integration_tests/CRISPRessoPooled_on_Both.Cas9
	python diff.py $^ --expected cli_integration_tests/expected_results/CRISPRessoPooled_on_Both.Cas9

cli_integration_tests/CRISPRessoPooled_on_Both.Cas9: install cli_integration_tests/inputs/Both.Cas9.fastq cli_integration_tests/inputs/Cas9.amplicons.txt
	cd cli_integration_tests && output=`CRISPRessoPooled -r1 inputs/Both.Cas9.fastq -f inputs/Cas9.amplicons.txt --keep_intermediate --min_reads_to_use_region 100 -p 4 --place_report_in_output_folder --debug 2>&1` || echo "$$output"

pooled-prime-editing: cli_integration_tests/CRISPRessoPooled_on_prime.editing

pooled-prime-editing-test: cli_integration_tests/CRISPRessoPooled_on_prime.editing
	python diff.py $^ --expected cli_integration_tests/expected_results/CRISPRessoPooled_on_prime.editing

cli_integration_tests/CRISPRessoPooled_on_prime.editing: install cli_integration_tests/inputs/prime.editing.fastq cli_integration_tests/inputs/prime.editing.amplicons.txt
	cd cli_integration_tests && output=`CRISPRessoPooled -r1 inputs/prime.editing.fastq -f inputs/prime.editing.amplicons.txt --keep_intermediate --min_reads_to_use_region 1 --place_report_in_output_folder --debug 2>&1` || echo "$$output"

wgs: cli_integration_tests/CRISPRessoWGS_on_Both.Cas9.fastq.smallGenome

wgs-test: cli_integration_tests/CRISPRessoWGS_on_Both.Cas9.fastq.smallGenome
	python diff.py $^ --expected cli_integration_tests/expected_results/CRISPRessoWGS_on_Both.Cas9.fastq.smallGenome

cli_integration_tests/CRISPRessoWGS_on_Both.Cas9.fastq.smallGenome: install cli_integration_tests/inputs/Both.Cas9.fastq.smallGenome.bam cli_integration_tests/inputs/small_genome/smallGenome.fa cli_integration_tests/inputs/Cas9.regions.txt
	cd cli_integration_tests && output=`CRISPRessoWGS -b inputs/Both.Cas9.fastq.smallGenome.bam -r inputs/small_genome/smallGenome.fa -f inputs/Cas9.regions.txt --place_report_in_output_folder --debug 2>&1` || echo "$$output"

compare: cli_integration_tests/CRISPRessoCompare_on_Cas9_VS_Untreated

compare-test: cli_integration_tests/CRISPRessoCompare_on_Cas9_VS_Untreated
	python diff.py $^ --expected cli_integration_tests/expected_results/CRISPRessoCompare_on_Cas9_VS_Untreated

cli_integration_tests/CRISPRessoCompare_on_Cas9_VS_Untreated: install cli_integration_tests/CRISPRessoBatch_on_FANC
	cd cli_integration_tests && output=`CRISPRessoCompare CRISPRessoBatch_on_FANC/CRISPResso_on_Cas9/ CRISPRessoBatch_on_FANC/CRISPResso_on_Untreated/ --place_report_in_output_folder --debug 2>&1` || echo "$$output"

stress: web_tests/web_stress_test.py
	python $^

web_ui: web_tests/CRISPResso_Web_UI_Tests/web_ui_test.py
	python $^ --log_file_path web_tests/UI_test_summary_log.txt

.PHONY: pooled-mixed-mode
pooled-mixed-mode: cli_integration_tests/CRISPRessoPooled_on_pooled-mixed-mode

.PHONY: pooled-mixed-mode-test
pooled-mixed-mode-test: cli_integration_tests/CRISPRessoPooled_on_pooled-mixed-mode
	python diff.py $^ --expected cli_integration_tests/expected_results/CRISPRessoPooled_on_pooled-mixed-mode && echo "$@ test passed!"

cli_integration_tests/CRISPRessoPooled_on_pooled-mixed-mode: install cli_integration_tests/inputs/Both.Cas9.fastq cli_integration_tests/inputs/ cli_integration_tests/inputs/ cli_integration_tests/inputs/Cas9.amplicons.txt
	cd cli_integration_tests && output=`CRISPRessoPooled -r1 inputs/Both.Cas9.fastq -x inputs/small_genome/smallGenome -f inputs/Cas9.amplicons.txt --keep_intermediate --min_reads_to_use_region 100 --debug -n pooled-mixed-mode --place_report_in_output_folder 2>&1` || echo "$$output"

.PHONY: batch-failing
batch-failing: cli_integration_tests/CRISPRessoBatch_on_batch-failing

.PHONY: batch-failing-test
batch-failing-test: cli_integration_tests/CRISPRessoBatch_on_batch-failing
	python diff.py $^ --expected cli_integration_tests/expected_results/CRISPRessoBatch_on_batch-failing && echo "$@ test passed!"

cli_integration_tests/CRISPRessoBatch_on_batch-failing: install cli_integration_tests/inputs/ cli_integration_tests/inputs/ cli_integration_tests/inputs/ cli_integration_tests/inputs/FANC_failing.batch
	cd cli_integration_tests && output=`CRISPRessoBatch -bs inputs/FANC_failing.batch -n batch-failing -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -g GGAATCCCTTCTGCAGCACC --debug --place_report_in_output_folder --base_editor --skip_failed 2>&1` || echo "$$output"
.PHONY: prime-editor
prime-editor: cli_integration_tests/CRISPResso_on_prime_editor

.PHONY: prime-editor-test
prime-editor-test: cli_integration_tests/CRISPResso_on_prime_editor
	python diff.py $^ --expected cli_integration_tests/expected_results/CRISPResso_on_prime_editor && echo "$@ test passed!"

cli_integration_tests/CRISPResso_on_prime_editor: install cli_integration_tests/inputs/prime_editor.fastq.gz cli_integration_tests/inputs/ cli_integration_tests/inputs/
	cd cli_integration_tests && output=`CRISPResso --fastq_r1 inputs/prime_editor.fastq.gz --amplicon_seq ACGTCTCATATGCCCCTTGGCAGTCATCTTAGTCATTACCTGAGGTGTTCGTTGTAACTCATATAAACTGAGTTCCCATGTTTTGCTTAATGGTTGAGTTCCGTTTGTCTGCACAGCCTGAGACATTGCTGGAAATAAAGAAGAGAGAAAAACAATTTTAGTATTTGGAAGGGAAGTGCTATGGTCTGAATGTATGTGTCCCACCAAAATTCCTACGT --prime_editing_pegRNA_spacer_seq GTCATCTTAGTCATTACCTG --prime_editing_pegRNA_extension_seq AACGAACACCTCATGTAATGACTAAGATG --prime_editing_nicking_guide_seq CTCAACCATTAAGCAAAACAT --prime_editing_pegRNA_scaffold_seq GTTTTAGAGCTAGAAATAGCAAGTTAAAATAAGGCTAGTCCGTTATCAACTTGAAAAAGTGGCACCGAGTCGGTGC --write_cleaned_report --place_report_in_output_folder --debug 2>&1` || echo "$$output"

.PHONY: hdr-insertion
hdr-insertion: cli_integration_tests/CRISPResso_on_hdr-insertion

.PHONY: hdr-insertion-test
hdr-insertion-test: cli_integration_tests/CRISPResso_on_hdr-insertion
	python diff.py $^ --expected cli_integration_tests/expected_results/CRISPResso_on_hdr-insertion && echo "$@ test passed!"

# Deletion in middle
cli_integration_tests/CRISPResso_on_hdr-insertion: install cli_integration_tests/inputs/FANC.Cas9.fastq cli_integration_tests/inputs/ cli_integration_tests/inputs/
	cd cli_integration_tests && CRISPResso -r1 inputs/HDR_insertion.fastq -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCTGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG,CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -g GGAATCCCTTCTGCAGCACC -c GGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTT --dump -qwc 20-30_175-185 -q 30 --default_min_aln_score 80 -an FANC,HDR -n hdr-insertion --base_edit -fg AGCCTTGCAGTGGGCGCGCTA,CCCACTGAAGGCCC --dsODN GCTAGATTTCCCAAGAAGA -gn hi -fgn dear -p max --place_report_in_output_folder --debug --exclude_bp_from_right 0 --debug # 2>&1` || echo "$$output"

# Insertion in middle
# cli_integration_tests/CRISPResso_on_hdr-insertion: install cli_integration_tests/inputs/FANC.Cas9.fastq cli_integration_tests/inputs/ cli_integration_tests/inputs/
# 	cd cli_integration_tests && CRISPResso -r1 inputs/HDR_insertion.fastq -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG,CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCTGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -g GGAATCCCTTCTGCAGCACC -c GGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTT --dump -qwc 20-30_213-222 -q 30 --default_min_aln_score 80 -an FANC,HDR -n hdr-insertion --base_edit -fg AGCCTTGCAGTGGGCGCGCTA,CCCACTGAAGGCCC --dsODN GCTAGATTTCCCAAGAAGA -gn hi -fgn dear -p max --place_report_in_output_folder --debug --exclude_bp_from_right 0 --debug # 2>&1` || echo "$$output"

# cli_integration_tests/CRISPResso_on_hdr-insertion: install cli_integration_tests/inputs/FANC.Cas9.fastq cli_integration_tests/inputs/ cli_integration_tests/inputs/
# 	cd cli_integration_tests && CRISPResso -r1 inputs/HDR_insertion.fastq -a AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCTGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG,CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -g GGAATCCCTTCTGCAGCACC -c GGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTT --dump -qwc 20-30_287-297 -q 30 --default_min_aln_score 80 -an FANC,HDR -n hdr-insertion --base_edit -fg AGCCTTGCAGTGGGCGCGCTA,CCCACTGAAGGCCC --dsODN GCTAGATTTCCCAAGAAGA -gn hi -fgn dear -p max --place_report_in_output_folder --debug --exclude_bp_from_right 0 --debug # 2>&1` || echo "$$output"

# Deletion at beginning
# cli_integration_tests/CRISPResso_on_hdr-insertion: install cli_integration_tests/inputs/FANC.Cas9.fastq cli_integration_tests/inputs/ cli_integration_tests/inputs/
# 	cd cli_integration_tests && CRISPResso -r1 inputs/HDR_insertion.fastq -a AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCTGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG,CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -g GGAATCCCTTCTGCAGCACC -c GGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTT --dump -qwc 20-30_175-185 -q 30 --default_min_aln_score 80 -an FANC,HDR -n hdr-insertion --base_edit -fg AGCCTTGCAGTGGGCGCGCTA,CCCACTGAAGGCCC --dsODN GCTAGATTTCCCAAGAAGA -gn hi -fgn dear -p max --place_report_in_output_folder --debug --exclude_bp_from_right 0 --debug # 2>&1` || echo "$$output"
