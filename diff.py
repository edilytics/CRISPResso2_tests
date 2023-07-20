import argparse
import json
import os
import re
import sys
import subprocess
from datetime import timedelta
from difflib import unified_diff
from pathlib import Path
from os.path import basename, join, dirname


FLOAT_REGEXP = re.compile(r'\d+\.\d+')
IGNORE_FILES = frozenset([
    'CRISPResso_RUNNING_LOG.txt',
    'CRISPRessoBatch_RUNNING_LOG.txt',
    'CRISPRessoPooled_RUNNING_LOG.txt',
    'CRISPRessoWGS_RUNNING_LOG.txt',
    'CRISPRessoCompare_RUNNING_LOG.txt',
])


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
    return str(round(float(f.group(0)), 3))


def diff(file_a, file_b):
    with open(file_a) as fh_a, open(file_b) as fh_b:
        lines_a = [FLOAT_REGEXP.sub(round_float, line) for line in fh_a]
        lines_b = [FLOAT_REGEXP.sub(round_float, line) for line in fh_b]
        return list(unified_diff(lines_a, lines_b))
    

def find_dir_matches(file_path_a, files_b, matches):
    dir_a = basename(dirname(file_path_a))
    for ind in matches:
        dir_b = basename(dirname(files_b[ind]))
        if dir_a == dir_b:
            return ind
    return -1
        


def diff_dir(dir_a, dir_b):
    files_a = [f for f in Path(dir_a).rglob('*.txt')]
    file_basenames_a = [basename(f) for f in files_a]
    files_b = [f for f in Path(dir_b).rglob('*.txt')]
    file_basenames_b = [basename(f) for f in files_b]
    diff_exists = False
    for file_path_a in files_a:
        file_basename_a = basename(file_path_a)
        if file_basename_a in IGNORE_FILES:
            continue
        matches = [ind for ind, f in enumerate(file_basenames_b) if f == file_basename_a]
        if len(matches) == 1:
            diff_results = diff(file_path_a, files_b[file_basenames_b.index(file_basename_a)])
            if diff_results:
                print('Comparing {0} to {1}'.format(
                    file_path_a, files_b[file_basenames_b.index(file_basename_a)],
                ))
                for result in diff_results:
                    print(result, end='')
                diff_exists |= True
        elif len(matches) > 1:
            match_dir = find_dir_matches(file_path_a, files_b, matches)
            if match_dir == -1:
                print('{0} is not in {1}'.format(file_basename_a, dir_b))
                diff_exists |= True
            diff_results = diff(file_path_a, files_b[match_dir])
            if diff_results:
                print('Comparing {0} to {1}'.format(
                    file_path_a, files_b[match_dir],
                ))

                if YDIFF_INSTALLED:
                    read, write = os.pipe()
                    os.write(write, ''.join(diff_results).encode('utf-8'))
                    os.close(write)

                    subprocess.check_call('ydiff -s -w 0 --wrap', stdin=read, shell=True)
                    os.close(read)
                else:
                    for line in diff_results:
                        print(line, end='')
                diff_exists |= True
        else:
            print('{0} is not in {1}'.format(file_basename_a, dir_b))
            diff_exists |= True

    for file_basename_b in file_basenames_b:
        if file_basename_b not in file_basenames_a:
            print('{0} is not in {1}'.format(file_basename_b, dir_a))
            diff_exists |= True

    return diff_exists


def diff_running_times(
    dir_a,
    dir_b,
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

    path_a, path_b = Path(dir_a) / info_file, Path(dir_b) / info_file
    if path_a.exists() and path_b.exists():
        with open(path_a) as fh_a, open(path_b) as fh_b:
            info_a, info_b = json.load(fh_a), json.load(fh_b)
        timedelta_a, timedelta_b = get_timedelta(info_a), get_timedelta(info_b)
        percent_different = (timedelta_a - timedelta_b) / (
            (timedelta_a + timedelta_b) / 2
        )
        if abs(percent_different) > percent_time_delta:
            print(
                'Directory A is {0:.2f}% {1} than directory B.'.format(
                    abs(percent_different) * 100,
                    'faster' if percent_different < 0 else 'slower',
                ),

            )


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('dir_a', help='Directory of text files to compare.')
    parser.add_argument('--dir_b', help='Other directory of text files to compare.')
    parser.add_argument(
        '--expected_prefix',
        default='expected_results',
        help='Directory to prepend for expected results when `dir_b` is not'
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
        ' It is assumed that the file is in the root of `dir_a` and `dir_b`.'
        'The default is `CRISPResso2_info.json`.',
    )

    args = parser.parse_args()

    if args.dir_b is None:
        dir_b = join(args.expected_prefix, args.dir_a)
    else:
        dir_b = args.dir_b

    diff_running_times(
        args.dir_a, dir_b, args.percent_time_delta, args.time_info_file,
    )
    if diff_dir(args.dir_a, dir_b):
        sys.exit(1)
    sys.exit(0)
