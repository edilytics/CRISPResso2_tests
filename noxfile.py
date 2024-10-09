import nox
import yaml


SESSION_ARGS = {
    'venv_backend': 'none',
}
COMMON_ARGS = ['--place_report_in_output_folder', '--halt_on_plot_fail', '--debug']
CRISPRESSO2_DIR = '../CRISPResso2'
CONDA_ENVIRONMENTS = {}


@nox.session(venv_backend='conda', reuse_venv=True)
@nox.parametrize('numpy', ['1.26.4', '2.0.0', '2.1.1'])
def conda_env(session, numpy):
    CONDA_ENVIRONMENTS[('numpy', numpy)] = session._runner.venv
    conda_list = session.run('conda', 'list', silent=True)
    if 'samtools' in conda_list:
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
        'scipy',
        'matplotlib',
        channel=['conda-forge', 'bioconda'],
    )


def create_cli_integration_test(test_name, cmd):
    @nox.session(**SESSION_ARGS, name=test_name)
    @nox.parametrize('numpy', ['1.26.4', '2.0.0', '2.1.1'])
    def cli_integration_test(session, numpy):
        # set the correct conda environment
        session._runner.venv = CONDA_ENVIRONMENTS[('numpy', numpy)]
        # install CRISPResso2
        with session.chdir(CRISPRESSO2_DIR):
            session.install('.')
        # run the test
        with session.chdir('cli_integration_tests'):
            session.run(*cmd)

    return cli_integration_test


def build_cmd(name, cmd):
    cmd = cmd.strip().split(' ')
    cmd.extend(['-n', name, *COMMON_ARGS])
    return cmd


with open('test_config.yml', 'r') as fh:
    TEST_CONFIG = yaml.safe_load(fh)
    for test_name, test_config in TEST_CONFIG['cli_integration_tests'].items():
        globals()[test_name] = create_cli_integration_test(
            test_name, build_cmd(test_name, test_config['cmd']),
        )
