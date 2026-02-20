import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

# Make diff.py importable
sys.path.insert(0, str(Path(__file__).parent))
import diff


MODULE_MAP = {
    'CRISPResso': 'CRISPResso2.CRISPRessoCORE',
    'CRISPRessoBatch': 'CRISPResso2.CRISPRessoBatchCORE',
    'CRISPRessoPooled': 'CRISPResso2.CRISPRessoPooledCORE',
    'CRISPRessoWGS': 'CRISPResso2.CRISPRessoWGSCORE',
    'CRISPRessoCompare': 'CRISPResso2.CRISPRessoCompareCORE',
    'CRISPRessoAggregate': 'CRISPResso2.CRISPRessoAggregateCORE',
}

DATA_SUFFIXES = ('.txt', '.sam', '.vcf')
HTML_SUFFIXES = ('.html',)


def pytest_addoption(parser):
    parser.addoption(
        '--with-coverage',
        action='store_true',
        default=False,
        help='Wrap CLI commands with coverage run for measuring CRISPResso2 code coverage.',
    )
    parser.addoption(
        '--skip-html',
        action='store_true',
        default=False,
        help='Skip HTML file comparisons (useful for quick local iteration).',
    )
    parser.addoption(
        '--pro',
        action='store_true',
        default=False,
        help='Compare HTML against expected_results_pro/ (overrides auto-detection).',
    )


def pytest_collection_modifyitems(config, items):
    pro_installed = importlib.util.find_spec('CRISPRessoPro') is not None
    if not pro_installed:
        skip_pro = pytest.mark.skip(reason='CRISPRessoPro not installed')
        for item in items:
            if 'pro_only' in item.keywords:
                item.add_marker(skip_pro)


@pytest.fixture(scope='session')
def pro_installed(request):
    return importlib.util.find_spec('CRISPRessoPro') is not None


@pytest.fixture(scope='session')
def cli_test_dir():
    return Path(__file__).parent / 'cli_integration_tests'


@pytest.fixture(scope='session')
def skip_html(request):
    return request.config.getoption('--skip-html')


@pytest.fixture(scope='session')
def run_crispresso(request, cli_test_dir):
    with_coverage = request.config.getoption('--with-coverage')

    def _run(cmd):
        if with_coverage:
            tool = cmd.split(None, 1)[0]
            rest = cmd.split(None, 1)[1] if ' ' in cmd else ''
            module = MODULE_MAP.get(tool)
            if module:
                coveragerc = str(cli_test_dir.parent / '.coveragerc')
                cmd = (
                    f'coverage run --parallel-mode --rcfile={coveragerc}'
                    f' -m {module} -- {rest}'
                )
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=str(cli_test_dir),
            capture_output=True,
            text=True,
        )
        return result

    return _run


@pytest.fixture(scope='session')
def assert_no_diff(pro_installed, skip_html, cli_test_dir):
    expected_results = cli_test_dir / 'expected_results'
    expected_results_pro = cli_test_dir / 'expected_results_pro'

    def _assert(actual_dir):
        test_name = actual_dir.name
        has_diff = False

        # Data files — always compared against expected_results/
        expected_data = expected_results / test_name
        if not expected_data.exists():
            pytest.skip(f'Expected results not found: {expected_data}')
        has_diff |= diff.diff_dir(
            str(actual_dir),
            str(expected_data),
            suffixes=DATA_SUFFIXES,
        )

        # HTML files
        if not skip_html:
            if pro_installed:
                expected_html = expected_results_pro / test_name
                if not expected_html.exists():
                    pytest.skip(
                        f'Pro HTML expected results not found: {expected_html}'
                    )
            else:
                expected_html = expected_data
            has_diff |= diff.diff_dir(
                str(actual_dir),
                str(expected_html),
                suffixes=HTML_SUFFIXES,
            )

        assert not has_diff, (
            f'Differences found for {test_name}'
        )

    return _assert
