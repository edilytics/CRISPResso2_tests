"""Synthetic end-to-end tests for the CRISPRessoPooled demultiplexer.

These tests generate all reads at runtime with syn-gen.  They intentionally
check read conservation and demultiplexing reports rather than comparing
large, platform-dependent pooled HTML/plot outputs.
"""

from __future__ import annotations

import csv
import gzip
import random
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest

from syn_gen import generate_synthetic_data


AMPLICON_A = (
    "CGGATGTTCCAATCAGTACGCAGAGAGTCGCCGTCTCCAAGGTGAAAGCGGAAGTAGGGCCTTCGCGCACCTCAT"
    "GGAATCCCTTCTGCAGCACCTGGATCGCTTTTCCGAGCTTCTGGCGGTCTCAAGCACTACCTACGTCAGCACCTG"
    "GGACCCCGCCACCGTGCGCCGGGCCTTGCAGTGGGCGCGCTACCTGCGCCACATCCATCGGCGCTTTGGTCGG"
)
AMPLICON_B = (
    "GGAAACGCCCATGCAATTAGTCTATTTCTGCTGCAAGTAAGCATGCATTTGTAGGCTTGATGCTTTTTTTCTGCT"
    "TCTCCAGCCCTGGCCTGGGTCAATCCTTGGGGCCCAGACTGAGCACGTGATGGCAGAGGAAAGGAAGCCCTGCT"
    "TCCTCCAGAGGGCGTCGCAGGACAGCTTTTCCTAGACAGGGGCTAGTATGTGCAGCTCCTGCACCGGGATACTGGTTGACAAG"
)
GUIDE_A = "GGAATCCCTTCTGCAGCACC"
GUIDE_B = "GGCCCAGACTGAGCACGTGA"


@dataclass(frozen=True)
class Target:
    name: str
    sequence: str
    guide: str
    reads: int
    seed: int


TARGETS = (
    Target("TARGET_A", AMPLICON_A, GUIDE_A, 48, 1001),
    Target("TARGET_B", AMPLICON_B, GUIDE_B, 52, 1002),
)


@dataclass
class SyntheticPool:
    fastq: Path
    amplicons: Path
    targets: tuple[Target, ...]
    stats: dict[str, dict]
    genome: Path | None = None
    genome_index: Path | None = None
    loci: dict[str, tuple[str, int, int]] | None = None


def _count_fastq(path: Path) -> int:
    opener = gzip.open if path.suffix == ".gz" else open
    count = 0
    with opener(path, "rt", encoding="utf-8") as handle:
        while True:
            header = handle.readline()
            if not header:
                return count
            sequence = handle.readline()
            separator = handle.readline()
            quality = handle.readline()
            assert sequence and separator and quality, f"Incomplete FASTQ record in {path}"
            assert header.startswith("@")
            assert separator.startswith("+")
            assert len(sequence.rstrip()) == len(quality.rstrip())
            count += 1


