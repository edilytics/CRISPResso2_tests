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
    from PIL import Image
    import numpy as np
    IMAGE_DEPS_AVAILABLE = True
except ImportError:
    IMAGE_DEPS_AVAILABLE = False


FLOAT_REGEXP = re.compile(r'\d+\.\d+')
DATETIME_REGEXP = re.compile(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}')
COMMAND_HTML_REGEXP = re.compile(r'<p>(<strong>)?Command used:.*')
COMMAND_LOG_REGEXP = re.compile(r'[\S]*/CRISPResso.*')
OUTPUT_REGEXP = re.compile(r'[\S]*/CRISPResso2[\S]*/cli_integration_tests/CRISPResso[\S]*')
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
WARNING_FILE_REGEXP = re.compile(r'CRISPResso2(Aggregate|Batch|Pooled|WGS|Compare)?_report.html')

TEXT_SUFFIXES = ('.txt', '.html', '.sam', '.vcf')
PDF_SUFFIXES = ('.pdf',)

# PDF stream detection patterns
PDF_STREAM_REGEXP = re.compile(rb'stream\r?\n(.*?)endstream', re.DOTALL)
PDF_DRAWING_REGEXP = re.compile(r'\b[mlhfcre]\b|BT|ET|Tj|TJ')
PDF_FONT_KEYWORDS = ('GDEF', 'cmap', 'CIDInit')

# PNG image comparison constants
IMAGE_SUFFIXES = ('.png',)
DEFAULT_IMAGE_THRESHOLD = 0.10  # RMSE threshold (0-1 scale); 0.10 = 10%
IMAGE_THUMBNAIL_SIZE = (256, 256)  # Downscale target for comparison


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
    line = OUTPUT_REGEXP.sub('CRISPResso2_tests/cli_integration_tests/CRISPResso', line)
    line = SAM_HEADER_BOWTIE_VERSION_REGEXP.sub(r'@PG\tID:bowtie2\tPN:bowtie2\tVN:2.5.4\tCL:bowtie2-align-s <parameters>', line)
    line = SAM_HEADER_REGEXP.sub(r'@HD\tVN:1.0\tSO:unsorted', line)
    return line


def diff(file_a, file_b):
    with open(file_a) as fh_a, open(file_b) as fh_b:
        lines_a = [substitute_line(line).strip() + '\n' for line in fh_a]
        lines_b = [substitute_line(line).strip() + '\n' for line in fh_b]
        return list(unified_diff(lines_a, lines_b))


def extract_pdf_drawing_streams(path):
    """Extract drawing/content streams from a matplotlib-generated PDF.

    Decompresses FlateDecode streams and returns only the drawing
    command streams (coordinates, colors, text), skipping embedded
    fonts and character maps.

    Parameters
    ----------
    path : str or Path
        Path to the PDF file.

    Returns
    -------
    str
        Concatenated drawing stream text.
    """
    with open(path, 'rb') as fh:
        data = fh.read()
    drawings = []
    for m in PDF_STREAM_REGEXP.finditer(data):
        try:
            decompressed = zlib.decompress(m.group(1))
            text = decompressed.decode('latin-1')
        except Exception:
            continue
        # Keep only streams with drawing commands, skip font data
        if PDF_DRAWING_REGEXP.search(text[:500]) and \
                not any(kw in text for kw in PDF_FONT_KEYWORDS):
            drawings.append(text)
    return '\n'.join(drawings)


