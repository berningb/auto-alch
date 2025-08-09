#!/usr/bin/env python3
"""
Analyze click timing CSV to derive per-digit baseline offsets.

Reads auto_actions/data/click_timing.csv (created by record_click_timing.py)
and prints stats per digit {1..4}:
  count, mean, median, p25/p75, stdev (ms)

Also prints a recommended pre_delay for digit 2 (median minus 20 ms).
"""

from __future__ import annotations

import csv
import os
import statistics as stats
from typing import Dict, List

try:
    import numpy as np
except Exception:
    np = None  # percentiles fallback


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(os.path.dirname(BASE_DIR), 'data', 'click_timing.csv')


def percentile(values: List[float], p: float) -> float:
    if not values:
        return float('nan')
    if np is not None:
        return float(np.percentile(values, p))
    # Fallback simple percentile
    s = sorted(values)
    k = (len(s) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(s) - 1)
    if f == c:
        return float(s[int(k)])
    d0 = s[f] * (c - k)
    d1 = s[c] * (k - f)
    return float(d0 + d1)


def main():
    if not os.path.exists(DATA_PATH):
        print(f"❌ No data file at {DATA_PATH}. Run record_click_timing.py first.")
        return

    per_digit: Dict[int, List[float]] = {1: [], 2: [], 3: [], 4: []}
    with open(DATA_PATH, 'r', newline='') as f:
        r = csv.DictReader(f)
        for row in r:
            d_str = row.get('digit', '')
            delta_str = row.get('ms_since_last_digit_change', '')
            if not d_str or not delta_str:
                continue
            try:
                d = int(d_str)
                delta = float(delta_str)
            except Exception:
                continue
            if d in per_digit:
                per_digit[d].append(delta)

    for d in (1, 2, 3, 4):
        vals = per_digit[d]
        if not vals:
            print(f"digit {d}: no samples")
            continue
        mean = stats.mean(vals)
        med = stats.median(vals)
        p25 = percentile(vals, 25)
        p75 = percentile(vals, 75)
        sd = stats.pstdev(vals) if len(vals) > 1 else 0.0
        print(f"digit {d}: n={len(vals)} mean={mean:.1f} ms  median={med:.1f} ms  p25={p25:.1f} ms  p75={p75:.1f} ms  sd={sd:.1f}")

    if per_digit[2]:
        med2 = stats.median(per_digit[2])
        recommended = max(0.0, med2 - 20.0)
        print(f"\nRecommended pre_delay for digit 2: {recommended:.0f} ms (median-20ms)")


if __name__ == '__main__':
    main()