def _write_amplicon_file(path: Path, targets: tuple[Target, ...]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for target in targets:
            handle.write(f"{target.name}\t{target.sequence}\t{target.guide}\n")


def _append_renamed_fastq(source: Path, destination, target_name: str) -> None:
    with source.open("r", encoding="utf-8") as handle:
        index = 0
        while True:
            header = handle.readline()
            if not header:
                break
            sequence = handle.readline()
            separator = handle.readline()
            quality = handle.readline()
            assert sequence and separator and quality
            destination.write(f"@{target_name}_read_{index}\n")
            destination.write(sequence)
            destination.write(separator)
            destination.write(quality)
            index += 1


def _random_backbone(length: int, seed: int) -> str:
    rng = random.Random(seed)
    return "".join(rng.choice("ACGT") for _ in range(length))


def _build_genome(tmp_path: Path, targets: tuple[Target, ...]) -> tuple[Path, Path, dict[str, tuple[str, int, int]]]:
    """Place each target at a known, unique locus and build a Bowtie2 index."""
    records = []
    loci = {}
    for index, target in enumerate(targets):
        chromosome = f"chrSynthetic{index + 1}"
        start = 500 + index * 200
        prefix = _random_backbone(start, 7000 + index)
        suffix = _random_backbone(700, 8000 + index)
        records.append((chromosome, prefix + target.sequence + suffix))
        loci[target.name] = (chromosome, start + 1, start + len(target.sequence))

    genome = tmp_path / "synthetic_genome.fa"
    with genome.open("w", encoding="utf-8") as handle:
        for chromosome, sequence in records:
            handle.write(f">{chromosome}\n{sequence}\n")

    index_prefix = tmp_path / "synthetic_genome"
    result = subprocess.run(
        ["bowtie2-build", str(genome), str(index_prefix)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    return genome, index_prefix, loci


def _make_pool(tmp_path: Path, *, with_genome: bool = False) -> SyntheticPool:
    amplicons = tmp_path / "synthetic.amplicons.tsv"
    fastq = tmp_path / "synthetic.pool.fastq"
    _write_amplicon_file(amplicons, TARGETS)

    stats = {}
    with fastq.open("w", encoding="utf-8") as output:
        for target in TARGETS:
            prefix = tmp_path / target.name
            stats[target.name] = generate_synthetic_data(
                amplicon=target.sequence,
                guide=target.guide,
                num_reads=target.reads,
                edit_rate=0.5,
                error_rate=0.0,
                output_prefix=str(prefix),
                amplicon_name=target.name,
                seed=target.seed,
                quiet=True,
                mode="nhej",
            )
            _append_renamed_fastq(prefix.with_suffix(".fastq"), output, target.name)

    pool = SyntheticPool(fastq, amplicons, TARGETS, stats)
    if with_genome:
        pool.genome, pool.genome_index, pool.loci = _build_genome(tmp_path, TARGETS)
    return pool


def _require_pooled_tools():
    missing = [tool for tool in ("CRISPRessoPooled", "bowtie2-build", "samtools") if shutil.which(tool) is None]
    if missing:
        pytest.skip("Missing pooled test dependencies: " + ", ".join(missing))


def _run_pooled(pool: SyntheticPool, output_parent: Path, name: str, *, genome_wide: bool = False) -> Path:
    _require_pooled_tools()
    output_parent.mkdir(parents=True, exist_ok=True)
    command = [
        "CRISPRessoPooled",
        "-r1", str(pool.fastq),
        "-f", str(pool.amplicons),
        "--min_reads_to_use_region", "1",
        "--keep_intermediate",
        "--suppress_plots",
        "--limit_open_files_for_demux",
        "--n_processes", "2",
        "-n", name,
        "-o", str(output_parent),
    ]
    if pool.genome_index is not None:
        command.extend(["-x", str(pool.genome_index)])
    if genome_wide:
        command.append("--demultiplex_genome_wide")

    result = subprocess.run(command, capture_output=True, text=True, timeout=300)
    assert result.returncode == 0, (
        "CRISPRessoPooled failed:\n"
        + " ".join(command)
        + "\nSTDOUT:\n"
        + result.stdout
        + "\nSTDERR:\n"
        + result.stderr
    )
    return output_parent / f"CRISPRessoPooled_on_{name}"


def _report_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def _assert_amplicon_demux(pool: SyntheticPool, output: Path) -> None:
    rows = _report_rows(output / "REPORT_READS_ALIGNED_TO_AMPLICONS.txt")
    assert {row["amplicon_name"] for row in rows} == {target.name for target in pool.targets}

    for target in pool.targets:
        row = next(row for row in rows if row["amplicon_name"] == target.name)
        observed = int(row["n_reads"])
        expected = target.reads
        generated = pool.stats[target.name]
        assert generated["total_reads"] == expected
        assert generated["edited_reads"] > 0
        assert observed == expected, f"{target.name}: expected {expected}, observed {observed}"

        demux_path = Path(row["Demultiplexed_fastq.gz_filename"])
        if not demux_path.is_absolute():
            candidates = [
                output / demux_path,
                output.parent / demux_path,
                output.parent.parent / demux_path,
                output / demux_path.name,
            ]
            demux_path = next((candidate for candidate in candidates if candidate.exists()), candidates[0])
        assert demux_path.exists(), f"Missing demultiplexed FASTQ for {target.name}"
        assert _count_fastq(demux_path) == expected

        subruns = [path for path in output.glob(f"CRISPResso_on_{target.name}*") if path.is_dir()]
        assert subruns, f"Missing CRISPResso sub-run for {target.name}"
        assert (subruns[0] / "CRISPResso2_info.json").exists()


def _assert_genome_demux(pool: SyntheticPool, output: Path) -> None:
    report = output / "REPORT_READS_ALIGNED_TO_GENOME_ALL_DEPTHS.txt"
    rows = _report_rows(report)
    assert rows
    assert pool.loci is not None
    chromosomes = {chromosome for chromosome, _, _ in pool.loci.values()}
    assert {row["chr_id"] for row in rows}.issubset(chromosomes)

    total = 0
    for row in rows:
        total += int(row["number of reads"])
        path = Path(row["output filename"])
        if not path.is_absolute():
            candidates = [
                output / path,
                output.parent / path,
                output.parent.parent / path,
                output / "MAPPED_REGIONS" / path.name,
            ]
            path = next((candidate for candidate in candidates if candidate.exists()), candidates[0])
        assert path.exists(), f"Missing mapped-region FASTQ: {path}"
        assert _count_fastq(path) == int(row["number of reads"])

    assert total == sum(target.reads for target in pool.targets)


@pytest.fixture
def pooled_tools():
    _require_pooled_tools()


def test_synthetic_pooled_amplicon_demultiplexing(tmp_path: Path, pooled_tools):
    """Synthetic reads are assigned to the correct amplicon exactly once."""
    pool = _make_pool(tmp_path)
    output = _run_pooled(pool, tmp_path / "outputs", "synthetic_amplicons")
    _assert_amplicon_demux(pool, output)


def test_synthetic_pooled_mixed_interval_demultiplexing(tmp_path: Path, pooled_tools):
    """Restricted mixed-mode demultiplexing preserves reads at target loci."""
    pool = _make_pool(tmp_path, with_genome=True)
    output = _run_pooled(pool, tmp_path / "outputs", "synthetic_mixed_intervals")
    _assert_genome_demux(pool, output)

    rows = _report_rows(output / "REPORT_READS_ALIGNED_TO_GENOME_ALL_DEPTHS.txt")
    assert {row["chr_id"] for row in rows} == {locus[0] for locus in pool.loci.values()}


def test_synthetic_pooled_genome_wide_demultiplexing(tmp_path: Path, pooled_tools):
    """Genome-wide mode groups CIGAR-derived spans without losing reads."""
    pool = _make_pool(tmp_path, with_genome=True)
    output = _run_pooled(
        pool,
        tmp_path / "outputs",
        "synthetic_genome_wide",
        genome_wide=True,
    )
    _assert_genome_demux(pool, output)
    assert list((output / "MAPPED_REGIONS").glob("*.fastq.gz"))
