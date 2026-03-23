.PHONY: all install test print update update-all skip_html diff-plots clean clean_cli_integration \
	install-pro all-pro clean-pro \
	pro-tests pro-smoke-single-plot pro-no-plots-key pro-subset-plots \
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
CRISPRESSOPRO_DIR ?= ../CRISPRessoPro
.DEFAULT_GOAL := all

# ── Pixi environment auto-activation ────────────────────────────────
# When PRO=1 is set, use the test-pro environment (CRISPResso2 + CRISPRessoPro).
# Otherwise, use the test environment (CRISPResso2 only).
# If already inside the target pixi environment, run commands directly.
ifdef PRO
  _PIXI_ENV := test-pro
else
  _PIXI_ENV := test
endif

ifneq ($(PIXI_ENVIRONMENT_NAME),$(_PIXI_ENV))
  PIXI := pixi run --manifest-path $(abspath $(CRISPRESSO2_DIR))/pixi.toml -e $(_PIXI_ENV) --
else
  PIXI :=
endif

# Pro-only targets always use test-pro, regardless of PRO=1.
ifneq ($(PIXI_ENVIRONMENT_NAME),test-pro)
  PIXI_PRO := pixi run --manifest-path $(abspath $(CRISPRESSO2_DIR))/pixi.toml -e test-pro --
else
  PIXI_PRO :=
endif

