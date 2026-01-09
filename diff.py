import argparse
import json
import os
import re
import sys
import subprocess
import tempfile
from datetime import timedelta
from difflib import unified_diff
from pathlib import Path
from os.path import basename, join, dirname
from shutil import copyfile


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


def diff_dir(actual, expected, suffixes=('.txt', '.html', '.sam'), prompt_to_update=False):
    files_actual = {f.relative_to(actual): f for f in Path(actual).glob('**/*') if f.suffix in suffixes}
    files_expected = {f.relative_to(expected): f for f in Path(expected).glob('**/*') if f.suffix in suffixes}
    diff_exists = False
    for file_basename_actual, file_path_actual in files_actual.items():
        if basename(file_basename_actual) in IGNORE_FILES:
            continue
        if file_basename_actual in files_expected:
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

    args = parser.parse_args()

    if args.expected is None:
        expected = join(args.expected_prefix, args.actual)
    else:
        expected = args.expected

    diff_running_times(
        args.actual, expected, args.percent_time_delta, args.time_info_file,
    )
    diff_suffixes=('.txt', '.html', '.sam')
    if args.skip_html:
        diff_suffixes = ('.txt', '.sam')

    if diff_dir(args.actual, expected, suffixes=diff_suffixes):
        sys.exit(1)
    sys.exit(0)
