"""Every plotly fragment in the Pro HTML baselines sits in the box
CRISPRessoPro.plot.write_html_in_centered_box writes, so a regeneration from
a CRISPRessoPro checkout that predates the box cannot land unnoticed."""
import re
from pathlib import Path

import pytest

PRO_BASELINES = Path(__file__).parent / 'cli_integration_tests' / 'expected_results_pro'
BOX = re.compile(r'<div style="width:100%;( max-width:700px;)? margin:0 auto;"><div>\s*<div id="([^"]+)"')
GRAPH_DIV = re.compile(r'<div id="([^"]+)" class="plotly-graph-div"')
UNCAPPED_ID = re.compile(r'^(batch|aggregate)-\d+-[a-z_]+-(heatmap|line)$')

BASELINE_HTML = sorted(p for p in PRO_BASELINES.rglob('*.html')
                       if 'plotly-graph-div' in p.read_text(encoding='utf-8'))


@pytest.mark.parametrize('path', BASELINE_HTML, ids=lambda p: str(p.relative_to(PRO_BASELINES)))
def test_every_plotly_fragment_is_boxed(path):
    html = path.read_text(encoding='utf-8')
    graph_ids = GRAPH_DIV.findall(html)
    boxed = {div_id: bool(cap) for cap, div_id in BOX.findall(html)}
    assert sorted(boxed) == sorted(graph_ids), 'plotly div outside the centered box'
    for div_id, capped in boxed.items():
        assert capped != bool(UNCAPPED_ID.match(div_id)), f'{div_id}: wrong cap'
    assert '"autosize":false' not in html


def test_baselines_exist():
    assert len(BASELINE_HTML) > 400
