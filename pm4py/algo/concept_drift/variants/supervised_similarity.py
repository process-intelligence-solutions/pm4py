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
"""Learned drift recognition on window similarity images."""

from collections.abc import Iterable
from dataclasses import dataclass
from itertools import groupby

import numpy as np

from pm4py.algo.concept_drift import _common


@dataclass(frozen=True)
class Region:
    """A model prediction in inclusive, zero-based image window coordinates."""

    start: int
    end: int
    kind: str
    confidence: float = 1.0


@dataclass
class SimilarityImage:
    """Grayscale image and the start-order trace ranges used to construct it."""

    pixels: np.ndarray
    windows: list[tuple[int, int]]


def similarity_image(log, parameters=None) -> SimilarityImage:
    """Encode cosine similarities between balanced windows of start-ordered cases.

    The darkest pixel is the minimum observed similarity and the brightest
    pixel represents identical behavior. An entirely uniform image is bright.
    ``num_windows`` defaults to 200 and is capped by the trace count.
    """
    image, _ = _encode(log, parameters)
    return image


def apply(log, parameters=None):
    """Use a trained predictor to map drift regions to their trace locations.

    Pass a callable as ``predictor`` that accepts the grayscale uint8 image and
    returns :class:`Region` objects. Use :func:`fit` for a patch classifier or
    adapt an external image detector to this interface. Predictions with
    confidence lower than ``min_confidence`` (default 0.5) are recorded as
    scores only. Sudden regions map to their middle window. Other regions
    produce an interval from the first to last predicted window.
    """
    get = _common.parameter
    predictor = get(parameters, "predictor", None)
    if not callable(predictor):
        raise TypeError("predictor must be a trained callable returning Region objects")
    threshold = _common.real(
        get(parameters, "min_confidence", 0.5), "min_confidence", maximum=1
    )
    image, traces = _encode(log, parameters)
    observed_at = max(trace.end for trace in traces) if traces else None
    scores = []
    changes = []
    intervals = []
    predicted = predictor(image.pixels) if len(image.windows) >= 2 else []
    regions = sorted(
        predicted, key=lambda region: (region.start, region.end, region.kind)
    )
    for region in regions:
        first, last = _validate_region(region, len(image.windows))
        confidence = _common.real(region.confidence, "confidence", maximum=1)
        location = (first + last) // 2 if region.kind == "sudden" else first
        start = image.windows[location][0]
        index = image.windows[last][1] - 1
        details = {
            "type": region.kind,
            "window_range": (first, last),
            "confidence": confidence,
        }
        point = _common.WindowScore(
            start, confidence, traces[start].start, observed_at, details=details
        )
        scores.append(point)
        if confidence < threshold:
            continue
        changes.append(
            _common.DriftAlarm(
                start, point.timestamp, observed_at, confidence, details=details
            )
        )
        if region.kind != "sudden":
            intervals.append(
                _common.DriftInterval(
                    start,
                    index,
                    point.timestamp,
                    traces[index].start,
                    observed_at,
                    details,
                )
            )

    return _common.DriftResult(
        "trace",
        sorted(scores, key=lambda score: score.index),
        sorted(changes, key=lambda alarm: alarm.index),
        metadata={
            "method": "supervised_similarity",
            "representation": "directly_follows_cosine_similarity_image",
            "predictor": type(predictor).__name__,
            "retrospective": True,
            "trace_order": "start",
            "num_windows": len(image.windows),
            "min_confidence": threshold,
            "windows": image.windows,
        },
        intervals=intervals,
    )


def fit(
    examples: Iterable[tuple],
    parameters=None,
    *,
    radius=2,
    random_state=0,
):
    """Train a decision tree to classify patches centered on window boundaries.

    Each example is a pair of an event log and its labeled :class:`Region`
    objects. Use ``kind="sudden"`` for point annotations, and intervals for
    other patterns. Unannotated boundaries provide stable examples. Apply
    the resulting predictor with the same image window settings as in training.
    This lightweight adaptation requires the ``pm4py[ml]`` extra.
    """
    try:
        from sklearn.tree import DecisionTreeClassifier
    except ModuleNotFoundError as error:
        if error.name != "sklearn":
            raise
        raise ImportError(
            "The patch classifier requires scikit-learn. Install pm4py[ml]."
        ) from error

    radius = _common.integer(radius, "radius")
    patches, labels = [], []
    for log, regions in examples:
        image = similarity_image(log, parameters)
        count = len(image.windows)
        targets = ["stable"] * count
        for region in regions:
            start, end = _validate_region(region, count)
            if start == 0:
                raise ValueError("A training region needs a preceding window")
            if region.kind == "sudden":
                start = end = (start + end) // 2
            if any(label != "stable" for label in targets[start : end + 1]):
                raise ValueError("Training regions must not overlap")
            targets[start : end + 1] = [region.kind] * (end - start + 1)
        if count >= 2:
            patches.extend(_patches(image.pixels, radius))
            labels.extend(targets[1:])
    if "stable" not in labels or len(set(labels)) < 2:
        raise ValueError("Training requires both stable and drift boundaries")
    model = DecisionTreeClassifier(
        max_depth=6, class_weight="balanced", random_state=random_state
    ).fit(patches, labels)
    return _PatchPredictor(model, radius)


@dataclass
class _PatchPredictor:
    model: object
    radius: int

    def __call__(self, pixels):
        if len(pixels) < 2:
            return []
        probabilities = self.model.predict_proba(_patches(pixels, self.radius))
        labels = self.model.classes_[probabilities.argmax(axis=1)]
        regions = []
        for kind, group in groupby(
            enumerate(labels, start=1), key=lambda item: item[1]
        ):
            if kind == "stable":
                continue
            windows = [index for index, _ in group]
            start, end = windows[0], windows[-1]
            confidence = probabilities[start - 1 : end].max(axis=1)
            if kind == "sudden":
                start += int(confidence.argmax())
                end = start
            regions.append(Region(start, end, str(kind), float(confidence.max())))
        return regions


def _patches(pixels, radius):
    extra = max(0, radius - 1)
    padded = np.pad(pixels, extra, mode="edge")
    width = 2 * radius
    return [
        padded[i : i + width, i : i + width].ravel() for i in range(len(pixels) - 1)
    ]


def _encode(log, parameters):
    traces = sorted(
        _common.completed_traces(log, parameters), key=lambda trace: trace.start
    )
    windows = _common.window_partition(
        len(traces), _common.parameter(parameters, "num_windows", 200)
    )
    similarity = _common.dfg_window_similarities(traces, windows)
    minimum = similarity.min() if similarity.size else 1
    if minimum < 1 and not np.isclose(minimum, 1, rtol=0, atol=1e-12):
        pixels = np.clip(255 * (similarity - minimum) / (1 - minimum), 0, 255)
    else:
        pixels = np.full(similarity.shape, 255)
    return SimilarityImage(pixels.astype(np.uint8), windows), traces


def _validate_region(region, count):
    start = _common.integer(region.start, "region start", 0)
    end = _common.integer(region.end, "region end", start)
    if end >= count:
        raise ValueError("Region lies outside the similarity image")
    if not isinstance(region.kind, str) or not region.kind or region.kind == "stable":
        raise ValueError("Region must have a drift type")
    return start, end
