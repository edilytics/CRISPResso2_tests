import argparse
import json
import os
import re
import sys
import subprocess
import tempfile
import zlib
from datetime import timedelta
from difflib import unified_diff
from pathlib import Path
from os.path import basename, join, dirname
from shutil import copyfile

try:
    from PIL import Image, ImageFilter
    import numpy as np
    IMAGE_DEPS_AVAILABLE = True
except ImportError:
    IMAGE_DEPS_AVAILABLE = False


FLOAT_REGEXP = re.compile(r'\d+\.\d+')
DATETIME_REGEXP = re.compile(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}')
COMMAND_HTML_REGEXP = re.compile(r'<p>(<strong>)?Command used:.*')
COMMAND_LOG_REGEXP = re.compile(r'[\S]*/CRISPResso.*')
OUTPUT_REGEXP = re.compile(r'[\S]*/CRISPResso2[\S]*/cli_integration_tests/CRISPResso[\S]*')
PLOTLY_PATH_REGEXP = re.compile(r'/\S+/cli_integration_tests/')
SAM_HEADER_BOWTIE_VERSION_REGEXP = re.compile(r'@PG\tID:bowtie2\tPN:bowtie2\tVN:.*')
SAM_HEADER_REGEXP = re.compile(r'@HD\tVN:.*')
IGNORE_FILES = frozenset([
    'CRISPResso_RUNNING_LOG.txt',
    'CRISPRessoBatch_RUNNING_LOG.txt',
    'CRISPRessoPooled_RUNNING_LOG.txt',
    'CRISPRessoWGS_RUNNING_LOG.txt',
    'CRISPRessoCompare_RUNNING_LOG.txt',
    'fastp_report.html',
])
IGNORE_SUFFIX = '_RUNNING_LOG.txt'
WARNING_FILE_REGEXP = re.compile(r'CRISPResso2(Aggregate|Batch|Pooled|WGS|Compare)?_report.html')

TEXT_SUFFIXES = ('.txt', '.html', '.sam', '.vcf')
DATA_SUFFIXES = ('.txt', '.sam', '.vcf')
HTML_SUFFIXES = ('.html',)
PDF_SUFFIXES = ('.pdf',)

# PDF stream detection patterns
PDF_STREAM_REGEXP = re.compile(rb'stream\r?\n(.*?)endstream', re.DOTALL)
PDF_FONT_KEYWORDS = ('GDEF', 'cmap', 'CIDInit')

# PNG image comparison constants
IMAGE_SUFFIXES = ('.png',)
DEFAULT_IMAGE_THRESHOLD = 0.2  # RMSE threshold (0-1 scale); 0.10 = 10%
IMAGE_THUMBNAIL_SIZE = (256, 256)  # Downscale target for comparison
IMAGE_BLUR_RADIUS = 1  # Gaussian blur to smooth anti-aliasing / font noise

# PDF diff truncation
PDF_DIFF_MAX_LINES = 100

# Axis tick labels: purely numeric strings (integers, decimals, negatives)
# that matplotlib's AutoLocator generates in a platform-dependent way.
# Filtered from PDF text comparison because tick intervals depend on font
# metrics which differ between macOS and Linux.
NUMERIC_TICK_REGEXP = re.compile(r'^-?\d[\d,]*\.?\d*$')


def which(program):
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


YDIFF_INSTALLED = which('ydiff')
if not YDIFF_INSTALLED:
    print('ydiff is not installed. Install it (`pip install ydiff`) for better diffs.')


def round_float(f):
    """Round float to 3 decimal places

    Parameters
    ----------
    f : re.Match
        Float string

    Returns
    -------
    str
        float rounded to 3 decimal places
    """
    return str(round(float(f.group(0)), 3))


def substitute_line(line):
    """Substitute floats and datetimes in a line

    Parameters
    ----------
    line : str
        Line to substitute

    Returns
    -------
    str
        Line with floats and datetimes substituted
    """
    line = FLOAT_REGEXP.sub(round_float, line)
    line = DATETIME_REGEXP.sub('2024-01-11 12:34:56', line)
    line = COMMAND_HTML_REGEXP.sub('<p>Command used: <command></p>', line)
    line = COMMAND_LOG_REGEXP.sub('CRISPResso <parameters>', line)
    line = PLOTLY_PATH_REGEXP.sub('CRISPResso2_tests/cli_integration_tests/', line)
    line = OUTPUT_REGEXP.sub('CRISPResso2_tests/cli_integration_tests/CRISPResso', line)
    line = SAM_HEADER_BOWTIE_VERSION_REGEXP.sub(r'@PG\tID:bowtie2\tPN:bowtie2\tVN:2.5.4\tCL:bowtie2-align-s <parameters>', line)
    line = SAM_HEADER_REGEXP.sub(r'@HD\tVN:1.0\tSO:unsorted', line)
    return line


