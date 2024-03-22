import argparse
import glob
import json
import os
from shutil import copyfile, copytree

from diff import diff_dir


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


def add_test_to_makefile(command, name, directory, input_files):
    with open('Makefile', 'r') as fh:
        makefile_lines = fh.readlines()

    with open('Makefile', 'w') as fh:
        for line in makefile_lines:
            if line.startswith('all:'):
                fh.write('{0} {1}\n'.format(line.strip(), name))
            elif line.startswith('cli_integration_tests/CRISPRessoBatch_on_large_batch* \\'):
                fh.write(line)
                fh.write('cli_integration_tests/{0}* \\\n'.format(directory))
            elif line.startswith('CRISPRessoWGS_on_Both.Cas9.fastq.smallGenome \\'):
                fh.write(line)
                fh.write('{0} \\\n'.format(directory))
            else:
                fh.write(line)
        fh.write('\n.PHONY: {name}\n{name}: cli_integration_tests/{directory}\n'.format(name=name, directory=directory))
        fh.write('\ncli_integration_tests/{directory}: install {input_files}\n'.format(
            directory=directory,
            input_files=' '.join('cli_integration_tests/inputs/{0}'.format(os.path.basename(i)) for i in input_files)
        ))
        fh.write('\tcd cli_integration_tests && cmd="{command}"; $(RUN)'.format(command=command))


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

    print('\nAdding test to Makefile...')
    add_test_to_makefile(test_command, run_name, directory_name, input_files)

    print('\nAdding actual files to .gitignore...')
    with open('.gitignore', 'a') as fh:
        fh.write('\ncli_integration_tests/{0}*\n'.format(directory_name))

    print('\nYou can now run the command with `make {0}`'.format(run_name))
    print('And test with the command `make {0}-test`'.format(run_name))


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
