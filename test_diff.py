"""Unit tests for diff.py — the file comparison engine.

Tests focus on correctness: ensuring files aren't missed, ignore rules
are applied symmetrically, normalization is stable, and warning files
don't cause false failures.

Run with:
    pytest test_diff.py -v
"""
import textwrap
from pathlib import Path

import pytest

import diff
from diff import (
    IGNORE_FILES,
    IGNORE_SUFFIX,
    WARNING_FILE_REGEXP,
    diff as diff_text,
    diff_dir,
    diff_dir_images,
    substitute_line,
    truncate_diff_lines,
    IMAGE_DEPS_AVAILABLE,
)

if IMAGE_DEPS_AVAILABLE:
    from PIL import Image
    import numpy as np


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_file(base, relpath, content=""):
    """Create a file under *base* with the given relative path and content."""
    p = Path(base) / relpath
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return p


def make_png(base, relpath, color='white', size=(10, 10)):
    """Create a small solid-color PNG under *base*."""
    p = Path(base) / relpath
    p.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new('RGB', size, color=color)
    img.save(str(p))
    return p


# ═══════════════════════════════════════════════════════════════════════════
# substitute_line — normalization regex tests
# ═══════════════════════════════════════════════════════════════════════════

class TestSubstituteLine:
    """Test that each normalization regex in substitute_line works correctly."""

    def test_float_rounding_basic(self):
        assert substitute_line("value is 3.14159") == "value is 3.142"

    def test_float_rounding_multiple(self):
        result = substitute_line("a=1.23456 b=7.89012")
        assert result == "a=1.235 b=7.89"

    def test_float_rounding_already_3_decimals(self):
        assert substitute_line("val=1.234") == "val=1.234"

    def test_float_rounding_trailing_zeros(self):
        # 1.10000 rounds to 1.1 (Python drops trailing zeros)
        assert substitute_line("val=1.10000") == "val=1.1"

    def test_float_rounding_zero_point_something(self):
        assert substitute_line("val=0.00049") == "val=0.0"

    def test_float_rounding_large_number(self):
        assert substitute_line("val=12345.6789") == "val=12345.679"

    def test_datetime_normalization(self):
        result = substitute_line("run at 2025-02-25 13:47:41")
        assert result == "run at 2024-01-11 12:34:56"

    def test_datetime_multiple(self):
        result = substitute_line("start=2023-01-01 00:00:00 end=2025-12-31 23:59:59")
        assert result == "start=2024-01-11 12:34:56 end=2024-01-11 12:34:56"

    def test_command_html_with_strong(self):
        line = "<p><strong>Command used: CRISPResso -r1 foo.fastq -a ATCG</strong></p>"
        assert substitute_line(line) == "<p>Command used: <command></p>"

    def test_command_html_without_strong(self):
        line = "<p>Command used: CRISPResso -r1 foo.fastq</p>"
        assert substitute_line(line) == "<p>Command used: <command></p>"

    def test_command_log_with_path(self):
        line = "/usr/local/bin/CRISPResso -r1 foo.fastq -a ATCG"
        assert substitute_line(line) == "CRISPResso <parameters>"

    def test_command_log_nested_path(self):
        line = "/home/user/.local/bin/CRISPRessoBatch -bs batch.txt"
        assert substitute_line(line) == "CRISPResso <parameters>"

    def test_plotly_path_normalization(self):
        line = '"/home/user/project/cli_integration_tests/plot.js"'
        result = substitute_line(line)
        assert "CRISPResso2_tests/cli_integration_tests/" in result

    def test_output_path_normalization(self):
        """OUTPUT_REGEXP is shadowed by COMMAND_LOG_REGEXP (which fires first
        and matches any path containing /CRISPResso). Both normalize the path,
        but COMMAND_LOG's broader match takes precedence."""
        line = "output in /home/user/CRISPResso2/cli_integration_tests/CRISPResso_on_test"
        result = substitute_line(line)
        # COMMAND_LOG_REGEXP matches first: [\S]*/CRISPResso.* → CRISPResso <parameters>
        assert result == "output in CRISPResso <parameters>"

    def test_sam_header_bowtie_version(self):
        line = "@PG\tID:bowtie2\tPN:bowtie2\tVN:2.4.1\tCL:bowtie2-align-s --very-sensitive"
        result = substitute_line(line)
        assert "VN:2.5.4" in result
        assert "<parameters>" in result

    def test_sam_header_hd(self):
        # Input has real tab chars; re.sub replacement r'@HD\tVN:...'
        # also produces real tabs (re.sub interprets \t in replacement)
        line = "@HD\tVN:1.5\tSO:coordinate"
        result = substitute_line(line)
        assert result == "@HD\tVN:1.0\tSO:unsorted"

    def test_no_match_passthrough(self):
        line = "ATCGATCGATCG"
        assert substitute_line(line) == "ATCGATCGATCG"

    def test_plain_text_no_floats(self):
        line = "This is a plain text line with no special patterns."
        assert substitute_line(line) == line

    def test_combined_float_and_datetime(self):
        line = "score=0.98765 at 2025-06-15 10:30:00"
        result = substitute_line(line)
        assert "0.988" in result
        assert "2024-01-11 12:34:56" in result


