.PHONY: all install test test_cli_integration clean clean_cli_integration \
	basic params batch pooled wgs compare print update syn-gen-test syn-gen-e2e syn-gen-all

CRISPRESSO2_DIR ?= ../CRISPResso2
CRISPRESSO2_SOURCES := $(wildcard $(CRISPRESSO2_DIR)/CRISPResso2/*.py*)
TEST_CLI_INTEGRATION_DIRECTORIES := $(addprefix cli_integration_tests/,CRISPResso_on_FANC.Cas9 \
CRISPResso_on_bam CRISPResso_on_params \
CRISPRessoBatch_on_FANC CRISPRessoPooled_on_Both.Cas9 \
CRISPRessoWGS_on_Both.Cas9.fastq.smallGenome \
CRISPResso_on_vcf-prime-edit-basic \
CRISPResso_on_vcf-base-edit-abe \
CRISPResso_on_vcf-base-edit-cbe \
CRISPResso_on_vcf-multi-amplicon \
CRISPResso_on_vcf-no-edits \
CRISPResso_on_vcf-insertions-only \
CRISPResso_on_vcf-deletions-only \
CRISPResso_on_vcf-basic \
CRISPResso_on_base_editor \
CRISPResso_on_asym_right \
CRISPResso_on_asym_left \
CRISPResso_on_asym_both \
CRISPResso_on_basic-write-bam-out-parallel \
CRISPResso_on_basic-write-bam-out \
CRISPResso_on_bam-out-parallel \
CRISPResso_on_bam_single \
CRISPResso_on_basic-parallel \
CRISPResso_on_bam-out-genome \
CRISPResso_on_bam-out \
CRISPRessoAggregate_on_aggregate \
CRISPRessoPooled_on_pooled-paired-sim \
CRISPResso_on_prime_editor \
CRISPRessoBatch_on_batch-failing \
CRISPRessoPooled_on_pooled-mixed-mode \
CRISPRessoPooled_on_pooled-mixed-mode-genome-demux \
CRISPRessoCompare_on_Cas9_VS_Untreated)

# Allow skip_html to work either as a variable or goal
ifneq ($(filter skip_html,$(MAKECMDGOALS)),)
  SKIP_HTML_FLAG := --skip_html
  MAKECMDGOALS := $(filter-out skip_html,$(MAKECMDGOALS))
endif
ifdef skip_html
  SKIP_HTML_FLAG := --skip_html
endif

define RUN
if [ "$(filter print, $(MAKECMDGOALS))" != "" ]; then \
 $$cmd; \
else \
  output=`$$cmd 2>&1` || echo "$$output"; \
fi && \
if [ "$(filter test, $(MAKECMDGOALS))" != "" ]; then \
 python ../diff.py $(subst cli_integration_tests/,./,$@) --expected $(subst cli_integration_tests/,./expected_results/,$@) $(SKIP_HTML_FLAG); \
fi && \
if [ "$(filter update, $(MAKECMDGOALS))" != "" ]; then \
 python ../test_manager.py update $(subst cli_integration_tests/,./,$@) $(subst cli_integration_tests/,./expected_results/,$@); \
fi && \
if [ "$(filter update-all, $(MAKECMDGOALS))" != "" ]; then \
 yes | python ../test_manager.py update $(subst cli_integration_tests/,./,$@) $(subst cli_integration_tests/,./expected_results/,$@); \
fi
endef

all: clean basic params prime-editor batch pooled wgs compare pooled-paired-sim pooled-mixed-mode pooled-mixed-mode-genome-demux aggregate bam bam-out bam-out-genome basic-parallel bam-single bam-out-parallel basic-write-bam-out basic-write-bam-out-parallel asym-both asym-left asym-right nhej_native_merge base_editor vcf-basic vcf-deletions-only vcf-insertions-only vcf-no-edits vcf-multi-amplicon vcf-base-edit-cbe vcf-base-edit-abe vcf-prime-edit-basic

print:
	@echo " ";

test:
	@echo " ";

update:
	@echo " ";

update-all:
	@echo " ";

install: $(CRISPRESSO2_SOURCES)
	cd $(CRISPRESSO2_DIR) && output=`pip install -e .` || echo "$$output"

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
cli_integration_tests/CRISPResso_on_vcf-prime-edit-basic* \
cli_integration_tests/CRISPResso_on_vcf-base-edit-abe* \
cli_integration_tests/CRISPResso_on_vcf-base-edit-cbe* \
cli_integration_tests/CRISPResso_on_vcf-multi-amplicon* \
cli_integration_tests/CRISPResso_on_vcf-no-edits* \
cli_integration_tests/CRISPResso_on_vcf-insertions-only* \
cli_integration_tests/CRISPResso_on_vcf-deletions-only* \
cli_integration_tests/CRISPResso_on_vcf-basic* \
cli_integration_tests/CRISPResso_on_base_editor* \
cli_integration_tests/CRISPResso_on_asym_right* \
cli_integration_tests/CRISPResso_on_asym_left* \
cli_integration_tests/CRISPResso_on_asym_both* \
cli_integration_tests/CRISPResso_on_basic-write-bam-out-parallel* \
cli_integration_tests/CRISPResso_on_basic-write-bam-out* \
cli_integration_tests/CRISPResso_on_bam-out-parallel* \
cli_integration_tests/CRISPResso_on_bam-single* \
cli_integration_tests/CRISPResso_on_basic-parallel* \
cli_integration_tests/CRISPResso_on_bam-out-genome* \
cli_integration_tests/CRISPResso_on_bam-out-2* \
cli_integration_tests/CRISPRessoAggregate_on_aggregate* \
cli_integration_tests/CRISPRessoPooled_on_pooled-paired-sim* \
cli_integration_tests/CRISPResso_on_prime_editor* \
cli_integration_tests/CRISPRessoBatch_on_batch-failing* \
cli_integration_tests/CRISPRessoPooled_on_pooled-mixed-mode* \
web_tests/stress_test_log.txt \
web_tests/UI_docker_log.txt \
web_tests/UI_selenium_log.txt

code-tests: params params-big-code params-multi-code params-medium params-multiple-codes params-small

basic: cli_integration_tests/CRISPResso_on_FANC.Cas9

cli_integration_tests/CRISPResso_on_FANC.Cas9: install cli_integration_tests/inputs/FANC.Cas9.fastq
	cd cli_integration_tests && cmd="CRISPResso -r1 inputs/FANC.Cas9.fastq -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -g GGAATCCCTTCTGCAGCACC --place_report_in_output_folder --halt_on_plot_fail --debug"; $(RUN)

bam: cli_integration_tests/CRISPResso_on_bam
	cd cli_integration_tests && cmd="CRISPResso --bam_input inputs/Both.Cas9.fastq.smallGenome.bam --bam_chr_loc chr9 --auto --name bam --n_processes 2 --place_report_in_output_folder --debug"; $(RUN)

cli_integration_tests/CRISPResso_on_bam: install cli_integration_tests/inputs/Both.Cas9.fastq.smallGenome.bam
	cd cli_integration_tests && cmd="CRISPResso --bam_input inputs/Both.Cas9.fastq.smallGenome.bam --bam_chr_loc chr9 --auto --name bam --n_processes 2 --place_report_in_output_folder --halt_on_plot_fail --debug"; $(RUN)

params-big-code: cli_integration_tests/CRISPResso_on_params_big_code

cli_integration_tests/CRISPResso_on_params_big_code: install cli_integration_tests/inputs/FANC.Cas9.fastq
	cd cli_integration_tests && cmd="CRISPResso -r1 inputs/FANC.Cas9.fastq -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -g GGAATCCCTTCTGCAGCACC -e CGGCCGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCTGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -c GGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCG --dump -qwc 20-30_45-50 -q 30 --default_min_aln_score 80 -an FANC -n params-big-code --base_edit -fg AGCCTTGCAGTGGGCGCGCTA,CCCACTGAAGGCCC --dsODN GCTAGATTTCCCAAGAAGA -gn hi -fgn dear -p max --place_report_in_output_folder --debug"; $(RUN)

params-multi-code: cli_integration_tests/CRISPResso_on_params_multiple_code_regions

cli_integration_tests/CRISPResso_on_params_multiple_code_regions: install cli_integration_tests/inputs/FANC.Cas9.fastq
	cd cli_integration_tests && cmd="CRISPResso -r1 inputs/FANC.Cas9.fastq -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -g GGAATCCCTTCTGCAGCACC -e CGGCCGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCTGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -c GGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTT,ATGTTCCAATCAGTACGCAGAGAGTCG,ACCTGCGCCACATCCATCGGCGCTTTGGT --dump -qwc 20-30_45-50 -q 30 --default_min_aln_score 80 -an FANC -n params_multi_code --base_edit -fg AGCCTTGCAGTGGGCGCGCTA,CCCACTGAAGGCCC --dsODN GCTAGATTTCCCAAGAAGA -gn hi -fgn dear -p max --place_report_in_output_folder --debug"; $(RUN)


params-medium: cli_integration_tests/CRISPResso_on_params_medium

cli_integration_tests/CRISPResso_on_params_medium: install cli_integration_tests/inputs/FANC.Cas9.fastq
	cd cli_integration_tests && cmd="CRISPResso -r1 inputs/FANC.Cas9.fastq -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -g GGAATCCCTTCTGCAGCACC -e CGGCCGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCTGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -c GGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAA --dump -qwc 20-30_45-50 -q 30 --default_min_aln_score 80 -an FANC -n params_medium --base_edit -fg AGCCTTGCAGTGGGCGCGCTA,CCCACTGAAGGCCC --dsODN GCTAGATTTCCCAAGAAGA -gn hi -fgn dear -p max --place_report_in_output_folder --debug"; $(RUN)


params-small: cli_integration_tests/CRISPResso_on_params_small

cli_integration_tests/CRISPResso_on_params_small: install cli_integration_tests/inputs/FANC.Cas9.fastq
	cd cli_integration_tests && cmd="CRISPResso -r1 inputs/FANC.Cas9.fastq -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -g GGAATCCCTTCTGCAGCACC -e CGGCCGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCTGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -c GGGCCTTCGCGCACCTCATGGAATCCC --dump -qwc 20-30_45-50 -q 30 --default_min_aln_score 80 -an FANC -n params_small --base_edit -fg AGCCTTGCAGTGGGCGCGCTA,CCCACTGAAGGCCC --dsODN GCTAGATTTCCCAAGAAGA -gn hi -fgn dear -p max --place_report_in_output_folder --debug"; $(RUN)

params-multiple-codes: cli_integration_tests/CRISPResso_on_params_multiple_codes

cli_integration_tests/CRISPResso_on_params_multiple_codes: install cli_integration_tests/inputs/FANC.Cas9.fastq
	cd cli_integration_tests && cmd="CRISPResso -r1 inputs/FANC.Cas9.fastq -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -g GGAATCCCTTCTGCAGCACC -e CGGCCGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCTGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -c GGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGC,TGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAA --dump -qwc 20-30_45-50 -q 30 --default_min_aln_score 80 -an FANC -n params_multiple_codes --base_editor_output -fg AGCCTTGCAGTGGGCGCGCTA,CCCACTGAAGGCCC --dsODN GCTAGATTTCCCAAGAAGA -gn hi -fgn dear -p max --place_report_in_output_folder --debug"; $(RUN)

params: cli_integration_tests/CRISPResso_on_params

cli_integration_tests/CRISPResso_on_params: install cli_integration_tests/inputs/FANC.Cas9.fastq
	cd cli_integration_tests && cmd="CRISPResso -r1 inputs/FANC.Cas9.fastq -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -g GGAATCCCTTCTGCAGCACC -e CGGCCGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCTGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -c GGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTT --dump -qwc 20-30_45-50 -q 30 --default_min_aln_score 80 -an FANC -n params --base_editor_output -fg AGCCTTGCAGTGGGCGCGCTA,CCCACTGAAGGCCC --dsODN GCTAGATTTCCCAAGAAGA -gn hi -fgn dear -p max --place_report_in_output_folder --base_editor_consider_changes_outside_qw --halt_on_plot_fail --debug"; $(RUN)

nhej: cli_integration_tests/CRISPResso_on_nhej

cli_integration_tests/CRISPResso_on_nhej: install cli_integration_tests/
	cd cli_integration_tests && cmd="CRISPResso -r1 inputs/nhej.r1.fastq.gz -r2 inputs/nhej.r2.fastq.gz -a AATGTCCCCCAATGGGAAGTTCATCTGGCACTGCCCACAGGTGAGGAGGTCATGATCCCCTTCTGGAGCTCCCAACGGGCCGTGGTCTGGTTCATCATCTGTAAGAATGGCTTCAAGAGGCTCGGCTGTGGTT -n nhej --process_paired_fastq --place_report_in_output_folder --halt_on_plot_fail --debug"; $(RUN)

.PHONY: nhej_native_merge
nhej_native_merge: cli_integration_tests/CRISPResso_on_nhej_native_merge

cli_integration_tests/CRISPResso_on_nhej_native_merge: install cli_integration_tests/
	cd cli_integration_tests && cmd="CRISPResso -r1 inputs/nhej.r1.fastq.gz -r2 inputs/nhej.r2.fastq.gz -a AATGTCCCCCAATGGGAAGTTCATCTGGCACTGCCCACAGGTGAGGAGGTCATGATCCCCTTCTGGAGCTCCCAACGGGCCGTGGTCTGGTTCATCATCTGTAAGAATGGCTTCAAGAGGCTCGGCTGTGGTT -n nhej_native_merge --crispresso_merge --place_report_in_output_folder --halt_on_plot_fail --debug"; $(RUN)

batch: cli_integration_tests/CRISPRessoBatch_on_FANC

cli_integration_tests/CRISPRessoBatch_on_FANC: install cli_integration_tests/inputs/FANC.batch
	cd cli_integration_tests && cmd="CRISPRessoBatch -bs inputs/FANC.batch -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -g GGAATCCCTTCTGCAGCACC --halt_on_plot_fail --debug --place_report_in_output_folder --base_editor_output"; $(RUN)

large-batch: cli_integration_tests/CRISPRessoBatch_on_large_batch

cli_integration_tests/CRISPRessoBatch_on_large_batch: install cli_integration_tests/inputs/FANC_large.batch
	cd cli_integration_tests && cmd="CRISPRessoBatch -bs inputs/FANC_large.batch -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -g GGAATCCCTTCTGCAGCACC --halt_on_plot_fail --debug --no_rerun --base_editor_output -p max -n large_batch --place_report_in_output_folder"; $(RUN)

pooled: cli_integration_tests/CRISPRessoPooled_on_Both.Cas9

cli_integration_tests/CRISPRessoPooled_on_Both.Cas9: install cli_integration_tests/inputs/Both.Cas9.fastq cli_integration_tests/inputs/Cas9.amplicons.txt
	cd cli_integration_tests && cmd="CRISPRessoPooled -r1 inputs/Both.Cas9.fastq -f inputs/Cas9.amplicons.txt --keep_intermediate --min_reads_to_use_region 100 -p 4 --place_report_in_output_folder --halt_on_plot_fail --debug"; $(RUN)

pooled-prime-editing: cli_integration_tests/CRISPRessoPooled_on_prime.editing

cli_integration_tests/CRISPRessoPooled_on_prime.editing: install cli_integration_tests/inputs/prime.editing.fastq cli_integration_tests/inputs/prime.editing.amplicons.txt
	cd cli_integration_tests && cmd="CRISPRessoPooled -r1 inputs/prime.editing.fastq -f inputs/prime.editing.amplicons.txt --keep_intermediate --min_reads_to_use_region 1 --place_report_in_output_folder --halt_on_plot_fail --debug"; $(RUN)

wgs: cli_integration_tests/CRISPRessoWGS_on_Both.Cas9.fastq.smallGenome

cli_integration_tests/CRISPRessoWGS_on_Both.Cas9.fastq.smallGenome: install cli_integration_tests/inputs/Both.Cas9.fastq.smallGenome.bam cli_integration_tests/inputs/small_genome/smallGenome.fa cli_integration_tests/inputs/Cas9.regions.txt
	cd cli_integration_tests && cmd="CRISPRessoWGS -b inputs/Both.Cas9.fastq.smallGenome.bam -r inputs/small_genome/smallGenome.fa -f inputs/Cas9.regions.txt --place_report_in_output_folder --halt_on_plot_fail --debug"; $(RUN)

compare: cli_integration_tests/CRISPRessoCompare_on_Cas9_VS_Untreated

cli_integration_tests/CRISPRessoCompare_on_Cas9_VS_Untreated: install
	cd cli_integration_tests && cmd="CRISPRessoCompare CRISPRessoBatch_on_FANC/CRISPResso_on_Cas9/ CRISPRessoBatch_on_FANC/CRISPResso_on_Untreated/ --place_report_in_output_folder --halt_on_plot_fail --debug"; $(RUN)

stress: web_tests/web_stress_test.py
	python $^

web_ui: web_tests/CRISPResso_Web_UI_Tests/web_ui_test.py
	python $^ --log_file_path web_tests/UI_test_summary_log.txt

.PHONY: pooled-mixed-mode
pooled-mixed-mode: cli_integration_tests/CRISPRessoPooled_on_pooled-mixed-mode

cli_integration_tests/CRISPRessoPooled_on_pooled-mixed-mode: install cli_integration_tests/inputs/Both.Cas9.fastq cli_integration_tests/inputs/ cli_integration_tests/inputs/ cli_integration_tests/inputs/Cas9.amplicons.txt
	cd cli_integration_tests && cmd="CRISPRessoPooled -r1 inputs/Both.Cas9.genome.fastq -x inputs/small_genome/smallGenome -f inputs/Cas9.amplicons.genome.txt --keep_intermediate --min_reads_to_use_region 100 --halt_on_plot_fail --debug -n pooled-mixed-mode --place_report_in_output_folder"; $(RUN)

.PHONY: pooled-mixed-mode-genome-demux
pooled-mixed-mode-genome-demux: cli_integration_tests/CRISPRessoPooled_on_pooled-mixed-mode-genome-demux

cli_integration_tests/CRISPRessoPooled_on_pooled-mixed-mode-genome-demux: install cli_integration_tests/inputs/Both.Cas9.fastq cli_integration_tests/inputs/ cli_integration_tests/inputs/ cli_integration_tests/inputs/Cas9.amplicons.txt
	cd cli_integration_tests && cmd="CRISPRessoPooled -r1 inputs/Both.Cas9.genome.fastq -x inputs/small_genome/smallGenome -f inputs/Cas9.amplicons.genome.txt --keep_intermediate --min_reads_to_use_region 100 --debug -n pooled-mixed-mode-genome-demux --place_report_in_output_folder --demultiplex_genome_wide --halt_on_plot_fail"; $(RUN)

.PHONY: batch-failing
batch-failing: cli_integration_tests/CRISPRessoBatch_on_batch-failing

cli_integration_tests/CRISPRessoBatch_on_batch-failing: install cli_integration_tests/inputs/ cli_integration_tests/inputs/ cli_integration_tests/inputs/ cli_integration_tests/inputs/FANC_failing.batch
	cd cli_integration_tests && cmd="CRISPRessoBatch -bs inputs/FANC_failing.batch -n batch-failing -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -g GGAATCCCTTCTGCAGCACC --debug --place_report_in_output_folder --base_editor_output --skip_failed --halt_on_plot_fail"; $(RUN)

.PHONY: prime-editor
prime-editor: cli_integration_tests/CRISPResso_on_prime_editor

cli_integration_tests/CRISPResso_on_prime_editor: install cli_integration_tests/inputs/prime_editor.fastq.gz cli_integration_tests/inputs/ cli_integration_tests/inputs/
	cd cli_integration_tests && cmd="CRISPResso --fastq_r1 inputs/prime_editor.fastq.gz --amplicon_seq ACGTCTCATATGCCCCTTGGCAGTCATCTTAGTCATTACCTGAGGTGTTCGTTGTAACTCATATAAACTGAGTTCCCATGTTTTGCTTAATGGTTGAGTTCCGTTTGTCTGCACAGCCTGAGACATTGCTGGAAATAAAGAAGAGAGAAAAACAATTTTAGTATTTGGAAGGGAAGTGCTATGGTCTGAATGTATGTGTCCCACCAAAATTCCTACGT --prime_editing_pegRNA_spacer_seq GTCATCTTAGTCATTACCTG --prime_editing_pegRNA_extension_seq AACGAACACCTCATGTAATGACTAAGATG --prime_editing_nicking_guide_seq CTCAACCATTAAGCAAAACAT --prime_editing_pegRNA_scaffold_seq GTTTTAGAGCTAGAAATAGCAAGTTAAAATAAGGCTAGTCCGTTATCAACTTGAAAAAGTGGCACCGAGTCGGTGC --write_cleaned_report --place_report_in_output_folder --halt_on_plot_fail --debug"; $(RUN)

.PHONY: pooled-paired-sim
pooled-paired-sim: cli_integration_tests/CRISPRessoPooled_on_pooled-paired-sim

cli_integration_tests/CRISPRessoPooled_on_pooled-paired-sim: install cli_integration_tests/inputs/simulated.trim_reqd.r1.fq cli_integration_tests/inputs/simulated.trim_reqd.r2.fq cli_integration_tests/inputs/ cli_integration_tests/inputs/simulated.amplicons.txt
	cd cli_integration_tests && cmd="CRISPRessoPooled -r1 inputs/simulated.trim_reqd.r1.fq -r2 inputs/simulated.trim_reqd.r2.fq -f inputs/simulated.amplicons.txt --place_report_in_output_folder --debug --min_reads_to_use_region 10 --trim_sequences --keep_intermediate -n pooled-paired-sim --halt_on_plot_fail"; $(RUN)

.PHONY: aggregate
aggregate: cli_integration_tests/CRISPRessoAggregate_on_aggregate

cli_integration_tests/CRISPRessoAggregate_on_aggregate: install
	cd cli_integration_tests && cmd="CRISPRessoAggregate -p CRISPRessoBatch_on_FANC/CRISPResso_on_ -n aggregate --debug --place_report_in_output_folder --halt_on_plot_fail"; $(RUN)

.PHONY: bam-out
bam-out: cli_integration_tests/CRISPResso_on_bam-out

cli_integration_tests/CRISPResso_on_bam-out: install cli_integration_tests/inputs/bam_test.fq
	cd cli_integration_tests && cmd="CRISPResso -r1 inputs/bam_test.fq -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTC,GGAAACGCCCATGCAATTAGTCTATTTCTGCTGCAAGTAAGCATGCATTTGTAGGCTTGATGCTTTTTTTCTGCTTCTCCAGCCCT --bam_output --halt_on_plot_fail --debug -n bam-out --place_report_in_output_folder"; $(RUN)

.PHONY: bam-out-genome
bam-out-genome: cli_integration_tests/CRISPResso_on_bam-out-genome

cli_integration_tests/CRISPResso_on_bam-out-genome: install cli_integration_tests/inputs/bam_test.fq cli_integration_tests/inputs/ cli_integration_tests/inputs/
	cd cli_integration_tests && cmd="CRISPResso -r1 inputs/bam_test.fq -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTC,GGAAACGCCCATGCAATTAGTCTATTTCTGCTGCAAGTAAGCATGCATTTGTAGGCTTGATGCTTTTTTTCTGCTTCTCCAGCCCT --bam_output --debug -n bam-out-genome -x inputs/small_genome/smallGenome --place_report_in_output_folder --halt_on_plot_fail"; $(RUN)

.PHONY: basic-parallel
basic-parallel: cli_integration_tests/CRISPResso_on_basic-parallel

cli_integration_tests/CRISPResso_on_basic-parallel: install cli_integration_tests/inputs/FANC.Cas9.fastq cli_integration_tests/inputs/ cli_integration_tests/inputs/
	cd cli_integration_tests && cmd="CRISPResso -r1 inputs/FANC.Cas9.fastq -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -g GGAATCCCTTCTGCAGCACC --place_report_in_output_folder --debug -p 2 -n basic-parallel --halt_on_plot_fail"; $(RUN)

.PHONY: bam-single
bam-single: cli_integration_tests/CRISPResso_on_bam-single

cli_integration_tests/CRISPResso_on_bam-single: install cli_integration_tests/inputs/ cli_integration_tests/inputs/ cli_integration_tests/inputs/Both.Cas9.fastq.smallGenome.bam
	cd cli_integration_tests && cmd="CRISPResso --bam_input inputs/Both.Cas9.fastq.smallGenome.bam --bam_chr_loc chr9 --auto --n_processes 1 --place_report_in_output_folder --debug -n bam-single --halt_on_plot_fail"; $(RUN)

.PHONY: bam-out-parallel
bam-out-parallel: cli_integration_tests/CRISPResso_on_bam-out-parallel

cli_integration_tests/CRISPResso_on_bam-out-parallel: install cli_integration_tests/inputs/bam_test.fq cli_integration_tests/inputs/ cli_integration_tests/inputs/
	cd cli_integration_tests && cmd="CRISPResso -r1 inputs/bam_test.fq -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTC,GGAAACGCCCATGCAATTAGTCTATTTCTGCTGCAAGTAAGCATGCATTTGTAGGCTTGATGCTTTTTTTCTGCTTCTCCAGCCCT --bam_output --debug -n bam-out-parallel --n_processes max --place_report_in_output_folder --halt_on_plot_fail"; $(RUN)

.PHONY: basic-write-bam-out
basic-write-bam-out: cli_integration_tests/CRISPResso_on_basic-write-bam-out

cli_integration_tests/CRISPResso_on_basic-write-bam-out: install cli_integration_tests/inputs/FANC.Cas9.fastq cli_integration_tests/inputs/ cli_integration_tests/inputs/
	cd cli_integration_tests && cmd="CRISPResso -r1 inputs/FANC.Cas9.fastq -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -g GGAATCCCTTCTGCAGCACC --place_report_in_output_folder --debug --bam_output -n basic-write-bam-out --halt_on_plot_fail"; $(RUN)

.PHONY: basic-write-bam-out-parallel
basic-write-bam-out-parallel: cli_integration_tests/CRISPResso_on_basic-write-bam-out-parallel

cli_integration_tests/CRISPResso_on_basic-write-bam-out-parallel: install cli_integration_tests/inputs/FANC.Cas9.fastq cli_integration_tests/inputs/ cli_integration_tests/inputs/
	cd cli_integration_tests && cmd="CRISPResso -r1 inputs/FANC.Cas9.fastq -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -g GGAATCCCTTCTGCAGCACC --place_report_in_output_folder --debug --bam_output --n_processes 2 -n basic-write-bam-out-parallel --halt_on_plot_fail"; $(RUN)

.PHONY: asym-both
asym-both: cli_integration_tests/CRISPResso_on_asym_both

cli_integration_tests/CRISPResso_on_asym_both: install cli_integration_tests/inputs/asym.fastq cli_integration_tests/inputs/ cli_integration_tests/inputs/
	cd cli_integration_tests && cmd="CRISPResso -r1 inputs/asym.fastq -a GACATACATACA -g GACATACATACA --exclude_bp_from_left 0 --exclude_bp_from_right 0 -n asym_both --place_report_in_output_folder --halt_on_plot_fail --debug"; $(RUN)
.PHONY: asym-left
asym-left: cli_integration_tests/CRISPResso_on_asym_left

cli_integration_tests/CRISPResso_on_asym_left: install cli_integration_tests/inputs/FANC.Cas9.fastq cli_integration_tests/inputs/ cli_integration_tests/inputs/
	cd cli_integration_tests && cmd="CRISPResso -r1 inputs/FANC.Cas9.fastq -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -g CGGATGTTCCAATCAGTACG --exclude_bp_from_left 0 -n asym_left --place_report_in_output_folder --halt_on_plot_fail --debug"; $(RUN)
.PHONY: asym-right
asym-right: cli_integration_tests/CRISPResso_on_asym_right

cli_integration_tests/CRISPResso_on_asym_right: install cli_integration_tests/inputs/FANC.Cas9.fastq cli_integration_tests/inputs/ cli_integration_tests/inputs/
	cd cli_integration_tests && cmd="CRISPResso -r1 inputs/FANC.Cas9.fastq -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -g TCCATCGGCGCTTTGGTCGG --exclude_bp_from_right 0 -n asym_right --place_report_in_output_folder --halt_on_plot_fail --debug"; $(RUN)

.PHONY: base_editor
base_editor: cli_integration_tests/CRISPResso_on_base_editor

cli_integration_tests/CRISPResso_on_base_editor: install cli_integration_tests/inputs/FANC.Cas9.fastq cli_integration_tests/inputs/ cli_integration_tests/inputs/
	cd cli_integration_tests && cmd="CRISPResso -r1 inputs/FANC.Cas9.fastq -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -g GGAATCCCTTCTGCAGCACC -e CGGCCGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCTGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -c GGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTT --dump -q 30 --default_min_aln_score 80 -an FANC -n base_editor --base_editor_output -fg AGCCTTGCAGTGGGCGCGCTA,CCCACTGAAGGCCC --dsODN GCTAGATTTCCCAAGAAGA -gn hi -fgn dear -p max --place_report_in_output_folder --halt_on_plot_fail --debug"; $(RUN)

.PHONY: vcf
vcf: vcf-basic vcf-deletions-only vcf-insertions-only vcf-no-edits vcf-multi-amplicon vcf-base-edit-abe vcf-base-edit-cbe vcf-prime-edit-basic

.PHONY: vcf-basic
vcf-basic: cli_integration_tests/CRISPResso_on_vcf-basic

cli_integration_tests/CRISPResso_on_vcf-basic: install cli_integration_tests/inputs/vcf_basic.fastq cli_integration_tests/inputs/ cli_integration_tests/inputs/
	cd cli_integration_tests && cmd="CRISPResso -r1 inputs/vcf_basic.fastq -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -g GGAATCCCTTCTGCAGCACC --quantification_window_coordinates 89-95 --vcf_output --amplicon_coordinates FANC:1 -n vcf-basic --place_report_in_output_folder --debug"; $(RUN)
.PHONY: vcf-deletions-only
vcf-deletions-only: cli_integration_tests/CRISPResso_on_vcf-deletions-only

cli_integration_tests/CRISPResso_on_vcf-deletions-only: install cli_integration_tests/inputs/vcf_deletions.fastq cli_integration_tests/inputs/ cli_integration_tests/inputs/
	cd cli_integration_tests && cmd="CRISPResso -r1 inputs/vcf_deletions.fastq -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -g GGAATCCCTTCTGCAGCACC --vcf_output --amplicon_coordinates FANC:1 --quantification_window_coordinates 89-94 -n vcf-deletions-only --place_report_in_output_folder --debug"; $(RUN)
.PHONY: vcf-insertions-only
vcf-insertions-only: cli_integration_tests/CRISPResso_on_vcf-insertions-only

cli_integration_tests/CRISPResso_on_vcf-insertions-only: install cli_integration_tests/inputs/vcf_insertions.fastq cli_integration_tests/inputs/ cli_integration_tests/inputs/
	cd cli_integration_tests && cmd="CRISPResso -r1 inputs/vcf_insertions.fastq -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -g GGAATCCCTTCTGCAGCACC --quantification_window_coordinates 89-95 --vcf_output --amplicon_coordinates FANC:1 -n vcf-insertions-only --place_report_in_output_folder --debug"; $(RUN)
.PHONY: vcf-no-edits
vcf-no-edits: cli_integration_tests/CRISPResso_on_vcf-no-edits

cli_integration_tests/CRISPResso_on_vcf-no-edits: install cli_integration_tests/inputs/vcf_no_edits.fastq cli_integration_tests/inputs/ cli_integration_tests/inputs/
	cd cli_integration_tests && cmd="CRISPResso -r1 inputs/vcf_no_edits.fastq -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -g GGAATCCCTTCTGCAGCACC --vcf_output --amplicon_coordinates FANC:1 -n vcf-no-edits --place_report_in_output_folder --debug"; $(RUN)
.PHONY: vcf-multi-amplicon
vcf-multi-amplicon: cli_integration_tests/CRISPResso_on_vcf-multi-amplicon

cli_integration_tests/CRISPResso_on_vcf-multi-amplicon: install cli_integration_tests/inputs/vcf_multi_amplicon.fastq cli_integration_tests/inputs/ cli_integration_tests/inputs/
	cd cli_integration_tests && cmd="CRISPResso -r1 inputs/vcf_multi_amplicon.fastq -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG,TACGGGTATTACCCGCGTTTAGTGGCTAGCGACTCGTGGACTTGCTGTACTGTCTACGGGCGTCAACTTGATAATCCCAAAAAAGCTTGGCCCCGCACAACTCGTTGAGCAATTCTTAAAAAGATGGTGTACGTCCCTCATACTTCGTATTCAATAAACCCGGTTAGACCATTGGGTGCGTGATGCTGCATTGCCTTGCA -an AMP1,AMP2 -g GGAATCCCTTCTGCAGCACC,CCCCGCACAACTCGTTGAGC --vcf_output --quantification_window_coordinates 89-95,104-109 --amplicon_coordinates chr1:1000,chr2:5000 -n vcf-multi-amplicon --place_report_in_output_folder --debug"; $(RUN)
.PHONY: vcf-base-edit-cbe
vcf-base-edit-cbe: cli_integration_tests/CRISPResso_on_vcf-base-edit-cbe

cli_integration_tests/CRISPResso_on_vcf-base-edit-cbe: install cli_integration_tests/inputs/vcf_base_edit_cbe.fastq cli_integration_tests/inputs/ cli_integration_tests/inputs/
	cd cli_integration_tests && cmd="CRISPResso -r1 inputs/vcf_base_edit_cbe.fastq -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -g GGAATCCCTTCTGCAGCACC --vcf_output --amplicon_coordinates FANC:1 --quantification_window_coordinates 76-96 -n vcf-base-edit-cbe --place_report_in_output_folder --debug"; $(RUN)
.PHONY: vcf-base-edit-abe
vcf-base-edit-abe: cli_integration_tests/CRISPResso_on_vcf-base-edit-abe

cli_integration_tests/CRISPResso_on_vcf-base-edit-abe: install cli_integration_tests/inputs/vcf_base_edit_abe.fastq cli_integration_tests/inputs/ cli_integration_tests/inputs/
	cd cli_integration_tests && cmd="CRISPResso -r1 inputs/vcf_base_edit_abe.fastq -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -g GGAATCCCTTCTGCAGCACC --vcf_output --amplicon_coordinates FANC:1 --quantification_window_coordinates 76-96 -n vcf-base-edit-abe --place_report_in_output_folder --debug"; $(RUN)
.PHONY: vcf-prime-edit-basic
vcf-prime-edit-basic: cli_integration_tests/CRISPResso_on_vcf-prime-edit-basic

cli_integration_tests/CRISPResso_on_vcf-prime-edit-basic: install cli_integration_tests/inputs/vcf_prime_edit_basic.fastq cli_integration_tests/inputs/ cli_integration_tests/inputs/
	cd cli_integration_tests && cmd="CRISPResso -r1 inputs/vcf_prime_edit_basic.fastq -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -g GGAATCCCTTCTGCAGCACC --prime_editing_pegRNA_spacer_seq GGAATCCCTTCTGCAGCACC --prime_editing_pegRNA_extension_seq ATCTGGATCGGCTGCAGAAGGGA --vcf_output --amplicon_coordinates FANC:1,FANC:1 -n vcf-prime-edit-basic --place_report_in_output_folder --debug"; $(RUN)
syn-gen-test:
	cd syn-gen && pytest test_syn_gen.py -v

syn-gen-e2e:
	cd syn-gen && pytest test_bwa_e2e.py test_bwa_verify.py -v

syn-gen-all:
	cd syn-gen && pytest test_syn_gen.py test_bwa_e2e.py test_bwa_verify.py -v
