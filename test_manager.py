import argparse
import glob
import json
import os
import re
from shutil import copyfile, copytree

from diff import diff_dir


COMMON_FLAGS = {'--place_report_in_output_folder', '--halt_on_plot_fail', '--debug'}

TOOL_TO_MARK = {
    'CRISPResso': 'crispresso',
    'CRISPRessoBatch': 'batch',
    'CRISPRessoPooled': 'pooled',
    'CRISPRessoWGS': 'wgs',
    'CRISPRessoCompare': 'compare',
    'CRISPRessoAggregate': 'aggregate',
}


def get_crispresso2_info_path(result_dir):
    potential_paths = glob.glob(os.path.join(result_dir, 'CRISPResso2*_info.json'))
    if len(potential_paths) > 1:
        raise Exception('More than one CRISPResso2 info file found in {0}'.format(result_dir))
    elif len(potential_paths) == 0:
        raise Exception('No CRISPResso2 info file found in {0}'.format(result_dir))
    return potential_paths[0]


def get_crispresso2_info(result_directory):
    crispresso2_info = {}
    with open(get_crispresso2_info_path(result_directory)) as fh:
        crispresso2_info = json.load(fh)
    return crispresso2_info


def parse_command_to_list(command):
    """Parse a command string into one-parameter-per-element list.

    Returns a list where each element is a single flag (possibly with its
    value), with COMMON_FLAGS stripped out.  The first element is the bare
    tool name.
    """
    tokens = command.split()
    # First token is the tool (may be a full path)
    tool = os.path.basename(tokens[0])
    parts = [tool]
    i = 1
    while i < len(tokens):
        token = tokens[i]
        if token in COMMON_FLAGS:
            i += 1
            continue
        if token.startswith('-'):
            # If the next token exists and is NOT a flag, it's the value
            if i + 1 < len(tokens) and not tokens[i + 1].startswith('-'):
                parts.append('{0} {1}'.format(token, tokens[i + 1]))
                i += 2
            else:
                parts.append(token)
                i += 1
        else:
            # Positional arg (rare) – keep as-is
            parts.append(token)
            i += 1
    return parts


def add_test_to_test_cli(cmd_parts, test_id, output_dir, mark):
    """Append a CLITestCase entry to the TESTS list in test_cli.py."""
    cmd_lines = ',\n            '.join(repr(p) for p in cmd_parts)
    marks_str = '[{0!r}]'.format(mark) if mark else '[]'
    entry = (
        "    CLITestCase(\n"
        "        id={id!r},\n"
        "        cmd=[\n"
        "            {cmd},\n"
        "        ],\n"
        "        output_dir={output_dir!r},\n"
        "        marks={marks},\n"
        "    ),\n"
    ).format(id=test_id, cmd=cmd_lines, output_dir=output_dir, marks=marks_str)

    with open('test_cli.py', 'r') as fh:
        content = fh.read()

    # Insert just before the closing ] of the TESTS list.
    # The list is followed by _make_params.
    m = re.search(r'\n]\n\n+def _make_params', content)
    if not m:
        raise Exception('Could not find end of TESTS list in test_cli.py')
    insert_pos = m.start()
    content = content[:insert_pos] + '\n' + entry + content[insert_pos:]

    with open('test_cli.py', 'w') as fh:
        fh.write(content)


def add_test_to_makefile(test_id, run_name, output_dir):
    """Add a pytest-backed Make target and update all:/clean/.PHONY."""
    with open('Makefile', 'r') as fh:
        lines = fh.readlines()

    new_lines = []
    for line in lines:
        # Append run_name to the .PHONY declaration (last continuation line)
        # The .PHONY block ends at the first non-continuation line.
        # We append to the last `\`-continued line.
        if line.startswith('all:'):
            line = line.rstrip('\n') + ' ' + run_name + '\n'
        new_lines.append(line)

    # Add to clean_cli_integration: find the last `cli_integration_tests/...* \`
    # line and insert after it.
    clean_insert_idx = None
    for i, line in enumerate(new_lines):
        if line.startswith('cli_integration_tests/') and line.rstrip().endswith('* \\'):
            clean_insert_idx = i
    if clean_insert_idx is not None:
        new_lines.insert(
            clean_insert_idx + 1,
            'cli_integration_tests/{0}* \\\n'.format(output_dir),
        )

    # Add the Make target at the end of the pytest-backed section
    # (just before "# ── Non-pytest targets")
    target_block = (
        "\n{name}: .install_sentinel\n"
        "\t$(call PYTEST_RUN,test_crispresso_cli[{test_id}],{output_dir})\n"
    ).format(name=run_name, test_id=test_id, output_dir=output_dir)

    insert_idx = None
    for i, line in enumerate(new_lines):
        if line.startswith('# ── Non-pytest targets'):
            insert_idx = i
            break
    if insert_idx is not None:
        new_lines.insert(insert_idx, target_block)
    else:
        # Fallback: append at end of file
        new_lines.append(target_block)

    with open('Makefile', 'w') as fh:
        fh.writelines(new_lines)


