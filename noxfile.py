import hashlib
import os
from pathlib import Path


import nox
import yaml


SESSION_ARGS = {
    'venv_backend': 'none',
}

with open('test_config.yml', 'r') as fh:
    TEST_CONFIG = yaml.safe_load(fh)

PARAMETERS = [
    'python, numpy, pandas',
    [
        (python, numpy, pandas)
        for python in TEST_CONFIG['package_versions']['python']
        for numpy in TEST_CONFIG['package_versions']['numpy']
        for pandas in TEST_CONFIG['package_versions']['pandas']
        if not ((python == '3.13' and numpy == '1.26.4') or
           (python == '3.13' and numpy == '2.0.0'))
    ],
]
COMMON_ARGS = ['--place_report_in_output_folder', '--halt_on_plot_fail', '--debug']
CRISPRESSO2_DIR = os.getenv('CRISPRESSO2_DIR', '../CRISPResso2')


def update_hash_from_dir(directory, current_hash):
    for path in sorted(Path(directory).iterdir(), key=lambda p: str(p).lower()):
        current_hash.update(path.name.encode())
        if path.is_file():
            with open(path, 'rb') as fh:
                current_hash.update(fh.read())
        elif path.is_dir():
            current_hash = update_hash_from_dir(path, current_hash)
    return current_hash


def hash_from_dir(directory):
    """Return the hash of a directory."""
    return update_hash_from_dir(directory, hashlib.md5()).hexdigest()


class Cache:
    """Simple cache to avoid re-installing CRISPResso2 in the same conda environment.

    The cache is stored in memory as `self.cache` with the conda environment name
    as the key and the hash of the CRISPResso2 directory as the value. The cache
    is also saved to disk as a tab-separated file with the same format.
    """
    def __init__(self, path='.nox/crispresso2_install_cache.tsv'):
        self.path = path
        self.cache = {}
        self._load_cache()

    def add(self, conda_env_name, dir_hash):
        """Add a new conda environment name and directory hash to the cache."""
        self.cache[conda_env_name] = dir_hash
        self.save()

    def is_hit(self, conda_env_name, dir_hash):
        """If the hash of the CRISPResso2 directory matches the cache, return True."""
        return self.cache.get(conda_env_name) == dir_hash

    def _load_cache(self):
        if os.path.exists(self.path):
            with open(self.path, 'r') as fh:
                for line in fh:
                    conda_env_name, dir_hash = line.strip().split('\t')
                    self.cache[conda_env_name] = dir_hash

    def save(self):
        """Save the cache to disk."""
        with open(self.path, 'w') as fh:
            for conda_env_name, dir_hash in self.cache.items():
                fh.write(f'{conda_env_name}\t{dir_hash}\n')


CRISPRESSO2_INSTALL_CACHE = Cache()


def get_conda_env_name(python, numpy, pandas):
    return '-'.join([
        '.nox/conda_env',
        f'python-{python.replace(".", "-")}',
        f'numpy-{numpy.replace(".", "-")}',
        f'pandas-{pandas.replace(".", "-")}'
    ])


def get_conda_env(python, numpy, pandas, cmd):
    return nox.virtualenv.CondaEnv(
            location=os.path.join(os.getcwd(), get_conda_env_name(python, numpy, pandas)),
            reuse_existing=True,
            conda_cmd=cmd,
        )


@nox.session(venv_backend='conda|micromamba', reuse_venv=True)
@nox.parametrize(*PARAMETERS)
def conda_env(session, python, numpy, pandas):
    conda_list = session.run(session.venv_backend, 'list', silent=True)
    if 'samtools' in conda_list and 'force' not in session.posargs:
        session.warn('samtools is installed, skipping installation of all dependencies.')
        return
    session.conda_install(
        'bowtie2',
        'samtools',
        'fastp',
        f'numpy={numpy}',
        f'pandas={pandas}',
        'cython',
        'jinja2',
        'tbb=2020.2',
        'pip',
        'pytest',
        'pytest-cov',
        'pyparsing=2.3.1',
        f'python={python}',
        'scipy',
        'setuptools',
        'matplotlib',
        channel=['conda-forge', 'bioconda'],
    )


def create_cli_integration_test(test_name, test_output, cmd):
    @nox.session(**SESSION_ARGS, name=test_name)
    @nox.parametrize(*PARAMETERS)
    def cli_integration_test(session, python, numpy, pandas):
        session._runner.venv = get_conda_env(python, numpy, pandas, session.venv_backend)
        crispresso2_hash = hash_from_dir(CRISPRESSO2_DIR)
        conda_env_name = get_conda_env_name(python, numpy, pandas)
        if not CRISPRESSO2_INSTALL_CACHE.is_hit(conda_env_name, crispresso2_hash):
            with session.chdir(CRISPRESSO2_DIR):
                session.install('.', '--no-build-isolation')
            CRISPRESSO2_INSTALL_CACHE.add(conda_env_name, hash_from_dir(CRISPRESSO2_DIR))

        cmd_silent = 'print' not in session.posargs
        with session.chdir('cli_integration_tests'):
            cmd_out = session.run(*cmd, silent=cmd_silent)

        if 'test' in session.posargs:
            try:
                session.run('python', 'diff.py', f'cli_integration_tests/{test_output}', '--expected', f'cli_integration_tests/expected_results/{test_output}', silent=True)
            except nox.command.CommandFailed as e:
                print(cmd_out)
                raise e
        if 'update' in session.posargs:
            session.run('python', 'test_manager.py', 'update', f'cli_integration_tests/{test_output}', f'cli_integration_tests/expected_results/{test_output}')

    return cli_integration_test


@nox.session(**SESSION_ARGS)
@nox.parametrize(*PARAMETERS)
def unit_tests(session, python, numpy, pandas):
    session._runner.venv = get_conda_env(python, numpy, pandas, session.venv_backend)
    with session.chdir(CRISPRESSO2_DIR):
        session.install('.', '--no-build-isolation')
        session.run('pytest', 'tests', '--cov=CRISPResso2')


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


@nox.session(default=False)
def clean(session):
    for integration_test in TEST_CONFIG['cli_integration_tests'].values():
        session.run('rm', '-rf', os.path.join('cli_integration_tests', integration_test['output']), external=True)


@nox.session
def web_ui(session):
    session.run('python', 'web_tests/CRISPResso_Web_UI_Tests/web_ui_tests.py', '--log_file_path', 'web_tests/UI_test_summary_log.txt')


@nox.session
def stress(session):
    session.run('python', 'web_tests/web_stress_test.py')
