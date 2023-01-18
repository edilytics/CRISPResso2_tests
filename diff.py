import argparse
import json
import re
import sys
from datetime import timedelta
from difflib import unified_diff
from pathlib import Path
from os.path import basename, join


FLOAT_REGEXP = re.compile(r'\d+\.\d+')
IGNORE_FILES = frozenset([
    'CRISPResso_RUNNING_LOG.txt',
    'CRISPRessoBatch_RUNNING_LOG.txt',
    'CRISPRessoPooled_RUNNING_LOG.txt',
    'CRISPRessoWGS_RUNNING_LOG.txt',
    'CRISPRessoCompare_RUNNING_LOG.txt',
])


def round_float(f):
    return str(round(float(f.group(0)), 3))


def diff(file_a, file_b):
    with open(file_a) as fh_a, open(file_b) as fh_b:
        lines_a = [FLOAT_REGEXP.sub(round_float, line) for line in fh_a]
        lines_b = [FLOAT_REGEXP.sub(round_float, line) for line in fh_b]
        return list(unified_diff(lines_a, lines_b))


def diff_dir(actual, expected):
    files_actual = {basename(f): f for f in Path(actual).rglob('*.txt')}
    files_expected = {basename(f): f for f in Path(expected).rglob('*.txt')}
    diff_exists = False
    for file_basename_actual, file_path_actual in files_actual.items():
        if file_basename_actual in IGNORE_FILES:
            continue
        if file_basename_actual in files_expected:
            diff_results = diff(file_path_actual, files_expected[file_basename_actual])
            if diff_results:
                print('Comparing {0} to {1}'.format(
                    file_path_actual, files_expected[file_basename_actual],
                ))
                for result in diff_results:
                    print(result, end='')
                diff_exists |= True
        else:
            print('New file in Actual ({0}) not found in Expected ({1})'.format(file_basename_actual, expected))
            diff_exists |= True

    for file_basename_expected in files_expected.keys():
        if file_basename_expected not in files_actual:
            print('Missing file {0} from Actual ({1})'.format(file_basename_expected, actual))
            diff_exists |= True

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
    parser.add_argument('actual', help='Directory of text files to compare (labelled "Actual").')
    parser.add_argument('--expected', help='Other directory of text files to compare (labelled "Expected").')
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

    args = parser.parse_args()

    if args.expected is None:
        expected = join(args.expected_prefix, args.actual)
    else:
        expected = args.expected

    diff_running_times(
        args.actual, expected, args.percent_time_delta, args.time_info_file,
    )
    if diff_dir(args.actual, expected):
        sys.exit(1)
    sys.exit(0)