# ═══════════════════════════════════════════════════════════════════════════
# diff (text file comparison)
# ═══════════════════════════════════════════════════════════════════════════

class TestDiff:
    """Test text file comparison with normalization."""

    def test_identical_files_no_diff(self, tmp_path):
        content = "line1\nline2\nline3\n"
        make_file(tmp_path, "a.txt", content)
        make_file(tmp_path, "b.txt", content)
        result = diff_text(tmp_path / "a.txt", tmp_path / "b.txt")
        assert result == []

    def test_different_files_produce_diff(self, tmp_path):
        make_file(tmp_path, "a.txt", "line1\nline2\n")
        make_file(tmp_path, "b.txt", "line1\nline3\n")
        result = diff_text(tmp_path / "a.txt", tmp_path / "b.txt")
        assert len(result) > 0

    def test_normalization_makes_files_equal(self, tmp_path):
        """Two files differing only in float precision should produce no diff."""
        make_file(tmp_path, "a.txt", "value=3.14159265\n")
        make_file(tmp_path, "b.txt", "value=3.14160000\n")
        result = diff_text(tmp_path / "a.txt", tmp_path / "b.txt")
        assert result == [], "Float normalization should make these equal"

    def test_datetime_normalization_makes_files_equal(self, tmp_path):
        make_file(tmp_path, "a.txt", "run at 2025-02-25 13:00:00\n")
        make_file(tmp_path, "b.txt", "run at 2024-01-01 00:00:00\n")
        result = diff_text(tmp_path / "a.txt", tmp_path / "b.txt")
        assert result == [], "Datetime normalization should make these equal"

    def test_real_content_difference_detected(self, tmp_path):
        """Different non-normalizable content must produce a diff."""
        make_file(tmp_path, "a.txt", "ATCGATCG\n")
        make_file(tmp_path, "b.txt", "GCTAGCTA\n")
        result = diff_text(tmp_path / "a.txt", tmp_path / "b.txt")
        assert len(result) > 0


# ═══════════════════════════════════════════════════════════════════════════
# diff_dir — directory comparison (critical path)
# ═══════════════════════════════════════════════════════════════════════════

