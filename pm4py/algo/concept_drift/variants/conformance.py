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
"""Sequential drift detection from completed-case alignment fitness."""

from enum import Enum

import numpy as np

from pm4py.algo.concept_drift import _common, _timeseries
from pm4py.algo.conformance.alignments.petri_net import algorithm as alignments
from pm4py.algo.discovery.inductive import algorithm as inductive
from pm4py.objects.conversion.process_tree import converter as tree_converter
from pm4py.objects.log.obj import Event, EventLog, Trace
from pm4py.objects.petri_net.obj import Marking, PetriNet
from pm4py.objects.petri_net.utils import align_utils
from pm4py.util import constants, xes_constants


class Parameters(Enum):
    METHOD = "method"
    REFERENCE_MODEL = "reference_model"
    REFERENCE_SIZE = "reference_size"
    MODEL_POLICY = "model_policy"
    UPDATE_WINDOW = "update_window"
    ACTIVITY_KEY = constants.PARAMETER_CONSTANT_ACTIVITY_KEY
    TIMESTAMP_KEY = constants.PARAMETER_CONSTANT_TIMESTAMP_KEY
    CASE_ID_KEY = constants.PARAMETER_CONSTANT_CASEID_KEY


def _discover(traces):
    log = EventLog(_activity_trace(trace.activities) for trace in traces)
    return tree_converter.apply(inductive.apply(log))


def _activity_trace(activities):
    return Trace(Event({xes_constants.DEFAULT_NAME_KEY: label}) for label in activities)


def _alignment_fitness(activities, model):
    trace = _activity_trace(activities)
    # Pass the standard log-move costs explicitly for the fitness normalization.
    trace_costs = [align_utils.STD_MODEL_LOG_MOVE_COST] * len(activities)
    diagnostics = alignments.apply_trace(
        trace,
        *model,
        parameters={alignments.Parameters.PARAM_TRACE_COST_FUNCTION: trace_costs},
        variant=alignments.Variants.VERSION_DIJKSTRA_LESS_MEMORY,
    )
    if diagnostics is None or not np.isfinite(diagnostics.get("fitness", np.nan)):
        raise ValueError(
            "Could not compute alignment fitness for the reference Petri net"
        )
    return float(diagnostics["fitness"])


def _reference_model(parameters):
    model = _common.parameter(parameters, Parameters.REFERENCE_MODEL, None)
    if model is not None and (
        not isinstance(model, tuple)
        or len(model) != 3
        or not isinstance(model[0], PetriNet)
        or not isinstance(model[1], Marking)
        or not isinstance(model[2], Marking)
    ):
        raise ValueError(
            "reference_model must be a (PetriNet, initial Marking, final Marking) tuple"
        )
    return model


def apply(log, parameters=None):
    """Monitor Petri-net alignment fitness with Page–Hinkley or ADWIN.

    ``method`` selects ``"page_hinkley"`` (default) or ``"adwin"``. Supply a
    sound ``reference_model`` tuple ``(net, initial_marking, final_marking)``,
    or discover one using Inductive Miner on the first ``reference_size``
    completed traces (default 30). The discovery traces calibrate the scalar
    monitor without issuing alarms and their fitness becomes available when
    the model has been trained. An external model starts monitoring the
    first completed trace immediately.

    With ``model_policy="fixed"`` the model stays fixed. With ``"on_alarm"``
    a new model is discovered from the estimated boundary through the trace
    that raised the alarm, or from the last ``update_window`` completed traces
    if a size is specified. Retraining uses only traces seen under the
    previous model after its training period. The detector is recalibrated
    on the replacement model's training traces. The new model applies to
    subsequent traces and appears in ``metadata["reference_models"]`` with
    the half-open index range used for its discovery.

    Scores report trace alignment fitness and store the detector statistic
    and model version in their details. Fitness detects changes in agreement
    with the reference model and can stay high when previously valid behavior
    disappears. This is a conformance-score detector inspired by FAIRY.
    """
    get = _common.parameter
    method = get(parameters, Parameters.METHOD, "page_hinkley")
    model = _reference_model(parameters)
    reference_size = _common.integer(
        get(parameters, Parameters.REFERENCE_SIZE, 30), "reference_size"
    )
    policy = get(parameters, Parameters.MODEL_POLICY, "fixed")
    update_window = get(parameters, Parameters.UPDATE_WINDOW, None)
    if policy not in ("fixed", "on_alarm"):
        raise ValueError("model_policy must be 'fixed' or 'on_alarm'")
    if update_window is not None:
        update_window = _common.integer(update_window, "update_window")
    detector_settings = _timeseries.detector_settings(method, parameters)
    traces = _common.completed_traces(log, parameters)
    reference_models = []
    result = _common.DriftResult(
        "trace",
        metadata={
            "variant": "conformance",
            "method": method,
            "retrospective": False,
            "reference_size": reference_size if model is None else 0,
            "model_policy": policy,
            "update_window": update_window,
            "detector_settings": detector_settings,
            "reference_models": reference_models,
        },
    )
    training_end = reference_size if model is None else 0
    if not traces or len(traces) < training_end:
        return result

    if model is None:
        model = _discover(traces[:training_end])
    reference_models.append(
        {"model": model, "training_range": (0, training_end) if training_end else None}
    )
    detector = _timeseries.make_detector(method, parameters)
    cache = {}

    def fitness(observation):
        activities = observation.activities
        if activities not in cache:
            cache[activities] = _alignment_fitness(activities, model)
        return cache[activities]

    for index, trace in enumerate(traces):
        value = fitness(trace)
        statistic, lag = detector.update(value)
        version = len(reference_models) - 1
        training = index < training_end
        available = traces[training_end - 1].end if training else trace.end
        result.scores.append(
            _common.WindowScore(
                index,
                value,
                trace.end,
                available,
                details={
                    "detector_score": statistic,
                    "reference_version": version,
                    "calibration": training,
                },
            )
        )
        result.versions.append(_common.VersionAssignment(index, version, trace.end))
        if training or lag is None:
            continue
        boundary = index - lag
        result.changes.append(
            _common.DriftAlarm(
                boundary,
                traces[boundary].end,
                available,
                statistic,
                details={"reference_version": version, "fitness": value},
            )
        )
        if policy == "on_alarm":
            start = boundary if update_window is None else index - update_window + 1
            start = max(training_end, start)
            training_end = index + 1
            training_traces = traces[start:training_end]
            model = _discover(training_traces)
            reference_models.append(
                {"model": model, "training_range": (start, training_end)}
            )
            cache.clear()
            detector = _timeseries.make_detector(method, parameters)
            for training_trace in training_traces:
                detector.update(fitness(training_trace))
    return result