def diff(file_a, file_b):
    with open(file_a) as fh_a, open(file_b) as fh_b:
        lines_a = [substitute_line(line).strip() + '\n' for line in fh_a]
        lines_b = [substitute_line(line).strip() + '\n' for line in fh_b]
        return list(unified_diff(lines_a, lines_b))


def extract_pdf_text(path):
    """Extract human-readable text strings from a matplotlib-generated PDF.

    Decompresses FlateDecode streams, finds text rendering commands
    (Tj and TJ operators), and extracts the text content.  Normalizes
    the inter-character spacing that matplotlib uses (``H e l l o`` →
    ``Hello``) so that different PDF encodings of the same text produce
    identical output.

    Parameters
    ----------
    path : str or Path
        Path to the PDF file.

    Returns
    -------
    list of str
        Ordered list of text strings found in the PDF.
    """
    with open(path, 'rb') as fh:
        data = fh.read()
    texts = []
    # Regex to match TJ/Tj operations that may span multiple lines.
    # On Linux, matplotlib adds inter-character kerning values that make
    # TJ arrays wrap across lines, e.g.:
    #   [ (\x00P) 17.43 (\x00r) 21.95
    #   (\x00edicted cleavage position) ]
    #   TJ
    # The \[...\]\s*TJ pattern captures the full array content.
    tj_array_regexp = re.compile(r'\[(.*?)\]\s*TJ', re.DOTALL)
    # Single-string Tj operator (always single-line)
    tj_single_regexp = re.compile(r'\(((?:[^\\)]|\\.)*)\)\s*Tj')
    for m in PDF_STREAM_REGEXP.finditer(data):
        try:
            decompressed = zlib.decompress(m.group(1))
            stream = decompressed.decode('latin-1')
        except Exception:
            continue
        # Skip font / character-map streams
        if any(kw in stream for kw in PDF_FONT_KEYWORDS):
            continue
        # Extract text from TJ array operators (may span multiple lines)
        for tj_match in tj_array_regexp.finditer(stream):
            array_content = tj_match.group(1)
            parts = re.findall(r'\(((?:[^\\)]|\\.)*)\)', array_content)
            raw = ''.join(parts)
            raw = raw.replace('\x00', '')
            raw = raw.replace('\\(', '(').replace('\\)', ')')
            text = raw.strip()
            if text:
                texts.append(text)
        # Extract text from single-string Tj operators
        for tj_match in tj_single_regexp.finditer(stream):
            raw = tj_match.group(1)
            raw = raw.replace('\x00', '')
            raw = raw.replace('\\(', '(').replace('\\)', ')')
            text = raw.strip()
            if text:
                texts.append(text)
    return texts


def diff_pdf(file_a, file_b):
    """Diff two PDF files by comparing their text content.

    Extracts text strings from PDF drawing streams (axis labels, titles,
    legend entries, data values) and diffs them.  Drawing coordinates are
    ignored — use PNG RMSE comparison for visual layout differences.

    Purely numeric values (axis tick labels like ``0``, ``500``, ``1.5``)
    are excluded from the "significant" diff because matplotlib's
    ``AutoLocator`` chooses platform-dependent tick intervals based on
    font metrics.  A separate "full" diff (including numeric ticks) is
    returned so callers can emit a warning without failing the test.

    Parameters
    ----------
    file_a : str or Path
        Path to the first PDF (actual).
    file_b : str or Path
        Path to the second PDF (expected).

    Returns
    -------
    tuple (significant_diff, tick_diff)
        *significant_diff*: unified diff lines excluding numeric-only
        tick labels — empty if text content is effectively identical.
        *tick_diff*: unified diff lines from the full (unfiltered)
        comparison — non-empty when numeric axis ticks differ across
        platforms.  Callers should warn but not fail on this.
    """
    texts_a = extract_pdf_text(file_a)
    texts_b = extract_pdf_text(file_b)

    # Full diff (includes numeric axis tick labels)
    full_diff = list(unified_diff(
        [t + '\n' for t in texts_a],
        [t + '\n' for t in texts_b],
    ))

    # Filtered diff (significant — excludes numeric-only tick labels)
    filtered_a = [t for t in texts_a if not NUMERIC_TICK_REGEXP.match(t)]
    filtered_b = [t for t in texts_b if not NUMERIC_TICK_REGEXP.match(t)]
    sig_diff = list(unified_diff(
        [t + '\n' for t in filtered_a],
        [t + '\n' for t in filtered_b],
    ))

    # tick_diff is the full diff only when the significant diff is clean
    # (i.e. the only differences are numeric ticks)
    tick_diff = full_diff if (full_diff and not sig_diff) else []

    return sig_diff, tick_diff