class TestDiffDir:
    """Test directory-level comparison: file discovery, ignore rules, warnings."""

    # --- Basic file matching ---

    def test_identical_dirs_no_diff(self, tmp_path, capsys):
        actual = tmp_path / "actual"
        expected = tmp_path / "expected"
        make_file(actual, "data.txt", "hello\n")
        make_file(expected, "data.txt", "hello\n")

        result = diff_dir(str(actual), str(expected))
        assert result is False

    def test_different_file_content_detected(self, tmp_path, capsys):
        actual = tmp_path / "actual"
        expected = tmp_path / "expected"
        make_file(actual, "data.txt", "hello\n")
        make_file(expected, "data.txt", "world\n")

        result = diff_dir(str(actual), str(expected))
        assert result is True

    def test_new_file_in_actual_detected(self, tmp_path, capsys):
        actual = tmp_path / "actual"
        expected = tmp_path / "expected"
        make_file(actual, "data.txt", "hello\n")
        make_file(actual, "extra.txt", "bonus\n")
        make_file(expected, "data.txt", "hello\n")

        result = diff_dir(str(actual), str(expected))
        assert result is True
        captured = capsys.readouterr()
        assert "New file in Actual" in captured.out

    def test_missing_file_from_actual_detected(self, tmp_path, capsys):
        actual = tmp_path / "actual"
        expected = tmp_path / "expected"
        make_file(actual, "data.txt", "hello\n")
        make_file(expected, "data.txt", "hello\n")
        make_file(expected, "missing.txt", "gone\n")

        result = diff_dir(str(actual), str(expected))
        assert result is True
        captured = capsys.readouterr()
        assert "Missing file" in captured.out

    def test_empty_dirs_no_diff(self, tmp_path):
        actual = tmp_path / "actual"
        expected = tmp_path / "expected"
        actual.mkdir()
        expected.mkdir()

        result = diff_dir(str(actual), str(expected))
        assert result is False

    # --- Subdirectory support ---

    def test_subdirectory_files_compared(self, tmp_path):
        actual = tmp_path / "actual"
        expected = tmp_path / "expected"
        make_file(actual, "sub/data.txt", "hello\n")
        make_file(expected, "sub/data.txt", "hello\n")

        result = diff_dir(str(actual), str(expected))
        assert result is False

    def test_subdirectory_file_difference_detected(self, tmp_path):
        actual = tmp_path / "actual"
        expected = tmp_path / "expected"
        make_file(actual, "sub/deep/data.txt", "hello\n")
        make_file(expected, "sub/deep/data.txt", "world\n")

        result = diff_dir(str(actual), str(expected))
        assert result is True

    def test_subdirectory_missing_file_detected(self, tmp_path, capsys):
        actual = tmp_path / "actual"
        expected = tmp_path / "expected"
        make_file(actual, "sub/a.txt", "hello\n")
        make_file(expected, "sub/a.txt", "hello\n")
        make_file(expected, "sub/b.txt", "extra\n")

        result = diff_dir(str(actual), str(expected))
        assert result is True
        captured = capsys.readouterr()
        assert "Missing file" in captured.out
        assert "b.txt" in captured.out

    # --- Suffix filtering ---

    def test_suffix_filtering_txt_only(self, tmp_path):
        """Only .txt files should be compared when suffixes=('.txt',)."""
        actual = tmp_path / "actual"
        expected = tmp_path / "expected"
        make_file(actual, "data.txt", "same\n")
        make_file(expected, "data.txt", "same\n")
        # Different .html file should be invisible
        make_file(actual, "report.html", "version A\n")
        make_file(expected, "report.html", "version B\n")

        result = diff_dir(str(actual), str(expected), suffixes=('.txt',))
        assert result is False

    def test_suffix_filtering_html_included(self, tmp_path):
        """When suffixes includes .html, html differences should be detected."""
        actual = tmp_path / "actual"
        expected = tmp_path / "expected"
        make_file(actual, "data.txt", "same\n")
        make_file(expected, "data.txt", "same\n")
        make_file(actual, "report.html", "version A\n")
        make_file(expected, "report.html", "version B\n")

        result = diff_dir(str(actual), str(expected), suffixes=('.txt', '.html'))
        assert result is True

    def test_suffix_filtering_excludes_unmatched(self, tmp_path):
        """Files with non-matching suffixes should be completely invisible."""
        actual = tmp_path / "actual"
        expected = tmp_path / "expected"
        # .txt files are identical
        make_file(actual, "data.txt", "same\n")
        make_file(expected, "data.txt", "same\n")
        # .png file only in actual — should be invisible with txt-only suffixes
        make_file(actual, "plot.png", "PNG data\n")

        result = diff_dir(str(actual), str(expected), suffixes=('.txt',))
        assert result is False

    def test_suffix_filtering_missing_file_only_matched_suffixes(self, tmp_path, capsys):
        """Missing file detection should also respect suffix filter."""
        actual = tmp_path / "actual"
        expected = tmp_path / "expected"
        make_file(actual, "data.txt", "same\n")
        make_file(expected, "data.txt", "same\n")
        # .html only in expected — invisible with txt-only suffixes
        make_file(expected, "extra.html", "extra\n")

        result = diff_dir(str(actual), str(expected), suffixes=('.txt',))
        assert result is False

    # --- Ignore files (actual side — should work) ---

    def test_ignore_running_log_in_actual(self, tmp_path):
        """CRISPResso_RUNNING_LOG.txt should be ignored even with different content."""
        actual = tmp_path / "actual"
        expected = tmp_path / "expected"
        make_file(actual, "data.txt", "same\n")
        make_file(expected, "data.txt", "same\n")
        make_file(actual, "CRISPResso_RUNNING_LOG.txt", "actual log\n")
        make_file(expected, "CRISPResso_RUNNING_LOG.txt", "expected log\n")

        result = diff_dir(str(actual), str(expected))
        assert result is False

    def test_ignore_all_running_logs_in_actual(self, tmp_path):
        """All tool-specific RUNNING_LOG files should be ignored."""
        actual = tmp_path / "actual"
        expected = tmp_path / "expected"
        make_file(actual, "data.txt", "same\n")
        make_file(expected, "data.txt", "same\n")
        for log_file in IGNORE_FILES:
            if log_file.endswith('.txt'):
                make_file(actual, log_file, "actual\n")
                make_file(expected, log_file, "expected\n")

        result = diff_dir(str(actual), str(expected))
        assert result is False

    def test_ignore_suffix_pattern_in_actual(self, tmp_path):
        """Any file ending in _RUNNING_LOG.txt should be ignored (suffix pattern)."""
        actual = tmp_path / "actual"
        expected = tmp_path / "expected"
        make_file(actual, "data.txt", "same\n")
        make_file(expected, "data.txt", "same\n")
        # Not in IGNORE_FILES but matches IGNORE_SUFFIX
        make_file(actual, "CustomTool_RUNNING_LOG.txt", "actual\n")
        make_file(expected, "CustomTool_RUNNING_LOG.txt", "expected\n")

        result = diff_dir(str(actual), str(expected))
        assert result is False

    def test_ignore_running_log_only_in_actual(self, tmp_path, capsys):
        """Running log only in actual (not in expected) should not cause diff."""
        actual = tmp_path / "actual"
        expected = tmp_path / "expected"
        make_file(actual, "data.txt", "same\n")
        make_file(expected, "data.txt", "same\n")
        make_file(actual, "CRISPResso_RUNNING_LOG.txt", "log content\n")

        result = diff_dir(str(actual), str(expected))
        assert result is False

    # --- Ignore files (expected side — BUG: not applied) ---

    def test_ignore_running_log_only_in_expected(self, tmp_path, capsys):
        """Running log only in expected should NOT be flagged as missing."""
        actual = tmp_path / "actual"
        expected = tmp_path / "expected"
        make_file(actual, "data.txt", "same\n")
        make_file(expected, "data.txt", "same\n")
        make_file(expected, "CRISPResso_RUNNING_LOG.txt", "log content\n")

        result = diff_dir(str(actual), str(expected))
        assert result is False, (
            "Ignored file CRISPResso_RUNNING_LOG.txt only in expected should not "
            "cause diff_dir to return True"
        )

    def test_ignore_suffix_only_in_expected(self, tmp_path, capsys):
        """File matching _RUNNING_LOG.txt suffix only in expected should NOT be flagged."""
        actual = tmp_path / "actual"
        expected = tmp_path / "expected"
        make_file(actual, "data.txt", "same\n")
        make_file(expected, "data.txt", "same\n")
        make_file(expected, "CustomTool_RUNNING_LOG.txt", "log content\n")

        result = diff_dir(str(actual), str(expected))
        assert result is False, (
            "Ignored suffix _RUNNING_LOG.txt only in expected should not "
            "cause diff_dir to return True"
        )

    # --- fastp_report.html ignore behavior ---

    def test_fastp_report_ignored_with_html_suffix(self, tmp_path):
        """fastp_report.html in both dirs with different content — ignored."""
        actual = tmp_path / "actual"
        expected = tmp_path / "expected"
        make_file(actual, "data.txt", "same\n")
        make_file(expected, "data.txt", "same\n")
        make_file(actual, "fastp_report.html", "version A\n")
        make_file(expected, "fastp_report.html", "version B\n")

        result = diff_dir(str(actual), str(expected), suffixes=('.txt', '.html'))
        assert result is False

    def test_fastp_report_invisible_without_html_suffix(self, tmp_path):
        """fastp_report.html invisible when suffixes exclude .html (skip_html)."""
        actual = tmp_path / "actual"
        expected = tmp_path / "expected"
        make_file(actual, "data.txt", "same\n")
        make_file(expected, "data.txt", "same\n")
        make_file(actual, "fastp_report.html", "version A\n")
        make_file(expected, "fastp_report.html", "version B\n")

        result = diff_dir(str(actual), str(expected), suffixes=('.txt',))
        assert result is False

    def test_fastp_report_missing_from_actual_not_flagged(self, tmp_path, capsys):
        """fastp_report.html only in expected should NOT be flagged as missing."""
        actual = tmp_path / "actual"
        expected = tmp_path / "expected"
        make_file(actual, "data.txt", "same\n")
        make_file(expected, "data.txt", "same\n")
        make_file(expected, "fastp_report.html", "some content\n")

        result = diff_dir(str(actual), str(expected), suffixes=('.txt', '.html'))
        assert result is False, (
            "fastp_report.html is in IGNORE_FILES — its absence from actual "
            "should not cause a failure"
        )

    # --- Warning file behavior ---

    def test_warning_file_diff_does_not_fail(self, tmp_path, capsys):
        """CRISPResso2_report.html diff should be printed but not cause failure."""
        actual = tmp_path / "actual"
        expected = tmp_path / "expected"
        make_file(actual, "data.txt", "same\n")
        make_file(expected, "data.txt", "same\n")
        make_file(actual, "CRISPResso2_report.html", "version A\n")
        make_file(expected, "CRISPResso2_report.html", "version B\n")

        result = diff_dir(str(actual), str(expected), suffixes=('.txt', '.html'))
        assert result is False, "Warning file diff should not cause failure"
        captured = capsys.readouterr()
        assert "Comparing" in captured.out

    def test_warning_file_new_does_not_fail(self, tmp_path, capsys):
        """CRISPResso2_report.html only in actual should not cause failure."""
        actual = tmp_path / "actual"
        expected = tmp_path / "expected"
        make_file(actual, "data.txt", "same\n")
        make_file(expected, "data.txt", "same\n")
        make_file(actual, "CRISPResso2_report.html", "report\n")

        result = diff_dir(str(actual), str(expected), suffixes=('.txt', '.html'))
        assert result is False, "New warning file should not cause failure"
        captured = capsys.readouterr()
        assert "New file in Actual" in captured.out

    def test_warning_file_missing_does_not_fail(self, tmp_path, capsys):
        """CRISPResso2_report.html only in expected should not cause failure."""
        actual = tmp_path / "actual"
        expected = tmp_path / "expected"
        make_file(actual, "data.txt", "same\n")
        make_file(expected, "data.txt", "same\n")
        make_file(expected, "CRISPResso2_report.html", "report\n")

        result = diff_dir(str(actual), str(expected), suffixes=('.txt', '.html'))
        assert result is False, "Missing warning file should not cause failure"
        captured = capsys.readouterr()
        assert "Missing file" in captured.out

    def test_warning_file_variants(self, tmp_path):
        """All CRISPResso2*_report.html variants should be treated as warnings."""
        actual = tmp_path / "actual"
        expected = tmp_path / "expected"
        make_file(actual, "data.txt", "same\n")
        make_file(expected, "data.txt", "same\n")

        warning_names = [
            "CRISPResso2_report.html",
            "CRISPResso2Batch_report.html",
            "CRISPResso2Pooled_report.html",
            "CRISPResso2WGS_report.html",
            "CRISPResso2Compare_report.html",
            "CRISPResso2Aggregate_report.html",
        ]
        for name in warning_names:
            make_file(actual, name, "version A\n")
            make_file(expected, name, "version B\n")

        result = diff_dir(str(actual), str(expected), suffixes=('.txt', '.html'))
        assert result is False, (
            "All CRISPResso2*_report.html variants should be warning-only"
        )

    def test_non_warning_html_diff_does_fail(self, tmp_path):
        """A non-warning .html file with differences should cause failure."""
        actual = tmp_path / "actual"
        expected = tmp_path / "expected"
        make_file(actual, "data.txt", "same\n")
        make_file(expected, "data.txt", "same\n")
        make_file(actual, "custom_report.html", "version A\n")
        make_file(expected, "custom_report.html", "version B\n")

        result = diff_dir(str(actual), str(expected), suffixes=('.txt', '.html'))
        assert result is True

    # --- Mixed scenarios ---

    def test_multiple_files_one_different(self, tmp_path):
        """If one file out of many differs, diff_dir returns True."""
        actual = tmp_path / "actual"
        expected = tmp_path / "expected"
        make_file(actual, "a.txt", "same\n")
        make_file(expected, "a.txt", "same\n")
        make_file(actual, "b.txt", "same\n")
        make_file(expected, "b.txt", "same\n")
        make_file(actual, "c.txt", "actual\n")
        make_file(expected, "c.txt", "expected\n")

        result = diff_dir(str(actual), str(expected))
        assert result is True

    def test_diff_and_warning_together(self, tmp_path):
        """Real diff + warning file diff: should return True (from the real diff)."""
        actual = tmp_path / "actual"
        expected = tmp_path / "expected"
        make_file(actual, "data.txt", "actual\n")
        make_file(expected, "data.txt", "expected\n")
        make_file(actual, "CRISPResso2_report.html", "version A\n")
        make_file(expected, "CRISPResso2_report.html", "version B\n")

        result = diff_dir(str(actual), str(expected), suffixes=('.txt', '.html'))
        assert result is True

    def test_only_ignored_files_different(self, tmp_path):
        """If only ignored files differ, diff_dir should return False."""
        actual = tmp_path / "actual"
        expected = tmp_path / "expected"
        make_file(actual, "data.txt", "same\n")
        make_file(expected, "data.txt", "same\n")
        # All of these should be ignored
        make_file(actual, "CRISPResso_RUNNING_LOG.txt", "actual\n")
        make_file(expected, "CRISPResso_RUNNING_LOG.txt", "expected\n")
        make_file(actual, "CRISPRessoBatch_RUNNING_LOG.txt", "actual\n")
        make_file(expected, "CRISPRessoBatch_RUNNING_LOG.txt", "expected\n")

        result = diff_dir(str(actual), str(expected))
        assert result is False

    def test_ignore_files_in_subdirectory(self, tmp_path):
        """Ignored files in subdirectories should also be skipped."""
        actual = tmp_path / "actual"
        expected = tmp_path / "expected"
        make_file(actual, "sub/data.txt", "same\n")
        make_file(expected, "sub/data.txt", "same\n")
        make_file(actual, "sub/CRISPResso_RUNNING_LOG.txt", "actual\n")
        make_file(expected, "sub/CRISPResso_RUNNING_LOG.txt", "expected\n")

        result = diff_dir(str(actual), str(expected))
        assert result is False

    def test_sam_and_vcf_suffixes(self, tmp_path):
        """Verify .sam and .vcf files are compared when in suffixes."""
        actual = tmp_path / "actual"
        expected = tmp_path / "expected"
        make_file(actual, "alignment.sam", "same\n")
        make_file(expected, "alignment.sam", "same\n")
        make_file(actual, "variants.vcf", "actual\n")
        make_file(expected, "variants.vcf", "expected\n")

        result = diff_dir(str(actual), str(expected), suffixes=('.sam', '.vcf'))
        assert result is True

    def test_normalization_applied_during_dir_diff(self, tmp_path):
        """Files that differ only in float precision should not cause a diff."""
        actual = tmp_path / "actual"
        expected = tmp_path / "expected"
        make_file(actual, "data.txt", "score=0.123456789\n")
        make_file(expected, "data.txt", "score=0.123400000\n")

        result = diff_dir(str(actual), str(expected))
        assert result is False


