import os

import nox
import yaml


SESSION_ARGS = {
    'venv_backend': 'none',
}

with open('test_config.yml', 'r') as fh:
    TEST_CONFIG = yaml.safe_load(fh)

PARAMETERS = [
    'python, numpy',
    [
        (python, numpy)
        for python in TEST_CONFIG['package_versions']['python']
        for numpy in TEST_CONFIG['package_versions']['numpy']
        if not ((python == '3.13' and numpy == '1.26.4') or
           (python == '3.13' and numpy == '2.0.0'))
    ],
]
COMMON_ARGS = ['--place_report_in_output_folder', '--halt_on_plot_fail', '--debug']
CRISPRESSO2_DIR = '../CRISPResso2'


@nox.session(venv_backend='conda', reuse_venv=True)
@nox.parametrize(*PARAMETERS)
def conda_env(session, python, numpy):
    conda_list = session.run('conda', 'list', silent=True)
    if 'samtools' in conda_list and 'force' not in session.posargs:
        session.warn('samtools is installed, skipping installation of all dependencies.')
        return
    session.conda_install(
        'bowtie2',
        'samtools',
        'fastp',
        f'numpy={numpy}',
        'pandas',
        'cython',
        'jinja2',
        'tbb=2020.2',
        'pyparsing=2.3.1',
        f'python={python}',
        'scipy',
        'matplotlib',
        channel=['conda-forge', 'bioconda'],
    )


def create_cli_integration_test(test_name, test_output, cmd):
    @nox.session(**SESSION_ARGS, name=test_name)
    @nox.parametrize(*PARAMETERS)
    def cli_integration_test(session, python, numpy):
        # set the correct conda environment
        session._runner.venv = nox.virtualenv.CondaEnv(
            location=os.path.join(os.getcwd(), f'.nox/conda_env-python-{python.replace(".", "-")}-numpy-{numpy.replace(".", "-")}'),
            reuse_existing=True,
            conda_cmd='conda',
        )
        # install CRISPResso2
        with session.chdir(CRISPRESSO2_DIR):
            session.install('.')
        # run the command
        cmd_silent = 'print' not in session.posargs
        with session.chdir('cli_integration_tests'):
            cmd_out = session.run(*cmd, silent=cmd_silent)
        # check for positional arguments
        if 'test' in session.posargs:
            try:
                session.run('python', 'diff.py', f'cli_integration_tests/{test_output}', '--expected', f'cli_integration_tests/expected_results/{test_output}', silent=True)
            except nox.command.CommandFailed as e:
                print(cmd_out)
                raise e
        if 'update' in session.posargs:
            session.run('python', 'test_manager.py', 'update', f'cli_integration_tests/{test_output}', f'cli_integration_tests/expected_results/{test_output}')

    return cli_integration_test


def build_cmd(name, cmd):
    cmd = cmd.strip().split(' ')
    cmd.extend(['-n', name, *COMMON_ARGS])
    return cmd


for test_name, test_config in TEST_CONFIG['cli_integration_tests'].items():
    globals()[test_name] = create_cli_integration_test(
        test_name,
        test_config['output'],
        build_cmd(test_name, test_config['cmd']),
    )