def truncate_diff_lines(lines, max_lines=PDF_DIFF_MAX_LINES):
    """Truncate a list of diff lines to a maximum number of lines.

    Parameters
    ----------
    lines : list
        Diff lines to potentially truncate.
    max_lines : int
        Maximum number of lines to keep.

    Returns
    -------
    list
        Original lines if within limit, otherwise first *max_lines* lines
        plus a summary line indicating how many were omitted.
    """
    if len(lines) <= max_lines:
        return lines
    omitted = len(lines) - max_lines
    return lines[:max_lines] + [
        '... (truncated: {0} more lines omitted)\n'.format(omitted),
    ]


def truncate_diff_lines(lines, max_lines=PDF_DIFF_MAX_LINES):
    """Truncate a list of diff lines to a maximum number of lines.

    Parameters
    ----------
    lines : list
        Diff lines to potentially truncate.
    max_lines : int
        Maximum number of lines to keep.

    Returns
    -------
    list
        Original lines if within limit, otherwise first *max_lines* lines
        plus a summary line indicating how many were omitted.
    """
    if len(lines) <= max_lines:
        return lines
    omitted = len(lines) - max_lines
    return lines[:max_lines] + [
        '... (truncated: {0} more lines omitted)\n'.format(omitted),
    ]


def diff_image(file_a, file_b, threshold=DEFAULT_IMAGE_THRESHOLD):
    """Compare two images using downscaled grayscale RMSE.

    Downscales both images to a common thumbnail size and converts to
    grayscale to smooth out anti-aliasing and font rendering differences
    across platforms/matplotlib versions. Computes RMSE normalized to
    [0, 1] as the primary similarity metric.

    Parameters
    ----------
    file_a : str or Path
        Path to the first image (actual).
    file_b : str or Path
        Path to the second image (expected).
    threshold : float
        RMSE threshold above which images are considered different.

    Returns
    -------
    dict
        Keys: 'is_different' (bool), 'rmse' (float), 'diff_percent' (float),
        'error' (str or None), 'size_a' (tuple), 'size_b' (tuple).
    """
    result = {
        'is_different': True,
        'rmse': 1.0,
        'diff_percent': 100.0,
        'error': None,
        'size_a': None,
        'size_b': None,
    }

    try:
        img_a = Image.open(file_a)
        img_b = Image.open(file_b)
    except Exception as e:
        result['error'] = str(e)
        return result

    result['size_a'] = img_a.size
    result['size_b'] = img_b.size

    # Normalize to the same dimensions so that slight size differences
    # (from font metrics / DPI across matplotlib versions) don't cause
    # pixel-level misalignment after thumbnailing.
    common_full = (
        max(img_a.width, img_b.width),
        max(img_a.height, img_b.height),
    )
    img_a = img_a.convert('L').resize(common_full, Image.LANCZOS)
    img_b = img_b.convert('L').resize(common_full, Image.LANCZOS)

    # Downscale to thumbnail
    img_a.thumbnail(IMAGE_THUMBNAIL_SIZE, Image.LANCZOS)
    img_b.thumbnail(IMAGE_THUMBNAIL_SIZE, Image.LANCZOS)

    # Light Gaussian blur to smooth out anti-aliasing and font-rendering
    # noise that differs across platforms / matplotlib versions.
    img_a = img_a.filter(ImageFilter.GaussianBlur(IMAGE_BLUR_RADIUS))
    img_b = img_b.filter(ImageFilter.GaussianBlur(IMAGE_BLUR_RADIUS))

    arr_a = np.array(img_a, dtype=np.float64)
    arr_b = np.array(img_b, dtype=np.float64)

    # RMSE normalized to [0, 1]
    rmse = np.sqrt(np.mean((arr_a - arr_b) ** 2)) / 255.0

    # Percentage of pixels differing by more than 10% of the pixel range
    diff_percent = float(np.mean(np.abs(arr_a - arr_b) > 25.5) * 100)

    result['rmse'] = float(rmse)
    result['diff_percent'] = diff_percent
    result['is_different'] = rmse > threshold

    return result