# ═══════════════════════════════════════════════════════════════════════════
# diff_dir_images — image directory comparison
# ═══════════════════════════════════════════════════════════════════════════

@pytest.mark.skipif(
    not IMAGE_DEPS_AVAILABLE,
    reason="Pillow and/or NumPy not installed",
)
class TestDiffDirImages:
    """Test image directory comparison for file discovery and RMSE logic."""

    def test_identical_images_no_diff(self, tmp_path):
        actual = tmp_path / "actual"
        expected = tmp_path / "expected"
        make_png(actual, "plot.png", color='white')
        make_png(expected, "plot.png", color='white')

        result = diff_dir_images(str(actual), str(expected))
        assert result is False

    def test_different_images_detected(self, tmp_path):
        actual = tmp_path / "actual"
        expected = tmp_path / "expected"
        make_png(actual, "plot.png", color='white')
        make_png(expected, "plot.png", color='black')

        result = diff_dir_images(str(actual), str(expected))
        assert result is True

    def test_new_image_in_actual_detected(self, tmp_path, capsys):
        actual = tmp_path / "actual"
        expected = tmp_path / "expected"
        make_png(actual, "plot.png", color='white')
        make_png(actual, "extra.png", color='red')
        make_png(expected, "plot.png", color='white')

        result = diff_dir_images(str(actual), str(expected))
        assert result is True
        captured = capsys.readouterr()
        assert "New image" in captured.out

    def test_missing_image_from_actual_detected(self, tmp_path, capsys):
        actual = tmp_path / "actual"
        expected = tmp_path / "expected"
        make_png(actual, "plot.png", color='white')
        make_png(expected, "plot.png", color='white')
        make_png(expected, "missing.png", color='blue')

        result = diff_dir_images(str(actual), str(expected))
        assert result is True
        captured = capsys.readouterr()
        assert "Missing image" in captured.out

    def test_empty_dirs_no_diff(self, tmp_path):
        actual = tmp_path / "actual"
        expected = tmp_path / "expected"
        actual.mkdir()
        expected.mkdir()

        result = diff_dir_images(str(actual), str(expected))
        assert result is False

    def test_subdirectory_images_compared(self, tmp_path):
        actual = tmp_path / "actual"
        expected = tmp_path / "expected"
        make_png(actual, "sub/plot.png", color='white')
        make_png(expected, "sub/plot.png", color='white')

        result = diff_dir_images(str(actual), str(expected))
        assert result is False

    def test_subdirectory_image_difference_detected(self, tmp_path):
        actual = tmp_path / "actual"
        expected = tmp_path / "expected"
        make_png(actual, "sub/plot.png", color='white')
        make_png(expected, "sub/plot.png", color='black')

        result = diff_dir_images(str(actual), str(expected))
        assert result is True

    def test_similar_images_below_threshold(self, tmp_path):
        """Nearly identical images (slight color shift) should not be flagged."""
        actual = tmp_path / "actual"
        expected = tmp_path / "expected"
        # Create nearly identical images — white vs very light gray
        p_actual = Path(actual) / "plot.png"
        p_expected = Path(expected) / "plot.png"
        p_actual.parent.mkdir(parents=True, exist_ok=True)
        p_expected.parent.mkdir(parents=True, exist_ok=True)
        Image.new('RGB', (10, 10), color=(255, 255, 255)).save(str(p_actual))
        Image.new('RGB', (10, 10), color=(250, 250, 250)).save(str(p_expected))

        result = diff_dir_images(str(actual), str(expected))
        assert result is False

    def test_custom_threshold(self, tmp_path):
        """A very strict threshold should flag minor differences."""
        actual = tmp_path / "actual"
        expected = tmp_path / "expected"
        p_actual = Path(actual) / "plot.png"
        p_expected = Path(expected) / "plot.png"
        p_actual.parent.mkdir(parents=True, exist_ok=True)
        p_expected.parent.mkdir(parents=True, exist_ok=True)
        Image.new('RGB', (10, 10), color=(255, 255, 255)).save(str(p_actual))
        Image.new('RGB', (10, 10), color=(200, 200, 200)).save(str(p_expected))

        # Default threshold: may or may not flag
        # Very strict threshold: should flag
        result = diff_dir_images(str(actual), str(expected), threshold=0.001)
        assert result is True