def diff_pdf(file_a, file_b):
    """Diff two PDF files by comparing their drawing streams.

    Extracts the drawing/content streams (skipping fonts and metadata),
    normalizes floats, and returns a unified diff.

    Parameters
    ----------
    file_a : str or Path
        Path to the first PDF (actual).
    file_b : str or Path
        Path to the second PDF (expected).

    Returns
    -------
    list
        Unified diff lines, empty if files are identical.
    """
    text_a = extract_pdf_drawing_streams(file_a)
    text_b = extract_pdf_drawing_streams(file_b)
    lines_a = [substitute_line(line).strip() + '\n' for line in text_a.splitlines()]
    lines_b = [substitute_line(line).strip() + '\n' for line in text_b.splitlines()]
    return list(unified_diff(lines_a, lines_b))


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

    # Convert to grayscale
    img_a = img_a.convert('L')
    img_b = img_b.convert('L')

    # Downscale using thumbnail (preserves aspect ratio)
    img_a.thumbnail(IMAGE_THUMBNAIL_SIZE, Image.LANCZOS)
    img_b.thumbnail(IMAGE_THUMBNAIL_SIZE, Image.LANCZOS)

    # Resize to identical dimensions (thumbnail may produce slightly
    # different sizes due to aspect ratio preservation)
    common_size = (
        min(img_a.width, img_b.width),
        min(img_a.height, img_b.height),
    )
    if img_a.size != common_size:
        img_a = img_a.resize(common_size, Image.LANCZOS)
    if img_b.size != common_size:
        img_b = img_b.resize(common_size, Image.LANCZOS)

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
    copyfile(actual, expected)


def remove_file(file_path):
    print('Do you want to remove this file?')
    remove_input = input('[y/n]: ')
    if remove_input.lower() == 'n':
        return
    os.remove(file_path)


def diff_dir(actual, expected, suffixes=TEXT_SUFFIXES, prompt_to_update=False):
    files_actual = {f.relative_to(actual): f for f in Path(actual).glob('**/*') if f.suffix in suffixes}
    files_expected = {f.relative_to(expected): f for f in Path(expected).glob('**/*') if f.suffix in suffixes}
    diff_exists = False
    for file_basename_actual, file_path_actual in files_actual.items():
        if basename(file_basename_actual) in IGNORE_FILES:
            continue
        if file_basename_actual in files_expected:
            if file_path_actual.suffix in PDF_SUFFIXES:
                diff_results = diff_pdf(file_path_actual, files_expected[file_basename_actual])
            else:
                diff_results = diff(file_path_actual, files_expected[file_basename_actual])
            if diff_results:
                print('Comparing {0} to {1}'.format(
                    file_path_actual, files_expected[file_basename_actual],
                ))
                print_diff(diff_results)
                if not WARNING_FILE_REGEXP.search(str(file_path_actual)):
                    diff_exists |= True
                if prompt_to_update:
                    update_file(file_path_actual, files_expected[file_basename_actual])
        else:
            print('New file in Actual ({0}) not found in Expected ({1})'.format(file_basename_actual, expected))
            if not WARNING_FILE_REGEXP.search(str(file_path_actual)):
                diff_exists |= True
            if prompt_to_update:
                update_file(file_path_actual, join(expected, file_basename_actual))

    for file_basename_expected in files_expected.keys():
        if file_basename_expected not in files_actual:
            print('Missing file {0} from Actual ({1})'.format(file_basename_expected, actual))
            if not WARNING_FILE_REGEXP.search(str(file_path_actual)):
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
        '--diff_plots',
        default=False,
        action="store_true",
        help='Whether to compare plot PDFs between actual and expected results.'
        ' Extracts drawing streams from PDFs and diffs them as text.',
    )
    parser.add_argument(
        '--diff_images',
        default=False,
        action="store_true",
        help='Whether to compare plot images (PNG files) between actual and'
        ' expected results using pixel RMSE. Useful as a fallback when'
        ' matplotlib versions change and PDF streams differ too much.'
        ' Requires Pillow and NumPy.',
    )
    parser.add_argument(
        '--image_threshold',
        default=DEFAULT_IMAGE_THRESHOLD,
        type=float,
        help='RMSE threshold (0-1) for image comparison. Images with RMSE above'
        ' this are flagged as significantly different. Lower values are stricter.'
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

    if args.diff_images:
        has_image_diff = diff_dir_images(
            args.actual, expected, threshold=args.image_threshold,
        )
        has_diff |= has_image_diff

    if has_diff:
        sys.exit(1)
    sys.exit(0)
