"""Regression coverage for the Batch/Aggregate report assertions."""

import pytest

from test_cli import assert_modification_summary


@pytest.fixture(params=['batch', 'aggregate'])
def mode(request):
    return request.param


def write_report(output_dir, mode, html):
    report = output_dir / f'CRISPResso2{mode.capitalize()}_report.html'
    report.write_text(html)
    return report


@pytest.mark.parametrize('heading', ['', '<h5>Summary Plots</h5>'])
def test_base_report_allows_static_summary_heading(tmp_path, mode, heading):
    write_report(tmp_path, mode, heading)
    assert_modification_summary(tmp_path, mode, pro_installed=False)


def test_base_report_rejects_pro_container(tmp_path, mode):
    write_report(tmp_path, mode, f'<div id="{mode}-modification-summary"></div>')
    with pytest.raises(AssertionError):
        assert_modification_summary(tmp_path, mode, pro_installed=False)


@pytest.fixture
def pro_summary(tmp_path, mode):
    """Minimal complete report using the production template's naming scheme."""
    data_file = tmp_path / 'Reference.MODIFICATION_PERCENTAGE_SUMMARY.txt'
    data_file.write_text('Modification\tA\nInsertions\t0.01\n')
    html = [f'<div id="{mode}-modification-summary"><h5>Summary Plots</h5>']
    plots = []
    for index, modification in enumerate(
        ('insertions', 'deletions', 'substitutions', 'all_modifications')
    ):
        for kind in ('heatmap', 'line'):
            target = f'{mode}-modification-{index}-{kind}'
            div_id = f'{mode}-0-{modification}-{kind}'
            html.append(
                f'<button id="{target}-tab" data-bs-target="#{target}"></button>'
                f'<div id="{target}"><div id="{div_id}"></div>'
                f'<a href="{data_file.name}">Data</a></div>'
            )
            plot = tmp_path / (
                f'CRISPResso{mode.capitalize()}_percentage_of_{modification}'
                f'_across_alleles_Reference_{kind}.html'
            )
            plot.write_text(f'<script>Plotly.newPlot("{div_id}", [], {{}});</script>')
            plots.append(plot)
    html.append('</div>')
    return write_report(tmp_path, mode, '\n'.join(html)), plots, data_file


def test_complete_pro_summary_passes(tmp_path, mode, pro_summary):
    assert_modification_summary(tmp_path, mode, pro_installed=True)


@pytest.mark.parametrize('defect', [
    'missing_container',
    'duplicate_id',
    'missing_tab',
    'broken_tab_target',
    'missing_embedded_plot',
    'missing_plot_file',
    'duplicate_plot_file',
    'missing_plotly',
    'missing_data_link',
    'missing_data_file',
])
def test_incomplete_pro_summary_fails(tmp_path, mode, pro_summary, defect):
    report, plots, data_file = pro_summary
    html = report.read_text()
    if defect == 'missing_container':
        html = html.replace(f'id="{mode}-modification-summary"', '')
    elif defect == 'duplicate_id':
        html += f'<div id="{mode}-modification-summary"></div>'
    elif defect == 'missing_tab':
        html = html.replace(f'data-bs-target="#{mode}-modification-3-line"', '')
    elif defect == 'broken_tab_target':
        html = html.replace(
            f'data-bs-target="#{mode}-modification-3-line"',
            f'data-bs-target="#{mode}-modification-missing"',
        )
    elif defect == 'missing_embedded_plot':
        html = html.replace(f'id="{mode}-0-all_modifications-line"', '')
    elif defect == 'missing_plot_file':
        plots[-1].unlink()
    elif defect == 'duplicate_plot_file':
        plots[-1].with_name(plots[-1].name.replace('Reference', 'Other')).write_text(
            plots[-1].read_text()
        )
    elif defect == 'missing_plotly':
        plots[-1].write_text('<html>No plot</html>')
    elif defect == 'missing_data_link':
        html = html.replace(f'href="{data_file.name}"', '', 1)
    elif defect == 'missing_data_file':
        data_file.unlink()
    report.write_text(html)
    with pytest.raises(AssertionError):
        assert_modification_summary(tmp_path, mode, pro_installed=True)