class TestDiffDirImagesDepsUnavailable:
    """Test behavior when Pillow/NumPy are not available."""

    def test_returns_false_when_deps_unavailable(self, tmp_path, monkeypatch, capsys):
        """When IMAGE_DEPS_AVAILABLE is False, should return False gracefully."""
        monkeypatch.setattr(diff, 'IMAGE_DEPS_AVAILABLE', False)

        actual = tmp_path / "actual"
        expected = tmp_path / "expected"
        actual.mkdir()
        expected.mkdir()

        result = diff_dir_images(str(actual), str(expected))
        assert result is False
        captured = capsys.readouterr()
        assert "not installed" in captured.out


# ═══════════════════════════════════════════════════════════════════════════
# truncate_diff_lines — utility
# ═══════════════════════════════════════════════════════════════════════════

class TestTruncateDiffLines:
    """Test diff line truncation."""

    def test_under_limit_unchanged(self):
        lines = ["line {}\n".format(i) for i in range(5)]
        result = truncate_diff_lines(lines, max_lines=10)
        assert result == lines

    def test_at_limit_unchanged(self):
        lines = ["line {}\n".format(i) for i in range(10)]
        result = truncate_diff_lines(lines, max_lines=10)
        assert result == lines

    def test_over_limit_truncated_with_summary(self):
        lines = ["line {}\n".format(i) for i in range(15)]
        result = truncate_diff_lines(lines, max_lines=10)
        assert len(result) == 11  # 10 kept + 1 summary
        assert result[:10] == lines[:10]
        assert "truncated" in result[-1]
        assert "5 more lines omitted" in result[-1]

    def test_one_over_limit(self):
        lines = ["line {}\n".format(i) for i in range(11)]
        result = truncate_diff_lines(lines, max_lines=10)
        assert len(result) == 11  # 10 kept + 1 summary
        assert "1 more lines omitted" in result[-1]

    def test_empty_list(self):
        result = truncate_diff_lines([], max_lines=10)
        assert result == []

    def test_default_max_lines(self):
        """Default max_lines should be PDF_DIFF_MAX_LINES (100)."""
        lines = ["line {}\n".format(i) for i in range(101)]
        result = truncate_diff_lines(lines)
        assert len(result) == 101  # 100 kept + 1 summary
        assert "1 more lines omitted" in result[-1]