def add_test(args):
    crispresso2_info = get_crispresso2_info(args.directory)
    test_command = crispresso2_info['running_info']['command_used']
    run_name = crispresso2_info['running_info']['args']['value']['name']
    input_file_keys = ['fastq_r1', 'r1', 'fastq_r2', 'r2', 'bam_input', 'batch_settings', 'amplicons_file']

    # Normalise tool path to bare name
    command_parts = test_command.split(' ')
    command_parts[0] = os.path.basename(command_parts[0])
    test_command = ' '.join(command_parts)
    tool_name = command_parts[0]

    print('Adding a new test case!\n')
    print('Test command: {0}'.format(test_command))
    command_input = input('Is this correct? [y/n]: ')
    if command_input.lower() == 'n':
        test_command = input('Enter the correct test command: ')
        tool_name = test_command.split()[0]

    if run_name:
        print('\nRun name: {0}'.format(run_name))
        print('This should be short and descriptive of the test case. No spaces, and use - to separate words. Do not append with `-test`.')
        print('This will be used as a short keyword to run the test.')
        run_name_input = input('Is this correct? [y/n]: ')
        if run_name_input.lower() == 'n':
            run_name = input('Enter the correct run name: ')
    else:
        run_name = input('Enter the run name: ')

    # Derive the pytest test id (underscores, no hyphens)
    test_id = run_name.replace('-', '_')

    print('Copying files to cli_integration_tests/inputs directory...')
    input_files = [
        crispresso2_info['running_info']['args']['value'][input_file_key]
        for input_file_key in input_file_keys
        if input_file_key in crispresso2_info['running_info']['args']['value']
    ]
    # check for more input files found in batch file
    if 'batch_settings' in crispresso2_info['running_info']['args']['value']:
        try:
            with open(crispresso2_info['running_info']['args']['value']['batch_settings']) as fh:
                column_headers = fh.readline().strip().split('\t')
                column_indexes_to_copy = []
                for column_index, column_header in enumerate(column_headers):
                    if column_header in input_file_keys:
                        column_indexes_to_copy += [column_index]
                for line in fh:
                    columns = line.strip().split('\t')
                    input_files.extend(columns[column_index] for column_index in column_indexes_to_copy)
        except:
            print('Could not find batch file {0}, please copy the batch file and the files found therein to cli_integration_tests/inputs manually!'.format(crispresso2_info['running_info']['args']['value']['batch_settings']))

    for input_file in input_files:
        if input_file:
            try:
                copyfile(input_file, os.path.join('cli_integration_tests/inputs', os.path.basename(input_file)))
                print('Copied {0} to cli_integration_tests/inputs/'.format(input_file))
            except:
                print('Could not copy {0} to cli_integration_tests/inputs, please manually copy!'.format(input_file))
    print('If there are other input files, please copy them to cli_integration_tests/inputs manually!')

    directory_name = os.path.basename(os.path.normpath(args.directory))
    print('\nAdding results to cli_integration_tests/expected_results/{0}'.format(directory_name))
    try:
        copytree(args.directory, os.path.join('cli_integration_tests/expected_results', directory_name), dirs_exist_ok=True)
    except:
        print('Could not copy {0} to cli_integration_tests/expected_results, please manually copy!'.format(args.directory))
    try:
        copyfile('{0}.html'.format(args.directory), os.path.join('cli_integration_tests/expected_results', '{0}.html'.format(directory_name)))
    except:
        print('Could not copy {0}.html to cli_integration_tests/expected_results, please manually copy!'.format(args.directory))

    # Parse command into one-param-per-element list (common flags stripped)
    cmd_parts = parse_command_to_list(test_command)
    mark = TOOL_TO_MARK.get(tool_name, '')

    print('\nAdding test to test_cli.py...')
    add_test_to_test_cli(cmd_parts, test_id, directory_name, mark)

    print('Adding target to Makefile...')
    add_test_to_makefile(test_id, run_name, directory_name)

    print('\nAdding actual files to .gitignore...')
    with open('.gitignore', 'a') as fh:
        fh.write('\ncli_integration_tests/{0}*\n'.format(directory_name))

    print('\nYou can now run the command with `make {0}`'.format(run_name))
    print('And test with the command `make {0} test`'.format(run_name))


def update_test(args):
    if not diff_dir(args.actual, args.expected, prompt_to_update=True):
        print('No changes to update!')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.set_defaults(func=lambda _: parser.print_help())

    subparsers = parser.add_subparsers()
    parser_add = subparsers.add_parser('add', help='Add a new test')
    parser_add.set_defaults(func=add_test)
    parser_add.add_argument('directory', help='Path to the result directory of the test to add')

    parser_update = subparsers.add_parser('update', help='Update an existing test')
    parser_update.set_defaults(func=update_test)
    parser_update.add_argument('actual', help='Path to the result directory of the test to update')
    parser_update.add_argument('expected', help='Path to the expected result directory of the test to update')

    args = parser.parse_args()
    args.func(args)
