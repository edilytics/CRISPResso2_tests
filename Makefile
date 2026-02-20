.PHONY: all install test print update update-all skip_html clean clean_cli_integration \
	basic params batch pooled wgs compare aggregate \
	prime-editor nhej nhej_native_merge base_editor \
	basic-parallel bam bam-single bam-out bam-out-genome bam-out-parallel \
	basic-write-bam-out basic-write-bam-out-parallel \
	asym-both asym-left asym-right \
	pooled-paired-sim pooled-mixed-mode pooled-mixed-mode-genome-demux \
	vcf vcf-basic vcf-deletions-only vcf-insertions-only vcf-no-edits \
	vcf-multi-amplicon vcf-base-edit-cbe vcf-base-edit-abe vcf-prime-edit-basic \
	batch-failing large-batch pooled-prime-editing \
	params-big-code params-multi-code params-medium params-small params-multiple-codes \
	code-tests stress web_ui \
	syn-gen-test syn-gen-e2e syn-gen-all \
	pytest pytest-coverage pytest-test coverage-report coverage-clean

CRISPRESSO2_DIR ?= ../CRISPResso2
CRISPRESSO2_SOURCES := $(wildcard $(CRISPRESSO2_DIR)/CRISPResso2/*.py*)

.install_sentinel: $(CRISPRESSO2_SOURCES)
	cd $(CRISPRESSO2_DIR) && output=`pip install -e . 2>&1` || echo "$$output"
	@touch $@

# ── Pytest flags built from make goals ───────────────────────────────
PYTEST_FLAGS :=
ifneq ($(filter test,$(MAKECMDGOALS)),)
  PYTEST_FLAGS += --test
endif
ifneq ($(filter print,$(MAKECMDGOALS)),)
  PYTEST_FLAGS += --print -s
endif
ifneq ($(filter skip_html,$(MAKECMDGOALS)),)
  PYTEST_FLAGS += --skip-html
endif
ifdef skip_html
  PYTEST_FLAGS += --skip-html
endif

# $(1): pytest node ID  (e.g. test_crispresso_cli[basic])
# $(2): output dir name (e.g. CRISPResso_on_FANC.Cas9)
define PYTEST_RUN
pytest "test_cli.py::$(1)" $(PYTEST_FLAGS)$(if $(filter update,$(MAKECMDGOALS)), && python test_manager.py update cli_integration_tests/$(2) cli_integration_tests/expected_results/$(2))$(if $(filter update-all,$(MAKECMDGOALS)), && yes | python test_manager.py update cli_integration_tests/$(2) cli_integration_tests/expected_results/$(2))
endef

# ── Goal-only targets (used as flags, not real builds) ───────────────
test:
	@:
print:
	@:
update:
	@:
update-all:
	@:
skip_html:
	@:

# ── Top-level targets ───────────────────────────────────────────────
install: .install_sentinel

all: clean basic params prime-editor batch pooled wgs compare pooled-paired-sim pooled-mixed-mode pooled-mixed-mode-genome-demux aggregate bam bam-out bam-out-genome basic-parallel bam-single bam-out-parallel basic-write-bam-out basic-write-bam-out-parallel asym-both asym-left asym-right nhej_native_merge base_editor vcf-basic vcf-deletions-only vcf-insertions-only vcf-no-edits vcf-multi-amplicon vcf-base-edit-cbe vcf-base-edit-abe vcf-prime-edit-basic

clean: clean_cli_integration
	rm -f .install_sentinel

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

# ── Core CRISPResso (pytest-backed) ─────────────────────────────────
basic: .install_sentinel
	$(call PYTEST_RUN,test_crispresso_cli[basic],CRISPResso_on_FANC.Cas9)

params: .install_sentinel
	$(call PYTEST_RUN,test_crispresso_cli[params],CRISPResso_on_params)

nhej_native_merge: .install_sentinel
	$(call PYTEST_RUN,test_crispresso_cli[nhej_native_merge],CRISPResso_on_nhej_native_merge)

prime-editor: .install_sentinel
	$(call PYTEST_RUN,test_crispresso_cli[prime_editor],CRISPResso_on_prime_editor)

base_editor: .install_sentinel
	$(call PYTEST_RUN,test_crispresso_cli[base_editor],CRISPResso_on_base_editor)

# ── Parallel / process variants (pytest-backed) ─────────────────────
basic-parallel: .install_sentinel
	$(call PYTEST_RUN,test_crispresso_cli[basic_parallel],CRISPResso_on_basic-parallel)

# ── Asymmetric (pytest-backed) ──────────────────────────────────────
asym-both: .install_sentinel
	$(call PYTEST_RUN,test_crispresso_cli[asym_both],CRISPResso_on_asym_both)

asym-left: .install_sentinel
	$(call PYTEST_RUN,test_crispresso_cli[asym_left],CRISPResso_on_asym_left)

asym-right: .install_sentinel
	$(call PYTEST_RUN,test_crispresso_cli[asym_right],CRISPResso_on_asym_right)

# ── BAM input (pytest-backed) ───────────────────────────────────────
bam: .install_sentinel
	$(call PYTEST_RUN,test_crispresso_cli[bam],CRISPResso_on_bam)

bam-single: .install_sentinel
	$(call PYTEST_RUN,test_crispresso_cli[bam_single],CRISPResso_on_bam-single)

# ── BAM output (pytest-backed) ──────────────────────────────────────
bam-out: .install_sentinel
	$(call PYTEST_RUN,test_crispresso_cli[bam_out],CRISPResso_on_bam-out)

bam-out-genome: .install_sentinel
	$(call PYTEST_RUN,test_crispresso_cli[bam_out_genome],CRISPResso_on_bam-out-genome)

bam-out-parallel: .install_sentinel
	$(call PYTEST_RUN,test_crispresso_cli[bam_out_parallel],CRISPResso_on_bam-out-parallel)

basic-write-bam-out: .install_sentinel
	$(call PYTEST_RUN,test_crispresso_cli[basic_write_bam_out],CRISPResso_on_basic-write-bam-out)

basic-write-bam-out-parallel: .install_sentinel
	$(call PYTEST_RUN,test_crispresso_cli[basic_write_bam_out_parallel],CRISPResso_on_basic-write-bam-out-parallel)

# ── Batch (pytest-backed) ───────────────────────────────────────────
batch: .install_sentinel
	$(call PYTEST_RUN,test_crispresso_cli[batch],CRISPRessoBatch_on_FANC)

# ── Pooled (pytest-backed) ──────────────────────────────────────────
pooled: .install_sentinel
	$(call PYTEST_RUN,test_crispresso_cli[pooled],CRISPRessoPooled_on_Both.Cas9)

pooled-paired-sim: .install_sentinel
	$(call PYTEST_RUN,test_crispresso_cli[pooled_paired_sim],CRISPRessoPooled_on_pooled-paired-sim)

pooled-mixed-mode: .install_sentinel
	$(call PYTEST_RUN,test_crispresso_cli[pooled_mixed_mode],CRISPRessoPooled_on_pooled-mixed-mode)

pooled-mixed-mode-genome-demux: .install_sentinel
	$(call PYTEST_RUN,test_crispresso_cli[pooled_mixed_mode_genome_demux],CRISPRessoPooled_on_pooled-mixed-mode-genome-demux)

# ── WGS (pytest-backed) ─────────────────────────────────────────────
wgs: .install_sentinel
	$(call PYTEST_RUN,test_crispresso_cli[wgs],CRISPRessoWGS_on_Both.Cas9.fastq.smallGenome)

# ── Compare / Aggregate (pytest-backed) ─────────────────────────────
compare: .install_sentinel
	$(call PYTEST_RUN,test_compare,CRISPRessoCompare_on_Cas9_VS_Untreated)

aggregate: .install_sentinel
	$(call PYTEST_RUN,test_aggregate,CRISPRessoAggregate_on_aggregate)

# ── VCF (pytest-backed) ─────────────────────────────────────────────
vcf: vcf-basic vcf-deletions-only vcf-insertions-only vcf-no-edits vcf-multi-amplicon vcf-base-edit-abe vcf-base-edit-cbe vcf-prime-edit-basic

vcf-basic: .install_sentinel
	$(call PYTEST_RUN,test_crispresso_cli[vcf_basic],CRISPResso_on_vcf-basic)

vcf-deletions-only: .install_sentinel
	$(call PYTEST_RUN,test_crispresso_cli[vcf_deletions_only],CRISPResso_on_vcf-deletions-only)

vcf-insertions-only: .install_sentinel
	$(call PYTEST_RUN,test_crispresso_cli[vcf_insertions_only],CRISPResso_on_vcf-insertions-only)

vcf-no-edits: .install_sentinel
	$(call PYTEST_RUN,test_crispresso_cli[vcf_no_edits],CRISPResso_on_vcf-no-edits)

vcf-multi-amplicon: .install_sentinel
	$(call PYTEST_RUN,test_crispresso_cli[vcf_multi_amplicon],CRISPResso_on_vcf-multi-amplicon)

vcf-base-edit-cbe: .install_sentinel
	$(call PYTEST_RUN,test_crispresso_cli[vcf_base_edit_cbe],CRISPResso_on_vcf-base-edit-cbe)

vcf-base-edit-abe: .install_sentinel
	$(call PYTEST_RUN,test_crispresso_cli[vcf_base_edit_abe],CRISPResso_on_vcf-base-edit-abe)

vcf-prime-edit-basic: .install_sentinel
	$(call PYTEST_RUN,test_crispresso_cli[vcf_prime_edit_basic],CRISPResso_on_vcf-prime-edit-basic)

# ── Non-pytest targets ──────────────────────────────────────────────
nhej: .install_sentinel
	cd cli_integration_tests && CRISPResso -r1 inputs/nhej.r1.fastq.gz -r2 inputs/nhej.r2.fastq.gz -a AATGTCCCCCAATGGGAAGTTCATCTGGCACTGCCCACAGGTGAGGAGGTCATGATCCCCTTCTGGAGCTCCCAACGGGCCGTGGTCTGGTTCATCATCTGTAAGAATGGCTTCAAGAGGCTCGGCTGTGGTT -n nhej --process_paired_fastq --place_report_in_output_folder --halt_on_plot_fail --debug

code-tests: params params-big-code params-multi-code params-medium params-multiple-codes params-small

params-big-code: .install_sentinel
	cd cli_integration_tests && CRISPResso -r1 inputs/FANC.Cas9.fastq -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -g GGAATCCCTTCTGCAGCACC -e CGGCCGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCTGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -c GGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCG --dump -qwc 20-30_45-50 -q 30 --default_min_aln_score 80 -an FANC -n params-big-code --base_edit -fg AGCCTTGCAGTGGGCGCGCTA,CCCACTGAAGGCCC --dsODN GCTAGATTTCCCAAGAAGA -gn hi -fgn dear -p max --place_report_in_output_folder --debug

params-multi-code: .install_sentinel
	cd cli_integration_tests && CRISPResso -r1 inputs/FANC.Cas9.fastq -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -g GGAATCCCTTCTGCAGCACC -e CGGCCGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCTGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -c GGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTT,ATGTTCCAATCAGTACGCAGAGAGTCG,ACCTGCGCCACATCCATCGGCGCTTTGGT --dump -qwc 20-30_45-50 -q 30 --default_min_aln_score 80 -an FANC -n params_multi_code --base_edit -fg AGCCTTGCAGTGGGCGCGCTA,CCCACTGAAGGCCC --dsODN GCTAGATTTCCCAAGAAGA -gn hi -fgn dear -p max --place_report_in_output_folder --debug

params-medium: .install_sentinel
	cd cli_integration_tests && CRISPResso -r1 inputs/FANC.Cas9.fastq -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -g GGAATCCCTTCTGCAGCACC -e CGGCCGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCTGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -c GGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAA --dump -qwc 20-30_45-50 -q 30 --default_min_aln_score 80 -an FANC -n params_medium --base_edit -fg AGCCTTGCAGTGGGCGCGCTA,CCCACTGAAGGCCC --dsODN GCTAGATTTCCCAAGAAGA -gn hi -fgn dear -p max --place_report_in_output_folder --debug

params-small: .install_sentinel
	cd cli_integration_tests && CRISPResso -r1 inputs/FANC.Cas9.fastq -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -g GGAATCCCTTCTGCAGCACC -e CGGCCGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCTGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -c GGGCCTTCGCGCACCTCATGGAATCCC --dump -qwc 20-30_45-50 -q 30 --default_min_aln_score 80 -an FANC -n params_small --base_edit -fg AGCCTTGCAGTGGGCGCGCTA,CCCACTGAAGGCCC --dsODN GCTAGATTTCCCAAGAAGA -gn hi -fgn dear -p max --place_report_in_output_folder --debug

params-multiple-codes: .install_sentinel
	cd cli_integration_tests && CRISPResso -r1 inputs/FANC.Cas9.fastq -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -g GGAATCCCTTCTGCAGCACC -e CGGCCGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCTGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -c GGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGC,TGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAA --dump -qwc 20-30_45-50 -q 30 --default_min_aln_score 80 -an FANC -n params_multiple_codes --base_editor_output -fg AGCCTTGCAGTGGGCGCGCTA,CCCACTGAAGGCCC --dsODN GCTAGATTTCCCAAGAAGA -gn hi -fgn dear -p max --place_report_in_output_folder --debug

large-batch: .install_sentinel
	cd cli_integration_tests && CRISPRessoBatch -bs inputs/FANC_large.batch -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -g GGAATCCCTTCTGCAGCACC --halt_on_plot_fail --debug --no_rerun --base_editor_output -p max -n large_batch --place_report_in_output_folder

pooled-prime-editing: .install_sentinel
	cd cli_integration_tests && CRISPRessoPooled -r1 inputs/prime.editing.fastq -f inputs/prime.editing.amplicons.txt --keep_intermediate --min_reads_to_use_region 1 --place_report_in_output_folder --halt_on_plot_fail --debug

batch-failing: .install_sentinel
	cd cli_integration_tests && CRISPRessoBatch -bs inputs/FANC_failing.batch -n batch-failing -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -g GGAATCCCTTCTGCAGCACC --debug --place_report_in_output_folder --base_editor_output --skip_failed --halt_on_plot_fail

# ── Web / stress tests ──────────────────────────────────────────────
stress: web_tests/web_stress_test.py
	python $^

web_ui: web_tests/CRISPResso_Web_UI_Tests/web_ui_test.py
	python $^ --log_file_path web_tests/UI_test_summary_log.txt

# ── syn-gen tests ────────────────────────────────────────────────────
syn-gen-test:
	cd syn-gen && pytest test_syn_gen.py -v

syn-gen-e2e:
	cd syn-gen && pytest test_bwa_e2e.py test_bwa_verify.py -v

syn-gen-all:
	cd syn-gen && pytest test_syn_gen.py test_bwa_e2e.py test_bwa_verify.py -v

# ── pytest convenience targets ───────────────────────────────────────
pytest:
	pytest test_cli.py

pytest-coverage:
	pytest test_cli.py --with-coverage
	coverage combine
	coverage report

pytest-test:
	pytest test_cli.py -k "$(TEST)" -v

coverage-report:
	coverage html
	@echo "Coverage report: htmlcov/index.html"

coverage-clean:
	coverage erase
	rm -rf htmlcov/
