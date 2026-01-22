"""BWA alignment verification for syn-gen synthetic reads."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


def parse_cigar(cigar: str) -> list[tuple[str, int]]:
    """
    Parse CIGAR string into list of (operation, length) tuples.

    Args:
        cigar: CIGAR string like '50M3D47M'

    Returns:
        List of tuples like [('M', 50), ('D', 3), ('M', 47)]
    """
    pattern = re.compile(r'(\d+)([MIDNSHP=X])')
    return [(op, int(length)) for length, op in pattern.findall(cigar)]
