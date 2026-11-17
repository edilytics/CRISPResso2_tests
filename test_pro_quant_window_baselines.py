"""The runs with a gapped quantification window draw one gray box per range and
one label in the Pro HTML baselines, so a regeneration from a CRISPRessoPro
checkout that predates either cannot land unnoticed."""
import json
import re
from pathlib import Path

import pytest

PRO_BASELINES = Path(__file__).parent / 'cli_integration_tests' / 'expected_results_pro'
NEW_PLOT = re.compile(r'Plotly\.newPlot\(\s*"[^"]+",\s*')
DECODER = json.JSONDecoder()

# Pinned from include_idxs in a fresh run: expected_results/*/CRISPResso2_info.json
# is not diffed by the suite and is stale for some of these runs.
PARAMS = [[[20, 30], [45, 50]], [[24, 34], [49, 54]]]
GAPPED_RUNS = {
    'CRISPResso_on_params': PARAMS,
    'CRISPResso_on_params-deletions': PARAMS,
    'CRISPResso_on_base_editor': [[[91, 92], [172, 173], [188, 189]], [[87, 88], [179, 180], [195, 196]]],
    'CRISPResso_on_prime_editor': [[[38, 39], [48, 57], [79, 80]]],
    'CRISPResso_on_vcf-prime-edit-basic': [[[91, 92], [97, 106]]],
}


def _plot_boxes(html):
    for match in NEW_PLOT.finditer(html):
        _, end = DECODER.raw_decode(html, match.end())
        start = end + re.match(r'\s*,\s*', html[end:]).end()
        layout, _ = DECODER.raw_decode(html, start)
        boxes = [[s['x0'], s['x1']] for s in layout.get('shapes', []) if s.get('fillcolor') == 'gray']
        if boxes:
            labels = [a['x'] for a in layout.get('annotations', []) if a.get('text') == 'Quantification window']
            yield boxes, labels


@pytest.mark.parametrize('run', GAPPED_RUNS)
def test_gapped_run_draws_a_box_per_range(run):
    plots = [
        plot
        for path in (PRO_BASELINES / run).glob('*.html')
        for plot in _plot_boxes(path.read_text(encoding='utf-8'))
    ]
    assert plots
    assert [boxes for boxes, _ in plots if boxes not in GAPPED_RUNS[run]] == []
    assert [labels for boxes, labels in plots if labels != [boxes[0][0]]] == []