# ═══════════════════════════════════════════════════════════════════════════
# WARNING_FILE_REGEXP — pattern validation
# ═══════════════════════════════════════════════════════════════════════════

class TestWarningFileRegexp:
    """Verify WARNING_FILE_REGEXP matches all expected report filenames."""

    @pytest.mark.parametrize("filename", [
        "CRISPResso2_report.html",
        "CRISPResso2Batch_report.html",
        "CRISPResso2Pooled_report.html",
        "CRISPResso2WGS_report.html",
        "CRISPResso2Compare_report.html",
        "CRISPResso2Aggregate_report.html",
    ])
    def test_matches_known_warning_files(self, filename):
        assert WARNING_FILE_REGEXP.search(filename), (
            "{} should match WARNING_FILE_REGEXP".format(filename)
        )

    @pytest.mark.parametrize("filename", [
        "custom_report.html",
        "CRISPResso_report.html",      # Missing the "2"
        "CRISPResso2_report.txt",       # Wrong extension
        "data.txt",
        "fastp_report.html",
    ])
    def test_does_not_match_non_warning_files(self, filename):
        assert not WARNING_FILE_REGEXP.search(filename), (
            "{} should NOT match WARNING_FILE_REGEXP".format(filename)
        )


# ═══════════════════════════════════════════════════════════════════════════
# IGNORE_FILES / IGNORE_SUFFIX — constant validation
# ═══════════════════════════════════════════════════════════════════════════

