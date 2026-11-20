'''
PM4Py – A Process Mining Library for Python
Copyright (C) 2026 Process Intelligence Solutions GmbH

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see this software project's root or
visit <https://www.gnu.org/licenses/>.

Website: https://processintelligence.solutions
Contact: contact@processintelligence.solutions
'''
"""Retrospective drift on calendar indicators with CV-based smoothing selection."""

from collections import defaultdict
from math import ceil

import numpy as np
import pandas as pd

from pm4py.algo.concept_drift import _common, _timeseries
from pm4py.algo.concept_drift.variants import indicators


def apply(log, parameters=None):
    """Select a smoothing width per calendar indicator before PELT.

    This CVDrift adaptation uses :func:`indicators.extract_features` to
    construct calendar observations. It chooses from ``candidate_windows``
    (default 1, 3, 5, 9, and 17 bins), using the knee of the coefficient of
    variation (CV) curve for centered rolling ``statistic="mean"`` or
    ``"median"``. The smallest width at or below the knee's CV is selected.
    The selected values are standardized before squared-error PELT.

    At least half the bins in each smoothing window must have values. The
    statistic is undefined at a center with a missing input and scores are
    aligned to the original calendar axis. A PELT segment needs ``min_size``
    usable observations (default 3). The penalty equals ``penalty_scale``
    (default 3) times the logarithm of the number of usable observations
    for that indicator. Changes from the same indicator closer than its
    smoothing width are consolidated by segment cost gain.

    All fits are retrospective. The score details include the smoothed
    indicator values. Metadata records candidate CVs and selected widths.
    """
    get = _common.parameter
    requested = get(parameters, "candidate_windows", (1, 3, 5, 9, 17))
    widths = sorted({_common.integer(width, "candidate window") for width in requested})
    if not widths:
        raise ValueError("candidate_windows must contain at least one width")
    statistic = get(parameters, "statistic", "mean")
    if statistic not in ("mean", "median"):
        raise ValueError("statistic must be 'mean' or 'median'")
    min_size = _common.integer(get(parameters, "min_size", 3), "min_size")
    penalty_scale = _common.real(
        get(parameters, "penalty_scale", 3),
        "penalty_scale",
        minimum=np.finfo(float).tiny,
    )
    frame = indicators.extract_features(log, parameters)
    bin_size = get(parameters, indicators.Parameters.BIN_SIZE, "D")
    indices = frame.index
    cutoff = (
        indices[-1] + pd.tseries.frequencies.to_offset(bin_size)
        if len(indices)
        else None
    )
    selected = {}
    curves = {}
    smoothed = {}
    evidence = defaultdict(dict)
    for name, series in frame.items():
        width, curve, values = _select_width(series, widths, statistic, 2 * min_size)
        curves[name] = curve
        if width is None:
            continue
        selected[name] = width
        smoothed[name] = values
        observed = np.flatnonzero(np.isfinite(values))
        scaled = _common.standardize(values[observed])
        penalty = penalty_scale * np.log(max(2, len(observed)))
        cost = _timeseries.segment_cost(scaled)
        cuts = _timeseries.pelt(scaled, penalty, min_size, cost=cost)
        for index, gain in _merge_cuts(cuts, observed, width, cost):
            evidence[index][name] = gain

    scores = [
        _common.WindowScore(
            i,
            float(len(evidence.get(i, {}))),
            timestamp,
            cutoff,
            details={
                "values": {
                    name: float(values[i])
                    for name, values in smoothed.items()
                    if np.isfinite(values[i])
                },
                "changed_features": evidence.get(i, {}),
            },
        )
        for i, timestamp in enumerate(indices)
    ]
    changes = [
        _common.DriftAlarm(
            int(i),
            indices[i],
            cutoff,
            float(len(features)),
            details={"changed_features": features},
        )
        for i, features in sorted(evidence.items())
    ]
    return _common.DriftResult(
        "calendar_bin",
        scores,
        changes,
        metadata={
            "method": "cv_indicators",
            "mode": "retrospective",
            "bin_size": bin_size,
            "statistic": statistic,
            "candidate_windows": widths,
            "selected_windows": selected,
            "cv_curves": curves,
            "min_size": min_size,
            "penalty_scale": penalty_scale,
        },
    )


def _select_width(series, widths, statistic, min_observed):
    """Compute candidate CVs on a common numeric scale and select the knee."""
    series = series.where(np.isfinite(series))
    scale = series.abs().max()
    if pd.isna(scale) or scale == 0:
        scale = 1.0
    normalized = series / scale
    candidates = {}
    curve = {}
    for width in widths:
        if width > len(series):
            break
        rolling = normalized.rolling(width, min_periods=ceil(width / 2), center=True)
        values = getattr(rolling, statistic)().where(series.notna()).to_numpy()
        valid = values[np.isfinite(values)]
        if len(valid) < min_observed:
            continue
        curve[width] = float(valid.std() / max(abs(valid.mean()), np.finfo(float).eps))
        candidates[width] = values
    if not curve:
        return None, curve, None
    x = np.array(list(curve), dtype=float)
    y = np.array(list(curve.values()))
    threshold = y.min()
    if len(x) > 2 and np.ptp(y) > np.finfo(float).eps:
        x = (x - x[0]) / (x[-1] - x[0])
        relative = (y - y.min()) / np.ptp(y)
        # A common factor in the point-to-line distance cannot move the knee.
        distances = np.abs(relative - relative[0] - x * (relative[-1] - relative[0]))
        if distances.max() > np.finfo(float).eps:
            threshold = y[distances.argmax()]
    chosen = next(width for width, variation in curve.items() if variation <= threshold)
    return chosen, curve, candidates[chosen] * scale


def _merge_cuts(cuts, observed, width, cost):
    segments = [0, *cuts, len(observed)]
    candidates = []
    for left, cut, right in zip(segments, cuts, segments[2:]):
        index = observed[cut]
        gain = float(cost(left, right) - cost(left, cut) - cost(cut, right))
        candidates.append((index, gain))
    # Within a connected group of nearby boundaries, keep the strongest.
    group = []
    for current in candidates:
        if group and current[0] - group[-1][0] >= width:
            yield max(group, key=lambda point: point[1])
            group.clear()
        group.append(current)
    if group:
        yield max(group, key=lambda point: point[1])
