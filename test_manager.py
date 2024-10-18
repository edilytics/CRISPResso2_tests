import argparse
import glob
import json
import os
from shutil import copyfile, copytree

from diff import diff_dir
from noxfile import COMMON_ARGS


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


def add_test_to_yaml(command, name, directory):
    with open('test_config.yml', 'a') as fh:
        fh.write(f'\n  {name}:\n')
        fh.write(f'  output: {directory}\n')
        fh.write('  cmd: |\n')
        fh.write(f'      {command}\n')


def add_test(args):
    crispresso2_info = get_crispresso2_info(args.directory)
    test_command = crispresso2_info['running_info']['command_used']
    run_name = crispresso2_info['running_info']['args']['value']['name']
    input_file_keys = ['fastq_r1', 'r1', 'fastq_r2', 'r2', 'bam_input', 'batch_settings', 'amplicons_file']

    command_parts = test_command.split(' ')
    command_parts[0] = os.path.basename(command_parts[0])
    test_command = ' '.join(command_parts)

    print('Adding a new test case!\n')
    print('Test command: {0}'.format(test_command))
    command_input = input('Is this correct? [y/n]: ')
    if command_input.lower() == 'n':
        test_command = input('Enter the correct test command: ')

    print('\nRemoving parameters that are automatically added...')
    for common_arg in COMMON_ARGS:
        try:
            command_parts.remove(common_arg)
            print(f'Removed {common_arg}')
        except ValueError:
            pass
    for name_parameter in ['-n', '--name']:
        try:
            name_index = command_parts.index('-n')
            run_name = command_parts[name_index + 1]
            command_parts.pop(name_index + 1)
            command_parts.pop(name_index)
            print(f'Removed {name_parameter} {run_name}')
        except ValueError:
            pass
    test_command = ' '.join(command_parts)
    print(f'Updated test command: {test_command}')

    if run_name:
        print('\nRun name: {0}'.format(run_name))
        print('This should be short and descriptive of the test case. No spaces, and use - to separate words. Do not append with `-test`.')
        print('This will be used as a short keyword to run the test.')
        run_name_input = input('Is this correct? [y/n]: ')
        if run_name_input.lower() == 'n':
            run_name = input('Enter the correct run name: ')
    else:
        run_name = input('Enter the run name: ')

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

    print('\nAdding test to test_config.yaml...')
    add_test_to_yaml(test_command, run_name, directory_name, input_files)

    print('\nAdding actual files to .gitignore...')
    with open('.gitignore', 'a') as fh:
        fh.write('\ncli_integration_tests/{0}*\n'.format(directory_name))

    print('\nYou can now run the command with `nox {0}`'.format(run_name))
    print('And test with the command `nox {0} -- test`'.format(run_name))


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
