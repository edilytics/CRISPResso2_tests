.PHONY: all install test test_cli_integration clean clean_cli_integration \
	basic params batch pooled wgs compare

CRISPRESSO2_DIR := ../CRISPResso2
CRISPRESSO2_SOURCES := $(wildcard $(CRISPRESSO2_DIR)/CRISPResso2/*.py*)
TEST_CLI_INTEGRATION_DIRECTORIES := $(addprefix cli_integration_tests/,CRISPResso_on_FANC.Cas9 \
CRISPResso_on_params CRISPRessoBatch_on_FANC CRISPRessoPooled_on_Both.Cas9 \
CRISPRessoWGS_on_Both.Cas9.fastq.smallGenome \
CRISPRessoCompare_on_Cas9_VS_Untreated)

all: test

install: $(CRISPRESSO2_SOURCES)
	cd $(CRISPRESSO2_DIR) && output=`pip install -e .` || echo "$$output"

test: clean test_cli_integration

test_cli_integration: $(TEST_CLI_INTEGRATION_DIRECTORIES)

clean : clean_cli_integration

clean_cli_integration:
	rm -rf cli_integration_tests/CRISPResso_on_FANC.Cas9* \
cli_integration_tests/CRISPResso_on_params* \
cli_integration_tests/CRISPRessoBatch_on_FANC* \
cli_integration_tests/CRISPRessoPooled_on_Both.Cas9* \
cli_integration_tests/CRISPRessoWGS_on_Both.Cas9.fastq.smallGenome* \
cli_integration_tests/CRISPRessoCompare_on_Cas9_VS_Untreated* \
	log.txt


basic: cli_integration_tests/CRISPResso_on_FANC.Cas9

cli_integration_tests/CRISPResso_on_FANC.Cas9: install cli_integration_tests/inputs/FANC.Cas9.fastq
	cd cli_integration_tests && output=`CRISPResso -r1 inputs/FANC.Cas9.fastq -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -g GGAATCCCTTCTGCAGCACC --debug 2>&1` || echo "$$output"
	python diff.py $@ --dir_b cli_integration_tests/expected_results/CRISPResso_on_FANC.Cas9

params: cli_integration_tests/CRISPResso_on_params

cli_integration_tests/CRISPResso_on_params: install cli_integration_tests/inputs/FANC.Cas9.fastq
	cd cli_integration_tests && output=`CRISPResso -r1 inputs/FANC.Cas9.fastq -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -g GGAATCCCTTCTGCAGCACC -e CGGCCGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCTGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -c GGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTT --dump -qwc 20-30_45-50 -q 30 --default_min_aln_score 80 -an FANC -n params --base_edit -fg AGCCTTGCAGTGGGCGCGCTA,CCCACTGAAGGCCC --dsODN GCTAGATTTCCCAAGAAGA -gn hi -fgn dear --debug 2>&1` || echo "$$output"
	python diff.py $@ --dir_b cli_integration_tests/expected_results/CRISPResso_on_params

nhej: cli_integration_tests/CRISPResso_on_nhej

cli_integration_tests/CRISPResso_on_nhej: install cli_integration_tests/
	cd cli_integration_tests && CRISPResso -r1 inputs/nhej.r1.fastq.gz -r2 inputs/nhej.r2.fastq.gz -a AATGTCCCCCAATGGGAAGTTCATCTGGCACTGCCCACAGGTGAGGAGGTCATGATCCCCTTCTGGAGCTCCCAACGGGCCGTGGTCTGGTTCATCATCTGTAAGAATGGCTTCAAGAGGCTCGGCTGTGGTT -n nhej --process_paired_fastq --debug # || echo "$$output"

batch: cli_integration_tests/CRISPRessoBatch_on_FANC

cli_integration_tests/CRISPRessoBatch_on_FANC: install cli_integration_tests/inputs/FANC.batch
	cd cli_integration_tests && output=`CRISPRessoBatch -bs inputs/FANC.batch -a CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCATGGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTGGGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG -g GGAATCCCTTCTGCAGCACC --debug --base_editor 2>&1` || echo "$$output"
	python diff.py $@ --dir_b cli_integration_tests/expected_results/CRISPRessoBatch_on_FANC

pooled: cli_integration_tests/CRISPRessoPooled_on_Both.Cas9

cli_integration_tests/CRISPRessoPooled_on_Both.Cas9: install cli_integration_tests/inputs/Both.Cas9.fastq cli_integration_tests/inputs/Cas9.amplicons.txt
	cd cli_integration_tests && output=`CRISPRessoPooled -r1 inputs/Both.Cas9.fastq -f inputs/Cas9.amplicons.txt --keep_intermediate --min_reads_to_use_region 100 -p 4 --debug 2>&1` || echo "$$output"
	python diff.py $@ --dir_b cli_integration_tests/expected_results/CRISPRessoPooled_on_Both.Cas9

wgs: cli_integration_tests/CRISPRessoWGS_on_Both.Cas9.fastq.smallGenome

cli_integration_tests/CRISPRessoWGS_on_Both.Cas9.fastq.smallGenome: install cli_integration_tests/inputs/Both.Cas9.fastq.smallGenome.bam cli_integration_tests/inputs/small_genome/smallGenome.fa cli_integration_tests/inputs/Cas9.regions.txt
	cd cli_integration_tests && output=`CRISPRessoWGS -b inputs/Both.Cas9.fastq.smallGenome.bam -r inputs/small_genome/smallGenome.fa -f inputs/Cas9.regions.txt --debug 2>&1` || echo "$$output"
	python diff.py $@ --dir_b cli_integration_tests/expected_results/CRISPRessoWGS_on_Both.Cas9.fastq.smallGenome

compare: cli_integration_tests/CRISPRessoCompare_on_Cas9_VS_Untreated

cli_integration_tests/CRISPRessoCompare_on_Cas9_VS_Untreated: install cli_integration_tests/CRISPRessoBatch_on_FANC
	cd cli_integration_tests && output=`CRISPRessoCompare CRISPRessoBatch_on_FANC/CRISPResso_on_Cas9/ CRISPRessoBatch_on_FANC/CRISPResso_on_Untreated/ --debug 2>&1` || echo "$$output"
	python diff.py $@ --dir_b cli_integration_tests/expected_results/CRISPRessoCompare_on_Cas9_VS_Untreated

stress: web_stress_test.py
	python web_stress_test.py