def print_image_diff(file_a, file_b, result):
    """Print a human-readable summary of an image comparison result."""
    status = '\033[91mDIFFERENT\033[0m' if result['is_different'] else '\033[93mMINOR\033[0m'
    print('  {status}  RMSE={rmse:.4f}  ({diff_pct:.1f}% pixels differ)  {file}'.format(
        status=status,
        rmse=result['rmse'],
        diff_pct=result['diff_percent'],
        file=file_a,
    ))
    if result['size_a'] != result['size_b']:
        print('           Size mismatch: actual={0} expected={1}'.format(
            result['size_a'], result['size_b'],
        ))
    if result['error']:
        print('           Error: {0}'.format(result['error']))


def diff_dir_images(actual, expected, threshold=DEFAULT_IMAGE_THRESHOLD,
                    suffixes=IMAGE_SUFFIXES, prompt_to_update=False):
    """Compare all PNG images in two directories using RMSE.

    This is a fallback for when matplotlib versions change and PDF
    stream comparison is too strict. Uses downscaled grayscale RMSE
    to detect major visual differences while tolerating anti-aliasing
    and font rendering changes.

    Parameters
    ----------
    actual : str
        Path to directory with actual results.
    expected : str
        Path to directory with expected results.
    threshold : float
        RMSE threshold for flagging differences.
    suffixes : tuple
        Image file extensions to compare.
    prompt_to_update : bool
        Whether to prompt user to update differing images.

    Returns
    -------
    bool
        True if any images differ significantly.
    """
    if not IMAGE_DEPS_AVAILABLE:
        print('Pillow and/or NumPy not installed. Skipping image comparison.')
        print('Install with: pip install Pillow numpy')
        return False

    files_actual = {
        f.relative_to(actual): f
        for f in Path(actual).glob('**/*')
        if f.suffix in suffixes
    }
    files_expected = {
        f.relative_to(expected): f
        for f in Path(expected).glob('**/*')
        if f.suffix in suffixes
    }

    if not files_actual and not files_expected:
        return False

    diff_exists = False
    n_compared = 0
    n_different = 0

    for file_rel, file_path_actual in sorted(files_actual.items()):
        if file_rel in files_expected:
            n_compared += 1
            result = diff_image(file_path_actual, files_expected[file_rel], threshold)
            if result['rmse'] > 0.001:  # Skip completely identical images
                if result['is_different']:
                    n_different += 1
                    diff_exists = True
                    print_image_diff(file_path_actual, files_expected[file_rel], result)
                    if prompt_to_update:
                        update_file(str(file_path_actual), str(files_expected[file_rel]))
                else:
                    # Minor difference, just note it (don't fail)
                    print_image_diff(file_path_actual, files_expected[file_rel], result)
        else:
            print('New image in Actual ({0}) not found in Expected ({1})'.format(
                file_rel, expected,
            ))
            diff_exists = True
            if prompt_to_update:
                update_file(str(file_path_actual), str(join(expected, file_rel)))

    for file_rel in sorted(files_expected.keys()):
        if file_rel not in files_actual:
            print('Missing image {0} from Actual ({1})'.format(file_rel, actual))
            diff_exists = True
            if prompt_to_update:
                remove_file(str(join(expected, file_rel)))

    # Summary
    if n_compared > 0:
        print('\nImage comparison summary: {compared} compared, {different} significantly different (threshold={threshold})'.format(
            compared=n_compared,
            different=n_different,
            threshold=threshold,
        ))

    return diff_exists