class TestIgnoreConstants:
    """Validate the ignore constants contain the expected entries."""

    def test_all_running_logs_in_ignore_files(self):
        expected_logs = [
            'CRISPResso_RUNNING_LOG.txt',
            'CRISPRessoBatch_RUNNING_LOG.txt',
            'CRISPRessoPooled_RUNNING_LOG.txt',
            'CRISPRessoWGS_RUNNING_LOG.txt',
            'CRISPRessoCompare_RUNNING_LOG.txt',
        ]
        for log in expected_logs:
            assert log in IGNORE_FILES, "{} should be in IGNORE_FILES".format(log)

    def test_fastp_in_ignore_files(self):
        assert 'fastp_report.html' in IGNORE_FILES

    def test_ignore_suffix(self):
        assert IGNORE_SUFFIX == '_RUNNING_LOG.txt'

    def test_all_ignore_files_match_suffix_or_are_special(self):
        """Every entry in IGNORE_FILES should either match IGNORE_SUFFIX or be
        a known special case (fastp_report.html)."""
        special_cases = {'fastp_report.html'}
        for f in IGNORE_FILES:
            assert f.endswith(IGNORE_SUFFIX) or f in special_cases, (
                "{} doesn't match IGNORE_SUFFIX and isn't a known special case".format(f)
            )