CRISPRESSO2_SOURCES := $(wildcard $(CRISPRESSO2_DIR)/CRISPResso2/*.py*) \
                       $(CRISPRESSO2_DIR)/setup.py \
                       $(CRISPRESSO2_DIR)/pyproject.toml

CRISPRESSOPRO_SOURCES := $(wildcard $(CRISPRESSOPRO_DIR)/CRISPRessoPro/*.py)

.install_sentinel: $(CRISPRESSO2_SOURCES)
	$(PIXI) pip install -e $(CRISPRESSO2_DIR)
	@touch $@

.install_pro_sentinel: $(CRISPRESSO2_SOURCES) $(CRISPRESSOPRO_SOURCES)
	$(PIXI) pip install -e $(CRISPRESSO2_DIR)
	$(PIXI) pip install -e $(CRISPRESSOPRO_DIR)
	@touch $@

ifdef PRO
  _SENTINEL := .install_pro_sentinel
else
  _SENTINEL := .install_sentinel
endif

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

ifneq ($(filter diff-plots,$(MAKECMDGOALS)),)
  PYTEST_FLAGS += --diff-plots
  DIFF_PLOTS_FLAG := --diff-plots
endif
ifdef diff-plots
  PYTEST_FLAGS += --diff-plots
  DIFF_PLOTS_FLAG := --diff-plots
endif


# ── Update command (Pro-aware) ────────────────────────────────────────
# $(1): output dir name (e.g. CRISPResso_on_FANC.Cas9)
# Non-Pro: update data + HTML + plots → expected_results/
# Pro:     update data + plots → expected_results/ (skip HTML),
#          update HTML → expected_results_pro/
ifdef PRO
define UPDATE_CMD
$(PIXI) python test_manager.py update cli_integration_tests/$(1) cli_integration_tests/expected_results/$(1) --skip-html $(DIFF_PLOTS_FLAG) && \
$(PIXI) python test_manager.py update cli_integration_tests/$(1) cli_integration_tests/expected_results_pro/$(1) --html-only
endef
define UPDATE_ALL_CMD
yes | $(PIXI) python test_manager.py update cli_integration_tests/$(1) cli_integration_tests/expected_results/$(1) --skip-html $(DIFF_PLOTS_FLAG) && \
yes | $(PIXI) python test_manager.py update cli_integration_tests/$(1) cli_integration_tests/expected_results_pro/$(1) --html-only
endef
else
define UPDATE_CMD
$(PIXI) python test_manager.py update cli_integration_tests/$(1) cli_integration_tests/expected_results/$(1) $(DIFF_PLOTS_FLAG)
endef
define UPDATE_ALL_CMD
yes | $(PIXI) python test_manager.py update cli_integration_tests/$(1) cli_integration_tests/expected_results/$(1) $(DIFF_PLOTS_FLAG)
endef
endif

# $(1): pytest node ID  (e.g. test_crispresso_cli[basic])
# $(2): output dir name (e.g. CRISPResso_on_FANC.Cas9)
define PYTEST_RUN
$(PIXI) pytest "test_cli.py::$(1)" $(PYTEST_FLAGS)$(if $(filter update,$(MAKECMDGOALS)), && $(call UPDATE_CMD,$(2)))$(if $(filter update-all,$(MAKECMDGOALS)), && $(call UPDATE_ALL_CMD,$(2)))
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

diff-plots:
	@:

# ── Top-level targets ───────────────────────────────────────────────
install: $(_SENTINEL)

install-pro:
	$(MAKE) install PRO=1

all-pro:
	$(MAKE) all PRO=1

clean-pro:
	rm -f .install_pro_sentinel

# ── Pro-only tests (always use test-pro environment) ─────────────────
pro-tests: pro-smoke-single-plot pro-no-plots-key pro-subset-plots

pro-smoke-single-plot: .install_pro_sentinel
	$(PIXI_PRO) pytest "test_cli.py::test_pro_smoke_single_plot" $(PYTEST_FLAGS)

pro-no-plots-key: .install_pro_sentinel
	$(PIXI_PRO) pytest "test_cli.py::test_pro_no_plots_key_shows_all_defaults" $(PYTEST_FLAGS)

pro-subset-plots: .install_pro_sentinel
	$(PIXI_PRO) pytest "test_cli.py::test_pro_subset_plots_in_order" $(PYTEST_FLAGS)

all: clean basic params prime-editor batch pooled wgs compare pooled-paired-sim pooled-mixed-mode pooled-mixed-mode-genome-demux aggregate bam bam-out bam-out-genome basic-parallel bam-single bam-out-parallel basic-write-bam-out basic-write-bam-out-parallel asym-both asym-left asym-right nhej_native_merge base_editor vcf-basic vcf-deletions-only vcf-insertions-only vcf-no-edits vcf-multi-amplicon vcf-base-edit-cbe vcf-base-edit-abe vcf-prime-edit-basic

clean: clean_cli_integration
	rm -f .install_sentinel .install_pro_sentinel

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
cli_integration_tests/CRISPResso_on_nhej_native_merge* \
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
cli_integration_tests/CRISPResso_on_pro-smoke-single-plot* \
cli_integration_tests/CRISPResso_on_pro-no-plots-key* \
cli_integration_tests/CRISPResso_on_pro-subset-plots* \
web_tests/stress_test_log.txt \
web_tests/UI_docker_log.txt \
web_tests/UI_selenium_log.txt

# ── Core CRISPResso (pytest-backed) ─────────────────────────────────
basic: $(_SENTINEL)
	$(call PYTEST_RUN,test_crispresso_cli[basic],CRISPResso_on_FANC.Cas9)

params: $(_SENTINEL)
	$(call PYTEST_RUN,test_crispresso_cli[params],CRISPResso_on_params)

nhej_native_merge: $(_SENTINEL)
	$(call PYTEST_RUN,test_crispresso_cli[nhej_native_merge],CRISPResso_on_nhej_native_merge)

prime-editor: $(_SENTINEL)
	$(call PYTEST_RUN,test_crispresso_cli[prime_editor],CRISPResso_on_prime_editor)

base_editor: $(_SENTINEL)
	$(call PYTEST_RUN,test_crispresso_cli[base_editor],CRISPResso_on_base_editor)

# ── Parallel / process variants (pytest-backed) ─────────────────────
basic-parallel: $(_SENTINEL)
	$(call PYTEST_RUN,test_crispresso_cli[basic_parallel],CRISPResso_on_basic-parallel)

# ── Asymmetric (pytest-backed) ──────────────────────────────────────
asym-both: $(_SENTINEL)
	$(call PYTEST_RUN,test_crispresso_cli[asym_both],CRISPResso_on_asym_both)

asym-left: $(_SENTINEL)
	$(call PYTEST_RUN,test_crispresso_cli[asym_left],CRISPResso_on_asym_left)

asym-right: $(_SENTINEL)
	$(call PYTEST_RUN,test_crispresso_cli[asym_right],CRISPResso_on_asym_right)

# ── BAM input (pytest-backed) ───────────────────────────────────────
bam: $(_SENTINEL)
	$(call PYTEST_RUN,test_crispresso_cli[bam],CRISPResso_on_bam)

bam-single: $(_SENTINEL)
	$(call PYTEST_RUN,test_crispresso_cli[bam_single],CRISPResso_on_bam-single)

# ── BAM output (pytest-backed) ──────────────────────────────────────
bam-out: $(_SENTINEL)
	$(call PYTEST_RUN,test_crispresso_cli[bam_out],CRISPResso_on_bam-out)

bam-out-genome: $(_SENTINEL)
	$(call PYTEST_RUN,test_crispresso_cli[bam_out_genome],CRISPResso_on_bam-out-genome)

bam-out-parallel: $(_SENTINEL)
	$(call PYTEST_RUN,test_crispresso_cli[bam_out_parallel],CRISPResso_on_bam-out-parallel)

basic-write-bam-out: $(_SENTINEL)
	$(call PYTEST_RUN,test_crispresso_cli[basic_write_bam_out],CRISPResso_on_basic-write-bam-out)

basic-write-bam-out-parallel: $(_SENTINEL)
	$(call PYTEST_RUN,test_crispresso_cli[basic_write_bam_out_parallel],CRISPResso_on_basic-write-bam-out-parallel)

# ── Batch (pytest-backed) ───────────────────────────────────────────
batch: $(_SENTINEL)
	$(call PYTEST_RUN,test_crispresso_cli[batch],CRISPRessoBatch_on_FANC)

# ── Pooled (pytest-backed) ──────────────────────────────────────────
pooled: $(_SENTINEL)
	$(call PYTEST_RUN,test_crispresso_cli[pooled],CRISPRessoPooled_on_Both.Cas9)

pooled-paired-sim: $(_SENTINEL)
	$(call PYTEST_RUN,test_crispresso_cli[pooled_paired_sim],CRISPRessoPooled_on_pooled-paired-sim)

pooled-mixed-mode: $(_SENTINEL)
	$(call PYTEST_RUN,test_crispresso_cli[pooled_mixed_mode],CRISPRessoPooled_on_pooled-mixed-mode)

pooled-mixed-mode-genome-demux: $(_SENTINEL)
	$(call PYTEST_RUN,test_crispresso_cli[pooled_mixed_mode_genome_demux],CRISPRessoPooled_on_pooled-mixed-mode-genome-demux)

# ── WGS (pytest-backed) ─────────────────────────────────────────────
wgs: $(_SENTINEL)
	$(call PYTEST_RUN,test_crispresso_cli[wgs],CRISPRessoWGS_on_Both.Cas9.fastq.smallGenome)

# ── Compare / Aggregate (pytest-backed) ─────────────────────────────
compare: $(_SENTINEL) batch
	$(call PYTEST_RUN,test_compare,CRISPRessoCompare_on_Cas9_VS_Untreated)

aggregate: $(_SENTINEL) batch
	$(call PYTEST_RUN,test_aggregate,CRISPRessoAggregate_on_aggregate)

# ── VCF (pytest-backed) ─────────────────────────────────────────────
vcf: vcf-basic vcf-deletions-only vcf-insertions-only vcf-no-edits vcf-multi-amplicon vcf-base-edit-abe vcf-base-edit-cbe vcf-prime-edit-basic

vcf-basic: $(_SENTINEL)
	$(call PYTEST_RUN,test_crispresso_cli[vcf_basic],CRISPResso_on_vcf-basic)

vcf-deletions-only: $(_SENTINEL)
	$(call PYTEST_RUN,test_crispresso_cli[vcf_deletions_only],CRISPResso_on_vcf-deletions-only)

vcf-insertions-only: $(_SENTINEL)
	$(call PYTEST_RUN,test_crispresso_cli[vcf_insertions_only],CRISPResso_on_vcf-insertions-only)

vcf-no-edits: $(_SENTINEL)
	$(call PYTEST_RUN,test_crispresso_cli[vcf_no_edits],CRISPResso_on_vcf-no-edits)

vcf-multi-amplicon: $(_SENTINEL)
	$(call PYTEST_RUN,test_crispresso_cli[vcf_multi_amplicon],CRISPResso_on_vcf-multi-amplicon)

vcf-base-edit-cbe: $(_SENTINEL)
	$(call PYTEST_RUN,test_crispresso_cli[vcf_base_edit_cbe],CRISPResso_on_vcf-base-edit-cbe)

vcf-base-edit-abe: $(_SENTINEL)
	$(call PYTEST_RUN,test_crispresso_cli[vcf_base_edit_abe],CRISPResso_on_vcf-base-edit-abe)

vcf-prime-edit-basic: $(_SENTINEL)
	$(call PYTEST_RUN,test_crispresso_cli[vcf_prime_edit_basic],CRISPResso_on_vcf-prime-edit-basic)

# ── Non-pytest targets ──────────────────────────────────────────────
nhej: $(_SENTINEL)
	cd cli_integration_tests && $(PIXI) CRISPResso -r1 inputs/nhej.r1.fastq.gz -r2 inputs/nhej.r2.fastq.gz -a AATGTCCCCCAATGGGAAGTTCATCTGGCACTGCCCACAGGTGAGGAGGTCATGATCCCCTTCTGGAGCTCCCAACGGGCCGTGGTCTGGTTCATCATCTGTAAGAATGGCTTCAAGAGGCTCGGCTGTGGTT -n nhej --process_paired_fastq --place_report_in_output_folder --halt_on_plot_fail --debug

code-tests: params params-big-code params-multi-code params-medium params-multiple-codes params-small

params-big-code: $(_SENTINEL)
	cd cli_integration_tests && $(PIXI) CRISPResso -r1 inputs/FANC.Cas9.fastq -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -g GGAATCCCTTCTGCAGCACC -e CGGCCGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCTGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -c GGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCG --dump -qwc 20-30_45-50 -q 30 --default_min_aln_score 80 -an FANC -n params-big-code --base_edit -fg AGCCTTGCAGTGGGCGCGCTA,CCCACTGAAGGCCC --dsODN GCTAGATTTCCCAAGAAGA -gn hi -fgn dear -p max --place_report_in_output_folder --debug

params-multi-code: $(_SENTINEL)
	cd cli_integration_tests && $(PIXI) CRISPResso -r1 inputs/FANC.Cas9.fastq -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -g GGAATCCCTTCTGCAGCACC -e CGGCCGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCTGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -c GGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTT,ATGTTCCAATCAGTACGCAGAGAGTCG,ACCTGCGCCACATCCATCGGCGCTTTGGT --dump -qwc 20-30_45-50 -q 30 --default_min_aln_score 80 -an FANC -n params_multi_code --base_edit -fg AGCCTTGCAGTGGGCGCGCTA,CCCACTGAAGGCCC --dsODN GCTAGATTTCCCAAGAAGA -gn hi -fgn dear -p max --place_report_in_output_folder --debug

params-medium: $(_SENTINEL)
	cd cli_integration_tests && $(PIXI) CRISPResso -r1 inputs/FANC.Cas9.fastq -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -g GGAATCCCTTCTGCAGCACC -e CGGCCGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCTGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -c GGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAA --dump -qwc 20-30_45-50 -q 30 --default_min_aln_score 80 -an FANC -n params_medium --base_edit -fg AGCCTTGCAGTGGGCGCGCTA,CCCACTGAAGGCCC --dsODN GCTAGATTTCCCAAGAAGA -gn hi -fgn dear -p max --place_report_in_output_folder --debug

params-small: $(_SENTINEL)
	cd cli_integration_tests && $(PIXI) CRISPResso -r1 inputs/FANC.Cas9.fastq -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -g GGAATCCCTTCTGCAGCACC -e CGGCCGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCTGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -c GGGCCTTCGCGCACCTCATGGAATCCC --dump -qwc 20-30_45-50 -q 30 --default_min_aln_score 80 -an FANC -n params_small --base_edit -fg AGCCTTGCAGTGGGCGCGCTA,CCCACTGAAGGCCC --dsODN GCTAGATTTCCCAAGAAGA -gn hi -fgn dear -p max --place_report_in_output_folder --debug

params-multiple-codes: $(_SENTINEL)
	cd cli_integration_tests && $(PIXI) CRISPResso -r1 inputs/FANC.Cas9.fastq -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -g GGAATCCCTTCTGCAGCACC -e CGGCCGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCTGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -c GGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGC,TGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAA --dump -qwc 20-30_45-50 -q 30 --default_min_aln_score 80 -an FANC -n params_multiple_codes --base_editor_output -fg AGCCTTGCAGTGGGCGCGCTA,CCCACTGAAGGCCC --dsODN GCTAGATTTCCCAAGAAGA -gn hi -fgn dear -p max --place_report_in_output_folder --debug

large-batch: $(_SENTINEL)
	cd cli_integration_tests && $(PIXI) CRISPRessoBatch -bs inputs/FANC_large.batch -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -g GGAATCCCTTCTGCAGCACC --halt_on_plot_fail --debug --no_rerun --base_editor_output -p max -n large_batch --place_report_in_output_folder

pooled-prime-editing: $(_SENTINEL)
	cd cli_integration_tests && $(PIXI) CRISPRessoPooled -r1 inputs/prime.editing.fastq -f inputs/prime.editing.amplicons.txt --keep_intermediate --min_reads_to_use_region 1 --place_report_in_output_folder --halt_on_plot_fail --debug

batch-failing: $(_SENTINEL)
	cd cli_integration_tests && $(PIXI) CRISPRessoBatch -bs inputs/FANC_failing.batch -n batch-failing -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -g GGAATCCCTTCTGCAGCACC --debug --place_report_in_output_folder --base_editor_output --skip_failed --halt_on_plot_fail

# ── Web / stress tests ──────────────────────────────────────────────
stress: web_tests/web_stress_test.py
	$(PIXI) python $^

web_ui: web_tests/CRISPResso_Web_UI_Tests/web_ui_test.py
	$(PIXI) python $^ --log_file_path web_tests/UI_test_summary_log.txt

# ── syn-gen tests ────────────────────────────────────────────────────
syn-gen-test:
	cd syn-gen && $(PIXI) pytest test_syn_gen.py -v

syn-gen-e2e:
	cd syn-gen && $(PIXI) pytest test_bwa_e2e.py test_bwa_verify.py -v

syn-gen-all:
	cd syn-gen && $(PIXI) pytest test_syn_gen.py test_bwa_e2e.py test_bwa_verify.py -v

# ── pytest convenience targets ───────────────────────────────────────
pytest:
	$(PIXI) pytest test_cli.py

pytest-coverage:
	$(PIXI) pytest test_cli.py --with-coverage
	$(PIXI) coverage combine
	$(PIXI) coverage report

pytest-test:
	$(PIXI) pytest test_cli.py -k "$(TEST)" -v

coverage-report:
	$(PIXI) coverage html
	@echo "Coverage report: htmlcov/index.html"

coverage-clean:
	$(PIXI) coverage erase
	rm -rf htmlcov/