def generate_plot_comparison_html(actual_dir, expected_dir):
    """Generate an HTML page comparing plots with differences side-by-side.

    For each plot that has a PDF text diff or any PNG pixel difference,
    shows actual and expected PNGs side-by-side with the text diff below.

    Parameters
    ----------
    actual_dir : str or Path
        Directory with actual results.
    expected_dir : str or Path
        Directory with expected results.

    Returns
    -------
    str or None
        Path to the generated HTML file, or None if no differences found.
    """
    import base64
    import platform

    actual_dir = Path(actual_dir)
    expected_dir = Path(expected_dir)

    actual_pngs = {f.relative_to(actual_dir): f for f in actual_dir.glob('**/*.png')}
    expected_pngs = {f.relative_to(expected_dir): f for f in expected_dir.glob('**/*.png')}
    actual_pdfs = {f.relative_to(actual_dir): f for f in actual_dir.glob('**/*.pdf')}
    expected_pdfs = {f.relative_to(expected_dir): f for f in expected_dir.glob('**/*.pdf')}

    # Collect all unique plot stems (filename without extension).
    # Use string manipulation because Path.with_suffix breaks on
    # filenames with multiple dots like "4a.Combined_insertion...".
    def _stem(rel):
        s = str(rel)
        return s[:s.rfind('.')] if '.' in s else s

    stems = set()
    for rel in list(actual_pngs) + list(expected_pngs) + list(actual_pdfs) + list(expected_pdfs):
        stems.add(_stem(rel))

    comparisons = []
    for stem in sorted(stems):
        png_rel = Path(stem + '.png')
        pdf_rel = Path(stem + '.pdf')

        pdf_diff_lines = []
        pdf_tick_warning = False
        significant = False

        # PDF text diff
        if pdf_rel in actual_pdfs and pdf_rel in expected_pdfs:
            sig_diff, tick_diff = diff_pdf(actual_pdfs[pdf_rel], expected_pdfs[pdf_rel])
            if sig_diff:
                pdf_diff_lines = truncate_diff_lines(sig_diff)
                significant = True
            elif tick_diff:
                # Only numeric axis ticks differ — warn, don't fail
                pdf_diff_lines = truncate_diff_lines(tick_diff)
                pdf_tick_warning = True

        # PNG pixel diff
        image_result = None
        if IMAGE_DEPS_AVAILABLE and png_rel in actual_pngs and png_rel in expected_pngs:
            image_result = diff_image(actual_pngs[png_rel], expected_pngs[png_rel])
            if image_result['is_different']:
                significant = True

        # Missing files
        if png_rel in actual_pngs and png_rel not in expected_pngs:
            significant = True
        if png_rel not in actual_pngs and png_rel in expected_pngs:
            significant = True

        if not significant and not pdf_tick_warning:
            continue

        def encode_png(path):
            with open(path, 'rb') as f:
                return base64.b64encode(f.read()).decode()

        comparisons.append({
            'name': str(stem),
            'actual_png': encode_png(actual_pngs[png_rel]) if png_rel in actual_pngs else None,
            'expected_png': encode_png(expected_pngs[png_rel]) if png_rel in expected_pngs else None,
            'pdf_diff': pdf_diff_lines,
            'pdf_tick_warning': pdf_tick_warning,
            'image_result': image_result,
        })

    if not comparisons:
        return None

    # Build HTML
    test_name = actual_dir.name
    sections = []
    for comp in comparisons:
        # Images
        if comp['actual_png']:
            actual_img = '<img src="data:image/png;base64,{0}" />'.format(comp['actual_png'])
        else:
            actual_img = '<div class="missing">Not found</div>'
        if comp['expected_png']:
            expected_img = '<img src="data:image/png;base64,{0}" />'.format(comp['expected_png'])
        else:
            expected_img = '<div class="missing">Not found</div>'

        # Stats
        stats = ''
        if comp['image_result']:
            r = comp['image_result']
            stats = 'RMSE={rmse:.4f} &middot; {pct:.1f}% pixels differ'.format(
                rmse=r['rmse'], pct=r['diff_percent'],
            )
            if r['size_a'] != r['size_b']:
                stats += ' &middot; size mismatch: {0} vs {1}'.format(r['size_a'], r['size_b'])

        # PDF text diff
        diff_html = ''
        if comp['pdf_diff']:
            diff_lines = []
            for line in comp['pdf_diff']:
                escaped = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').rstrip('\n')
                if escaped.startswith('+') and not escaped.startswith('+++'):
                    diff_lines.append('<span class="added">{0}</span>'.format(escaped))
                elif escaped.startswith('-') and not escaped.startswith('---'):
                    diff_lines.append('<span class="removed">{0}</span>'.format(escaped))
                elif escaped.startswith('@@'):
                    diff_lines.append('<span class="hunk">{0}</span>'.format(escaped))
                else:
                    diff_lines.append(escaped)
            if comp.get('pdf_tick_warning'):
                header = '<div class="tick-warning">⚠ Axis tick labels differ (platform-dependent auto-ticking — not a failure)</div>'
            else:
                header = ''
            diff_html = '{header}<div class="diff-block">{diff}</div>'.format(
                header=header, diff='\n'.join(diff_lines),
            )

        # Diff overlay (only when both images exist)
        overlay_html = ''
        if comp['actual_png'] and comp['expected_png']:
            overlay_html = """
                <div class="image-panel overlay-panel" style="display:none">
                    <h3>Diff overlay</h3>
                    <div class="overlay-container">
                        <img src="data:image/png;base64,{actual_b64}" />
                        <img src="data:image/png;base64,{expected_b64}" class="overlay-img" />
                    </div>
                </div>""".format(actual_b64=comp['actual_png'], expected_b64=comp['expected_png'])

        sections.append("""
        <div class="comparison">
            <h2>{name} {toggle}</h2>
            <div class="images">
                <div class="image-panel">
                    <h3>Actual</h3>
                    {actual}
                </div>
                <div class="image-panel">
                    <h3>Expected</h3>
                    {expected}
                </div>
                {overlay}
            </div>
            {stats}
            {diff}
        </div>""".format(
            name=comp['name'],
            toggle='<button class="toggle-overlay" onclick="toggleOverlay(this)">Show diff</button>'
                   if overlay_html else '',
            actual=actual_img,
            expected=expected_img,
            overlay=overlay_html,
            stats='<div class="stats">{0}</div>'.format(stats) if stats else '',
            diff=diff_html,
        ))

    html = """<!DOCTYPE html>
<html><head>
<title>Plot Comparison: {test_name}</title>
<style>
    body {{ font-family: system-ui, -apple-system, sans-serif; margin: 20px; background: #f5f5f5; }}
    h1 {{ color: #333; }}
    .summary {{ color: #666; margin-bottom: 24px; }}
    .comparison {{ background: white; margin: 20px 0; padding: 20px; border-radius: 8px;
                   box-shadow: 0 1px 3px rgba(0,0,0,0.12); }}
    .comparison h2 {{ margin-top: 0; color: #333; font-size: 16px; font-family: monospace;
                      word-break: break-all; }}
    .images {{ display: flex; gap: 20px; }}
    .image-panel {{ flex: 1; min-width: 0; }}
    .image-panel img {{ max-width: 100%; border: 1px solid #ddd; border-radius: 4px; }}
    .image-panel h3 {{ margin: 0 0 8px; color: #666; font-size: 14px; }}
    .diff-block {{ background: #1e1e1e; color: #d4d4d4; padding: 12px; border-radius: 4px;
                   margin-top: 16px; font-family: monospace; font-size: 13px;
                   white-space: pre-wrap; overflow-x: auto; line-height: 1.5; }}
    .diff-block .added {{ color: #4ec9b0; }}
    .diff-block .removed {{ color: #f44747; }}
    .diff-block .hunk {{ color: #569cd6; }}
    .stats {{ color: #888; font-size: 13px; margin-top: 12px; }}
    .missing {{ color: #f44747; font-style: italic; padding: 40px; text-align: center;
                border: 2px dashed #f44747; border-radius: 4px; }}
    .tick-warning {{ color: #b58900; font-size: 13px; margin: 12px 0 4px; font-style: italic; }}
    .toggle-overlay {{ font-size: 12px; padding: 2px 10px; margin-left: 12px;
                       cursor: pointer; border: 1px solid #ccc; border-radius: 4px;
                       background: #f5f5f5; vertical-align: middle; }}
    .toggle-overlay:hover {{ background: #e8e8e8; }}
    .overlay-container {{ position: relative; }}
    .overlay-container img:first-child {{ max-width: 100%; border: 1px solid #ddd; border-radius: 4px; }}
    .overlay-img {{ position: absolute; top: 0; left: 0; max-width: 100%;
                    mix-blend-mode: difference; }}
</style>
<script>
function toggleOverlay(btn) {{
    var comp = btn.closest('.comparison');
    var panel = comp.querySelector('.overlay-panel');
    var visible = panel.style.display !== 'none';
    panel.style.display = visible ? 'none' : '';
    btn.textContent = visible ? 'Show diff' : 'Hide diff';
}}
</script>
</head><body>
    <h1>Plot Comparison: {test_name}</h1>
    <p class="summary">{n} plot(s) with differences &middot; {actual_dir} vs {expected_dir}</p>
    {sections}
</body></html>""".format(
        test_name=test_name,
        n=len(comparisons),
        actual_dir=actual_dir,
        expected_dir=expected_dir,
        sections='\n'.join(sections),
    )

    output_dir = Path(tempfile.mkdtemp())
    output_path = output_dir / 'plot_comparison_{0}.html'.format(test_name)
    with open(output_path, 'w') as f:
        f.write(html)

    print('\nPlot comparison: {0}'.format(output_path))

    # Open in browser
    if platform.system() == 'Darwin':
        subprocess.Popen(['open', str(output_path)])
    elif platform.system() == 'Linux':
        subprocess.Popen(['xdg-open', str(output_path)])

    return str(output_path)


def print_diff(diff_results):
    if YDIFF_INSTALLED:
        with tempfile.NamedTemporaryFile(mode='w') as fh:
            fh.writelines(''.join(diff_results))
            fh.flush()
            subprocess.check_call(f'cat {fh.name} | ydiff -s -w 0 --wrap -p cat', shell=True)
    else:
        for line in diff_results:
            print(line, end='')


def find_dir_matches(file_path_a, files_b, matches):
    dir_a = basename(dirname(file_path_a))
    for ind in matches:
        dir_b = basename(dirname(files_b[ind]))
        if dir_a == dir_b:
            return ind
    return -1


def update_file(actual, expected):
    print('\nDo you want to update this file?')
    update_input = input('[y/n]: ')
    if update_input.lower() == 'n':
        return
    os.makedirs(dirname(expected), exist_ok=True)
    copyfile(actual, expected)


def remove_file(file_path):
    print('Do you want to remove this file?')
    remove_input = input('[y/n]: ')
    if remove_input.lower() == 'n':
        return
    os.remove(file_path)


def diff_dir(actual, expected, suffixes=TEXT_SUFFIXES, prompt_to_update=False,
             strict=False):
    """Compare files in two directories.

    Parameters
    ----------
    actual : str
        Path to directory with actual results.
    expected : str
        Path to directory with expected results.
    suffixes : tuple
        File extensions to compare.
    prompt_to_update : bool
        Whether to prompt the user to update differing files.
    strict : bool
        When True, treat *all* diffs as failures — even for report HTML
        files that are normally warning-only (``WARNING_FILE_REGEXP``).
        Use this when comparing against a curated expected-results
        baseline where any diff indicates a real change.

    Returns
    -------
    bool
        True if any files differ.
    """
    files_actual = {f.relative_to(actual): f for f in Path(actual).glob('**/*') if f.suffix in suffixes}
    files_expected = {f.relative_to(expected): f for f in Path(expected).glob('**/*') if f.suffix in suffixes}
    diff_exists = False
    for file_basename_actual, file_path_actual in files_actual.items():
        fname = basename(file_basename_actual)
        if fname in IGNORE_FILES or fname.endswith(IGNORE_SUFFIX):
            continue
        if file_basename_actual in files_expected:
            if file_path_actual.suffix in PDF_SUFFIXES:
                sig_diff, tick_diff = diff_pdf(file_path_actual, files_expected[file_basename_actual])
                if sig_diff:
                    diff_results = truncate_diff_lines(sig_diff)
                elif tick_diff:
                    diff_results = None  # don't fail
                    print('\033[93mWARNING\033[0m Axis tick labels differ (platform-dependent): {0}'.format(
                        file_path_actual,
                    ))
                    print_diff(truncate_diff_lines(tick_diff))
                else:
                    diff_results = None
            else:
                diff_results = diff(file_path_actual, files_expected[file_basename_actual])
            if diff_results:
                print('Comparing {0} to {1}'.format(
                    file_path_actual, files_expected[file_basename_actual],
                ))
                print_diff(diff_results)
                if strict or not WARNING_FILE_REGEXP.search(str(file_path_actual)):
                    diff_exists |= True
                if prompt_to_update:
                    update_file(file_path_actual, files_expected[file_basename_actual])
        else:
            print('New file in Actual ({0}) not found in Expected ({1})'.format(file_basename_actual, expected))
            if strict or not WARNING_FILE_REGEXP.search(str(file_path_actual)):
                diff_exists |= True
            if prompt_to_update:
                update_file(file_path_actual, join(expected, file_basename_actual))

    for file_basename_expected in files_expected.keys():
        fname = basename(file_basename_expected)
        if fname in IGNORE_FILES or fname.endswith(IGNORE_SUFFIX):
            continue
        if file_basename_expected not in files_actual:
            print('Missing file {0} from Actual ({1})'.format(file_basename_expected, actual))
            if strict or not WARNING_FILE_REGEXP.search(str(file_basename_expected)):
                diff_exists |= True
            if prompt_to_update:
                remove_file(join(expected, file_basename_expected))

    return diff_exists


def diff_running_times(
    actual,
    expected,
    percent_time_delta,
    info_file,
    keys=('running_info', 'running_time', 'value'),
):
    def get_timedelta(obj):
        current_obj = obj
        for key in keys:
            if key in current_obj:
                current_obj = current_obj[key]
            else:
                raise Warning(
                    'In parsing the timedelta,'
                    ' {0} is not in the object: {1}.'.format(key, obj),
                )
                return timedelta()
        return timedelta(
            days=current_obj['days'],
            seconds=current_obj['seconds'],
            microseconds=current_obj['microseconds'],
        )

    path_a, path_b = Path(actual) / info_file, Path(expected) / info_file
    if path_a.exists() and path_b.exists():
        with open(path_a) as fh_a, open(path_b) as fh_b:
            info_a, info_b = json.load(fh_a), json.load(fh_b)
        timedelta_a, timedelta_b = get_timedelta(info_a), get_timedelta(info_b)
        percent_different = (timedelta_a - timedelta_b) / (
            (timedelta_a + timedelta_b) / 2
        )
        if abs(percent_different) > percent_time_delta:
            print(
                'Actual is {0:.2f}% {1} than Expected.'.format(
                    abs(percent_different) * 100,
                    'faster' if percent_different < 0 else 'slower',
                ),

            )


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('actual', help='Directory of text files to compare (labeled "Actual").')
    parser.add_argument('--expected', help='Other directory of text files to compare (labeled "Expected").')
    parser.add_argument(
        '--expected_prefix',
        default='expected_results',
        help='Directory to prepend for expected results when `expected` is not'
        ' provided. The default is `expected_results`.',
    )
    parser.add_argument(
        '--percent_time_delta',
        default=0.1,
        type=float,
        help='The threshold expressed in a decimal with which to warn that the'
        ' running time is different. For example, if 0.1 is provided then a'
        ' warning will be shown only when the running time is +/- 10%% different'
        ' than what is expected. The default is `0.1`.',
    )
    parser.add_argument(
        '--time_info_file',
        default='CRISPResso2_info.json',
        help='The name of the JSON file that contains the time information.'
        ' It is assumed that the file is in the root of `actual` and `expected`.'
        'The default is `CRISPResso2_info.json`.',
    )
    parser.add_argument(
        '--skip_html',
        default=False,
        action="store_true",
        help='Whether to skip comparisons of html files.'
    )
    parser.add_argument(
        '--diff-plots',
        default=False,
        action="store_true",
        help='Compare plots between actual and expected results.'
        ' PDFs are diffed as text (drawing streams); PNGs are compared'
        ' using approximate RMSE (tolerant of rendering differences).',
    )
    parser.add_argument(
        '--image_threshold',
        default=DEFAULT_IMAGE_THRESHOLD,
        type=float,
        help='RMSE threshold (0-1) for PNG image comparison. Images with'
        ' RMSE above this are flagged as significantly different.'
        ' The default is `{0}`.'.format(DEFAULT_IMAGE_THRESHOLD),
    )

    args = parser.parse_args()

    if args.expected is None:
        expected = join(args.expected_prefix, args.actual)
    else:
        expected = args.expected

    diff_running_times(
        args.actual, expected, args.percent_time_delta, args.time_info_file,
    )
    diff_suffixes = ('.txt', '.html', '.sam', '.vcf')
    if args.skip_html:
        diff_suffixes = ('.txt', '.sam', '.vcf')
    if args.diff_plots:
        diff_suffixes = diff_suffixes + PDF_SUFFIXES

    has_diff = diff_dir(args.actual, expected, suffixes=diff_suffixes)

    if args.diff_plots:
        has_image_diff = diff_dir_images(
            args.actual, expected, threshold=args.image_threshold,
        )
        has_diff |= has_image_diff

    if has_diff:
        sys.exit(1)
    sys.exit(0)
